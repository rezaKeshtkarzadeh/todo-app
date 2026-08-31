# Frontend (Next.js) - Agent Directives & Architecture

## AI Agent Persona & Coding Directives
You are an **Expert Frontend Developer**, specializing in React, Next.js (App Router), Redux Toolkit, and secure client-side architecture.

Before implementing or modifying frontend code, read `../AGENTS.md`.

**CRITICAL CODING RULES FOR THIS PROJECT:**
1. **Strict App Router Conventions:** This project exclusively uses the Next.js App Router (`app/` directory). ALWAYS import routing hooks from `next/navigation` (NOT `next/router`).
2. **Server vs. Client Components:** Default to Server Components. You MUST add the `'use client'` directive at the very top of any file using hooks (`useState`, `useEffect`, `useForm`, Redux hooks) or handling user events (`onClick`, `onSubmit`).
3. **Redux + Axios (No RTK Query):** Use Redux Toolkit's `createAsyncThunk` combined with the centralized Axios `apiClient`. Do NOT introduce RTK Query, React Query, or SWR.
4. **Forms and Validation:** Always use `react-hook-form` paired with `zod` and `@hookform/resolvers/zod`.
5. **UI Components:** Rely strictly on `shadcn/ui` and `lucide-react` for icons. Do NOT write custom CSS or inline styles; use Tailwind utility classes exclusively.
6. **Localization is Mandatory:** No user-visible string may be hardcoded in a component. Every label, error, and validation message goes through `next-intl` in both `en` and `fa`.

---

## 1. Stack

* Next.js
* App Router
* TypeScript
* Axios
* Redux Toolkit
* React Hook Form
* Zod
* Shadcn/ui
* TailwindCSS
* next-themes
* next-intl

Use Server Components where appropriate. Interactive components that require browser APIs, Redux, forms, or client-side state use Client Components.

---

## 2. Suggested Structure

```text
frontend/
â”œâ”€â”€ AGENTS.md
â”œâ”€â”€ messages/
â”‚   â”œâ”€â”€ en.json
â”‚   â””â”€â”€ fa.json
â”œâ”€â”€ src/
â”‚   â”œâ”€â”€ app/
â”‚   â”‚   â”œâ”€â”€ layout.tsx
â”‚   â”‚   â”œâ”€â”€ page.tsx
â”‚   â”‚   â”œâ”€â”€ login/
â”‚   â”‚   â”‚   â””â”€â”€ page.tsx
â”‚   â”‚   â”œâ”€â”€ tasks/
â”‚   â”‚   â”‚   â””â”€â”€ page.tsx
â”‚   â”‚   â”œâ”€â”€ profile/
â”‚   â”‚   â”‚   â””â”€â”€ page.tsx
â”‚   â”‚   â”œâ”€â”€ settings/
â”‚   â”‚   â”‚   â””â”€â”€ page.tsx
â”‚   â”‚   â””â”€â”€ security/
â”‚   â”‚       â””â”€â”€ page.tsx
â”‚   â”œâ”€â”€ components/
â”‚   â”‚   â”œâ”€â”€ ui/
â”‚   â”‚   â”œâ”€â”€ providers/
â”‚   â”‚   â”‚   â”œâ”€â”€ StoreProvider.tsx
â”‚   â”‚   â”‚   â”œâ”€â”€ ThemeProvider.tsx
â”‚   â”‚   â”‚   â”œâ”€â”€ IntlProvider.tsx
â”‚   â”‚   â”‚   â””â”€â”€ AppInit.tsx
â”‚   â”‚   â”œâ”€â”€ layout/
â”‚   â”‚   â”‚   â”œâ”€â”€ AppNav.tsx
â”‚   â”‚   â”‚   â”œâ”€â”€ ThemeToggle.tsx
â”‚   â”‚   â”‚   â””â”€â”€ LocaleSwitcher.tsx
â”‚   â”‚   â”œâ”€â”€ auth/
â”‚   â”‚   â”‚   â”œâ”€â”€ PhoneForm.tsx
â”‚   â”‚   â”‚   â””â”€â”€ OtpForm.tsx
â”‚   â”‚   â”œâ”€â”€ tasks/
â”‚   â”‚   â”‚   â”œâ”€â”€ TaskList.tsx
â”‚   â”‚   â”‚   â”œâ”€â”€ TaskItem.tsx
â”‚   â”‚   â”‚   â”œâ”€â”€ TaskForm.tsx
â”‚   â”‚   â”‚   â””â”€â”€ TaskEditDialog.tsx
â”‚   â”‚   â”œâ”€â”€ profile/
â”‚   â”‚   â”‚   â”œâ”€â”€ AvatarUploader.tsx
â”‚   â”‚   â”‚   â””â”€â”€ PhoneChangeWizard.tsx
â”‚   â”‚   â””â”€â”€ security/
â”‚   â”‚       â”œâ”€â”€ DeviceList.tsx
â”‚   â”‚       â”œâ”€â”€ DeviceCard.tsx
â”‚   â”‚       â”œâ”€â”€ SessionRow.tsx
â”‚   â”‚       â””â”€â”€ RevokeAllDialog.tsx
â”‚   â”œâ”€â”€ lib/
â”‚   â”‚   â”œâ”€â”€ api-client.ts
â”‚   â”‚   â”œâ”€â”€ api-error.ts
â”‚   â”‚   â”œâ”€â”€ error-messages.ts
â”‚   â”‚   â”œâ”€â”€ types.ts
â”‚   â”‚   â”œâ”€â”€ csrf.ts
â”‚   â”‚   â”œâ”€â”€ device-id.ts
â”‚   â”‚   â”œâ”€â”€ local-prefs.ts
â”‚   â”‚   â”œâ”€â”€ image.ts
â”‚   â”‚   â””â”€â”€ api/
â”‚   â”‚       â”œâ”€â”€ auth.ts
â”‚   â”‚       â”œâ”€â”€ profile.ts
â”‚   â”‚       â”œâ”€â”€ security.ts
â”‚   â”‚       â””â”€â”€ tasks.ts
â”‚   â”œâ”€â”€ store/
â”‚   â”‚   â”œâ”€â”€ store.ts
â”‚   â”‚   â”œâ”€â”€ hooks.ts
â”‚   â”‚   â””â”€â”€ slices/
â”‚   â”‚       â”œâ”€â”€ authSlice.ts
â”‚   â”‚       â”œâ”€â”€ tasksSlice.ts
â”‚   â”‚       â”œâ”€â”€ profileSlice.ts
â”‚   â”‚       â”œâ”€â”€ securitySlice.ts
â”‚   â”‚       â””â”€â”€ settingsSlice.ts
â”‚   â””â”€â”€ middleware.ts
â”œâ”€â”€ .env.example
â”œâ”€â”€ next.config.ts
â”œâ”€â”€ package.json
â””â”€â”€ tailwind.config.ts
```

The exact structure may change when a simpler organization is more appropriate, but every page listed above must exist in some form.

---

## 3. Authentication and Client Storage Rules

The frontend must never access authentication credentials directly.

The frontend must not:

* read `access_token`;
* read `refresh_token`;
* store either token in Redux;
* store either token in LocalStorage or SessionStorage;
* manually decode the JWT to determine authorization.

Authentication credentials are managed entirely by browser cookies and the backend. The frontend only maintains application-level authentication state.

### LocalStorage Policy

`localStorage` may hold exactly three non-sensitive values, and nothing else:

| Key         | Purpose                    | Cleared on logout |
| ----------- | -------------------------- | ----------------- |
| `device_id` | Stable device identity     | **No**            |
| `theme`     | Dark/Light preference      | **Yes**           |
| `locale`    | `en` or `fa`               | **Yes**           |

* `device_id` is a UUIDv4 generated once on first visit (`lib/device-id.ts`), read lazily and only in the browser. It **MUST survive logout**: clearing it would register a brand-new Device on every login and fill the user's device list with duplicates. Treat it as hardware-ish identity, not session data.
* `theme` and `locale` are session-scoped preferences. On any logout (local, device-level, or global) they are removed and the app falls back to system theme and the default locale. They are never sent to or stored on the backend.
* Never write tokens, OTP codes, phone-change tokens, or CSRF values to `localStorage` or `sessionStorage`.
* All `localStorage` access goes through `lib/local-prefs.ts` and `lib/device-id.ts`. Never touch `window.localStorage` directly from a component, and always guard for server-side rendering.

---

## 4. Axios API Client

All HTTP communication with the backend must use a centralized Axios client. Do not create independent Axios instances anywhere.

```text
Component
    â†“
Redux thunk / application logic
    â†“
API module
    â†“
apiClient
    â†“
Axios
    â†“
FastAPI
```

Components must not call Axios directly.

---

## 5. API Client Responsibilities

The centralized `apiClient` is responsible for transport-level behavior:

* base API URL;
* credentials/cookies;
* common headers;
* `X-CSRF-Token` header on state-changing requests;
* `X-Device-Id` header on every request;
* Axios request configuration;
* typed responses;
* API error normalization;
* authentication refresh;
* retrying the original request once after successful refresh;
* preventing refresh-request loops;
* handling refresh failure.

The API client must not contain business logic, UI logic, toast calls, Redux reducers, resource-specific transformations, or application navigation beyond the minimal mechanism needed for authentication recovery.

### Content-Type handling

The client sets `application/json` by default. For `FormData` payloads (avatar upload) it MUST **not** set `Content-Type` at all, so the browser can generate the multipart boundary. Detect `FormData` in the request interceptor and delete the header rather than overriding it with a hand-written multipart type.

---

## 6. Axios Credentials

The Axios client must send cookies with every request (`withCredentials: true`), configured centrally rather than per request.

---

## 7. CSRF and Device Headers

The frontend may read `csrf_token` from `document.cookie` (`lib/csrf.ts`). It must never attempt to read `access_token` or `refresh_token`.

The API client attaches:

* `X-CSRF-Token`, read fresh from the cookie at request time, on `POST`, `PUT`, `PATCH`, `DELETE`;
* `X-Device-Id`, from `lib/device-id.ts`, on **every** request.

Neither value belongs in Redux. Reading the CSRF token from the cookie when constructing the request is required, because rotation on refresh would make a cached copy stale.

---

## 8. Initial CSRF Initialization

On client application initialization, call `GET /auth/csrf-token` once to establish the CSRF cookie. This runs in a dedicated `AppInit` client component mounted from the root layout.

The endpoint does not return an authentication token, and the initialization logic must not assume the user is authenticated.

---

## 9. Authentication Refresh

When an authenticated API request receives `401`, attempt a refresh:

```text
API Request
    â†“
401
    â†“
POST /auth/refresh
    â†“
success?
 â”Œâ”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”
Yes            No
 â†“              â†“
Retry once     clear auth state
original       clear theme/locale
request        redirect to /login
```

The refresh endpoint itself must never recursively trigger another refresh attempt.

If the failing response carries `error.code === "AUTH_SESSION_REVOKED"`, do **not** attempt a refresh. The session is gone: reset auth state immediately and route to `/login` with a message explaining that the session was revoked.

---

## 10. Refresh Concurrency

Multiple API requests may receive 401 at approximately the same time. The frontend must avoid sending multiple concurrent refresh requests with the same Refresh Token.

```text
Request A â†’ 401 â”€â”
Request B â†’ 401 â”€â”¼â†’ one refresh request
Request C â†’ 401 â”€â”˜
                    â†“
                 success
                    â†“
             retry pending requests
```

Use a single shared in-flight refresh promise. Concurrent 401s await that same promise rather than starting their own refresh. If it fails, all affected requests fail consistently and auth state resets once, not once per request.

This behavior belongs in the API client layer. Getting it wrong triggers backend reuse detection and kills the user's session, so it must be covered by tests.

---

## 11. Authentication Retry Limits

Each request may undergo at most one authentication refresh cycle, tracked with a private flag on the request config. The refresh request itself must never cause another refresh request.

Avoid loops such as:

```text
401 â†’ refresh â†’ 401 â†’ refresh â†’ 401 ...
```

---

## 12. Generic Network Retry

Authentication retry and network retry are different concerns. Do not automatically retry all failed HTTP requests.

Blindly retrying mutations such as `POST /tasks` or `DELETE /tasks/{id}` may duplicate an operation the server actually completed. If generic retry is implemented at all, limit it to idempotent GETs with a small bounded count.

Generic network retry is optional. Authentication refresh/retry is required.

---

## 13. Typed API Responses

API functions must be strongly typed:

```text
tasksApi.list() â†’ Task[]
tasksApi.create(...) â†’ Task
tasksApi.update(...) â†’ Task
securityApi.listDevices() â†’ DeviceWithSessions[]
```

The API client supports generic response typing internally. Never use `any` for API responses.

---

## 14. API Contract and OpenAPI

The backend Pydantic schemas are the source of truth. Use FastAPI's OpenAPI schema to keep frontend types synchronized, and prefer generated TypeScript types over manually duplicating backend response types.

Where runtime validation is required, use Zod schemas generated from or kept synchronized with the contract.

```text
TypeScript = compile-time safety
Zod        = runtime validation
```

Do not assume TypeScript alone validates data received over HTTP.

Task updates use **PATCH** with a partial body. There is no PUT variant.

---

## 15. API Modules

Keep endpoint definitions separate from the low-level client:

```text
lib/api/auth.ts      â†’ sendOtp, verifyOtp, logout
lib/api/profile.ts   â†’ uploadAvatar, requestCurrentPhoneOtp, verifyCurrentPhoneOtp,
                       requestNewPhoneOtp, verifyNewPhoneOtp
lib/api/security.ts  â†’ listDevices, revokeSession, revokeDeviceSessions, revokeAllSessions
lib/api/tasks.ts     â†’ list, create, update, remove
```

These modules use `apiClient`. They never create their own Axios instances and never import React components.

---

## 16. API Error Handling

Backend errors follow:

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

Normalize them into a consistent `ApiError` representation:

```text
ApiError
â”œâ”€â”€ status
â”œâ”€â”€ code
â”œâ”€â”€ message
â”œâ”€â”€ details
â””â”€â”€ requestId
```

Network failures and non-conforming responses must also normalize into this shape, with a synthetic code, so consumers never have to inspect a raw Axios error.

---

## 17. Error Codes, Not Error Messages

Frontend logic must branch on `error.code`, never on `error.message`.

```text
Incorrect: if (message === "The OTP is invalid")
Correct:   if (code === "AUTH_INVALID_OTP")
```

Human-readable messages are not stable identifiers, and in this app they are localized, so comparing them is doubly broken.

`lib/error-messages.ts` maps each `error.code` to a `next-intl` message key, with a generic fallback for unknown codes. The backend `message` field is never shown to the user directly.

---

## 18. Error Presentation

The API client does not display toasts. It throws normalized errors. Application/UI layers decide presentation.

```text
AUTH_INVALID_OTP / AUTH_OTP_EXPIRED     â†’ inline error on the OTP field
AUTH_OTP_MAX_ATTEMPTS                   â†’ destroy the OTP step, send the user back to the phone step
AUTH_OTP_RATE_LIMITED                   â†’ disable resend, show cooldown
AUTH_SESSION_REVOKED                    â†’ reset auth state, route to /login with an explanation
PROFILE_AVATAR_TOO_LARGE / _INVALID_TYPE â†’ inline error on the uploader
PROFILE_PHONE_CHANGE_TOKEN_INVALID      â†’ reset the wizard to step 1
SESSION_NOT_FOUND / DEVICE_NOT_FOUND    â†’ refetch the device list, it is stale
TASK_NOT_FOUND                          â†’ remove the task from local state
INTERNAL_ERROR                          â†’ generic toast
```

Shadcn Sonner may be used for success/error notifications.

---

## 19. Redux Responsibilities

Redux Toolkit is for application state. It must never store Access Tokens, Refresh Tokens, JWT secrets, raw OTPs, phone-change tokens, or CSRF credentials as persistent state.

### `authSlice`

```text
isAuthenticated: boolean
phoneNumber: string | null
currentSessionId: string | null
status: idle | loading | error
error: serializable ApiError-like state
```

Thunks: `sendOtp`, `verifyOtp`, `logout`, `checkAuth`.

Authentication state is a UI representation of backend authentication. It is not an authorization mechanism.

### `profileSlice`

```text
avatarUrl: string | null
phoneChangeStep: idle | currentRequested | currentVerified | newRequested
status / error
```

The `phone_change_token` is held only for the lifetime of the wizard, in component state or a non-persisted slice field, and is wiped when the wizard unmounts or completes. It is never persisted to storage.

### `securitySlice`

```text
devices: DeviceWithSessions[]
status / error
revoking: string | null
```

### `settingsSlice`

```text
theme: 'light' | 'dark' | 'system'
locale: 'en' | 'fa'
```

`settingsSlice` mirrors the values written by `lib/local-prefs.ts` so the UI can react to them. `next-themes` remains the authority for applying the theme; the slice must not fight it.

---

## 20. Authentication State Initialization

Determine authentication state on startup with a lightweight authenticated request:

```text
GET /tasks â†’ 200 = authenticated, 401 = not authenticated
```

Do not add a dedicated `/auth/me` endpoint solely for this purpose.

CSRF initialization and authentication-state initialization are separate concerns and must not be collapsed into one call.

`currentSessionId` is not derived on the client. It comes from the `is_current` flag in `GET /security/devices`. Never decode the JWT to obtain it.

---

## 21. Tasks Slice

```text
items: Task[]
status: idle | loading | succeeded | error
error: string | null
```

Thunks: `fetchTasks`, `createTask`, `updateTask`, `deleteTask`.

Task API responses use shared/generated TypeScript types.

---

## 22. Optimistic Updates

Use optimistic updates for toggling `is_done` and deleting a task. The UI updates immediately; on failure, restore the previous state and surface the error.

Optimistic updates must not hide server failures. Creating a task does not need to be optimistic.

Session revocation must **not** be optimistic. Revocation is destructive and irreversible: wait for the server, then refetch the device list.

---

## 23. `/login`

```text
Phone number
    â†“
Send code
    â†“
OTP form
    â†“
Verify
    â†“
/tasks
```

The OTP form uses a 4-digit code. The testing-only `otp_debug` value may be surfaced during development, gated behind a development check. Do not design production UX around it.

Show remaining resend cooldown. On `AUTH_OTP_MAX_ATTEMPTS`, clear the OTP input, return to the phone step, and explain that a new code is required. Never count attempts client-side as if it were enforcement; the backend is authoritative.

---

## 24. `/tasks`

The task page provides an add-task form, the task list, a completion checkbox, the task title, edit and delete actions, and navigation to profile/settings/security.

Completed tasks visually indicate completion (for example a strikethrough title). Deleting a task uses a Shadcn `AlertDialog` confirmation.

---

## 25. Route Protection

Unauthenticated users attempting to reach `/tasks`, `/profile`, `/settings`, or `/security` are redirected to `/login`.

Route protection may use a client-side authentication check, or middleware. If middleware is used it MUST NOT attempt to verify the JWT: the signing secret exists only on the backend. A cookie-presence check is a navigation hint only. Backend authorization remains authoritative.

---

## 26. Components

Keep interactive components small and focused. Do not put an entire workflow into a single component.

Use Server Components for static/layout content. Use Client Components for forms, Redux consumers, interactive dialogs, checkboxes, client-side authentication state, and browser cookie/storage access.

---

## 27. Shadcn/ui

Use the official Shadcn CLI to add base components: `Button`, `Input`, `Dialog`, `AlertDialog`, `Card`, `Checkbox`, `Form`, `Sonner`, `Accordion`, `Avatar`, `Badge`, `Skeleton`, `Separator`, `DropdownMenu`, `Tabs`.

Do not manually recreate Shadcn base components when the official one exists. Use Shadcn's default styling and theme. Do not introduce a custom Material You-style color system.

---

## 28. Forms and Validation

Use React Hook Form + Zod for, at minimum:

* phone number form;
* OTP form;
* task creation form;
* task editing form;
* avatar upload (client-side type and size check before sending);
* each step of the phone-change wizard.

Validation messages come from `next-intl`, not hardcoded English strings. Zod schemas therefore carry message **keys** resolved at render time, not literal text.

Frontend validation improves UX but does not replace backend validation.

---

## 29. API and Redux Separation

```text
Component â†’ Redux thunk â†’ API module â†’ apiClient â†’ Axios
```

Do not put raw Axios calls inside reducers, UI notifications inside API functions, or React dependencies inside API modules.

---

## 30. Serializable Redux State

Redux state and actions must remain serializable. Do not store Axios responses or request objects, `Error` class instances, HTTP clients, promises, `File`/`FormData` objects, or browser objects.

Convert `ApiError` instances into plain serializable objects before putting them in state.

---

## 31. Loading and Error States

Every asynchronous operation has predictable UI states: `idle`, `loading`, `success`, `error`. Never leave the UI in a permanent loading state after a failure. Use Shadcn `Skeleton` for initial loads of the task list and device list.

---

## 32. Environment Configuration

`.env.example` should contain at least:

```text
NEXT_PUBLIC_API_URL=
NEXT_PUBLIC_API_ORIGIN=
```

Only values that genuinely need browser exposure use the `NEXT_PUBLIC_` prefix. No authentication secrets belong in frontend environment variables.

Avatars are served from the backend's `/uploads` mount, which is a different origin in development. `next.config.ts` MUST declare it in `images.remotePatterns`, driven by configuration, or `next/image` will refuse to render avatars.

---

## 33. Security Boundaries

Never:

* expose authentication tokens through JavaScript;
* log authentication tokens, OTPs, or phone-change tokens;
* include tokens in Redux;
* put tokens in URLs;
* decode tokens to make authorization decisions;
* trust client-provided user IDs for authorization;
* treat `device_id` as a security factor. It identifies a device for display and grouping only, and it is trivially forgeable.

The backend is responsible for authentication and authorization.

---

## 34. Simplicity

Do not introduce a custom state-management framework, multiple HTTP clients, GraphQL, React Query alongside Redux, custom authentication libraries, unnecessary middleware, complex offline synchronization, or unnecessary abstraction layers.

Axios + centralized API client + Redux Toolkit is sufficient for the current scope.

---

## 35. UI/UX, Theme, and i18n

### Responsive Design

The application MUST be fully responsive (mobile, tablet, desktop) using Tailwind breakpoints (`sm:`, `md:`, `lg:`). Mobile is the primary target: the task list and device list must be comfortable on a phone.

### Theme Management

* Implement Dark Mode with `next-themes` integrated with `shadcn/ui`.
* Provide a Sun/Moon toggle in the navigation and in settings.
* Persist to `localStorage` under `theme`, and **clear it on logout**.
* Suppress the hydration flash using the standard `next-themes` setup.

### Internationalization (i18n) & RTL

* Support English (LTR) and Persian (RTL) with `next-intl`.
* Messages live in `messages/en.json` and `messages/fa.json` with identical key sets. A key present in one and missing in the other is a bug.
* All strings, error messages, and validation messages must be localized. No hardcoded user-visible text.
* `<html>` must receive the correct `lang` and `dir` for the active locale.
* Use Tailwind logical properties (`ms-*`, `me-*`, `ps-*`, `pe-*`, `text-start`, `text-end`) instead of physical left/right utilities so RTL works without duplicate styles. Directional icons must flip in RTL.
* Persian UI should render digits and dates appropriately for the locale.
* Persist to `localStorage` under `locale`, and **clear it on logout**.

### Profile & Security UI

* **Avatar:** Shadcn `Avatar` with an upload control. Validate type (`jpeg`/`png`/`webp`) and size (**5 MB max**) before upload, and downscale/compress in the browser (`lib/image.ts`) so ordinary phone-camera photos pass. Show a local preview, then the server-returned path on success. The backend limit is authoritative; never assume client-side validation is sufficient.
* **Phone change:** a multi-step wizard mirroring the backend's 2-step flow (request current OTP â†’ verify current â†’ enter new number â†’ verify new). Each step is a separate form with its own validation. The `phone_change_token` lives only in wizard state. On expiry or `PROFILE_PHONE_CHANGE_TOKEN_INVALID`, reset to step 1 and say why. Leaving the page abandons the flow.
* **Session & device UI:** devices as Shadcn `Card` or `Accordion` items with their active sessions nested inside. Each session shows creation time, last activity, and expiry, with a `Badge` on the current session. Provide a Revoke button at session level and at device level, each behind an `AlertDialog`.
* **Global logout:** a clearly separated destructive action with its own `AlertDialog` that states plainly that **all** sessions on **all** devices, including this one, will be terminated. On success, reset all slices, clear `theme` and `locale` from `localStorage`, keep `device_id`, and redirect to `/login`.
* **Revoking the current session:** if the user revokes the session they are currently using (directly, via its device, or via global logout), treat it exactly like logout: reset state, clear preference keys, redirect to `/login`. Do not leave the app rendering an authenticated shell against dead cookies.

---

## 36. Logout Cleanup Routine

Every logout path (explicit logout, refresh failure, `AUTH_SESSION_REVOKED`, current-session revocation, global logout) must run one shared cleanup routine that:

1. resets `authSlice`, `tasksSlice`, `profileSlice`, `securitySlice`;
2. removes `theme` and `locale` from `localStorage`;
3. **preserves** `device_id`;
4. redirects to `/login`.

Implement it once and call it from everywhere. Duplicating this logic is how the app ends up half-logged-out.

---

## 37. Out of Scope

Unless explicitly requested later:

* complex synchronization;
* PWA/offline functionality;
* server-side persistence of theme or locale;
* device fingerprinting beyond the `device_id` UUID;
* locale-prefixed routing (`/en/...`, `/fa/...`) unless a concrete requirement appears.

---

## 38. Frontend Testing Protocol

* **Framework:** `Vitest` and `React Testing Library`.
* **API Mocking:** MSW. Do NOT mock Axios directly; mock the network layer so `apiClient` logic (refresh interceptor, concurrency, header injection) is genuinely exercised.
* **Redux:** test slices and thunks independently, verifying `idle â†’ loading â†’ success/error` transitions.
* **Components:** test user interactions (clicking, typing) rather than implementation details, and confirm forms trigger validation errors.
* **Required coverage:**
  * `X-Device-Id` present on every request; `X-CSRF-Token` present on mutations only.
  * `FormData` requests do not carry a hand-set `Content-Type`.
  * A 401 triggers exactly one refresh and one retry of the original request.
  * Three concurrent 401s trigger exactly **one** refresh call.
  * Refresh failure runs the cleanup routine once and redirects to `/login`.
  * `AUTH_SESSION_REVOKED` skips refresh entirely.
  * Logout clears `theme` and `locale` but leaves `device_id` intact.
  * Optimistic toggle and delete roll back correctly on server error.
  * `en.json` and `fa.json` have identical key sets.