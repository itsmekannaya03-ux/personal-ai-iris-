# Encryption

## Purpose
Define the Encryption system — the cryptographic standards, key management, and encryption operations that protect data at rest, in transit, and during processing.

## Responsibilities
- Encrypt sensitive data at rest (deep memory, credentials)
- Provide TLS for data in transit
- Manage encryption keys securely
- Support key rotation
- Ensure forward secrecy where applicable

## Design Goals
- **Standard**: AES-256-GCM for data at rest, TLS 1.3 for transit
- **Performant**: Encryption adds < 5ms overhead
- **Key-secure**: Keys are stored separately from data
- **Rotatable**: Keys can be rotated without data loss

## Architecture
```
Data → Encryption Layer
         ├── At Rest: AES-256-GCM
         ├── In Transit: TLS 1.3
         ├── Credentials: Encrypted store
         └── Deep Memory: AES-256-GCM + key derivation
```

## Components
- **At Rest Encryptor**: Encrypts data files stored on disk
- **In Transit Provider**: TLS configuration for HTTP servers
- **Credential Encryptor**: Encrypts API keys and secrets
- **Key Manager**: Generates, stores, and rotates keys
- **Key Derivation**: Derives encryption keys from user password

### Key Hierarchy
```
Master Key (user password) → Key Derivation (PBKDF2/Argon2)
  ├── Storage Key (data files)
  ├── Memory Key (deep memory)
  └── Credential Key (API keys, tokens)
```

## Data Flow
Plaintext → Encrypt (AES-256-GCM + IV) → Ciphertext → Storage

Ciphertext → Decrypt (AES-256-GCM + IV) → Plaintext → Application

## Public Interfaces
- `POST /encryption/status` → Encryption status
- `POST /encryption/rotate` → Rotate encryption keys
- `POST /encryption/set-password` → Set encryption password
- `POST /encryption/verify` → Verify encryption is working

## Configuration
- Encryption algorithm: `encryption_algorithm` (default: AES-256-GCM)
- Key derivation: `key_derivation` (default: Argon2id)
- Key derivation params: `key_derivation_params`
- Key storage: `key_storage` (default: file with permissions)
- TLS config: TLS certificate paths in config

## Dependencies
- cryptography library (AES, Argon2, RSA)
- TLS certificates (self-signed or CA)
- Key storage (file system or HSM)

## Security Considerations
- Keys are never stored in code or environment variables
- Master key is derived from user password
- Key derivation uses Argon2id (memory-hard)
- Old keys are securely deleted after rotation
- Encryption is verified on each boot
- No encryption key can be recovered from ciphertext alone

## Failure Recovery
- Key corruption → data loss (restore from backup)
- Wrong password → clear error, retry count tracking
- Encryption failure → fail-safe (do not expose plaintext)
- TLS certificate expiry → warn, auto-renew if possible

## Future Improvements
- Phase 2: Hardware Security Module (HSM) support
- Phase 3: End-to-end encryption for sync
- Phase 4: Homomorphic encryption for cloud computation

## Engineering Notes
Never implement custom cryptography. Use well-audited libraries and standard algorithms.

## Acceptance Criteria
- Deep memory is encrypted at rest with AES-256-GCM
- All HTTP traffic uses TLS 1.3
- Credentials are encrypted in storage
- Keys can be rotated without data loss
- Encryption is verified on system boot

## References
- Volume-5-Security/01-Security.md
- Volume-4-Infrastructure/05-Storage.md
- Volume-5-Security/07-Recovery-System.md
