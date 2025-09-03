# 🍷 Medoc Marathon Route Planner

A comprehensive route planning application for the famous **Médoc Marathon** - the world's longest wine tasting event! This interactive Streamlit application helps you plan your wine stops, optimize your route, and ensure you finish within your target time while enjoying the best châteaux along the way.

## 🏃‍♂️ About the Medoc Marathon

The Médoc Marathon is a unique 42.2km marathon that takes place in the Bordeaux wine region of France. What makes it special:

- **Wine stops**: Over 20 château stops offering wine tastings along the route
- **Food stations**: Traditional French delicacies at various points  
- **Costume theme**: Many participants run in costumes matching the year's theme
- **Time limit**: Usually 6.5 hours to complete the course
- **Scenic route**: Through world-famous vineyards and wine estates

This application helps you plan the perfect balance between running performance and wine enjoyment!

## ✨ Features

### 🗺️ Interactive Route Visualization
- **Interactive map** powered by Folium showing the complete marathon route
- **Wine stop markers** with detailed information (price, rating, distance)
- **Route segments** with start/finish markers
- **Real-time updates** as you select different stops

### 🎯 Smart Route Optimization
- **Constraint-based optimization** considering your time goals and preferences
- **Gap analysis** ensuring you don't go too long between stops
- **Time calculations** with customizable pace and stop durations
- **Budget tracking** for wine purchases along the route

### 📋 Planning Tools
- **Marathon time goals**: Set your target finish time
- **Running pace**: Configure your expected pace per km
- **Stop strategy**: Define min/max stops and time per stop
- **Distance constraints**: Set maximum distance between stops

### 🔍 Route Validation
- **Constraint checking**: Validates if your plan is realistic
- **Time analysis**: Breaks down running vs. stopping time
- **Gap detection**: Identifies problematic distances between stops
- **Success predictions**: Estimates if you'll meet your goals

### 📊 Detailed Timeline
- **Step-by-step route**: Complete timeline from start to finish
- **Cumulative timing**: Track your progress throughout the race
- **Stop details**: Wine prices, ratings, and food options
- **Budget calculation**: Total wine costs for your selected stops

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or higher
- [UV package manager](https://docs.astral.sh/uv/) (recommended) or pip

### Installation

#### Using UV (Recommended)
```bash
# Clone the repository
git clone <repository-url>
cd medoc_marathon

# Install dependencies with UV
uv sync

# Run the application
uv run streamlit run src/main.py
```

#### Using pip
```bash
# Clone the repository
git clone <repository-url>
cd medoc_marathon

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Run the application
streamlit run src/main.py
```

### 🎮 Usage

1. **Open the app** in your browser (usually http://localhost:8501)

2. **Set your race goals** in the "Race Planning" section:
   - Marathon time target (e.g., 6h 30m)
   - Expected running pace (e.g., 6:30/km)
   - Time per stop (e.g., 8 minutes)
   - Min/max number of stops
   - Maximum distance between stops

3. **Select wine stops** in the sidebar:
   - Stops are categorized by priority (Must stop, Nice to stop, etc.)
   - Each shows distance, wine info, and food options

4. **Optimize your route** using the "Route Optimization" section:
   - Click "Optimize Route" to automatically select stops
   - View the optimization log to see what changes were made

5. **Validate your plan** in the "Route Validation" section:
   - Check for constraint violations
   - See time analysis and gap warnings
   - Get recommendations for improvements

6. **Review your timeline** in the "Planned Route" section:
   - See your complete race timeline
   - Track cumulative time and costs
   - Identify potential issues

## 📁 Project Structure

```
medoc_marathon/
├── src/
│   ├── main.py                 # Main Streamlit application
│   ├── services/
│   │   ├── data_processing.py  # Data loading and processing
│   │   ├── kml_processor.py    # KML/KMZ file processing
│   │   ├── map_service.py      # Map creation with Folium
│   │   └── optimization.py     # Route optimization algorithms
│   ├── ui/
│   │   └── ui_components.py    # Streamlit UI components
│   └── utils/
│       └── helpers.py          # Utility functions
├── data/
│   ├── medoc2025.csv              # Wine stop data
│   ├── medoc_marathon_complete_route.csv  # Route coordinates
│   └── Medoc Marathon 2025.kmz    # KMZ file from Google My Maps
├── pyproject.toml              # Project dependencies
└── README.md                   # This file
```

## 🔧 Dependencies

- **streamlit**: Web application framework
- **folium & streamlit-folium**: Interactive maps
- **pandas**: Data manipulation and analysis
- **scipy**: Scientific computing (interpolation)
- **geopy**: Geographic calculations
- **matplotlib & plotly**: Data visualization

## 📊 Data Sources

The application uses three main data files:

1. **`medoc2025.csv`**: Wine stop information including:
   - Stop names and locations
   - Wine ratings and prices
   - Food availability
   - Distance along route

2. **`medoc_marathon_complete_route.csv`**: Complete route coordinates with:
   - GPS coordinates (latitude/longitude)
   - Cumulative distance markers
   - Route segments

3. **`Medoc Marathon 2025.kmz`**: Google My Maps export containing:
   - Route segments
   - Stop locations
   - Additional geographic data

## 🎯 Optimization Algorithm

The route optimizer uses a multi-phase approach:

1. **Constraint validation**: Ensures your goals are mathematically possible
2. **Gap filling**: Adds stops to prevent long distances without wine
3. **Value optimization**: Selects highest-rated/most expensive stops when possible
4. **Time management**: Balances stop quantity with time constraints

---

**Bonne chance et santé!** 🏃‍♂️🍷

*Enjoy planning your perfect balance of running and wine tasting at the Médoc Marathon!*
