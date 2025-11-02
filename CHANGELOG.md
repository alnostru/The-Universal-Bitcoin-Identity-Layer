# Changelog

All notable changes to the HODLXXI Universal Bitcoin Identity Layer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Multi-signature wallet support
- Lightning Channel management UI
- Advanced analytics dashboard
- Mobile SDKs (iOS/Android)
- Webhook support for events
- GraphQL API endpoint

---

## [1.0.0] - 2025-10-31

### Added
- **OAuth2/OpenID Connect Provider**: Full OAuth2 and OIDC implementation
  - Authorization code flow
  - Token refresh mechanism
  - Discovery endpoint (`/.well-known/openid-configuration`)
  - JWKS endpoint for key verification
  - Support for `openid`, `profile`, and `email` scopes
  
- **LNURL-Auth Integration**: Lightning Network authentication (LUD-04)
  - `/api/lnurl-auth/login` - LNURL login endpoint
  - `/api/lnurl-auth/verify` - Signature verification
  - `/api/lnurl-auth/callback` - Authentication callback
  
- **Bitcoin Wallet Management**:
  - Encrypted wallet operations
  - Multi-wallet support
  - Balance verification
  - Transaction history
  - Address generation and management
  
- **Proof of Funds (PoF) System**:
  - PSBT-based non-custodial balance verification
  - Multiple privacy levels (boolean, threshold, aggregate)
  - Challenge-response authentication
  - Time-limited proofs
  - `/api/pof/challenge` - Generate verification challenge
  - `/api/pof/verify` - Verify signed PSBT
  - `/api/pof/get-status` - Check verification status
  
- **Real-time Chat System**:
  - WebSocket-based encrypted messaging
  - User-to-user direct messaging
  - Channel/room support
  - Message history (in-memory)
  - Typing indicators
  - Read receipts
  - `/api/chat/rooms` - List available rooms
  - `/api/chat/messages` - Retrieve message history
  - `/api/chat/send` - Send message
  
- **User Management**:
  - Bitcoin public key-based identity
  - Profile management
  - Special user designations
  - Covenant-based group authentication
  - `/api/users/profile` - Get user profile
  - `/api/users/update` - Update profile
  
- **Security Features**:
  - Rate limiting (configurable per endpoint)
  - Cryptographic signature verification
  - CORS protection
  - CSRF protection
  - Encrypted session management
  - TLS/SSL enforcement
  - Audit logging
  
- **Monitoring & Observability**:
  - Prometheus metrics endpoint (`/metrics`)
  - Health check endpoint (`/health`)
  - Comprehensive error logging
  - Request/response logging
  - Performance metrics
  
- **Documentation**:
  - 190+ KB comprehensive documentation
  - API reference with examples (17 KB)
  - Error code documentation (24 KB)
  - OAuth/LNURL specification (48 KB)
  - Security requirements (31 KB)
  - Token policies (33 KB)
  - Production deployment guide (29 KB)
  - Privacy Policy (9 KB)
  - Terms of Service (15 KB)

### Security
- Implemented defense-in-depth security architecture
- All passwords hashed with bcrypt
- Bitcoin wallet encryption
- Secure session management
- Input validation and sanitization
- SQL injection protection
- XSS protection

### Infrastructure
- Docker support with `docker-compose.yml`
- Multi-stage Dockerfile for optimized builds
- Environment variable configuration (`.env.example`)
- PostgreSQL database support
- SQLite support for development
- Bitcoin Core RPC integration
- systemd service configuration

---

## [0.9.0] - 2025-10-15 (Beta)

### Added
- Initial beta release
- Core authentication system
- Basic wallet operations
- Chat prototype
- Admin panel

### Changed
- Migrated from SQLite to PostgreSQL for production
- Improved error handling
- Enhanced logging

### Fixed
- WebSocket connection stability
- Token refresh race conditions
- Memory leaks in long-running sessions

---

## [0.8.0] - 2025-09-30 (Alpha)

### Added
- Alpha release for testing
- OAuth2 foundation
- LNURL-auth prototype
- Basic API endpoints

### Known Issues
- Rate limiting not implemented
- Limited error codes
- Documentation incomplete

---

## Migration Guides

### Migrating to 1.0.0 from 0.9.0

**Breaking Changes:**
- API endpoint paths changed from `/auth/*` to `/oauth/*`
- Token response format now follows RFC 6749 strictly
- `expires_in` now returns seconds as integer (was string)

**Database Changes:**
```sql
-- Add new columns for OAuth2
ALTER TABLE users ADD COLUMN oauth_client_id VARCHAR(255);
ALTER TABLE users ADD COLUMN oauth_client_secret VARCHAR(255);

-- Create new OAuth tables
CREATE TABLE oauth_codes (
    code VARCHAR(255) PRIMARY KEY,
    client_id VARCHAR(255),
    user_id INTEGER,
    expires_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

**Configuration Changes:**
```bash
# Old .env format
AUTH_TYPE=basic

# New .env format
OAUTH_ENABLED=true
LNURL_ENABLED=true
```

**API Changes:**
```python
# Old: GET /auth/token
# New: POST /oauth/token

# Old response:
{"access_token": "...", "expires_in": "3600"}

# New response:
{"access_token": "...", "token_type": "Bearer", "expires_in": 3600}
```

---

## Deprecation Notices

### Version 1.0.0
- **Deprecated**: Legacy `/auth/*` endpoints (use `/oauth/*` instead)
- **Deprecated**: Plaintext password storage (use OAuth2 flow)
- **Removed**: Support for Python 3.7 (minimum now 3.8)

### Version 0.9.0
- **Deprecated**: SQLite in production (use PostgreSQL)
- **Deprecated**: Unencrypted WebSocket connections

---

## Upgrade Instructions

### From 0.9.x to 1.0.0

1. **Backup your database**:
   ```bash
   pg_dump hodlxxi_db > backup_20251031.sql
   ```

2. **Update dependencies**:
   ```bash
   pip install -r requirements.txt --upgrade
   ```

3. **Run migrations**:
   ```bash
   python manage.py db upgrade
   ```

4. **Update environment variables**:
   - Review `.env.example` for new variables
   - Add `OAUTH_ENABLED=true`
   - Add `JWT_SECRET_KEY` (generate new secure key)

5. **Restart services**:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

6. **Verify deployment**:
   ```bash
   curl https://your-domain.com/health
   curl https://your-domain.com/.well-known/openid-configuration
   ```

---

## Version Support

| Version | Release Date | End of Support | Status |
|---------|--------------|----------------|--------|
| 1.0.x   | 2025-10-31   | 2026-10-31     | ✅ Current |
| 0.9.x   | 2025-10-15   | 2025-12-31     | 🔄 Maintenance |
| 0.8.x   | 2025-09-30   | 2025-11-30     | ⚠️ Security Only |

---

## Links

- [GitHub Repository](https://github.com/alnostru/Universal-Bitcoin-Identity-Layer)
- [Documentation](app/README.md)
- [Issue Tracker](https://github.com/alnostru/Universal-Bitcoin-Identity-Layer/issues)
- [Security Policy](SECURITY.md)

---

**Legend:**
- `Added` - New features
- `Changed` - Changes in existing functionality
- `Deprecated` - Soon-to-be removed features
- `Removed` - Removed features
- `Fixed` - Bug fixes
- `Security` - Security improvements
