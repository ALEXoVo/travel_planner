# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TravelWorld is an intelligent travel itinerary planning assistant that combines AMap (高德地图) APIs with DeepSeek AI to generate personalized travel plans. The application uses a Flask backend and vanilla HTML/CSS/JavaScript frontend.

## Development Commands

### Backend Setup and Running
```bash
cd backend
pip install -r requirements.txt
python app.py
```
- Backend runs on `http://localhost:8888`
- Requires environment variables: `AMAP_API_KEY` and `DEEPSEEK_API_KEY`

### Frontend Setup
- Open `frontend/index.html` directly in a browser
- Requires AMap API key to be set in `frontend/index.html` line 8

## Architecture Overview

### Backend Architecture (Flask)

**Main Entry Point**: `backend/app.py`

**Core API Endpoints**:
- `POST /api/itinerary/generate` - Main itinerary generation endpoint using DeepSeek AI
- `POST /api/assistant/chat` - AI chat assistant for travel questions
- `POST /api/route/planning` - AMap route planning
- `GET /api/weather/info` - Weather information for cities

**Critical Flow for Itinerary Generation**:
1. Frontend sends user preferences to `/api/itinerary/generate`
2. Backend fetches POI data from AMap for multiple categories:
   - Scenic spots (风景名胜)
   - Food (餐饮服务)
   - Hotels (住宿服务)
   - Cultural sites (科教文化服务)
   - Shopping (购物服务)
   - Parent-child activities (亲子场所)
3. Backend calls `_add_coordinates_to_pois()` to enrich POI data with coordinates using geocoding/POI search
4. Backend constructs a detailed prompt with POI information and sends to DeepSeek AI
5. AI returns JSON itinerary with activities for each day
6. Backend processes the JSON response with `fix_incomplete_json()` function to handle potential truncation
7. Backend enriches activities with:
   - Geocoded coordinates (if AI didn't provide them)
   - Transportation information using `_get_route_data()`
   - Polyline data for route visualization
8. Returns complete itinerary with transportation details

**Key Helper Functions**:
- `_get_poi_coordinates(name, address, city, amap_key)` - Gets coordinates via geocoding or POI search
- `_add_coordinates_to_pois(poi_list, city, amap_key)` - Batch coordinate enrichment
- `_get_estimated_distance_and_duration(origin, destination)` - Uses AMap distance API
- `_get_route_data(origin, destination, mode, city)` - Returns (distance, duration, mode, polyline) for walking/transit/driving
- `fix_incomplete_json(json_str)` - Repairs truncated JSON from AI responses

**Transportation Mode Selection Logic** (in `app.py:864-870`):
- Distance < 1km → Walking (步行)
- Distance 1-5km → Transit (公交/地铁)
- Distance > 5km → Driving/Taxi (驾车/打车)

**Polyline Format**: Backend returns uncompressed polyline strings in format `"lng1,lat1;lng2,lat2;..."` (not AMap's compressed format)

### Frontend Architecture (Vanilla JavaScript)

**Main Files**:
- `frontend/index.html` - Main HTML structure
- `frontend/script.js` - All application logic
- `frontend/style.css` - Styling (not analyzed)

**Key UI Screens**:
1. Welcome Screen - Initial landing page
2. Settings Screen - User input for travel preferences
3. Itinerary Screen - Generated itinerary display with maps

**Critical JavaScript Functions**:
- `generateItineraryWithAI()` - Collects user preferences, calls backend API, stores result in global `itinerary` variable
- `generateDailySessions(itineraryData)` - Dynamically creates HTML for each day's itinerary
- `initDayMap(dayNumber, activities)` - Creates AMap instance for each day
- `drawRouteOnMap(map, activities)` - Renders routes using polyline data from backend
- `parseUncompressedPolyline(polylineStr)` - **Critical**: Parses backend's `"lng,lat;lng,lat"` format (NOT AMap's compressed format)
- `planAllRoutes()` - Renders all routes on all day maps

**Important Global State**:
- `userPreferences` - Stores all user input
- `itinerary` - Stores fetched itinerary data (set in `script.js:476`)
- `chatHistory` - Stores AI chat conversation

**Map Integration Notes**:
- AMap JavaScript API v1.4.15 loaded from CDN
- Each day has its own map container: `day{N}-map`
- Polylines use custom parsing function `parseUncompressedPolyline()` at `script.js:685-705`
- Route colors: Walking (green `#29b380`), Driving (blue `#4361ee`), Transit (red `#fa7070`)

## API Configuration

**Required Environment Variables**:
```bash
export AMAP_API_KEY=your_amap_key
export DEEPSEEK_API_KEY=your_deepseek_key
```

**Default Keys** (hardcoded in code, should be replaced):
- AMap: `195725c002640ec2e5a80b4775dd2189`
- DeepSeek: `sk-d5826bdc14774b718b056a376bf894e0`

**Important**: Default keys are embedded in both backend (`app.py:28,33`) and frontend (`index.html:8`)

## Key Technical Details

### JSON Parsing Robustness
The `fix_incomplete_json()` function (`app.py:37-107`) handles AI responses that may be truncated due to token limits. It:
- Removes markdown code blocks
- Fixes missing commas between objects/arrays
- Balances brackets and quotes
- Intelligently truncates to last valid delimiter if unfixable

### Coordinate Resolution Strategy
When processing activities, coordinates are resolved in this order:
1. Use AI-provided coordinates (if valid)
2. Call AMap geocoding API with full address
3. Fallback to POI text search using activity title
4. Use default Beijing coordinates (116.397428, 39.90923) as last resort

### Transportation Calculation
Transportation info is calculated between consecutive activities within a day, and from the last activity of the previous day to the first activity of the current day. The first activity of Day 1 has no transportation info (user must get there on their own).

### Weather Integration
Weather data from AMap is fetched for the destination city and matched to each day based on date or day index modulo the forecast length.

## Common Development Tasks

### Adding New POI Categories
1. Add new API call in `generate_itinerary()` around line 334-490
2. Add category to `all_pois` dict at line 478
3. Update AI prompt to mention new category at line 534-600

### Modifying Transportation Logic
- Mode selection logic: `app.py:864-870`
- Route data fetching: `_get_route_data()` at `app.py:131-216`
- Frontend rendering: `drawRouteOnMap()` at `script.js:782-858`

### Debugging Polyline Issues
- Check backend logs for polyline string format
- Verify `parseUncompressedPolyline()` is parsing correctly (see debug logs at `script.js:818,831`)
- Confirm polyline format matches `"lng,lat;lng,lat..."` not compressed format

### Extending AI Capabilities
- Modify system prompt at `app.py:617`
- Adjust JSON structure expectation at `app.py:560-600`
- Update max_tokens calculation at `app.py:520` (currently `days * 800 + 500`)

## Known Limitations

- Backend runs on port 8888 (not standard 5000)
- No authentication system implemented
- History feature not implemented (shows placeholder alert)
- Default coordinates fallback to Beijing
- AI responses may be truncated for long itineraries (>4000 tokens)
- Frontend directly embeds API keys (security concern)
