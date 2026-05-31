## Original Requirement
Create a reminder app with task management.

**Identified Issues:**
- **Vague Functional Scope:** "Task management" is not defined; lacks details on task fields, statuses, categorization, or complexity handling (e.g., sub-tasks).
- **Missing Trigger Conditions:** Does not specify when, how, or through what channels reminders should be sent (e.g., push notifications, email, sound alerts) or how trigger events are defined relative to deadlines.
- **No Consideration of Behavioral Psychology:** Fails to address common user pain points like procrastination, lack of motivation, or friction in task creation, which are critical for engagement.
- **Lack of Non-Functional Requirements:** Fails to specify data persistence constraints (e.g., local storage or database), accessibility standards, or performance benchmarks.
- **Undefined Design and Layout Constraints:** Does not specify design style, layout, responsiveness, or visual feedback mechanisms for task completion.

## EARS Transformation
1. When a user creates a new task, the system shall guide the user to decompose the large task into executable small task steps. (Event-driven)
2. When a task deadline is within 15 minutes AND the user has not marked the task as completed, the system shall trigger a browser notification with a sound alert and a link to start the task. (Event-driven)
3. When a user completes a task or sub-task, the system shall update the overall task progress and trigger positive visual feedback to reinforce the completion. (Event-driven)
4. While the user is viewing the task dashboard, the system shall sort and display tasks grouped by urgency and importance to establish visual hierarchy. (State-driven)
5. If the user attempts to save a task with an empty title, the system shall prevent the action and highlight the title input field with a validation message. (Unwanted behavior / Conditional)
6. When a reminder notification is displayed, the system shall provide the user with the option to snooze the reminder for 5, 10, or 15 minutes, rescheduling the next notification accordingly. (Event-driven)
7. While the application is loaded, the system shall automatically persist all task and reminder state to the browser's local storage to prevent data loss on reload or offline sessions. (State-driven)
8. If the user denies browser notification permissions, the system shall display an in-app banner warning requesting permission or offering visual reminders within the interface. (Conditional / Fallback)

## Domain & Theories
**Primary Domain:** Personal Productivity and Habit Formation

**Applicable Theories:**
- **Getting Things Done (GTD) by David Allen** - Capturing, clarifying, and organizing tasks into atomic next actions.
- **BJ Fogg Behavior Model (B=MAT)** - Highlighting triggers (reminders) when ability (deconstructed task) is highest.
- **Atomic Habits by James Clear** - Celebrating completions (confetti, streaks) to build satisfying habit loops.
- **Eisenhower Matrix** - Categorizing tasks by Urgency and Importance to direct focus to high-impact activities.
- **Miller's Law (7±2) & Gestalt Principles** - Grouping related sub-tasks and visual cards to minimize cognitive load.

## Enhanced Prompt
# Role
Expert Product Designer and Senior Frontend Engineer specializing in personal productivity apps, cognitive psychology, and user experience design. Deeply versed in David Allen's Getting Things Done (GTD) methodology, BJ Fogg's Behavior Model, and modern UI engineering.

## Skills
- Designing task classification architectures based on GTD and the Eisenhower Matrix.
- Designing behavioral trigger systems utilizing the BJ Fogg Behavior Model (B=MAT).
- Creating rewarding completion loops using gamification mechanics (Atomic Habits principles).
- Managing cognitive load and visual hierarchy using Gestalt Principles and Miller's Law.
- Building responsive, accessible (WCAG 2.1 AA), and visually premium web interfaces using HTML, CSS, and vanilla JavaScript.
- Implementing local data persistence and offline capabilities using Web Storage and Service Workers.

## Workflows
1. **Inbox Capture & Clarification (GTD)**:
   - Provide a persistent quick-add input at the top of the interface to capture tasks instantly.
   - Upon task addition, prompt the user to assign a priority (Eisenhower Matrix) and break large tasks into atomic sub-tasks (Fogg model - lowering ability barriers).
2. **Dynamic Task Sorting & Visual Hierarchy (UX/Gestalt)**:
   - Group tasks into Eisenhower quadrants or sort them in a unified list prioritizing Overdue and High Priority (Urgent & Important) tasks.
   - Use color encoding (e.g., warm hues for high priority, cool hues for low priority) and clean card designs with clear margins and proximity rules.
3. **Behavioral Triggers & Notification Schedules (B=MAT)**:
   - Check task due times against system time continuously or using background workers.
   - Prompt the user for notification permissions on first interaction.
   - If permission is granted, dispatch browser notifications 15 minutes before deadline with a direct Call-To-Action (e.g., "Start task"). If denied, render an elegant, non-intrusive in-app banner fallback.
4. **Positive Reinforcement Loop (Atomic Habits)**:
   - When a task or sub-task check-box is clicked, play a micro-animation (e.g., custom CSS confetti or checklist check effect) and update a visual progress ring.
   - If all sub-tasks under a main task are completed, show a milestone completion card and increment the user's daily productivity streak.
5. **Local Data Sync & Offline Safety**:
   - Write the entire state (tasks, sub-tasks, settings, streaks) to localStorage whenever a write operation occurs (add, edit, delete, toggle).
   - Read from localStorage on initial page load to restore UI state seamlessly.

## Examples
- **Task Deconstructing Example**:
  - Main Task: "Prepare slides for the project kick-off" (Due: 4:00 PM, Priority: High)
  - Generated Sub-tasks:
    - [ ] "Draft outline (15 mins)"
    - [ ] "Find slide template (10 mins)"
    - [ ] "Write content for 5 slides (45 mins)"
    - [ ] "Review slide layout (10 mins)"
- **Reminder Trigger Event**:
  - Time is 3:45 PM (15m before deadline). Main task is incomplete.
  - Action: Display system notification: "Kick-off slides due at 4:00 PM! Ready to spend 15 mins drafting the outline?"
- **Eisenhower Matrix Layout**:
  - Quadrant 1 (Do First): Red borders, bold text, positioned top-left.
  - Quadrant 2 (Schedule): Blue borders, positioned top-right.
  - Quadrant 3 (Delegate): Yellow borders, positioned bottom-left.
  - Quadrant 4 (Eliminate): Grey borders, opacity 0.7, positioned bottom-right.

## Formats
A single-page, fully responsive HTML web application containing:
- **HTML Structure**: Semantic tags (`<header>`, `<main>`, `<section>`, `<article>`), logical keyboard navigation order, and clear ARIA roles/labels for accessibility.
- **CSS Styles**: Modern, premium styling using CSS custom properties (variables) for theme management (elegant dark/light mode transition). Use smooth transition durations, backdrop-filter for glassmorphism panels, and HSL colors for harmonious palettes (no default red/blue/green).
- **JavaScript Engine**: Modular, clean, vanilla ES6+ JavaScript. Implement a state object to manage tasks, sub-tasks, streak counts, and themes. Use Event Delegation for list interactions.
- **Local Storage Schema**: JSON payload containing list of task objects:
  ```json
  [
    {
      "id": "task-12345",
      "title": "Prepare project slides",
      "description": "",
      "dueDate": "2026-05-29T16:00:00",
      "quadrant": "urgent-important",
      "completed": false,
      "subTasks": [
        { "id": "sub-1", "title": "Draft outline", "completed": false }
      ],
      "snoozeCount": 0
    }
  ]
  ```
- **Deliverables Checklist**:
  - [ ] App UI loads correctly on mobile, tablet, and desktop viewports.
  - [ ] Tasks can be added, edited, deleted, and filtered by quadrant.
  - [ ] Sub-tasks can be toggled and their parent task updates progress dynamically.
  - [ ] Local storage persists state across page reloads.
  - [ ] Custom sound and browser notification schedules successfully trigger alerts.
  - [ ] UI is fully usable with keyboard navigation.

---

**How to use:**
1. Copy the **Enhanced Prompt** markdown section above.
2. Provide it to an AI code assistant (such as ChatGPT, Claude, or a specialized software agent).
3. The generated code will follow the detailed structure, implementing the EARS requirements, productivity frameworks, and specific UX requirements.
4. Iterate or adapt the prompt structure to support additional platforms (e.g., React, Flutter, or native mobile apps) as needed.
