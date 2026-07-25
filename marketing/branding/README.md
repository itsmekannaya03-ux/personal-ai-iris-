# Marketing & Deployment — Member 10

## Your Job
- Design the logo and brand identity
- Create posters and promotional materials
- Write landing page content and taglines
- Prepare installation guide for end users
- Define future scope and business model
- Coordinate with Member 4 on visual branding

---

## 1. Brand Identity

### Name
**IGRIS AI** — Your AI, Your Privacy, Your Way

### Tagline Ideas
- "Your AI. Your PC. Your Privacy."
- "The AI that lives on your machine."
- "Jarvis for everyone. Private by design."
- "No cloud. No tracking. Just you and your AI."

### Color Palette (Already in code)
```
Primary:   #4F46E5 (Indigo)
Hover:     #6366F1 (Lighter Indigo)
Dark bg:   #0A0A0F (Near-black)
Card bg:   rgba(255,255,255,0.05) (Subtle white)
Text:      rgba(255,255,255,0.5-1.0)
Accent:    #06B6D4 (Cyan, optional)
```

---

## 2. Logo Requirements

Create these logo files in `marketing/logo/`:
| File | Size | Format |
|------|------|--------|
| `igris-logo.svg` | Vector | SVG |
| `igris-logo-192.png` | 192x192 | PNG (favicon) |
| `igris-logo-512.png` | 512x512 | PNG (app icon) |
| `igris-banner.png` | 1200x630 | PNG (social media) |

### Logo Design Ideas
- **Icon:** A stylized "I" that looks like a brain circuit / AI node
- **OR:** A subtle orb/glow that represents the AI presence
- **Style:** Minimal, gradient indigo-to-cyan, tech feel
- **Font:** Inter Bold or custom geometric sans-serif

---

## 3. Poster Content

Create 2-3 promotional posters for the college expo:

### Poster 1: "Meet IGRIS — Your Private AI"
```
Headline: Meet IGRIS
Subheadline: The AI that lives on YOUR machine.
Bullet points:
- 100% Local — No cloud, no tracking
- Full PC Control — Apps, files, system
- Voice + CLI + Web Dashboard
- Learns you over time (3-tier memory)
- One-command install
- From ₹99/month or ₹999 lifetime
QR Code → github.com/igris-ai/igris
```

### Poster 2: "Privacy First AI"
```
Headline: Your Data Stays Yours.
Body:
Every major AI sends your data to the cloud.
ChatGPT, Siri, Alexa — they all store your conversations.
IGRIS is different: Zero data leaves your PC.
Forever. Private. Encrypted. Yours only.
QR Code → igris.ai
```

---

## 4. Landing Page Content (for Member 1)

Provide Member 1 with final text for the landing page:

### Hero Section
```
Headline: Your AI. Your PC. Your Privacy.
Subheadline: Meet IGRIS — the first truly private AI assistant
that runs 100% on your machine. No cloud. No tracking.
Just you and your AI.
CTA: Get Started Free
```

### Features Section
```
Feature 1: Privacy First
"Zero data ever leaves your PC. Not even we can see your conversations."

Feature 2: 3-Tier Memory
"IGRIS remembers what matters — short-term for sessions,
long-term for habits, deep for who you are."

Feature 3: Total PC Control
"Open apps, find files, check system stats, search the web.
Your AI controls your computer."

Feature 4: Voice + CLI + UI
"Talk to it, type to it, or use the beautiful web dashboard.
All three modes, one AI, always in sync."

Feature 5: Customizable
"Name it ARIA, MAX, JARVIS. Choose from 6 themes.
Make it yours."

Feature 6: One Command Install
"curl -fsSL https://igris.ai/install | sh"
"Done. Your AI is ready."
```

---

## 5. Installation Guide

```markdown
# IGRIS AI — Installation Guide

## System Requirements
- Windows 10/11, macOS 13+, or Linux (Ubuntu 22+)
- 8GB RAM minimum (16GB recommended)
- 10GB free disk space
- Internet connection (for initial setup only)

## One-Command Install

### Windows (PowerShell)
```powershell
curl -fsSL "https://igris.ai/api/install/script/windows/YOUR_TOKEN" | iex
```

### macOS / Linux
```bash
curl -fsSL "https://igris.ai/api/install/script/mac/YOUR_TOKEN" | sh
```

## What Happens
1. Ollama is installed (local AI runtime)
2. LLaMA 3.2 model is downloaded (~2GB)
3. Your personal profile is injected as AI's DNA
4. ChromaDB memory database is set up
5. AI engine starts on localhost:5743
6. Your AI greets you by name!

## After Installation
- **Dashboard:** Open http://localhost:5743
- **CLI:** Type `ai "your message"` in terminal
- **Voice:** Say "hey igris" followed by your command
```

---

## 6. Business Model

### Revenue Streams
| Stream | Details |
|--------|---------|
| Student Pro (₹99/mo) | Subscription — recurring revenue |
| Lifetime (₹999) | One-time payment — higher upfront |
| Future: Enterprise | Team plans, organization deployment |
| Future: Custom Models | Fine-tuned models for specific use cases |

### Target Audience
1. **College Students** — Privacy-conscious, affordable, study aid
2. **Developers** — CLI power users, local-first mindset
3. **Privacy Advocates** — People who avoid cloud services
4. **Power Users** — People who want PC automation

### Competitive Advantage
- No cloud costs (zero server expenses after website)
- No per-user model training cost (clone architecture)
- Organic growth through tech communities
- Student-friendly pricing (₹99 = ~$1.20)

---

## 7. Distribution Channels

| Channel | Strategy |
|---------|----------|
| GitHub | Open-source releases, README, issues |
| Devpost/ProductHunt | Launch post for exposure |
| College Tech Fests | Demo at events |
| LinkedIn/Twitter | Dev blogs, feature highlights |
| YouTube | Demo video, installation tutorial |

---

## 8. Deliverables

| File | Content | Due |
|------|---------|-----|
| `logo/` | Logo files (SVG, PNG) | Week 4 |
| `posters/` | 2-3 promotional posters | Week 6 |
| `landing-content.md` | All landing page text | Week 3 |
| `installation-guide.md` | Step-by-step install guide | Week 8 |
| `business-model.md` | Monetization and distribution plan | Week 6 |
