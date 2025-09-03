import folium
import pandas as pd


def get_stop_color(stop_type):
    """Get color for stop markers based on type"""
    colors = {
        'Must stop': 'red',
        'Nice to stop': 'orange', 
        'Can stop': 'blue',
        'Can skip': 'white'
    }
    return colors.get(stop_type, 'gray')


def create_map(route_df, stops_with_coords, selected_stops):
    """Create folium map with route and selected stops"""
    # Calculate map center
    center_lat = route_df['latitude'].mean()
    center_lon = route_df['longitude'].mean()
    
    # Create base map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles='OpenStreetMap'
    )
    
    # Add route line
    route_coords = [[lat, lon] for lat, lon in zip(route_df['latitude'], route_df['longitude'])]
    folium.PolyLine(
        route_coords,
        color='purple',
        weight=3,
        opacity=0.7,
        popup='Medoc Marathon Route'
    ).add_to(m)
    
    # Add start marker
    folium.Marker(
        [route_df.iloc[0]['latitude'], route_df.iloc[0]['longitude']],
        popup='START',
        icon=folium.Icon(color='green', icon='play')
    ).add_to(m)
    
    # Add finish marker
    folium.Marker(
        [route_df.iloc[-1]['latitude'], route_df.iloc[-1]['longitude']],
        popup='FINISH',
        icon=folium.Icon(color='green', icon='stop')
    ).add_to(m)
    
    # Add selected stop markers
    selected_stops_data = stops_with_coords[
        stops_with_coords.apply(
            lambda x: x['wine_stop'] in selected_stops, 
            axis=1
        )
    ]
    
    for idx, stop in selected_stops_data.iterrows():
        food_info = f" {stop['food_stop']}" if pd.notna(stop['food_stop']) else ""
        popup_text = f"""
        <b>{stop['wine_stop']}</b><br>
        Distance: {stop['approx_km']}km<br>
        Type: {stop['wine_rating']}<br>
        Price: £{stop['approx_uk_price_winesearcher']}{food_info}
        """
        
        folium.Marker(
            [stop['latitude'], stop['longitude']],
            popup=folium.Popup(popup_text, max_width=200),
            icon=folium.Icon(
                color=get_stop_color(stop['wine_rating']), 
                icon='wine-glass',
                prefix='fa'
            )
        ).add_to(m)
    
    return m
