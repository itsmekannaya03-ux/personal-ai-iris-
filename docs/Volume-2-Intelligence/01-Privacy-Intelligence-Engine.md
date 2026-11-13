# Privacy Intelligence Engine (PIE)

## Purpose
Define the Privacy Intelligence Engine — the core privacy system that classifies user input, routes inference requests to local or cloud providers, anonymizes sensitive data, and adapts to user corrections.

## Responsibilities
- Classify user input into privacy levels (low, medium, high, critical)
- Route inference requests: local for sensitive, cloud for non-sensitive
- Anonymize PII before sending to cloud providers
- Reconstruct responses from anonymized data
- Learn from user corrections to improve classification
- Maintain persistent user privacy profiles

## Design Goals
- **Accurate**: > 95% classification accuracy after learning period
- **Fast**: Classification completes in < 50ms
- **Adaptive**: Improves with user corrections
- **Explainable**: Can explain why a classification was made

## Architecture
```
User Input
    │
    ▼
┌─────────────────────────────┐
│        Classifier            │
│  (keyword + regex + context) │
└──────────┬──────────────────┘
           │ Classification (low/medium/high/critical)
           ▼
┌─────────────────────────────┐
│        Hybrid Router         │
│  CRITICAL → local (always)   │
│  HIGH/MEDIUM → anonymize→cloud│
│  LOW → cloud (default)       │
└──────────┬──────────────────┘
           │ Decision
           ▼
┌──────────────┐    ┌──────────────┐
│  Local Engine │    │  Cloud Provider│
│  (IRIS Neural Core)     │    │  (Anonymized)  │
└──────────────┘    └──────────────┘
```

## Components
- **Classifier**: 20+ regex/keyword rules, context analysis, confidence scoring
- **Hybrid Router**: Complete decision tree (CRITICAL→local, HIGH/MEDIUM→anonymize→cloud, LOW→cloud)
- **Anonymizer**: Entity replacement (names, emails, phones, addresses, SSN, credit cards, etc.)
- **Learner**: Correction storage, auto-whitelist after 3 corrections, stats tracking
- **Profile Manager**: Persistent `~/.iris/privacy_profile.json` with user preferences

## Data Flow
1. Input received by engine
2. Classifier scores privacy level with confidence
3. Router decides disposition based on classification
4. If cloud: Anonymizer replaces entities → cloud provider → De-anonymizer reconstructs
5. If local: Send directly to local inference engine
6. Learner records result; user may correct via /pie correct

## Public Interfaces
- `POST /pie/status` → Current PIE state, mode, stats
- `POST /pie/correct` → Submit a correction
- `POST /pie/explain` → Get explanation for a classification
- `POST /pie/classify` → Classify specific text
- `GET /pie/anonymize` → Anonymize sample text
- Slash commands in chat: `/pie`, `/privacy`

## Configuration
- Privacy profile: `~/.iris/privacy_profile.json`
- Default mode: `conservative` (route sensitive to local)
- Whitelist/blacklist domains in profile
- Sensitive patterns in `classifier.py`

## Dependencies
- Python `re` module for regex classification
- `app/pie/` modules (classifier, router, anonymizer, learner, profile)
- Runtime Inference Engine (local path)
- Cloud Provider abstraction (cloud path)

## Security Considerations
- CRITICAL data never leaves local machine
- Anonymized data is reconstructed only from cloud response
- Privacy profile is stored encrypted (future)
- User corrections are stored locally only

## Failure Recovery
- Classifier failure → default to `high` privacy (local only)
- Anonymizer failure → route to local
- Learner failure → corrections lost for that session, but profile is persisted

## Future Improvements
- Phase 2: ML-based classification model
- Phase 3: Federated learning across user profiles
- Phase 4: Privacy-preserving cloud inference (homomorphic encryption)

## Engineering Notes
PIE is the most privacy-critical component. Changes must be reviewed by security team.

## Acceptance Criteria
- Classification accuracy > 95% after learning period
- Classification completes in < 50ms
- Anonymization covers all PII types in the entity list
- User corrections persist across engine restarts
- PIE can explain any classification decision

## References
- Volume-5-Security/02-Privacy-Profiles.md
- Volume-4-Infrastructure/03-Hybrid-Intelligence.md
- app/pie/ (all modules)
