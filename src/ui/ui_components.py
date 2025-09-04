import streamlit as st
import pandas as pd
import time
from utils.helpers import mark_route_as_not_optimized


def initialize_session_state(stops_df):
    """Initialize session state for selected stops and planning parameters"""
    if 'selected_stops' not in st.session_state:
        # Get must stop names from stops_df
        must_stop_names = stops_df[stops_df['wine_rating'] == 'Must stop']['wine_stop'].tolist()
        st.session_state.selected_stops = must_stop_names
    
    # Ensure all stops have a unique identifier
    if 'stop_checkboxes' not in st.session_state:
        st.session_state.stop_checkboxes = {}
    
    # Initialize planning parameters
    if 'total_marathon_hours' not in st.session_state:
        st.session_state.total_marathon_hours = 6
    if 'total_marathon_minutes' not in st.session_state:
        st.session_state.total_marathon_minutes = 30
    if 'running_pace_minutes' not in st.session_state:
        st.session_state.running_pace_minutes = 6
    if 'running_pace_seconds' not in st.session_state:
        st.session_state.running_pace_seconds = 30
    if 'time_per_stop' not in st.session_state:
        st.session_state.time_per_stop = 8
    if 'max_stops' not in st.session_state:
        st.session_state.max_stops = 15
    if 'min_stops' not in st.session_state:
        st.session_state.min_stops = 6
    if 'max_distance_between_stops' not in st.session_state:
        st.session_state.max_distance_between_stops = 8.0
    if 'route_optimized' not in st.session_state:
        st.session_state.route_optimized = False
    if 'optimization_log' not in st.session_state:
        st.session_state.optimization_log = []
    if 'optimization_iterations' not in st.session_state:
        st.session_state.optimization_iterations = 0


def create_planning_section():
    """Create the race planning section with input parameters"""
    st.subheader("📋 Race Planning")
    st.markdown("Configure your marathon strategy and constraints:")
    
    # Create columns for neat arrangement
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**⏱️ Time Goals**")
        
        # Total marathon time
        hours = st.number_input(
            "Marathon Hours",
            min_value=3,
            max_value=7,
            value=6,
            key="total_marathon_hours_input",
            on_change=mark_route_as_not_optimized
        )
        
        minutes = st.number_input(
            "Marathon Minutes",
            min_value=0,
            max_value=59,
            value=30,
            key="total_marathon_minutes_input",
            on_change=mark_route_as_not_optimized
        )
        
        # Update session state
        st.session_state.total_marathon_hours = hours
        st.session_state.total_marathon_minutes = minutes
        
        # Display total time
        total_minutes = hours * 60 + minutes
        st.info(f"Total time: {hours}h {minutes}m ({total_minutes} min)")
    
    with col2:
        st.markdown("**🏃‍♂️ Pace**")
        
        # Running pace
        pace_min = st.number_input(
            "Pace (min/km)",
            min_value=4,
            max_value=12,
            value=6,
            key="running_pace_minutes_input",
            on_change=mark_route_as_not_optimized
        )
        
        pace_sec = st.number_input(
            "Pace (sec/km)",
            min_value=0,
            max_value=59,
            value=30,
            key="running_pace_seconds_input",
            on_change=mark_route_as_not_optimized
        )
        
        # Update session state
        st.session_state.running_pace_minutes = pace_min
        st.session_state.running_pace_seconds = pace_sec
        
        # Display pace
        st.info(f"Pace: {pace_min}:{pace_sec:02d}/km")
    
    with col3:
        st.markdown("**🎯 Stop Strategy**")

        # Time per stop
        time_per_stop = st.number_input(
            "Time per stop (min)",
            min_value=2,
            max_value=30,
            value=8,
            key="time_per_stop_input",
            on_change=mark_route_as_not_optimized
        )
        
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Min stops
            min_stops = st.number_input(
                "Min stops",
                min_value=1,
                max_value=st.session_state.max_stops,
                value=6,
                key="min_stops_input",
                on_change=mark_route_as_not_optimized
            )

        with col2:
            # Max stops
            max_stops = st.number_input(
                "Max stops",
                min_value=st.session_state.min_stops,
                max_value=23,
                value=15,
                key="max_stops_input",  
                on_change=mark_route_as_not_optimized
            )
        
        # Max distance between stops
        max_distance = st.number_input(
            "Max gap (km)",
            min_value=1.0,
            max_value=20.0,
            value=8.0,
            step=0.5,
            key="max_distance_input",
            on_change=mark_route_as_not_optimized
        )
        
        # Update session state
        st.session_state.time_per_stop = time_per_stop
        st.session_state.max_stops = max_stops
        st.session_state.min_stops = min_stops
        st.session_state.max_distance_between_stops = max_distance
        
        # Validate constraints
        if min_stops > max_stops:
            st.error("Min stops cannot exceed max stops!")

    st.markdown("---")

    


def create_optimization_section(route_df, stops_with_coords):
    """Create the route optimization section"""
    from services.optimization import optimize_route
    
    st.subheader("🚀 Route Optimization")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Show optimization button
        if st.button(
            "🔧 Optimize Route", 
            help="Automatically optimize your stop selection based on constraints"
        ):
            # Run optimization
            with st.spinner("Optimizing route..."):
                time.sleep(3)
                result = optimize_route(route_df, st.session_state, stops_with_coords)
                
                if result['success']:
                    # Update session state with optimized stops
                    st.session_state.selected_stops = result['optimized_stops']
                    st.session_state.route_optimized = True
                    
                    # Store optimization log for display
                    st.session_state.optimization_log = result['optimization_log']
                    st.session_state.optimization_iterations = result['iterations']
                    
                    st.success(f"✅ Route optimized successfully in {result['iterations']} iterations!")
                    # st.rerun()  # Refresh to show updated selection
                else:
                    st.error("❌ Optimization failed")
        
        # Show optimization status
        if st.session_state.route_optimized:
            st.success("✅ Route is optimized")
        else:
            st.info("⚪ Route not optimized")
    
    with col2:
        # Show optimization log if available
        if hasattr(st.session_state, 'optimization_log') and st.session_state.optimization_log:
            with st.expander("📋 Optimization Log", expanded=st.session_state.route_optimized):
                for i, log_entry in enumerate(st.session_state.optimization_log):
                    if "Starting" in log_entry:
                        st.write(f"**{i+1}.** {log_entry}")
                    elif "Removed" in log_entry:
                        st.write(f"**{i+1}.** ❌ {log_entry}")
                    elif "Added" in log_entry:
                        st.write(f"**{i+1}.** ✅ {log_entry}")
                    elif "Found" in log_entry and "gap" in log_entry:
                        st.write(f"**{i+1}.** 🔍 {log_entry}")
                    elif "optimization complete" in log_entry:
                        st.write(f"**{i+1}.** 🎯 {log_entry}")
                    else:
                        st.write(f"**{i+1}.** {log_entry}")
                
                if hasattr(st.session_state, 'optimization_iterations'):
                    st.write(f"**Total iterations:** {st.session_state.optimization_iterations}")
    
    st.markdown("---")


def create_validation_section(route_df, stops_with_coords):
    """Create validation section showing constraint analysis"""
    from services.optimization import validate_route_constraints, calculate_time_breakdown
    
    st.subheader("🔍 Route Validation")
    
    # Run validation
    validation = validate_route_constraints(route_df, st.session_state, stops_with_coords)
    
    # Create columns for validation results
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Show validation status
        if validation['is_valid']:
            st.success("✅ Route constraints are valid!")
        else:
            st.error("❌ Route constraints have issues that need fixing")
        
        # Show errors
        if validation['errors']:
            st.subheader("🚨 Critical Issues")
            for error in validation['errors']:
                st.error(f"**Error:** {error}")
        
        # Show warnings  
        if validation['warnings']:
            st.subheader("⚠️ Warnings")
            for warning in validation['warnings']:
                st.warning(f"**Warning:** {warning}")
                
        # Show helpful info
        st.subheader("📊 Analysis")
        info = validation['info']
        
        st.write(f"**Total Distance:** {info['total_distance']:.1f} km")
        st.write(f"**Required stops for max gap constraint:** {info['required_stops_for_gap']} stops")
        
        # Time breakdown with minimum stops
        time_breakdown = calculate_time_breakdown(route_df, st.session_state, len(st.session_state.selected_stops))
        st.write(f"**Time with {len(st.session_state.selected_stops)} stops:**")
        st.write(f"  - Running: {time_breakdown['running_time_formatted']}")
        st.write(f"  - Stops: {time_breakdown['stop_time_formatted']}")  
        st.write(f"  - **Total: {time_breakdown['total_time_formatted']}**")
        
        marathon_goal = f"{st.session_state.total_marathon_hours}h {st.session_state.total_marathon_minutes}m"
        st.write(f"**Marathon Goal:** {marathon_goal}")
    
    with col2:
        # Show optimization status
        st.metric(
            "Route Status", 
            "Optimized" if st.session_state.route_optimized else "Not Optimized",
            delta="Ready" if validation['is_valid'] else "Fix Issues First"
        )
        
        # Show key numbers
        st.metric("Total Distance", f"{info['total_distance']:.1f} km")
        st.metric("Min Required Stops", info['required_stops_for_gap'])
        
        # Show current gap if available
        if 'max_current_gap' in info and st.session_state.selected_stops:
            gap_status = "+✅" if info['max_current_gap'] <= st.session_state.max_distance_between_stops else "-❌"
            st.metric(
                "Largest Gap", 
                f"{info['max_current_gap']:.1f} km",
                delta=f"{gap_status} vs {st.session_state.max_distance_between_stops}km limit"
            )
            st.write(f"Between: {info['max_current_gap_between']}")
        
        total_time = time_breakdown['total_time_minutes']
        goal_time = info['marathon_goal_minutes'] 
        buffer = goal_time - total_time
        st.metric(
            "Time Buffer", 
            f"{buffer:.0f} min" if buffer > 0 else f"{abs(buffer):.0f} min over",
            delta="Good" if buffer > 30 else ("Tight" if buffer > 0 else "-Over Goal")
        )
    
    st.markdown("---")


def create_sidebar(stops_df, app_version):
    """Create sidebar with grouped checkboxes"""
    st.sidebar.write(app_version)
    st.sidebar.title("🍷 Wine Stops Selection")
    st.sidebar.markdown("Select the stops you want to visit during the marathon:")
    
    
    # Group stops by wine_rating (stop type)
    stop_groups = stops_df.groupby('wine_rating')
    
    # Define order for stop types
    priority_order = {
        'Must stop': '🔴', 
        'Nice to stop': '🟠', 
        'Can stop': '🔵', 
        'Can skip': '⚪'
    }
    
    selected_stops = []
    
    for stop_type in priority_order.keys():
        if stop_type in stop_groups.groups:
            group_stops = stop_groups.get_group(stop_type)
            
            # Create expander for each group
            with st.sidebar.expander(f"{priority_order[stop_type]} {stop_type} ({len(group_stops)} stops)", expanded=True):
                for idx, row in group_stops.iterrows():
                    stop_key = row['wine_stop']
                    
                    # Create checkbox with stop info
                    food_info = f" {row['food_stop']}" if pd.notna(row['food_stop']) else ""
                    label = f"{row['wine_stop']}{food_info} ({row['approx_km']}km)"
                    
                    is_selected = st.checkbox(
                        label,
                        key=stop_key,
                        value=stop_key in st.session_state.selected_stops,
                        on_change=mark_route_as_not_optimized
                    )
                    
                    if is_selected:
                        selected_stops.append(stop_key)
    
    st.session_state.selected_stops = selected_stops


def create_planned_route_panel(route_df, stops_df, stops_with_coords, selected_stops):
    """Create the planned route panel showing the marathon journey"""
    st.subheader("📍 Planned Route")
    
    if not selected_stops:
        st.info("Select some wine stops to see your planned route")
        return
    
    # Get selected stops data and sort by distance
    selected_stops_data = stops_with_coords[
        stops_with_coords['wine_stop'].isin(selected_stops)
    ].sort_values('approx_km').reset_index(drop=True)
    
    total_distance = route_df['cumulative_distance_km'].max()
    pace_per_km = (st.session_state.running_pace_minutes + 
                   st.session_state.running_pace_seconds / 60)
    
    # Calculate route segments
    route_segments = []
    cumulative_time = 0
    
    # Start to first stop
    if len(selected_stops_data) > 0:
        first_stop = selected_stops_data.iloc[0]
        distance = first_stop['approx_km']
        running_time = distance * pace_per_km
        
        route_segments.append({
            'type': 'running',
            'from': 'START',
            'to': first_stop['wine_stop'],
            'distance': distance,
            'running_time': running_time,
            'cumulative_time': cumulative_time + running_time,
            'from_km': 0,
            'to_km': first_stop['approx_km']
        })
        cumulative_time += running_time
        
        # Add first stop
        route_segments.append({
            'type': 'stop',
            'stop_name': first_stop['wine_stop'],
            'stop_time': st.session_state.time_per_stop,
            'price': first_stop['approx_uk_price_winesearcher'],
            'rating': first_stop['wine_rating'],
            'food': first_stop['food_stop'] if pd.notna(first_stop['food_stop']) else None,
            'cumulative_time': cumulative_time + st.session_state.time_per_stop,
            'km': first_stop['approx_km']
        })
        cumulative_time += st.session_state.time_per_stop
    
    # Between stops
    for i in range(len(selected_stops_data) - 1):
        current_stop = selected_stops_data.iloc[i]
        next_stop = selected_stops_data.iloc[i + 1]
        
        distance = next_stop['approx_km'] - current_stop['approx_km']
        running_time = distance * pace_per_km
        
        route_segments.append({
            'type': 'running',
            'from': current_stop['wine_stop'],
            'to': next_stop['wine_stop'],
            'distance': distance,
            'running_time': running_time,
            'cumulative_time': cumulative_time + running_time,
            'from_km': current_stop['approx_km'],
            'to_km': next_stop['approx_km']
        })
        cumulative_time += running_time
        
        # Add stop
        route_segments.append({
            'type': 'stop',
            'stop_name': next_stop['wine_stop'],
            'stop_time': st.session_state.time_per_stop,
            'price': next_stop['approx_uk_price_winesearcher'],
            'rating': next_stop['wine_rating'],
            'food': next_stop['food_stop'] if pd.notna(next_stop['food_stop']) else None,
            'cumulative_time': cumulative_time + st.session_state.time_per_stop,
            'km': next_stop['approx_km']
        })
        cumulative_time += st.session_state.time_per_stop
    
    # Last stop to finish
    if len(selected_stops_data) > 0:
        last_stop = selected_stops_data.iloc[-1]
        distance = total_distance - last_stop['approx_km']
        running_time = distance * pace_per_km
        
        route_segments.append({
            'type': 'running',
            'from': last_stop['wine_stop'],
            'to': 'FINISH',
            'distance': distance,
            'running_time': running_time,
            'cumulative_time': cumulative_time + running_time,
            'from_km': last_stop['approx_km'],
            'to_km': total_distance
        })
        cumulative_time += running_time
    
    # Display route summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Stops", len(selected_stops))
    with col2:
        st.metric("Total Time", f"{int(cumulative_time//60)}h {int(cumulative_time%60)}m")
    with col3:
        total_wine_cost = selected_stops_data['approx_uk_price_winesearcher'].sum()
        st.metric("Wine Budget", f"£{total_wine_cost}")
    
    # Display route timeline
    st.markdown("---")
    st.markdown("**🗺️ Route Timeline**")
    
    with st.container():
        for i, segment in enumerate(route_segments):
            if segment['type'] == 'running':
                # Running segment
                time_str = f"{int(segment['cumulative_time']//60)}:{int(segment['cumulative_time']%60):02d}"
                
                if segment['from'] == 'START':
                    from_display = "🟢 START (0km)"
                elif segment['from'] == 'FINISH':
                    from_display = f"🏁 FINISH ({segment['from_km']:.1f}km)"
                else:
                    from_display = f"🍷 {segment['from']} ({segment['from_km']:.1f}km)"
                
                if segment['to'] == 'START':
                    to_display = "🟢 START (0km)"
                elif segment['to'] == 'FINISH':
                    to_display = f"🏁 FINISH ({segment['to_km']:.1f}km)"
                else:
                    to_display = f"🍷 {segment['to']} ({segment['to_km']:.1f}km)"
                
                st.write(f"**{time_str}** | 🏃‍♂️ **{segment['distance']:.1f}km** ({int(segment['running_time'])}min) | {from_display} → {to_display}")
                
            else:
                # Stop segment
                time_str = f"{int(segment['cumulative_time']//60)}:{int(segment['cumulative_time']%60):02d}"
                
                # Rating color
                rating_colors = {
                    'Must stop': '🔴',
                    'Nice to stop': '🟠', 
                    'Can stop': '🔵',
                    'Can skip': '⚪'
                }
                rating_icon = rating_colors.get(segment['rating'], '⚪')
                
                food_info = f" {segment['food']}" if segment['food'] else ""
                
                st.write(f"**{time_str}** | {rating_icon} **{segment['stop_name']}** ({segment['km']:.1f}km) | £{segment['price']} | {segment['stop_time']}min{food_info}")
    
    # Show final arrival time
    marathon_goal_minutes = (st.session_state.total_marathon_hours * 60 + 
                            st.session_state.total_marathon_minutes)
    
    st.markdown("---")
    final_time_str = f"{int(cumulative_time//60)}:{int(cumulative_time%60):02d}"
    goal_time_str = f"{st.session_state.total_marathon_hours}:{st.session_state.total_marathon_minutes:02d}"
    
    if cumulative_time <= marathon_goal_minutes:
        time_diff = marathon_goal_minutes - cumulative_time
        st.success(f"🏁 **Finish: {final_time_str}** (Goal: {goal_time_str}) - **{int(time_diff)}min ahead!**")
    else:
        time_diff = cumulative_time - marathon_goal_minutes  
        st.error(f"🏁 **Finish: {final_time_str}** (Goal: {goal_time_str}) - **{int(time_diff)}min over**")
