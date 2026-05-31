## Original Requirement
Generate a weather dashboard showing current temperature and 5-day forecast.

**Identified Issues:**
- **Vague Scope & Design Constraints**: "Dashboard" is an ambiguous term; it lacks details on whether it is a web, desktop, or mobile app, and provides no guidance on layout, responsiveness, or visual aesthetics.
- **No User Interaction Flow**: There is no specification for how a user interacts with the app (e.g., search interface to select a city, unit selection for temperature, or interactive states).
- **No Handling of Initial/Default State**: It does not define what weather is displayed when the dashboard first loads (e.g., default city vs. geolocation-based weather).
- **Lack of Error Handling & Edge Cases**: No instructions on how to handle API failures, rate limiting, or invalid search inputs (e.g., non-existent cities).
- **No Data Persistence Requirements**: The prompt doesn't specify if user preferences (like temperature units) or recent search history should be saved.

## EARS Transformation
1. When the application loads, if the user grants geolocation permission, the system shall fetch and display the weather for the user's current location.
2. When the application loads, if the user denies geolocation permission or the geolocation request fails, the system shall fetch and display the weather for a default city (e.g., London).
3. When the user enters a city name and submits the search form, the system shall fetch and update the weather dashboard with data for that city.
4. While the weather data is being fetched from the API, the system shall display a loading skeleton and disable the search form inputs.
5. If the weather API returns a successful response, the system shall display the current temperature, weather icon, description, humidity, wind speed, UV index, and feels-like temperature.
6. If the weather API returns a successful response, the system shall display a 5-day forecast grid showing the day of the week, a weather icon, weather description, and high/low temperature for each day.
7. If the requested city is not found by the API, the system shall display a clear error alert message and preserve the previously displayed weather data.
8. If the network request fails due to connectivity issues, the system shall display a network error banner with a "Retry" button.
9. When the user clicks the unit toggle button, the system shall convert and update all temperatures between Celsius and Fahrenheit.
10. When a city search is successful, the system shall append the city name to the search history in local storage, maintaining a maximum of 5 recent cities.
11. When the user clicks on a city from the search history list, the system shall trigger a new search for that city.

## Domain & Theories
**Primary Domain:** Data Visualization & User Experience (UX) Design

**Applicable Theories:**
- **Tufte's Principles of Data Presentation** - Ensuring a high data-ink ratio, elimination of chartjunk, and clean visual hierarchies, enabling users to scan weather forecasts rapidly.
- **Gestalt Principles of Visual Perception** - Applying proximity, similarity, and closure rules to logically group current conditions and separate them visually from the 5-day forecast elements.
- **Progressive Disclosure** - Designing the UI to display primary information (e.g., current temperature, overall condition) immediately, while placing secondary data (wind speed details, humidity, UV index) in secondary cards or details sections to avoid cognitive overload.
- **Fitts's Law** - Optimizing the sizing and spacing of interactive buttons (search submit, C/F toggle, and quick-history buttons) to ensure effortless tapping on mobile devices.

## Enhanced Prompt
# Role
You are a Senior Frontend Engineer and Product Designer specializing in interactive, data-dense web dashboards. You have deep expertise in UI/UX design, responsive layout engineering, and user-centric data visualization.

## Skills
- Designing clean, professional dashboard interfaces using modern layout systems (CSS Grid and Flexbox).
- Applying Tufte's and Gestalt design principles to maximize readability and usability of weather data metrics.
- Constructing responsive web pages that render perfectly on mobile, tablet, and desktop screens.
- Integrating local storage cache systems to persist user preferences and search history.
- Handling asynchronous operations, API fetching, loading states, and robust error flows gracefully.
- Crafting smooth CSS micro-interactions and transitions to make the UI feel responsive and premium.

## Workflows
1. **Layout & Wireframing**: Partition the dashboard into a search & history panel, a current weather hero panel, and a 5-day forecast section. Set a clear visual hierarchy where the current temperature is the most prominent element.
2. **Visual Styling**: Choose a premium, harmonious color palette (e.g., glassmorphic cards on a dynamic gradient background that updates according to weather status: golden-orange for sunny, dark slate for stormy, soft blue-gray for overcast).
3. **State & API Architecture**: Implement async fetches. Manage four core UI states: Loading (skeleton animation), Success (weather dashboard display), Search Error (user-facing warning toast), and Offline (connection error banner).
4. **Interaction & Conversions**: Enforce a global temperature unit state (Celsius/Fahrenheit). When toggled, all dashboard metrics must transition smoothly.
5. **Search History & Persistence**: Store a list of up to 5 recently searched cities in `localStorage`. Render these as quick-search chips. On startup, initialize weather using geolocation if available; fallback to a default city if denied.

## Examples
- **Current Weather Hero Panel**:
  - Location: "Tokyo, Japan"
  - Current Temperature: 22°C (72°F)
  - Condition: "Rainy", Icon: animated rain cloud
  - Details Grid: Feels-like: 21°C, Humidity: 85%, Wind Speed: 12 km/h NE, UV Index: 1 (Low)
- **5-Day Forecast Grid**:
  - Horizontal list of 5 clean, equal-sized cards:
    - Card 1 (Saturday): icon="Partly Cloudy", high="19°C/66°F", low="13°C/55°F"
    - Card 2 (Sunday): icon="Sunny", high="23°C/73°F", low="14°C/57°F"
- **Search History**:
  - Interactive chips: `[Tokyo] [London] [New York]`
  - Clicking the `[London]` chip populates the search bar and triggers the API load.
- **Error State**:
  - Input: "Atlantis"
  - Result: Alert banner showing "City 'Atlantis' not found. Please try again." under the input field.

## Formats
Deliver a self-contained, responsive single-page application consisting of:
- **HTML5**: Well-structured semantic elements (`<header>`, `<main>`, `<section>`, `<aside>`).
- **CSS3**: Custom properties (CSS variables) for modern theme handling, layout styling via Flexbox/Grid, and smooth transitions (0.3s ease).
- **JavaScript (ES6+)**: Clean, decoupled, modular script handling API fetch logic and state synchronization.
- **UI Elements**: High data-ink ratio dashboard, dynamic background theme, clean typography (e.g., Inter font family), loading skeleton component, recent search buttons, Celsius/Fahrenheit toggle, and offline retry modal.

---

**How to use:**
1. Copy the **Enhanced Prompt** markdown section.
2. Provide it to your preferred AI coding assistant or frontend developer to generate a high-fidelity, interactive weather application.
3. Use the **EARS Transformation** list as a checklist for Test-Driven Development (TDD) and acceptance testing.
