# Optimized Prompt: Weather Dashboard Specification

## Original Requirement
Generate a weather dashboard showing current temperature and 5-day forecast.

**Identified Issues:**
- **Too Vague & Unspecified**: No detail on the search mechanism, location handling, default behavior, or layout.
- **Lack of Interaction Definition**: No states for loading, unit conversion (Celsius/Fahrenheit), error handling, or location search failures.
- **No Non-Functional Constraints**: No specification for API performance, rate limits, caching, local storage usage, or accessibility.
- **Undefined Aesthetics & UX Design**: No alignment with visual theories, responsive design expectations, or information architecture standards.

## EARS Transformation
1. When the user loads the application, the system shall retrieve the last successfully searched city from LocalStorage and render its current weather data and 5-day forecast.
2. If there is no city saved in LocalStorage, the system shall default to loading weather data for "London" as the initial state.
3. When the user inputs a city name into the search bar and clicks the search button or presses Enter, the system shall execute an API request to fetch weather data for the specified city.
4. When the API request is initiated, the system shall display a skeleton loading state for all temperature displays, current metrics, and forecast cards.
5. When the API request successfully resolves, the system shall update the search input, display current weather details (city name, date/time, temperature, weather condition icon, wind speed, humidity, and UV index), render the 5-day forecast cards, and save the city name to LocalStorage.
6. When the API request fails due to an invalid city name, the system shall display an inline error alert "City not found. Please check spelling." and retain the previously loaded weather data.
7. When the API request fails due to network issues or server errors, the system shall display a banner "Unable to connect to weather service. Please try again." and display a retry button.
8. When the user clicks the temperature unit toggle button, the system shall convert all displayed temperatures between Celsius and Fahrenheit.
9. When the user clicks the "Use Current Location" button, the system shall request geolocation coordinates from the browser.
10. If geolocation access is granted, the system shall fetch weather data for the user's current latitude and longitude coordinates.
11. If geolocation access is denied or fails, the system shall display a notification "Location access denied. Displaying last searched city." and remain in the current state.
12. While weather conditions are active, the system shall dynamically update the dashboard's background gradient and visual accents to match the current condition (e.g., bright golden gradients for sunny, slate blue/grey for rainy, and dark indigo for nighttime).

## Domain & Theories
**Primary Domain:** Weather Data Visualization & Frontend User Interface

**Applicable Theories:**
- **Gestalt Principles (Visual Hierarchy)** - Use containment (cards), proximity, and similarity to visually distinguish between current conditions and the 5-day forecast, grouping relevant data elements logically.
- **Miller's Law (Information Chunking)** - Limit primary current weather details to a small, readable set of metrics (temperature, description, high/low), while chunking detailed secondary metrics (humidity, wind speed, UV index) into a grid to prevent cognitive overload.
- **Progressive Disclosure** - Present the most essential weather data (temperature, city, status) immediately and make secondary parameters accessible via toggles or secondary panels.
- **Tufte's Data-ink Ratio** - Keep layout elements clean by maximizing the data-ink ratio; avoid heavy frames, and use modern vector weather icons with minimalist design.

## Enhanced Prompt

# Role
You are a senior frontend engineer and UI/UX designer specializing in real-time data visualization and modern, accessible web interfaces. You design interfaces that are clean, intuitive, and visually responsive to live data.

## Skills
- Design responsive, modern layouts using CSS Grid and Flexbox with premium glassmorphic aesthetics.
- Implement asynchronous API integrations (e.g., OpenWeatherMap, WeatherAPI) with robust error handling and loading indicators.
- Apply UX theories (Gestalt Principles, Miller's Law, Progressive Disclosure) to organize dense information logically.
- Develop dynamic UI states (e.g., background gradients matching weather conditions).
- Utilize localStorage for client-side data caching and persistence.
- Implement accessibility standards (WCAG) including aria-labels and keyboard navigation.

## Workflows
1. **Design System & Layout Construction**: Set up CSS variables for color themes (adaptive based on weather state), establish typography using Google Fonts (e.g., Inter, Outfit), and build a layout with clear visual hierarchy.
2. **Dynamic UI Styling**: Implement conditions to dynamically adjust the UI theme (gradients, icons) depending on the weather status (e.g., sunny, rainy, snowy, night).
3. **API and Data Management**: Integrate a mock weather service or a free weather API to retrieve current conditions and a 5-day forecast. Store the last searched city in localStorage.
4. **Interactive States & Transitions**: Implement search submission, loading skeletons, unit toggle (C/F), geolocation coordinates lookup, and error toasts.
5. **Polishing & Responsive Verification**: Ensure the layout reflows gracefully on mobile, tablet, and desktop viewports, verifying touch targets are at least 44x44px.

## Examples
- **Current Temperature display**: "San Francisco, US", Temp: "16°C" (61°F), Condition: "Partly Cloudy", Feels Like: "15°C", Wind: "14 km/h (W)", Humidity: "72%", UV Index: "4 (Moderate)", Air Quality: "Good".
- **5-Day Forecast display**:
  - Tomorrow: Min 11°C / Max 17°C, Weather: Showers (icon: rain, Pop: 70%).
  - Day 2: Min 12°C / Max 19°C, Weather: Partly Cloudy (icon: cloud with sun).
  - Day 3: Min 13°C / Max 21°C, Weather: Sunny (icon: sun).
  - Day 4: Min 10°C / Max 15°C, Weather: Heavy Rain (icon: thunderstorm, Pop: 90%).
  - Day 5: Min 9°C / Max 14°C, Weather: Mostly Cloudy (icon: clouds).
- **Error scenarios**: City "Xyzabc" searched → inline error alert "City 'Xyzabc' not found. Please try again." without wiping current dashboard content.

## Formats
Provide a single-page HTML web application (containing CSS and JS or cleanly split into index.html, index.css, and app.js) that delivers:
- **Premium Glassmorphic Design**: Clean layouts using backdrop-filter blur, semi-transparent card containers, and dynamic background gradients that change according to weather.
- **Search Header**: Centered search bar with location permission shortcut icon.
- **Layout Sections**: A main panel for current temperature and location, a grid of secondary metrics cards, and a horizontal/grid display of 5-day forecast cards.
- **Interactive features**: Fahrenheit/Celsius conversion toggle, search capability, browser Geolocation fallback, loading animations.
- **Deliverables**: All HTML, CSS, and JS code blocks required to run the dashboard locally.

---

**How to use:**
1. Feed this prompt into a code generator or use it as a developer checklist to build a high-fidelity weather dashboard.
2. Ensure the API keys, if using real API endpoints, are handled via environment variables or a secure configuration input.

## Next Steps
An optimized specification has been successfully generated. Please select your next action:

Options:
A) web-artifacts-builder — Propose building the application prototype using the newly generated prompt.
B) deep-research — Research deep technical details or competitor approaches for the features in the optimized prompt.
C) github-ops — Prepare the project repository or branch for developing these requirements.
D) No thanks — The optimized prompt is ready as-is.
