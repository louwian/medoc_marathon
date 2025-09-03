import math
import streamlit as st

def validate_route_constraints(route_df, session_state, stops_with_coords=None):
    """
    Validate if the user's planning constraints are realistic.
    
    Args:
        route_df: DataFrame with route data
        session_state: Streamlit session state with planning parameters
        stops_with_coords: DataFrame with stop coordinates (optional, for selected stops validation)
    
    Returns:
        dict: Validation results with success status and messages
    """
    # Extract parameters from session state
    total_distance = route_df['cumulative_distance_km'].max()
    max_gap = session_state.max_distance_between_stops
    min_stops = session_state.min_stops
    max_stops = session_state.max_stops
    time_per_stop = session_state.time_per_stop
    
    # Calculate marathon goal time in minutes
    marathon_time_minutes = (session_state.total_marathon_hours * 60 + 
                           session_state.total_marathon_minutes)
    
    # Calculate pace in minutes per km
    pace_per_km = (session_state.running_pace_minutes + 
                   session_state.running_pace_seconds / 60)
    
    validation_results = {
        'is_valid': True,
        'warnings': [],
        'errors': [],
        'info': {}
    }
    
    # Check 1: Required stops to maintain max gap constraint
    required_stops_for_gap = math.ceil(total_distance / max_gap)
    validation_results['info']['required_stops_for_gap'] = required_stops_for_gap
    validation_results['info']['total_distance'] = total_distance
    
    if required_stops_for_gap < min_stops:
        validation_results['warnings'].append(
            f"Your max gap ({max_gap}km) allows for only {required_stops_for_gap} stops, "
            f"but you want at least {min_stops} stops. Consider reducing max gap or min stops."
        )
    elif required_stops_for_gap > max_stops:
        validation_results['errors'].append(
            f"To maintain max gap of {max_gap}km, you need at least {required_stops_for_gap} stops, "
            f"but your max is {max_stops}. Increase max stops or increase max gap distance."
        )
        validation_results['is_valid'] = False
    

    # Check 2: Time feasibility with minimum stops
    running_time = total_distance * pace_per_km
    stop_time = min_stops * time_per_stop
    total_time_with_min_stops = running_time + stop_time
    
    validation_results['info']['running_time_minutes'] = running_time
    validation_results['info']['stop_time_minutes'] = stop_time
    validation_results['info']['total_time_with_min_stops'] = total_time_with_min_stops
    validation_results['info']['marathon_goal_minutes'] = marathon_time_minutes
    
    if total_time_with_min_stops > marathon_time_minutes:
        time_over = total_time_with_min_stops - marathon_time_minutes
        validation_results['errors'].append(
            f"Even with minimum stops ({min_stops}), you'd need {total_time_with_min_stops:.0f} minutes "
            f"({total_time_with_min_stops//60:.0f}h {total_time_with_min_stops%60:.0f}m), "
            f"which is {time_over:.0f} minutes over your {marathon_time_minutes} minute goal. "
            f"Consider: faster pace, fewer stops, or longer marathon time."
        )
        validation_results['is_valid'] = False
    elif total_time_with_min_stops > marathon_time_minutes * 0.9:  # Within 90% of goal
        buffer = marathon_time_minutes - total_time_with_min_stops
        validation_results['warnings'].append(
            f"Tight schedule: {buffer:.0f} minutes buffer with minimum stops. "
            f"Consider some contingency for slower sections or longer stops."
        )
    
    # Check 3: Validate selected stops don't exceed max gap
    if stops_with_coords is not None and hasattr(session_state, 'selected_stops') and session_state.selected_stops:
        # Get selected stops data and sort by distance
        selected_stops_data = stops_with_coords[
            stops_with_coords['wine_stop'].isin(session_state.selected_stops)
        ].sort_values('approx_km').reset_index(drop=True)
        
        if len(selected_stops_data) > 0:
            # Calculate gaps between consecutive selected stops
            gaps = []
            
            # Gap from start to first stop
            if len(selected_stops_data) > 0:
                first_gap = selected_stops_data.iloc[0]['approx_km']
                if first_gap > 0:
                    gaps.append(('Start', selected_stops_data.iloc[0]['wine_stop'], first_gap))
            
            # Gaps between consecutive stops
            for i in range(len(selected_stops_data) - 1):
                current_stop = selected_stops_data.iloc[i]
                next_stop = selected_stops_data.iloc[i + 1]
                gap = next_stop['approx_km'] - current_stop['approx_km']
                gaps.append((current_stop['wine_stop'], next_stop['wine_stop'], gap))
            
            # Gap from last stop to finish
            if len(selected_stops_data) > 0:
                last_stop = selected_stops_data.iloc[-1]
                final_gap = total_distance - last_stop['approx_km']
                if final_gap > 0:
                    gaps.append((last_stop['wine_stop'], 'Finish', final_gap))

            # Find maximum gap
            max_current_gap = max(gaps, key=lambda x: x[2]) if gaps else None
            validation_results['info']['max_current_gap'] = max_current_gap[2] if max_current_gap else 0

            if max_current_gap[0] == 'Start':
                start = 'Start (0km)'
            else:
                start = f"{max_current_gap[0]} ({stops_with_coords[stops_with_coords['wine_stop'] == max_current_gap[0]]['approx_km'].values[0]:.1f}km)"
            if max_current_gap[1] == 'Finish':
                end = f'Finish ({total_distance:.1f}km)'
            else:
                end = f"{max_current_gap[1]} ({stops_with_coords[stops_with_coords['wine_stop'] == max_current_gap[1]]['approx_km'].values[0]:.1f}km)"
            validation_results['info']['max_current_gap_between'] = f"{start} → {end}" if max_current_gap else "N/A"

            # Check if any gap exceeds the limit
            if max_current_gap and max_current_gap[2] > max_gap:
                validation_results['errors'].append(
                    f"Selected stops have a {max_current_gap[2]:.1f}km gap between "
                    f"'{max_current_gap[0]}' and '{max_current_gap[1]}', which exceeds your "
                    f"{max_gap}km limit. Add more stops or increase max gap distance."
                )
                validation_results['is_valid'] = False
            elif max_current_gap and max_current_gap[2] > max_gap * 0.8:  # Within 80% of limit
                validation_results['warnings'].append(
                    f"Large gap of {max_current_gap[2]:.1f}km between '{max_current_gap[0]}' "
                    f"and '{max_current_gap[1]}' is close to your {max_gap}km limit."
                )
    
    return validation_results


def calculate_time_breakdown(route_df, session_state, num_stops):
    """
    Calculate detailed time breakdown for a given number of stops.
    
    Returns:
        dict: Time breakdown with running time, stop time, and total
    """
    total_distance = route_df['cumulative_distance_km'].max()
    pace_per_km = (session_state.running_pace_minutes + 
                   session_state.running_pace_seconds / 60)
    
    running_time = total_distance * pace_per_km
    stop_time = num_stops * session_state.time_per_stop
    total_time = running_time + stop_time
    
    return {
        'running_time_minutes': running_time,
        'stop_time_minutes': stop_time,
        'total_time_minutes': total_time,
        'running_time_formatted': f"{int(running_time//60)}h {int(running_time%60)}m",
        'stop_time_formatted': f"{int(stop_time//60)}h {int(stop_time%60)}m", 
        'total_time_formatted': f"{int(total_time//60)}h {int(total_time%60)}m"
    }


def optimize_route(route_df, session_state, stops_with_coords):
    """
    Optimize the route selection based on constraints.
    
    Returns:
        dict: Optimization results with new selection and status
    """
    import pandas as pd
    
    # Get current selected stops
    selected_stops = list(session_state.selected_stops) if hasattr(session_state, 'selected_stops') else []
    max_stops = session_state.max_stops
    max_gap = session_state.max_distance_between_stops
    
    optimization_log = []
    optimization_log.append(f"Starting optimization with {len(selected_stops)} selected stops")
    
    # Step 1: Remove lowest price stops if over max_stops limit
    if len(selected_stops) > max_stops:
        optimization_log.append(f"Reducing from {len(selected_stops)} to {max_stops} stops")
        
        # Get selected stops data with prices
        selected_stops_data = stops_with_coords[
            stops_with_coords['wine_stop'].isin(selected_stops)
        ].copy()
        
        # Sort by price (lowest first) and remove lowest priced ones
        selected_stops_data = selected_stops_data.sort_values('approx_uk_price_winesearcher')
        stops_to_remove = len(selected_stops) - max_stops
        
        for i in range(stops_to_remove):
            stop_to_remove = selected_stops_data.iloc[i]
            selected_stops.remove(stop_to_remove['wine_stop'])
            optimization_log.append(f"Removed {stop_to_remove['wine_stop']} (£{stop_to_remove['approx_uk_price_winesearcher']})")
    
    # Step 2: Find and fill gaps that exceed max_gap
    max_iterations = 50  # Prevent infinite loops
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        # Get current selected stops data and sort by distance
        current_selected = stops_with_coords[
            stops_with_coords['wine_stop'].isin(selected_stops)
        ].sort_values('approx_km').reset_index(drop=True)
        
        if len(current_selected) == 0:
            break
            
        # Find gaps
        gaps = []
        total_distance = route_df['cumulative_distance_km'].max()
        
        # Gap from start to first stop
        if len(current_selected) > 0:
            first_gap = current_selected.iloc[0]['approx_km']
            if first_gap > max_gap:
                gaps.append({
                    'start_km': 0,
                    'end_km': current_selected.iloc[0]['approx_km'],
                    'gap': first_gap,
                    'before_stop': 'Start',
                    'after_stop': current_selected.iloc[0]['wine_stop']
                })
        
        # Gaps between consecutive stops
        for i in range(len(current_selected) - 1):
            current_stop = current_selected.iloc[i]
            next_stop = current_selected.iloc[i + 1]
            gap = next_stop['approx_km'] - current_stop['approx_km']
            
            if gap > max_gap:
                gaps.append({
                    'start_km': current_stop['approx_km'],
                    'end_km': next_stop['approx_km'],
                    'gap': gap,
                    'before_stop': current_stop['wine_stop'],
                    'after_stop': next_stop['wine_stop']
                })
        
        # Gap from last stop to finish
        if len(current_selected) > 0:
            last_stop = current_selected.iloc[-1]
            final_gap = total_distance - last_stop['approx_km']
            if final_gap > max_gap:
                gaps.append({
                    'start_km': last_stop['approx_km'],
                    'end_km': total_distance,
                    'gap': final_gap,
                    'before_stop': last_stop['wine_stop'],
                    'after_stop': 'Finish'
                })
        
        # If no gaps found, we're done
        if not gaps:
            optimization_log.append("No gaps exceeding limit found - optimization complete")
            break
        
        # Find the largest gap
        largest_gap = max(gaps, key=lambda x: x['gap'])
        optimization_log.append(f"Found {largest_gap['gap']:.1f}km gap between {largest_gap['before_stop']} and {largest_gap['after_stop']}")
        
        # Find available stops in this gap range
        available_stops = stops_with_coords[
            (stops_with_coords['approx_km'] > largest_gap['start_km']) &
            (stops_with_coords['approx_km'] < largest_gap['end_km']) &
            (~stops_with_coords['wine_stop'].isin(selected_stops))
        ]
        
        if len(available_stops) == 0:
            optimization_log.append(f"No available stops found in gap - cannot optimize further")
            break
        
        # Select the highest priced stop in the gap
        best_stop = available_stops.loc[available_stops['approx_uk_price_winesearcher'].idxmax()]
        selected_stops.append(best_stop['wine_stop'])
        optimization_log.append(f"Added {best_stop['wine_stop']} (£{best_stop['approx_uk_price_winesearcher']}) at {best_stop['approx_km']:.1f}km")
        
        # Check if we've hit the max stops limit
        if len(selected_stops) >= max_stops:
            optimization_log.append(f"Reached maximum stops limit ({max_stops})")
            break
    
    if iteration >= max_iterations:
        optimization_log.append("Warning: Maximum iterations reached")
    
    # Step 3: Add valuable stops if time capacity allows
    optimization_log.append("Adding valuable stops with time capacity")
    
    # Check if we have time buffer
    total_distance = route_df['cumulative_distance_km'].max()
    pace_per_km = (session_state.running_pace_minutes + 
                   session_state.running_pace_seconds / 60)
    marathon_time_minutes = (session_state.total_marathon_hours * 60 + 
                           session_state.total_marathon_minutes)
    
    current_running_time = total_distance * pace_per_km
    current_stop_time = len(selected_stops) * session_state.time_per_stop
    current_total_time = current_running_time + current_stop_time
    time_buffer = marathon_time_minutes - current_total_time
    
    optimization_log.append(f"Current total time: {current_total_time:.0f} min, Buffer: {time_buffer:.0f} min")
    
    if time_buffer > session_state.time_per_stop and len(selected_stops) < max_stops:
        optimization_log.append(f"Time buffer allows for more stops, trying to add valuable ones...")
        
        # Get all remaining stops sorted by price (highest first)
        remaining_stops = stops_with_coords[
            ~stops_with_coords['wine_stop'].isin(selected_stops)
        ].sort_values('approx_uk_price_winesearcher', ascending=False)
        
        phase3_iterations = 0
        for _, candidate_stop in remaining_stops.iterrows():
            phase3_iterations += 1
            
            # Check if we still have time capacity
            potential_stop_time = (len(selected_stops) + 1) * session_state.time_per_stop
            potential_total_time = current_running_time + potential_stop_time
            
            if potential_total_time > marathon_time_minutes:
                optimization_log.append(f"No time capacity for more stops (would exceed goal time by {potential_total_time - marathon_time_minutes:.0f} min)")
                break
            
            if len(selected_stops) >= max_stops:
                optimization_log.append(f"Reached maximum stops limit ({max_stops})")
                break
            
            # Temporarily add this stop
            test_stops = selected_stops + [candidate_stop['wine_stop']]
            
            # Check for gap breaches with this stop added
            test_selected_data = stops_with_coords[
                stops_with_coords['wine_stop'].isin(test_stops)
            ].sort_values('approx_km').reset_index(drop=True)
            
            # Calculate gaps with the new stop
            gaps = []
            
            # Gap from start to first stop
            if len(test_selected_data) > 0:
                first_gap = test_selected_data.iloc[0]['approx_km']
                if first_gap > max_gap:
                    gaps.append(first_gap)
            
            # Gaps between consecutive stops
            for i in range(len(test_selected_data) - 1):
                current_stop = test_selected_data.iloc[i]
                next_stop = test_selected_data.iloc[i + 1]
                gap = next_stop['approx_km'] - current_stop['approx_km']
                if gap > max_gap:
                    gaps.append(gap)
            
            # Gap from last stop to finish
            if len(test_selected_data) > 0:
                last_stop = test_selected_data.iloc[-1]
                final_gap = total_distance - last_stop['approx_km']
                if final_gap > max_gap:
                    gaps.append(final_gap)
            
            # If no gaps exceed the limit, add this stop
            if not gaps:
                selected_stops.append(candidate_stop['wine_stop'])
                optimization_log.append(f"Added valuable stop: {candidate_stop['wine_stop']} (£{candidate_stop['approx_uk_price_winesearcher']}) at {candidate_stop['approx_km']:.1f}km")
                
                # Update time calculations for next iteration
                current_stop_time = len(selected_stops) * session_state.time_per_stop
                current_total_time = current_running_time + current_stop_time
                time_buffer = marathon_time_minutes - current_total_time
                optimization_log.append(f"  New buffer: {time_buffer:.0f} min with {len(selected_stops)} stops")
                
            else:
                max_breach = max(gaps)
                optimization_log.append(f"Cannot add {candidate_stop['wine_stop']} - would create {max_breach:.1f}km gap (limit: {max_gap}km)")
                optimization_log.append("🎯 No more stops can be added without breaching gap constraints")
                break
        
        optimization_log.append(f"Phase 3 complete after checking {phase3_iterations} candidate stops")
    else:
        if time_buffer <= session_state.time_per_stop:
            optimization_log.append(f"Insufficient time buffer ({time_buffer:.0f} min) for additional stops")
        if len(selected_stops) >= max_stops:
            optimization_log.append(f"Already at maximum stops limit ({max_stops})")
    
    final_iterations = iteration + phase3_iterations if 'phase3_iterations' in locals() else iteration
    
    return {
        'optimized_stops': selected_stops,
        'optimization_log': optimization_log,
        'iterations': final_iterations,
        'success': True
    }
