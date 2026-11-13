# M1 — Full-Stack & AI Lead — Website Status

## Role
Build and maintain the Next.js frontend (`website/`) and FastAPI backend (`api/`).

## ✅ Completed
### Frontend (`website/`)
- Landing page — hero, features grid, how-it-works, CTA
- Pricing page — 3-tier comparison table
- Login & Signup pages — multi-step form with step-by-step validation, safe age parsing, and robust error banners
- Dashboard Overview — engine status cards with live polling, quick launch tiles, memory metrics, download CTA
- Theme Selector — interactive selector for all 6 official themes (Blob, Cyber Terminal, Voice Spectrum, Drum Waves, Hologram Orb, Minimal Dot) with visual mockups and profile sync
- Skill Toggles — accessible switch toggles for autonomous AI modules (PC Control, Voice Always-On, VS Code Runner, Multilingual Perception, Universal Messaging, Media Control)
- Download page — OS selector with dynamic install command + token
- Profile page — edit name, age, job, interests, goals, AI name with validation
- Settings page — integrated Theme Selector, Skill Toggles, plan status, privacy declaration, danger zone
- Navbar + Sidebar components — responsive desktop & mobile hamburger navigation drawer
- API client (`lib/api.ts`) with auth token handling & refresh queue
- Next.js rewrites for engine (port 5743) and configurable backend (port 8001 / env `BACKEND_PORT`)

### Backend (`api/`)
- User auth — signup, login, JWT token, password hashing
- Profile CRUD — get/update profile fields
- Subscriptions — create, status check, free/student/lifetime plans
- Installer system — generate token, serve install scripts, validate tokens
- Webhook stubs — Stripe + Razorpay
- PostgreSQL async models — User, Subscription, Clone, Payment

## 📋 Pending
- [ ] **Stripe/Razorpay live integration** — currently uses placeholder (direct activation)
- [ ] **Memory Viewer dedicated panel** — 3-tier browser for Short-Term, Long-Term (ChromaDB), and Deep memories
- [ ] **Forgot password** — password reset flow
- [ ] **Email verification** — verify email after signup

## 🎯 Next Step
Implement dedicated 3-tier Memory Viewer panel on Dashboard or Stripe/Razorpay live checkout.
