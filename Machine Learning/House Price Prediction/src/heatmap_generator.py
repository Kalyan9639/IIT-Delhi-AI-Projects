"""
Heatmap generation module for Bangalore Real Estate Intelligence System.
Creates interactive price heatmaps and investment visualizations.
"""

import warnings

import folium
import pandas as pd
import plotly.express as px
from folium import plugins

from .config import HEATMAP_CONFIG
from .logging_utils import log_error, log_info

warnings.filterwarnings("ignore")


class HeatmapGenerator:
    """Heatmap generation class for real estate data."""

    def __init__(self, Bangalore_lat=12.9716, Bangalore_lon=77.5946):
        self.bangalore_center = [Bangalore_lat, Bangalore_lon]
        self.zoom_level = HEATMAP_CONFIG["zoom_level"]

    def create_price_heatmap(self, df, output_path="price_heatmap.html"):
        log_info("create_price_heatmap", "Creating price heatmap")

        if "location" not in df.columns or "price" not in df.columns:
            log_error("create_price_heatmap", "Required columns not found")
            return None

        m = folium.Map(location=self.bangalore_center, zoom_start=self.zoom_level, tiles="CartoDB positron", control_scale=True)
        location_prices = df.groupby("location").agg(price=("price", "mean"), total_sqft=("total_sqft", "mean"), bhk=("bhk", "mean")).reset_index()
        location_coords = self._create_location_coordinates(df)
        heatmap_data = []

        for _, row in location_prices.iterrows():
            location = row["location"]
            if location not in location_coords:
                continue

            coord = location_coords[location]
            price = row["price"]
            color = "blue" if price < 50 else "green" if price < 100 else "orange" if price < 200 else "red"

            folium.CircleMarker(
                location=coord,
                radius=max(5, min(15, row["price"] / 10)),
                popup=f"{location}<br>Avg Price: Rs. {row['price']:.2f} Lakhs<br>Avg Area: {row['total_sqft']:.0f} sqft",
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
            ).add_to(m)

            heatmap_data.append([coord[0], coord[1], row["price"]])

        if heatmap_data:
            plugins.HeatMap(
                heatmap_data,
                radius=HEATMAP_CONFIG["cluster_radius"],
                gradient=HEATMAP_CONFIG["gradient"],
                blur=15,
                max_zoom=13,
            ).add_to(m)

        folium.LayerControl().add_to(m)
        m.get_root().html.add_child(folium.Element("<div style='position: fixed; top: 10px; left: 50px; background-color: white; padding: 10px; border-radius: 5px; z-index: 9999; font-size: 16px; font-weight: bold;'>Bangalore Real Estate Price Heatmap</div>"))
        m.save(output_path)
        return m

    def create_price_concentration_map(self, df, output_path="price_concentration.html"):
        log_info("create_price_concentration_map", "Creating price concentration map")

        if "location" not in df.columns or "price" not in df.columns:
            return None

        m = folium.Map(location=self.bangalore_center, zoom_start=self.zoom_level, tiles="CartoDB dark_matter")
        location_stats = df.groupby("location").agg(avg_price=("price", "mean"), listing_count=("price", "count"), avg_area=("total_sqft", "mean")).reset_index()
        location_coords = self._create_location_coordinates(df)

        for _, row in location_stats.iterrows():
            location = row["location"]
            if location not in location_coords:
                continue

            coord = location_coords[location]
            price = row["avg_price"]
            count = row["listing_count"]

            if price < 50:
                color = "#006837"
            elif price < 100:
                color = "#1a9850"
            elif price < 200:
                color = "#66bd63"
            elif price < 300:
                color = "#fdae61"
            else:
                color = "#d7191c"

            popup_html = (
                f"<div style='font-family: Arial; font-size: 12px;'>"
                f"<b>{location}</b><br>"
                f"Avg Price: Rs. {price:.2f} Lakhs<br>"
                f"Listings: {count}<br>"
                f"Avg Area: {row['avg_area']:.0f} sqft"
                f"</div>"
            )

            folium.CircleMarker(
                location=coord,
                radius=min(20, count / 5),
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.8,
                popup=folium.Popup(popup_html, max_width=300),
            ).add_to(m)

        m.get_root().html.add_child(folium.Element("<div style='position: fixed; bottom: 50px; left: 50px; background-color: white; padding: 15px; border-radius: 5px; z-index: 9999; font-size: 12px;'><b>Price Legend (Lakhs)</b><br><i style='background: #006837; width: 20px; height: 20px; display: inline-block; margin-right: 5px;'></i> &lt; 50<br><i style='background: #1a9850; width: 20px; height: 20px; display: inline-block; margin-right: 5px;'></i> 50-100<br><i style='background: #66bd63; width: 20px; height: 20px; display: inline-block; margin-right: 5px;'></i> 100-200<br><i style='background: #fdae61; width: 20px; height: 20px; display: inline-block; margin-right: 5px;'></i> 200-300<br><i style='background: #d7191c; width: 20px; height: 20px; display: inline-block; margin-right: 5px;'></i> &gt; 300</div>"))
        m.save(output_path)
        return m

    def create_investment_heatmap(self, df, output_path="investment_heatmap.html"):
        log_info("create_investment_heatmap", "Creating investment heatmap")

        if "location" not in df.columns or "investment_score" not in df.columns:
            return None

        m = folium.Map(location=self.bangalore_center, zoom_start=self.zoom_level, tiles="CartoDB dark_matter")
        location_stats = df.groupby("location").agg(investment_score=("investment_score", "mean"), price=("price", "mean"), price_per_sqft=("price_per_sqft", "mean")).reset_index()
        location_coords = self._create_location_coordinates(df)

        for _, row in location_stats.iterrows():
            location = row["location"]
            if location not in location_coords:
                continue

            coord = location_coords[location]
            score = row["investment_score"]

            if score < 0.3:
                color = "#d73027"
            elif score < 0.5:
                color = "#fc8d59"
            elif score < 0.7:
                color = "#fee08b"
            elif score < 0.85:
                color = "#d9ef8b"
            else:
                color = "#1a9850"

            popup_html = (
                f"<div style='font-family: Arial; font-size: 12px;'>"
                f"<b>{location}</b><br>"
                f"Investment Score: {score:.3f}<br>"
                f"Avg Price: Rs. {row['price']:.2f} Lakhs<br>"
                f"Price/Sqft: Rs. {row['price_per_sqft']:.2f}"
                f"</div>"
            )

            folium.CircleMarker(
                location=coord,
                radius=10,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.8,
                popup=folium.Popup(popup_html, max_width=300),
            ).add_to(m)

        m.get_root().html.add_child(folium.Element("<div style='position: fixed; bottom: 50px; left: 50px; background-color: white; padding: 15px; border-radius: 5px; z-index: 9999; font-size: 12px;'><b>Investment Score Legend</b><br><i style='background: #d73027; width: 20px; height: 20px; display: inline-block; margin-right: 5px;'></i> Poor (&lt; 0.3)<br><i style='background: #fc8d59; width: 20px; height: 20px; display: inline-block; margin-right: 5px;'></i> Below Avg (0.3-0.5)<br><i style='background: #fee08b; width: 20px; height: 20px; display: inline-block; margin-right: 5px;'></i> Average (0.5-0.7)<br><i style='background: #d9ef8b; width: 20px; height: 20px; display: inline-block; margin-right: 5px;'></i> Good (0.7-0.85)<br><i style='background: #1a9850; width: 20px; height: 20px; display: inline-block; margin-right: 5px;'></i> Excellent (&gt; 0.85)</div>"))
        m.save(output_path)
        return m

    def create_price_distribution_plot(self, df, output_path="price_distribution.html"):
        log_info("create_price_distribution_plot", "Creating price distribution plot")
        if "price" not in df.columns:
            return None

        fig = px.histogram(df, x="price", nbins=50, title="Price Distribution in Bangalore", labels={"price": "Price (Lakhs)", "count": "Number of Properties"}, color_discrete_sequence=["#1f77b4"])
        fig.update_layout(template="plotly_white", showlegend=False, height=600, width=1000)
        median_price = df["price"].median()
        fig.add_vline(x=median_price, line_dash="dash", line_color="red", annotation_text=f"Median: Rs. {median_price:.2f} Lakhs", annotation_position="top")
        fig.write_html(output_path)
        return fig

    def create_price_per_sqft_by_location(self, df, output_path="price_per_sqft_by_location.html"):
        log_info("create_price_per_sqft_by_location", "Creating price per sqft comparison")
        if "location" not in df.columns or "price_per_sqft" not in df.columns:
            return None

        location_prices = df.groupby("location")["price_per_sqft"].mean().sort_values(ascending=False)
        top_locations = location_prices.head(20).index.tolist()
        df_top = df[df["location"].isin(top_locations)]

        fig = px.box(
            df_top,
            x="price_per_sqft",
            y="location",
            orientation="h",
            title="Price per Square Foot by Location (Top 20)",
            labels={"price_per_sqft": "Price per Sqft (Rs.)", "location": "Location"},
            color="location",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_layout(template="plotly_white", height=800, width=1000, showlegend=False)
        fig.write_html(output_path)
        return fig

    def create_investment_scatter_plot(self, df, output_path="investment_scatter.html"):
        log_info("create_investment_scatter_plot", "Creating investment scatter plot")
        if "price" not in df.columns or "investment_score" not in df.columns:
            return None

        fig = px.scatter(
            df,
            x="price",
            y="investment_score",
            color="investment_score",
            size="total_sqft",
            hover_data=["location", "bhk", "price_per_sqft"],
            title="Investment Opportunities: Price vs Investment Score",
            labels={"price": "Price (Lakhs)", "investment_score": "Investment Score"},
            color_continuous_scale="RdYlGn",
        )
        fig.update_layout(template="plotly_white", height=600, width=1000)
        fig.write_html(output_path)
        return fig

    def create_price_trend_by_bhk(self, df, output_path="price_trend_by_bhk.html"):
        log_info("create_price_trend_by_bhk", "Creating price trend by BHK")
        if "bhk" not in df.columns or "price" not in df.columns:
            return None

        bhk_prices = df.groupby("bhk")["price"].agg(["mean", "std", "count"]).reset_index()
        fig = px.bar(
            bhk_prices,
            x="bhk",
            y="mean",
            error_y="std",
            title="Average Price by BHK",
            labels={"bhk": "BHK", "mean": "Average Price (Lakhs)"},
            text="count",
        )
        fig.update_layout(template="plotly_white", height=600, width=800)
        fig.write_html(output_path)
        return fig

    def _create_location_coordinates(self, df):
        major_locations = {
            "Whitefield": [12.9716, 77.7513],
            "Sarjapur Road": [12.8950, 77.7036],
            "Electronic City": [12.8480, 77.6594],
            "Kanakpura Road": [12.8569, 77.5639],
            "Thanisandra": [13.1042, 77.6058],
            "Yelahanka": [13.1042, 77.5946],
            "Uttarahalli": [12.9056, 77.5467],
            "Hebbal": [13.0359, 77.5970],
            "Marathahalli": [13.0175, 77.6083],
            "Raja Rajeshwari Nagar": [12.9167, 77.5267],
            "Hennur Road": [13.0067, 77.6283],
            "Bannerghatta Road": [12.8697, 77.5586],
            "7th Phase JP Nagar": [12.9056, 77.5944],
            "Haralur Road": [12.8922, 77.5761],
            "Bellandur": [12.9236, 77.6336],
            "KR Puram": [13.0194, 77.6214],
            "Rajaji Nagar": [13.0244, 77.5811],
            "Indiranagar": [12.9751, 77.6364],
            "Koramangala": [12.9352, 77.6245],
            "HSR Layout": [12.9167, 77.6028],
            "Jayanagar": [12.9236, 77.5825],
            "Malleshwaram": [13.0100, 77.5747],
            "Basavanagudi": [12.9208, 77.5692],
            "BTM Layout": [12.9106, 77.5989],
            "Domlur": [12.9236, 77.6364],
            "Old Airport Road": [12.9236, 77.6167],
            "Nagawara": [13.0333, 77.6167],
            "Vijayanagar": [12.9167, 77.5667],
            "Frazer Town": [13.0167, 77.5667],
            "Mahadevpura": [13.0167, 77.5167],
            "Jakkur": [13.0500, 77.6167],
            "Banaswadi": [12.9167, 77.6167],
            "South Bangalore": [12.9333, 77.5833],
            "North Bangalore": [13.0167, 77.6167],
            "East Bangalore": [12.9667, 77.6333],
            "West Bangalore": [12.9833, 77.5500],
        }

        location_coords = {}
        for location in df["location"].unique():
            location_str = str(location).strip()
            if location_str in major_locations:
                location_coords[location_str] = major_locations[location_str]
                continue

            for major_location, coords in major_locations.items():
                if major_location.lower() in location_str.lower() or location_str.lower() in major_location.lower():
                    location_coords[location_str] = coords
                    break
            else:
                location_coords[location_str] = self.bangalore_center

        return location_coords
