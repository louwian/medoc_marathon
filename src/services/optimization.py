import math
import streamlit as st

def validate_route_constraints(route_df, session_state, stops_with_coords=None, selected_stops_override=None):
    """
    Validate if the user's planning constraints are realistic.
    
    Args:
        route_df: DataFrame with route data
        session_state: Streamlit session state with planning parameters
        stops_with_coords: DataFrame with stop coordinates (optional, for selected stops validation)
        selected_stops_override: List of stops to validate instead of session_state.selected_stops
    
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
    # Use override if provided, otherwise use session_state.selected_stops
    selected_stops_to_validate = selected_stops_override if selected_stops_override is not None else (
        session_state.selected_stops if hasattr(session_state, 'selected_stops') else []
    )
    
    if stops_with_coords is not None and selected_stops_to_validate:
        # Get selected stops data and sort by distance
        selected_stops_data = stops_with_coords[
            stops_with_coords['wine_stop'].isin(selected_stops_to_validate)
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
    
    # Check 4: Total number of stops doesn't exceed max stops
    num_selected_stops = len(selected_stops_to_validate)
    validation_results['info']['num_selected_stops'] = num_selected_stops
    
    if num_selected_stops > max_stops:
        validation_results['errors'].append(
            f"You have selected {num_selected_stops} stops, which exceeds your maximum of {max_stops} stops. "
            f"Remove {num_selected_stops - max_stops} stops or increase your maximum stops limit."
        )
        validation_results['is_valid'] = False
    elif num_selected_stops > max_stops * 0.9:  # Within 90% of limit
        validation_results['warnings'].append(
            f"You have {num_selected_stops} stops selected, close to your maximum of {max_stops} stops."
        )
    
    # Check 5: Total time doesn't exceed marathon goal time
    if selected_stops_to_validate:  # Only check if we have stops selected
        total_time_with_selected = running_time + (num_selected_stops * time_per_stop)
        validation_results['info']['total_time_with_selected_stops'] = total_time_with_selected
        
        if total_time_with_selected > marathon_time_minutes:
            time_over = total_time_with_selected - marathon_time_minutes
            validation_results['errors'].append(
                f"With {num_selected_stops} stops, you'd need {total_time_with_selected:.0f} minutes "
                f"({total_time_with_selected//60:.0f}h {total_time_with_selected%60:.0f}m), "
                f"which is {time_over:.0f} minutes over your {marathon_time_minutes:.0f} minute goal. "
                f"Consider: removing stops, faster pace, or longer marathon time."
            )
            validation_results['is_valid'] = False
        elif total_time_with_selected > marathon_time_minutes * 0.95:  # Within 95% of goal
            buffer = marathon_time_minutes - total_time_with_selected
            validation_results['warnings'].append(
                f"Very tight schedule: only {buffer:.0f} minutes buffer with {num_selected_stops} stops. "
                f"Consider reducing stops for safety margin."
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
    Holistic optimization using validation-driven approach.
    After each change, all constraints are re-validated.
    
    Returns:
        dict: Optimization results with new selection and status
    """
    import pandas as pd
    
    # Get current selected stops
    selected_stops = list(session_state.selected_stops) if hasattr(session_state, 'selected_stops') else []
    optimization_log = []
    optimization_log.append(f"Starting holistic optimization with {len(selected_stops)} selected stops")
    
    max_iterations = 100  # Prevent infinite loops
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        optimization_log.append(f"\n--- Iteration {iteration} ---")
        
        # Validate current state
        validation = validate_route_constraints(route_df, session_state, stops_with_coords, selected_stops)
        optimization_log.append(f"Current selection: {len(selected_stops)} stops")
        optimization_log.append(f"Validation: {'✔️ VALID' if validation['is_valid'] else '❌ INVALID'}")
        
        # Log any warnings
        for warning in validation['warnings']:
            optimization_log.append(f"⚠️  {warning}")
        
        # If valid, try to optimize further (add valuable stops if possible)
        if validation['is_valid']:
            optimization_log.append("Current solution is valid - attempting optimization...")
            
            # Try to add a valuable stop if we have capacity
            improvement_made = try_add_valuable_stop(
                selected_stops, stops_with_coords, session_state, route_df, optimization_log
            )
            
            if not improvement_made:
                optimization_log.append("No further improvements possible - optimization complete")
                break
        
        # If invalid, address the errors
        else:
            optimization_log.append("Addressing constraint violations...")
            for error in validation['errors']:
                optimization_log.append(f"❌ {error}")
            
            # Address the most critical error first
            error_addressed = address_constraint_violation(
                selected_stops, stops_with_coords, session_state, route_df, 
                validation, optimization_log
            )
            
            if not error_addressed:
                optimization_log.append("❌ Cannot address constraint violations - optimization failed")
                break
    
    if iteration >= max_iterations:
        optimization_log.append("⚠️  Maximum iterations reached")
    
    return {
        'optimized_stops': selected_stops,
        'optimization_log': optimization_log,
        'iterations': iteration,
        'success': iteration < max_iterations
    }


def address_constraint_violation(selected_stops, stops_with_coords, session_state, route_df, validation, optimization_log):
    """
    Address the most critical constraint violation based on validation results.
    Returns True if a change was made, False if no solution found.
    """
    
    # Priority 1: Too many stops (detected by Check 4 validation)
    for error in validation['errors']:
        if "exceeds your maximum of" in error and "stops" in error:
            return handle_too_many_stops(selected_stops, stops_with_coords, session_state, optimization_log)
    
    # Priority 2: Time constraint violation (detected by Check 5 validation)
    for error in validation['errors']:
        if "minutes over your" in error and "minute goal" in error:
            return handle_time_violation(selected_stops, stops_with_coords, session_state, optimization_log)
    
    # Priority 3: Gap constraint violations
    for error in validation['errors']:
        if "exceeds your" in error and "km limit" in error:
            return handle_gap_violation(selected_stops, stops_with_coords, session_state, route_df, optimization_log)
        if "you need at least" in error and "stops" in error:
            return handle_insufficient_stops_for_gaps(selected_stops, stops_with_coords, session_state, route_df, optimization_log)
    
    return False


def handle_too_many_stops(selected_stops, stops_with_coords, session_state, optimization_log):
    """Remove lowest value stops to meet max_stops constraint."""
    if len(selected_stops) <= session_state.max_stops:
        return False
    
    optimization_log.append(f"Removing {len(selected_stops) - session_state.max_stops} stops to meet max_stops constraint")
    
    # Get selected stops data with prices
    selected_stops_data = stops_with_coords[
        stops_with_coords['wine_stop'].isin(selected_stops)
    ].copy()
    
    # Sort by price (lowest first) and remove lowest priced ones
    selected_stops_data = selected_stops_data.sort_values('approx_uk_price_winesearcher')
    stops_to_remove = len(selected_stops) - session_state.max_stops
    
    for i in range(stops_to_remove):
        stop_to_remove = selected_stops_data.iloc[i]
        selected_stops.remove(stop_to_remove['wine_stop'])
        optimization_log.append(f"Removed {stop_to_remove['wine_stop']} (£{stop_to_remove['approx_uk_price_winesearcher']})")
    
    return True


def handle_time_violation(selected_stops, stops_with_coords, session_state, optimization_log):
    """Remove lowest value stops to meet time constraints."""
    if len(selected_stops) == 0:
        return False
    
    optimization_log.append("Removing lowest value stop to address time constraint")
    
    # Get selected stops data with prices
    selected_stops_data = stops_with_coords[
        stops_with_coords['wine_stop'].isin(selected_stops)
    ].copy()
    
    # Remove the lowest priced stop
    lowest_value_stop = selected_stops_data.loc[selected_stops_data['approx_uk_price_winesearcher'].idxmin()]
    selected_stops.remove(lowest_value_stop['wine_stop'])
    optimization_log.append(f"Removed {lowest_value_stop['wine_stop']} (£{lowest_value_stop['approx_uk_price_winesearcher']})")
    
    return True


def handle_gap_violation(selected_stops, stops_with_coords, session_state, route_df, optimization_log):
    """Add stops to fill gaps that exceed max_distance_between_stops."""
    total_distance = route_df['cumulative_distance_km'].max()
    max_gap = session_state.max_distance_between_stops
    
    # Get current selected stops data sorted by distance
    current_selected = stops_with_coords[
        stops_with_coords['wine_stop'].isin(selected_stops)
    ].sort_values('approx_km').reset_index(drop=True)
    
    # Find the largest gap that exceeds the limit
    largest_gap = find_largest_gap_violation(current_selected, total_distance, max_gap)
    
    if not largest_gap:
        return False
    
    optimization_log.append(f"Filling {largest_gap['gap']:.1f}km gap between {largest_gap['before_stop']} and {largest_gap['after_stop']}")
    
    # Find available stops in this gap range
    available_stops = stops_with_coords[
        (stops_with_coords['approx_km'] > largest_gap['start_km']) &
        (stops_with_coords['approx_km'] < largest_gap['end_km']) &
        (~stops_with_coords['wine_stop'].isin(selected_stops))
    ]
    
    if len(available_stops) == 0:
        optimization_log.append("No available stops found in gap")
        return False
    
    # Select the highest priced stop in the gap (best value)
    best_stop = available_stops.loc[available_stops['approx_uk_price_winesearcher'].idxmax()]
    selected_stops.append(best_stop['wine_stop'])
    optimization_log.append(f"Added {best_stop['wine_stop']} (£{best_stop['approx_uk_price_winesearcher']}) at {best_stop['approx_km']:.1f}km")
    
    return True


def handle_insufficient_stops_for_gaps(selected_stops, stops_with_coords, session_state, route_df, optimization_log):
    """Add stops when minimum required for gap constraint isn't met."""
    optimization_log.append("Adding stops to meet minimum required for gap constraints")
    
    # Find the best available stop overall
    available_stops = stops_with_coords[
        ~stops_with_coords['wine_stop'].isin(selected_stops)
    ]
    
    if len(available_stops) == 0:
        optimization_log.append("No available stops to add")
        return False
    
    # Add the highest value stop
    best_stop = available_stops.loc[available_stops['approx_uk_price_winesearcher'].idxmax()]
    selected_stops.append(best_stop['wine_stop'])
    optimization_log.append(f"Added {best_stop['wine_stop']} (£{best_stop['approx_uk_price_winesearcher']}) at {best_stop['approx_km']:.1f}km")
    
    return True


def try_add_valuable_stop(selected_stops, stops_with_coords, session_state, route_df, optimization_log):
    """
    Try to add a valuable stop if we have capacity (time and stop count).
    Uses validate_route_constraints to check all constraints for each potential addition.
    Returns True if a stop was added, False otherwise.
    """
    # Get remaining stops sorted by value (price)
    available_stops = stops_with_coords[
        ~stops_with_coords['wine_stop'].isin(selected_stops)
    ].sort_values('approx_uk_price_winesearcher', ascending=False)
    
    # Try to add the most valuable stop that doesn't create constraint violations
    for _, candidate_stop in available_stops.iterrows():
        # Create test selection with this stop
        test_stops = selected_stops + [candidate_stop['wine_stop']]
        
        # Validate this potential addition
        test_validation = validate_route_constraints(route_df, session_state, stops_with_coords, test_stops)
        
        if test_validation['is_valid']:
            selected_stops.append(candidate_stop['wine_stop'])
            optimization_log.append(f"Added valuable stop: {candidate_stop['wine_stop']} (£{candidate_stop['approx_uk_price_winesearcher']}) at {candidate_stop['approx_km']:.1f}km")
            return True
        else:
            optimization_log.append(f"Cannot add {candidate_stop['wine_stop']}: would violate constraints")
    
    optimization_log.append("No valuable stops can be added without violating constraints")
    return False


def find_largest_gap_violation(current_selected, total_distance, max_gap):
    """Find the largest gap that exceeds max_gap."""
    gaps = []
    
    if len(current_selected) == 0:
        return None
    
    # Gap from start to first stop
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
    
    # Return the largest gap
    return max(gaps, key=lambda x: x['gap']) if gaps else None
