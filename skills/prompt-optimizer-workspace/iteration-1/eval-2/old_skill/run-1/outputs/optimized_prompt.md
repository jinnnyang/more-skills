## Original Requirement
Generate a weather dashboard showing current temperature and 5-day forecast.

**Identified Issues:**
- **Lacks user interaction and input details**: The request does not define how location is input (e.g. search input, geolocation API, or defaults).
- **Missing secondary weather metrics**: The request does not specify what other essential metrics to show (humidity, wind speed, UV index, air quality).
- **No state management or error handling**: No description of loading state UI, offline support, caching mechanisms, or handling API error codes (e.g. 404 city not found).
- **No styling or responsiveness guidelines**: The prompt does not specify look-and-feel (e.g. responsive layout, theme colors, dynamic visual backgrounds reflecting weather conditions).

## EARS Transformation
1. The system shall display a search input field for city queries, a unit toggle (Celsius/Fahrenheit), and a geolocation search button.
2. When the user submits a city query via the search input, the system shall fetch weather data for that city and refresh the dashboard.
3. When the user clicks the geolocation button, the system shall request permission to access the user's coordinates.
4. When location access is granted, the system shall fetch weather data for the current coordinates and refresh the dashboard.
5. When a weather query is successful, the system shall display the city name, current temperature, high/low temperatures, weather condition text, local date/time, humidity, wind speed, UV index, and a 5-day forecast.
6. When a weather query fails (e.g. city not found or offline status), the system shall display a non-blocking error toast and retain the previously loaded valid weather data.
7. When the user switches the unit toggle, the system shall recalculate and update all temperatures on the screen immediately in-memory without making another API request.
8. While a weather query is in progress, the system shall display animated skeleton loading states in place of the weather metrics.
9. While weather data is loaded, the system shall dynamically transition the page's background gradient and visual elements to match the primary weather condition (e.g. Sunny, Rain, Snow, Clouds, Thunderstorm).
10. If a weather query is actively loading, the system shall prevent duplicate API requests for the same query.
11. If the API rate limit is reached, the system shall display a rate limit warning and fall back to the cached dashboard content from `localStorage` (if less than 30 minutes old).

## Domain & Theories
**Primary Domain:** Data Visualization & UX/UI Design

**Applicable Theories:**
- **Miller's Law (7±2) / Chunking**: Organizes complex dashboard weather details into logical visual segments, separating primary data from secondary parameters.
- **Gestalt Principles (Proximity & Similarity)**: Groups forecast days using identical layouts and uniform spacing for easy scanability.
- **Tufte's Data-ink Ratio**: Replaces clutter with high-density data visualizations like clean custom weather icons and minimalistic forecast trend layouts.
- **BJ Fogg Behavior Model (B=MAT)**: Enhances Ability through automated geolocation detection and autocomplete searches to minimize search friction.

## Enhanced Prompt
# Role
Expert Frontend UI/UX Engineer specializing in real-time dashboards, interactive weather applications, and dynamic data visualizations, with a deep understanding of browser APIs and clean data presentation.

## Skills
- Crafting responsive, mobile-first dashboard layouts with flexible CSS Grid and Flexbox systems.
- Designing dynamic theme engines that update page backgrounds, shadows, and text colors based on API state (weather conditions).
- Designing interactive SVG/CSS weather icons and layout animations (smooth transitions, skeleton loaders).
- Applying UX theories (Miller's Law, Gestalt principles, and Tufte's data-ink ratio) to organize dense meteorological datasets.
- Integrating external REST APIs (e.g., OpenWeatherMap, WeatherAPI) with robust error states and data fallback mechanisms.
- Implementing frontend data caching using `localStorage` to improve load performance and avoid rate limits.

## Workflows
1. **Layout & System Setup**: Define a modular, mobile-first design system with CSS custom properties for different weather themes (sunny, rainy, cloudy, snowy, night).
2. **Geolocating & Fallback Search**: Implement browser Geolocation API triggers alongside a robust textual city search engine.
3. **Data Fetching & Resiliency**: Create a fetch workflow that caches API responses in `localStorage` for up to 30 minutes, handling offline detection and API errors gracefully.
4. **Dynamic styling & Themes**: Apply CSS transitions to shift the page gradients and ambient overlay animations to match the retrieved weather condition.
5. **Weather Metrics Layout**: Chunk the UI into a primary visual block (temperature, condition, location), a secondary details grid (humidity, wind speed, UV index, air quality), and a 5-day forecast grid.
6. **Interaction & State Transitions**: Set up skeleton screens for active fetching, toggling Celsius/Fahrenheit dynamically in-memory, and displaying non-blocking errors.

## Examples
- **Successful Sunny Flow**:
  - Input: "Sydney"
  - Output UI: Bright warm gold/blue gradient background. Current weather card displays large "22°C" with a glowing sun icon, "Sunny", "Humidity: 45%", "Wind: 10 km/h". Forecast grid shows 5 clean, horizontally aligned cards with daily summaries (e.g., "Mon | ☀️ | 24° / 15°").
- **Dynamic Rain Theme**:
  - Input: "London"
  - Output UI: Moody steel-blue gradient background with a soft, CSS-animated rainfall overlay. Current weather shows "13°C", "Light Rain", "Precipitation: 80%".
- **Error/Fallback Handler**:
  - Input: "InvalidCity123"
  - Output UI: Screen briefly displays toast alert: "Could not find 'InvalidCity123'. Please check the spelling." The screen retains London's weather details instead of resetting to blank or crashing.

## Formats
A complete, self-contained HTML/CSS/JS application matching the following specification:
- **File Structure**: Single self-contained HTML file containing inline styles/scripts, or a clean folder with index.html, styles.css, and app.js.
- **IDs & Classes**: All interactive and key display elements must have descriptive IDs (`#search-input`, `#search-btn`, `#geo-btn`, `#unit-toggle`, `#current-temp`, `#forecast-grid`, `#loading-skeleton`, `#error-toast`).
- **Styling Specs**: Modern glassmorphic theme elements (`backdrop-filter: blur(...)`), readable typography (using Inter or System Sans), smooth background transitions (`transition: background 0.5s ease`), and a fully responsive grid matching screen sizes from mobile to desktop.
- **Accessibility**: Semantic elements (`<header>`, `<main>`, `<section>`), proper `aria-label` tags for icon buttons, and high contrast text ratios.

---

**How to use:**
1. Copy the **Enhanced Prompt** section above.
2. Provide it to any LLM/AI coding assistant (e.g. Claude, GPT-4) to generate a fully realized, professional, responsive weather dashboard web page with state-of-the-art styling, interaction models, and resilient error flows.
