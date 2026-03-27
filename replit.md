# Workspace

## Overview

pnpm workspace monorepo using TypeScript + Python Flask app (299+ Ai Canli Analiz).

## Stack

- **Monorepo tool**: pnpm workspaces
- **Node.js version**: 24
- **Package manager**: pnpm
- **TypeScript version**: 5.9
- **API framework**: Express 5 (api-server) + Flask (Python)
- **Database**: PostgreSQL + Drizzle ORM (Node), SQLite (Python Flask app)
- **Validation**: Zod (`zod/v4`), `drizzle-zod`
- **API codegen**: Orval (from OpenAPI spec)
- **Build**: esbuild (CJS bundle)

## Structure

```text
artifacts-monorepo/
├── artifacts/              # Deployable applications
│   └── api-server/         # Express API server
├── python/                 # Python Flask app (299+ Ai Canli Analiz)
│   ├── main.py             # Flask app - Ana uygulama (port 5000)
│   ├── api_canli.py        # API-Football entegrasyonu
│   ├── ligler.py           # Lig listesi ve mappingleri
│   ├── market_olusturucu.py# Bahis market olusturucu
│   ├── veri_bot.py         # Veri guncelleme botu + zamanlayici
│   ├── index.html          # Ana frontend
│   ├── admin.html          # Admin paneli
│   ├── api_veri.json       # Veri cache dosyasi
│   └── veritabani.db       # SQLite kullanici veritabani
├── lib/                    # Shared libraries
│   ├── api-spec/           # OpenAPI spec + Orval codegen config
│   ├── api-client-react/   # Generated React Query hooks
│   ├── api-zod/            # Generated Zod schemas from OpenAPI
│   └── db/                 # Drizzle ORM schema + DB connection
├── scripts/                # Utility scripts
├── pyproject.toml          # Python dependencies (flask, schedule, requests)
├── pnpm-workspace.yaml     # pnpm workspace
├── tsconfig.base.json      # Shared TS options
├── tsconfig.json           # Root TS project references
└── package.json            # Root package
```

## Python App (299+ Ai)

### Data Flow
1. **Primary**: API-Football (api-sports.io) fetches real fixtures for today + tomorrow
2. **Fallback**: Simulated data generator with realistic schedules if API fails
3. **Other sports**: Basketball, Volleyball, Tennis use simulated data (API covers football only)
4. **Auto-refresh**: Every 6 hours + midnight (00:00, 00:05 IST) via scheduler
5. **Client refresh**: Every 5 minutes + on day change detection

### Key Features
- 60+ betting markets per football match (MS, Alt/Üst, Handikap, Korner, Kart, Tam Skor etc.)
- AI probability analysis for each market
- User auth system (register/login with SQLite)
- Admin panel (/admin) with stats, messages, users management
- "Günün Kuponu" and "Günün Kombinesi" features
- Istanbul UTC+3 timezone throughout
- League filtering, date tabs, sport tabs
- Profile photo upload
- Coupon save/load/delete system (30-day retention)

### Role System (Hierarchy)
- **Kurucu** (Founder): Full access, can manage admins, cannot be deleted/changed
- **Admin**: Can manage users (VIP/Normal), view admin panel, cannot touch kurucu
- **VIP**: Paid tier user (assigned by admin/kurucu)
- **Kullanıcı** (Normal): Standard free user

### Email / Verification
- SMTP via env vars: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`
- If SMTP not configured, codes printed to console (simulated)
- Email verification: 6-digit code, 10-min expiry, 5-attempt brute-force protection
- Password reset: Same code system, available from login page
- Old codes invalidated when new ones sent

### API Integration (api_canli.py)
- Uses `API_FOOTBALL_KEY` environment secret
- Maps 55+ API-Football league IDs to internal system
- Free plan: 100 requests/day, access to today + tomorrow fixtures
- Generates AI analysis/odds from real team data
- Falls back to veri_bot.py simulated data on API failure

### Auth
- Kurucu (founder): username=`admin`, password=`admin`
- Session: cookie-based, SameSite=Lax, 7-day lifetime
- SECRET_KEY from env or hardcoded fallback

### Workflows
- `Start application` - Flask app (port 5000) - Ana uygulama
- `artifacts/api-server: API Server` - Express proxy (port 8080)

## TypeScript & Composite Projects

Every package extends `tsconfig.base.json` which sets `composite: true`. The root `tsconfig.json` lists all packages as project references.

## Root Scripts

- `pnpm run build` — runs `typecheck` first, then recursively runs `build` in all packages that define it
- `pnpm run typecheck` — runs `tsc --build --emitDeclarationOnly` using project references

## Packages

### `artifacts/api-server` (`@workspace/api-server`)

Express 5 API server. Routes live in `src/routes/`.

### `lib/db` (`@workspace/db`)

Database layer using Drizzle ORM with PostgreSQL.

### `lib/api-spec` (`@workspace/api-spec`)

Owns the OpenAPI 3.1 spec and Orval config.
Run codegen: `pnpm --filter @workspace/api-spec run codegen`

### `scripts` (`@workspace/scripts`)

Utility scripts package.
