# UI/UX Design — Member 4

## Your Job
- Design website layout and dashboard screens
- Create color themes and typography system
- Design user flow and wireframes
- Create UI components in Figma or Canva

---

## 1. Design System

### Colors (Already in code — `tailwind.config.ts`)
```
Primary:   iris-600  (#4F46E5 indigo)
Hover:     iris-500  (#6366F1)
Bg cards:  white/5    (rgba(255,255,255,0.05))
Text:      white/50-70-100
```

### Available Theme names (for UI)
| Theme | Keyword | Description |
|-------|---------|-------------|
| Blob | `blob` | Organic morphing blob that pulses with voice |
| Terminal | `terminal` | Green-on-black hacker aesthetic |
| Voice Bar | `voicebar` | Single bar expanding with audio |
| Drum Waves | `drum` | Concentric waveforms reacting to frequency |
| Hologram | `hologram` | Rotating 3D wireframe sphere |
| Minimal | `minimal` | Single pulsing dot |

### Typography
- **Font:** Inter (sans), JetBrains Mono (mono)
- **Scale:** 12/14/16/18/20/24/30/36px

---

## 2. Pages to Design

Create wireframes + final designs for:

### Public Pages
- [ ] Landing page (`/`) — Hero, features, how-it-works, CTA
- [ ] Features page (`/features`) — Grid of features with icons
- [ ] Pricing page (`/pricing`) — 3-tier comparison table
- [ ] Login page (`/login`) — Email + password form
- [ ] Signup page (`/signup`) — Multi-step form (profile + payment)

### Dashboard Pages
- [ ] Dashboard overview (`/dashboard`) — Welcome + status cards
- [ ] Download page (`/dashboard/download`) — OS selector + install cmd
- [ ] Profile page (`/dashboard/profile`) — Edit personal info
- [ ] Settings page (`/dashboard/settings`) — Plan, privacy, danger zone

---

## 3. UI Components to Design

These already exist in code — your job is to refine their look:
- [ ] Button (primary, secondary, ghost, outline)
- [ ] Card (default, glow variant)
- [ ] Input (with label, error state)
- [ ] Navbar (logo, nav links, auth buttons)
- [ ] Sidebar (dashboard navigation)
- [ ] Status card icons (CPU, RAM, memory stats)

---

## 4. Deliverables

| File | Format | Due |
|------|--------|-----|
| Wireframes (all pages) | Figma/PDF | Sprint 1 |
| Final UI mockups | Figma/PNG | Sprint 2 |
| Color palette guide | PDF | Sprint 1 |
| Icon set | SVG | Sprint 2 |
| Theme previews (6 themes) | GIF/Video | Sprint 4 |

---

## 5. Figma Resources

- Create a shared Figma project: **iris-ai-design**
- Use auto-layout for responsive frames
- Export assets as SVG for web
- Use the Inter font family
- Frame size: 1440x900 (desktop), 390x844 (mobile)
