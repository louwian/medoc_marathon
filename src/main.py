import streamlit as st
from streamlit_folium import st_folium
import base64
from pathlib import Path

# Import from services
from services.data_processing import (
    load_data, 
    interpolate_stop_positions
)

from services.map_service import create_map
from utils.helpers import load_css

# Import from UI
from ui.ui_components import (
    initialize_session_state,
    create_planning_section,
    create_optimization_section,
    create_validation_section,
    create_sidebar, 
    create_planned_route_panel
)

APP_VERSION = "V1.2"


def create_main_header():
    """Create main page header with title and logo"""
    # Load logo
    current_file = Path(__file__)
    logo_path = current_file.parent / "images" / "_WL_logo.png"
    with logo_path.open("rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()

    # Load CSS styles
    style = load_css(current_file.parent / "css" / "logo.css")
    st.markdown(style, unsafe_allow_html=True)
    
    # Create header HTML
    header_html = f"""
    <div class="main-header">
        <h1>🍷 Medoc Marathon Route Planner</h1>
        <div class="main-header-logo">
            <img src="data:image/png;base64,{encoded_string}" alt="Wine & Logistics Logo">
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)


# Set page config
st.set_page_config(
    page_title="Medoc Marathon Route Planner",
    page_icon="🍷",
    layout="wide",
    initial_sidebar_state="expanded"
)


def main():
    """Main application"""
    create_main_header()
    st.markdown("Plan your wine stops for the famous Medoc Marathon! Select stops in the sidebar to see them on the map.")
    
    try:
        # Load data
        route_df, stops_df = load_data()
        
        # Interpolate stop positions
        stops_with_coords = interpolate_stop_positions(route_df, stops_df)
        
        # Initialize session state
        initialize_session_state(stops_df)
        
        # Create sidebar
        create_sidebar(stops_df, APP_VERSION)
        
        # Create planning section
        create_planning_section()
        
        # Create optimization section
        create_optimization_section(route_df, stops_with_coords)
        
        # Create validation section
        create_validation_section(route_df, stops_with_coords)
        
        st.subheader("Route Map")
        # Create and display map
        map_obj = create_map(route_df, stops_with_coords, st.session_state.selected_stops)
        st_folium(map_obj, width="stretch", height=600)
        
        # Create planned route panel
        create_planned_route_panel(
            route_df, 
            stops_df, 
            stops_with_coords, 
            st.session_state.selected_stops
        )
            
    except FileNotFoundError as e:
        st.error(f"Data files not found. Please ensure the CSV files are in the 'data' directory: {e}")
    except Exception as e:
        st.error(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
