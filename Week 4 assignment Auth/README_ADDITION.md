# Task CRUD API — Week 4: Auth with Supabase

Adds Supabase Auth on top of the Postgres task API: signup, login, logout, and a reusable
bearer-token guard protecting two routes.

## Setup
1. Create a free Supabase project at supabase.com.
2. Authentication → Sign In / Providers → Email → turn OFF "Confirm email" (local dev only).
3. Project Settings → API → copy Project URL and anon key (never service_role).
4. cp .env.example .env and fill in SUPABASE_URL / SUPABASE_KEY.

## How to run
docker compose up

## Endpoints
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /auth/signup | none | Create account |
| POST | /auth/login | none | Get access token |
| POST | /auth/logout | Bearer | End session |
| GET | /public/info | none | Open data |
| GET | /protected/profile | Bearer | Your user info |
| GET | /protected/dashboard | Bearer | Second guarded route |
| GET/POST/PUT/DELETE /tasks | none | Same as Week 3 |

## Example
curl -i -X POST http://localhost:8000/auth/signup -H "Content-Type: application/json" -d "{\"email\":\"test@example.com\",\"password\":\"password123\"}"

curl -i http://localhost:8000/protected/profile -H "Authorization: Bearer <ACCESS_TOKEN>"

## Swagger UI
Visit http://localhost:8000/docs — click Authorize, paste your token, Try it out.

## AI vs me
<!-- fill in after Stage 7 -->
