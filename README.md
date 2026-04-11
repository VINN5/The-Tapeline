# TapeLine

**A full-stack data connector platform** for connecting to multiple databases, extracting data in configurable batches, editing records interactively, and storing results securely.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16 (App Router) |
| UI State | Zustand |
| Server State | TanStack React Query |
| Data Grid | TanStack React Table |
| Styling | Tailwind CSS |
| Backend | Django + Django REST Framework |
| Auth | SimpleJWT (with token blacklisting) |
| Database | PostgreSQL |
| Connectors | psycopg2, PyMySQL, pymongo, clickhouse-connect |
| Containerization | Docker + Docker Compose |

## Features

- Connect to **PostgreSQL, MySQL, MongoDB, and ClickHouse** databases
- Extract data in **configurable batch sizes** from any connected source
- **Inline editing** of extracted records via an interactive data grid
- **Dual storage** on submission — records saved to PostgreSQL and exported as JSON or CSV
- Exported files include **source metadata and timestamps**
- **Role-based access control** — admins have full access, users see only their own data and files shared with them
- **Preset connection system** for one-click connection to local Docker databases and cloud services (Neon PostgreSQL, MongoDB Atlas)
- JWT authentication with **automatic token refresh** and **logout blacklisting**

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose installed

### Running the App

1. **Clone the repository**
   ```bash
   git clone https://github.com/VINN5/Tapeline.git
   cd Tapeline
   ```

2. **Set up environment variables**

   Create a `.env` file in the `backend/` directory:
   ```env
   SECRET_KEY=your-django-secret-key
   ENCRYPTION_KEY=your-fernet-encryption-key
   DEBUG=True
   ```

3. **Start all services**
   ```bash
   docker compose up --build
   ```

4. **Access the app**
   - Frontend: [http://localhost:3000](http://localhost:3000)
   - Backend API: [http://localhost:8000/api/](http://localhost:8000/api/)

## API Reference

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/accounts/register/` | Register new user, returns tokens |
| POST | `/api/accounts/token/` | Login, returns JWT access + refresh |
| POST | `/api/accounts/token/refresh/` | Refresh access token |
| POST | `/api/accounts/logout/` | Blacklist refresh token |
| GET/PATCH | `/api/accounts/profile/` | Get or update user profile |
| GET | `/api/accounts/users/` | List all users (admin only) |

### Connections

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/connections/` | List own connections |
| POST | `/api/connections/` | Create new connection |
| DELETE | `/api/connections/{id}/` | Delete connection |
| POST | `/api/connections/{id}/test/` | Test connection |
| GET | `/api/connections/{id}/tables/` | List tables/collections |
| GET | `/api/connections/presets/` | Get preset configurations |
| POST | `/api/connections/connect_preset/` | Connect using a preset |

### Jobs & Files

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/jobs/` | List extraction jobs |
| POST | `/api/jobs/` | Create and run extraction job |
| GET | `/api/jobs/{id}/records/` | Get extracted records |
| POST | `/api/jobs/{id}/submit/` | Submit edited records + generate file |
| GET | `/api/files/` | List accessible files |
| GET | `/api/files/{id}/download/` | Download a file |
| POST | `/api/files/{id}/share/` | Share file with another user |
| DELETE | `/api/files/{id}/` | Delete a file |

## Project Structure

```
Tapeline/
├── backend/
│   ├── accounts/        # User model, JWT auth, registration
│   ├── connectors/      # DB connection model + connector abstraction layer
│   ├── data_manager/    # Extraction jobs, records, dual storage
│   ├── core/            # Legacy connection config
│   └── tapeline/        # Django project settings
├── frontend/
│   ├── app/
│   │   ├── dashboard/
│   │   │   ├── connections/   # Connection management
│   │   │   ├── jobs/          # Extraction + editable data grid
│   │   │   └── files/         # File listing, download, share
│   │   ├── login/
│   │   └── register/
│   └── lib/
│       ├── api.ts       # Axios instance with JWT interceptors
│       └── store.ts     # Zustand auth store
└── docker-compose.yml
```

## Running Tests

```bash
# Backend unit tests
docker compose exec backend python manage.py test
```

## License

This project was built as part of a Full Stack Developer assessment.