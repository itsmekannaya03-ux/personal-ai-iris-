# Permissions

## Purpose
Define the Permission system — the granular access control model that governs what actions each component, skill, plugin, and user can perform.

## Responsibilities
- Define permission categories and levels
- Enforce permission checks on all actions
- Provide permission configuration interface
- Log permission denials for audit
- Support escalation and delegation (future)

## Design Goals
- **Granular**: Permissions at action level
- **Least Privilege**: Default deny
- **Configurable**: Users can customize permissions
- **Auditable**: All permission checks are logged

## Architecture
```
Request → Permission Checker → Permission Store → Allow/Deny
                                      │
                                      ▼
                                Audit Log
```

## Components
- **Permission Store**: Defines available permissions and their state
- **Permission Checker**: Validates requests against permissions
- **Permission Manager**: CRUD interface for permissions
- **Audit Logger**: Records permission decisions

### Permission Categories
| Category | Permissions | Scope |
|----------|-------------|-------|
| Network | internet_access, local_network | Skills, plugins |
| Files | read, write, delete | Skills, terminal |
| System | process_execute, system_config | Terminal |
| Media | camera, microphone | Voice, vision |
| Data | memory_read, memory_write | Engine |
| Account | profile_read, profile_write | User |

## Data Flow
Action Request → Check Category → Check Permission → Allow/Deny → Log Decision

## Public Interfaces
- `GET /permissions/list` → List all permissions
- `GET /permissions/status` → Current permission state
- `POST /permissions/grant` → Grant permission
- `POST /permissions/revoke` → Revoke permission
- `POST /permissions/reset` → Reset to defaults

## Configuration
- Permission file: `~/.iris/permissions.yaml`
- Default permission: `deny` for all sensitive actions
- Permission levels: `allow` | `ask` | `deny` per category
- Auto-approve timeout for `ask`: `ask_timeout_seconds` (default: 30)

## Dependencies
- Authentication System (user identity)
- Storage System (permission persistence)
- Audit Logging (permission decisions)

## Security Considerations
- Default deny for all sensitive permissions
- Network, file, and system permissions require explicit grant
- Permissions can be scoped per skill/plugin/user
- Permission changes are logged for audit
- Temporary permission grants expire

## Failure Recovery
- Permission store corruption → reset to defaults
- Permission check failure → deny by default (safe failure)
- Missing permission definition → deny

## Future Improvements
- Phase 2: Time-based permissions
- Phase 3: Role-based access control (RBAC)
- Phase 4: Permission escalation with approval

## Engineering Notes
When in doubt, deny. It is always safer to deny a legitimate action than to allow a malicious one.

## Acceptance Criteria
- All sensitive actions are permission-gated
- Default is deny for all sensitive categories
- Permissions can be granted and revoked at runtime
- Permission denials are logged with context
- Permission state persists across restarts

## References
- Volume-5-Security/01-Security.md
- Volume-5-Security/03-Authentication.md
- Volume-6-Engineering/06-Code-Review.md (permission review)
