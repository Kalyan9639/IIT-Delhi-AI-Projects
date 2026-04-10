from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import requests
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_loader import load_all_data  # noqa: E402


API_URL = 'http://127.0.0.1:8000/forecast'


st.set_page_config(page_title='PJM Energy Forecast Dashboard', layout='wide')

st.title('PJM Hourly Energy Forecast Dashboard')
st.caption('Select a region or forecast all regions using the shared trained model.')


@st.cache_data(show_spinner=False)
def get_regions() -> list[str]:
    data = load_all_data()
    return sorted(data['Region'].dropna().astype(str).unique().tolist())


regions = get_regions()
selected_region = st.sidebar.selectbox('Forecast mode', ['All regions'] + regions)
horizon = st.sidebar.slider('Forecast horizon (hours)', 1, 168, 24)

if st.button('Generate forecast', type='primary'):
    payload = {
        'region': None if selected_region == 'All regions' else selected_region,
        'horizon': horizon,
    }

    try:
        response = requests.post(API_URL, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
    except requests.RequestException as exc:
        st.error(f'Unable to reach the forecasting API: {exc}')
        st.stop()

    forecast_rows = pd.DataFrame(result['forecast_rows'])
    if forecast_rows.empty:
        st.warning('The API returned no forecast rows.')
        st.stop()

    st.success(
        f"Generated {len(forecast_rows)} forecast rows for "
        f"{'all regions' if result['mode'] == 'all' else result['requested_region']}."
    )

    if result['mode'] == 'single':
        chart_df = forecast_rows.copy()
        chart_df['Datetime'] = pd.to_datetime(chart_df['Datetime'])
        chart_df = chart_df.set_index('Datetime')[['Predicted_Load']]
        st.line_chart(chart_df)
        st.dataframe(forecast_rows, use_container_width=True)
    else:
        chart_df = forecast_rows.copy()
        chart_df['Datetime'] = pd.to_datetime(chart_df['Datetime'])
        pivot = chart_df.pivot_table(index='Datetime', columns='Region', values='Predicted_Load')
        st.line_chart(pivot)
        st.dataframe(forecast_rows, use_container_width=True)

    st.download_button(
        label='Download forecast CSV',
        data=forecast_rows.to_csv(index=False).encode('utf-8'),
        file_name='pjm_forecast.csv',
        mime='text/csv',
    )
