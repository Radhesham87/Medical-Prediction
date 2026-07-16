# NEET Medical College Prediction Portal

A production-ready full-stack web app that predicts probable medical colleges from a
candidate's **NEET score** or **All-India Rank (AIR)**, using the previous year's closing
cutoffs. It includes JWT auth with an **admin-approval workflow**, a prediction engine over
an Excel dataset, PDF report export, per-user history, and a full admin dashboard.

> **Disclaimer:** Predictions are based on last year's closing cutoffs and are indicative
> only. Actual admissions depend on the seat matrix, counselling rounds, and official
> eligibility. Always verify with the official counselling authority.

---

## Tech stack

| Layer            | Technology                                                        |
| ---------------- | ----------------------------------------------------------------- |
| Frontend         | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, React Hook Form, next-themes, sonner |
| Backend          | Python 3.12, FastAPI, SQLAlchemy 2, Pydantic v2, SlowAPI (rate limiting) |
| Prediction       | Pandas, NumPy, OpenPyXL                                            |
| PDF / Excel      | ReportLab, OpenPyXL                                                |
| Database         | PostgreSQL (SQLite fallback for local dev)                         |
| Auth             | JWT (python-jose) + bcrypt password hashing                        |
| Deploy           | Frontend → Vercel · Backend + DB → Render                          |

---

## Folder structure

```
Medical Prediction/
├── data/
│   └── All_Medical_College_Last_Cutoff.xlsx   # cutoff dataset
├── backend/
│   ├── app/
│   │   ├── core/          # config, security (JWT + bcrypt), logging
│   │   ├── db/            # SQLAlchemy engine & session
│   │   ├── models/        # User, Prediction ORM models
│   │   ├── schemas/       # Pydantic request/response models
│   │   ├── api/
│   │   │   ├── deps.py    # auth guards (current user / admin / approved)
│   │   │   └── routes/    # auth, users, admin, predict, history, dataset
│   │   ├── services/      # prediction_engine, pdf_generator, excel_export
│   │   ├── seed.py        # create tables + first admin
│   │   └── main.py        # FastAPI app (CORS, rate limit, security headers)
│   ├── tests/             # pytest suite for the prediction engine
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── src/
│       ├── app/           # landing, login, register, predict, history, admin
│       ├── components/    # navbar, theme-provider, prediction-table, loading
│       ├── lib/           # api client, auth token store, utils
│       └── types/         # shared TypeScript types
├── .github/workflows/ci.yml   # CI: backend tests + frontend build
├── docker-compose.yml         # one-command local full stack
├── render.yaml                # Render blueprint (backend + free Postgres)
└── README.md
```

---

## How the prediction engine works

The dataset holds **last year's closing cutoff** for each
`college × degree × category × gender` bucket. A cutoff is the *last admitted* candidate,
so the engine grades a candidate against it:

1. **Load & normalise** — split the `Quota-Gender` column (e.g. `OBC-M`) into category +
   gender, drop physically-impossible NEET scores (keeps `0–720`) and non-positive ranks,
   and parse the numeric category rank out of the `Category` column (e.g. `SEBC-2710`).
2. **Filter** by the selected degree(s), gender, and category.
3. **Grade the chance:**
   - **By score:** `delta = candidate − cutoff`. `≥ +10` → **High**, `−5…+10` → **Moderate**,
     `−20…−5` → **Low**, below that → dropped.
   - **By AIR:** `ratio = candidate ÷ cutoff` (lower is better). `≤ 0.85` → **High**,
     `≤ 1.05` → **Moderate**, `≤ 1.25` → **Low**, above that → dropped.
4. **Sort** best band first, then most-competitive college within a band.
5. **OPEN rule:** for the OPEN category the *Category Rank* column is hidden entirely.

The bands are heuristic and interpretable — tune the constants at the top of
`backend/app/services/prediction_engine.py` to taste.

---

## Local development

### Option A — Docker (one command)

```bash
docker compose up --build
```

- Frontend → http://localhost:3000
- Backend docs → http://localhost:8000/docs
- Postgres → localhost:5432

### Option B — run each part manually

**Backend**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # edit SECRET_KEY etc.
uvicorn app.main:app --reload
```

Tables are created and the first admin is seeded automatically on startup.
Without a `DATABASE_URL` it uses a local SQLite file — zero external services needed.

**Frontend**

```bash
cd frontend
cp .env.example .env.local     # NEXT_PUBLIC_API_URL=http://localhost:8000/api
npm install
npm run dev
```

### Default admin

```
Email:    admin@medpredict.local
Password: Admin@12345
```

Change these via `FIRST_ADMIN_EMAIL` / `FIRST_ADMIN_PASSWORD` **before first startup**.

### Tests

```bash
cd backend && PYTHONPATH=. pytest -q      # backend engine tests
cd frontend && npx tsc --noEmit && npm run build   # frontend typecheck + build
```

---

## Environment variables

**Backend** (`backend/.env`)

| Variable                      | Purpose                                        |
| ----------------------------- | ---------------------------------------------- |
| `SECRET_KEY`                  | JWT signing key (use a long random string)     |
| `DATABASE_URL`                | Postgres URL; omit for SQLite local dev        |
| `CORS_ORIGINS`                | Comma-separated allowed frontend origins       |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT lifetime (default 1440)                     |
| `FIRST_ADMIN_EMAIL/PASSWORD`  | Seeded admin credentials                        |
| `DATASET_PATH`                | Path to the `.xlsx` cutoff dataset              |

**Frontend** (`frontend/.env.local`)

| Variable              | Purpose                        |
| --------------------- | ------------------------------ |
| `NEXT_PUBLIC_API_URL` | Base URL of the backend `/api` |

---

## API reference (prefix `/api`)

| Method | Path                               | Auth   | Description                        |
| ------ | ---------------------------------- | ------ | --------------------------------- |
| POST   | `/auth/register`                   | —      | Register (status → pending)       |
| POST   | `/auth/login`                      | —      | Login, returns JWT                |
| GET    | `/users/me`                        | user   | Current profile                   |
| POST   | `/predict`                         | user   | Run a prediction (saved)          |
| GET    | `/predict/{id}/pdf`                | user   | Download PDF report               |
| GET    | `/history`                         | user   | My prediction history             |
| DELETE | `/history/{id}`                    | user   | Delete a history entry            |
| GET    | `/admin/stats`                     | admin  | Dashboard counters                |
| GET    | `/admin/users`                     | admin  | List users (`?status_filter=`)    |
| POST   | `/admin/users/{id}/approve`        | admin  | Approve user                      |
| POST   | `/admin/users/{id}/reject`         | admin  | Reject user                       |
| POST   | `/admin/users/{id}/enable|disable` | admin  | Enable / disable account          |
| POST   | `/admin/users/{id}/reset-password` | admin  | Reset a user's password           |
| DELETE | `/admin/users/{id}`                | admin  | Delete user                       |
| GET    | `/admin/export/users.xlsx`         | admin  | Export registered users           |
| GET    | `/admin/export/predictions.xlsx`   | admin  | Export predictions                |
| GET    | `/admin/history`                   | admin  | All predictions (`?search=&sort=`)|
| GET    | `/dataset/stats`                   | admin  | Dataset statistics                |
| POST   | `/dataset/upload`                  | admin  | Replace dataset (auto-backup)     |
| GET    | `/dataset/backups`                 | admin  | List backups                      |
| POST   | `/dataset/restore/{name}`          | admin  | Restore a backup                  |

Interactive docs live at `/docs` (Swagger UI).

---

## Deployment

### Backend + database → Render

1. Push this repo to GitHub.
2. In Render, **New → Blueprint** and point it at the repo. `render.yaml` provisions the
   web service and a free Postgres instance.
3. Set the `FIRST_ADMIN_PASSWORD` secret and update `CORS_ORIGINS` to your Vercel URL.
4. The dataset ships in `data/`; the app reads it via `DATASET_PATH`.

### Frontend → Vercel

1. In Vercel, **New Project** → import the repo, set **Root Directory** to `frontend`.
2. Add env var `NEXT_PUBLIC_API_URL = https://<your-render-service>.onrender.com/api`.
3. Deploy. Then set the backend's `CORS_ORIGINS` to the Vercel domain and redeploy the API.

### CI

`.github/workflows/ci.yml` runs the backend test suite and a frontend typecheck + build on
every push / PR to `main`.

---

## Security

- Bcrypt password hashing, JWT bearer auth, role- and status-based access guards.
- Rate limiting (SlowAPI), CORS allow-list, and hardening headers
  (`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `X-XSS-Protection`).
- SQLAlchemy ORM parameterises queries (SQL-injection safe); React escapes output (XSS safe).
- Serve over HTTPS in production (Render and Vercel provide TLS by default).

---

## License

Provided as-is for educational and internal use. Verify all predictions against official
counselling data before acting on them.
