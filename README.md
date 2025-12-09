# F1 Picks

A free-to-play prediction web app for Formula 1 fans who want to compete socially with friends and groups. Users make predictions before race sessions, which are then automatically scored once official timing and telemetry data becomes available via the FastF1 library.

🌐 **Live App**: [https://f1-picks-frontend.vercel.app](https://f1-picks-frontend.vercel.app)  
🔧 **API**: [https://f1picks-backend.fly.dev](https://f1picks-backend.fly.dev)

## 🏎️ Features

- **Telemetry-Aware Predictions**: Predict race winners, podium finishes, fastest laps, sector times, and pit windows
- **Post-Session Auto-Scoring**: Transparent scoring using FastF1 data (30-120 minutes post-session)
- **Global & League Leaderboards**: Compete globally or create private leagues
- **Real-time Updates**: Live leaderboard updates after scoring completes
- **Analytics & Transparency**: Hit rate, average margin, and per-prop scoring breakdown
- **Social Features**: Camera integration for profile photos and QR code league joining

## 🏗️ Architecture

This is a monorepo containing:

- **Frontend** (`/frontend`): Next.js 15 with TypeScript and Tailwind CSS
- **Backend** (`/backend`): FastAPI with Python 3.13
- **Shared** (`/shared`): Common utilities, types, and configurations
- **Worker**: Python worker for FastF1 data ingestion (post-session)

### Tech Stack

- **Frontend**: Next.js 15, React 19, TypeScript 5, Tailwind CSS, shadcn/ui
- **Backend**: FastAPI, SQLAlchemy, Alembic, asyncpg, Python 3.13
- **Database**: PostgreSQL (Supabase)
- **Data Source**: FastF1 library for F1 telemetry and results
- **Authentication**: Supabase Auth (email/password, OAuth)
- **Deployment**: Vercel (frontend), Fly.io (backend), automated via GitHub Actions
- **CI/CD**: GitHub Actions with Release Please
- **Package Management**: npm workspaces (frontend), uv (backend)

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm 9+
- Python 3.13+
- PostgreSQL
- Git
- Docker (optional, for containerized development)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd F1Picks
   ```

2. **Install dependencies**
   ```bash
   # Install all workspace dependencies
   npm ci --include-workspace-root
   
   # Install backend dependencies
   cd backend
   pip install -r requirements.txt
   pip install -r dev-requirements.txt
   cd ..
   ```

3. **Environment Setup**
   ```bash
   # Backend environment
   cd backend
   cp .env.example .env
   # Edit .env with your configuration:
   # - DATABASE_URL (PostgreSQL connection string)
   # - SUPABASE_URL and SUPABASE_ANON_KEY
   # - SECRET_KEY for JWT tokens
   
   # Frontend environment
   cd ../frontend
   cp .env.example .env
   # Edit .env with:
   # - NEXT_PUBLIC_SUPABASE_URL
   # - NEXT_PUBLIC_SUPABASE_ANON_KEY
   # - NEXT_PUBLIC_API_URL (backend URL)
   ```

4. **Database Setup**
   ```bash
   # Run database migrations
   cd backend
   alembic upgrade head
   
   # Optional: Seed development data
   python scripts/seed_dev_data.py
   ```

5. **Start Development Servers**
   ```bash
   # Start both frontend and backend
   npm run dev
   
   # Or start individually:
   npm run dev:frontend  # http://localhost:3000
   npm run dev:backend   # http://localhost:8000
   ```

## 📁 Project Structure

```
F1Picks/
├── frontend/                 # Next.js frontend application
│   ├── src/
│   │   ├── app/             # App router pages (home, leagues, profile)
│   │   ├── components/      # React components (ui, layout)
│   │   ├── contexts/        # React contexts (auth)
│   │   └── lib/             # API client, utilities
│   ├── public/              # Static assets
│   └── package.json
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── models/          # SQLAlchemy database models
│   │   ├── repositories/    # Data access layer
│   │   ├── routers/         # API endpoints (users, leagues, picks, etc.)
│   │   ├── config.py        # Application settings
│   │   ├── database.py      # Database connection
│   │   └── main.py          # FastAPI app with CORS
│   ├── alembic/             # Database migrations
│   ├── scripts/             # Utility scripts (seed data, migrations)
│   ├── tests/               # Backend tests
│   ├── requirements.txt     # Python dependencies
│   └── fly.toml             # Fly.io deployment config
├── worker/                  # FastF1 data ingestion worker
│   ├── app/
│   │   ├── fastf1_client.py # FastF1 integration
│   │   ├── scheduler.py     # Celery task scheduler
│   │   └── database.py      # Database connection
│   └── requirements.txt
├── shared/                  # Shared TypeScript types
├── .github/workflows/       # CI/CD workflows
│   ├── ci.yml              # PR validation
│   ├── deploy.yml          # Production deployment
│   └── daily-data-sync.yml # Scheduled data updates
├── package.json            # Root package.json with workspaces
└── README.md
```

## 🛠️ Development

### Available Scripts

- `npm run dev` - Start both frontend and backend in development mode
- `npm run build` - Build shared package and frontend for production
- `npm run lint` - Run ESLint on frontend
- `npm run lint:backend` - Run Ruff linting on backend
- `npm run format:backend` - Format backend code with Ruff

### Code Quality

- **Frontend**: ESLint, TypeScript
- **Backend**: Ruff (linting and formatting)
- **CI/CD**: Automated testing on PRs, deployment on merge to main

## 🚢 Deployment

### CI/CD Pipeline

The project uses a multi-workflow GitHub Actions setup:

1. **CI Pipeline** (`ci.yml`) - Runs on PRs to `main`
   - Frontend: Lint, build, and validate
   - Backend: Lint with Ruff, test FastAPI startup
   - Does NOT deploy

2. **Deploy** (`deploy.yml`) - Runs on merge to `main`
   - Deploys backend to Fly.io using Docker
   - Frontend deploys automatically via Vercel GitHub integration

3. **Release Please** (`release-please.yml`) - Automated versioning
   - Creates release PRs with changelog generation
   - Bumps versions across all workspace packages
   - Follows Conventional Commits specification

### Frontend (Vercel)
- **URL**: https://f1-picks-frontend.vercel.app
- Automatic deployment from `main` branch via Vercel GitHub integration
- Environment variables configured in Vercel dashboard:
  - `NEXT_PUBLIC_API_URL`
  - `NEXT_PUBLIC_SUPABASE_URL`
  - `NEXT_PUBLIC_SUPABASE_ANON_KEY`

### Backend (Fly.io)
- **URL**: https://f1picks-backend.fly.dev
- Deployed using `fly.toml` configuration
- Triggered by `deploy.yml` workflow on merge to `main`
- Database migrations run automatically on deployment
- Environment variables configured via Fly.io secrets:
  - `DATABASE_URL`
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `SECRET_KEY`

## 🧪 Testing

### Frontend
```bash
cd frontend
npm run test
```

### Backend
```bash
cd backend
pytest
```

### CI/CD Testing
All tests run automatically on pull requests via GitHub Actions.

## 📊 Data Flow

1. **Schedule Ingestion**: Worker fetches F1 schedule from FastF1
2. **User Predictions**: Users make picks before session start times
3. **Session Execution**: F1 sessions run (qualifying, practice, race)
4. **Data Availability**: FastF1 publishes results/telemetry (30-120 min delay)
5. **Auto-Scoring**: Worker ingests data, calculates scores, updates leaderboards
6. **User Notification**: Users see updated scores and leaderboard positions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes using [Conventional Commits](https://www.conventionalcommits.org/)
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `chore:` for maintenance tasks
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
6. CI pipeline will automatically run tests and validation
7. After merge, Release Please will handle versioning and changelog generation

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏁 Current Status & Roadmap

### ✅ Completed
- [x] Full-stack application deployed (Frontend on Vercel, Backend on Fly.io)
- [x] Database schema with 8 models (User, League, Event, Pick, Result, Score, etc.)
- [x] Supabase authentication integration
- [x] League management (create, join, view members)
- [x] User profiles and leaderboards
- [x] CI/CD pipeline with automated deployments
- [x] CORS configuration for production
- [x] Database migrations with Alembic

### 🚧 In Progress
- [ ] FastF1 data ingestion worker
- [ ] Automated scoring system
- [ ] Real-time leaderboard updates

### 📋 Planned
- [ ] Advanced telemetry predictions (sector times, pit windows)
- [ ] QR code league joining
- [ ] Camera integration for profile photos
- [ ] Analytics dashboard (hit rate, average margin)
- [ ] Seasonal leaderboards and playoffs
- [ ] Mobile app (React Native)
