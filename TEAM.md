# IGRIS AI — Team Structure & Folder Ownership

| Member | Role | Owns These Folders | Key Files |
|--------|------|-------------------|-----------|
| **Member 1** | Full-Stack & AI Lead | `website/`, `api/`, `app/` | All frontend + backend + AI engine code |
| **Member 2** | Local AI & System Dev | *(Covered by Member 1)* | — |
| **Member 3** | Project Manager | `project-management/` | Timeline, sprints, issues, meeting notes |
| **Member 4** | UI/UX Designer | `designs/` | Figma files, wireframes, mockups, color themes |
| **Member 5** | Research & Literature Survey | `docs/research/` | Comparison tables, USP, problem statement, objectives |
| **Member 6** | Documentation Lead | `docs/report/` | Project report, methodology, user manual, references |
| **Member 7** | Testing & QA | `tests/` | Test cases, bug reports, performance testing |
| **Member 8** | Database & Content Manager | `docs/content/` | Sample data, feature descriptions, help pages, pricing |
| **Member 9** | Presentation & Demo Coordinator | `docs/presentation/` | PPT, demo script, workflow diagrams |
| **Member 10** | Marketing & Deployment | `marketing/` | Logo, posters, landing page content, promotional materials |

## Folder Status

| Folder | Status | Ready For |
|--------|--------|-----------|
| `website/` | ✅ Built | Member 1 to finalize, Member 4 to design |
| `api/` | ✅ Built | Member 1 to finalize |
| `app/` | ✅ Built | Member 1 to maintain, Member 7 to test |
| `project-management/` | 📋 Template ready | Member 3 to fill |
| `designs/` | 📋 Template ready | Member 4 to start |
| `docs/research/` | 📋 Template ready | Member 5 to fill |
| `docs/report/` | 📋 Template ready | Member 6 to fill |
| `tests/` | 📋 Template ready | Member 7 to fill |
| `docs/content/` | 📋 Template ready | Member 8 to fill |
| `docs/presentation/` | 📋 Template ready | Member 9 to fill |
| `marketing/` | 📋 Template ready | Member 10 to fill |

## Code Owners (for git)

Each member should only modify files in their owned folders. If you need to touch another member's folder, create a PR and tag them for review.

## Repo Setup

```bash
git clone https://github.com/your-org/igris-ai.git
cd igris-ai
npm install
npm run dev          # Frontend (localhost:3000)
npm run dev:engine   # AI Engine (localhost:5743)
npm run dev:api      # Backend API (localhost:8000)
```
