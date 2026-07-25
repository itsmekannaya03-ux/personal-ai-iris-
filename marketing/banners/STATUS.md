# M4 — UI/UX Designer — Design Status

## Role
Design the website layout, dashboard screens, color themes, and visual components. You write HTML/CSS/TSX code — not just mockups.

## ✅ Completed (by M1 — needs your review/improvement)
### Pages Already Built (need UI polish)
| Page | File | Status |
|------|------|--------|
| Landing Page | `website/app/page.tsx` | Built, needs visual refinement |
| Pricing Page | `website/app/(marketing)/pricing/page.tsx` | Built, needs design polish |
| Login Page | `website/app/(auth)/login/page.tsx` | Built, basic |
| Signup Page | `website/app/(auth)/signup/page.tsx` | Built, 3-step form |
| Dashboard | `website/app/dashboard/page.tsx` | Built, status cards |
| Download Page | `website/app/dashboard/download/page.tsx` | Built, OS selector |
| Profile Page | `website/app/dashboard/profile/page.tsx` | Built, form fields |
| Settings Page | `website/app/dashboard/settings/page.tsx` | Built, basic |

### Components (need UI polish)
- Button — primary/secondary/ghost/outline variants
- Card — default/glow variants
- Input — with label and error state
- Navbar — navigation with auth buttons

### Design System (already in code)
```css
/* tailwind.config.ts — custom igris color palette */
igris-50 through igris-900 (indigo shades)
/* globals.css — custom CSS */
.gradient-text, .glow, .grid-bg
```

## 📋 Your Tasks
- [ ] **Review all pages** — open each page at `localhost:3000` and note what looks bad
- [ ] **Redesign the landing page** — make it visually stunning (animations, gradients, layout)
- [ ] **Create 6 UI themes** — blob, terminal, voicebar, drum, hologram, minimal (CSS-only, no libraries)
- [ ] **Improve dashboard** — add animations, better status cards, theme preview
- [ ] **Design system documentation** — component examples page
- [ ] **Mobile responsive fixes** — test on phone-sized viewport
- [ ] **Dark mode** — ensure all pages look great on dark background

## 🎯 Next Step
Open `website/app/page.tsx` and improve the landing page hero section. Add smooth animations and better visual hierarchy.

## Files to Edit
All files are in `website/app/` and `website/components/`. Use Tailwind CSS classes (already configured).
