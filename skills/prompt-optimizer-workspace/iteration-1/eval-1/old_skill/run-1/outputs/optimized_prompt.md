## Original Requirement
Build a user login system with secure password policies.

**Identified Issues:**
- **Too Broad:** The request does not define the full scope of a login system (e.g., registration, session management, logout, password hashing).
- **Ambiguous Constraints:** The term "secure password policies" is undefined. It doesn't specify complexity rules, hashing algorithms, or protection against common/leaked passwords.
- **No Trigger Conditions:** The flow of successful/failed events is missing, such as what happens during incorrect logins or how rate-limiting is handled.
- **Lack of Session/Security Controls:** No mention of session management (e.g., cookie security, token expiration) or brute-force prevention (e.g., account lockout).

## EARS Transformation
1. The system shall provide a registration interface requiring email address, password, and password confirmation.
2. The system shall provide a login interface requiring email address and password.
3. When a user submits registration or password update credentials, if the password is less than 12 characters OR does not contain at least 1 uppercase letter, 1 lowercase letter, 1 number, and 1 special character, the system shall prevent registration and display a specific validation error message.
4. When a user submits registration credentials, if the password matches a known compromised password from a common password database, the system shall prevent registration and prompt the user to create a different password.
5. The system shall hash all passwords using the bcrypt algorithm with a work factor of 12 prior to storing them in the database.
6. When a user submits credentials via the login interface, if the email and password match the database records and the account is not locked, the system shall authenticate the user, generate a secure HTTP-only session cookie valid for 24 hours, and redirect the user to the dashboard.
7. When a user submits credentials via the login interface, if the email or password do not match the database records, the system shall display a generic "Invalid email or password" error message and increment the failed login counter for that email.
8. If an account experiences 5 consecutive failed login attempts within 15 minutes, the system shall lock the account for 30 minutes and send an email notification to the registered email address.
9. While a user session is active, if there is no user activity for 30 minutes, the system shall invalidate the session token and redirect the user to the login page.
10. When an authenticated user clicks "Logout", the system shall invalidate the session token on the server, clear the session cookie from the client browser, and redirect the user to the login page.

## Domain & Theories
**Primary Domain:** Authentication Security & Identity Management (IAM)

**Applicable Theories:**
- **Defense in Depth** - Implementation of layered security controls (password strength, bcrypt hashing, account lockout, and secure session attributes) to protect user credentials.
- **Zero Trust Architecture** - Never trusting client state; verifying authentication tokens on every request, server-side validation of inputs, and applying the principle of least privilege.
- **OWASP Application Security Verification Standard (ASVS)** - Adhering to standards for credential verification, password storage strength, brute-force protection, and session management.
- **Progressive Disclosure (UX Design)** - Showing password requirements dynamically as the user types and providing real-time feedback to manage cognitive load during registration.

## Enhanced Prompt
# Role
Senior Security Engineer & Full-Stack Developer specializing in IAM (Identity and Access Management) and secure web architectures, with deep expertise in OWASP Top 10 security standards and NIST guidelines.

## Skills
- Design secure and user-friendly authentication flows (login, registration, logout, lockout).
- Implement robust cryptographic password hashing using industry-standard algorithms (bcrypt or Argon2id).
- Apply defense-in-depth principles to prevent credentials-based attacks (brute force, credential stuffing, enumeration).
- Build secure session management (HTTP-only, Secure, SameSite cookies, session expiration, token revocation).
- Create accessible (WCAG compliant) forms with real-time validation and progressive disclosure.

## Workflows
1. **System & Database Schema Design**: Define user database schema with fields for email, hashed_password, failed_login_attempts, locked_until, and session tokens.
2. **Registration and Password Validation**: Implement server-side and client-side password validation (complexity, length, list checking) during user registration.
3. **Password Storage**: Hash passwords using bcrypt with cost factor 12 before writing to the database.
4. **Authentication & Session Issuance**: Verify user credentials, generate secure session identifiers, and issue secure cookies.
5. **Rate Limiting & Lockout**: Track failed login attempts; implement lockout logic after 5 failures within 15 minutes.
6. **Session Expiration & Revocation**: Implement session timeout after 30 minutes of inactivity and full clean up on logout.
7. **Error Handling & Logging**: Use generic error messages for authentication failures to prevent enumeration, and log security events securely.

## Examples
- **Registration Input Validations**:
  - `user@domain.com` / `secret` -> Rejected (failed length, complexity constraints).
  - `user@domain.com` / `password12345` -> Rejected (matches a common/compromised password list).
  - `user@domain.com` / `P@ssword$ecure2026!` -> Accepted. Saved as a 60-character bcrypt hash in database.
- **Authentication Response**:
  - Correct credentials -> Responds with HTTP header `Set-Cookie: session_id=session_uuid_here; Secure; HttpOnly; SameSite=Strict` and HTTP 200/Redirect.
  - Incorrect credentials -> Responds with HTTP 401 and JSON payload `{"error": "Invalid email or password"}` (no mention of whether the email exists).
- **Lockout State**:
  - 5 failed login attempts for `admin@example.com`.
  - Next login attempts block immediately with HTTP 423 (Locked) or generic error with a timer, and writes a log entry: `SECURITY ALERT: Account admin@example.com locked due to multiple failed login attempts.`

## Formats
Deliver a complete implementation package including:
- **Backend API Code**: (Node.js/Express, Python/FastAPI, or similar) containing route handlers for `/register`, `/login`, `/logout`.
- **Database Schema**: SQL definition for `users` and `sessions` tables (with required security fields).
- **Frontend Code**: HTML/CSS/JS files for a responsive login and registration form, using clear validation states and error messages.
- **Security Configuration Checklist**: Documentation detailing the bcrypt cost factor, cookie attributes, rate-limiting parameters, and HTTPS requirements.

---

**How to use:**
1. Provide this prompt to your AI coding assistant to generate a robust and secure authentication system.
2. Ensure the generated code is integrated with HTTPS in your development and production environments.
3. Run integration tests corresponding to the EARS transformation scenarios (success, validation failure, rate-limiting lockout, session timeout).
