# Testing & QA — Member 7

## Your Job
- Test every feature thoroughly
- Report bugs with reproduction steps
- Verify bug fixes
- Prepare test cases
- Performance and usability testing

---

## 1. Test Areas

### Website Tests (`website/`)
| Test Case | Expected | Status |
|-----------|----------|--------|
| Landing page loads | Page renders with hero, features, CTA | ⬜ |
| Login with valid credentials | Redirects to dashboard | ⬜ |
| Login with wrong password | Shows error message | ⬜ |
| Signup with new email | Creates account, redirects to payment | ⬜ |
| Signup with existing email | Shows "email already exists" | ⬜ |
| Pricing page displays | 3 tiers visible with prices | ⬜ |
| Dashboard loads with user data | Welcome message, status cards | ⬜ |
| Profile update saves | Changes persist after reload | ⬜ |
| Download page generates token | Install command appears | ⬜ |
| Copy button works | Copies to clipboard | ⬜ |
| Theme change persists | Stays after page reload | ⬜ |

### API Tests (`api/`)
| Test Case | Expected | Status |
|-----------|----------|--------|
| `POST /auth/signup` | Returns token + user | ⬜ |
| `POST /auth/login` | Returns JWT token | ⬜ |
| `GET /auth/me` | Returns current user | ⬜ |
| `GET /profile` | Returns profile data | ⬜ |
| `PUT /profile` | Updates profile | ⬜ |
| `POST /subscriptions/create` | Creates Stripe session | ⬜ |
| `GET /subscriptions/status` | Returns plan info | ⬜ |
| `GET /download/{os}` | Returns script with token | ⬜ |
| `GET /installer/{token}` | Returns profile JSON | ⬜ |
| `POST /webhooks/stripe` | Handles Stripe events | ⬜ |

### AI Engine Tests (`app/`)
| Test Case | Expected | Status |
|-----------|----------|--------|
| AIEngine loads profile | Reads from `~/.igris/profile.json` | ⬜ |
| Chat sends to Ollama | Returns response text | ⬜ |
| Intent detection works | Correctly identifies 10 intents | ⬜ |
| Emotion analysis works | Detects 6 emotions | ⬜ |
| Short-term memory stores | Max 1000 entries | ⬜ |
| ChromaDB stores long-term | Persists across restarts | ⬜ |
| Memory promotes at weight 5 | Moves to deep memory | ⬜ |
| `"always remember"` triggers instant deep | Goes directly to deep | ⬜ |
| PC Control opens apps | Launches specified app | ⬜ |
| PC Control system info | Returns CPU/RAM/disk | ⬜ |
| Screenshot saves file | File created in `~/.igris/screenshots/` | ⬜ |
| Timer fires after N seconds | Prints notification | ⬜ |
| CLI interactive mode | Chat loop works | ⬜ |
| CLI slash commands | /memory, /skills, /mode work | ⬜ |
| Voice wake word detection | Detects "hey igris" | ⬜ |

---

## 2. Bug Report Template

```markdown
## Bug Report

**Severity:** (Critical / Major / Minor / Cosmetic)
**Module:** (Website / API / Engine / Installer)

**Steps to Reproduce:**
1. Go to ...
2. Click on ...
3. See error

**Expected Behavior:**
...

**Actual Behavior:**
...

**Environment:**
- OS: Windows 11 / macOS 14 / Ubuntu 24
- Browser: Chrome 125 / Firefox 126
- Python: 3.11
- Node: 20.x

**Screenshots:**
[Attach]

**Additional Context:**
...
```

---

## 3. Performance Testing

| Metric | Target | Tool |
|--------|--------|------|
| Page load time | < 2s | Chrome DevTools |
| API response time | < 500ms | Postman / curl |
| Ollama response time | < 5s (3B model) | Manual |
| ChromaDB query time | < 200ms | Python timer |
| Memory usage | < 500MB RAM | Task Manager |
| Installer time | < 5 min | Manual timing |

---

## 4. Test Scripts

Existing test scripts in `scripts/`:
- `test_intent.py` — Tests intent detection
- `test_emotion.py` — Tests emotion analysis

Run them with:
```bash
cd scripts
python test_intent.py
python test_emotion.py
```

---

## 5. Deliverables

| File | Content | Due |
|------|---------|-----|
| `test-plan.md` | Overall testing strategy | Week 3 |
| `test-cases.md` | All test cases (this file filled) | Week 8 |
| `bug-reports/` | All bugs found | Ongoing |
| `performance-report.md` | Performance metrics | Week 10 |
