# M1 — Full-Stack & AI Lead — Website Status

## Role
Build and maintain the Next.js frontend (`website/`) and FastAPI backend (`api/`).

## ✅ Completed
### Frontend (`website/`)
- Landing page — hero, features grid, how-it-works, CTA
- Pricing page — 3-tier comparison table
- Login & Signup pages — multi-step form with profile fields
- Dashboard — overview with engine status cards, download CTA
- Download page — OS selector with dynamic install command + token
- Profile page — edit name, age, job, interests, goals, AI name
- Settings page — plan info, privacy section, danger zone
- Navbar + Sidebar components
- API client (`lib/api.ts`) with auth token handling
- Next.js rewrites for engine (port 5743) and backend (port 8000)

### Backend (`api/`)
- User auth — signup, login, JWT token, password hashing
- Profile CRUD — get/update profile fields
- Subscriptions — create, status check, free/student/lifetime plans
- Installer system — generate token, serve install scripts, validate tokens
- Webhook stubs — Stripe + Razorpay
- PostgreSQL async models — User, Subscription, Clone, Payment

## 📋 Pending
- [ ] **Stripe/Razorpay live integration** — currently uses placeholder (direct activation)
- [ ] **Dashboard pages polish** — add memory viewer, theme selector, skill toggles
- [ ] **Error handling improvements** — better user-facing error messages
- [ ] **Mobile responsiveness** — test and fix on smaller screens
- [ ] **Forgot password** — password reset flow
- [ ] **Email verification** — verify email after signup

## 🎯 Next Step
Fix the signup flow error (check browser Network tab → find failing API call → fix backend/frontend)
