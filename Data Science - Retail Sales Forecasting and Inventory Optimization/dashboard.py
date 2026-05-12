import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Retail Forecasting & Inventory", layout="wide", page_icon="📊")

@st.cache_data
def load_data():
    forecast = pd.read_csv('forecast_results.csv', parse_dates=['Date'])
    inventory = pd.read_csv('inventory_recommendations.csv')
    raw = pd.read_csv('demand_forecasting.csv', parse_dates=['Date'])
    return forecast, inventory, raw

forecast_df, inventory_df, raw_df = load_data()

st.title("Retail Sales Forecasting & Inventory Optimization")

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filters")
stores = st.sidebar.multiselect("Store", sorted(forecast_df['Store ID'].unique()), default=sorted(forecast_df['Store ID'].unique())[:2])
products = st.sidebar.multiselect("Product", sorted(forecast_df['Product ID'].unique()), default=sorted(forecast_df['Product ID'].unique())[:5])
date_range = st.sidebar.date_input("Date Range", [forecast_df['Date'].min(), forecast_df['Date'].max()])

f_df = forecast_df[
    (forecast_df['Store ID'].isin(stores)) &
    (forecast_df['Product ID'].isin(products)) &
    (forecast_df['Date'].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])))
]

# --- KPI ROW ---
col1, col2, col3, col4 = st.columns(4)
mape = (f_df['Abs_Error'].sum() / f_df['Actual'].sum()) * 100
bias = ((f_df['Forecast'] - f_df['Actual']).sum() / f_df['Actual'].sum()) * 100
stockout_skus = inventory_df[inventory_df['Stockout_Risk']]['Product ID'].nunique()
total_order = inventory_df['Suggested_Order_Qty'].sum()

col1.metric("Weighted MAPE", f"{mape:.1f}%", delta="-2.3%" if mape < 15 else None)
col2.metric("Forecast Bias", f"{bias:.1f}%", delta_color="inverse")
col3.metric("SKUs at Risk", f"{stockout_skus}", delta=f"{stockout_skus} need action")
col4.metric("Suggested Orders", f"{int(total_order):,} units")

st.markdown("---")

# --- TAB LAYOUT ---
tab1, tab2, tab3 = st.tabs(["📈 Forecast Performance", "📦 Inventory Health", "🔍 SKU Deep Dive"])

with tab1:
    st.subheader("Forecast vs Actual")
    agg = f_df.groupby('Date').agg({'Actual':'sum','Forecast':'sum'}).reset_index()
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=agg['Date'], y=agg['Actual'], name='Actual', line=dict(width=3)))
    fig1.add_trace(go.Scatter(x=agg['Date'], y=agg['Forecast'], name='Forecast', line=dict(width=3, dash='dot')))
    fig1.update_layout(hovermode='x unified', height=400, legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig1, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Error by Store")
        err_store = f_df.groupby('Store ID').apply(lambda x: (x['Abs_Error'].sum()/x['Actual'].sum())*100).reset_index(name='WMAPE')
        fig2 = px.bar(err_store, x='Store ID', y='WMAPE', color='WMAPE', color_continuous_scale='RdYlGn_r', text_auto='.1f')
        fig2.update_layout(height=350)
        st.plotly_chart(fig2, use_container_width=True)
    with col_b:
        st.subheader("Error Distribution")
        fig3 = px.histogram(f_df, x='APE', nbins=40, marginal='box')
        fig3.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)

with tab2:
    st.subheader("Inventory Overview")
    inv_filtered = inventory_df[inventory_df['Store ID'].isin(stores) & inventory_df['Product ID'].isin(products)]

    col1, col2 = st.columns([2,1])
    with col1:
        fig4 = px.scatter(inv_filtered, x='Inventory Level', y='Reorder_Point',
                          size='Forecast_Mean', color='Stockout_Risk',
                          hover_data=['Product ID','Days_of_Supply','Safety_Stock'],
                          color_discrete_map={True:'red', False:'green'},
                          title='Inventory Level vs Reorder Point')
        fig4.add_shape(type='line', x0=0, y0=0, x1=inv_filtered['Inventory Level'].max(),
                       y1=inv_filtered['Inventory Level'].max(), line=dict(dash='dash'))
        st.plotly_chart(fig4, use_container_width=True)
    with col2:
        risk_counts = inv_filtered['Stockout_Risk'].value_counts()
        fig5 = px.pie(values=risk_counts.values, names=['Healthy','At Risk'],
                      hole=0.5, color_discrete_sequence=['#2ca02c', '#d62728'])
        fig5.update_layout(title='Stock Health')
        st.plotly_chart(fig5, use_container_width=True)

    st.subheader("Top Action Items")
    top_orders = inv_filtered.sort_values('Suggested_Order_Qty', ascending=False).head(10)
    fig6 = px.bar(top_orders, x='Suggested_Order_Qty', y='Product ID',
                  orientation='h', color='Days_of_Supply',
                  hover_data=['Store ID','Inventory Level','Reorder_Point'],
                  color_continuous_scale='Bluered')
    fig6.update_layout(yaxis={'categoryorder':'total ascending'}, height=400)
    st.plotly_chart(fig6, use_container_width=True)

with tab3:
    st.subheader("SKU Deep Dive")
    sku = st.selectbox("Select SKU", products)
    sku_df = f_df[f_df['Product ID'] == sku]

    fig7 = go.Figure()
    fig7.add_trace(go.Scatter(x=sku_df['Date'], y=sku_df['Actual'], name='Actual', mode='lines+markers'))
    fig7.add_trace(go.Scatter(x=sku_df['Date'], y=sku_df['Forecast'], name='Forecast', mode='lines'))
    fig7.add_trace(go.Bar(x=sku_df['Date'], y=sku_df['Abs_Error'], name='Error', yaxis='y2', opacity=0.3))
    fig7.update_layout(yaxis2=dict(overlaying='y', side='right', showgrid=False), height=450, title=f'{sku} Performance')
    st.plotly_chart(fig7, use_container_width=True)

    # Feature importance simulation from raw data
    st.subheader("Demand Drivers")
    raw_sku = raw_df[raw_df['Product ID'] == sku]
    driver_df = raw_sku.groupby('Date').agg({'Units Sold':'sum','Price':'mean','Promotion':'mean'}).reset_index()
    fig8 = px.line(driver_df, x='Date', y=['Units Sold','Price'],
                   facet_col='variable', facet_col_wrap=1)
    st.plotly_chart(fig8, use_container_width=True)

st.markdown("---")
st.caption("Data refresh: from forecast_results.csv and inventory_recommendations.csv. Update files to refresh dashboard.")