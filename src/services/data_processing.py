import pandas as pd
import streamlit as st
from scipy.interpolate import interp1d
from pathlib import Path


@st.cache_data
def load_data():
    """Load and process the route and stops data"""
    # Get the project root directory (two levels up from this file)
    project_root = Path(__file__).parent.parent.parent
    
    # Load route data
    route_path = project_root / 'data' / 'medoc_marathon_complete_route.csv'
    route_df = pd.read_csv(route_path)
    
    # Load stops data
    stops_path = project_root / 'data' / 'medoc2025.csv'
    stops_df = pd.read_csv(stops_path)
    
    # Clean and process stops data
    stops_df = stops_df.dropna(subset=['wine_stop', 'wine_rating'])
    
    return route_df, stops_df


def interpolate_stop_positions(route_df, stops_df):
    """Interpolate latitude/longitude positions for stops based on their distance along route"""
    # Create interpolation functions
    f_lat = interp1d(route_df['cumulative_distance_km'], route_df['latitude'], 
                     kind='linear', bounds_error=False, fill_value='extrapolate')
    f_lon = interp1d(route_df['cumulative_distance_km'], route_df['longitude'], 
                     kind='linear', bounds_error=False, fill_value='extrapolate')
    
    # Calculate positions for each stop
    stops_with_coords = stops_df.copy()
    stops_with_coords['latitude'] = f_lat(stops_df['approx_km'])
    stops_with_coords['longitude'] = f_lon(stops_df['approx_km'])
    
    return stops_with_coords


def get_selected_stops_data(stops_with_coords, selected_stops):
    """Get data for selected stops"""
    return stops_with_coords[
        stops_with_coords.apply(
            lambda x: x['wine_stop'] in selected_stops, 
            axis=1
        )
    ]
