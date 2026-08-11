<div align="center">

# 🔌 TapeLine

**A full-stack data connector platform for engineers and analysts who need to extract, edit, and store data from multiple database sources — fast.**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-6.1-092E20?style=flat-square&logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Celery](https://img.shields.io/badge/Celery-5.6-37814A?style=flat-square&logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis&logoColor=white)](https://redis.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

**[Live Demo](https://the-tapeline.vercel.app) · [API Docs](https://the-tapeline.onrender.com/api/docs/) · [ReDoc](https://the-tapeline.onrender.com/api/redoc/)**

</div>

---

## What is TapeLine?

TapeLine lets you connect to any of your databases — PostgreSQL, MySQL, MongoDB, or ClickHouse — extract data in configurable batches with dynamic filtering and sorting, edit records interactively in a live data grid, and export the results as JSON, CSV, or Excel with full source metadata. All from one clean, role-aware web interface.

Built as a full-stack portfolio project demonstrating production patterns: JWT auth with token blacklisting, encrypted credential storage, async job processing with Celery + Redis, composite database indexes, bulk record creation, paginated API responses, and authenticated file downloads.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔗 **Multi-DB Connectors** | Connect to PostgreSQL, MySQL, MongoDB, and ClickHouse |
| 📦 **Batch Extraction** | Configure batch sizes when pulling records from any source |
| 🔍 **Query Builder** | Filter by column/operator/value and sort before extraction |
| ✏️ **Inline Editing** | Edit extracted records directly in an interactive data grid |
| 💾 **Multi-Format Export** | Export as JSON, CSV, or styled Excel (.xlsx) with source metadata |
| ⚡ **Async Job Processing** | Celery + Redis background workers — API responds instantly |
| 📄 **Authenticated Downloads** | Files served via JWT-authenticated endpoint, not raw URLs |
| 🕐 **Metadata on Export** | All exported files include source DB, table, and timestamps |
| 🔐 **Role-Based Access** | Admins see everything; users see only their own data and shared files |
| ⚙️ **Connection Presets** | One-click presets for Docker-local DBs, Neon PostgreSQL, and MongoDB Atlas |
| 🔑 **JWT Auth** | Login, token refresh, and logout with refresh-token blacklisting |
| 🔒 **Encrypted Credentials** | Database passwords stored using Fernet symmetric encryption |
| 📊 **Auto API Docs** | Swagger UI and ReDoc generated via drf-spectacular |
| 🚀 **Optimised Queries** | Composite DB indexes, select_related, and bulk_create throughout |

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 16 (App Router), TypeScript |
| **UI State** | Zustand |
| **Server State** | TanStack React Query |
| **Data Grid** | TanStack React Table |
| **Styling** | Tailwind CSS |
| **Backend** | Django 6.1 + Django REST Framework |
| **Auth** | SimpleJWT (with token blacklisting) |
| **Async Tasks** | Celery 5.6 + Redis 7 |
| **Primary DB** | PostgreSQL 16 |
| **Connectors** | psycopg2, PyMySQL, pymongo, clickhouse-connect |
| **Export** | openpyxl (Excel), csv, json |
| **API Docs** | drf-spectacular (Swagger + ReDoc) |
| **Infrastructure** | Docker + Docker Compose |
| **Deployment** | Render (backend) + Vercel (frontend) |

---

## 🏗 Project Structure

The-Tapeline/
├── backend/
│ ├── accounts/ # User model, JWT auth, registration & profiles
│ ├── connectors/ # DB connection model + multi-DB connector abstraction
│ ├── data_manager/ # Extraction jobs, records, Celery tasks, file downloads
│ │ ├── models.py # ExtractionJob, ExtractedRecord, StoredFile (with indexes)
│ │ ├── views.py # REST endpoints with select_related + bulk_create
│ │ └── tasks.py # Celery async extraction task
│ ├── core/ # Project-level config utilities
│ └── tapeline/ # Django settings, URL routing, Celery config
│ ├── celery.py # Celery app configuration
│ └── settings.py # CELERY_*, REST_FRAMEWORK, SPECTACULAR_SETTINGS
├── frontend/
│ ├── app/
│ │ ├── dashboard/
│ │ │ ├── connections/ # Connection creation & management UI
│ │ │ ├── jobs/ # Query builder, extraction jobs, inline data grid
│ │ │ └── files/ # File listing, authenticated download, share
│ │ ├── login/
│ │ └── register/
│ └── lib/
│ ├── api.ts # Axios instance with JWT interceptors
│ └── store.ts # Zustand auth store
├── docker-compose.yml # 9 services: backend, frontend, celery, redis, 4 DBs
├── .env.example # Environment variable template
└── README.md


---

## 🚀 Getting Started

### Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose installed

### 1. Clone the repository

```bash
git clone https://github.com/VINN5/The-Tapeline.git
cd The-Tapeline
```

### 2. Set up environment variables

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

> **Generate a Fernet encryption key:**
> ```bash
> python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
> ```

> **Generate a Django secret key:**
> ```bash
> python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
> ```

### 3. Start all services

```bash
docker compose up --build
```

This spins up 9 containers: Django backend, Next.js frontend, Celery worker, Redis, PostgreSQL, MySQL, MongoDB, and ClickHouse.

### 4. Access the app

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000/api/ |
| Swagger UI | http://localhost:8000/api/docs/ |
| ReDoc | http://localhost:8000/api/redoc/ |

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

### Jobs

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/jobs/` | List extraction jobs |
| `POST` | `/api/jobs/` | Create job — dispatches async Celery task, returns instantly |
| `GET` | `/api/jobs/{id}/` | Get a single job and its current status |
| `GET` | `/api/jobs/{id}/records/` | Get paginated extracted records |
| `POST` | `/api/jobs/{id}/submit/` | Submit edited records and generate export file |

### Files

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/files/` | List files accessible to you |
| `GET` | `/api/files/{id}/download/` | Authenticated file download (JSON/CSV/XLSX) |
| `POST` | `/api/files/{id}/share/` | Share a file with another user by username |
| `DELETE` | `/api/files/{id}/` | Delete a file |

---

## ⚙️ How Async Extraction Works

1. User submits a job via the UI
2. API creates the job record with `status: pending` and responds **immediately**
3. Celery worker picks up the task from Redis queue
4. Worker fetches data from the external database, applies filters/sort, and bulk-creates records
5. Job status updates to `completed` or `failed`
6. Frontend polls the job status and loads records when ready

---

## 🧪 Running Tests

```bash
docker compose exec backend python manage.py test
```

---

## 🗺 Roadmap

- [x] Multi-DB connectors (PostgreSQL, MySQL, MongoDB, ClickHouse)
- [x] Batch extraction with configurable batch sizes
- [x] Inline record editing with TanStack React Table
- [x] Multi-format export (JSON, CSV, Excel)
- [x] Query builder — filter and sort before extraction
- [x] Async job processing with Celery + Redis
- [x] Auto-generated API docs (Swagger UI + ReDoc)
- [x] Authenticated file downloads
- [x] DB performance optimisation (indexes, select_related, bulk_create)
- [x] Live deployment (Render + Vercel)
- [ ] Frontend polling for real-time job status
- [ ] Connection health status indicators
- [ ] Scheduled extractions (cron-style via Celery Beat)
- [ ] Virtualised data grid for large record sets

---

## 👤 Author

**Vincent Wambugu**
Full Stack Developer — Nairobi, Kenya

[![GitHub](https://img.shields.io/badge/GitHub-VINN5-181717?style=flat-square&logo=github)](https://github.com/VINN5)

---

## 📄 License

This project is licensed under the MIT License.