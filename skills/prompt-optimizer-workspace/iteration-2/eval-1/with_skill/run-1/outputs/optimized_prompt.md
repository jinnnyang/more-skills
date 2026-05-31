# Prompt Optimization: User Login System with Secure Password Policies

## Original Requirement
Build a user login system with secure password policies.

**Identified Issues:**
- **Overly broad:** The requirement does not define what features are included in a "login system" (e.g., registration, logout, session management, account lockout, audit logs).
- **Ambiguous criteria:** "Secure password policies" is subjective and lacks measurable requirements (e.g., minimum character length, complexity types, and checks against dictionary attacks or compromised lists).
- **Missing triggers/states:** No specifications on when sessions should expire, when account locking triggers, or how failed attempts are handled.
- **Lack of non-functional constraints:** There are no performance thresholds, transport security requirements, or data protection standards specified.

---

## EARS Transformation
The login system shall satisfy the following specifications:

1. **[Ubiquitous]** The system shall enforce HTTPS utilizing TLS 1.3 for all authentication-related requests and responses.
2. **[Ubiquitous]** The system shall include standard security headers (`Strict-Transport-Security`, `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, and `Referrer-Policy`) in all HTTP responses.
3. **[Event-driven]** When a user registers or updates their password, the system shall validate that the password contains at least 12 characters, including at least one uppercase letter (A-Z), one lowercase letter (a-z), one numeric digit (0-9), and one special character (e.g., `!@#$%^&*`).
4. **[Event-driven]** When a user registers or updates their password, the system shall query a breached-password database (e.g., Have I Been Pwned API) and reject the password if it has been exposed in a known breach.
5. **[Event-driven]** When a user submits credentials for login, the system shall verify the email and password against stored bcrypt hashes utilizing a cost factor of at least 12.
6. **[Event-driven]** When a user successfully authenticates, the system shall generate a cryptographically secure 256-bit session token, link it to the user's session record, and store it in an `HttpOnly`, `Secure`, `SameSite=Strict` cookie on the client.
7. **[Unwanted Behavior]** When a login attempt fails 5 consecutive times within a rolling 15-minute window for a specific email address, the system shall lock the account and prevent further authentication attempts for 30 minutes.
8. **[Unwanted Behavior]** When account lockout is triggered, the system shall send an email notification to the registered user address containing details of the lock event and a secure account recovery link.
9. **[State-driven]** While a user session is active, the system shall terminate the session if the user remains inactive (no HTTP requests received) for more than 30 minutes.
10. **[State-driven]** While a user session is active, the system shall terminate the session if the absolute duration since initial authentication exceeds 24 hours.
11. **[Event-driven]** When a user requests to log out, the system shall delete the session token from the server database/store and clear the browser's session cookie.

---

## Domain & Theories
**Primary Domain:** Authentication Security & Cryptography

**Applicable Theories:**
- **Defense in Depth:** Implementing multiple layers of security to prevent single points of failure. This is reflected in combining TLS 1.3 transport security, bcrypt credential hashing, multi-character password complexity, breach lookups, account lockouts, and HttpOnly/SameSite session cookies.
- **Zero Trust Architecture:** Never trust, always verify. The server must validate the cryptographically random session token for every request, enforce server-side expiration times independently of client-side cookies, and treat all inputs as untrusted until validated.
- **Hick's Law & progressive disclosure (UX Design):** Designing signup and login interfaces to present password requirements dynamically as the user types (checking off satisfied rules in real-time) rather than displaying a static, overwhelming list of rules.

---

## Enhanced Prompt

```markdown
# Role
You are a Senior Security Architect and Lead Frontend Engineer specializing in authentication systems, with deep expertise in OWASP Application Security Verification Standards (ASVS v4.0) and security-focused UX design.

## Skills
- Design secure, OWASP-compliant user authentication and session management workflows.
- Implement cryptographic hashing algorithms (bcrypt/argon2id) with secure configuration.
- Develop brute force mitigation strategies including account lockouts and IP rate limiting.
- Ground systems in the Principle of Least Privilege and Zero Trust security policies.
- Build responsive, accessible HTML/CSS/JS interfaces with dynamic, real-time input validation.

## Workflows

1. **User Registration & Validation Workflow**
   - Provide email and password input fields with client-side checks.
   - Run real-time password strength validation using standard metrics (e.g., length, uppercase, lowercase, digits, special characters, and entropy estimation via zxcvbn).
   - Perform server-side schema verification, check the password against a breached password API (e.g., Have I Been Pwned), hash the password with bcrypt (cost factor 12) with a random salt, and store it.

2. **Login & Session Generation Workflow**
   - Check if the account is currently locked before processing credentials.
   - Verify credentials against bcrypt hashes.
   - On success, generate a cryptographically random 256-bit session token, store it in a database with `created_at` and `last_activity_at` timestamps, and issue an `HttpOnly`, `Secure`, `SameSite=Strict` cookie.
   - Reset the consecutive failed attempts counter.

3. **Brute Force & Lockout Workflow**
   - On login failure, increment the consecutive failed login attempts counter.
   - If consecutive failures reach 5 within a 15-minute window, mark the account as locked with a `locked_until` timestamp set to 30 minutes in the future.
   - Dispatch an account lockout email notification with unlock/recovery details.
   - Return a generic error message to prevent username enumeration (e.g., "Invalid email or password").

4. **Session Lifecycle & Invalidation Workflow**
   - Validate the session token on the server for every authenticated request.
   - Check if `last_activity_at` is older than 30 minutes (idle timeout) or if `created_at` is older than 24 hours (absolute timeout). If either is true, delete the session and return 401.
   - On logout request, delete the token from the database and set the cookie's expiration to the past.

## Examples

- **Valid Password Example:**
  - Password: `Tr0ub4dor&3rd`
  - Meets requirements: Length = 13, has uppercase, lowercase, numbers, special characters, and passes breach checklist.
- **Invalid Password Example:**
  - Password: `password123!`
  - Fails: Flagged as a breached password by the Have I Been Pwned API, low entropy.
- **Account Lockout Timing:**
  - 5th failed attempt occurs at `14:00`.
  - Account `user@example.com` locked until `14:30`.
  - Attempt at `14:15` returns standard "Invalid email or password" error but logs the blocked attempt with reason `ACCOUNT_LOCKED`.
- **BCrypt Hashing Sample:**
  - Salt: `$2b$12$e0ZXAQLXh8Q3D9Y6b/7cOe`
  - Output Hash: `$2b$12$e0ZXAQLXh8Q3D9Y6b/7cOexH2Z/Z8G7H/9E1d9M8qG.YqOqZ9D3jS`

## Formats
Deliver a clean, modular repository structure including:
- **Backend API Implementation:** A Node.js/Express (TypeScript) server containing controllers for `/signup`, `/login`, `/logout`, and `/recovery`, alongside session verification middleware.
- **Database Schema (Prisma/SQL):** Database schemas detailing `User` and `Session` models including login failure counts, lockout timestamps, and session creation/activity records.
- **Frontend UI Forms:** Semantic HTML5 registration and login pages styled with modern, accessible CSS (supporting dark mode, focus states, and aria-live status announcements).
- **JavaScript Validation:** Dynamic frontend JS providing visual cues as password strength guidelines are satisfied.
- **Security Audit Configuration:** A checklist detail of CORS, CSP, and helmet middleware configurations deployed.
```

---

## How to use
Provide this enhanced specification directly to your AI developer agent or engineering team. The EARS-based requirements translate cleanly into unit/integration test cases, the domain theories ensure compliance with modern security postures, and the examples establish a precise verification baseline.

---

## Next Step: Pipeline Handoff

I have generated the optimized prompt for building a secure user login system.

Options:
A) web-artifacts-builder — Propose building the application prototype using the newly generated prompt.
B) deep-research — Research deep technical details or competitor approaches for the features in the optimized prompt.
C) github-ops — Prepare the project repository or branch for developing these requirements.
D) No thanks — The optimized prompt is ready as-is.
