# Todo App — Phased Implementation Checklist

Derived from `/AGENTS.md` (root), `backend/AGENTS.md`, `frontend/AGENTS.md`.
Each phase is intentionally small in scope. Complete and verify a phase before moving to the next — later phases assume earlier ones are done and tested.

---

## PHASE 0 — Repo & Tooling Baseline

- [ ] Confirm `todo-app/AGENTS.md`, `backend/AGENTS.md`, `frontend/AGENTS.md` are committed as-is (source of truth).
- [ ] Confirm `backend/` has `pyproject.toml` from `uv init --bare` and `fastapi[standard]` installed.
- [ ] Confirm `frontend/` has a working `bun install` / Next.js App Router skeleton.
- [ ] Add root `.gitignore` covering `__pycache__/`, `.venv/`, `node_modules/`, `.next/`, `uploads/`, `.env`.
- [ ] Create `docker-compose.yml` for local PostgreSQL and Redis **only**.
  - [ ] Redis must use `redis:8.6.4-alpine`.
  - [ ] PostgreSQL must use the latest stable PostgreSQL image available at implementation time.
  - [ ] Docker Compose must never be used for any other application, service, or infrastructure component.
- [ ] Verify PostgreSQL and Redis containers start and are reachable locally.
- [ ] Decide and document local ports (backend, frontend, Postgres, Redis) in root `README.md`.

---

## PHASE 1 — Backend: Project Skeleton & Config

- [ ] Create `backend/app/` package with empty `__init__.py` files per the suggested structure.
- [ ] Create `backend/app/core/config.py` using Pydantic v2 `BaseSettings` (`pydantic-settings`).
- [ ] Add all settings fields from backend §34: `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, `OTP_TTL_SECONDS`, `OTP_RESEND_COOLDOWN_SECONDS`, `OTP_MAX_ATTEMPTS`, `PHONE_CHANGE_TOKEN_TTL_SECONDS`, `AVATAR_MAX_BYTES`, `UPLOADS_DIR`, `FRONTEND_ORIGIN`, `COOKIE_SECURE`, `ENV`.
- [ ] Create `backend/.env.example` with the same keys, no real values.
- [ ] Create local `backend/.env` (gitignored) with dev values (`COOKIE_SECURE=false`, `ENV=development`).
- [ ] Add dependencies: `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `redis`, `argon2-cffi`, `pyjwt` (or `python-jose`), `python-multipart`, `pillow`, `pydantic-settings`.
- [ ] Add dev dependencies: `pytest`, `pytest-asyncio`, `httpx`, `fakeredis`.
- [ ] Create `backend/app/main.py` with a minimal FastAPI app instance and a `/health` route.
- [ ] Confirm `uv run uvicorn app.main:app --reload` boots successfully from the IDE/run configuration; the backend is not run through Docker Compose.

---

## PHASE 2 — Backend: Database Foundation

- [ ] Create `backend/app/db/base.py` with SQLAlchemy 2.0 `DeclarativeBase`.
- [ ] Create `backend/app/db/session.py` with async engine (`create_async_engine`) reading `DATABASE_URL`.
- [ ] Implement `get_db_session` async generator dependency (yields `AsyncSession`, closes on exit).
- [ ] Confirm connection to local PostgreSQL works via a throwaway script or `/health` DB check.
- [ ] Initialize Alembic in `backend/alembic/` (`alembic init`).
- [ ] Configure `alembic/env.py` to use the async engine and import `Base.metadata` for autogenerate.
- [ ] Configure `alembic.ini` (or env var override) to read `DATABASE_URL` from settings, not hardcoded.

---

## PHASE 3 — Backend: Models (one sub-phase per table)

### 3.1 User model
- [ ] Create `app/models/user.py`: `id` (UUID pk), `phone_number` (String, unique, not null), `avatar_path` (nullable), `created_at`, `updated_at`.
- [ ] Add server-side timestamp defaults (`server_default=func.now()`, `onupdate` for `updated_at`).

### 3.2 Device model
- [ ] Create `app/models/device.py`: `id` (UUID pk, **client-supplied, not server-generated**), `user_id` (FK → users.id), `name` (nullable), `user_agent` (nullable), `created_at`, `last_seen_at` (nullable), `revoked_at` (nullable).
- [ ] Add FK cascade behavior appropriate for user deletion (define policy, even if user deletion isn't a current feature).
- [ ] Add composite index/uniqueness consideration on `(id, user_id)` per binding lookup contract.

### 3.3 Session model
- [ ] Create `app/models/session.py`: `id`, `user_id` (FK), `device_id` (FK), `token_family_id` (UUID), `created_at`, `expires_at`, `last_used_at` (nullable), `revoked_at` (nullable), `revoke_reason` (nullable).
- [ ] Add index on `user_id`, index on `device_id`.

### 3.4 RefreshToken model
- [ ] Create `app/models/refresh_token.py`: `id`, `session_id` (FK), `token_family_id`, `token_hash`, `issued_at`, `expires_at`, `used_at` (nullable), `revoked_at` (nullable), `replaced_by_id` (nullable, self-referential FK).
- [ ] Add index on `session_id`, index on `token_family_id`.

### 3.5 Task model
- [ ] Create `app/models/task.py`: `id`, `user_id` (FK), `title` (String), `is_done` (Boolean, default False), `created_at`, `updated_at`.
- [ ] **No `deleted_at` field** — hard delete only.
- [ ] Add index on `user_id` for task listing.

### 3.6 SecurityLog model
- [ ] Create `app/models/security_log.py` per backend §28 fields (`id`, `user_id` nullable, `session_id` nullable, `device_id` nullable, `event_type`, `severity`, `request_id` nullable, `ip_address` nullable, `user_agent` nullable, `metadata` JSON nullable, `created_at`).
- [ ] Define `event_type` as a String/Enum matching backend §26 event list.

### 3.7 AuditLog model
- [ ] Create `app/models/audit_log.py` per backend §27 fields (`id`, `user_id` nullable, `action`, `resource_type`, `resource_id` nullable, `request_id` nullable, `metadata` JSON nullable, `created_at`).

### 3.8 Migration
- [ ] Generate the initial Alembic migration covering all 7 tables.
- [ ] Manually review the migration file for correct FK cascades and indexes (autogenerate is not always right).
- [ ] Apply migration to local dev DB and confirm all tables exist with `\d` in psql.
- [ ] Confirm `alembic downgrade -1` / `upgrade head` both work cleanly.

---

## PHASE 4 — Backend: Core Security Utilities (no endpoints yet)

### 4.1 Redis client
- [ ] Create `app/core/redis_client.py` using `redis.asyncio`, reading `REDIS_URL`, exposing a reusable client/dependency.

### 4.2 JWT / Access Token utilities
- [ ] In `app/core/security.py`, implement `create_access_token(user_id, session_id) -> str` (JWT with `sub`, `sid`, `exp`, `HS256`, ~15 min).
- [ ] Implement `decode_access_token(token) -> payload | raises` with signature + expiry validation.

### 4.3 Refresh token utilities
- [ ] Implement generation of `token_id` + cryptographically random `secret` (use `secrets`, not `random`).
- [ ] Implement Argon2 hashing of the secret and Argon2 verification helper.
- [ ] Implement encode/decode of the `token_id.secret` cookie value format.

### 4.4 CSRF token utilities
- [ ] Implement cryptographically random CSRF token generation.
- [ ] Implement constant-time comparison helper for CSRF header vs cookie.

### 4.5 Cookie helpers
- [ ] Create `app/core/cookies.py` centralizing set/clear for `access_token`, `refresh_token`, `csrf_token`.
- [ ] Set cookie attrs from config: `HttpOnly` (true for access/refresh, false for csrf), `Secure` (from `COOKIE_SECURE`), `SameSite=Lax`, correct `max_age`/`expires` per token type.
- [ ] Implement a `clear_all_auth_cookies(response)` helper using identical attributes used at set-time.

### 4.6 Error contract
- [ ] Create `app/schemas/errors.py` with the `ApiError` envelope shape (`code`, `message`, `details`, `request_id`).
- [ ] Create `app/core/errors.py` with an `AppError` exception class carrying `code`/`http_status`/`message`/`details`.
- [ ] Define one constant/enum listing every error code from root §12.

### 4.7 Request ID middleware
- [ ] Add middleware generating a `request_id` (UUID) per request if not already present, storing it on `request.state`.

### 4.8 Exception handlers
- [ ] Register a handler for `AppError` → standard envelope + correct HTTP status.
- [ ] Register a handler for `RequestValidationError` → `VALIDATION_ERROR` envelope with field `details`.
- [ ] Register a handler for `HTTPException` → standard envelope.
- [ ] Register a catch-all handler for unhandled exceptions → `INTERNAL_ERROR`, no stack trace leaked, but logged server-side.

### 4.9 CORS
- [ ] Configure `CORSMiddleware` with `allow_origins=[FRONTEND_ORIGIN]` only, `allow_credentials=True`.
- [ ] Add `X-CSRF-Token` and `X-Device-Id` to `allow_headers`.

**Checkpoint:** app boots, hitting a deliberately broken route returns the standard error envelope with a `request_id`.

---

## PHASE 5 — Backend: Dependencies Layer

### 5.1 Device dependency
- [ ] Create `app/dependencies/device.py`: read `X-Device-Id` header.
- [ ] Missing header → raise `AppError(DEVICE_ID_MISSING, 400)`.
- [ ] Present but invalid UUID → raise `AppError(DEVICE_ID_INVALID, 400)`.
- [ ] Return the raw device UUID (validation only — no DB lookup here yet).

### 5.2 Current-user dependency
- [ ] Create `app/dependencies/auth.py`: read `access_token` cookie.
- [ ] Missing cookie → `AUTH_UNAUTHENTICATED` (401).
- [ ] Invalid signature/expired → `AUTH_UNAUTHENTICATED` (401).
- [ ] Decode `sub` (user id) and `sid` (session id).
- [ ] Load user by id; not found → `AUTH_UNAUTHENTICATED` (401).
- [ ] Load session by id; not found, revoked, or expired → `AUTH_SESSION_REVOKED` (401).
- [ ] Return a small `CurrentUser` object bundling `user` + `session_id`.

### 5.3 CSRF dependency
- [ ] Create `app/dependencies/csrf.py`: read `csrf_token` cookie and `X-CSRF-Token` header.
- [ ] Missing header → `CSRF_TOKEN_MISSING` (403) + Security Log `CSRF_FAILURE`.
- [ ] Mismatch (constant-time compare) → `CSRF_TOKEN_INVALID` (403) + Security Log `CSRF_FAILURE`.
- [ ] Apply only where the route explicitly requires it (not globally middleware-based, since OTP endpoints are exempt).

**Checkpoint:** write a throwaway protected test route using all three dependencies together and confirm each failure mode returns the right code/status.

---

## PHASE 6 — Backend: Logging Services

- [ ] Create `app/services/` logging helpers (or fold into a `logging_service.py`) — a function to write a `SecurityLog` row and a function to write an `AuditLog` row, both taking a DB session so they participate in the caller's transaction.
- [ ] Confirm helpers never accept/store raw tokens, OTPs, or secrets — enforce via docstring + code review, not just convention.
- [ ] Confirm helper signatures accept `request_id` so it can be attached from `request.state`.

---

## PHASE 7 — Backend: OTP Service & Send-OTP Endpoint

### 7.1 Phone normalization
- [ ] Implement a phone-number normalization function (single canonical format) in a shared utility.
- [ ] Add a Pydantic validator/schema (`schemas/auth.py`) that runs normalization on input.

### 7.2 OTP service
- [ ] Create `app/services/otp_service.py`: `generate_otp()` using `secrets`, 4 digits.
- [ ] Implement `otp:{phone_number}` storage in Redis with TTL from config.
- [ ] Implement `otp_attempts:{phone_number}` counter key, same TTL.
- [ ] Implement `otp_cooldown:{phone_number}` key for send-rate limiting (TTL = cooldown seconds).
- [ ] Implement `check_and_set_cooldown()` → raises `AUTH_OTP_RATE_LIMITED` (429) if still active.
- [ ] Implement `verify_otp(phone, code)`: constant-time compare, increments attempts atomically (`INCR`) on mismatch, deletes OTP+counter on 5th failure raising `AUTH_OTP_MAX_ATTEMPTS` (429), deletes both on success.

### 7.3 `POST /auth/send-otp`
- [ ] Create `app/schemas/auth.py` request/response models for send-otp.
- [ ] Create `app/routers/auth.py`, implement the route per backend §12 steps 1–8.
- [ ] Gate `otp_debug` field in response behind `ENV != production`.
- [ ] Print OTP to console for dev only.
- [ ] Write `OTP_REQUESTED` Security Log entry (never the code).
- [ ] No CSRF required on this route (unauthenticated).
- [ ] Manually test: first call succeeds, immediate second call returns `AUTH_OTP_RATE_LIMITED`.

---

## PHASE 8 — Backend: Verify-OTP, Session/Device/RefreshToken Creation

- [ ] Create response/request schemas for `POST /auth/verify-otp`.
- [ ] Require `X-Device-Id` via the Phase 5 dependency.
- [ ] Step: read OTP from Redis, `AUTH_OTP_EXPIRED` if absent.
- [ ] Step: constant-time compare; on mismatch route through `otp_service.verify_otp` attempt logic.
- [ ] Step: on success, delete OTP + attempts.
- [ ] Step: find-or-create `User` by normalized phone number.
- [ ] Step: find-or-create `Device` scoped by `(X-Device-Id, user_id)`; update `user_agent`, `last_seen_at`.
- [ ] Step: create `Session` (`token_family_id` = new UUID, `expires_at` per refresh-token lifetime config).
- [ ] Step: create first `RefreshToken` row (Argon2-hashed secret) in that family.
- [ ] Step: create Access Token JWT containing `sub`, `sid`.
- [ ] Step: set `access_token`, `refresh_token`, and a fresh `csrf_token` cookie via cookie helpers.
- [ ] Step: write `LOGIN_SUCCESS` Security Log.
- [ ] Confirm neither token appears anywhere in the JSON response body.
- [ ] Wrap DB writes (user/device/session/refresh_token/security_log) in one transaction.
- [ ] Manual test: verify with correct OTP → cookies set, 200 response, no tokens in body.
- [ ] Manual test: verify with wrong OTP 5x → 5th response is `AUTH_OTP_MAX_ATTEMPTS`, further verify attempts return `AUTH_OTP_EXPIRED` (code destroyed).

---

## PHASE 9 — Backend: Refresh Endpoint & Rotation Logic

### 9.1 Rotation core
- [ ] Implement `app/services/auth_service.py::rotate_refresh_token(...)` implementing backend §9 flow end to end.
- [ ] Parse `token_id.secret` from cookie.
- [ ] Look up `RefreshToken` by `token_id`.
- [ ] Load associated `Session`; reject if revoked/expired → `AUTH_SESSION_REVOKED`.
- [ ] Verify token `expires_at`/`revoked_at`/`used_at` state.
- [ ] Argon2-verify the secret against `token_hash`.
- [ ] Atomically consume: `UPDATE refresh_tokens SET used_at = now() WHERE id = :id AND used_at IS NULL AND revoked_at IS NULL`, check rowcount == 1.
- [ ] If rowcount == 0 → treat as **reuse** (Phase 9.2).
- [ ] Create replacement `RefreshToken` (same `session_id`, same `token_family_id`), set old row's `replaced_by_id`.
- [ ] Issue new Access Token.
- [ ] Update `sessions.last_used_at`, `devices.last_seen_at`.
- [ ] Write `REFRESH_SUCCESS` Security Log.

### 9.2 Reuse detection
- [ ] On detecting reuse (already used/revoked token presented), write `REFRESH_TOKEN_REUSED` Security Log.
- [ ] Revoke the entire token family (mark all non-revoked tokens in family `revoked_at = now()`).
- [ ] Revoke the associated `Session`.
- [ ] Return 401 `AUTH_REFRESH_TOKEN_REUSED`.
- [ ] Clear auth cookies on this response.

### 9.3 Route
- [ ] Implement `POST /auth/refresh` requiring CSRF dependency.
- [ ] Wire the above service function in.
- [ ] On any invalid/expired/revoked/unusable token: 401, clear cookies, do not issue new tokens.
- [ ] Set replacement cookies on success.

### 9.4 Concurrency test (manual or scripted)
- [ ] Fire two parallel refresh requests with the same refresh cookie; confirm exactly one succeeds and the other gets reuse-style rejection (or a clean 401), and confirm the session survives if the "loser" request is just a race, not real reuse — validate against backend §11/§39 expectations.

---

## PHASE 10 — Backend: Logout & CSRF-Token Endpoints

- [ ] Implement `GET /auth/csrf-token`: generate token, set cookie, no auth required, return 200.
- [ ] Implement `POST /auth/logout` requiring CSRF (and current-user, but tolerate missing/invalid session gracefully).
- [ ] Identify current session from refresh/session context; revoke session + its active refresh token family.
- [ ] Clear all three cookies.
- [ ] Write `LOGOUT` Security Log.
- [ ] Confirm idempotency: calling logout twice in a row both return the same success shape, no error leaking whether a session existed.

**Checkpoint — Phase 5–10 Definition of Done:** full login → refresh → logout cycle works via curl/Postman with real cookies, reuse detection verified manually.

---

## PHASE 11 — Backend: Profile — Avatar Upload

- [ ] Create `app/schemas/profile.py` response schema for avatar endpoint.
- [ ] Implement `POST /profile/avatar` requiring auth + CSRF, `multipart/form-data`.
- [ ] Reject unsupported `Content-Type` claim early → but do not trust it as final validation.
- [ ] Enforce 5 MB size limit → `PROFILE_AVATAR_TOO_LARGE` (413) if exceeded.
- [ ] Decode the actual image bytes with Pillow; reject non-conforming files → `PROFILE_AVATAR_INVALID_TYPE` (400).
- [ ] Generate stored filename as `{user_id}/{uuid4}.{ext}` — never use client filename.
- [ ] Save into `UPLOADS_DIR`; store the **relative** path on `users.avatar_path`.
- [ ] Delete/orphan the previous avatar file deterministically when replacing.
- [ ] Write `AVATAR_UPDATED` Audit Log in the same transaction as the DB update.
- [ ] Mount `/uploads` as a static directory in `main.py`, path from config.
- [ ] Return new avatar path/URL in response body.
- [ ] Manual test: upload valid jpeg/png/webp, oversized file, and a renamed non-image file (e.g. `.jpg` that's actually text) — confirm each is handled correctly.

---

## PHASE 12 — Backend: Profile — Phone Number Change (2-Step Flow)

- [ ] Define Redis key `phone_change:{user_id}` for the step-up token, TTL from config.
- [ ] Implement `POST /profile/phone/request-current`: send OTP to current phone number (reuse OTP service, same cooldown/attempt rules).
- [ ] Implement `POST /profile/phone/verify-current`: verify that OTP; on success issue random `phone_change_token`, store in Redis keyed to user, return token in body (never as cookie).
- [ ] Implement `POST /profile/phone/request-new`: require valid `phone_change_token`; validate new number not in use (`PROFILE_PHONE_ALREADY_IN_USE`) and not same as current (`PROFILE_PHONE_SAME_AS_CURRENT`); send OTP to new number.
- [ ] Bind the token to the requested new number in Redis once step 3 runs (so it can't be reused for a different number).
- [ ] Implement `POST /profile/phone/verify-new`: require token + new number + new OTP; on success update `users.phone_number`, invalidate token, delete both OTPs.
- [ ] All four routes require auth + CSRF.
- [ ] Invalid/expired/consumed token on any step → `PROFILE_PHONE_CHANGE_TOKEN_INVALID` (403).
- [ ] Write Security Log events: `PHONE_CHANGE_REQUESTED`, `PHONE_CHANGE_CURRENT_VERIFIED`, `PHONE_CHANGE_COMPLETED`.
- [ ] Write Audit Log `PHONE_CHANGED` on completion, same transaction as the phone number update.
- [ ] Confirm sessions are **not** revoked by a phone number change.
- [ ] Confirm no OTP or token value ever appears in any log.

---

## PHASE 13 — Backend: Security — Device & Session Management API

- [ ] Create `app/services/session_service.py` for shared revocation logic.
- [ ] Implement `GET /security/devices`: return devices scoped to current user with nested active sessions; compute `is_current` per session from the `sid` claim.
- [ ] Confirm response never includes token values, hashes, or token IDs.
- [ ] Implement `DELETE /security/sessions/{id}`: scoped by `(id, user_id)`; not found/other-user → 404 `SESSION_NOT_FOUND`. Also revokes the associated refresh-token family.
- [ ] Implement `DELETE /security/devices/{id}/sessions`: scoped by `(id, user_id)`; not found → 404 `DEVICE_NOT_FOUND`. Revoke every session (and token family) under that device.
- [ ] Implement `DELETE /security/sessions` (global logout): revoke every session/family for the user, including current.
- [ ] For all three revocation endpoints: if the current session is among the revoked set, clear auth cookies on that same response.
- [ ] Write `SESSION_REVOKED` Security Log with `scope` metadata (`single`/`device`/`global`) for each revocation call.
- [ ] All revocation routes require auth + CSRF.
- [ ] Manual test: revoke a session belonging to another user's device/session ID → confirm 404, not 403.
- [ ] Manual test: global logout while authenticated as the caller → cookies cleared in response, subsequent request with old access token is rejected.

---

## PHASE 14 — Backend: Tasks API

- [ ] Create `app/schemas/task.py`: `TaskCreate`, `TaskUpdate` (partial, all fields optional but at least one required), `TaskRead`.
- [ ] Implement `GET /tasks`: list tasks scoped to `current_user.id`, no CSRF required.
- [ ] Implement `POST /tasks`: create task scoped to `current_user.id`, requires CSRF, write `TASK_CREATED` Audit Log in same transaction.
- [ ] Implement `PATCH /tasks/{id}`: scoped by `(id, user_id)` in the query itself; requires CSRF.
- [ ] Reject a PATCH body with no recognized field as a validation error (not a silent no-op).
- [ ] Not found/other-user's task → 404 `TASK_NOT_FOUND`.
- [ ] Write `TASK_UPDATED` Audit Log in same transaction as the update.
- [ ] Implement `DELETE /tasks/{id}`: scoped by `(id, user_id)`; requires CSRF; hard delete.
- [ ] Not found/other-user's task → 404 `TASK_NOT_FOUND`.
- [ ] Write `TASK_DELETED` Audit Log in same transaction as the delete.
- [ ] Confirm no PUT route exists for tasks anywhere.
- [ ] Manual test: cross-user task ID on GET-by-id-via-PATCH/DELETE returns 404, never 403 or 200.

**Checkpoint:** all backend endpoints from root/backend AGENTS.md now exist. Full manual pass with curl/Postman: login → create/list/patch/delete task → avatar upload → phone change → device list → revoke → global logout.

---

## PHASE 15 — Backend: Testing Pass

- [ ] Set up `tests/` with a dedicated test database and per-test transaction rollback fixture.
- [ ] Mock Redis with `fakeredis` for all OTP/rate-limit tests.
- [ ] Route avatar-upload tests to a temp directory, never the real uploads dir.
- [ ] Test: OTP attempt limit — 5 failures destroy code, return `AUTH_OTP_MAX_ATTEMPTS`.
- [ ] Test: OTP send cooldown returns `AUTH_OTP_RATE_LIMITED` on rapid resend.
- [ ] Test: refresh rotation happy path across ≥3 generations of tokens.
- [ ] Test: refresh reuse — family + session revoked, 401 `AUTH_REFRESH_TOKEN_REUSED`, cookies cleared.
- [ ] Test: concurrent refresh — two parallel requests, same token, exactly one succeeds.
- [ ] Test: cross-user access on task/session/device all return 404.
- [ ] Test: CSRF missing/mismatched header on every protected verb (POST/PUT/PATCH/DELETE routes that require it).
- [ ] Test: global logout revokes current session and clears cookies.
- [ ] Test: every custom error code returns expected HTTP status + JSON envelope shape.
- [ ] Test: avatar upload rejects oversized files and non-image content regardless of claimed `Content-Type`.
- [ ] Test: phone-change token can't be reused for a different phone number than the one it was bound to.
- [ ] Run full backend test suite green before moving to frontend integration.

---

## PHASE 16 — Frontend: Project Foundation

- [ ] Install/configure TailwindCSS if not already set up by `bunx create-next-app`.
- [ ] Install and initialize `shadcn/ui`; add base components: `Button`, `Input`, `Dialog`, `AlertDialog`, `Card`, `Checkbox`, `Form`, `Sonner`, `Accordion`, `Avatar`, `Badge`, `Skeleton`, `Separator`, `DropdownMenu`, `Tabs`.
- [ ] Install `axios`, `@reduxjs/toolkit`, `react-redux`, `react-hook-form`, `zod`, `@hookform/resolvers`, `next-themes`, `next-intl`, `lucide-react`.
- [ ] Create `frontend/.env.example` and local `.env.local` with `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_API_ORIGIN`.
- [ ] Configure `next.config.ts` `images.remotePatterns` to allow the backend's `/uploads` origin, driven by env config.
- [ ] Scaffold empty route files: `app/login/page.tsx`, `app/tasks/page.tsx`, `app/profile/page.tsx`, `app/settings/page.tsx`, `app/security/page.tsx`.
- [ ] Confirm `bun run dev` boots and all placeholder routes render.

---

## PHASE 17 — Frontend: i18n & Theme Wiring (structure only, content later)

- [ ] Create `messages/en.json` and `messages/fa.json` with a minimal matching key set (e.g. `common.appName`).
- [ ] Configure `next-intl` provider/config for the App Router (no locale-prefixed routing per §37).
- [ ] Set `<html lang>` and `<html dir>` dynamically based on active locale in root layout.
- [ ] Configure `next-themes` `ThemeProvider` with the standard hydration-flash suppression setup.
- [ ] Build `components/providers/ThemeProvider.tsx` and `components/providers/IntlProvider.tsx` wrapping children.
- [ ] Build `components/layout/ThemeToggle.tsx` (Sun/Moon icon toggle, no logic yet — wire to Redux in Phase 21).
- [ ] Build `components/layout/LocaleSwitcher.tsx` skeleton.
- [ ] Manual test: toggling theme/locale changes rendering, RTL flips layout when Persian is selected.

---

## PHASE 18 — Frontend: Core `lib/` Utilities (no Redux yet)

### 18.1 Device ID
- [ ] Implement `lib/device-id.ts`: lazily read/create a UUIDv4 in `localStorage['device_id']`, guarded for SSR (only runs in browser).

### 18.2 Local preferences
- [ ] Implement `lib/local-prefs.ts`: get/set/remove for `theme` and `locale` only, SSR-guarded. No other keys allowed through this module.

### 18.3 CSRF reader
- [ ] Implement `lib/csrf.ts`: read `csrf_token` value from `document.cookie` fresh on each call (never cached).

### 18.4 Types
- [ ] Implement `lib/types.ts` (or generate from OpenAPI): `Task`, `DeviceWithSessions`, `Session`, `User`/profile shape, request/response types per endpoint.
- [ ] Decide and document the OpenAPI-sync approach (manual for now vs. generated types) — at minimum keep field names identical to backend Pydantic schemas.

### 18.5 API error normalization
- [ ] Implement `lib/api-error.ts`: `ApiError` class/type with `status`, `code`, `message`, `details`, `requestId`.
- [ ] Implement a normalizer function turning any Axios error (including network failures / non-JSON responses) into `ApiError`, with a synthetic code for the network-failure case.

### 18.6 Error-code → message-key map
- [ ] Implement `lib/error-messages.ts` mapping each backend error code to a `next-intl` key, with a generic fallback key for unrecognized codes.

### 18.7 Image helper
- [ ] Implement `lib/image.ts`: client-side downscale/compress of an image file before upload (canvas-based), plus a type/size pre-check helper mirroring backend limits (jpeg/png/webp, 5 MB).

---

## PHASE 19 — Frontend: Centralized Axios API Client

- [ ] Create `lib/api-client.ts`: single Axios instance, `baseURL` from `NEXT_PUBLIC_API_URL`, `withCredentials: true`.
- [ ] Request interceptor: attach `X-Device-Id` on every request from `lib/device-id.ts`.
- [ ] Request interceptor: attach `X-CSRF-Token` (read fresh from cookie) on `POST`/`PUT`/`PATCH`/`DELETE` only.
- [ ] Request interceptor: detect `FormData` body and delete any `Content-Type` header rather than setting one, so the browser sets the multipart boundary.
- [ ] Response interceptor: on success, pass through.
- [ ] Response interceptor: on error, normalize to `ApiError` via `lib/api-error.ts` before rethrowing, for all non-401 cases.
- [ ] Implement the 401 handling flow:
  - [ ] If `error.code === 'AUTH_SESSION_REVOKED'`, skip refresh entirely — reject immediately (caller handles cleanup+redirect).
  - [ ] Otherwise, if this request hasn't already been retried, attempt refresh via `POST /auth/refresh`.
  - [ ] Use a single shared in-flight refresh promise so concurrent 401s await one refresh call, not one each.
  - [ ] On refresh success: retry the original request exactly once (mark it as retried) and resolve.
  - [ ] On refresh failure: reject all pending requests consistently; do not attempt refresh again.
  - [ ] Ensure the refresh request itself is never intercepted into triggering another refresh (loop guard).
- [ ] Confirm the API client contains no business logic, no toast calls, no Redux imports, no navigation beyond the auth-recovery mechanism.
- [ ] Create thin API modules `lib/api/auth.ts`, `lib/api/profile.ts`, `lib/api/security.ts`, `lib/api/tasks.ts` — each a set of typed functions calling `apiClient`, no independent Axios instances.

**Checkpoint:** write a small manual harness page or Vitest test hitting a protected backend route with an expired access token, confirming exactly one refresh + one retry.

---

## PHASE 20 — Frontend: Redux Store Skeleton

- [ ] Create `store/store.ts` configuring the Redux store with all slice reducers (added incrementally in later phases).
- [ ] Create `store/hooks.ts` with typed `useAppDispatch`/`useAppSelector`.
- [ ] Create `components/providers/StoreProvider.tsx` wrapping the app in a `Provider`.
- [ ] Confirm state serializability middleware isn't disabled — Redux DevTools should not show non-serializable warnings once slices are added.

---

## PHASE 21 — Frontend: `authSlice` + Login Flow

### 21.1 Slice
- [ ] Create `store/slices/authSlice.ts` with state shape from frontend §19: `isAuthenticated`, `phoneNumber`, `currentSessionId`, `status`, `error`.
- [ ] Implement thunk `sendOtp(phoneNumber)` calling `lib/api/auth.ts`.
- [ ] Implement thunk `verifyOtp({phoneNumber, code})`.
- [ ] Implement thunk `logout()`.
- [ ] Implement thunk `checkAuth()` using `GET /tasks` as the lightweight authenticated probe (200 = authenticated, 401 = not).
- [ ] Ensure any error stored in state is the plain serializable `ApiError` shape, not a class instance.

### 21.2 Shared logout/cleanup routine
- [ ] Implement a single shared cleanup function (e.g. `lib/auth-cleanup.ts`) that: resets `authSlice`, `tasksSlice`, `profileSlice`, `securitySlice`; removes `theme`+`locale` from localStorage; preserves `device_id`; redirects to `/login`.
- [ ] Call this routine from: explicit logout success, refresh-failure path in the API client, `AUTH_SESSION_REVOKED` handling, current-session revocation, and global logout success. No duplicated inline logic anywhere else.

### 21.3 `AppInit`
- [ ] Build `components/providers/AppInit.tsx` (client component) mounted from root layout: on mount, call `GET /auth/csrf-token` once.
- [ ] Confirm this logic does not assume the user is authenticated and is a separate concern from `checkAuth()`.

### 21.4 Login page & components
- [ ] Build `components/auth/PhoneForm.tsx`: RHF + Zod phone validation, dispatches `sendOtp`, shows resend cooldown countdown.
- [ ] Build `components/auth/OtpForm.tsx`: RHF + Zod 4-digit code validation, dispatches `verifyOtp`.
- [ ] On `AUTH_OTP_MAX_ATTEMPTS`: clear OTP input, return to phone step, show explanatory message.
- [ ] On `AUTH_INVALID_OTP`/`AUTH_OTP_EXPIRED`: inline field error via `error-messages.ts` lookup.
- [ ] On `AUTH_OTP_RATE_LIMITED`: disable resend button, show cooldown.
- [ ] Surface `otp_debug` only when a development flag is set; never rely on it for production UX.
- [ ] Build `app/login/page.tsx` orchestrating phone step → OTP step → redirect to `/tasks` on success.
- [ ] Confirm no client-side attempt counting is used as enforcement — only for display/UX.

---

## PHASE 22 — Frontend: Route Protection

- [ ] Decide client-check vs. middleware approach (per §25) and implement consistently.
- [ ] If middleware: only perform a cookie-presence hint check, never JWT verification (no secret on frontend).
- [ ] Protect `/tasks`, `/profile`, `/settings`, `/security` — unauthenticated access redirects to `/login`.
- [ ] Confirm backend authorization remains authoritative even if the frontend check is bypassed somehow (defense in depth, not a real boundary).

---

## PHASE 23 — Frontend: `tasksSlice` + `/tasks` Page

### 23.1 Slice
- [ ] Create `store/slices/tasksSlice.ts`: `items`, `status`, `error`.
- [ ] Implement thunks: `fetchTasks`, `createTask`, `updateTask`, `deleteTask`, all via `lib/api/tasks.ts`.
- [ ] Implement optimistic update for toggling `is_done`: update UI immediately, roll back on server error.
- [ ] Implement optimistic delete: remove immediately, roll back + surface error on failure.
- [ ] Task creation is **not** optimistic — wait for server response before adding to list.

### 23.2 Components
- [ ] Build `components/tasks/TaskForm.tsx`: RHF + Zod title validation, dispatches `createTask`.
- [ ] Build `components/tasks/TaskItem.tsx`: checkbox (toggle `is_done`), title, strikethrough style when completed, edit/delete actions.
- [ ] Build `components/tasks/TaskEditDialog.tsx`: Shadcn `Dialog` + RHF/Zod for title editing, dispatches `updateTask` with a partial PATCH body.
- [ ] Delete action uses a Shadcn `AlertDialog` confirmation before dispatching `deleteTask`.
- [ ] Build `components/tasks/TaskList.tsx`: renders items, uses `Skeleton` during initial `loading` state, shows empty/error states distinctly.
- [ ] Build `app/tasks/page.tsx`: mounts add-task form, task list, and nav links to profile/settings/security.
- [ ] Confirm every async state (`idle`/`loading`/`success`/`error`) has a distinct, non-stuck UI representation.

---

## PHASE 24 — Frontend: `settingsSlice` + Theme/Locale UI

- [ ] Create `store/slices/settingsSlice.ts`: `theme`, `locale`, mirroring `lib/local-prefs.ts` values on load.
- [ ] Wire `ThemeToggle.tsx` to `next-themes` `setTheme` and update `settingsSlice`/`local-prefs` together (next-themes remains authority, slice mirrors it — no fighting).
- [ ] Wire `LocaleSwitcher.tsx` to update locale, persist via `local-prefs.ts`, and reflect in `next-intl` routing/rendering.
- [ ] Build `app/settings/page.tsx` hosting both toggles.
- [ ] Confirm theme/locale are cleared (reset to system/default) via the shared logout cleanup routine, never persisted server-side.

---

## PHASE 25 — Frontend: `profileSlice` + Avatar Upload

- [ ] Create `store/slices/profileSlice.ts`: `avatarUrl`, `phoneChangeStep`, `status`, `error`.
- [ ] Implement thunk for avatar upload calling `lib/api/profile.ts::uploadAvatar` with a `FormData` body.
- [ ] Build `components/profile/AvatarUploader.tsx`: Shadcn `Avatar`, client-side type/size pre-check + downscale via `lib/image.ts`, local preview before upload, replace with server-returned path on success.
- [ ] Handle `PROFILE_AVATAR_TOO_LARGE`/`PROFILE_AVATAR_INVALID_TYPE` as inline errors on the uploader (never assume client validation alone is sufficient).
- [ ] Build `app/profile/page.tsx` hosting the avatar uploader (phone-change wizard added next phase).

---

## PHASE 26 — Frontend: Phone-Change Wizard

- [ ] Build `components/profile/PhoneChangeWizard.tsx` as a multi-step form: request-current → verify-current → enter-new-number/request-new → verify-new.
- [ ] Each step is its own RHF+Zod form.
- [ ] Hold `phone_change_token` only in wizard-local component state (or a non-persisted slice field) — wiped on unmount/completion, never in `localStorage`.
- [ ] On `PROFILE_PHONE_CHANGE_TOKEN_INVALID`, reset the wizard to step 1 with an explanatory message.
- [ ] Leaving the page abandons the flow cleanly (no lingering token references).
- [ ] Mount the wizard on `app/profile/page.tsx` alongside the avatar uploader.
- [ ] Manual test: full wizard happy path against the live backend, plus an expired-token scenario.

---

## PHASE 27 — Frontend: `securitySlice` + `/security` Page

### 27.1 Slice
- [ ] Create `store/slices/securitySlice.ts`: `devices`, `status`, `error`, `revoking`.
- [ ] Implement thunks: `fetchDevices`, `revokeSession`, `revokeDeviceSessions`, `revokeAllSessions`, via `lib/api/security.ts`.
- [ ] Confirm none of these are optimistic — always wait for server, then refetch the device list.

### 27.2 Components
- [ ] Build `components/security/DeviceCard.tsx` (Shadcn `Card`/`Accordion`): device metadata + nested sessions.
- [ ] Build `components/security/SessionRow.tsx`: creation time, last activity, expiry, `Badge` for `is_current`, per-session Revoke button behind `AlertDialog`.
- [ ] Build `components/security/DeviceList.tsx`: renders all devices, `Skeleton` during initial load, per-device "Revoke all sessions" behind `AlertDialog`.
- [ ] Build `components/security/RevokeAllDialog.tsx`: clearly destructive global-logout confirmation stating all devices (including this one) will be logged out.
- [ ] On global logout success, or on revoking the session currently in use (directly or via its device), run the shared logout cleanup routine instead of just refetching.
- [ ] Build `app/security/page.tsx` assembling the above.
- [ ] Manual test: open two browser sessions (or a session + curl-simulated second device), revoke the non-current one, confirm the current session is unaffected and the list updates.
- [ ] Manual test: revoke the current session from the list — confirm the app logs the user out and redirects, not just an error toast.

---

## PHASE 28 — Frontend: i18n Content Completion

- [ ] Fill in `messages/en.json` and `messages/fa.json` with every user-visible string across all pages/components built so far.
- [ ] Cross-check key parity between `en.json` and `fa.json` (script or manual diff) — no key present in one and missing in the other.
- [ ] Confirm every Zod schema uses message **keys**, not literal English text, resolved at render/validation time.
- [ ] Confirm every `error-messages.ts` mapping resolves to a real key in both locale files.
- [ ] Confirm directional icons flip correctly in RTL and physical `left-*`/`right-*` Tailwind utilities have been replaced with logical (`ms-*`/`me-*`/`ps-*`/`pe-*`/`text-start`/`text-end`).
- [ ] Spot-check Persian digit/date rendering.

---

## PHASE 29 — Frontend: Responsive Pass

- [ ] Review `/login`, `/tasks`, `/profile`, `/settings`, `/security` at mobile width first, then tablet/desktop breakpoints.
- [ ] Confirm task list and device list are comfortable and usable on a phone-sized viewport.
- [ ] Confirm dialogs/wizards don't overflow small screens.

---

## PHASE 30 — Frontend: Testing Pass

- [ ] Set up Vitest + React Testing Library + MSW (mock the network layer, not Axios directly).
- [ ] Test: `X-Device-Id` present on every request; `X-CSRF-Token` present only on mutating verbs.
- [ ] Test: `FormData` requests never carry a hand-set `Content-Type`.
- [ ] Test: a 401 triggers exactly one refresh and one retry of the original request.
- [ ] Test: three concurrent 401s trigger exactly one refresh call.
- [ ] Test: refresh failure runs the cleanup routine once and redirects to `/login`.
- [ ] Test: `AUTH_SESSION_REVOKED` skips refresh entirely.
- [ ] Test: logout clears `theme`/`locale` but leaves `device_id` intact.
- [ ] Test: optimistic toggle and optimistic delete roll back correctly on simulated server error.
- [ ] Test: `en.json`/`fa.json` key-set equality (can be a small script run as part of the test suite).
- [ ] Test: slice thunks go through `idle → loading → succeeded/error` correctly for tasks, auth, security, profile.
- [ ] Test: form validation errors surface correctly for phone/OTP/task/avatar/phone-change forms.
- [ ] Run full frontend test suite green.

---

## PHASE 31 — Full Integration & Definition-of-Done Review

- [ ] End-to-end manual walkthrough with real backend + frontend running together: login → create/edit/complete/delete tasks → change avatar → change phone number → view devices/sessions → revoke a non-current session → global logout.
- [ ] Confirm CORS works correctly between the two dev origins (no preflight failures on `X-CSRF-Token`/`X-Device-Id`).
- [ ] Confirm avatar images render via `next/image` given the cross-origin `/uploads` mount.
- [ ] Walk through root `AGENTS.md` §19 Definition of Done, item by item, for every implemented feature.
- [ ] Confirm no error code in root §12 is unused/unhandled on either side, and no undocumented error code was invented.
- [ ] Confirm Security Log and Audit Log tables are actually populated correctly during the full walkthrough (spot-check rows in psql).
- [ ] Confirm nothing sensitive (tokens, OTPs, secrets) appears in any log table, browser storage, or Redux DevTools state.
- [ ] Final read-through of both `AGENTS.md` "Out of Scope" sections to confirm nothing extra crept in (no extra product features, no extra infra, no PUT-for-tasks, no soft delete, etc.).

---

### Notes on using this checklist
- Treat each **Phase** as a PR-sized (or smaller) unit of work; sub-numbered items within a phase are the individual commits/tasks.
- Don't start a phase's manual/automated "Checkpoint" until every checkbox above it in that phase is done.
- Phases 1–15 (backend) can mostly be finished before phases 16–30 (frontend) begin, since the frontend's API modules and types depend on a stable backend contract — but Phase 16–20 (frontend scaffolding, no live calls yet) can be done in parallel if you want to save time.