# IRIS AI — Personal AI Companion

A privacy-first, local AI assistant that learns, remembers, and controls your PC.

## Team (10 Members)

| Member | Role | Folder |
|---|---|---|
| **Member 1** | Full-Stack & AI Lead | `website/`, `api/` |
| **Member 2** | Local AI & System Developer | `app/` |
| **Member 3** | Project Manager | `project-management/` |
| **Member 4** | UI/UX Designer | `designs/` |
| **Member 5** | Research & Literature Survey | `docs/research/` |
| **Member 6** | Documentation Lead | `docs/report/` |
| **Member 7** | Testing & QA | `tests/` |
| **Member 8** | Database & Content Manager | `docs/content/` |
| **Member 9** | Presentation & Demo Coordinator | `docs/presentation/` |
| **Member 10** | Marketing & Deployment Support | `marketing/` |

See `TEAM.md` for detailed ownership.

## One-Command Setup

```bash
# 1. Clone
git clone <repo-url>
cd iris-ai

# 2. Website
npm install
npm run dev              # → http://localhost:3000

# 3. API (separate terminal)
cd api
pip install -r requirements.txt
uvicorn main:app --reload  # → http://localhost:8000

# 4. App (separate terminal)
cd app
pip install -r requirements.txt
python cli.py "hello"      # CLI mode
python server.py           # → http://localhost:5743
```

## Project Structure

```
iris-ai/
├── website/            Next.js 14 + Tailwind — Member 1
├── api/                FastAPI backend — Member 1
├── app/                Local AI engine — Member 2
├── project-management/ Member 3
├── designs/            Member 4
├── docs/
│   ├── research/       Member 5
│   ├── report/         Member 6
│   ├── content/        Member 8
│   └── presentation/   Member 9
├── tests/              Member 7
├── marketing/          Member 10
├── scripts/            Shared utilities
├── TEAM.md             Role & folder ownership
├── CONTRIBUTING.md     Workflow guide
└── .gitignore
```
