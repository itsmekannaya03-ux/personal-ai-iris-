# Threat Model

## Purpose
Define the security threat model for IGRIS — identifying potential threats, their impact, and the mitigations in place to protect against them.

## Responsibilities
- Identify and categorize security threats
- Assess threat impact and likelihood
- Document mitigations for each threat
- Guide security testing priorities
- Maintain threat landscape awareness

## Design Goals
- **Comprehensive**: Cover all threat categories
- **Realistic**: Focus on plausible threats
- **Actionable**: Mitigations are implementable
- **Living**: Updated as new threats emerge

## Architecture
```
Threat Model
├── Assets (what we protect)
├── Threats (what we protect against)
├── Mitigations (how we protect)
└── Residual Risks (what remains)
```

## Components

### Assets
| Asset | Sensitivity | Storage |
|-------|-------------|---------|
| User messages | High | Local, encrypted |
| Memory data | High | Encrypted |
| API credentials | Critical | Encrypted store |
| AI model files | Medium | Local files |
| Conversation history | Medium | Local, encrypted |
| User profiles | Medium | Local |
| Logs | Low | Local |

### Threat Categories
| Threat | Impact | Likelihood | Mitigation |
|--------|--------|------------|------------|
| Credential theft | Critical | Low | Encrypted storage, limited scope |
| Model poisoning | High | Low | Model checksums, signed manifests |
| Privilege escalation | Critical | Low | Least privilege, permission model |
| Data exfiltration | Critical | Medium | PIE, encryption, local-by-default |
| MITM | High | Low | TLS 1.3, certificate pinning |
| DoS | Medium | Medium | Rate limiting, resource limits |
| Supply chain | High | Low | Dependency audit, pinned versions |
| Physical access | Critical | Low | Disk encryption, screen lock |
| Social engineering | Medium | Medium | User education |
| Side-channel | Low | Low | Constant-time operations |

## Data Flow
Threat Identification → Risk Assessment → Mitigation Design → Implementation → Verification → Monitoring

## Public Interfaces
- `GET /threat-model/status` → Current threat mitigation status
- `POST /threat-model/assess` → Assess a new threat

## Configuration
- Threat model config: `~/.igris/security.yaml` (threat section)
- Severity thresholds: `severity_levels`
- Mitigation enforcement: `mitigation_enforcement` (default: strict)

## Dependencies
- All security systems (authentication, permissions, encryption)
- PIE (privacy threat mitigation)
- Monitoring system (threat detection)

## Security Considerations
- External dependencies are audited for known vulnerabilities
- Dependency scanning is automated in CI/CD
- Security patches are applied within SLAs
- Threat model is reviewed quarterly

## Failure Recovery
- Threat detected → isolate affected component → notify user
- Mitigation failure → escalate to alert
- Unpatched vulnerability → disable affected feature

## Future Improvements
- Phase 2: Automated penetration testing
- Phase 3: Bug bounty program
- Phase 4: Real-time threat intelligence integration

## Engineering Notes
The threat model is a living document. Review and update every quarter.

## Acceptance Criteria
- All identified threats have documented mitigations
- High-severity threats have implemented mitigations
- Threat model is reviewed quarterly
- Dependency scanning runs in CI/CD
- Security incidents trigger defined response procedures

## References
- Volume-5-Security/01-Security.md
- Volume-5-Security/07-Recovery-System.md
- Volume-6-Engineering/05-Testing.md (security testing)
