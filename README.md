Note: Notice that this app will have some issue or something won't match with AGENTS rule I wrote. This is my first app with AI/AGENTS, so this may have mentioned problems. Or maybe something in architecture of app is wrong or mismatch.

# Todo App

A security-conscious full-stack Todo application built with modern web technologies.

This project is planned and implemented using an **Agent-Driven Development** approach, where AI agents assist throughout the software development lifecycle under defined architectural, security, and implementation rules.

## Features

* Phone number + OTP authentication
* Cookie-based authentication
* Access and Refresh Token separation
* Refresh Token rotation and reuse detection
* Session and device management
* CSRF protection
* User-scoped Todo CRUD operations
* Profile avatar management
* Secure phone number change flow
* Security and audit logging
* Dark and Light themes
* English and Persian language support
* Responsive design

## Tech Stack

**Backend**

* Python
* FastAPI
* PostgreSQL
* SQLAlchemy Async
* Redis
* Alembic
* Pydantic v2
* Argon2
* JWT
* Uvicorn

**Frontend**

* Next.js
* TypeScript
* App Router
* Axios
* Redux Toolkit
* React Hook Form
* Zod
* Shadcn/ui
* Tailwind CSS
* next-themes
* next-intl
* Bun

## Repository Structure

```text
todo-app/
├── AGENTS.md
├── README.md
├── backend/
│   ├── AGENTS.md
│   └── ...
└── frontend/
    ├── AGENTS.md
    └── ...
```

## AI Agent-Driven Development

The project is planned and implemented with the assistance of **AI Agents**.

The `AGENTS.md` files define the project's:

* Architecture
* Security requirements
* Technology constraints
* API contracts
* Coding standards
* Testing requirements
* Scope boundaries

These rules guide AI agents throughout the development process.

## Running the Project

### Prerequisites

* Python
* [uv](https://docs.astral.sh/uv/)
* [Bun](https://bun.sh/)
* PostgreSQL
* Redis

### Backend

```bash
cd backend
uv sync
```

Create the environment file:

```bash
cp .env.example .env
```

Run migrations:

```bash
uv run alembic upgrade head
```

The backend can be started directly from the IDE by running:

```text
backend/app/main.py
```

The application also supports running through the command line:

```bash
uv run python -m app.main
```

Backend:

```text
http://localhost:8000
```

API documentation:

```text
http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
bun install
```

Create the environment file:

```bash
cp .env.example .env.local
```

Start the development server:

```bash
bun dev
```

Frontend:

```text
http://localhost:3000
```

## Documentation

Detailed project architecture, development rules, and security requirements are defined in:

```text
AGENTS.md
backend/AGENTS.md
frontend/AGENTS.md
```
