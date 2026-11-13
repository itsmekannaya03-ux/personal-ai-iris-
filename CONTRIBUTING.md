# Contributing to IRIS AI

## Git Workflow

1. **Clone the repo**
   ```bash
   git clone <repo-url>
   cd iris-ai
   ```

2. **Create a branch** named after your member number and feature:
   ```bash
   git checkout -b m1-intent-detection
   ```

3. **Only modify files in your owned folders** (see TEAM.md).

4. **Commit often** with clear messages:
   ```bash
   git commit -m "[m1] Add intent detection module"
   ```

5. **Push and create a PR** — tag the relevant member for review.

## Code Conventions

- **Python** (engine + api): PEP 8, use type hints
- **TypeScript** (website): Prettier, use TypeScript strict
- **No secrets** in code — use `.env` files

## Setup Commands

### Website (Member 1)
```bash
npm install
npm run dev     # → localhost:3000
```

### API (Member 1)
```bash
cd api
pip install -r requirements.txt
uvicorn main:app --reload    # → localhost:8000
```

### App (Member 2)
```bash
cd app
pip install -r requirements.txt
python cli.py "hello"        # CLI mode
python server.py             # Server mode → localhost:5743
```

## Testing (Member 7)
```bash
cd tests
pytest
```

## Before Pushing
- Check your files don't break the existing structure
- Update TEAM.md if you add new folders
- Never commit `.env` or `__pycache__`
