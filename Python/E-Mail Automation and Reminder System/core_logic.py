import feedparser
import trafilatura
import smtplib
import json
import logging
import os
import ollama
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging for professional error tracking
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s"
)

DECISIONS_FILE = "ai_decisions_log.json"

def get_feed_entries(feed_url: str, limit: int = 5):
    """Extracts headlines from an RSS feed."""
    logging.info(f"Attempting to fetch feed: {feed_url}")
    try:
        feed = feedparser.parse(feed_url)
        if feed.bozo:
            logging.error(f"Feed formatting error (Bozo exception): {feed.bozo_exception}")
            return []
        return feed.entries[:limit]
    except Exception as e:
        logging.error(f"Failed to extract feed {feed_url}: {str(e)}")
        return []

def extract_article_body(url: str):
    """Extracts clean text from a URL using Trafilatura."""
    logging.info(f"Downloading body for: {url}")
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded is None:
            logging.warning(f"Trafilatura failed to download URL: {url}")
            return None
        text = trafilatura.extract(downloaded)
        return text if text else None
    except Exception as e:
        logging.error(f"Error extracting body from {url}: {str(e)}")
        return None

def analyze_compliance_risk(title: str, body: str):
    """Uses cloud Ollama to act as a Financial Compliance Analyst."""
    logging.info(f"Sending data to Ollama for reasoning: {title}")
    
    # POINT 4 FIX: Strict instruction for lowercase boolean
    prompt = f"""
    You are a RegTech Compliance Analyst in India. Analyze the following regulatory update from the RBI/Government.
    Title: {title}
    Details: {body[:1500]} # Limit tokens
    
    Respond STRICTLY in JSON format with these exact keys:
    "risk_level": (Low, Medium, High, Critical),
    "summary": (A 2-sentence summary of the impact on Indian startups),
    "action_required": (true or false as a lowercase boolean, not a string),
    "recommendation": (What the compliance team should do next)
    """
    
    try:
        response = ollama.generate(
            model="gpt-oss:20b-cloud", 
            prompt=prompt,
            format="json"
        )
        
        # POINT 1 FIX: Clean potential markdown formatting before parsing
        raw_response = response.get("response", "{}")
        cleaned_response = raw_response.strip().removeprefix("```json").removesuffix("```").strip()
        
        decision = json.loads(cleaned_response)
        return decision
    except Exception as e:
        logging.error(f"Ollama reasoning failed: {str(e)}")
        return {"risk_level": "Unknown", "summary": "AI Processing Failed", "action_required": False, "recommendation": "Review manually."}

def save_decision_to_json(data: dict):
    """Saves the AI's reasoning to a persistent JSON log."""
    try:
        if not os.path.exists(DECISIONS_FILE):
            with open(DECISIONS_FILE, "w") as f:
                json.dump([], f)
                
        with open(DECISIONS_FILE, "r") as f:
            logs = json.load(f)
            
        logs.append(data)
        
        with open(DECISIONS_FILE, "w") as f:
            json.dump(logs, f, indent=4)
        logging.info("Decision successfully saved to JSON.")
    except Exception as e:
        logging.error(f"Failed to save JSON log: {str(e)}")

def send_tracked_email(to_email: str, from_email: str, app_password: str, subject: str, ai_data: dict, tracking_id: str, api_url: str):
    """Sends an email with a 1x1 tracking pixel embedded in the HTML."""
    logging.info(f"Preparing to send email to {to_email}")
    
    # The tracking pixel URL (points to our FastAPI backend)
    tracking_pixel = f'<img src="{api_url}/track/{tracking_id}.gif" width="1" height="1" />'
    
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #d9534f;">🚨 Regulatory Sentinel Alert</h2>
            <p><strong>Subject:</strong> {subject}</p>
            <p><strong>Risk Level:</strong> {ai_data.get('risk_level', 'N/A')}</p>
            <p><strong>AI Summary:</strong><br>{ai_data.get('summary', 'N/A')}</p>
            <p><strong>Recommended Action:</strong><br>{ai_data.get('recommendation', 'N/A')}</p>
            <hr>
            <p style="font-size: 0.8em; color: #777;">Automated by RegTech AI Pipeline</p>
            {tracking_pixel}
        </body>
    </html>
    """
    
    try:
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = f"[{ai_data.get('risk_level', 'Info')}] {subject}"
        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(from_email, app_password)
            server.send_message(msg)
            
        logging.info(f"Email successfully sent to {to_email}")
        return True
    except Exception as e:
        logging.error(f"SMTP Email failed to send: {str(e)}")
        return False

def send_reminder_email(to_email: str, from_email: str, app_password: str, subject: str, message: str, tracking_id: str, api_url: str):
    """Sends a reminder email with a different template."""
    logging.info(f"Preparing to send reminder email to {to_email}")
    
    # The tracking pixel URL (points to our FastAPI backend)
    tracking_pixel = f'<img src="{api_url}/track/{tracking_id}.gif" width="1" height="1" />'
    
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; background-color: #f9f9f9;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h2 style="color: #0066cc; border-bottom: 3px solid #0066cc; padding-bottom: 10px;">⏰ Team Reminder</h2>
                <p style="font-size: 16px; line-height: 1.6; color: #333;">{message}</p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                <p style="font-size: 0.9em; color: #666; text-align: center;">📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p style="font-size: 0.8em; color: #999; text-align: center;">Automated Reminder System</p>
            </div>
            {tracking_pixel}
        </body>
    </html>
    """
    
    try:
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = f"⏰ {subject}"
        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(from_email, app_password)
            server.send_message(msg)
            
        logging.info(f"Reminder email successfully sent to {to_email}")
        return True
    except Exception as e:
        logging.error(f"Reminder email failed to send: {str(e)}")
        return False