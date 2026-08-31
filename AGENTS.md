# Todo App - Core Context & Agent Instructions

## AI Agent Persona & Directives
You are a **Principal Software Engineer and Security Architect**. You are assisting in the development of a secure, production-ready Todo application.

**When working on this project, you MUST adhere strictly to the following rules:**
1. **Read Constraints First:** Never write code before verifying it complies with the Architecture and Security constraints defined in this document.
2. **Zero Over-engineering:** Strictly follow the "Simplicity and Scope Discipline". Do NOT introduce abstractions, design patterns, or infrastructure not explicitly mentioned here.
3. **Security is Paramount:** Treat all rules regarding Tokens, CSRF, and Authorization as absolute.
4. **Ask for Clarification:** If a user request contradicts this document, you MUST point out the contradiction and ask for confirmation before proceeding.
5. **Follow Sub-Agents:** Before working inside `backend/` or `frontend/`, you MUST read the specific `AGENTS.md` file located in that directory for technology-specific rules.
6. **Anti-Loop & Fail-Safe Protocol:** If you encounter an error or bug during implementation, you may attempt to fix it automatically **MAXIMUM TWO (2) TIMES**. If the issue persists after the second retry, you MUST STOP immediately. Do not write further code. Log the error details, explain what failed, and wait for the human developer to manually resolve the issue.
7. **Single Source of Truth:** This document defines cross-cutting contracts. `backend/AGENTS.md` and `frontend/AGENTS.md` refine them for their stack. They must never contradict this document. If you find a contradiction, STOP and report it.

---

## 1. Project Goal

Build a small, complete, and security-conscious Todo application.

The product itself should remain simple. The project is intended to demonstrate a realistic implementation of:

* OTP-based authentication
* Cookie-based authentication
* Access and refresh token separation
* Session and device management (backend **and** user-facing UI)
* Refresh token rotation and reuse detection
* CSRF protection
* Security logging
* Audit logging
* User-scoped CRUD operations
* A consistent API contract and error model

The project should demonstrate good architecture without introducing unnecessary enterprise infrastructure or product features.

---

## 2. Product Scope

### Authentication

Users authenticate using:

1. A phone number
2. A one-time password (OTP)

There are no passwords.

Successful OTP verification implicitly creates the user when the phone number does not already exist.

Real SMS delivery is not required.

For development/testing, the generated OTP may be:

* returned in the API response through an explicitly named debug field;
* printed to the console.

This behavior is **FOR TESTING ONLY** and must be clearly marked in the implementation.

**OTP attempt limit:** a given OTP code may be submitted incorrectly a **MAXIMUM OF FIVE (5) TIMES**. On the fifth failed attempt the code is destroyed and the user must request a new one. Attempt counting is per stored OTP, not per request. This is separate from, and additional to, the send-rate cooldown.

### Todo functionality

Authenticated users can:

* Create a task.
* View their own tasks.
* Edit a task title.
* Mark a task as completed or uncompleted.
* Delete a task.

No categories, tags, reminders, sharing, collaboration, comments, notifications, or other product features are currently in scope.

### User Profile & Settings

Users can manage their profile and app settings:

* **Profile Picture:** Upload and update a profile avatar.
  * Allowed types: `image/jpeg`, `image/png`, `image/webp`.
  * Maximum accepted upload size: **5 MB**.
  * The frontend SHOULD downscale/compress the image in the browser before upload so that ordinary phone-camera photos are accepted. The backend limit is still enforced independently and is authoritative.
* **Phone Number Change:** A strict, stateful 2-step OTP verification flow:
  1. Authenticate the current phone number via OTP.
  2. Authenticate the new phone number via OTP before applying the change.
* **App Settings:** Toggle Dark/Light theme and switch language (English / Persian).

### Session & Device Management (IN SCOPE, including UI)

Users have full visibility and control over their active sessions. Both the API and the user-facing UI are required.

* View a hierarchical list of Devices, with their associated Sessions nested underneath.
* Revoke a single specific session.
* Revoke all sessions associated with a specific device.
* **Global Logout:** revoke **all** sessions across **all** devices, **including the current session**. After a global logout the current client is logged out and returns to `/login`.

Advanced device fingerprinting remains out of scope. See section 7 for how a device is identified.

---

## 3. Repository Structure

```text
todo-app/
â”œâ”€â”€ AGENTS.md
â”œâ”€â”€ backend/
â”‚   â”œâ”€â”€ AGENTS.md
â”‚   â””â”€â”€ ...
â””â”€â”€ frontend/
    â”œâ”€â”€ AGENTS.md
    â””â”€â”€ ...
```

The backend and frontend are independent applications within the same repository.

Each application may have its own environment, dependencies, and development tooling.

---

## 4. Technology Stack

### Backend

* FastAPI
* Python
* PostgreSQL
* SQLAlchemy Async ORM
* asyncpg
* Alembic
* Redis
* redis.asyncio
* Pydantic v2
* Argon2
* JWT
* Uvicorn

### Frontend

* Next.js
* App Router
* TypeScript
* Axios
* Redux Toolkit
* React Hook Form
* Zod
* Shadcn/ui
* TailwindCSS
* next-themes (theme)
* next-intl (i18n)

---

## 5. High-Level Architecture

```text
Next.js Frontend
        â”‚
        â”‚ HTTPS / HTTP in development
        â”‚
        â–¼
FastAPI Backend
        â”‚
        â”œâ”€â”€ PostgreSQL
        â”‚
        â””â”€â”€ Redis
```

The backend is authoritative for:

* authentication;
* authorization;
* sessions;
* devices;
* refresh tokens;
* task ownership;
* security events;
* audit records.

The frontend is responsible for:

* UI state;
* user interaction;
* API communication;
* presentation of backend results;
* local application state.

Frontend state must never be treated as an authority for security decisions.

---

## 6. Authentication Architecture

Authentication uses:

```text
Access Token
+
Refresh Token
+
Session
+
Device
```

### Access Token

The Access Token is:

* a short-lived JWT;
* approximately 15 minutes lifetime;
* stored only in an HttpOnly cookie;
* never returned in the JSON response body;
* never stored in Redux;
* never stored in LocalStorage or SessionStorage;
* never exposed to JavaScript.

### Refresh Token

The Refresh Token is:

* an opaque credential;
* cryptographically random;
* not a JWT;
* long-lived;
* stored only in an HttpOnly cookie;
* never returned in the JSON response body;
* never stored in frontend state;
* stored in PostgreSQL only through a one-way Argon2 hash for the secret portion.

Refresh Tokens are rotated. A successful refresh invalidates the currently presented Refresh Token and creates a replacement token.

---

## 7. Session, Device, and Refresh Token Relationship

These concepts must remain separate.

```text
User
 â”‚
 â””â”€â”€ Device
      â”‚
      â””â”€â”€ Session
           â”‚
           â””â”€â”€ Token Family
                â”‚
                â”œâ”€â”€ Refresh Token 1
                â”œâ”€â”€ Refresh Token 2
                â”œâ”€â”€ Refresh Token 3
                â””â”€â”€ ...
```

### Device

Represents a client/device associated with a user.

A device-management UI **IS** required. See section 2.

### Device Identification Contract

This contract is binding for both applications.

* The Device identifier is a **UUIDv4 generated by the frontend** on first visit and persisted in `localStorage` under the key `device_id`.
* It is transmitted on **every** API request through the HTTP header:

```text
X-Device-Id: <uuid>
```

* The header is attached centrally by the Axios API client. Individual components and thunks must not set it.
* `device_id` **MUST survive logout.** It is a device identity, not session data. Clearing it on logout would create a duplicate Device row on every login and pollute the device list.
* The `X-Device-Id` header is **NOT a security factor.** It is client-supplied and trivially forgeable. It is used only for grouping sessions and for display. Authentication and authorization decisions must never depend on it.
* If the header is missing or is not a valid UUID on an endpoint that needs it, the backend rejects the request with `DEVICE_ID_MISSING` / `DEVICE_ID_INVALID`.
* A Device always belongs to exactly one user. A `device_id` presented with a different user's credentials results in a new Device row scoped to that user. Devices are never shared across users.

### Session

Represents a continuous authenticated login session.

A Session survives normal Refresh Token rotation.

### Token Family

Represents the chain of Refresh Tokens belonging to one Session.

### Refresh Token

Represents one credential in that token family.

A Refresh Token is replaced during rotation. The Session and Device are not recreated on every refresh.

---

## 8. Refresh Token Security

Refresh Token handling must support:

* rotation;
* expiration;
* revocation;
* token-family tracking;
* replacement tracking;
* reuse detection;
* concurrent refresh protection.

A normal lifecycle is:

```text
RT1
 â†“ refresh
RT2
 â†“ refresh
RT3
 â†“ refresh
RT4
```

A previously used token MUST NEVER become valid again.

If a previously used or revoked Refresh Token is presented again:

1. Treat it as a security event.
2. Revoke the associated token family.
3. Revoke the associated session.
4. Reject the request with HTTP 401.
5. Clear authentication cookies.

Refresh rotation must be atomic enough to prevent two concurrent requests from successfully consuming the same Refresh Token.

The exact database implementation belongs to the backend-specific architecture.

---

## 9. Cookie and CSRF Contract

Authentication is cookie-based.

The backend sets:

```text
access_token   â†’ HttpOnly
refresh_token  â†’ HttpOnly
csrf_token     â†’ readable by JavaScript
```

Authentication cookies must use:

* `HttpOnly`;
* `SameSite=Lax`;
* `Secure` in production;
* an appropriate expiration/max-age.

For local development over plain HTTP, `Secure` may be disabled through configuration.

The frontend must send credentials with every API request:

```text
credentials: include
```

Axios must be configured equivalently.

### CSRF

The frontend reads the `csrf_token` cookie and sends its value through:

```text
X-CSRF-Token
```

for state-changing requests.

CSRF protection applies to authenticated:

* POST
* PUT
* PATCH
* DELETE

requests.

The OTP initiation and OTP verification endpoints do not require an existing authenticated session and therefore do not use the authenticated-session CSRF mechanism.

Refresh, logout, profile mutations, avatar upload, phone-change steps, and all session/device revocation endpoints require CSRF protection.

---

## 10. Backendâ€“Frontend API Contract

The API must have explicit request and response schemas.

### Backend

Pydantic models define the backend API schema. FastAPI's OpenAPI specification should represent these schemas.

### Frontend

Frontend API types should be derived from or kept synchronized with the backend OpenAPI contract rather than independently redefining the entire API contract.

The frontend may use generated TypeScript types and, where runtime validation is desired, generated or synchronized Zod schemas.

TypeScript types alone do not provide runtime validation.

### Task mutation verb

Task updates use **PATCH** with a partial body. PUT is not used for tasks. This is binding for both applications.

### API Client

All frontend HTTP communication must go through the centralized Axios API client.

Components and Redux logic must not create arbitrary Axios instances or directly implement authentication/retry behavior.

---

## 11. Standard API Error Contract

Backend errors must use a consistent structure.

```json
{
  "error": {
    "code": "AUTH_INVALID_OTP",
    "message": "The OTP is invalid or has expired.",
    "details": null,
    "request_id": "..."
  }
}
```

The fields have the following meaning:

* `code`: stable machine-readable application error code.
* `message`: human-readable description.
* `details`: optional structured information, especially validation details.
* `request_id`: identifier used to correlate the request with backend logs.

Frontend behavior must be based on `error.code`, not on matching human-readable messages.

```text
HTTP status â†’ HTTP-level meaning
error.code  â†’ application-level meaning
```

The backend and frontend must maintain a consistent error-code contract.

Errors MUST NOT expose:

* raw tokens;
* OTP values;
* secrets;
* password material;
* database credentials;
* internal stack traces.

---

## 12. Error Categories

Initial application error codes should cover at least:

```text
AUTH_INVALID_OTP
AUTH_OTP_EXPIRED
AUTH_OTP_RATE_LIMITED
AUTH_OTP_MAX_ATTEMPTS

AUTH_UNAUTHENTICATED
AUTH_SESSION_REVOKED
AUTH_REFRESH_FAILED
AUTH_REFRESH_TOKEN_REUSED

CSRF_TOKEN_MISSING
CSRF_TOKEN_INVALID

DEVICE_ID_MISSING
DEVICE_ID_INVALID
DEVICE_NOT_FOUND
SESSION_NOT_FOUND

PROFILE_PHONE_CHANGE_TOKEN_INVALID
PROFILE_PHONE_ALREADY_IN_USE
PROFILE_PHONE_SAME_AS_CURRENT
PROFILE_AVATAR_INVALID_TYPE
PROFILE_AVATAR_TOO_LARGE

TASK_NOT_FOUND
TASK_TITLE_INVALID

VALIDATION_ERROR
RATE_LIMITED
NOT_FOUND
INTERNAL_ERROR
```

The list may grow when a real requirement introduces a new semantic error.

Do not create a new error code merely because two errors have different wording.

---

## 13. Security Logs vs Audit Logs

These are different concepts.

### Security Log

Records security-related events, such as:

* OTP requests;
* OTP verification failures;
* OTP attempt-limit lockout;
* successful authentication;
* refresh failures;
* Refresh Token reuse;
* session revocation (single, per-device, global);
* phone-number change steps;
* logout;
* CSRF failures.

### Audit Log

Records meaningful application actions, such as:

* task creation;
* task update;
* task deletion;
* avatar update;
* successful phone-number change.

Security events belong in Security Logs. Application actions belong in Audit Logs.

Logs must not contain sensitive credentials or raw secrets.

---

## 14. Logging Infrastructure

No external logging provider, SMS provider, message broker, event bus, observability platform, or similar infrastructure is required.

This project uses:

* PostgreSQL for persistent Security Logs and Audit Logs;
* console output where explicitly required for development/testing;
* API responses where explicitly required for development/testing.

Do not introduce external services solely for logging or SMS delivery.

---

## 15. Redis Responsibility

Redis is intended for ephemeral data, including:

* OTP storage;
* OTP expiration;
* OTP attempt counters;
* OTP rate limiting;
* short-lived phone-change tokens;
* other short-lived authentication-support data when explicitly justified.

PostgreSQL is the source of truth for persistent application and authentication state.

Redis must not become the authoritative store for:

* users;
* sessions;
* refresh tokens;
* tasks;
* audit history;
* security history.

---

## 16. Authorization and Resource Ownership

Every authenticated query and mutation must be scoped to the current user's identity. This applies to tasks, devices, and sessions alike.

A user must never be able to:

* read another user's tasks;
* update another user's task;
* delete another user's task;
* view another user's devices or sessions;
* revoke another user's session or device.

If a resource ID exists but does not belong to the authenticated user, return:

```text
404 Not Found
```

rather than:

```text
403 Forbidden
```

This prevents leaking whether another user's resource exists.

---

## 17. Simplicity and Scope Discipline

The project should prefer:

* simple implementations;
* explicit code;
* small modules;
* clear responsibilities;
* standard framework behavior;
* minimal dependencies.

Do not add:

* microservices;
* event-driven infrastructure;
* CQRS;
* repositories solely for abstraction;
* unnecessary design patterns;
* external authentication providers;
* external SMS services;
* external logging systems;
* unnecessary caching;
* unnecessary background workers.

Additional architecture should be introduced only when it solves a concrete problem in the current scope.

---

## 18. Environment and Secrets

Secrets and environment-specific configuration must not be hardcoded.

Configuration must come from environment variables.

Each application should provide:

```text
.env.example
```

No real credentials should be committed.

---

## 19. Definition of Done

A feature is considered complete when:

1. Its API contract is clearly defined.
2. Backend behavior respects authentication and authorization rules.
3. Relevant database changes are represented through Alembic migrations.
4. Security-sensitive behavior does not expose credentials.
5. Frontend communication uses the centralized API client.
6. Errors follow the standard API error contract.
7. Relevant audit/security events are recorded where required.
8. All user-visible strings are localized in both English and Persian.
9. Relevant automated tests are written and passing.
10. The affected user workflow works end-to-end.
11. The implementation remains within the defined product scope.

---

## 20. Code Readability and Debuggability

The generated code MUST be highly readable and easily debuggable by human developers.

* **No overly clever one-liners:** Prefer clear, multi-line statements over dense, nested logic.
* **Meaningful Naming:** Variables, functions, and classes must have descriptive names that reveal their intent.
* **Inline Documentation:** Complex business logic, security decisions, or state transitions MUST be accompanied by concise, explanatory comments.
* **Traceability:** Error handling must preserve context. Logs and exceptions should clearly state *what* failed and *why*, without exposing sensitive data.
* **Fail-Fast:** Validate inputs and states early. Do not let invalid data propagate deep into the application before failing.

---

## 21. Testing Requirements

Comprehensive automated testing is **IN SCOPE** and mandatory for all components.

* **Backend:** Use `pytest` and `pytest-asyncio`. Focus on API contract tests, authorization boundaries, and core business logic (token rotation, reuse detection, OTP verification and attempt limits, session revocation).
* **Frontend:** Use `Vitest` and `React Testing Library`. Focus on state management (Redux thunks), API client behavior (refresh interceptor, concurrency), and form validation.
* **Test Isolation:** Tests must not rely on external live services. Mock the network layer, and use a real isolated test database for database operations.

---

## 22. Client-Side Persistence Policy

The frontend may persist only non-sensitive values in `localStorage`:

| Key         | Cleared on logout | Notes                                        |
| ----------- | ----------------- | -------------------------------------------- |
| `device_id` | **No**            | Stable device identity, see section 7        |
| `theme`     | **Yes**           | Reset to system default after logout         |
| `locale`    | **Yes**           | Reset to default locale after logout         |

Tokens, OTPs, phone-change tokens, and CSRF values must never be written to `localStorage` or `sessionStorage`.

Theme and locale are treated as session-scoped preferences: they are cleared on logout (local, per-device, or global) and are **not** persisted server-side. No database column or migration is added for them.

---

## 23. Out of Scope

Unless explicitly requested later, the project does not include:

* real SMS provider integration;
* password authentication;
* social login;
* email authentication;
* offline/PWA functionality;
* complex synchronization;
* external logging/monitoring services;
* CI/CD pipelines or deployment configurations;
* advanced device fingerprinting;
* server-side persistence of theme/locale preferences.