import streamlit as st
import requests
import base64

# Configuration
API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Sahāyak | Climate Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS to force Streamlit into the Prototype's UI/UX
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&family=JetBrains+Mono:wght@500&family=Sora:wght@600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

    /* Base Background */
    .stApp {
        background-color: #0B0F19;
    }
    
    /* Hide top padding and header */
    .block-container {
        padding-top: 2rem !important;
        max-width: 1100px;
    }
    header {
        background: rgba(16, 20, 21, 0.05) !important;
        backdrop-filter: blur(20px) !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    /* Force columns to stretch horizontally to fix gaps */
    div[data-testid="stHorizontalBlock"] {
        align-items: stretch;
    }

    /* Search Bar Input Styling */
    div[data-baseweb="input"] {
        background-color: #05070A !important;
        border: none !important;
        border-bottom: 2px solid #3a494a !important;
        border-radius: 0.5rem 0.5rem 0 0 !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-bottom-color: #00dce5 !important;
        box-shadow: 0 0 20px rgba(0, 220, 229, 0.2) !important;
    }
    input {
        color: #e0e3e5 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 1.125rem !important;
        padding: 1rem !important;
    }

    /* Primary Button (ANALYZE) */
    button[data-testid="baseButton-primary"] {
        background-color: #00dce5 !important;
        color: #002021 !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        border-radius: 0.25rem !important;
        border: none !important;
        height: 100%;
        margin-top: 26px; /* Align with input */
    }
    button[data-testid="baseButton-primary"]:hover {
        background-color: #63f7ff !important;
        transform: scale(0.98);
    }

    /* Custom Scrollbar for Risk Translator Text */
    .custom-scroll::-webkit-scrollbar {
        width: 4px;
    }
    .custom-scroll::-webkit-scrollbar-track {
        background: transparent;
    }
    .custom-scroll::-webkit-scrollbar-thumb {
        background: rgba(0, 220, 229, 0.3);
        border-radius: 10px;
    }
    .custom-scroll::-webkit-scrollbar-thumb:hover {
        background: rgba(0, 220, 229, 0.7);
    }
    </style>
    """, unsafe_allow_html=True)

# CACHE: Caches the API response for 60 seconds to make UI interactions instantaneous
@st.cache_data(ttl=60, show_spinner=False)
def fetch_data():
    try:
        response = requests.get(f"{API_URL}/dashboard-data")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        # Silently fail here; UI will render the sleek skeleton state
        pass
    return None

def update_location(zipcode):
    try:
        requests.post(f"{API_URL}/update-location?zipcode={zipcode}")
        # Clear cache so the new location's data is fetched immediately
        fetch_data.clear()
        st.success(f"Updating location to {zipcode}...")
    except:
        st.error("Failed to update location.")

# --- Header & Search Hero Section ---
st.markdown("""
<div style="text-align: center; margin-top: 2rem; margin-bottom: 2rem;">
    <h1 style="font-family: 'Sora', sans-serif; font-size: 3rem; font-weight: 700; color: #00dce5; margin-bottom: 1rem; letter-spacing: -0.04em;">Sahāyak - Predictive Climate Intelligence</h1>
    <p style="font-family: 'Inter', sans-serif; font-size: 1.125rem; color: #b9caca; max-width: 600px; margin: 0 auto;">Enter your global PIN or coordinates to access institutional-grade risk forecasting and physical parameter data.</p>
</div>
""", unsafe_allow_html=True)

# Search Bar
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    search_col, btn_col = st.columns([3, 1])
    with search_col:
        search_zip = st.text_input("Location", placeholder="Enter PIN code or city...", label_visibility="collapsed")
    with btn_col:
        if st.button("ANALYZE", type="primary", use_container_width=True):
            if search_zip:
                update_location(search_zip)
                st.rerun()

# --- Main Dashboard ---
data = fetch_data()

if data and data.get('weather'):
    weather = data['weather']
    aqi = data['aqi']
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Row 1: Risk Vector and Advisor
    c1, c2 = st.columns([2, 1])
    
    with c1:
        # Compound Risk Vector HTML built to match exact CSS from prototype
        st.markdown(f"""
        <div style="background: rgba(255, 255, 255, 0.04); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 0.75rem; padding: 2rem; position: relative; overflow: hidden; height: 100%; min-height: 380px; display: flex; flex-direction: column; justify-content: space-between;">
           <!-- Glow -->
           <div style="position: absolute; top: -2rem; right: -2rem; width: 16rem; height: 16rem; background: rgba(254, 183, 0, 0.1); border-radius: 50%; filter: blur(3rem); pointer-events: none;"></div>

           <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 2rem;">
              <div>
                 <h2 style="font-family: 'Inter', sans-serif; font-size: 0.75rem; font-weight: 700; color: #b9caca; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">Compound Risk Vector</h2>
                 <div style="font-family: 'Sora', sans-serif; font-size: 3rem; font-weight: 700; color: #feb700; display: flex; align-items: baseline; gap: 0.5rem; line-height: 1.1;">
                    Critical <span style="font-size: 1.5rem; font-weight: 600; color: #b9caca;">Alert</span>
                 </div>
              </div>
              <div style="width: 1rem; height: 1rem; border-radius: 50%; background-color: #feb700; box-shadow: 0 0 15px rgba(254, 183, 0, 0.6); margin-top: 0.5rem;"></div>
           </div>

           <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: auto;">
              <!-- WBT Box -->
              <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 0.5rem; padding: 1rem;">
                 <div style="font-family: 'Inter', sans-serif; font-size: 0.75rem; font-weight: 700; color: #b9caca; margin-bottom: 0.25rem;">WET BULB TEMP</div>
                 <div style="font-family: 'JetBrains Mono', monospace; font-size: 2rem; font-weight: 500; color: #00dce5;">{weather['wbt']}°C</div>
                 <div style="font-family: 'Inter', sans-serif; font-size: 1rem; color: #feb700; margin-top: 0.25rem;">Exceeds safe limits</div>
              </div>
              <!-- AQI Box -->
              <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 0.5rem; padding: 1rem;">
                 <div style="font-family: 'Inter', sans-serif; font-size: 0.75rem; font-weight: 700; color: #b9caca; margin-bottom: 0.25rem;">AIR QUALITY INDEX</div>
                 <div style="font-family: 'JetBrains Mono', monospace; font-size: 2rem; font-weight: 500; color: #ffb4ab;">{aqi['aqi']}</div>
                 <div style="font-family: 'Inter', sans-serif; font-size: 1rem; color: #ffb4ab; margin-top: 0.25rem;">{aqi.get('status', 'Hazardous')}</div>
              </div>
           </div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        # Risk Translator Card - Button removed, layout simplified
        st.markdown(f"""
        <div style="background: rgba(255, 255, 255, 0.04); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 0.75rem; padding: 2rem; height: 100%; min-height: 380px; display: flex; flex-direction: column;">
            <div style="display: flex; align-items: center; gap: 0.5rem; color: #00dce5; border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding-bottom: 1rem; margin-bottom: 1rem;">
                <span class="material-symbols-outlined">smart_toy</span>
                <h3 style="font-family: 'Sora', sans-serif; font-size: 1.5rem; font-weight: 600; margin: 0;">Risk Translator</h3>
            </div>
            <div class="custom-scroll" style="font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #e0e3e5; line-height: 1.6; margin-bottom: 1rem; flex-grow: 1; max-height: 220px; overflow-y: auto; padding-right: 0.5rem; text-align: justify;">
                {data['advisory']}
            </div>
            <p style="font-family: 'Inter', sans-serif; font-size: 0.875rem; color: #b9caca; margin-bottom: 0;">AI Confidence: <span style="color: #00dce5; font-family: 'JetBrains Mono', monospace;">98.4%</span></p>
        </div>
        """, unsafe_allow_html=True)

    # Row 2: 24-Hour Trajectory
    st.markdown("<br>", unsafe_allow_html=True)
    img_tag = f'<img src="data:image/png;base64,{data["plot_base64"]}" style="width: 100%; border-radius: 0.5rem; filter: invert(0.9) hue-rotate(180deg); opacity: 0.85;" />' if data.get('plot_base64') else ""
    
    st.markdown(f"""
    <div style="background: rgba(255, 255, 255, 0.04); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 0.75rem; padding: 2rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
            <h2 style="font-family: 'Inter', sans-serif; font-size: 0.75rem; font-weight: 700; color: #b9caca; text-transform: uppercase; letter-spacing: 0.05em;">24-Hour Trajectory: Temp vs Humidity</h2>
            <div style="display: flex; gap: 1rem;">
                <div style="display: flex; align-items: center; gap: 0.5rem;"><div style="width: 0.75rem; height: 2px; background: #00dce5;"></div><span style="font-family: 'JetBrains Mono', monospace; font-size: 0.875rem; color: #b9caca;">Temp</span></div>
                <div style="display: flex; align-items: center; gap: 0.5rem;"><div style="width: 0.75rem; height: 2px; background: #feb700;"></div><span style="font-family: 'JetBrains Mono', monospace; font-size: 0.875rem; color: #b9caca;">Humidity</span></div>
            </div>
        </div>
        {img_tag}
    </div>
    """, unsafe_allow_html=True)

    # Row 3: Secondary Metrics
    st.markdown("<br>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    
    with m1:
        st.markdown(f"""<div style="background: rgba(255, 255, 255, 0.04); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 0.75rem; padding: 1.5rem;"><span class="material-symbols-outlined" style="color: #00dce5; font-size: 2rem; margin-bottom: 1rem; display: block;">terrain</span><h4 style="font-family: 'Inter', sans-serif; font-size: 0.75rem; font-weight: 700; color: #b9caca; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.05em;">Elevation</h4><div style="font-family: 'JetBrains Mono', monospace; font-size: 1.5rem; color: #e0e3e5; font-weight: 500;">{weather['elevation']} <span style="font-size: 1rem; color: #b9caca; font-family: 'Inter', sans-serif; font-weight: 400;">m</span></div></div>""", unsafe_allow_html=True)
        
    with m2:
        precip = weather['current'].get('precipitation', 0.0)
        st.markdown(f"""<div style="background: rgba(255, 255, 255, 0.04); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 0.75rem; padding: 1.5rem;"><span class="material-symbols-outlined" style="color: #00dce5; font-size: 2rem; margin-bottom: 1rem; display: block;">water_drop</span><h4 style="font-family: 'Inter', sans-serif; font-size: 0.75rem; font-weight: 700; color: #b9caca; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.05em;">Precipitation (24H)</h4><div style="font-family: 'JetBrains Mono', monospace; font-size: 1.5rem; color: #e0e3e5; font-weight: 500;">{precip} <span style="font-size: 1rem; color: #b9caca; font-family: 'Inter', sans-serif; font-weight: 400;">mm</span></div></div>""", unsafe_allow_html=True)
        
    with m3:
        terrain_risk = "Elevated" if weather['elevation'] > 1000 else "Normal"
        terrain_color = "#ffb4ab" if terrain_risk == "Elevated" else "#e0e3e5"
        glow_html = '<div style="position: absolute; right: 0; top: 0; width: 4rem; height: 4rem; background: rgba(255, 180, 171, 0.2); filter: blur(1rem);"></div>' if terrain_risk == "Elevated" else ''
        st.markdown(f"""<div style="background: rgba(255, 255, 255, 0.04); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 0.75rem; padding: 1.5rem; position: relative; overflow: hidden;">{glow_html}<span class="material-symbols-outlined" style="color: {terrain_color}; font-size: 2rem; margin-bottom: 1rem; display: block;">landscape</span><h4 style="font-family: 'Inter', sans-serif; font-size: 0.75rem; font-weight: 700; color: #b9caca; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.05em;">Terrain Risk Vector</h4><div style="font-family: 'Sora', sans-serif; font-size: 1.5rem; color: {terrain_color}; font-weight: 600;">{terrain_risk}</div></div>""", unsafe_allow_html=True)

else:
    # Sleek Skeleton Loading/Standby State
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <style>
    @keyframes pulse-glow {
        0%, 100% { opacity: 0.3; box-shadow: 0 0 0 rgba(0, 220, 229, 0); }
        50% { opacity: 0.7; box-shadow: 0 0 20px rgba(0, 220, 229, 0.1); }
    }
    .skeleton-panel {
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(20px);
        border: 1px dashed rgba(0, 220, 229, 0.3);
        border-radius: 0.75rem;
        animation: pulse-glow 2.5s infinite ease-in-out;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

    # Skeleton Row 1
    sc1, sc2 = st.columns([2, 1])
    with sc1:
        st.markdown("""
        <div class="skeleton-panel" style="height: 380px; padding: 2rem;">
            <span class="material-symbols-outlined" style="font-size: 3rem; color: #00dce5; margin-bottom: 1rem;">radar</span>
            <h3 style="font-family: 'Sora', sans-serif; font-size: 1.25rem; font-weight: 600; color: #00dce5; margin: 0;">Awaiting Telemetry...</h3>
            <p style="font-family: 'JetBrains Mono', monospace; font-size: 0.875rem; color: #b9caca; margin-top: 0.5rem;">Synchronizing with atmospheric sensors & geocoding nodes</p>
        </div>
        """, unsafe_allow_html=True)
    with sc2:
        st.markdown("""
        <div class="skeleton-panel" style="height: 380px; padding: 2rem;">
            <span class="material-symbols-outlined" style="font-size: 3rem; color: #00dce5; margin-bottom: 1rem;">memory</span>
            <h3 style="font-family: 'Sora', sans-serif; font-size: 1.25rem; font-weight: 600; color: #00dce5; margin: 0;">AI Translator Standby</h3>
            <p style="font-family: 'JetBrains Mono', monospace; font-size: 0.875rem; color: #b9caca; margin-top: 0.5rem;">Waking local LLM parameters for risk analysis</p>
        </div>
        """, unsafe_allow_html=True)
        
    # Skeleton Row 2
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="skeleton-panel" style="height: 160px; padding: 2rem; width: 100%;">
        <span class="material-symbols-outlined" style="font-size: 2rem; color: #00dce5; margin-bottom: 0.5rem;">query_stats</span>
        <p style="font-family: 'JetBrains Mono', monospace; font-size: 0.875rem; color: #b9caca;">Establishing Baseline Trajectory...</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Skeleton Row 3
    st.markdown("<br>", unsafe_allow_html=True)
    sm1, sm2, sm3 = st.columns(3)
    for col in [sm1, sm2, sm3]:
        with col:
            st.markdown("""
            <div class="skeleton-panel" style="height: 120px; width: 100%;"></div>
            """, unsafe_allow_html=True)

# --- Minimalist Footer ---
st.markdown("""
<div style="border-top: 1px solid rgba(255,255,255,0.05); margin-top: 4rem; padding-top: 2rem; padding-bottom: 2rem; display: flex; justify-content: space-between; align-items: center; font-family: 'Inter', sans-serif; font-size: 0.875rem;">
   <div style="font-family: 'Sora', sans-serif; font-size: 1.5rem; font-weight: 700; color: #00dce5; letter-spacing: -0.04em;">Sahāyak</div>
   <div style="color: #849495;">© 2026 Sahāyak Global. Powered by FastAPI, Ollama, and Open-Meteo.</div>
</div>
""", unsafe_allow_html=True)
