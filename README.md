# Todo App - Phased Implementation Roadmap

This document sequences the work defined in `AGENTS.md`, `backend/AGENTS.md`, and `frontend/AGENTS.md`.

**Rules for the AI agent using this roadmap:**

1. Phases are executed **in order**. Do not start a phase before the previous phase's Exit Gate passes.
2. Inside a phase, complete the checklist top to bottom. Backend items precede the frontend items that consume them.
3. A phase is finished only when **every** Exit Gate line is true. Never mark a phase done with failing tests.
4. If a checklist item contradicts an `AGENTS.md` rule, STOP and report the contradiction (root directive 4).
5. Apply the Anti-Loop protocol per item: at most **two** automatic fix attempts, then stop and hand back to the human.
6. Every phase that touches the UI ships its strings in `en.json` **and** `fa.json` in the same phase. Localization is never deferred to the end.

Legend: `[BE]` backend Â· `[FE]` frontend Â· `[T]` test Â· `[DOC]` docs/config

---

## Phase Map

```text
Phase 0  Foundations & Scaffolding
Phase 1  Cross-Cutting Contracts (errors, request id, config, cookies)
Phase 2  OTP Login (backend)
Phase 3  Refresh Rotation, Reuse Detection, Concurrency (backend)
Phase 4  Frontend Transport Layer (apiClient, CSRF, device id, refresh interceptor)
Phase 5  Login UI & Auth State
Phase 6  Tasks End-to-End
Phase 7  Profile: Avatar
Phase 8  Profile: Phone Number Change
Phase 9  Session & Device Management
Phase 10 Theme, i18n & RTL
Phase 11 Hardening, Test Sweep & Definition-of-Done Audit
```

Dependency notes: Phase 4 needs 1-3. Phase 9 needs 3 (revocation semantics) and 4 (`is_current` flow). Phase 10 touches every screen, so it lands after the screens exist, but each earlier phase already registers its message keys.

---

## Phase 0 - Foundations & Scaffolding

**Goal:** both applications boot, talk to each other, and nothing is hardcoded.

### Checklist

* [ ] `[BE]` Create `backend/` project with `pyproject.toml`, FastAPI, Uvicorn, async SQLAlchemy, asyncpg, Alembic, `redis.asyncio`, Pydantic v2, `argon2-cffi`, `python-multipart`, Pillow.
* [ ] `[BE]` `core/config.py`: Pydantic Settings reading every variable listed in `backend/AGENTS.md` Â§34. No literal defaults for secrets.
* [ ] `[BE]` `db/session.py` async engine + session dependency; `db/base.py` declarative base.
* [ ] `[BE]` `core/redis_client.py` async Redis client with lifespan management.
* [ ] `[BE]` `main.py` with app factory, lifespan startup/shutdown, `/health` endpoint.
* [ ] `[BE]` CORS configured from `FRONTEND_ORIGIN`, `allow_credentials=True`, `allow_headers` including `X-CSRF-Token` and `X-Device-Id`. Never `["*"]`.
* [ ] `[BE]` Alembic initialized and wired to the async engine.
* [ ] `[BE]` `uploads/` directory created and git-ignored (keep it with `.gitkeep`).
* [ ] `[FE]` `create-next-app` with TypeScript + App Router + Tailwind.
* [ ] `[FE]` `shadcn/ui` init; add `Button`, `Input`, `Card`, `Form`, `Sonner`.
* [ ] `[FE]` Redux store + `StoreProvider` + typed `useAppDispatch` / `useAppSelector`.
* [ ] `[FE]` `next.config.ts` with `images.remotePatterns` for the backend origin, driven by env.
* [ ] `[DOC]` `backend/.env.example` and `frontend/.env.example` committed, no real secrets.
* [ ] `[T]` `pytest` + `pytest-asyncio` + `httpx` configured; one passing smoke test on `/health`.
* [ ] `[T]` `Vitest` + React Testing Library + MSW configured; one passing smoke test.

### Exit Gate

* Backend serves `/health` and connects to PostgreSQL and Redis.
* Frontend builds and renders a page.
* Both test runners execute successfully.
* No secret or URL is hardcoded anywhere.

---

## Phase 1 - Cross-Cutting Contracts

**Goal:** the error envelope, request IDs, cookie helpers, and logging tables exist before any feature uses them. Building these later means retrofitting every endpoint.

### Checklist

* [ ] `[BE]` `core/errors.py`: single `AppError` type carrying `code`, HTTP status, message, optional details.
* [ ] `[BE]` Error-code enum covering every code in root `AGENTS.md` Â§12.
* [ ] `[BE]` Exception handlers for `AppError`, `HTTPException`, `RequestValidationError`, and unhandled exceptions. All four emit the identical envelope.
* [ ] `[BE]` Unhandled exceptions return `INTERNAL_ERROR` with no stack trace, message, or internal detail leaked.
* [ ] `[BE]` Request-ID middleware: generate when absent, attach to request state, include in every error response.
* [ ] `[BE]` `core/cookies.py`: centralized set/clear helpers for `access_token`, `refresh_token`, `csrf_token`. Clearing reuses the exact attributes used when setting.
* [ ] `[BE]` Models + initial Alembic migration for `users`, `devices`, `sessions`, `refresh_tokens`, `tasks`, `security_logs`, `audit_logs`, with FKs, cascades, and justified indexes.
* [ ] `[BE]` `sessions` and `devices` scoped-lookup helpers (always by `(id, user_id)`).
* [ ] `[BE]` Security-log writer and audit-log writer services with a hard rule: no raw credentials in payloads.
* [ ] `[T]` Validation error, 404, and forced internal error all return the exact envelope shape with a `request_id`.
* [ ] `[T]` Migration applies cleanly to an empty database and downgrades without error.

### Exit Gate

* No endpoint can return an error outside the envelope.
* `alembic upgrade head` builds the full schema from scratch.
* Log writers are covered by tests and reject sensitive keys.

---

## Phase 2 - OTP Login (Backend)

**Goal:** a user can obtain authentication cookies from a phone number and a code.

### Checklist

* [ ] `[BE]` `dependencies/device.py`: parse and validate `X-Device-Id`; `DEVICE_ID_MISSING` / `DEVICE_ID_INVALID` â†’ 400.
* [ ] `[BE]` Phone normalization utility; the same input can never create two users.
* [ ] `[BE]` `otp_service`: generate 4-digit code with `secrets`, store `otp:{phone}` with TTL from config.
* [ ] `[BE]` Send cooldown via `otp_cooldown:{phone}` â†’ 429 `AUTH_OTP_RATE_LIMITED`.
* [ ] `[BE]` Attempt counter via `otp_attempts:{phone}`, atomic `INCR`, same TTL as the code.
* [ ] `[BE]` On the 5th failed attempt: delete the code, return 429 `AUTH_OTP_MAX_ATTEMPTS`, log `OTP_MAX_ATTEMPTS_REACHED`.
* [ ] `[BE]` `POST /auth/send-otp`: console print + `otp_debug` in the response, **both gated on `ENV != production`** and clearly commented as testing-only.
* [ ] `[BE]` `POST /auth/verify-otp`: constant-time compare, find-or-create user, find-or-create device scoped by `(device_id, user_id)`, create session, token family, first refresh token, Argon2-hash the secret.
* [ ] `[BE]` Access Token JWT with `sub`, `sid`, `exp`. `sid` is mandatory.
* [ ] `[BE]` Set `access_token`, `refresh_token`, and a fresh `csrf_token` cookie. Neither token appears in the JSON body.
* [ ] `[BE]` `GET /auth/csrf-token`, unauthenticated, sets the readable CSRF cookie.
* [ ] `[BE]` `dependencies/auth.py`: current-user dependency verifying JWT, loading user, loading session, returning user + `session_id`. Revoked/expired session â†’ 401 `AUTH_SESSION_REVOKED`.
* [ ] `[BE]` `dependencies/csrf.py`: constant-time header/cookie comparison, `CSRF_TOKEN_MISSING` / `CSRF_TOKEN_INVALID` â†’ 403, `CSRF_FAILURE` logged.
* [ ] `[BE]` `POST /auth/logout`: idempotent, revokes session + token family, clears all three cookies, logs `LOGOUT`, and reveals nothing to unauthenticated callers.
* [ ] `[BE]` Security logs for `OTP_REQUESTED`, `OTP_VERIFICATION_FAILED`, `LOGIN_SUCCESS`, `LOGIN_FAILED`.
* [ ] `[T]` Happy path: send â†’ verify â†’ cookies set, tokens absent from the body.
* [ ] `[T]` Wrong code 5 times: 5th returns `AUTH_OTP_MAX_ATTEMPTS` and the code is gone from Redis.
* [ ] `[T]` Resend inside the cooldown returns 429.
* [ ] `[T]` Expired/absent code returns `AUTH_OTP_EXPIRED`.
* [ ] `[T]` Missing and malformed `X-Device-Id` both return 400 with the right codes.
* [ ] `[T]` No security log row anywhere contains the OTP value.
* [ ] `[T]` Logout twice in a row both succeed.

### Exit Gate

* Login works end-to-end through the API with cookies only.
* The attempt limit is enforced in Redis, not in Python-only logic.
* `sid` is present in every issued Access Token.

---

## Phase 3 - Refresh Rotation, Reuse Detection, Concurrency

**Goal:** the security centerpiece. Do not move on until the concurrency test is green.

### Checklist

* [ ] `[BE]` Token format `token_id.secret`; only the secret is Argon2-hashed; the raw value never persists.
* [ ] `[BE]` `POST /auth/refresh` (CSRF-protected) implementing the full 13-step sequence in `backend/AGENTS.md` Â§18.
* [ ] `[BE]` Atomic consumption: conditional `UPDATE ... WHERE used_at IS NULL AND revoked_at IS NULL` with an affected-row check, or `SELECT ... FOR UPDATE`. Application-level checks alone are forbidden.
* [ ] `[BE]` Replacement token in the same session and token family; `replaced_by_id` set on the consumed token.
* [ ] `[BE]` Consumption + replacement creation in one transaction.
* [ ] `[BE]` Rotate the `csrf_token` cookie alongside the auth cookies.
* [ ] `[BE]` Update `sessions.last_used_at` and `devices.last_seen_at`.
* [ ] `[BE]` Reuse detection: used/revoked/replaced token â†’ log `REFRESH_TOKEN_REUSED`, revoke family, revoke session, 401 `AUTH_REFRESH_TOKEN_REUSED`, clear cookies.
* [ ] `[BE]` Revoked session on refresh â†’ 401 `AUTH_SESSION_REVOKED`, distinct from ordinary expiry.
* [ ] `[BE]` Any invalid refresh clears cookies and issues nothing.
* [ ] `[BE]` Session-revocation helper that also revokes the token family. Every future revocation path uses it.
* [ ] `[T]` Rotate 4 generations successfully; the session ID never changes.
* [ ] `[T]` Replay RT1 after rotating to RT2: family and session revoked, cookies cleared, correct code.
* [ ] `[T]` **Two parallel refreshes with the same token: exactly one succeeds.**
* [ ] `[T]` Expired refresh token â†’ 401, no new token.
* [ ] `[T]` Refresh without the CSRF header â†’ 403.
* [ ] `[T]` After a revoked session, an unexpired Access Token no longer grants access.

### Exit Gate

* All six tests above pass, including concurrency.
* No code path issues a token after reuse detection.
* Revoking a session always kills its refresh family.

---

## Phase 4 - Frontend Transport Layer

**Goal:** one API client that handles cookies, CSRF, device id, and refresh. Every later phase depends on it, so it gets built and tested in isolation first.

### Checklist

* [ ] `[FE]` `lib/device-id.ts`: lazily generate a UUIDv4, persist under `device_id`, SSR-guarded, **never cleared on logout**.
* [ ] `[FE]` `lib/local-prefs.ts`: the only module touching `localStorage` for `theme` and `locale`, SSR-guarded.
* [ ] `[FE]` `lib/csrf.ts`: read `csrf_token` from `document.cookie`. Reading auth cookies is never implemented.
* [ ] `[FE]` `lib/api-error.ts`: `ApiError` normalization with `status`, `code`, `message`, `details`, `requestId`; network and malformed responses get synthetic codes.
* [ ] `[FE]` `lib/api-client.ts` with `withCredentials: true` and a single base URL from env.
* [ ] `[FE]` Request interceptor: attach `X-Device-Id` always; attach `X-CSRF-Token` read fresh from the cookie on POST/PUT/PATCH/DELETE.
* [ ] `[FE]` Request interceptor: for `FormData` payloads, **delete** `Content-Type` so the browser sets the boundary.
* [ ] `[FE]` Response interceptor: normalize every failure into `ApiError`.
* [ ] `[FE]` Refresh interceptor with a **single shared in-flight promise**; concurrent 401s await it.
* [ ] `[FE]` One refresh cycle per request, tracked by a private config flag; `/auth/refresh` itself never triggers a refresh.
* [ ] `[FE]` `AUTH_SESSION_REVOKED` skips refresh entirely and goes straight to cleanup.
* [ ] `[FE]` `lib/error-messages.ts`: `error.code` â†’ i18n message key, with a generic fallback. Backend `message` is never rendered.
* [ ] `[FE]` Shared logout-cleanup routine per `frontend/AGENTS.md` Â§36: reset slices, clear `theme` + `locale`, keep `device_id`, redirect to `/login`. Implemented once.
* [ ] `[FE]` `AppInit` client component calling `GET /auth/csrf-token` once on startup.
* [ ] `[T]` `X-Device-Id` on every request; `X-CSRF-Token` on mutations only.
* [ ] `[T]` A `FormData` request carries no manually set `Content-Type`.
* [ ] `[T]` A 401 produces exactly one refresh and one retry.
* [ ] `[T]` **Three concurrent 401s produce exactly one refresh call.**
* [ ] `[T]` Refresh failure runs cleanup once and redirects.
* [ ] `[T]` `AUTH_SESSION_REVOKED` never calls `/auth/refresh`.
* [ ] `[T]` Cleanup clears `theme` and `locale` and preserves `device_id`.

### Exit Gate

* All seven MSW tests pass.
* No component or thunk sets auth/device/CSRF headers by hand.
* Cleanup exists in exactly one place.

---

## Phase 5 - Login UI & Auth State

**Goal:** a human can log in through the browser.

### Checklist

* [ ] `[FE]` `lib/api/auth.ts`: `sendOtp`, `verifyOtp`, `logout`.
* [ ] `[FE]` `authSlice` with `isAuthenticated`, `phoneNumber`, `currentSessionId`, `status`, serializable `error`; thunks `sendOtp`, `verifyOtp`, `logout`, `checkAuth`.
* [ ] `[FE]` `checkAuth` uses `GET /tasks` (200 = authenticated, 401 = not). No `/auth/me` endpoint is added.
* [ ] `[FE]` `PhoneForm` with RHF + Zod, message **keys** not literals.
* [ ] `[FE]` `OtpForm` with a 4-digit input, RHF + Zod.
* [ ] `[FE]` Resend cooldown countdown; resend disabled while active.
* [ ] `[FE]` `AUTH_OTP_MAX_ATTEMPTS` clears the input and returns the user to the phone step with an explanation.
* [ ] `[FE]` `AUTH_INVALID_OTP` / `AUTH_OTP_EXPIRED` render inline on the OTP field.
* [ ] `[FE]` `otp_debug` surfaced only behind a development check.
* [ ] `[FE]` Successful verification routes to `/tasks`.
* [ ] `[FE]` Route protection for `/tasks`, `/profile`, `/settings`, `/security`. If middleware is used it only checks cookie presence and never verifies the JWT.
* [ ] `[FE]` Register all Phase-5 keys in `en.json` and `fa.json`.
* [ ] `[T]` Phone and OTP validation errors render.
* [ ] `[T]` `authSlice` transitions `idle â†’ loading â†’ succeeded/error`.
* [ ] `[T]` `AUTH_OTP_MAX_ATTEMPTS` resets the form to the phone step.
* [ ] `[T]` Visiting a protected route while unauthenticated redirects to `/login`.

### Exit Gate

* Full browser login works against the real backend.
* No token is present in Redux, `localStorage`, or any log.
* Both message files carry every new key.

---

## Phase 6 - Tasks End-to-End

**Goal:** the actual product, fully user-scoped.

### Checklist

* [ ] `[BE]` Task Pydantic schemas; a PATCH body with no recognized field is a validation error, not a silent success.
* [ ] `[BE]` `GET /tasks`, `POST /tasks`, `PATCH /tasks/{id}`, `DELETE /tasks/{id}`. **No PUT.**
* [ ] `[BE]` Every single-task query filters `id` **and** `user_id` in the SQL itself. Never fetch-then-authorize.
* [ ] `[BE]` Non-owned or missing task â†’ 404 `TASK_NOT_FOUND`.
* [ ] `[BE]` Hard delete only; no `deleted_at` anywhere.
* [ ] `[BE]` Audit logs `TASK_CREATED`, `TASK_UPDATED`, `TASK_DELETED`, committed in the same transaction as the mutation.
* [ ] `[BE]` Title validation â†’ `TASK_TITLE_INVALID`.
* [ ] `[FE]` `lib/api/tasks.ts` with typed returns; no `any`.
* [ ] `[FE]` `tasksSlice` with `fetchTasks`, `createTask`, `updateTask`, `deleteTask`.
* [ ] `[FE]` Optimistic `is_done` toggle and optimistic delete, both rolling back on failure.
* [ ] `[FE]` Create is not optimistic.
* [ ] `[FE]` `TaskForm`, `TaskList`, `TaskItem`, `TaskEditDialog`; completed tasks visually struck through.
* [ ] `[FE]` Delete behind a Shadcn `AlertDialog`.
* [ ] `[FE]` `TASK_NOT_FOUND` removes the task from local state.
* [ ] `[FE]` `Skeleton` on first load; no permanent loading state after failure.
* [ ] `[FE]` Logout action wired to the shared cleanup routine.
* [ ] `[FE]` Phase-6 keys in both message files.
* [ ] `[T]` `[BE]` User B gets 404 on every one of User A's task endpoints.
* [ ] `[T]` `[BE]` Each mutation writes exactly one audit row; a failed mutation writes none.
* [ ] `[T]` `[BE]` Every task mutation without the CSRF header â†’ 403.
* [ ] `[T]` `[FE]` Optimistic toggle and delete both roll back on server error.

### Exit Gate

* Full CRUD works in the browser.
* Cross-user access returns 404, never 403.
* Audit rows exist for all three task actions.

---

## Phase 7 - Profile: Avatar

### Checklist

* [ ] `[BE]` `POST /profile/avatar` (auth + CSRF), `multipart/form-data`.
* [ ] `[BE]` Reject by real content: decode the header with Pillow. Client `Content-Type` and file extension are never trusted.
* [ ] `[BE]` Allowed `image/jpeg`, `image/png`, `image/webp`; otherwise 400 `PROFILE_AVATAR_INVALID_TYPE`.
* [ ] `[BE]` Enforce `AVATAR_MAX_BYTES` (5 MB) â†’ 413 `PROFILE_AVATAR_TOO_LARGE`. Enforce while streaming; do not buffer an unbounded body.
* [ ] `[BE]` Server-generated filename `{user_id}/{uuid4}.{ext}`. The client filename is never used or interpolated into a path.
* [ ] `[BE]` Store the relative path in `users.avatar_path`; replacing an avatar deterministically removes the old file.
* [ ] `[BE]` Static mount for uploads from `UPLOADS_DIR`.
* [ ] `[BE]` Audit log `AVATAR_UPDATED`.
* [ ] `[FE]` `lib/image.ts`: browser downscale/compress before upload.
* [ ] `[FE]` `AvatarUploader` with client-side type + 5 MB check, local preview, server path on success.
* [ ] `[FE]` `profileSlice` avatar state; `File`/`FormData` never enter Redux.
* [ ] `[FE]` `/profile` page with Shadcn `Avatar`.
* [ ] `[FE]` `next/image` renders the backend-served avatar (confirms `remotePatterns`).
* [ ] `[FE]` Phase-7 keys in both message files.
* [ ] `[T]` `[BE]` A `.txt` renamed to `.jpg` is rejected.
* [ ] `[T]` `[BE]` An oversized upload returns 413.
* [ ] `[T]` `[BE]` A path-traversal filename cannot escape the uploads directory.
* [ ] `[T]` `[BE]` Upload without CSRF â†’ 403.
* [ ] `[T]` `[FE]` Oversized and wrong-type files show inline errors before any request fires.

### Exit Gate

* A phone-camera photo uploads successfully and renders.
* Content-based validation is proven by test, not by extension checking.
* Tests write to a temp directory, never the real uploads dir.

---

## Phase 8 - Profile: Phone Number Change

### Checklist

* [ ] `[BE]` `POST /profile/phone/request-current` (auth + CSRF), reusing the OTP cooldown and attempt rules.
* [ ] `[BE]` `POST /profile/phone/verify-current`: on success issue an opaque random `phone_change_token`, store at `phone_change:{user_id}` with a 10-minute TTL, return it in the body. Never a cookie.
* [ ] `[BE]` `POST /profile/phone/request-new`: requires a valid token; reject `PROFILE_PHONE_ALREADY_IN_USE` and `PROFILE_PHONE_SAME_AS_CURRENT`; send an OTP to the new number.
* [ ] `[BE]` Bind the token to the requested new number once step 3 runs; presenting it for a different number fails.
* [ ] `[BE]` `POST /profile/phone/verify-new`: update the phone number, invalidate the token, delete both OTPs, all in one transaction with the audit write.
* [ ] `[BE]` Invalid/expired/consumed token â†’ 403 `PROFILE_PHONE_CHANGE_TOKEN_INVALID`.
* [ ] `[BE]` Security logs `PHONE_CHANGE_REQUESTED`, `PHONE_CHANGE_CURRENT_VERIFIED`, `PHONE_CHANGE_COMPLETED`; audit log `PHONE_CHANGED`. Never the OTPs or the token.
* [ ] `[BE]` Changing the phone number does **not** revoke sessions.
* [ ] `[FE]` `lib/api/profile.ts` phone-change functions.
* [ ] `[FE]` `PhoneChangeWizard`: 4 steps, each its own RHF + Zod form.
* [ ] `[FE]` The token lives only in wizard/slice state and is wiped on unmount or completion. Never in storage.
* [ ] `[FE]` `PROFILE_PHONE_CHANGE_TOKEN_INVALID` resets the wizard to step 1 with an explanation.
* [ ] `[FE]` Leaving the page abandons the flow cleanly.
* [ ] `[FE]` Phase-8 keys in both message files.
* [ ] `[T]` `[BE]` Skipping step 2 (no token) fails.
* [ ] `[T]` `[BE]` Token reuse after completion fails.
* [ ] `[T]` `[BE]` A token issued for number X cannot verify number Y.
* [ ] `[T]` `[BE]` Changing to an already-registered number fails with the right code.
* [ ] `[T]` `[BE]` Expired token â†’ 403.
* [ ] `[T]` `[FE]` An invalid-token response resets the wizard to step 1.

### Exit Gate

* The 2-step flow cannot be short-circuited by any request ordering.
* The token never reaches `localStorage`, a cookie, or a log.

---

## Phase 9 - Session & Device Management

**Goal:** the feature that made the original documents contradict each other. It is fully in scope, API plus UI.

### Checklist

* [ ] `[BE]` `GET /security/devices`: devices with nested active sessions; per session `id`, `created_at`, `last_used_at`, `expires_at`, and `is_current` derived from the Access Token's `sid`.
* [ ] `[BE]` The response never contains token values, hashes, or token IDs.
* [ ] `[BE]` `DELETE /security/sessions/{id}` (auth + CSRF), scoped by user; foreign ID â†’ 404 `SESSION_NOT_FOUND`.
* [ ] `[BE]` `DELETE /security/devices/{id}/sessions`, scoped by user; foreign ID â†’ 404 `DEVICE_NOT_FOUND`.
* [ ] `[BE]` `DELETE /security/sessions` = global logout revoking **all** sessions on **all** devices, **including the current one**.
* [ ] `[BE]` Every revocation goes through the Phase-3 helper so the refresh family dies with the session.
* [ ] `[BE]` Whenever the revoked set includes the current session, clear all three cookies on that response.
* [ ] `[BE]` `SESSION_REVOKED` security log with scope metadata (`single` / `device` / `global`).
* [ ] `[FE]` `lib/api/security.ts` and `securitySlice`.
* [ ] `[FE]` `/security` page: devices as `Card`/`Accordion` with nested sessions.
* [ ] `[FE]` Each session shows created / last-active / expiry, with a `Badge` on the current one.
* [ ] `[FE]` Revoke buttons at session and device level, each behind an `AlertDialog`.
* [ ] `[FE]` A visually separated global-logout action whose dialog states plainly that all sessions on all devices including this one will end.
* [ ] `[FE]` Revocation is **never** optimistic: await the server, then refetch.
* [ ] `[FE]` If the revoked set includes the current session, run the shared cleanup routine and redirect to `/login`.
* [ ] `[FE]` `SESSION_NOT_FOUND` / `DEVICE_NOT_FOUND` refetch the list as stale.
* [ ] `[FE]` Phase-9 keys in both message files.
* [ ] `[T]` `[BE]` User B gets 404 for User A's session and device IDs.
* [ ] `[T]` `[BE]` Revoking a session invalidates its refresh token immediately.
* [ ] `[T]` `[BE]` Global logout revokes the current session and clears cookies.
* [ ] `[T]` `[BE]` `is_current` marks exactly one session.
* [ ] `[T]` `[BE]` No response field exposes token material.
* [ ] `[T]` `[FE]` Revoking the current session triggers cleanup and redirect.

### Exit Gate

* Logging in from two browsers, revoking one from the other, and having the revoked one land on `/login` works by hand.
* Global logout logs the initiating client out too.

---

## Phase 10 - Theme, i18n & RTL

**Goal:** the app is bilingual and directional. Keys were registered per phase; this phase makes them real.

### Checklist

* [ ] `[FE]` `next-themes` + `ThemeProvider` integrated with Shadcn; hydration flash suppressed.
* [ ] `[FE]` `ThemeToggle` (Sun/Moon) in navigation and settings.
* [ ] `[FE]` Theme persisted to `localStorage.theme`, **cleared on logout**, falling back to system.
* [ ] `[FE]` `next-intl` configured with `messages/en.json` and `messages/fa.json`.
* [ ] `[FE]` `LocaleSwitcher`; locale persisted to `localStorage.locale`, **cleared on logout**.
* [ ] `[FE]` `<html>` receives the correct `lang` and `dir` for the active locale.
* [ ] `[FE]` `settingsSlice` mirrors theme + locale without fighting `next-themes`.
* [ ] `[FE]` Replace every physical spacing utility with logical ones (`ms-*`, `me-*`, `ps-*`, `pe-*`, `text-start`, `text-end`).
* [ ] `[FE]` Directional icons flip in RTL.
* [ ] `[FE]` Persian locale renders digits and dates appropriately.
* [ ] `[FE]` Zod message keys resolve through `next-intl` at render time.
* [ ] `[FE]` Sweep for hardcoded user-visible strings; zero remain.
* [ ] `[FE]` `/settings` page exposing theme and language.
* [ ] `[FE]` No locale-prefixed routing unless a concrete need appears.
* [ ] `[T]` `en.json` and `fa.json` have identical key sets (automated).
* [ ] `[T]` Switching to `fa` sets `dir="rtl"`.
* [ ] `[T]` Validation errors render localized in both locales.
* [ ] `[T]` Logout clears theme and locale but keeps `device_id`.

### Exit Gate

* Every screen is usable in Persian RTL and English LTR.
* The key-parity test passes.
* No hardcoded string remains in any component.

---

## Phase 11 - Hardening, Test Sweep & DoD Audit

**Goal:** confirm every rule in the three `AGENTS.md` files actually holds. This is verification, not new features.

### Security audit

* [ ] No token, OTP, or phone-change token appears in any log, error body, response body, `localStorage`, `sessionStorage`, or Redux.
* [ ] Every mutating authenticated endpoint enforces CSRF; verified endpoint by endpoint.
* [ ] Every user-scoped resource returns 404 (never 403) for foreign IDs: tasks, sessions, devices.
* [ ] `Secure` cookies enabled when `ENV=production`; `COOKIE_SECURE=false` only for local HTTP.
* [ ] CORS allows exactly one configured origin with credentials, and lists both custom headers.
* [ ] `otp_debug` and console OTP printing are impossible in production.
* [ ] `X-Device-Id` influences no authorization decision anywhere in the codebase.
* [ ] Unhandled exceptions leak no stack trace or internal detail.

### Coverage sweep

* [ ] Every error code in root `AGENTS.md` Â§12 has a test asserting its HTTP status and envelope.
* [ ] Concurrent refresh (backend) and single-flight refresh (frontend) both covered.
* [ ] Reuse detection covered including cookie clearing.
* [ ] OTP attempt lockout covered.
* [ ] Cross-user access covered for all three resource types.
* [ ] Optimistic rollback covered for toggle and delete.
* [ ] Message-file parity covered.

### Definition of Done audit (root Â§19)

* [ ] Every feature has a defined API contract in OpenAPI.
* [ ] Auth and authorization rules respected everywhere.
* [ ] All schema changes exist as Alembic migrations; `upgrade head` works from empty.
* [ ] No security-sensitive behavior exposes credentials.
* [ ] All frontend HTTP goes through `apiClient`; zero stray Axios instances.
* [ ] All errors use the standard envelope.
* [ ] Audit and security events recorded where required.
* [ ] All user-visible strings localized in `en` and `fa`.
* [ ] Tests written and passing.
* [ ] Every user workflow verified end-to-end by hand.
* [ ] Nothing built outside the defined scope.

### Scope-discipline audit

* [ ] No microservices, event bus, CQRS, abstraction-only repositories, external SMS/logging providers, background workers, or unnecessary caching.
* [ ] No RTK Query, React Query, or SWR.
* [ ] No second Axios instance.
* [ ] No server-side theme/locale persistence.
* [ ] No custom Material-You color system; Shadcn defaults intact.
* [ ] `README` documents local setup, migrations, and the testing-only OTP behavior.

### Exit Gate

* Both test suites green.
* Every box above checked.
* A fresh clone can be brought up from `.env.example` plus migrations and reach a working login.

---

## Manual End-to-End Scenarios (run before declaring the project done)

1. First visit generates a `device_id`; login creates exactly one Device.
2. Login, wait for the Access Token to expire, act again: a silent refresh keeps you working.
3. Open several tabs, let the token expire, act in all of them at once: one refresh, no logout.
4. Login from two browsers; revoke browser B from browser A; B lands on `/login`.
5. Global logout from browser A: both clients are out, and A returns to `/login`.
6. Enter a wrong OTP five times: the code dies and a new one is required.
7. Change the phone number end-to-end, then log in with the new number.
8. Upload a full-resolution phone photo as an avatar: it succeeds and renders.
9. Switch to Persian: the whole app flips to RTL with no broken layout.
10. Logout: theme and locale reset, but `device_id` persists and no duplicate Device appears on the next login.
11. Try to reach another user's task, session, and device by ID: all 404.