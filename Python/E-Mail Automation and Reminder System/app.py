import streamlit as st
import requests
import json
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="RegTech Sentinel", page_icon="🛡️", layout="wide")

st.title("🛡️ RegTech Agentic Sentinel")
st.markdown("Automated compliance monitoring, reasoning, and outreach pipeline for the Indian Market.")

# Sidebar for global configuration
with st.sidebar:
    st.header("⚙️ SMTP Configuration")
    st.info("Credentials are used per-request and not permanently stored.")
    sender_email = st.text_input("Your Email (Sender)", "compliance_bot@gmail.com")
    app_pwd = st.text_input("App Password", type="password")
    target_email = st.text_input("Target Email (Receiver)", "manager@startup.in")

# Tabs for the UI
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard & Tracking", "📡 Create Campaign", "⏰ Manual Reminders", "🧠 AI Decisions Log"])

with tab1:
    st.header("Email Delivery & Tracking")
    if st.button("Refresh Stats"):
        try:
            res = requests.get(f"{API_URL}/stats")
            logs = res.json().get("logs", [])
            if logs:
                df = pd.DataFrame(logs, columns=["Tracking ID", "Target", "Subject", "Status", "Timestamp"])
                # Color code statuses
                def color_status(val):
                    color = 'green' if val == 'Opened' else 'orange'
                    return f'color: {color}; font-weight: bold;'
                
                # POINT 2 FIX: Updated from applymap() to map()
                st.dataframe(df.style.map(color_status, subset=['Status']), use_container_width=True)
            else:
                st.write("No emails sent yet.")
        except Exception as e:
            st.error("Make sure FastAPI backend is running on port 8000.")

with tab2:
    st.header("Schedule a Regulatory Watchdog")
    st.markdown("Set up a cron job to monitor RSS feeds and trigger the LLM.")
    
    feed_url = st.selectbox("Select RegTech Feed", [
        "https://www.rbi.org.in/notifications_rss.xml", # RBI Notifications
        "https://www.rbi.org.in/pressreleases_rss.xml",  # RBI Press Releases
        "Custom URL"
    ])
    
    if feed_url == "Custom URL":
        feed_url = st.text_input("Enter Custom RSS URL")
    
    interval = st.number_input("Check Interval (Minutes)", min_value=1, max_value=10080, value=60, step=5)
    
    if st.button("Deploy Sentinel Agent"):
        if sender_email and app_pwd:
            payload = {
                "feed_url": feed_url,
                "target_email": target_email,
                "sender_email": sender_email,
                "app_password": app_pwd,
                "interval_minutes": interval
            }
            res = requests.post(f"{API_URL}/campaigns/create", json=payload)
            st.success(f"Success: {res.json()['message']} (ID: {res.json()['job_id']})")
        else:
            st.error("Please configure SMTP in the sidebar first.")

with tab3:
    st.header("Schedule a Team Reminder")
    st.markdown("Set a one-off automated email reminder.")
    
    rem_message = st.text_area("Reminder Message")
    rem_date = st.date_input("Date")
    rem_time = st.time_input("Time")
    
    if st.button("Schedule Reminder"):
        dt_str = f"{rem_date}T{rem_time}"
        payload = {
            "target_email": target_email,
            "sender_email": sender_email,
            "app_password": app_pwd,
            "message": rem_message,
            "run_date": dt_str
        }
        res = requests.post(f"{API_URL}/reminders/create", json=payload)
        st.success("Reminder Scheduled!")

with tab4:
    st.header("🧠 Ollama Reasoning Log")
    st.markdown("View the local AI's risk assessments.")
    try:
        with open("ai_decisions_log.json", "r") as f:
            decisions = json.load(f)
            # Display latest first
            st.json(list(reversed(decisions)))
    except FileNotFoundError:
        st.info("No AI decisions logged yet. The watchdog needs to process an article first.")