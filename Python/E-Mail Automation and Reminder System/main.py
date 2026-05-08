from fastapi import FastAPI, BackgroundTasks, Response
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import sqlite3
import uuid
import datetime
from contextlib import asynccontextmanager

from core_logic import get_feed_entries, extract_article_body, analyze_compliance_risk, save_decision_to_json, send_tracked_email, send_reminder_email

# --- Database Setup (SQLite) ---
DB_FILE = "sentinel.db"
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS email_logs (id TEXT PRIMARY KEY, to_email TEXT, subject TEXT, status TEXT, timestamp DATETIME)''')
    c.execute('''CREATE TABLE IF NOT EXISTS processed_articles (link TEXT PRIMARY KEY)''')
    conn.commit()
    conn.close()

init_db()

# --- Scheduler Setup ---
jobstores = {'default': SQLAlchemyJobStore(url=f'sqlite:///jobs.sqlite')}
scheduler = BackgroundScheduler(jobstores=jobstores)

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(title="RegTech API API", lifespan=lifespan)

# --- Pydantic Models ---
class CampaignConfig(BaseModel):
    feed_url: str
    target_email: str
    sender_email: str
    app_password: str
    interval_minutes: int

class Reminder(BaseModel):
    target_email: str
    sender_email: str
    app_password: str
    message: str
    run_date: str # ISO format

# --- Background Worker Logic ---
def watchdog_job(config: dict):
    """The automated job that runs on a schedule."""
    entries = get_feed_entries(config['feed_url'])
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    for entry in entries:
        # Prevent duplicate processing
        c.execute("SELECT link FROM processed_articles WHERE link=?", (entry.link,))
        if c.fetchone():
            continue
            
        body = extract_article_body(entry.link)
        if not body:
            continue
            
        decision = analyze_compliance_risk(entry.title, body)
        
        # Save to JSON
        log_data = {"timestamp": str(datetime.datetime.now()), "title": entry.title, "decision": decision}
        save_decision_to_json(log_data)
        
        # Only email if action is required or risk is high
        if decision.get("action_required") or decision.get("risk_level") in ["High", "Critical"]:
            tracking_id = str(uuid.uuid4())
            # Insert pending status
            c.execute("INSERT INTO email_logs VALUES (?, ?, ?, 'Sent', ?)", (tracking_id, config['target_email'], entry.title, datetime.datetime.now()))
            conn.commit()
            
            # Note: In production, change 127.0.0.1 to your actual server domain
            api_url = "http://127.0.0.1:8000"
            send_tracked_email(config['target_email'], config['sender_email'], config['app_password'], entry.title, decision, tracking_id, api_url)
        
        c.execute("INSERT INTO processed_articles VALUES (?)", (entry.link,))
        conn.commit()
    conn.close()

# --- API Endpoints ---
@app.post("/campaigns/create")
def create_campaign(config: CampaignConfig):
    job_id = f"campaign_{uuid.uuid4().hex[:8]}"
    scheduler.add_job(
        watchdog_job, 
        'interval', 
        minutes=config.interval_minutes, 
        args=[config.model_dump()], # POINT 2 FIX: Updated from dict()
        id=job_id,
        replace_existing=True
    )
    return {"message": "Campaign started", "job_id": job_id}

@app.post("/reminders/create")
def create_reminder(rem: Reminder):
    # Sends a one-off email at a specific time
    job_id = f"reminder_{uuid.uuid4().hex[:8]}"
    run_time = datetime.datetime.fromisoformat(rem.run_date)
    
    scheduler.add_job(
        send_reminder_email, 
        'date', 
        run_date=run_time, 
        args=[rem.target_email, rem.sender_email, rem.app_password, "Reminder", rem.message, job_id, "http://127.0.0.1:8000"],
        id=job_id
    )
    return {"message": "Reminder scheduled", "job_id": job_id}

@app.get("/track/{tracking_id}.gif")
def track_email_open(tracking_id: str):
    """The invisible pixel endpoint. When hit, updates DB to 'Opened'."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE email_logs SET status='Opened' WHERE id=?", (tracking_id,))
    conn.commit()
    conn.close()
    
    # Return a 1x1 transparent GIF
    pixel = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
    return Response(content=pixel, media_type="image/gif")

@app.get("/stats")
def get_stats():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM email_logs ORDER BY timestamp DESC")
    logs = c.fetchall()
    conn.close()
    return {"logs": logs}