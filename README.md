# F1 Picks

A free-to-play prediction web app for Formula 1 fans who want to compete socially with friends and groups. Users make predictions before race sessions, which are then automatically scored once official timing and telemetry data becomes available via the FastF1 library.

## 🏎️ Features

- **Telemetry-Aware Predictions**: Predict race winners, podium finishes, fastest laps, sector times, and pit windows
- **Post-Session Auto-Scoring**: Transparent scoring using FastF1 data (30-120 minutes post-session)
- **Global & League Leaderboards**: Compete globally or create private leagues
- **Real-time Updates**: Live leaderboard updates after scoring completes
- **Analytics & Transparency**: Hit rate, average margin, and per-prop scoring breakdown
- **Social Features**: Camera integration for profile photos and QR code league joining

## 🏗️ Architecture

This is a monorepo containing:

- **Frontend** (`/frontend`): Next.js with TypeScript and Tailwind CSS
- **Backend** (`/backend`): FastAPI with Python 3.9+
- **Shared** (`/shared`): Common utilities, types, and configurations
- **Worker**: Python worker for FastF1 data ingestion (post-session)

### Tech Stack

- **Frontend**: Next.js, TypeScript, Tailwind CSS, React
- **Backend**: FastAPI, SQLAlchemy, Alembic, asyncpg
- **Database**: PostgreSQL
- **Data Source**: FastF1 library for F1 telemetry and results
- **Authentication**: Firebase (email/password, Google/Apple)
- **Deployment**: Vercel (frontend), Fly.io (backend + workers)
- **CI/CD**: GitHub Actions

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm 9+
- Python 3.9+
- PostgreSQL
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd F1Picks
   ```

2. **Install dependencies**
   ```bash
   # Install root dependencies
   npm install
   
   # Install backend dependencies
   npm run install:backend
   ```

3. **Environment Setup**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit .env with your configuration
   # - Database connection string
   # - Firebase configuration
   # - API keys
   ```

4. **Database Setup**
   ```bash
   # Run database migrations
   cd backend
   alembic upgrade head
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
│   │   ├── app/             # App router pages
│   │   ├── components/      # React components
│   │   └── lib/            # Frontend utilities
│   ├── public/             # Static assets
│   └── package.json
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── main.py         # FastAPI app
│   ├── alembic/            # Database migrations
│   ├── tests/              # Backend tests
│   └── requirements.txt
├── shared/                  # Shared utilities and types
├── .github/workflows/       # CI/CD workflows
├── package.json            # Root package.json with workspaces
└── README.md
```

## 🛠️ Development

### Available Scripts

- `npm run dev` - Start both frontend and backend in development mode
- `npm run build` - Build the frontend for production
- `npm run lint` - Run linting for both frontend and backend
- `npm run format` - Format code for both frontend and backend
- `npm run test` - Run tests for both frontend and backend

### Code Quality

- **Frontend**: ESLint, Prettier, TypeScript
- **Backend**: Black, isort, mypy, flake8
- **Pre-commit hooks**: Automated formatting and linting

## 🚢 Deployment

### Frontend (Vercel)
- Automatic deployment from `main` branch
- Environment variables configured in Vercel dashboard

### Backend (Fly.io)
- Deployed using `fly.toml` configuration
- Database and environment variables configured via Fly.io

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
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏁 Roadmap

- [ ] MVP: Global leaderboard with basic telemetry props
- [ ] Private leagues and invitations
- [ ] Advanced telemetry props (undercuts, anomaly detection)
- [ ] Seasonal leaderboards and playoffs
- [ ] Mobile app (React Native)
- [ ] Country-based leaderboards
