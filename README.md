<div align="center">

# 🔌 TapeLine

**A full-stack data connector platform for engineers and analysts who need to extract, edit, and store data from multiple database sources — fast.**

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-REST_Framework-092E20?style=flat-square&logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

</div>

---

## What is TapeLine?

TapeLine lets you connect to any of your databases — PostgreSQL, MySQL, MongoDB, or ClickHouse — extract data in configurable batches, edit records interactively in a live data grid, and export the results as JSON or CSV with full source metadata. All from one clean, role-aware web interface.

It was built as a full-stack developer assessment project and demonstrates production patterns including JWT auth with token blacklisting, encrypted credential storage, dual write storage, and inline data editing via TanStack React Table.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔗 **Multi-DB Connectors** | Connect to PostgreSQL, MySQL, MongoDB, and ClickHouse |
| 📦 **Batch Extraction** | Configure batch sizes when pulling records from any source |
| ✏️ **Inline Editing** | Edit extracted records directly in an interactive data grid |
| 💾 **Dual Storage** | Submissions saved to PostgreSQL *and* exported as JSON or CSV |
| 🕐 **Metadata on Export** | All exported files include source info and timestamps |
| 🔐 **Role-Based Access** | Admins see everything; users see only their own data and shared files |
| ⚡ **Connection Presets** | One-click presets for Docker-local DBs, Neon PostgreSQL, and MongoDB Atlas |
| 🔑 **JWT Auth** | Login, token refresh, and logout with refresh-token blacklisting |
| 🔒 **Encrypted Credentials** | Database passwords stored using Fernet symmetric encryption |

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 16 (App Router), TypeScript |
| **UI State** | Zustand |
| **Server State** | TanStack React Query |
| **Data Grid** | TanStack React Table |
| **Styling** | Tailwind CSS |
| **Backend** | Django + Django REST Framework |
| **Auth** | SimpleJWT (with token blacklisting) |
| **Primary DB** | PostgreSQL |
| **Connectors** | psycopg2, PyMySQL, pymongo, clickhouse-connect |
| **Infrastructure** | Docker + Docker Compose |

---

## 🏗 Project Structure

```
The-Tapeline/
├── backend/
│   ├── accounts/        # User model, JWT auth, registration & profiles
│   ├── connectors/      # DB connection model + multi-DB connector abstraction
│   ├── data_manager/    # Extraction jobs, records, dual storage logic
│   ├── core/            # Project-level config utilities
│   └── tapeline/        # Django project settings & URL routing
├── frontend/
│   ├── app/
│   │   ├── dashboard/
│   │   │   ├── connections/   # Connection creation & management UI
│   │   │   ├── jobs/          # Extraction jobs + inline editable data grid
│   │   │   └── files/         # File listing, download, and share
│   │   ├── login/
│   │   └── register/
│   └── lib/
│       ├── api.ts             # Axios instance with JWT interceptors
│       └── store.ts           # Zustand auth store
├── docker-compose.yml
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose installed on your machine

### 1. Clone the repository

```bash
git clone https://github.com/VINN5/The-Tapeline.git
cd The-Tapeline
```

### 2. Set up environment variables

Create a `.env` file inside the `backend/` directory:

```env
SECRET_KEY=your-django-secret-key
ENCRYPTION_KEY=your-fernet-encryption-key
DEBUG=True
```

> **Generate a Fernet key** by running:
> ```bash
> python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
> ```

### 3. Start all services

```bash
docker compose up --build
```

This spins up the Django backend, Next.js frontend, and a PostgreSQL database.

### 4. Access the app

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000/api/ |

---

## 📡 API Reference

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/accounts/register/` | Register a new user; returns JWT tokens |
| `POST` | `/api/accounts/token/` | Login; returns access + refresh tokens |
| `POST` | `/api/accounts/token/refresh/` | Refresh an access token |
| `POST` | `/api/accounts/logout/` | Blacklist the refresh token |
| `GET/PATCH` | `/api/accounts/profile/` | Get or update user profile |
| `GET` | `/api/accounts/users/` | List all users *(admin only)* |

### Connections

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/connections/` | List your saved connections |
| `POST` | `/api/connections/` | Create a new connection |
| `DELETE` | `/api/connections/{id}/` | Delete a connection |
| `POST` | `/api/connections/{id}/test/` | Test a connection |
| `GET` | `/api/connections/{id}/tables/` | List tables or collections |
| `GET` | `/api/connections/presets/` | Get available preset configs |
| `POST` | `/api/connections/connect_preset/` | Connect using a preset |

### Jobs & Files

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/jobs/` | List extraction jobs |
| `POST` | `/api/jobs/` | Create and run a new extraction job |
| `GET` | `/api/jobs/{id}/records/` | Get extracted records for a job |
| `POST` | `/api/jobs/{id}/submit/` | Submit edited records and generate export file |
| `GET` | `/api/files/` | List files accessible to you |
| `GET` | `/api/files/{id}/download/` | Download a file |
| `POST` | `/api/files/{id}/share/` | Share a file with another user |
| `DELETE` | `/api/files/{id}/` | Delete a file |

---

## 🧪 Running Tests

```bash
# Run backend unit tests inside the running container
docker compose exec backend python manage.py test
```

The test suite covers authentication flows, connection validation, extraction job logic, and role-based access controls.

---

## 🗺 Roadmap

- [ ] Query builder UI — filter and sort before extraction
- [ ] Excel (`.xlsx`) export support
- [ ] Scheduled extractions with Celery + Redis
- [ ] Auto-generated API docs via `drf-spectacular` (Swagger UI)
- [ ] Connection health status indicators
- [ ] Live deployment (Railway + Vercel)

---

## 👤 Author

**Vincent Wambugu**
Full Stack Developer — Nairobi, Kenya

[![GitHub](https://img.shields.io/badge/GitHub-VINN5-181717?style=flat-square&logo=github)](https://github.com/VINN5)

---

## 📄 License

This project is licensed under the MIT License.
