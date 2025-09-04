"""
Medoc Marathon Route Planner - Plan your wine stops for the famous Medoc Marathon!

This package provides tools for:
- Loading and processing marathon route data
- Interactive map visualization  
- Route optimization based on constraints
- Time and budget planning
- Route validation
"""

__version__ = "0.1.0"

# Import key functionality from subpackages
from .services import (
    load_data,
    interpolate_stop_positions,
    create_map,
    optimize_route,
    validate_route_constraints,
)

from .ui import (
    initialize_session_state,
    create_planning_section,
    create_optimization_section,
    create_validation_section,
    create_sidebar,
    create_planned_route_panel,
)

from .utils import mark_route_as_not_optimized

__all__ = [
    # Core data functions
    "load_data",
    "interpolate_stop_positions",
    
    # Visualization
    "create_map",
    
    # Optimization & validation
    "optimize_route", 
    "validate_route_constraints",
    
    # UI components
    "initialize_session_state",
    "create_planning_section",
    "create_optimization_section", 
    "create_validation_section",
    "create_sidebar",
    "create_planned_route_panel",
    
    # Utilities
    "mark_route_as_not_optimized",
]
