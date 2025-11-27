# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TravelWorld (TravelPlanner) is an intelligent travel itinerary planning platform that combines **LLM creativity** with **algorithmic precision** to deliver practical, personalized travel plans. The core differentiator is solving the "multi-entrance backtracking problem" for large attractions and dynamically adjusting planning strategies based on trip proximity.

**Architecture Philosophy**: "Sandwich Architecture"
- **Upper Layer (LLM)**: Intent recognition, POI recommendations, narrative generation
- **Middle Layer (Algorithm)**: Geocoding, multi-entrance calculation, route optimization (TSP)
- **Lower Layer (LLM)**: Polishing final itinerary with conversational text

**Tech Stack**:
- Backend: Python Flask + AMap APIs + DeepSeek AI + OR-Tools
- Frontend: Vanilla HTML/CSS/JavaScript + AMap JavaScript API
- Dependencies: See `backend/requirements.txt` (Flask, CORS, requests, openai, ortools, numpy)

## Development Commands

### Backend Setup and Running
```bash
cd backend
pip install -r requirements.txt

# Set environment variables
export AMAP_API_KEY=your_amap_api_key
export DEEPSEEK_API_KEY=your_deepseek_api_key

# Run server
python app.py
```
- Backend runs on `http://localhost:8888` (configurable in `config.py`)
- API key configuration: `backend/config.py:14-19`

### Frontend Setup
- Open `frontend/index.html` in a browser
- Update AMap API key at `frontend/index.html:8`

### Testing Route Optimization
```bash
cd backend
python -c "from services.route_optimizer import RouteOptimizer; print(RouteOptimizer)"
```

## Core Architecture

### Backend Structure

```
backend/
├── app.py                    # Flask app entry point, blueprint registration
├── config.py                 # Centralized configuration (API keys, constants)
├── routes/
│   ├── itinerary.py         # POST /api/itinerary/generate, /api/assistant/chat
│   ├── map.py               # POST /api/route/planning, GET /api/weather/info
│   └── poi.py               # POI CRUD operations
├── services/
│   ├── amap_service.py      # AMap API wrapper (geocoding, routing, POI search, weather)
│   ├── ai_service.py        # DeepSeek AI client wrapper
│   ├── route_optimizer.py   # OR-Tools TSP solver + greedy fallback
│   └── itinerary_builder.py # Main orchestrator: integrates AI + maps + optimization
└── utils/
    ├── geo_utils.py         # Haversine distance, coordinate batch processing
    ├── json_fixer.py        # Robust JSON parsing for truncated LLM responses
    └── prompts.py           # Prompt templates for LLM itinerary generation
```

### Key Modules

#### 1. `itinerary_builder.py` - Main Orchestrator
**Flow**: `build_itinerary()` at line 40
1. Validate user preferences (destination, dates, budget, travelers, styles)
2. Calculate trip duration
3. Fetch POI data (scenic spots, food, hotels, cultural, shopping, parent-child)
4. Fetch weather data
5. Generate AI itinerary using structured prompt
6. Enrich itinerary with coordinates and transportation

**Critical Methods**:
- `_fetch_poi_data()` (line 128): Fetches all POI categories from AMap
- `_generate_ai_itinerary()` (line 202): Constructs prompt and calls AI
- `_enrich_itinerary()` (line 299): Adds coordinates, calculates transportation
- `_resolve_activity_coordinates()` (line 410): Geocoding cascade (AI coords → geocode → POI search → default)
- `_calculate_transportation()` (line 453): Calculates routes between consecutive activities

#### 2. `route_optimizer.py` - TSP Solver
**Algorithm**: Uses OR-Tools Constraint Solver with guided local search
- `optimize_route()` (line 39): Main entry point
- `_solve_with_ortools()` (line 78): Professional TSP solver (>2 POIs)
- `_greedy_nearest_neighbor()` (line 155): Fallback for small problems or OR-Tools unavailable
- `_apply_weights()` (line 258): **Extension point** for weather/traffic penalties

**Distance Matrix**: Built using Haversine formula (`_calculate_distance()` at line 226)

**Search Parameters** (line 123-130):
- Strategy: `PATH_CHEAPEST_ARC`
- Metaheuristic: `GUIDED_LOCAL_SEARCH`
- Timeout: 5 seconds

#### 3. `amap_service.py` - AMap API Client
**Core Methods**:
- `search_scenic_spots()`, `search_food()`, `search_hotels()`, etc.: POI category search
- `geocode()`: Address → coordinates
- `regeocode()`: Coordinates → address
- `get_distance()`: Fast distance/duration estimation
- `get_walking_route()`, `get_driving_route()`, `get_transit_route()`: Detailed routing with polylines
- `get_weather()`: Weather forecast

**Polyline Format**: Returns uncompressed `"lng,lat;lng,lat;..."` format (NOT AMap's compressed format)

#### 4. `ai_service.py` - DeepSeek Client
- `generate_itinerary()`: Structured JSON generation with dynamic token calculation
- Token formula: `days * 800 + 500`
- Model: `deepseek-chat`
- System prompt emphasizes JSON structure compliance

### Frontend Architecture

**Main Files**:
- `frontend/index.html`: UI structure, AMap SDK loading
- `frontend/script.js`: All application logic (see line references below)
- `frontend/style.css`: Styling

**Key Functions** (`script.js`):
- `generateItineraryWithAI()`: Collects user input, calls backend `/api/itinerary/generate`
- `generateDailySessions()`: Renders itinerary HTML
- `initDayMap()`: Creates AMap instance per day
- `drawRouteOnMap()`: Renders polylines from backend data
- `parseUncompressedPolyline()` (line 685-705): **CRITICAL** - Parses `"lng,lat;lng,lat"` format
- `planAllRoutes()`: Triggers route rendering for all days

**Global State**:
- `userPreferences`: User form input
- `itinerary`: Fetched itinerary data (set at line 476)
- `chatHistory`: AI chat conversation

**Map Integration**:
- AMap JS API v1.4.15 from CDN
- Each day has its own map container: `day{N}-map`
- Route colors: Walking (green `#29b380`), Driving (blue `#4361ee`), Transit (red `#fa7070`)

## API Reference

### Itinerary Generation
```http
POST /api/itinerary/generate
Content-Type: application/json

{
  "destinationCity": "北京",
  "originCity": "上海",          // Optional
  "startDate": "2023-10-01",
  "endDate": "2023-10-03",
  "budget": "3000-5000",
  "budgetType": "range",
  "customBudget": "",             // Optional
  "travelers": 2,
  "travelStyles": ["culture", "food"]
}
```

**Response**: JSON with `{ "itinerary": [...], "summary": {...} }`

### AI Chat Assistant
```http
POST /api/assistant/chat
Content-Type: application/json

{
  "message": "推荐北京的美食",
  "history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

### Route Planning
```http
POST /api/route/planning
{
  "origin": "116.397428,39.90923",
  "destination": "116.480656,39.989576",
  "waypoints": ["116.4,39.95"],  // Optional
  "strategy": 0                  // 0: fastest, 1: shortest, 2: avoid highway
}
```

### Weather
```http
GET /api/weather/info?city=北京
```

## Configuration (`config.py`)

**API Keys** (lines 14-19):
- `AMAP_API_KEY`: From `os.environ` or hardcoded default
- `DEEPSEEK_API_KEY`: From `os.environ` or hardcoded default
- **Security Note**: Default keys are hardcoded for development only

**Transport Thresholds** (lines 42-53):
- Distance < 1000m → Walking
- Distance 1000-5000m → Transit (subway/bus)
- Distance > 5000m → Driving/taxi

**Route Optimization Settings** (lines 55-59):
- Weather weight: 0.2
- Traffic weight: 0.3
- Distance weight: 0.5

**Default Coordinates**: Beijing (116.397428, 39.90923)

## Planned Features & Reference Projects

This project will integrate techniques from three sibling projects in the parent directory:

### 1. Integration with `amap-mcp-server` (Python MCP Server)

**Purpose**: No-database dynamic POI resolution with multi-entrance support

**Key Functions to Port** (from `amap-mcp-server/server.py`):
- `maps_text_search(keywords, city)`: Main POI coordinates
- `maps_around_search(location, keywords="门|出入口")`: **CRITICAL** - Find all gates/entrances
- `maps_search_detail(id)`: Determine if POI is a large scenic area
- `maps_distance(origins, destination)`: Distance matrix calculation

**Planned Implementation** (`backend/services/amap_service.py`):
```python
def get_poi_gates(poi_name: str, city: str) -> List[Dict]:
    """
    Get all entrances/exits for a POI.

    Steps:
    1. Search main POI coordinates
    2. Use maps_around_search(location, keywords="门|出入口", radius=2000)
    3. Return list of gate coordinates
    """
    pass
```

**Algorithm**: Vector-based Gate Selection (`route_optimizer.py` extension)
- For route A → B → C:
  - Find all gates of B: {g1, g2, ...}
  - Calculate min(distance(A, gi)) → Entry_B
  - Calculate min(distance(gj, C)) → Exit_B
  - Ensure Entry_B ≠ Exit_B for large attractions (force traversal)

**Reference Implementation Ideas**:
- Use `maps_distance` for batch distance calculations (line 77 in `amap-mcp-server/README.md`)
- Check POI type via `maps_search_detail` to determine if multi-entrance logic applies

### 2. Integration with `graphhopper` (Java Routing Engine)

**Purpose**: Learn advanced weighting and custom routing strategies

**Key Concepts to Study**:
- `graphhopper/core/.../weighting/SpeedWeighting.java`: Dynamic edge weights based on road conditions
- `graphhopper/core/.../weighting/custom/CustomWeighting.java`: Injecting custom parameters (weather, user preferences)
- `VirtualEdgeIterator`: Concept of snapping POIs to road network (adapt for gate snapping)

**Planned Implementation** (`route_optimizer.py` enhancement):
```python
def _apply_weights(distance_matrix, pois, weather_data, traffic_data):
    """
    Cost = Distance × w1 + Duration × w2 + WeatherPenalty

    WeatherPenalty logic (inspired by CustomWeighting.java):
    - If rain: increase cost for outdoor attractions, walking routes
    - If traffic jam: increase cost for driving routes
    - If near-term trip: use real-time traffic data
    """
    pass
```

**Time-Sensitive Strategy** (from DESIGN.md line 24-28):
- Far-future trips: Distance-weighted (traffic/weather uncertain)
- Near-term trips: Call AMap's real-time traffic + weather APIs, adjust penalties dynamically

### 3. Integration with `tripper` (Kotlin/Spring Boot Agent)

**Purpose**: Stylized prompt engineering and multi-LLM orchestration

**Key Files to Study**:
- `tripper/src/.../TripperAgent.kt`: Persona definitions, style customization
- `tripper/src/.../agent/domain.kt`: Structured travel preferences (Preferences class)
- Agent architecture: How to coordinate multiple LLMs (Claude Sonnet + GPT-4o-mini)

**Planned Implementation** (`utils/prompts.py` enhancement):
```python
STYLE_PERSONAS = {
    "photography": """
        You are a travel photographer. Focus on:
        - Golden hour timing (sunrise/sunset)
        - Iconic viewpoints
        - Photo-friendly cafes
    """,
    "foodie": """
        You are a food critic. Prioritize:
        - Michelin/high-rated restaurants
        - Local street food
        - Meal timing aligned with restaurant hours
    """,
    "adventure": """
        You are an adventure guide. Include:
        - Hiking trails, biking routes
        - Outdoor activities
        - Physical challenge levels
    """
}

def build_itinerary_generation_prompt(..., travel_styles):
    persona = STYLE_PERSONAS.get(travel_styles[0], "")
    # Inject persona into system prompt
```

**Custom Prompt Support** (DESIGN.md line 40):
- User input like "traveling with elderly parents, minimize walking"
- Append to system prompt to adjust POI selection and route weights

### 4. Planned Algorithm Enhancements (from DESIGN.md)

**Multi-Strategy Route Planning** (line 33):
- Generate 3 route variants: "fastest", "fewest transfers", "shortest distance"
- Use OR-Tools with different cost functions
- Present all 3 options to user

**Dynamic Weight Calculation** (line 79):
```python
# Pseudo-code for future implementation
Cost = Distance × w_distance + Duration × w_duration + WeatherPenalty + TrafficPenalty

# Weather penalty (line 86-90 in DESIGN.md)
if weather == "rainy":
    if poi_type == "outdoor":
        WeatherPenalty += 5000  # Heavily discourage outdoor activities
    if transport_mode == "walking" or transport_mode == "cycling":
        WeatherPenalty += 2000  # Discourage walking in rain

# Traffic penalty (near-term trips only)
if days_until_trip < 7:
    realtime_duration = amap_service.get_driving_route_with_traffic(...)
    TrafficPenalty = (realtime_duration - estimated_duration) × w_traffic
```

## Development Roadmap (from DESIGN.md)

### Phase 1: API Integration Layer (`backend/services/amap_service.py`)
- [ ] Port core functions from `amap-mcp-server/server.py`
  - `maps_text_search`, `maps_weather`, `maps_distance`, `maps_around_search`
- [ ] Implement `get_poi_gates(poi_name)`: Search main POI → Search nearby gates
- [ ] Add caching layer for POI/gate data to reduce API calls

### Phase 2: Core Algorithm Layer (`backend/services/route_optimizer.py`)
- [ ] Implement `calculate_optimized_route(poi_list, date_proximity)`
  - Support 3 optimization strategies (fastest/fewest-transfers/shortest)
- [ ] Implement `optimize_gates_for_sequence()`
  - Vector-based gate selection algorithm (DESIGN.md line 67-74)
- [ ] Add weather/traffic penalty logic to `_apply_weights()`

### Phase 3: Business Logic Layer (`backend/services/itinerary_builder.py`)
- [ ] Integrate gate optimization into `_enrich_activities()`
  - Call `get_poi_gates()` for attractions
  - Pass to `optimize_gates_for_sequence()`
- [ ] Construct structured gate data for LLM prompt:
  ```json
  {"poi": "故宫", "entry": "午门", "exit": "神武门", "reason": "minimizes backtracking"}
  ```
- [ ] Update prompt to instruct LLM to use gate info in narrative

### Phase 4: Frontend & UX Enhancements
- [ ] Add style selection UI (photography/foodie/adventure/custom)
- [ ] Add budget range picker
- [ ] Display 3 route options with comparison table
- [ ] Add interactive chat sidebar with "Add to itinerary" buttons

## Key Technical Details

### JSON Parsing Robustness
**Problem**: LLM responses truncated due to token limits (especially for long trips)

**Solution**: `utils/json_fixer.py` (lines 37-107 in old app.py)
- Removes markdown code blocks
- Fixes missing commas between objects/arrays
- Balances brackets and quotes
- Intelligently truncates to last valid delimiter if unfixable

**Usage**: Called in `itinerary_builder.py:285` after AI response parsing fails

### Coordinate Resolution Cascade
**Priority** (`itinerary_builder.py:410-451`):
1. AI-provided coordinates (if valid float)
2. AMap geocoding API with full address
3. AMap POI text search using activity title
4. Default Beijing coordinates (116.397428, 39.90923)

**Logging**: All coordinate resolutions logged at INFO level for debugging

### Transportation Calculation Logic
**Rules** (`itinerary_builder.py:453-519`):
- First activity of first day: No transportation (user gets there independently)
- First activity of subsequent days: From last activity of previous day
- Other activities: From previous activity in same day

**Mode Selection** (`config.py:42-46`):
- Based on distance thresholds
- Future: Will incorporate weather/traffic penalties

### Polyline Handling
**Backend** (`amap_service.py`):
- Returns uncompressed format: `"lng1,lat1;lng2,lat2;..."`
- NOT using AMap's compressed polyline format

**Frontend** (`script.js:685-705`):
- Custom parser: `parseUncompressedPolyline()`
- Splits by `;`, then by `,` to extract [lng, lat] pairs
- Debug logs at lines 818, 831 for troubleshooting

**Common Issue**: If polylines don't render, check:
1. Backend logs for polyline format
2. Frontend console for parsing errors
3. Confirm format is uncompressed (not Base64/GZip compressed)

## Common Development Tasks

### Adding New POI Category
1. Add search method to `amap_service.py` (e.g., `search_adventure()`)
2. Call in `itinerary_builder.py:_fetch_poi_data()` around line 140-190
3. Add to `poi_data` dict (line 140)
4. Update prompt template in `utils/prompts.py` to mention new category

### Modifying Transportation Logic
- Mode selection: `itinerary_builder.py:521` (calls `config.py:42-46`)
- Route fetching: `itinerary_builder.py:530` (dispatches to walking/transit/driving)
- Frontend rendering: `script.js:782-858` (drawRouteOnMap)

### Debugging OR-Tools Optimization
**Check if OR-Tools is available**:
```python
from services.route_optimizer import ORTOOLS_AVAILABLE
print(ORTOOLS_AVAILABLE)  # Should be True
```

**Force greedy fallback** (for testing):
```python
# In route_optimizer.py:70, change:
if ORTOOLS_AVAILABLE and len(pois) > 2:
# To:
if False:  # Force greedy algorithm
```

**Adjust solver timeout** (`route_optimizer.py:130`):
```python
search_parameters.time_limit.seconds = 10  # Increase for complex routes
```

### Testing Multi-Entrance Logic (Future)
1. Add test POI with known multiple entrances (e.g., 故宫, 天坛)
2. Call `get_poi_gates("故宫", "北京")`
3. Verify gate list contains "午门", "神武门", etc.
4. Test `optimize_gates_for_sequence()` with A→故宫→B route
5. Confirm entry ≠ exit for large attractions

### Extending Weather/Traffic Weights
**Current state**: Placeholder at `route_optimizer.py:258-294`

**Implementation steps**:
1. Fetch weather via `amap_service.get_weather()`
2. Check `weather_data['forecasts'][0]['casts'][day_index]`
3. If `dayweather` contains "雨":
   - Multiply outdoor POI distances by 1.5
   - Multiply walking/cycling routes by 1.3
4. For traffic (near-term trips):
   - Use `amap_service.get_driving_route(origin, dest)` with real-time traffic
   - Compare `duration` vs baseline → add penalty if significantly longer

## Known Limitations & Future Work

**Current Limitations**:
- No user authentication system
- History feature not implemented (shows placeholder alert)
- Single-entrance assumption for all POIs (multi-entrance logic planned)
- Static transportation mode selection (no weather/traffic consideration)
- No route optimization across multiple days (only within each day)
- Frontend embeds API keys (security risk)

**Planned Improvements** (from README.md):
- [ ] Complete route optimization algorithm with multi-entrance support
- [ ] User authentication system
- [ ] Offline map support
- [ ] Mobile responsive design
- [ ] Community sharing features
- [ ] Multi-strategy route comparison (fastest/shortest/fewest-transfers)
- [ ] Real-time traffic integration for near-term trips

**Technical Debt**:
- Hardcoded API keys in `config.py` and `frontend/index.html`
- No rate limiting on API endpoints
- No database (all data fetched on-demand)
- Limited error handling for AI response parsing
- OR-Tools timeout may be insufficient for >20 POIs

## Environment Setup

**Required Environment Variables**:
```bash
export AMAP_API_KEY=your_amap_key_here
export DEEPSEEK_API_KEY=your_deepseek_key_here
```

**Get API Keys**:
- AMap: https://console.amap.com/
- DeepSeek: https://platform.deepseek.com/

**Dependencies**:
- Python 3.8+
- Flask 2.3.2
- Flask-CORS 4.0.0
- requests 2.31.0
- openai 1.3.5 (for DeepSeek client)
- ortools ≥9.7.0 (TSP solver)
- numpy ≥1.24.0

**Install**:
```bash
cd backend
pip install -r requirements.txt
```

## Debugging Tips

**Enable verbose logging**:
```python
# In app.py:17
logging.basicConfig(level=logging.DEBUG, ...)
```

**Check AI response truncation**:
- Look for "JSON parsing failed, attempting to fix" in logs
- Check `itinerary_builder.py:281`
- If persistent, increase `max_tokens` in `ai_service.py`

**Verify AMap API connectivity**:
```python
from services.amap_service import AmapService
service = AmapService()
result = service.search_scenic_spots("北京")
print(len(result))  # Should return >0
```

**Frontend map not loading**:
- Open browser console
- Check for AMap API key errors
- Verify `frontend/index.html:8` has correct key

**Polylines not rendering**:
- Check `script.js:818, 831` console logs for parsed coordinates
- Verify backend returns `polyline` field in transportation data
- Confirm format: `"lng,lat;lng,lat;..."` (semicolon-separated, not comma-only)

## Project Context

**Location**: `D:\Individual\Study\InnovativeThinking\Project\TravelPlanner`

**Related Projects** (sibling directories):
- `../amap-mcp-server`: AMap MCP server (Python) - POI search, routing, geocoding
- `../tripper`: Embabel travel agent (Kotlin/Spring) - Multi-LLM orchestration, persona-based planning
- `../graphhopper`: Routing engine (Java) - Advanced weighting, custom routing strategies

**Design Document**: See `DESIGN.md` for detailed feature specifications and algorithm explanations
