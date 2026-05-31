## Original Requirement
Build a user login system with secure password policies.

**Identified Issues:**
- **Overly Broad Functional Scope**: Does not define what components constitute the login system (e.g., API endpoints, frontend forms, session stores).
- **Ambiguous Security Policies**: "Secure password policies" is undefined and lacks concrete specifications for password length, character complexity, or dictionary checks.
- **Missing Triggers & Conditions**: No explicit triggers for event-driven authentication flows (e.g., successful login, failed login, logging out).
- **No Non-Functional Constraints**: Fails to specify critical security standards such as transport security (HTTPS), cryptographic hashing algorithms, session expiration, rate-limiting thresholds, or anti-enumeration policies.

## EARS Transformation
1. **Event-driven**: When a user submits registration credentials, the system shall validate the password against the password security policy.
2. **Conditional**: If the user's proposed password is less than 12 characters in length OR does not contain at least one uppercase letter, one lowercase letter, one number, and one special character, the system shall prevent registration and display a validation error.
3. **Conditional**: If the user's proposed password matches any entries in a database of commonly compromised passwords (e.g., Have I Been Pwned API or local top 1,000 list), the system shall prevent registration and prompt the user to choose a different password.
4. **Ubiquitous**: The system shall hash all passwords using the Argon2id or bcrypt (cost factor >= 12) algorithm with a unique, cryptographically random salt before storing them in the database.
5. **Event-driven**: When a user submits login credentials (email and password):
   - If the credentials match an active, non-locked user account, the system shall reset the failed login attempts counter, establish a secure session, set a session cookie, and redirect the user to the application dashboard.
   - If the credentials do not match, the system shall increment the failed login attempts counter for that email/IP and display a generic "Invalid email or password" error message.
6. **State-driven**: While a user session is active, the system shall track session idle time and invalidate the session token after 30 minutes of continuous inactivity.
7. **Event-driven**: When a logged-in user clicks "Logout", the system shall invalidate the session identifier on the server side and clear the session cookie from the client's browser.
8. **Event-driven**: When a single email account or IP address accumulates 5 failed login attempts within 15 minutes, the system shall lock the account and block the IP address from login attempts for a duration of 15 minutes.
9. **Ubiquitous**: The system shall transmit all authentication data over HTTPS connections and configure session cookies with `HttpOnly`, `Secure`, and `SameSite=Strict` attributes.

## Domain & Theories
**Primary Domain:** Authentication Security & Session Management

**Applicable Theories:**
- **NIST SP 800-63B Guidelines (Digital Identity Guidelines)** - Outlines modern password management standards, advocating for long passphrases (minimum 8-12 characters), checking passwords against common dictionary/compromised lists, avoiding arbitrary complexity rules that lead to predictable patterns, and rate-limiting brute force attacks.
- **Defense in Depth** - A security methodology that employs multiple independent layers of security controls (e.g., HTTPS transport encryption, Argon2id database hashing, Express/FastAPI rate-limiting middleware, secure cookie attributes, and sanitization of login error messages to prevent username enumeration).
- **Zero Trust Architecture** - Emphasizes "never trust, always verify" by verifying token authenticity, signature, and expiration on every request and enforcing strict access controls at all boundary levels.

## Enhanced Prompt
# Role
Senior security engineer and backend developer specializing in Identity and Access Management (IAM) and web application security, with deep expertise in OWASP guidelines and NIST standards.

## Skills
- Implementing secure password hashing algorithms (Argon2id, bcrypt, PBKDF2)
- Designing resilient session management architectures (session cookies, stateless/stateful JWTs)
- Developing middleware for rate limiting, brute force prevention, and account lockout
- Protecting authentication systems against common vulnerabilities (credential stuffing, session hijacking, XSS, CSRF, SQL Injection, username enumeration)
- Implementing compliance standards (NIST SP 800-63B, OWASP Top 10)
- Writing robust, clean, and testable code in Node.js/Express, Python/FastAPI, or similar modern backend environments

## Workflows
1. **Security Architecture Planning**: Design the authentication database schema, session management flow, and transport security controls.
2. **Database Schema Definition**: Create database tables/schemas for users (storing email, salted password hash, failed attempt counter, lockout expiry timestamp) and active session tokens.
3. **Password Validation Implementation**: Write validation logic that enforces password complexity and queries a compromised password list.
4. **Registration & Hashing**: Implement the registration endpoint, generating a cryptographically secure hash using Argon2id or bcrypt (cost factor >= 12) before saving to the database.
5. **Secure Authentication & Session Issuance**: Implement the login verification logic. Issue secure, signed session identifiers over HTTPS configured with `HttpOnly`, `Secure`, and `SameSite=Strict` cookie flags.
6. **Rate Limiting & Lockout Middleware**: Create middleware to track failed logins by user email and IP. Enforce a 15-minute lockout after 5 failed attempts.
7. **Session Expiration & Logout**: Write a middleware to enforce a 30-minute idle session timeout, and create a logout endpoint to destroy sessions on both the client and server.
8. **Logging & Diagnostics**: Set up secure logging that records security events (e.g., lockouts, failed logins) without exposing sensitive information (e.g., raw passwords or tokens).

## Examples
- **Password Strength Assessment**:
  - *Input*: `123456abcdef` (Rejected - common dictionary pattern)
  - *Input*: `Short1!` (Rejected - less than 12 characters)
  - *Input*: `C0mplex_P@ssphr@se_2026` (Accepted - 23 characters, passes all complexity rules)
- **Generic Error Message**:
  - *Scenario*: User attempts to log in with an email that does not exist in the database.
  - *System Action*: Return HTTP 401 Unauthorized with the message: `Invalid email or password`.
- **Lockout Response**:
  - *Scenario*: An IP address fails login 5 times in 10 minutes.
  - *System Action*: Return HTTP 429 Too Many Requests with the body: `{"error": "Too many failed login attempts. Please try again in 15 minutes."}`.
- **Secure Cookie Header**:
  - `Set-Cookie: session_id=abc123xyz789; Path=/; Max-Age=1800; HttpOnly; Secure; SameSite=Strict`

## Formats
Provide a complete reference implementation containing:
- **Backend API Implementation**: Ready-to-run API endpoints in Node.js/Express or Python/FastAPI for `/api/auth/register`, `/api/auth/login`, `/api/auth/logout`, and `/api/auth/session-status`.
- **Database Schema**: A schema definition (SQL or Prisma) for the `users` table including account lockout columns.
- **Rate-Limiting Middleware**: Middleware code demonstrating IP and email-based throttling.
- **Unit & Integration Tests**: Test suite verifying password validation, hashing security, rate-limiting lockout triggers, and session timeout expiration.
- **Security Alignment Checklist**: A detailed markdown table showing how the implementation addresses specific OWASP Top 10 vulnerabilities and NIST SP 800-63B guidelines.

---

**How to use:**
1. Feed the **Enhanced Prompt** into an AI coding assistant (like Claude) to generate a complete, secure implementation of the login system.
2. Review the generated code against the provided **EARS Transformation** requirements to ensure functional and security completeness.
3. Run the generated unit and integration tests to verify the lockout, rate-limiting, and session validation behaviors.
