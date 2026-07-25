# Plugin System

## Purpose
Define the Plugin System — the extensibility framework that allows third-party developers to create and register new capabilities for IGRIS.

## Responsibilities
- Define plugin interface and lifecycle
- Manage plugin registration and discovery
- Sandbox plugin execution for security
- Handle plugin dependencies and versioning
- Provide plugin development toolkit

## Design Goals
- **Extensible**: Anyone can write a plugin
- **Isolated**: Plugins cannot access unauthorized resources
- **Versioned**: Plugins are versioned and can be updated
- **Discoverable**: Users can browse and install plugins

## Architecture
```
Plugin Registry ← Plugin Discovery → Plugin Store
      │
      ▼
Plugin Loader → Sandbox → Plugin Instance → Skill Integration
```

## Components
- **Plugin Registry**: Registers installed plugins
- **Plugin Loader**: Loads plugin modules with dependency resolution
- **Sandbox**: Restricted execution environment
- **Plugin API**: Python API for plugin development
- **Permission Manager**: Manages plugin permissions

## Data Flow
Plugin Registration → Validation → Loading → Permission Check → Execution → Result

## Public Interfaces
- `GET /plugins/list` → List installed plugins
- `POST /plugins/install` → Install plugin
- `POST /plugins/uninstall` → Uninstall plugin
- `POST /plugins/<id>/enable` → Enable plugin
- `POST /plugins/<id>/disable` → Disable plugin
- `GET /plugins/search` → Search available plugins

## Configuration
- Plugin directory: `~/.igris/plugins/`
- Plugin config per plugin: `~/.igris/plugins/<id>/config.yaml`
- Permission model: `allow` | `ask` | `deny` per capability

## Dependencies
- Skill System (plugins extend as skills)
- Python import system (plugin loading)

## Security Considerations
- Plugins run in isolated sandbox
- Explicit permission model for each plugin capability
- Plugin code is validated before loading
- Network access requires permission
- File system access restricted to plugin directory

## Failure Recovery
- Plugin crash → restart plugin (max 3 times)
- Malformed plugin → reject with validation errors
- Dependency conflict → clear error with resolution steps

## Future Improvements
- Phase 2: Plugin store and community submissions
- Phase 3: WebAssembly plugin support
- Phase 4: Visual plugin builder

## Engineering Notes
The plugin API should be stable for at least one major version. Breaking changes require migration path.

## Acceptance Criteria
- Plugins can be installed and uninstalled at runtime
- Plugin sandbox prevents unauthorized access
- Plugin permissions are user-configurable
- Plugin format is versioned and validated

## References
- Volume-3-Capabilities/01-Skill-System.md
- Volume-5-Security/04-Permissions.md
