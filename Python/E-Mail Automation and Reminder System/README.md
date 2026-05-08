# 🛡️ RegTech Agentic Sentinel

An automated compliance monitoring, AI-powered reasoning, and email outreach pipeline designed for the Indian market. This system continuously monitors regulatory updates from RBI (Reserve Bank of India) and other government sources, analyzes them using AI, and sends intelligent alerts to compliance teams.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Database Schema](#database-schema)
- [How It Works](#how-it-works)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

RegTech Sentinel is an intelligent compliance monitoring system that:

1. **Monitors** RSS feeds from regulatory bodies (RBI, Government of India)
2. **Analyzes** regulatory updates using AI (Ollama) for compliance risk assessment
3. **Alerts** compliance teams via email with risk levels and recommendations
4. **Tracks** email opens using invisible tracking pixels
5. **Schedules** automated campaigns and manual reminders
6. **Logs** all AI decisions for audit purposes

### Use Cases

- **Startups**: Stay compliant with changing RBI regulations
- **Fintech Companies**: Monitor regulatory changes affecting digital payments
- **Compliance Teams**: Automated risk assessment of regulatory updates
- **Legal Departments**: Track and analyze regulatory announcements

---

## 🏗️ Architecture

```
┌─────────────────┐
│   Streamlit UI  │  (User Interface)
│     (app.py)    │
└────────┬────────┘
         │ HTTP Requests
         ▼
┌─────────────────┐
│   FastAPI       │  (REST API Backend)
│   (main.py)     │
└────────┬────────┘
         │
         ├─────────────────────────────────┐
         │                                 │
         ▼                                 ▼
┌─────────────────┐              ┌─────────────────┐
│  APScheduler   │              │   SQLite DB     │
│  (Job Queue)   │              │  (sentinel.db)  │
└────────┬────────┘              └─────────────────┘
         │
         ▼
┌─────────────────┐
│  core_logic.py  │  (Business Logic)
│                 │
│  • RSS Parsing  │
│  • AI Analysis  │
│  • Email Sending│
└────────┬────────┘
         │
         ├─────────────────────────────────┐
         │                                 │
         ▼                                 ▼
┌─────────────────┐              ┌─────────────────┐
│  Ollama AI      │              │  Gmail SMTP     │
│  (Local/Cloud)  │              │  (Email Service)│
└─────────────────┘              └─────────────────┘
```

### Component Breakdown

| Component | File | Purpose |
|-----------|------|---------|
| **UI** | `app.py` | Streamlit web interface for user interaction |
| **API** | `main.py` | FastAPI backend with REST endpoints |
| **Core Logic** | `core_logic.py` | Business logic for RSS, AI, and email |
| **Database** | `sentinel.db` | SQLite database for tracking |
| **Job Store** | `jobs.sqlite` | APScheduler job persistence |
| **AI Log** | `ai_decisions_log.json` | JSON log of AI decisions |

---

## ✨ Features

### 🤖 AI-Powered Risk Analysis
- Uses Ollama AI to analyze regulatory updates
- Categorizes risk levels: Low, Medium, High, Critical
- Provides actionable recommendations
- Generates 2-sentence impact summaries

### 📧 Intelligent Email System
- HTML-formatted compliance alerts
- Risk-level tagged subject lines
- Invisible tracking pixel for open detection
- Gmail SMTP integration with app passwords

### 📡 RSS Feed Monitoring
- Pre-configured RBI feeds (Notifications, Press Releases)
- Custom RSS feed support
- Configurable check intervals (15-1440 minutes)
- Duplicate article prevention

### ⏰ Job Scheduling
- Automated periodic monitoring campaigns
- One-off reminder scheduling
- Background job execution
- Job persistence across restarts

### 📊 Tracking & Analytics
- Email open tracking via invisible pixels
- Real-time status dashboard
- Historical email logs
- AI decision audit trail

### 🎨 User-Friendly Interface
- Modern Streamlit UI
- Tabbed navigation
- Color-coded status indicators
- Responsive design

---

## 📦 Prerequisites

### Required Software

1. **Python 3.8+**
   ```bash
   python --version
   ```

2. **Ollama** (for AI analysis)
   - Download from: https://ollama.ai
   - Install and start Ollama service
   - Pull required model:
     ```bash
     ollama pull gpt-oss:20b-cloud
     # OR use any other model like:
     # ollama pull llama2
     # ollama pull mistral
     ```

3. **Gmail Account with App Password**
   - Enable 2-Factor Authentication
   - Generate App Password: Google Account → Security → App Passwords
   - Use this app password (not your regular password)

### System Requirements

- **OS**: Windows, macOS, or Linux
- **RAM**: 4GB minimum (8GB recommended for AI)
- **Disk**: 500MB free space
- **Network**: Internet connection for RSS feeds and email

---

## 🚀 Installation

### Step 1: Clone or Download the Project

```bash
cd "E:\Jupyter Notebook\IIT Delhi AI Projects\Python\E-Mail Automation and Reminder System"
```

### Step 2: Create Virtual Environment

```powershell
# Windows PowerShell
python -m venv em
.\em\Scripts\Activate.ps1

# If you get execution policy error, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 3: Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# OR using uv (faster)
uv pip install -r requirements.txt
```

### Step 4: Verify Installation

```bash
# Check Python packages
python -c "import fastapi, streamlit, ollama, feedparser; print('All packages installed!')"

# Check Ollama
ollama list
```

### Step 5: Initialize Database

The database is automatically created when you first run `main.py`. No manual setup required.

---

## ⚙️ Configuration

### Environment Variables (Optional)

Create a `.env` file in the project root:

```env
# Ollama Configuration
OLLAMA_MODEL=gpt-oss:20b-cloud
OLLAMA_URL=http://localhost:11434

# SMTP Configuration (can also be set in UI)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# API Configuration
API_HOST=127.0.0.1
API_PORT=8000
```

### Model Configuration

Edit `core_logic.py` line 60 to change the AI model:

```python
response = ollama.generate(
    model="gpt-oss:20b-cloud",  # Change this to your model
    prompt=prompt,
    format="json"
)
```

Available Ollama models:
- `gpt-oss:20b-cloud` (default, cloud-based)
- `llama2` (local, 7B parameters)
- `mistral` (local, 7B parameters)
- `codellama` (for code analysis)

---

## 🎮 Usage

### Starting the System

You need to run **two** components:

#### 1. Start the FastAPI Backend

```bash
# Terminal 1
python main.py
```

The API will be available at: `http://127.0.0.1:8000`

#### 2. Start the Streamlit UI

```bash
# Terminal 2
streamlit run app.py
```

The UI will open in your browser at: `http://localhost:8501`

### Using the Web Interface

#### Tab 1: 📊 Dashboard & Tracking
- View all sent emails
- Check open status (tracked via invisible pixel)
- Refresh statistics

#### Tab 2: 📡 Create Campaign
1. Select RSS feed (RBI Notifications/Press Releases or Custom)
2. Set check interval (15-1440 minutes)
3. Configure SMTP in sidebar (if not done)
4. Click "Deploy Sentinel Agent"

#### Tab 3: ⏰ Manual Reminders
1. Enter reminder message
2. Select date and time
3. Click "Schedule Reminder"

#### Tab 4: 🧠 AI Decisions Log
- View all AI risk assessments
- See timestamps and decisions
- Export for audit purposes

---

## 🔌 API Endpoints

### POST `/campaigns/create`
Create a new monitoring campaign.

**Request Body:**
```json
{
  "feed_url": "https://www.rbi.org.in/notifications_rss.xml",
  "target_email": "manager@startup.in",
  "sender_email": "compliance_bot@gmail.com",
  "app_password": "your-app-password",
  "interval_minutes": 60
}
```

**Response:**
```json
{
  "message": "Campaign started",
  "job_id": "campaign_a1b2c3d4"
}
```

### POST `/reminders/create`
Schedule a one-off reminder email.

**Request Body:**
```json
{
  "target_email": "manager@startup.in",
  "sender_email": "compliance_bot@gmail.com",
  "app_password": "your-app-password",
  "message": "Review the new RBI guidelines",
  "run_date": "2026-05-08T14:30:00"
}
```

**Response:**
```json
{
  "message": "Reminder scheduled",
  "job_id": "reminder_e5f6g7h8"
}
```

### GET `/track/{tracking_id}.gif`
Invisible tracking pixel endpoint. Called when email is opened.

**Response:** 1x1 transparent GIF image

**Side Effect:** Updates email status to "Opened" in database

### GET `/stats`
Get email delivery statistics.

**Response:**
```json
{
  "logs": [
    ["uuid-1", "manager@startup.in", "RBI New Guidelines", "Opened", "2026-05-08 10:30:00"],
    ["uuid-2", "manager@startup.in", "Payment Regulation Update", "Sent", "2026-05-08 11:45:00"]
  ]
}
```

---

## 🗄️ Database Schema

### `sentinel.db` (Main Database)

#### Table: `email_logs`
Tracks all sent emails and their status.

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT (PK) | Unique tracking ID (UUID) |
| `to_email` | TEXT | Recipient email address |
| `subject` | TEXT | Email subject line |
| `status` | TEXT | Status: "Sent" or "Opened" |
| `timestamp` | DATETIME | When email was sent |

#### Table: `processed_articles`
Prevents duplicate processing of articles.

| Column | Type | Description |
|--------|------|-------------|
| `link` | TEXT (PK) | Article URL (unique identifier) |

### `jobs.sqlite` (Job Store)
Managed by APScheduler for job persistence.

### `ai_decisions_log.json` (AI Log)
JSON array of all AI decisions:

```json
[
  {
    "timestamp": "2026-05-08 10:30:00",
    "title": "RBI Issues New Digital Payment Guidelines",
    "decision": {
      "risk_level": "High",
      "summary": "New regulations require additional KYC for digital payments above ₹50,000. Startups must update compliance processes within 30 days.",
      "action_required": true,
      "recommendation": "Review current KYC processes and implement additional verification for high-value transactions."
    }
  }
]
```

---

## 🔄 How It Works

### Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    1. USER CREATES CAMPAIGN                  │
│              (via Streamlit UI or API Call)                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              2. APSCHEDULER CREATES BACKGROUND JOB           │
│         (Runs every X minutes as configured)                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              3. WATCHDOG JOB EXECUTES (core_logic.py)        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Step 3.1: Fetch RSS Feed                             │  │
│  │ • Parse RSS using feedparser                         │  │
│  │ • Get latest 5 entries                              │  │
│  │ • Check for duplicates in DB                        │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                        │
│                     ▼                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Step 3.2: Extract Article Content                    │  │
│  │ • Download article using trafilatura                 │  │
│  │ • Extract clean text body                           │  │
│  │ • Skip if extraction fails                          │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                        │
│                     ▼                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Step 3.3: AI Risk Analysis                           │  │
│  │ • Send title + body to Ollama                        │  │
│  │ • Get JSON response with:                            │  │
│  │   - risk_level (Low/Medium/High/Critical)           │  │
│  │   - summary (2-sentence impact)                     │  │
│  │   - action_required (boolean)                       │  │
│  │   - recommendation (actionable advice)                │  │
│  │ • Save decision to JSON log                         │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                        │
│                     ▼                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Step 3.4: Conditional Email Sending                 │  │
│  │ • Check if action_required OR risk_level is High/    │  │
│  │   Critical                                           │  │
│  │ • If yes:                                            │  │
│  │   - Generate unique tracking ID (UUID)              │  │
│  │   - Insert email log with "Sent" status             │  │
│  │   - Send email with tracking pixel                  │  │
│  │ • Mark article as processed in DB                   │  │
│  └──────────────────┬───────────────────────────────────┘  │
└─────────────────────┼──────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              4. EMAIL SENT WITH TRACKING PIXEL               │
│                                                              │
│  HTML Email Contains:                                        │
│  • Risk level in subject line                                │
│  • AI summary and recommendations                           │
│  • Invisible 1x1 tracking pixel:                            │
│    <img src="http://127.0.0.1:8000/track/{uuid}.gif" />     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ (When recipient opens email)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              5. TRACKING PIXEL LOADED                        │
│                                                              │
│  • Browser requests: GET /track/{uuid}.gif                   │
│  • FastAPI endpoint updates DB: status = "Opened"           │
│  • Returns 1x1 transparent GIF                               │
└─────────────────────────────────────────────────────────────┘
```

### Detailed Step-by-Step Process

#### Phase 1: Campaign Creation
1. User configures SMTP credentials in Streamlit sidebar
2. User selects RSS feed and interval
3. Streamlit sends POST request to `/campaigns/create`
4. FastAPI creates APScheduler job with interval trigger
5. Job ID returned to user for tracking

#### Phase 2: Scheduled Execution
1. APScheduler triggers `watchdog_job()` function
2. Function receives campaign configuration (dict)
3. Job runs in background, doesn't block API

#### Phase 3: RSS Feed Processing
1. `get_feed_entries()` called with feed URL
2. feedparser parses RSS XML
3. Returns list of feed entries (title, link, published, etc.)
4. Each entry checked against `processed_articles` table
5. Only new articles proceed to next step

#### Phase 4: Content Extraction
1. `extract_article_body()` called with article URL
2. trafilatura downloads HTML from URL
3. Extracts main content, removes ads/navigation
4. Returns clean text (or None if failed)
5. Failed extractions are skipped with warning log

#### Phase 5: AI Analysis
1. `analyze_compliance_risk()` called with title and body
2. Constructs prompt with role (RegTech Compliance Analyst)
3. Limits body to 1500 characters (token management)
4. Sends to Ollama via `ollama.generate()`
5. Requests JSON format response
6. Parses JSON response, handles markdown formatting
7. Returns decision dict with 4 keys:
   - `risk_level`: String enum
   - `summary`: 2-sentence impact analysis
   - `action_required`: Boolean
   - `recommendation`: Actionable advice
8. On error, returns fallback decision

#### Phase 6: Decision Logging
1. `save_decision_to_json()` called with log data
2. Creates `ai_decisions_log.json` if doesn't exist
3. Loads existing logs (or empty array)
4. Appends new decision with timestamp
5. Writes back to file with pretty formatting
6. Logs success/failure to console

#### Phase 7: Conditional Emailing
1. Checks if `action_required` is True
2. OR checks if `risk_level` is "High" or "Critical"
3. If condition met:
   - Generates UUID for tracking
   - Inserts row into `email_logs` with status "Sent"
   - Calls `send_tracked_email()`
4. If condition not met:
   - Logs article as processed but doesn't email
   - Still saves AI decision for audit

#### Phase 8: Email Sending
1. `send_tracked_email()` called with all parameters
2. Constructs tracking pixel URL with UUID
3. Creates HTML email body with:
   - Styled header with risk color
   - Subject line
   - Risk level badge
   - AI summary
   - Recommendation
   - Tracking pixel (invisible)
4. Creates MIME multipart message
5. Attaches HTML body
6. Connects to Gmail SMTP (port 587)
7. Starts TLS encryption
8. Authenticates with app password
9. Sends message
10. Logs success/failure

#### Phase 9: Email Tracking
1. Recipient opens email in email client
2. Email client loads images (including tracking pixel)
3. Browser makes GET request to `/track/{uuid}.gif`
4. FastAPI endpoint receives request
5. Updates `email_logs` table: status = "Opened"
6. Returns 1x1 transparent GIF (43 bytes)
7. User can see updated status in Dashboard

#### Phase 10: Analytics & Reporting
1. User clicks "Refresh Stats" in Dashboard
2. Streamlit calls GET `/stats`
3. FastAPI queries `email_logs` table
4. Returns all logs ordered by timestamp
5. Streamlit displays in DataFrame
6. Status color-coded (green=Opened, orange=Sent)
7. User can track engagement over time

---

## 🐛 Troubleshooting

### Common Issues and Solutions

#### 1. Import Errors: "Module not found"

**Problem:**
```
ImportError: No module named 'feedparser'
```

**Solution:**
```bash
# Make sure virtual environment is activated
.\em\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```

#### 2. Ollama Connection Failed

**Problem:**
```
Ollama reasoning failed: Connection refused
```

**Solution:**
```bash
# Check if Ollama is running
ollama list

# Start Ollama service
# Windows: Ollama should be running in background
# Check system tray for Ollama icon

# Test connection
curl http://localhost:11434/api/generate
```

#### 3. Email Sending Failed

**Problem:**
```
SMTP Email failed to send: Authentication failed
```

**Solution:**
- Verify you're using App Password, not regular password
- Enable 2-Factor Authentication on Google Account
- Generate new App Password from Google Security settings
- Check if Gmail allows less secure apps (use App Password instead)

#### 4. RSS Feed Not Updating

**Problem:**
Campaign running but no new emails being sent.

**Solution:**
```bash
# Check if articles are being processed
# Open ai_decisions_log.json to see recent decisions

# Check processed_articles table
sqlite3 sentinel.db "SELECT * FROM processed_articles LIMIT 10;"

# Clear processed articles to re-process (careful!)
sqlite3 sentinel.db "DELETE FROM processed_articles;"
```

#### 5. Tracking Pixel Not Working

**Problem:**
Email status stays "Sent" even after opening.

**Solution:**
- Check if API is running on correct URL
- Verify tracking pixel URL in email HTML
- Some email clients block images by default
- User may need to "display images" in email client
- Check if `http://127.0.0.1:8000` is accessible from recipient's network
- For production, use public domain instead of localhost

#### 6. Streamlit Can't Connect to API

**Problem:**
```
Make sure FastAPI backend is running on port 8000.
```

**Solution:**
```bash
# Check if main.py is running
# Look for terminal with: Uvicorn running on http://127.0.0.1:8000

# Start API if not running
python main.py

# Check if port is in use
netstat -ano | findstr :8000
```

#### 7. Database Locked Error

**Problem:**
```
sqlite3.OperationalError: database is locked
```

**Solution:**
- Close all database connections
- Restart the application
- Delete `.db-wal` and `.db-shm` files if they exist
- Only one process should write to database at a time

#### 8. AI Returns Invalid JSON

**Problem:**
```
JSONDecodeError: Expecting value: line 1 column 1
```

**Solution:**
- The code already handles this with fallback response
- Check Ollama model output format
- Try different model: `llama2`, `mistral`
- Adjust prompt to be more strict about JSON format

#### 9. Virtual Environment Activation Issues (Windows)

**Problem:**
```
cannot be loaded because running scripts is disabled
```

**Solution:**
```powershell
# Run in PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then try activation again
.\em\Scripts\Activate.ps1
```

#### 10. Port Already in Use

**Problem:**
```
OSError: [Errno 48] Address already in use
```

**Solution:**
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# OR use different port in main.py
# Change: uvicorn.run(app, host="127.0.0.1", port=8001)
```

### Debug Mode

Enable detailed logging by modifying `core_logic.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    format="%(asctime)s - [%(levelname)s] - %(message)s"
)
```

### Testing Components Individually

```python
# Test RSS parsing
python -c "from core_logic import get_feed_entries; print(get_feed_entries('https://www.rbi.org.in/notifications_rss.xml'))"

# Test Ollama
python -c "import ollama; print(ollama.generate(model='gpt-oss:20b-cloud', prompt='Hello'))"

# Test Email (use your credentials)
python -c "from core_logic import send_tracked_email; send_tracked_email('to@example.com', 'from@gmail.com', 'app-pass', 'Test', {'risk_level': 'Low', 'summary': 'Test', 'recommendation': 'Test'}, 'test-id', 'http://127.0.0.1:8000')"
```

---

## 📝 Development Notes

### Code Structure

- **core_logic.py**: Pure business logic, no framework dependencies
- **main.py**: FastAPI application, database, and scheduling
- **app.py**: Streamlit UI, user interaction
- **requirements.txt**: Python dependencies

### Design Patterns

- **Separation of Concerns**: UI, API, and business logic are separate
- **Dependency Injection**: Configuration passed as parameters
- **Error Handling**: Try-except blocks with logging
- **Idempotency**: Duplicate prevention via database checks

### Future Enhancements

- [ ] Support for multiple email providers (Outlook, SendGrid)
- [ ] Webhook notifications for real-time alerts
- [ ] Multi-language support for AI analysis
- [ ] Dashboard with charts and analytics
- [ ] User authentication and authorization
- [ ] Team management and role-based access
- [ ] Integration with Slack/Teams notifications
- [ ] PDF report generation for compliance audits
- [ ] Historical trend analysis of regulatory changes
- [ ] Custom risk threshold configuration

---

## 📄 License

This project is for educational and demonstration purposes.

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

## 📞 Support

For issues or questions:
- Check the Troubleshooting section above
- Review the API documentation
- Check logs in the terminal
- Examine `ai_decisions_log.json` for AI errors

---

## 🙏 Acknowledgments

- **Ollama** - Local AI inference
- **FastAPI** - Modern Python web framework
- **Streamlit** - Rapid UI development
- **RBI** - Regulatory data source
- **Trafilatura** - Web content extraction

---

**Built with ❤️ for the Indian RegTech Community**