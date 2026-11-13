# Storage

## Purpose
Define the Storage architecture — the data persistence layer that manages user profiles, memory, credentials, configuration, and system state across restart.

## Responsibilities
- Persist user profiles and preferences
- Store encrypted credentials
- Maintain system configuration
- Backup and restore data
- Manage disk space usage

## Design Goals
- **Persistent**: Data survives system restarts
- **Organized**: Well-defined storage hierarchy
- **Encrypted**: Sensitive data encrypted at rest
- **Portable**: Storage structure works cross-platform

## Architecture
```
~/.iris/
├── config.yaml              # Main system configuration
├── models.yaml              # Model registry
├── privacy_profile.json     # PIE user preferences
├── personality.json         # Personality settings
├── install_token.json       # Installation token
├── credentials/             # Encrypted API keys
│   ├── cloud.key            # Cloud provider keys
│   └── db.key               # Database credentials
├── modules/                 # Module configurations
├── memory/                  # Memory system data
│   ├── chroma/              # ChromaDB vector store
│   └── deep_memory.json     # Encrypted deep memory
├── logs/                    # System logs
├── plugins/                 # Installed plugins
├── skills/                  # Skill configurations
└── backups/                 # Automated backups
```

## Components
- **Config Store**: YAML-based configuration files
- **Profile Store**: JSON-based user profile data
- **Credential Store**: Encrypted storage for API keys
- **Memory Store**: ChromaDB + encrypted deep memory
- **Log Store**: Rotating log files
- **Backup Manager**: Automated backup and restore

## Data Flow
Component → Storage API → File System (standard) / ChromaDB (vectors) / Encrypted Store (secrets)

## Public Interfaces
- `POST /storage/export` → Export user data
- `POST /storage/import` → Import user data
- `POST /storage/backup` → Create backup
- `POST /storage/restore` → Restore from backup
- `GET /storage/usage` → Disk space usage
- `GET /storage/integrity` → Check data integrity

## Configuration
- Data directory: `~/.iris/` (configurable via `IRIS_DATA_DIR`)
- Deep memory encryption: `deep_memory_encrypt` (default: true)
- Backup interval: `backup_interval_days` (default: 7)
- Backup retention: `backup_retention_count` (default: 10)
- Log rotation: `log_max_size_mb` (default: 100)

## Dependencies
- ChromaDB (vector store)
- cryptography or pycryptodome (encryption)
- File system (standard persistence)

## Security Considerations
- Deep memory is AES-256 encrypted
- Credentials are stored in encrypted files
- Data exports are encrypted by default
- File permissions restrict access to user only
- Backup files are encrypted

## Failure Recovery
- Corrupted config → restore from backup → notify user
- Credential store decryption failure → prompt for master password
- ChromaDB corruption → rebuild from memory logs
- Disk full → emergency cleanup of old logs and backups

## Future Improvements
- Phase 2: Cloud backup (encrypted, user-controlled key)
- Phase 3: Incremental backup
- Phase 4: Data deduplication

## Engineering Notes
All storage paths use `~/.iris/` as root. Never hardcode absolute paths.

## Acceptance Criteria
- All persistent data survives engine restart
- Deep memory cannot be read without encryption key
- Backup and restore works for all data types
- Storage usage is reported accurately
- Corrupted data is detected and reported

## References
- Volume-2-Intelligence/03-Memory-System.md
- Volume-5-Security/05-Encryption.md
- Volume-1-Architecture/05-Runtime.md
