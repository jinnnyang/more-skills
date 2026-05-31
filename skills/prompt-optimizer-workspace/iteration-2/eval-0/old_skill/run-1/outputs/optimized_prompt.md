## Original Requirement
Create a reminder app with task management.

**Identified Issues:**
- **Ambiguous Scope:** "Reminder app with task management" lacks definition regarding what counts as a task, how tasks are organized, or what user data is saved.
- **Missing Triggers & Conditions:** No specification for when reminders trigger, how they are delivered (sound, toast, visual shifts), or what happens for overdue tasks.
- **No Behavioral Science Integration:** Standard reminder systems fail to help procrastinating users. There is no usage of productivity frameworks (e.g., GTD, Pomodoro, Eisenhower Matrix) to manage cognitive overload or encourage habit formation.
- **Unclear Non-functional Requirements:** No constraints on performance, responsiveness, data persistence, or offline capability.
- **No Validation/Error Rules:** Lacks definition on how to handle edge cases, empty input fields, or duplicate titles.

## EARS Transformation
1. The system shall organize all tasks into a 2x2 layout representing the four quadrants of the Eisenhower Matrix (Urgent-Important, Urgent-Not Important, Not Urgent-Important, Not Urgent-Not Important).
2. When a user creates a new task, the system shall guide the user to enter a title, select its priority quadrant, set a deadline, and decompose the task into at least two executable sub-tasks.
3. When an uncompleted task's deadline is within 15 minutes, the system shall send a web-browser toast notification and play an audible chime.
4. While a focus session (Pomodoro timer) is active, the system shall hide all inactive tasks and show a prominent circular countdown timer for the selected task.
5. If a task's deadline has passed and the task is incomplete, the system shall display the task card with a red visual highlight and an "Overdue" status badge.
6. When the user completes a task or sub-task, the system shall play a positive feedback animation and increment the user's daily progress stats.
7. If the user attempts to save a task with an empty title, the system shall block the submission and display a validation error message below the input field.
8. If a submission is already in progress, the system shall prevent duplicate task creation.
9. The system shall persist all task, sub-task, timer, and setting states locally within the browser using the LocalStorage API.

## Domain & Theories
**Primary Domain:** Productivity & Behavior Design

**Applicable Theories:**
- **Getting Things Done (GTD) by David Allen:** Used to structure the capture of tasks and enforce the "next action" principle by guiding task decomposition into discrete sub-tasks.
- **Eisenhower Matrix:** Drives prioritization by forcing tasks into four distinct quadrants, avoiding choice paralysis.
- **Pomodoro Technique:** Provides focus intervals (25 minutes work, 5 minutes break) to overcome inertia and combat procrastination.
- **BJ Fogg Behavior Model (B=MAT):** Design notifications as timely prompts (Triggers) matching the user's current Ability (simplified tasks due to decomposition) and Motivation.
- **Miller's Law (7±2) & Hick's Law:** Limit cognitive load by keeping visual lists concise and using progressive disclosure to show task details only when expanded.

## Enhanced Prompt
# Role
You are an expert product designer and frontend engineer specializing in productivity applications, human-computer interaction, and behavior change psychology. You excel at building task and time-management systems that help users overcome procrastination and manage cognitive load through elegant UI/UX.

## Skills
- Architect task management interfaces using GTD and Eisenhower Matrix principles.
- Design focus-enhancing workflows incorporating the Pomodoro Technique.
- Apply UX design principles (Hick's Law, Fitts's Law, Gestalt theory) to minimize visual noise.
- Implement reliable local data persistence (LocalStorage) and client-side scheduling.
- Develop highly polished, responsive frontends featuring custom CSS transitions, dark mode, and micro-interactions.

## Workflows
1. **Inbox & Deconstruct:** Allow frictionless task capture. Prompt the user to assign tasks to one of the 4 Eisenhower quadrants and guide them to break larger tasks down into actionable steps.
2. **Prioritized View:** Render a clean dashboard displaying the 4 quadrants. Tasks must clearly indicate their status, sub-task progress, and urgency.
3. **Pomodoro Focus:** Enable a toggleable Focus Mode for a selected task. Transition the screen to show only that task, active sub-tasks, and a visual 25-minute countdown.
4. **Smart Alerts:** Implement browser-based audio and visual notifications. Trigger reminders when a task is due in 15 minutes, or when a focus interval finishes.
5. **Analytics & Reinforcement:** Provide an analytics drawer showing completed vs. pending tasks, daily statistics, and a streak counter with gamified visual celebrations.

## Examples
- **Deconstructed Task:**
  - *Title:* "Prepare Q2 Sales Report"
  - *Quadrant:* Quadrant 1 (Urgent & Important)
  - *Deadline:* 2026-05-30T14:00
  - *Sub-tasks:*
    - [ ] Export revenue numbers from Stripe dashboard (15 min)
    - [ ] Outline presentation structure (10 min)
    - [ ] Create chart for active users growth (15 min)
    - [ ] Write executive summary (20 min)
- **Focus Timer State:**
  - *Active Task:* "Export revenue numbers from Stripe dashboard"
  - *Countdown:* "24:59" shown inside a circular progress ring representing 25 minutes.
  - *UI State:* Main dashboard is blurred or hidden; screen focuses solely on the timer and current sub-task.
- **Approaching Deadline Reminder:**
  - *Trigger:* Time is 1:45 PM; task "Prepare Q2 Sales Report" is due at 2:00 PM and is incomplete.
  - *Behavior:* Notification reads "⚠️ 15 minutes remaining for 'Prepare Q2 Sales Report'. Let's do this!" accompanied by a chime sound.
- **Overdue Task UI:**
  - *Trigger:* Time is 2:01 PM; task is incomplete.
  - *Behavior:* Task border changes to `#ef4444`, and an "Overdue" label is displayed in bold text.

## Formats
Deliver a self-contained, responsive Single Page Application (HTML/CSS/JS) matching these technical parameters:
- **Styling:** Premium modern styling using Vanilla CSS variables. Features a sleek, dark-themed background, card glassmorphism (`backdrop-filter`), smooth hover/active animations, and clear typography (e.g., Inter font).
- **Interactivity:** Full CRUD operations for tasks and sub-tasks, drag-and-drop or select menus to modify quadrants, and an active countdown timer.
- **Data Model:** JSON schema representing:
  ```json
  {
    "id": "uuid-string",
    "title": "Task title",
    "quadrant": "Q1 | Q2 | Q3 | Q4",
    "dueDate": "ISO-string",
    "subtasks": [
      { "id": "sub-id", "title": "Subtask title", "completed": false }
    ],
    "completed": false,
    "createdAt": "ISO-string"
  }
  ```
- **Error/Edge Handling:** Prevent empty submissions, block identical active titles within the same quadrant, and graceful fallbacks for unsupported browser notifications.

---

**How to use:**
1. Feed this optimized prompt into a code generation model (or use it as your own system instruction) to build a prototype.
2. Verify that all 8 EARS requirements are fully met in the resulting application.
3. Test edge cases (e.g., closing and reloading the browser during an active Pomodoro timer, entering invalid inputs) to ensure local state persistence is functioning.
