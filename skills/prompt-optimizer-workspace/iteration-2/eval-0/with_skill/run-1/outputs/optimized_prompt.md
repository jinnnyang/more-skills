## Original Requirement
Create a reminder app with task management.

**Identified Issues:**
- **Overly Broad Functionality**: The phrase "reminder app with task management" does not specify the scope of task properties (e.g., categories, sub-tasks, priority, tags) or the reminder mechanism (browser push, email, SMS, audio alerts).
- **Missing Triggers and State Logic**: No definition of when reminders should trigger, how overdue tasks should behave, or how the task status transition affects the reminders.
- **No Measurable Usability or Design Criteria**: Phrases like "reminder app" do not specify key performance metrics, data persistence expectations (local storage vs backend database), or aesthetic constraints.
- **Absence of Cognitive or Psychological Grounding**: The requirement does not incorporate productivity frameworks, which are crucial for ensuring that a reminder/task app successfully helps users complete work rather than causing notification fatigue.

## EARS Transformation
1. **Ubiquitous**: The system shall provide a task management interface for creating, viewing, updating, and deleting tasks.
2. **Event-driven**: When a user creates a new task, the system shall prompt the user to input a Title, Description, Due Date/Time, Priority Level (Low, Medium, High), and optional Sub-tasks.
3. **Event-driven**: When a task's due date/time is reached, the system shall play a distinct, high-frequency audio chime and display a system-level browser push notification.
4. **State-driven**: While a task is in the "Active Focus" state, the system shall display a Pomodoro timer countdown (default 25 minutes) with a visual progress ring and mute/unmute audio controls.
5. **Conditional**: If a task remains incomplete after its due date and time, the system shall highlight the task in a high-contrast warning state (red outline) and display it in a dedicated "Overdue" section.
6. **Unwanted behavior**: If a user attempts to save a task without a title, the system shall prevent the action and display a validation error message "Task title is required."
7. **Unwanted behavior**: If a user attempts to add a sub-task with empty content, the system shall prevent insertion and display a warning toast "Sub-task details cannot be blank."
8. **Ubiquitous**: The system shall save all tasks and states in the browser's `localStorage` to ensure persistence across page refreshes.

## Domain & Theories
**Primary Domain:** Productivity, Time Management, and Behavioral Change

**Applicable Theories:**
- **Getting Things Done (GTD) by David Allen** - Guides the user in capturing tasks quickly and immediately clarifying them by breaking large, complex goals into discrete, actionable sub-tasks.
- **BJ Fogg's Behavior Model (B=MAT)** - Enhances user "Ability" by decomposing daunting tasks into micro-steps, and sets precise "Triggers" (notifications) at the exact moment the user is prompted to act.
- **Pomodoro Technique by Francesco Cirillo** - Structures work into 25-minute focused blocks followed by short breaks, helping users manage cognitive load and maintain concentration.
- **Miller's Law (7±2)** - Groups tasks into structured categories (Today, Upcoming, Overdue, Completed) to keep visual and cognitive clutter below the human processing threshold.

## Enhanced Prompt
# Role
You are a senior product designer and expert frontend engineer specializing in human-computer interaction, cognitive ergonomics, and high-performance productivity systems. You design visually stunning, responsive, and psychologically grounded tools that optimize cognitive load and drive user engagement.

## Skills
- Design responsive dashboards utilizing premium aesthetics (dark mode, glassmorphism, fluid spacing).
- Implement interactive task management architectures supporting nested sub-tasks and visual progress tracking.
- Build resilient front-end notification systems using the Web Audio API and Web Notifications API.
- Apply behavioral psychology frameworks (GTD, Pomodoro, B=MAT) to UI flows.
- Optimize client-side data structures for local persistence (localStorage) and rapid queries.

## Workflows
1. **Information Architecture & Layout Planning**: Structure a dual-panel dashboard. The left panel shows categorized lists (Inbox, Today, Upcoming, Overdue, Completed); the right details panel displays the active task, its sub-tasks, and the Pomodoro focus module.
2. **Decomposition Flow (GTD)**: When a task is selected, expose a dynamic sub-task decomposition field, prompting the user with: "Break this down into at least 2 small, actionable steps."
3. **Focus State Engagement (Pomodoro)**: When a user clicks "Start Focus" on a task, minimize peripheral dashboard elements (progressive disclosure) and initialize a 25-minute countdown. Maintain state even if the user navigates between lists.
4. **Trigger & Reminder Execution**: Calculate time differences dynamically. When a task's due time is hit, instantiate a browser notification and play a clean, 2-second synthesized sine-wave chime using the Web Audio API (to avoid external file dependencies).
5. **Progress & Feedback Loop**: As sub-tasks are toggled, recalculate task progress (`(completed_subtasks / total_subtasks) * 100`). When 100% is reached, trigger a subtle confetti micro-animation and transition the task to the "Completed" section.

## Examples
- **Decomposed Task Data**:
  - Title: "Publish Q3 Product Roadmap"
  - Description: "Align with engineering leaders and release the roadmap"
  - Priority: High
  - Due Date: "2026-05-30T10:00:00"
  - Sub-tasks:
    - [x] Gather feedback from dev leads (Est. 45 min)
    - [ ] Update slides in the master deck (Est. 30 min)
    - [ ] Schedule review meeting with PM director (Est. 15 min)
  - Current Progress: 33%
- **Overdue Visual State**:
  - Task: "Review budget allocation" (Due: "2026-05-28T14:00:00" - past current time)
  - UI Presentation: Displayed with a soft red ambient glow (`box-shadow: 0 0 12px rgba(239, 68, 68, 0.2)`), an orange warning badge labeled "Overdue", and pushed to the top of the feed.
- **Audio Chime Code Example (Web Audio API)**:
  ```javascript
  const ctx = new (window.AudioContext || window.webkitAudioContext)();
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  osc.connect(gain);
  gain.connect(ctx.destination);
  osc.frequency.setValueAtTime(880, ctx.currentTime); // A5 note
  gain.gain.setValueAtTime(0.1, ctx.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 1.5);
  osc.start();
  osc.stop(ctx.currentTime + 1.5);
  ```

## Formats
Output a single-page, fully responsive Web Application using HTML5, Vanilla JavaScript, and standard CSS.
- **Styling Specs**:
  - Color Palette: Sleek Dark Mode. Background: `#0B0F19` (Deep slate blue); Card Background: `#161F30` (Semi-transparent glassmorphism with `backdrop-filter: blur(10px)`); Primary Accent: `#6366F1` (Indigo); Success: `#10B981` (Emerald); Warning/Overdue: `#EF4444` (Rose).
  - Typography: Load 'Inter' or 'Outfit' from Google Fonts. Font-size scaling from 12px (labels) to 28px (dashboard titles).
  - Visual Transitions: Smooth hover expansions, transition duration `0.25s` with `cubic-bezier(0.4, 0, 0.2, 1)`.
- **Functionality Checklist**:
  - [ ] Interactive task creation/editing form with input validation (prevent empty titles).
  - [ ] Sub-task checklist supporting addition/deletion/toggling of items with dynamic progress bar.
  - [ ] Pomodoro Timer component with play/pause/reset, SVG circular countdown indicator, and Audio context chimes.
  - [ ] Persistent browser notifications (check permission first, fallback to in-app custom modal if permission is denied).
  - [ ] Comprehensive LocalStorage CRUD utility.
  - [ ] Dynamic category filtering (All, Today, Overdue, Completed).

---

**How to use:**
Provide this optimized prompt to an AI assistant, or use it as a formal requirements document for developers. The structured workflow guarantees consistent user experiences, the design directives ensure visual excellence, and the EARS syntax yields testable conditions suitable for quality assurance.

---

## Next Step

An optimized specification for the reminder app with task management has been successfully generated in compliance with EARS syntax and behavioral design frameworks.

Options:
A) web-artifacts-builder — Propose building the application prototype using the newly generated prompt.
B) deep-research — Research deep technical details or competitor approaches for the features in the optimized prompt.
C) github-ops — Prepare the project repository or branch for developing these requirements.
D) No thanks — The optimized prompt is ready as-is.
