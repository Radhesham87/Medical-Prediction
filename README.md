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

## Prediction modules (v2)

The portal now offers four counselling types, chosen from the landing page:

| Module | Route | Dataset | Filters | PDF columns |
| --- | --- | --- | --- | --- |
| AIIMS | `/aiims` | `data/AIIMS_Cutoff.xlsx` | Category, State | Institute, State, AIR, Score |
| All India (85%) | `/all-india` | `data/All_India_Cutoff.xlsx` | Degree (MBBS/BDS), Category, State | Institute, Degree, State, AIR, Score |
| Maharashtra (85%) | `/predict` | `data/All_Medical_College_Last_Cutoff.xlsx` | Degree (MBBS/BDS/BAMS/BHMS/BUMS/BPTH), Category | College Code, College Name, Status, Degree, AIR, Score, SML |
| Deemed | `/deemed` | `data/Deemed_Cutoff.xlsx` | Degree (MBBS/BDS), State | Institute, Degree, State, AIR, Score |

Every module takes a student name and a NEET score **or** AIR, shows a ranked on-screen
result graded High/Moderate/Low, and offers a downloadable A4 PDF.

Backend endpoints for the three institute modules are stateless:
`GET /api/institute/{module}/options`, `POST /api/institute/{module}/predict`,
`POST /api/institute/{module}/pdf` where `{module}` is `aiims`, `all-india` or `deemed`.
The Maharashtra module keeps its existing `/api/predict` endpoint and history.

## Device tracking (v3)

A fixed, pre-approved **regular-user** login is seeded automatically and can be used
on multiple devices:

- Email: `jadav784@gmail.com`
- Password: `Jadav@95`

Every login records the device (browser + OS + IP) in a `login_sessions` table.
In the **Admin panel → Users** tab, each account now shows a **Devices** count;
clicking it opens a dialog listing every connected device with its last-seen time,
and an admin can **Remove** a device (forcing it to log in again).

Because a single shared password is used across devices, the app cannot identify
individual people — the device count (deduplicated per browser + IP) is the most it
can show, and anyone holding the password counts as one device.

New admin endpoints: `GET /api/admin/users/{id}/devices` and
`DELETE /api/admin/users/{id}/devices/{session_id}`.

## Per-module access + usage (v4)

- **All India card renamed** to **All India (15%)** (label only; same data).
- **Category** is now a single-select dropdown (one at a time) in every module.
- **State** is a single-select dropdown with an **"All states"** option.
- **Maharashtra** now supports three inputs: **NEET Score / SML / All-India Rank (AIR)**.
- **Per-module approval:** each user has four independent permissions (AIIMS,
  All India 15%, Maharashtra 85%, Deemed). A brand-new approved user starts with
  **all modules OFF** and sees "waiting for admin approval" on each until the admin
  grants access. The shared `jadav784@gmail.com` account is seeded with all four ON.
- **Admin panel → Users → "Module access"** (slider icon): tick the modules a user
  may use; the dialog also shows how many times they used each module.

New endpoints: `PUT /api/admin/users/{id}/modules` (set the four booleans).
Every prediction (all modules) is logged to `prediction_usage` for the counts.
On existing databases, the `predictions.sml` column is added automatically at startup.

## Per-module admin dashboards (v5)

**Admin panel → Modules tab**: a separate dashboard block for each predictor —
AIIMS, All India (15%), Maharashtra (85%), Deemed — in the same stat-card format
as the main dashboard. Each shows: Users with Access, Users Who Used It,
Predictions, Today's Predictions, Downloads.

Notes on the numbers:
- Maharashtra keeps its full history (all past predictions and downloads count).
- AIIMS / All India / Deemed counters start from this deploy — those modules
  never logged predictions or downloads before, so past activity there cannot
  be counted retroactively.
- PDF downloads in AIIMS / All India / Deemed are now logged (new `kind` column
  on `prediction_usage`, added automatically on startup for existing databases).

New endpoint: `GET /api/admin/module-stats`.

## Veterinary module (v7)

Fifth predictor: **Veterinary (B.V.Sc & A.H)** — landing-page card + `/veterinary` page.
- Data: `data/Veterinary_Cutoff.xlsx` (sheet "Round 3 Cutoff", 291 rows, 58 colleges,
  State column included; 2 rows with "-" cutoffs are skipped automatically).
- Flow: Name → Marks or Rank → Category (single-select; State optional, default all) → results on screen → PDF.
- PDF columns: Sr, Institute Name, State, Course, Marks, Rank — sorted by Rank (best first).
- Per-module approval applies: new users need the admin to tick "Veterinary"
  (existing databases get the new permission column added automatically on startup;
  the shared jadav784 account gets it ON). Appears in the Modules dashboards,
  today's-per-module breakdown, usage chart, and PREDS totals.

## Branded PDF account (v8)

A fixed counselling account is seeded whose PDF downloads carry their own branding:

- Email: `radheshamtaynath8@gmail.com` · Password: `Radhe@87` (approved, all modules ON,
  credentials enforced at startup like the shared account).
- Every PDF this account downloads shows the headline
  **"DR SHINDE EDUCATION SERVICES PVT LTD Latur"**:
  - Maharashtra (85%) PDFs use a full counselling-report layout: brand header +
    "NEET PREDICTION REPORT" + date, a student card (Name, Stream/Degree, AIR/Score/SML,
    Reserved Category with Gender), a prediction analysis summary (High/Moderate/Low/Total),
    and a line-separated college table (College with code · status · state, Category,
    Cutoff, Your Rank, Chance) sorted most-competitive first.
  - AIIMS / All India / Deemed / Veterinary PDFs keep their layouts but the
    title and footer show the brand.
- All other users' PDFs are unchanged. Branding is mapped per-email in
  `backend/app/core/branding.py` — more branded accounts can be added there.

## Letterhead PDF account (v9)

A second branded account is seeded: `jadhavs785@gmail.com` · Password: `Bright2026`.
Approved, all modules ON, credentials enforced at startup.

Every PDF this account downloads is stamped with the **Bright Future Education
Group letterhead**: the header strip (logo + "Dr Sagar Jadhav Sir · MBBS MD ·
Your Medical Admission partner") at the **top of the first page**, and the
offices/contact block at the **bottom of the last page**. Other pages carry a
small "Generated via Bright Future Education Group · Page N of M" footer.
Applies to all five modules' PDFs; every other user's PDFs are unchanged.

Assets live in `backend/app/assets/` (extracted from the supplied letterhead
sample); per-email mapping in `backend/app/core/branding.py`.


## Bright Future counselling-style body (v10)

- The `jadhavs785@gmail.com` password changed to **Bright2026** (enforced automatically
  at startup, including on existing databases).
- Its **Maharashtra (85%) PDF** now combines both samples: the Bright Future letterhead
  images stay on the **top of the first page** and the **bottom of the last page**, and the
  report body between them uses the counselling-report format — "NEET PREDICTION REPORT"
  + date line, student card (Name, Stream/Degree, AIR/Score/SML, Reserved Category with
  Gender), Prediction Analysis Summary boxes, and the line-separated college table
  (College with code · status · state, Category, Cutoff, Your Rank, Chance) sorted
  most-competitive first.
- Its other module PDFs keep the letterhead with the standard layouts. All other
  accounts are unchanged.

## Shared account gets the Bright Future report (v11)

The shared multi-device account `jadav784@gmail.com` (password unchanged: `Jadav@95`)
now downloads the same branded PDFs as the Bright Future account: letterhead header
strip on the top of the first page, offices/contact block on the bottom of the last
page, and the counselling-report body (report label + date, student card, analysis
summary, line-separated college table) in between. Applies to all five modules
(institute modules keep their standard tables inside the letterhead). Dr Shinde's
account and all other users are unchanged.

## Watermark for the shared account (v12)

PDFs downloaded by `jadav784@gmail.com` (login unchanged: `Jadav@95`) now also carry
the **Bright Future logo as a faint watermark** centered behind the content of every
page (pre-faded ~10% so text stays fully readable), in addition to the letterhead
strips and counselling-report body. Asset: `backend/app/assets/brightfuture_watermark.jpg`.
The `jadhavs785@gmail.com` account keeps letterhead without the watermark; Dr Shinde
and normal users are unchanged.
