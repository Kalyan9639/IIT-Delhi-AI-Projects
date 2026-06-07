import streamlit as st
import pandas as pd
import numpy as np
import joblib
import json
import os
import plotly.express as px
import plotly.graph_objects as go

# Set page configuration with a modern, wide layout and theme styling
st.set_page_config(
    page_title="Sales Forecasting & Demand Prediction Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished, premium layout elements
st.markdown("""
<style>
    /* Styling headers and metrics card designs */
    .metric-card {
        background-color: rgba(250, 250, 250, 0.9);
        border: 1px solid #e6e9ef;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.02);
        margin-bottom: 15px;
    }
    .dark .metric-card {
        background-color: rgba(30, 30, 30, 0.9);
        border: 1px solid #2d3139;
    }
    .metric-header {
        font-size: 0.9rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1e293b;
    }
    .dark .metric-value {
        color: #f1f5f9;
    }
    .metric-desc {
        font-size: 0.8rem;
        color: #94a3b8;
        margin-top: 5px;
    }
    /* Section headers alignment */
    .section-title {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 20px;
        border-left: 5px solid #4f46e5;
        padding-left: 10px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 1. LOAD ASSETS (CACHED FOR SPEED)
# -----------------------------------------------------------------------------

@st.cache_data
def load_data():
    """Load the cleaned dataset used for computing averages and historical profiles."""
    if os.path.exists("final_data.csv"):
        df = pd.read_csv("final_data.csv")
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df
    elif os.path.exists("sales_data.csv"):
        # Fallback to original dataset if final_data is not run yet
        df = pd.read_csv("sales_data.csv")
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df
    else:
        return None

@st.cache_resource
def load_prediction_model():
    """Load the pre-trained XGBoost Model and categorical encodings."""
    model, encodings = None, None
    
    # Load Model
    if os.path.exists("xgboost_demand_model.joblib"):
        try:
            model = joblib.load("xgboost_demand_model.joblib")
            st.success("✅ Model loaded successfully!")
        except Exception as e:
            st.error(f"❌ Error loading model: {e}. Running on simulated fallback model.")
            model = None
    else:
        st.warning("⚠️ 'xgboost_demand_model.joblib' not found. Please make sure to run your model training file first. Running on simulated fallback model.")
    
    # Load Encodings
    if os.path.exists("target_encoding_maps.json"):
        try:
            with open("target_encoding_maps.json", "r") as f:
                encodings = json.load(f)
            st.success("✅ Target encodings loaded successfully!")
        except Exception as e:
            st.error(f"❌ Error loading encodings: {e}. Categorical mapping will run on default mean levels.")
            encodings = None
    else:
        st.warning("⚠️ 'target_encoding_maps.json' not found. Categorical mapping will run on default mean levels.")
        
    return model, encodings

# Load data structures
df_raw = load_data()
model, encodings = load_prediction_model()

# Debug: Check if model loaded
if model is None:
    st.warning("⚠️ Using fallback simulation model. For accurate predictions, train and save the XGBoost model first.")
else:
    st.success("✅ XGBoost model is active for predictions.")

# -----------------------------------------------------------------------------
# 2. DEFAULT FALLBACK VALUES
# -----------------------------------------------------------------------------
# If columns are completely missing or not inputted, these are the global means
GLOBAL_MEANS = {
    'Price': 62.5,
    'Discount': 9.2,
    'Competitor Pricing': 68.3,
    'Demand_Lag_1': 105.0,
    'Demand_Lag_7': 105.0,
    'Rolling_Mean_7': 105.0,
    'Price_Diff': -5.8,
    'Discount_Rate': 0.092,
    'Inventory_Buffer_Ratio': 2.3,
    'Price_Ratio': 0.91,
    'Day_of_Week': 3,
    'Month': 6,
    'Quarter': 2,
    'Is_Weekend': 0,
    'Is_Month_Start': 0,
    'Is_Month_End': 0,
    'Promoted_Weekend': 0,
    'Epidemic': 0
}

# Overwrite global means with true database calculations if final_data exists
if df_raw is not None:
    for col in GLOBAL_MEANS.keys():
        if col in df_raw.columns:
            if df_raw[col].dtype in [np.float64, np.int64, np.int32]:
                GLOBAL_MEANS[col] = float(df_raw[col].mean())

# -----------------------------------------------------------------------------
# 3. DASHBOARD FRONT-END STRUCTURE
# -----------------------------------------------------------------------------

# Title Banner
st.title("📈 Retail Sales Forecasting & Demand Prediction Dashboard")
st.write("An enterprise AI forecasting module leveraging XGBoost and secure target encoding to optimize supply chains.")

# Sidebar Controls
st.sidebar.header("🕹️ Forecast Configuration Engine")
st.sidebar.write("Choose a selection strategy to populate base historical configurations:")

if df_raw is not None:
    # Mode selection
    ui_mode = st.sidebar.radio("Data Input Mode", ["Select Store & Product (Database Loaded)", "Manual Input Sandbox"])
else:
    ui_mode = "Manual Input Sandbox"
    st.sidebar.warning("Running in Standalone Sandbox. Connect 'final_data.csv' to unlock store-level profiles.")

# Variable instantiation
selected_store = "S001"
selected_product = "P0001"
active_category = "Groceries"
active_region = "North"

# Default placeholders for UI controls
default_price = GLOBAL_MEANS['Price']
default_comp_price = GLOBAL_MEANS['Competitor Pricing']
default_discount = int(GLOBAL_MEANS['Discount'])
default_promo = 0
default_weather = "Sunny"
default_season = "Summer"
default_epidemic = 0
default_inventory = 150

# Retrieve values if database mode selected
if ui_mode == "Select Store & Product (Database Loaded)":
    # Multi-dimensional cascading dropdown selectors
    stores = sorted(df_raw['Store ID'].dropna().unique().tolist())
    selected_store = st.sidebar.selectbox("Select Store", stores)
    
    # Filter products available at this store
    available_products = sorted(df_raw[df_raw['Store ID'] == selected_store]['Product ID'].dropna().unique().tolist())
    selected_product = st.sidebar.selectbox("Select Product ID", available_products)
    
    # Get the latest entry in database to populate defaults dynamically
    latest_record = df_raw[(df_raw['Store ID'] == selected_store) & (df_raw['Product ID'] == selected_product)].sort_values('Date').iloc[-1]
    
    # Auto-extract non-editable fields
    active_category = latest_record['Category']
    active_region = latest_record['Region']
    
    # Assign inputs dynamically
    default_price = float(latest_record['Price'])
    default_comp_price = float(latest_record['Competitor Pricing'])
    default_discount = int(latest_record['Discount'])
    default_promo = int(latest_record['Promotion'])
    default_weather = latest_record['Weather Condition']
    default_season = latest_record['Seasonality']
    default_epidemic = int(latest_record['Epidemic'])
    default_inventory = int(latest_record['Inventory Level'])
    
    st.sidebar.success(f"📍 Profile Found!\nCategory: **{active_category}**\nRegion: **{active_region}**")

else:
    # Manual Input Selectors
    active_category = st.sidebar.selectbox("Product Category", ["Groceries", "Electronics", "Clothing", "Toys", "Furniture"])
    active_region = st.sidebar.selectbox("Store Region", ["North", "South", "East", "West"])

st.sidebar.markdown("---")
st.sidebar.subheader("Adjust Market Parameters")

# Inputs for parameters that influence forecast
input_date = st.sidebar.date_input("Prediction Horizon Date", pd.Timestamp.now())
input_price = st.sidebar.number_input("Selling Price ($)", value=default_price, min_value=0.1, step=1.0)
input_comp_price = st.sidebar.number_input("Competitor Pricing ($)", value=default_comp_price, min_value=0.1, step=1.0)
input_discount = st.sidebar.slider("Discount (%)", min_value=0, max_value=100, value=default_discount, step=5)
input_promo = st.sidebar.selectbox("Active Promotion?", [0, 1], index=int(default_promo))
input_weather = st.sidebar.selectbox("Weather Condition", ["Sunny", "Snowy", "Rainy", "Cloudy"], index=["Sunny", "Snowy", "Rainy", "Cloudy"].index(default_weather) if default_weather in ["Sunny", "Snowy", "Rainy", "Cloudy"] else 0)
input_season = st.sidebar.selectbox("Season", ["Spring", "Summer", "Autumn", "Winter"], index=["Spring", "Summer", "Autumn", "Winter"].index(default_season) if default_season in ["Spring", "Summer", "Autumn", "Winter"] else 0)
input_epidemic = st.sidebar.selectbox("Epidemic Warning Active?", [0, 1], index=int(default_epidemic))
input_inventory = st.sidebar.number_input("Available Stock Inventory", value=default_inventory, min_value=0, step=10)

# -----------------------------------------------------------------------------
# 4. COMPUTE INFERRED FEATURES & EXCLUDE LEAKAGE
# -----------------------------------------------------------------------------

# Date decomposition
parsed_date = pd.to_datetime(input_date)
day_of_week = parsed_date.dayofweek
month = parsed_date.month
quarter = (month - 1) // 3 + 1
is_weekend = 1 if day_of_week >= 5 else 0
is_month_start = 1 if parsed_date.is_month_start else 0
is_month_end = 1 if parsed_date.is_month_end else 0
promoted_weekend = 1 if (input_promo == 1 and is_weekend == 1) else 0

# Calculate market indicators
price_diff = input_price - input_comp_price
price_ratio = input_price / input_comp_price
discount_rate = input_discount / 100.0

# Extract background time-series features based on profile or fallback to overall average
lag_1 = GLOBAL_MEANS['Demand_Lag_1']
lag_7 = GLOBAL_MEANS['Demand_Lag_7']
rolling_mean = GLOBAL_MEANS['Rolling_Mean_7']

if ui_mode == "Select Store & Product (Database Loaded)":
    # Get actual history profiles
    hist_subset = df_raw[(df_raw['Store ID'] == selected_store) & (df_raw['Product ID'] == selected_product)]
    if len(hist_subset) > 0:
        lag_1 = float(hist_subset['Demand_Lag_1'].iloc[-1])
        lag_7 = float(hist_subset['Demand_Lag_7'].iloc[-1])
        rolling_mean = float(hist_subset['Rolling_Mean_7'].iloc[-1])

# Calculate derived ratio using available inventory
inventory_buffer_ratio = input_inventory / (rolling_mean + 1e-5)

# Encode Categorical Inputs safely using saved target mapping JSON
def get_target_encoded_value(col_name, original_value):
    if encodings and col_name in encodings:
        if str(original_value) in encodings[col_name]:
            return float(encodings[col_name][str(original_value)])
    return float(GLOBAL_MEANS.get(col_name, encodings.get("global_mean", 105.26) if encodings else 105.26))

encoded_category = get_target_encoded_value("Category", active_category)
encoded_region = get_target_encoded_value("Region", active_region)
encoded_weather = get_target_encoded_value("Weather Condition", input_weather)
encoded_season = get_target_encoded_value("Seasonality", input_season)

# Compile exact Feature Frame in the order XGBoost was trained on
features_dict = {
    'Category': [encoded_category],
    'Region': [encoded_region],
    'Price': [input_price],
    'Discount': [input_discount],
    'Weather Condition': [encoded_weather],
    'Promotion': [input_promo],
    'Competitor Pricing': [input_comp_price],
    'Seasonality': [encoded_season],
    'Epidemic': [input_epidemic],
    'Day_of_Week': [day_of_week],
    'Month': [month],
    'Quarter': [quarter],
    'Is_Weekend': [is_weekend],
    'Is_Month_Start': [is_month_start],
    'Is_Month_End': [is_month_end],
    'Demand_Lag_1': [lag_1],
    'Demand_Lag_7': [lag_7],
    'Rolling_Mean_7': [rolling_mean],
    'Price_Diff': [price_diff],
    'Discount_Rate': [discount_rate],
    'Promoted_Weekend': [promoted_weekend],
    'Inventory_Buffer_Ratio': [inventory_buffer_ratio],
    'Price_Ratio': [price_ratio]
}

features_df = pd.DataFrame(features_dict)

# -----------------------------------------------------------------------------
# 5. EXECUTE FORECAST ENGINES
# -----------------------------------------------------------------------------

# Predict Demand
if model is not None:
    try:
        raw_prediction = model.predict(features_df)[0]
        predicted_demand = int(np.round(max(0.0, raw_prediction)))
        st.success(f"✅ Model prediction successful: {predicted_demand} units")
    except Exception as e:
        st.error(f"❌ Prediction error: {e}. Using fallback simulation.")
        # High-fidelity mathematical simulation if model not trained yet
        # Simulates demand based on base rate influenced by promo, discount, price differential, and seasonality
        base_demand = rolling_mean if ui_mode == "Select Store & Product (Database Loaded)" else 100.0
        promo_boost = 25.0 if input_promo == 1 else 0.0
        discount_boost = input_discount * 1.2
        price_impact = -1.5 * (price_diff)
        weather_impact = -10.0 if input_weather in ["Snowy", "Rainy"] else 5.0
        epidemic_impact = -30.0 if input_epidemic == 1 else 0.0
        
        simulated_demand = base_demand + promo_boost + discount_boost + price_impact + weather_impact + epidemic_impact
        predicted_demand = int(np.round(max(5.0, simulated_demand)))
else:
    # High-fidelity mathematical simulation if model not trained yet
    # Simulates demand based on base rate influenced by promo, discount, price differential, and seasonality
    base_demand = rolling_mean if ui_mode == "Select Store & Product (Database Loaded)" else 100.0
    promo_boost = 25.0 if input_promo == 1 else 0.0
    discount_boost = input_discount * 1.2
    price_impact = -1.5 * (price_diff)
    weather_impact = -10.0 if input_weather in ["Snowy", "Rainy"] else 5.0
    epidemic_impact = -30.0 if input_epidemic == 1 else 0.0
    
    simulated_demand = base_demand + promo_boost + discount_boost + price_impact + weather_impact + epidemic_impact
    predicted_demand = int(np.round(max(5.0, simulated_demand)))

# Operational Capping (Sales vs Demand Rule)
forecasted_sales = int(min(predicted_demand, input_inventory))

# Financial Revenue Projection
forecasted_revenue = forecasted_sales * input_price * (1.0 - discount_rate)

# Lost potential sales due to stockouts
lost_sales_volume = max(0, predicted_demand - input_inventory)
lost_revenue = lost_sales_volume * input_price * (1.0 - discount_rate)

# -----------------------------------------------------------------------------
# 6. DASHBOARD INTERFACE LAYOUT
# -----------------------------------------------------------------------------

# Layout Columns
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-header">🔮 Predicted Demand</div>
        <div class="metric-value">{predicted_demand} <span style='font-size: 1.2rem; font-weight: normal; color: #94a3b8;'>Units</span></div>
        <div class="metric-desc">Unconstrained customer market demand prediction</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    # Color condition based on whether inventory limits sales
    sales_color = "#10b981" if forecasted_sales == predicted_demand else "#f59e0b"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-header">📦 Forecasted Sales</div>
        <div class="metric-value" style="color: {sales_color};">{forecasted_sales} <span style='font-size: 1.2rem; font-weight: normal; color: #94a3b8;'>Units</span></div>
        <div class="metric-desc">Actual sales projection (Capped by inventory constraints)</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-header">💵 Projected Revenue</div>
        <div class="metric-value">${forecasted_revenue:,.2f}</div>
        <div class="metric-desc">Estimated turnover after promotional discounts</div>
    </div>
    """, unsafe_allow_html=True)

# Alerts and Recommendations Section
st.write("")
if lost_sales_volume > 0:
    st.error(f"⚠️ **Stockout Risk Warning!** Current available stock ({input_inventory} units) is insufficient to fulfill customer demand ({predicted_demand} units). You are projected to lose **{lost_sales_volume} sales units**, resulting in **${lost_revenue:,.2f} in lost revenue**. Recommend increasing replenishment immediately.")
else:
    st.success(f"✅ **Optimal Stock Safety Level.** Available stock ({input_inventory} units) is sufficient to completely cover predicted market demand ({predicted_demand} units). Overstock buffer size: {input_inventory - predicted_demand} units.")

# -----------------------------------------------------------------------------
# 7. VISUAL ANALYTICAL CHARTS
# -----------------------------------------------------------------------------
st.write("")
st.markdown('<div class="section-title">📊 Scenario Planning & Analytics</div>', unsafe_allow_html=True)

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Price Sensitivity Simulator")
    st.write("Compare how shifting price levels impacts demand compared to competitor pricing:")
    
    # Generate price ranges for simulator
    sim_prices = np.linspace(max(5, input_comp_price - 30), input_comp_price + 30, 20)
    sim_demands = []
    
    for p in sim_prices:
        # Prepare scenario DataFrame
        scenario_feat = features_df.copy()
        scenario_feat['Price'] = p
        scenario_feat['Price_Diff'] = p - input_comp_price
        scenario_feat['Price_Ratio'] = p / input_comp_price
        
        if model is not None:
            pred = max(0.0, model.predict(scenario_feat)[0])
        else:
            # High-fidelity mock simulator fallback matching model variables
            pred = max(5.0, (rolling_mean if ui_mode == "Select Store & Product (Database Loaded)" else 100.0) + (1.2 * input_discount) - (1.5 * (p - input_comp_price)))
        sim_demands.append(pred)
        
    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(x=sim_prices, y=sim_demands, mode='lines+markers', name='Predicted Demand', line=dict(color='#4f46e5', width=3)))
    fig_price.add_vline(x=input_price, line_dash="dash", line_color="#ef4444", annotation_text="Selected Price", annotation_position="top left")
    fig_price.add_vline(x=input_comp_price, line_dash="dot", line_color="#10b981", annotation_text="Competitor Price", annotation_position="bottom right")
    
    fig_price.update_layout(
        xaxis_title="Simulated Selling Price ($)",
        yaxis_title="Demand Units",
        margin=dict(l=40, r=40, t=20, b=40),
        height=320,
        hovermode="x"
    )
    st.plotly_chart(fig_price, use_container_width=True)

with chart_col2:
    st.subheader("Discount Optimization Curve")
    st.write("Understand the correlation between markdown rates and revenue capture:")
    
    sim_discounts = np.arange(0, 55, 5)
    sim_revenues = []
    
    for d in sim_discounts:
        scenario_feat = features_df.copy()
        scenario_feat['Discount'] = d
        scenario_feat['Discount_Rate'] = d / 100.0
        
        if model is not None:
            d_pred = max(0.0, model.predict(scenario_feat)[0])
        else:
            d_pred = max(5.0, (rolling_mean if ui_mode == "Select Store & Product (Database Loaded)" else 100.0) + (1.2 * d) - (1.5 * price_diff))
            
        s_sales = min(d_pred, input_inventory)
        s_rev = s_sales * input_price * (1.0 - (d / 100.0))
        sim_revenues.append(s_rev)
        
    fig_discount = go.Figure()
    fig_discount.add_trace(go.Scatter(x=sim_discounts, y=sim_revenues, mode='lines+markers', name='Projected Revenue', line=dict(color='#10b981', width=3)))
    fig_discount.add_vline(x=input_discount, line_dash="dash", line_color="#ef4444", annotation_text="Active Discount", annotation_position="top left")
    
    fig_discount.update_layout(
        xaxis_title="Discount Offer (%)",
        yaxis_title="Projected Revenue ($)",
        margin=dict(l=40, r=40, t=20, b=40),
        height=320,
        hovermode="x"
    )
    st.plotly_chart(fig_discount, use_container_width=True)

# Historical context section
if ui_mode == "Select Store & Product (Database Loaded)":
    st.write("")
    st.markdown('<div class="section-title">🕒 Historical Demand Context (Last 30 records)</div>', unsafe_allow_html=True)
    
    # Slice the last 30 chronological days for this product category
    hist_subset_plot = df_raw[(df_raw['Store ID'] == selected_store) & (df_raw['Product ID'] == selected_product)].sort_values('Date').tail(30)
    
    if len(hist_subset_plot) > 0:
        fig_hist = px.line(hist_subset_plot, x='Date', y=['Demand', 'Inventory Level', 'Units Sold'], 
                           title="Chronological Sales vs Demand and Inventory Patterns",
                           color_discrete_sequence=["#4f46e5", "#ef4444", "#10b981"])
        fig_hist.update_layout(
            xaxis_title="Timeline",
            yaxis_title="Quantity",
            margin=dict(l=40, r=40, t=40, b=40),
            height=300
        )
        st.plotly_chart(fig_hist, use_container_width=True)

# -----------------------------------------------------------------------------
# 8. TECHNICAL PIPELINE INFORMATION
# -----------------------------------------------------------------------------
st.write("")
with st.expander("🛠️ Advanced Technical Architecture"):
    st.markdown("""
    ### Dashboard Feature Pipeline and Engineering Design
    This application is designed to mimic real-world business constraints by implementing a secure, leakproof machine learning model pipeline:
    1. **Zero Operational Leakage**: To ensure true predictive accuracy, all immediate results of sales (such as `Units Sold`, `Units Ordered`, and `Revenue`) have been completely dropped from the feature set.
    2. **Lag Recurrence Simulation**: Instead of forcing the user to guess complex time-series parameters, the model dynamically resolves `Demand_Lag_1`, `Demand_Lag_7`, and `Rolling_Mean_7` by querying historical data patterns.
    3. **Safe Target Encodings**: Categorical variables (`Category`, `Region`, `Weather Condition`, `Seasonality`) are safely loaded from `target_encoding_maps.json` to prevent data leakage during preprocessing, retaining true mathematical weights without introducing arbitrary numerical biases (like Label Encoding would).
    """)