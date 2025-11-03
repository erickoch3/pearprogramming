# Pear Programming - Technical Details

## Project Overview

**Pear Programming** is an intelligent activity recommendation platform that leverages AI and real-time data aggregation to deliver personalized event suggestions. Built for HackTheBurgh, our system transforms how people discover local experiences by understanding context, preferences, and real-time conditions.

![Demo](./assets/demo.gif)

## Architecture & Tech Stack

### Backend (Python FastAPI)

**Core Framework:**

- **FastAPI** - High-performance async API framework
- **Uvicorn** - ASGI server for production deployment
- **Pydantic** - Data validation and serialization

**AI & Language Models:**

- **LangChain** - LLM orchestration and agent framework
- **OpenAI GPT Models** - Primary: `gpt-5`, Fallbacks: `gpt-4o`, `gpt-4.1`

**Key Utilities:**

- **BeautifulSoup4** - Extracting data from webpages
- **Requests** - HTTP client for API integrations

### Frontend (Next.js + React)

**Core Framework:**

- **Next.js** - React framework with App Router
- **React** - Component library
- **TypeScript** - Type safety and developer experience

**Mapping & Visualization:**

- **Leaflet** - Interactive mapping library
- **React-Leaflet** - React bindings for Leaflet

**Styling & Development:**

- **Tailwind CSS** - Utility-first CSS framework
- **Vitest** - Fast unit testing framework

## External APIs & Data Sources

### Real-Time Data Integration

**Weather Data:**

- **OpenWeatherMap API** - Real-time weather conditions and forecasts
- Features: Temperature, humidity, wind speed, precipitation

**Festival Events:**

- **Edinburgh Festival City API** - Official festival listings
- Supports multiple festivals (Fringe, Book Festival, etc.)

**Event Discovery:**

- **Eventbrite Web Scraper** - Custom scraper for public event listings
- **Google Maps Geocoding API** - Address to coordinate conversion
- Filters for location, date range, and event type

## AI-Powered Recommendation Engine

### Context Aggregation System

**Multi-Source Data Fusion:**

```python
class ContextAggregator:
    def gather_context(self, preferences, target_date, city, country_code):
        # Parallel data fetching with ThreadPoolExecutor
        - Weather conditions and forecasts
        - Festival event schedules
        - Eventbrite event listings
        - User preference parsing
        - Seasonal context estimation
```

**Intelligent Preprocessing:**

- Natural language preference extraction
- Location context with coordinate mapping
- Time-sensitive event filtering

### LLM Agent Implementation

**Structured Output Generation:**

```python
class LLM:
    # Multi-model fallback system
    _model_candidates = ["gpt-5", "gpt-4o", "gpt-4.1"]
    
    def generate_event_suggestions(context, max_events):
        # Structured output with Pydantic validation
        # Custom prompt engineering for event recommendations
        # Confidence scoring (0-10) for each suggestion
```

**Agent Features:**

- **Context-Aware Prompting** - Incorporates weather, preferences, and local events
- **Structured Response Format** - Pydantic schemas ensure consistent output
- **Fallback Mechanisms** - Graceful degradation when APIs fail
- **Preference Alignment** - Scores events based on user stated preferences (9-10 strong alignment, 6-8 partial, 0-5 weak)

## Development Environment & Tooling

### Build System

```makefile
# UV-based Python environment management
install:    # Virtual environment setup with uv
api:        # FastAPI development server
mockapi:    # API with mock data (MOCK=1)
ui:         # Next.js development server  
mockui:     # UI with mock data (NEXT_PUBLIC_MOCK=1)
test:       # Pytest suite execution
```

### Testing & Quality Assurance

- **Pytest** - Comprehensive backend test suite
- **Mock testing** - Isolated testing without external dependencies
- **Type safety** - TypeScript coverage in frontend

## Data Models & API Contracts

### Event Schema

```typescript
interface Event {
  name: string;           // Human-readable event name
  description: string;    // Brief event description
  emoji: string;          // Visual event category indicator
  location: [number, number]; // [x, y] coordinate system
  event_score: number;    // Confidence/relevance score (0-10)
  link?: string | null;   // Optional URL for more information
}
```

### User Experience Features

- **Natural Language Preferences** - "something creative and outdoors" → structured recommendations
- **Real-Time Adaptation** - Weather-aware suggestions using real time data
- **Confidence Scoring** - Transparent recommendation quality indicators
- **Interactive Mapping** - Visual exploration of activity locations