# Known Limitations

## Purpose
Document the current known limitations of IGRIS — technical constraints, capability gaps, and areas requiring improvement.

## Responsibilities
- Maintain accurate inventory of known limitations
- Document impact and severity of each limitation
- Track progress toward resolving limitations
- Communicate limitations to users transparently

## Design Goals
- **Honest**: Limitations are stated clearly, not hidden
- **Prioritized**: Most impactful limitations addressed first
- **Trackable**: Each limitation has status and resolution plan
- **User-aware**: Users can check limitation status

## Components

### Technical Limitations

| Limitation | Impact | Severity | Resolution Path |
|------------|--------|----------|-----------------|
| Port 8000 stuck in TIME_WAIT | API moved to 8001 | Medium | OS socket release / reboot |
| AI engine not auto-starting | Manual start required | Medium | Installer/service integration |
| Stripe payment placeholder | No real payments | Low | Stripe integration |
| JWT storage in localStorage | XSS vulnerability | High | HTTP-only cookies |
| No rate limiting | Abuse potential | Medium | Rate limiting middleware |
| No database migrations | Schema change risk | Medium | Alembic integration |
| Ollama dependency hidden | Installer complexity | Low | Better abstraction |
| Engine port 5743 ECONNREFUSED | Engine not started | Medium | Auto-start on first request |

### Capability Gaps

| Gap | Impact | Phase |
|-----|--------|-------|
| No JWT refresh tokens | Manual re-login | Phase 1 (post-MVP) |
| No vision system | Cannot process images | Phase 2 |
| Limited voice backends | Basic TTS only | Phase 2 |
| No cloud sync | Single device | Phase 3 |
| No mobile companion | Desktop only | Phase 3 |
| Limited multi-user | Single user | Phase 2 |
| No team features | Individual only | Phase 3 |
| Basic plugin system | Limited extensibility | Phase 2 |

### Known Issues

| Issue | Status | Workaround |
|-------|--------|------------|
| Deep memory not yet implemented | In progress | Use long-term memory |
| M4/M8 member tasks placeholder | Not started | Create STATUS.md updates |
| macOS installer untested | Untested | Use manual setup |
| GPU acceleration detection | Basic | Manual configuration |
| Model download resume | Not implemented | Restart download |

## Data Flow
Limitation → Issue Tracking → Prioritization → Resolution → Verification → Closure

## Public Interfaces
- `GET /system/limitations` → Current known limitations
- `GET /system/known-issues` → Active known issues

## Configuration
Limitation tracking in GitHub Issues with `known-limitation` label.

## Dependencies
- Issue tracking system (GitHub Issues)
- Project management (GitHub Projects)

## Security Considerations
- Security limitations are disclosed responsibly
- Critical security issues are fixed before public disclosure
- Limitations documentation does not expose security vulnerabilities

## Failure Recovery
- New limitation discovered → add to inventory → triage → prioritize
- Limitation resolved → update status → close issue

## Future Improvements
By definition, resolving limitations is the path to future improvements.

## Engineering Notes
Transparency about limitations builds trust with users and within the team.

## Acceptance Criteria
- All known limitations are documented
- Each limitation has severity and resolution path
- Limitations are updated as they are resolved or discovered
- Users can check limitation status
- Security limitations are prioritized for immediate resolution

## References
- Volume-7-Roadmap/06-Long-Term-Vision.md
- Volume-6-Engineering/07-Contributing.md (how to report limitations)
