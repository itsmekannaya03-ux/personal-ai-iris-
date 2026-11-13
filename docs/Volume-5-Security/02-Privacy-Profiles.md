# Privacy Profiles

## Purpose
Define the Privacy Profile system — the user-configurable privacy preferences that control how IRIS handles data, routing, and memory.

## Responsibilities
- Store user privacy preferences persistently
- Control PIE routing behavior (local vs cloud)
- Manage whitelist/blacklist for cloud routing
- Control memory retention and encryption
- Provide granular privacy controls

## Design Goals
- **Configurable**: Users choose their privacy level
- **Persistent**: Preferences survive restarts
- **Granular**: Per-category and per-domain controls
- **Transparent**: Users can see current privacy state

## Architecture
```
Privacy Profile → PIE → Routing Decisions
       │
       ├── Privacy Level (standard, conservative, maximum)
       ├── Cloud Routing (allowed domains, blocked domains)
       ├── Memory Policy (retention, encryption)
       └── Data Sharing (telemetry, diagnostics)
```

## Components
- **Profile Manager**: Reads/writes profile to `~/.iris/privacy_profile.json`
- **Privacy Levels**: Standard (balanced), Conservative (local preferred), Maximum (local only)
- **Domain Rules**: Whitelist/blacklist for cloud routing
- **Memory Policies**: Retention periods, encryption settings
- **Data Policies**: Telemetry and diagnostics opt-in/out

### Privacy Levels
| Level | Description | Cloud Routing | Memory |
|-------|-------------|---------------|--------|
| Standard | Balanced privacy | PIE decides | Normal retention |
| Conservative | Local preferred | Only low-risk cloud | Extended retention |
| Maximum | Local only | No cloud | Full encryption |

## Data Flow
User Settings → Profile Manager → `~/.iris/privacy_profile.json` → PIE → Routing Decisions

## Public Interfaces
- `GET /privacy/profile` → Get current privacy profile
- `POST /privacy/profile` → Update privacy profile
- `POST /privacy/level` → Set privacy level
- `POST /privacy/whitelist` → Add domain to whitelist
- `POST /privacy/blacklist` → Add domain to blacklist
- `GET /privacy/status` → Current privacy state

## Configuration
- Profile file: `~/.iris/privacy_profile.json`
- Default privacy level: `conservative`
- Default whitelist: `[]`
- Default blacklist: `[]`
- Memory encryption: `true` (for maximum level)
- Telemetry opt-in: `false` (default)

## Dependencies
- PIE (Privacy Intelligence Engine)
- Storage system (profile persistence)
- Memory System (encryption settings)

## Security Considerations
- Privacy profile is stored in plaintext (no secrets)
- Profile does not contain credentials
- Changes take effect immediately
- Users can reset to defaults at any time
- Profile cannot be exported without user consent

## Failure Recovery
- Profile corruption → reset to defaults, notify user
- Profile read failure → use conservative defaults
- Invalid profile values → clamp to safe defaults

## Future Improvements
- Phase 2: Per-session privacy profiles
- Phase 3: Location-based privacy rules
- Phase 4: Automatic privacy mode (PIE sets profile)

## Engineering Notes
Privacy profiles should be simple enough for non-technical users while powerful enough for privacy experts.

## Acceptance Criteria
- Privacy level changes take effect immediately
- Whitelist/blacklist domains are respected for cloud routing
- Memory policies match privacy level
- Profile survives engine restart
- Profile can be exported and imported

## References
- Volume-2-Intelligence/01-Privacy-Intelligence-Engine.md
- Volume-5-Security/05-Encryption.md
- app/pie/profile.py
