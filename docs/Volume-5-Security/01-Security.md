# Security

## Purpose
Define the overall security architecture, principles, and strategy for protecting IRIS, user data, and system integrity.

## Responsibilities
- Establish security principles and policies
- Define security architecture and controls
- Ensure compliance with security best practices
- Coordinate security incident response
- Maintain security documentation

## Design Goals
- **Defense in Depth**: Multiple layers of security controls
- **Least Privilege**: Components access only what they need
- **Secure by Default**: Default configurations are secure
- **Privacy by Design**: Privacy is embedded in architecture

## Architecture
```
Security Layers
├── Authentication (JWT, API tokens)
├── Authorization (permission model)
├── Encryption (AES-256, TLS 1.3)
├── Privacy (PIE, anonymization)
├── Isolation (sandbox, module isolation)
├── Auditing (structured logging)
└── Recovery (backup, restore)
```

## Components
- **Auth Layer**: JWT authentication for API users
- **Token Layer**: API tokens for inter-service auth
- **Permission Layer**: Granular permission model
- **Privacy Layer**: PIE privacy classification and routing
- **Encryption Layer**: AES-256 for data at rest, TLS for transit
- **Audit Layer**: Structured logging of security events
- **Recovery Layer**: Backup and disaster recovery

## Data Flow
Request → TLS → Authentication → Authorization → Permission Check → Processing → Audit Log

## Public Interfaces
- `GET /security/status` → Security configuration status
- `GET /security/audit` → Recent security events
- `POST /security/rotate-keys` → Rotate encryption keys

## Configuration
- Security policy file: `~/.iris/security.yaml`
- Auth token expiry: `auth_token_expiry_minutes` (default: 60)
- Max login attempts: `max_login_attempts` (default: 5)
- Session timeout: `session_timeout_minutes` (default: 120)
- Encryption algorithm: `encryption_algorithm` (default: AES-256-GCM)

## Dependencies
- JWT library (PyJWT)
- TLS (HTTPS)
- Encryption library (cryptography)
- Logging System (audit logging)

## Security Considerations
- All API endpoints require authentication
- Inter-service communication uses API tokens
- Secrets never appear in logs
- Failed authentication attempts are logged
- Security events trigger alerts

## Failure Recovery
- Auth service failure → degrade to minimum functionality
- Token validation failure → clear error, request re-auth
- Encryption key loss → data loss (user notified)
- Security breach detected → lock down, notify user

## Future Improvements
- Phase 2: Hardware security module support
- Phase 3: Zero-trust architecture
- Phase 4: Security audit automation

## Engineering Notes
Security is not a feature — it is a property of the entire system.

## Acceptance Criteria
- All API endpoints require authentication
- Passwords are never stored in plaintext
- Inter-service communication uses tokens
- Security events are logged with context
- Encryption keys can be rotated

## References
- Volume-5-Security/03-Authentication.md
- Volume-5-Security/04-Permissions.md
- Volume-5-Security/05-Encryption.md
- Volume-5-Security/06-Threat-Model.md
