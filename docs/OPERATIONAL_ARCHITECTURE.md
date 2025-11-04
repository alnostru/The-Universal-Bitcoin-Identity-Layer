# HODLXXI Operational Architecture

**Purpose:** This document explains HOW HODLXXI works in production. While ARCHITECTURAL_DECISIONS.md explains WHY decisions were made, this document explains WHAT HAPPENS at runtime.

**Last Updated:** 2025-11-04

**Audience:** Future you (in 2030-2042) debugging production issues or onboarding someone to help maintain the system.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Application Startup Sequence](#application-startup-sequence)
3. [Request Flow Patterns](#request-flow-patterns)
4. [Authentication Flows](#authentication-flows)
5. [Data Flow and Storage](#data-flow-and-storage)
6. [WebSocket Lifecycle](#websocket-lifecycle)
7. [Bitcoin RPC Integration](#bitcoin-rpc-integration)
8. [Error Handling and Recovery](#error-handling-and-recovery)
9. [Performance Characteristics](#performance-characteristics)
10. [Monitoring and Observability](#monitoring-and-observability)

---

## System Overview

### Production Deployment Architecture

```
                                    ┌──────────────────┐
                                    │   Internet       │
                                    └────────┬─────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │  Nginx (443)     │
                                    │  - TLS           │
                                    │  - Rate limiting │
                                    │  - Static assets │
                                    └────────┬─────────┘
                                             │
                                             ▼
                    ┌────────────────────────────────────────┐
                    │   Gunicorn (5000)                      │
                    │   ├── Worker 1 (gevent)                │
                    │   ├── Worker 2 (gevent)                │
                    │   ├── Worker 3 (gevent)                │
                    │   └── Worker 4 (gevent)                │
                    │        Flask + SocketIO app            │
                    └───┬──────────────────┬─────────────┬───┘
                        │                  │             │
                        ▼                  ▼             ▼
                ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
                │ PostgreSQL   │  │    Redis     │  │ Bitcoin Core │
                │ (5432)       │  │    (6379)    │  │   RPC (8332) │
                │              │  │              │  │              │
                │ - Users      │  │ - Sessions   │  │ - Blockchain │
                │ - OAuth      │  │ - Cache      │  │ - Wallets    │
                │ - Audit logs │  │ - Rate limit │  │ - Verify     │
                └──────────────┘  └──────────────┘  └──────────────┘
```

### Component Responsibilities

| Component | Purpose | Failure Impact |
|-----------|---------|----------------|
| **Nginx** | TLS termination, static assets, rate limiting | Complete service outage |
| **Gunicorn Workers** | Application logic, HTTP/WebSocket handling | Reduced capacity (3/4 workers still work) |
| **PostgreSQL** | Persistent storage (users, tokens, audit logs) | Complete service outage |
| **Redis** | Session storage, cache, rate limiting | Degraded service (sessions lost, slower) |
| **Bitcoin Core** | Blockchain queries, signature verification | Bitcoin features unavailable |

### Port Allocations

- **443** - Nginx (HTTPS)
- **80** - Nginx (HTTP redirect to HTTPS)
- **5000** - Gunicorn (internal only)
- **5432** - PostgreSQL (localhost only)
- **6379** - Redis (localhost only)
- **8332** - Bitcoin Core RPC (localhost only)
- **3478** - TURN server (optional, for WebRTC)

**Security:** Only 443/80 exposed to internet. All other ports firewalled.

---

## Application Startup Sequence

### What Happens When You Start HODLXXI

**Command:** `gunicorn --worker-class gevent --workers 4 --bind 0.0.0.0:5000 wsgi:app`

### Step-by-Step Initialization

```
1. Gunicorn master process starts
   └── Reads wsgi.py

2. Import app/app.py (THIS IS WHERE EVERYTHING HAPPENS)
   ├── Load environment variables from .env
   ├── Configure Python logging
   │   └── logs/app.log (rotating, 10MB × 10 files)
   │
   ├── Load configuration (app/config.py)
   │   ├── Validate required environment variables
   │   ├── Set Flask secret key
   │   ├── Configure JWT settings
   │   └── Set CORS origins
   │
   ├── Initialize database connections (app/database.py)
   │   ├── Create PostgreSQL engine
   │   │   ├── Connection pool (size=10, max_overflow=20)
   │   │   ├── Pool pre-ping enabled
   │   │   └── Pool recycle after 3600s
   │   │
   │   ├── Create all tables if not exist
   │   │   └── (Production: use Alembic migrations instead)
   │   │
   │   └── Initialize Redis client
   │       ├── Connect to localhost:6379
   │       ├── Test connection with PING
   │       └── Set up connection pool
   │
   ├── Initialize audit logger (app/audit_logger.py)
   │   └── Ready to log security events
   │
   ├── Initialize Flask app
   │   ├── Set secret key
   │   ├── Configure session management
   │   └── Set JSON encoder for Bitcoin types
   │
   ├── Initialize SocketIO
   │   ├── CORS allowed origins
   │   ├── Async mode: gevent
   │   └── Message queue: Redis (for multi-worker)
   │
   └── Register all route handlers
       ├── OAuth endpoints (/oauth/*)
       ├── LNURL endpoints (/api/lnurl-auth/*)
       ├── Wallet endpoints (/import_descriptor, etc.)
       ├── Chat endpoints (/chat, WebSocket events)
       └── Health endpoints (/health, /metrics)

3. Gunicorn spawns 4 worker processes
   ├── Each worker is a separate OS process
   ├── Each worker has its own PostgreSQL connection pool
   ├── Each worker has its own Redis connection
   └── Workers share nothing (except PostgreSQL/Redis via network)

4. Each worker starts gevent event loop
   ├── Greenlets (lightweight threads) handle requests
   ├── Can handle thousands of concurrent connections per worker
   └── WebSocket connections are long-lived greenlets

5. Application is ready
   └── Listening on 0.0.0.0:5000
```

### Startup Failure Points

If startup fails, check these in order:

1. **Environment variables missing** → Check `.env` file exists and is readable
2. **PostgreSQL connection fails** → Check PostgreSQL is running, credentials correct
3. **Redis connection fails** → Check Redis is running on localhost:6379
4. **Bitcoin RPC connection fails** → Check Bitcoin Core is running, RPC credentials correct
5. **Port 5000 already in use** → Check if another Gunicorn instance is running

**Logs:** Check `logs/app.log` for detailed error messages

---

## Request Flow Patterns

### HTTP Request Flow

```
1. Client request arrives at Nginx
   ├── TLS handshake (if HTTPS)
   ├── Check rate limits (Nginx level)
   └── If rate limit OK, continue

2. Nginx routes request
   ├── If /static/* → serve directly from disk
   └── Else → proxy to http://localhost:5000

3. Gunicorn receives request
   └── Load balances across workers (round-robin)

4. Worker's gevent event loop picks up request
   └── Spawns greenlet to handle it

5. Flask application processes request
   ├── Match route (e.g., /oauth/authorize)
   ├── Run before_request hooks
   │   ├── Check authentication if required
   │   └── Check rate limits (application level)
   │
   ├── Execute route handler
   │   ├── Read from database if needed
   │   ├── Call Bitcoin RPC if needed
   │   ├── Verify signatures if needed
   │   └── Generate response
   │
   └── Run after_request hooks
       └── Add CORS headers, security headers

6. Response sent back through layers
   ├── Flask → Gunicorn worker → Nginx → Client
   └── Connection may stay open (keep-alive) or close

7. Audit log written (async)
   └── PostgreSQL AuditLog table
```

### WebSocket Request Flow

```
1. Client initiates WebSocket upgrade
   ├── GET request with Upgrade: websocket header
   └── Arrives at Nginx

2. Nginx proxies WebSocket connection
   ├── Detects Upgrade header
   ├── Establishes long-lived connection to Gunicorn
   └── Keeps connection open

3. Gunicorn worker accepts WebSocket
   └── SocketIO handles the connection

4. SocketIO 'connect' event fires
   ├── Extract pubkey from session or auth params
   ├── Add to ACTIVE_SOCKETS dict
   ├── Add to ONLINE_USERS set (in Redis)
   ├── Broadcast presence update
   └── Store socket_id → pubkey mapping

5. Connection stays open
   ├── Heartbeat messages keep connection alive
   ├── Client can emit events (message, rtc:offer, etc.)
   ├── Server can emit events (message, user_joined, etc.)
   └── Handled by gevent greenlet (non-blocking)

6. On disconnect
   ├── SocketIO 'disconnect' event fires
   ├── Remove from ACTIVE_SOCKETS
   ├── Remove from ONLINE_USERS (if last socket for user)
   ├── Broadcast presence update
   └── Greenlet terminates
```

### Performance Implications

**HTTP Requests:**
- Fast: ~10-50ms for simple operations (no Bitcoin RPC)
- Medium: ~100-500ms for Bitcoin RPC calls
- Slow: ~1-5s for wallet operations with many addresses

**WebSocket Messages:**
- Very fast: ~1-10ms latency (in-memory only)
- Network latency dominates (~20-200ms depending on geography)

**Database Queries:**
- Simple SELECT by primary key: ~1-5ms
- Complex JOINs: ~10-50ms
- Full table scan (should never happen): >1000ms

---

## Authentication Flows

### Flow 1: Bitcoin Signature Authentication

**Use Case:** User logs into HODLXXI with Bitcoin wallet

```
1. User visits /login page
   └── HTML form or API client

2. User provides three things:
   ├── Bitcoin public key (hex or base58)
   ├── Message (e.g., "Login to HODLXXI at 2025-11-04T12:00:00Z")
   └── Signature (signed with private key)

3. POST /verify_signature
   ├── Extract pubkey, message, signature from request
   │
   ├── Verify signature
   │   ├── Use Python cryptography library
   │   ├── Verify signature(message) == pubkey
   │   └── If invalid, return 401 Unauthorized
   │
   ├── Check if user exists in database
   │   ├── SELECT * FROM users WHERE pubkey = ?
   │   └── If not exists, create new user
   │
   ├── Create session
   │   ├── Generate session_id (UUID)
   │   ├── Store in PostgreSQL sessions table
   │   ├── Store in Redis (for fast lookup)
   │   └── Set cookie: session_id
   │
   ├── Update user.last_login
   │
   └── Write audit log
       └── AuditLog(event='login', user=pubkey, success=True)

4. Return success response
   └── Set-Cookie: session=<session_id>; HttpOnly; Secure

5. User is authenticated
   └── Subsequent requests include session cookie
```

**Failure Modes:**
- Invalid signature → 401 Unauthorized
- Malformed pubkey → 400 Bad Request
- Database error → 500 Internal Server Error (retry)

---

### Flow 2: LNURL-Auth Flow

**Use Case:** User authenticates with Lightning wallet (Alby, Blixt, etc.)

```
1. Client requests LNURL-Auth session
   POST /api/lnurl-auth/create
   ├── Generate k1 challenge (32 bytes random)
   ├── Create LNURLChallenge record in database
   │   ├── k1 = random_hex(32)
   │   ├── session_id = uuid4()
   │   ├── created_at = now()
   │   ├── expires_at = now() + 5 minutes
   │   └── verified = False
   │
   └── Return: {session_id, lnurl, qr_code_data}

2. Client displays QR code
   └── User scans with Lightning wallet

3. Wallet decodes LNURL
   ├── Format: LNURL1... (bech32 encoded URL)
   └── Decoded: https://hodlxxi.com/api/lnurl-auth/callback/<session_id>?k1=<k1>

4. Wallet requests authentication parameters
   GET /api/lnurl-auth/params?session_id=<id>
   └── Return: {k1, callback_url, tag: "login"}

5. Wallet signs k1 with its private key
   ├── Signature algorithm: secp256k1
   ├── DER-encoded signature
   └── Derives pubkey from wallet's identity key

6. Wallet calls callback URL
   GET /api/lnurl-auth/callback/<session_id>?k1=<k1>&sig=<sig>&key=<pubkey>
   ├── Load LNURLChallenge from database
   ├── Verify k1 matches
   ├── Verify not expired (5 minutes)
   ├── Verify signature
   │   ├── Use coincurve library
   │   ├── Verify sig(k1) == pubkey
   │   └── If invalid, return error
   │
   ├── Check if user exists (by pubkey)
   │   └── If not, create new user
   │
   ├── Mark LNURLChallenge as verified
   ├── Create session (same as signature auth)
   ├── Write audit log
   └── Return: {status: "OK"}

7. Client polls for completion
   GET /api/lnurl-auth/check/<session_id>
   ├── Check LNURLChallenge.verified
   └── If verified, return session token

8. User is authenticated
```

**Timing:**
- Step 1-2: ~100ms (database write)
- Step 3-6: User interaction time (5-30 seconds typical)
- Step 7: Polling every 2 seconds until verified

**Failure Modes:**
- Challenge expired (>5 min) → User must restart
- Invalid signature → Wallet bug or attack attempt
- Wallet doesn't support LNURL-auth → User must use different auth method

---

### Flow 3: OAuth2 Authorization Code Flow

**Use Case:** Third-party app wants to access HODLXXI on user's behalf

```
1. App registers with HODLXXI (one-time)
   POST /oauth/register
   ├── App provides: name, redirect_uris
   └── HODLXXI returns: client_id, client_secret

2. App redirects user to authorization endpoint
   GET /oauth/authorize?
       response_type=code
       &client_id=<client_id>
       &redirect_uri=<redirect_uri>
       &scope=profile:read wallet:read
       &state=<random_state>
       &code_challenge=<pkce_challenge>
       &code_challenge_method=S256

3. User must be logged in to HODLXXI
   ├── If not logged in → redirect to /login
   └── After login → return to /oauth/authorize

4. HODLXXI shows consent screen
   ├── "App X wants to access:"
   ├── "- Your profile information"
   ├── "- Your wallet balance"
   └── [Authorize] [Deny]

5. User clicks Authorize
   POST /oauth/authorize (form submission)
   ├── Validate client_id exists
   ├── Validate redirect_uri matches registered
   ├── Validate scope is allowed
   │
   ├── Generate authorization code
   │   ├── code = random_urlsafe(32)
   │   ├── Store in OAuthCode table
   │   │   ├── code
   │   │   ├── client_id
   │   │   ├── user_id (pubkey)
   │   │   ├── redirect_uri
   │   │   ├── scope
   │   │   ├── code_challenge (for PKCE)
   │   │   ├── expires_at (now + 10 minutes)
   │   │   └── used = False
   │   │
   │   └── Code valid for 10 minutes, one-time use
   │
   └── Redirect user back to app
       └── HTTP 302: <redirect_uri>?code=<code>&state=<state>

6. App's backend receives authorization code
   └── Via redirect from user's browser

7. App exchanges code for tokens
   POST /oauth/token
   ├── Headers: Authorization: Basic <client_id:client_secret>
   ├── Body:
   │   ├── grant_type=authorization_code
   │   ├── code=<code>
   │   ├── redirect_uri=<redirect_uri>
   │   └── code_verifier=<pkce_verifier>
   │
   ├── Validate authorization code
   │   ├── Check code exists in database
   │   ├── Check not expired (<10 minutes old)
   │   ├── Check not already used
   │   ├── Check client_id matches
   │   ├── Check redirect_uri matches
   │   └── Verify PKCE: SHA256(code_verifier) == code_challenge
   │
   ├── Mark code as used
   │
   ├── Generate tokens
   │   ├── Access token (JWT)
   │   │   ├── Algorithm: HS256 or RS256
   │   │   ├── Payload: {sub: pubkey, scope: granted_scopes, exp: 1hr}
   │   │   ├── Sign with JWT_SECRET
   │   │   └── access_token = "eyJhbGc..."
   │   │
   │   ├── Refresh token
   │   │   ├── refresh_token = random_urlsafe(64)
   │   │   └── Valid for 30 days
   │   │
   │   └── Store in OAuthToken table
   │       ├── access_token
   │       ├── refresh_token
   │       ├── client_id
   │       ├── user_id (pubkey)
   │       ├── scope
   │       ├── access_expires_at (now + 1 hour)
   │       ├── refresh_expires_at (now + 30 days)
   │       └── revoked = False
   │
   └── Return JSON:
       {
         "access_token": "eyJhbGc...",
         "token_type": "Bearer",
         "expires_in": 3600,
         "refresh_token": "...",
         "scope": "profile:read wallet:read"
       }

8. App uses access token to call API
   GET /api/demo/protected
   ├── Headers: Authorization: Bearer <access_token>
   │
   ├── Verify JWT signature
   │   ├── Decode JWT header to get algorithm
   │   ├── Verify signature with public key (RS256) or secret (HS256)
   │   └── If invalid, return 401 Unauthorized
   │
   ├── Check token not expired
   │   ├── Compare exp claim to current time
   │   └── If expired, return 401 with error="token_expired"
   │
   ├── Check scope
   │   ├── Route requires scope="profile:read"
   │   ├── Token has scope="profile:read wallet:read"
   │   └── OK (token has required scope)
   │
   ├── Load user from token.sub (pubkey)
   │
   └── Execute API logic
       └── Return requested data

9. When access token expires
   ├── App receives 401 Unauthorized
   │
   └── App refreshes token
       POST /oauth/token
       ├── grant_type=refresh_token
       ├── refresh_token=<refresh_token>
       ├── Authorization: Basic <client_id:client_secret>
       │
       ├── Validate refresh token
       │   ├── Check exists in database
       │   ├── Check not expired (<30 days)
       │   ├── Check not revoked
       │   └── Check client_id matches
       │
       ├── Generate new access token (JWT)
       ├── Optionally rotate refresh token
       ├── Update OAuthToken record
       │
       └── Return new access_token
```

**Token Lifetimes:**
- Authorization code: 10 minutes, one-time use
- Access token: 1 hour
- Refresh token: 30 days

**Security Features:**
- PKCE prevents authorization code interception
- Client secret required for token exchange
- Refresh token rotation (optional)
- Token revocation supported

---

## Data Flow and Storage

### Where Data Lives

| Data Type | Primary Storage | Cache Layer | TTL/Persistence |
|-----------|----------------|-------------|-----------------|
| **Users** | PostgreSQL | - | Permanent |
| **Sessions** | PostgreSQL | Redis | 24 hours |
| **OAuth Clients** | PostgreSQL | - | Permanent |
| **OAuth Codes** | PostgreSQL | - | 10 minutes |
| **OAuth Tokens** | PostgreSQL | - | 1 hour (access), 30 days (refresh) |
| **LNURL Challenges** | PostgreSQL | Redis | 5 minutes |
| **Chat Messages** | PostgreSQL | In-memory (app.py) | Permanent (DB), session (memory) |
| **Online Users** | Redis | - | While connected |
| **Rate Limits** | Redis | - | 1 hour window |
| **Audit Logs** | PostgreSQL | - | Permanent |
| **Bitcoin Wallets** | PostgreSQL | - | Permanent |

### Data Consistency Patterns

**Strong Consistency (PostgreSQL):**
- User accounts
- OAuth tokens
- Audit logs
- Financial data

**Eventual Consistency (Redis):**
- Online presence (ok if slightly stale)
- Rate limit counters (ok if approximate)
- Session cache (falls back to DB if missing)

**In-Memory Only:**
- Chat history (CHAT_HISTORY list in app.py)
  - ⚠️ **Risk:** Lost on restart
  - ⚠️ **Should be fixed:** Move to PostgreSQL or Redis

### Database Schema Relationships

```
┌──────────────┐
│    User      │
│ PK: pubkey   │
└───────┬──────┘
        │
        │ 1:N
        ▼
┌──────────────┐         ┌──────────────────┐
│   Session    │         │   OAuthClient    │
│ FK: user_id  │         │ PK: client_id    │
└──────────────┘         └────────┬─────────┘
                                  │
                                  │ 1:N
        ┌─────────────────────────┼─────────────────┐
        │                         │                 │
        ▼                         ▼                 ▼
┌──────────────┐         ┌──────────────┐   ┌──────────────┐
│  OAuthCode   │         │  OAuthToken  │   │ RateLimit    │
│ FK: user_id  │         │ FK: user_id  │   │ FK: client   │
│ FK: client   │         │ FK: client   │   │              │
└──────────────┘         └──────────────┘   └──────────────┘

┌──────────────────┐
│ LNURLChallenge   │
│ FK: user_id      │
│    (after verify)│
└──────────────────┘

┌──────────────────┐     ┌──────────────────┐
│  ChatMessage     │     │  BitcoinWallet   │
│  FK: sender      │     │  FK: user_id     │
│  FK: recipient   │     │                  │
└──────────────────┘     └──────────────────┘

┌──────────────────┐
│    AuditLog      │
│    FK: user_id   │
│    (if applicable)│
└──────────────────┘
```

### Critical Data Integrity Rules

1. **User pubkey is immutable** - Never change a user's pubkey. It's their identity.

2. **OAuth codes are one-time use** - Mark `used=True` immediately after exchange.

3. **Tokens can be revoked** - Check `revoked=False` before accepting token.

4. **Sessions expire** - Check `expires_at > now()` on every request.

5. **LNURL challenges expire** - Cleanup expired challenges periodically.

6. **Audit logs are append-only** - Never UPDATE or DELETE audit logs.

### Database Migrations

**Tool:** Alembic (SQLAlchemy migrations)

**Migration workflow:**
```bash
# Create new migration
alembic revision --autogenerate -m "Add new column to users"

# Review generated migration in alembic/versions/
# Edit if autogeneration made mistakes

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

**Production deployment:**
1. Backup database before migration
2. Run migration during maintenance window
3. Test application startup
4. Monitor for errors
5. Keep backup for 7 days

---

## WebSocket Lifecycle

### Data Structures for Real-Time Features

**In app/app.py:**

```python
# Active WebSocket connections
ACTIVE_SOCKETS = {}  # socket_id → pubkey mapping
# Example: {'abc123': '02a1b2c3...'}

# Online users (deduplicated by pubkey)
ONLINE_USERS = set()  # {pubkey1, pubkey2, ...}

# Chat history (in-memory, ⚠️ lost on restart)
CHAT_HISTORY = []  # [{sender, recipient, message, timestamp}, ...]
```

**In Redis:**

```
Key: "online_users"
Type: Set
Value: {pubkey1, pubkey2, pubkey3, ...}
TTL: None (explicitly removed on disconnect)

Key: "user:<pubkey>:sockets"
Type: Set
Value: {socket_id1, socket_id2, ...}  # Multiple tabs/devices
TTL: None (cleaned up on disconnect)
```

### WebSocket Events

**Client → Server:**

| Event | Payload | Purpose |
|-------|---------|---------|
| `connect` | `{pubkey}` | Establish WebSocket connection |
| `message` | `{to, message}` | Send chat message |
| `rtc:offer` | `{to, offer}` | WebRTC call initiation |
| `rtc:answer` | `{to, answer}` | WebRTC call acceptance |
| `rtc:ice` | `{to, candidate}` | WebRTC ICE candidate exchange |
| `rtc:hangup` | `{to}` | End WebRTC call |

**Server → Client:**

| Event | Payload | Purpose |
|-------|---------|---------|
| `message` | `{from, message, timestamp}` | Deliver chat message |
| `user_joined` | `{pubkey}` | User came online |
| `user_left` | `{pubkey}` | User went offline |
| `online_users` | `{users: [pubkey1, ...]}` | Current online users list |
| `rtc:offer` | `{from, offer}` | Forward WebRTC offer |
| `rtc:answer` | `{from, answer}` | Forward WebRTC answer |
| `rtc:ice` | `{from, candidate}` | Forward ICE candidate |
| `rtc:hangup` | `{from}` | Call ended notification |

### Connection Lifecycle Detail

```
1. User opens /chat page
   └── Browser executes Socket.IO client code

2. Socket.IO initiates connection
   ├── HTTP GET /socket.io/?transport=polling
   │   └── Establishes session, gets socket_id
   │
   └── Upgrade to WebSocket
       └── GET /socket.io/?transport=websocket

3. Server 'connect' event handler
   @socketio.on('connect')
   def handle_connect():
       socket_id = request.sid
       pubkey = get_pubkey_from_session()

       ACTIVE_SOCKETS[socket_id] = pubkey
       ONLINE_USERS.add(pubkey)

       # Also store in Redis for multi-worker
       redis.sadd('online_users', pubkey)
       redis.sadd(f'user:{pubkey}:sockets', socket_id)

       # Notify others
       emit('user_joined', {'pubkey': pubkey}, broadcast=True)

       # Send current online users to new connection
       emit('online_users', {'users': list(ONLINE_USERS)})

4. Connection is established
   ├── Heartbeat messages every 25 seconds (Socket.IO default)
   └── Connection stays open indefinitely

5. User sends message
   Client: emit('message', {to: 'target_pubkey', message: 'Hello'})

   Server:
   @socketio.on('message')
   def handle_message(data):
       sender = ACTIVE_SOCKETS[request.sid]
       recipient = data['to']
       message = data['message']
       timestamp = datetime.utcnow()

       # Save to database (permanent)
       save_chat_message(sender, recipient, message, timestamp)

       # Save to in-memory history (⚠️ lost on restart)
       CHAT_HISTORY.append({
           'from': sender,
           'to': recipient,
           'message': message,
           'timestamp': timestamp
       })

       # Find recipient's socket(s)
       recipient_sockets = redis.smembers(f'user:{recipient}:sockets')

       # Send to recipient
       for socket_id in recipient_sockets:
           emit('message', {
               'from': sender,
               'message': message,
               'timestamp': timestamp
           }, room=socket_id)

6. User closes browser tab
   └── Browser sends disconnect

7. Server 'disconnect' event handler
   @socketio.on('disconnect')
   def handle_disconnect():
       socket_id = request.sid
       pubkey = ACTIVE_SOCKETS.pop(socket_id, None)

       if pubkey:
           # Remove from Redis
           redis.srem(f'user:{pubkey}:sockets', socket_id)
           remaining_sockets = redis.scard(f'user:{pubkey}:sockets')

           # If no more sockets for this user, mark offline
           if remaining_sockets == 0:
               ONLINE_USERS.discard(pubkey)
               redis.srem('online_users', pubkey)
               emit('user_left', {'pubkey': pubkey}, broadcast=True)
```

### Multi-Worker WebSocket Coordination

**Problem:** 4 Gunicorn workers, each has own ONLINE_USERS set. How to coordinate?

**Solution:** Redis as shared state

```python
# When user connects (any worker)
redis.sadd('online_users', pubkey)

# When broadcasting (any worker)
socketio.emit('message', data, broadcast=True)
# Socket.IO uses Redis pub/sub to forward to other workers

# When checking online status
online = redis.smembers('online_users')
```

**How Socket.IO handles multi-worker:**
1. Each worker has own Socket.IO server
2. Redis pub/sub connects them
3. `broadcast=True` publishes to Redis channel
4. All workers subscribe and forward to their clients

---

## Bitcoin RPC Integration

### When Bitcoin RPC is Called

| Operation | Endpoint | RPC Calls | Purpose |
|-----------|----------|-----------|---------|
| Health check | `/health` | `getblockchaininfo()` | Verify RPC connectivity |
| Import descriptor | `/import_descriptor` | `importdescriptor()` | Watch-only wallet setup |
| Check balance | `/verify_pubkey_and_list` | `scantxoutset()` or `listunspent()` | Get wallet balance |
| Export wallet | `/export_wallet` | `listdescriptors()` | Backup wallet config |
| Verify address | Various | `validateaddress()` | Check address validity |

### RPC Connection Pattern

```python
def get_rpc_connection():
    """Create Bitcoin Core RPC connection"""
    try:
        rpc = AuthServiceProxy(
            f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}",
            timeout=30
        )
        # Test connection
        rpc.getblockchaininfo()
        return rpc
    except Exception as e:
        logger.error(f"Bitcoin RPC connection failed: {e}")
        return None
```

### RPC Error Handling

**Common errors:**

1. **Connection refused** - Bitcoin Core not running
   - Solution: Start Bitcoin Core
   - Status: 503 Service Unavailable

2. **Authentication failed** - Wrong RPC credentials
   - Solution: Check RPC_USER, RPC_PASSWORD in .env
   - Status: 500 Internal Server Error

3. **Wallet not loaded** - RPC calls fail with "Wallet not found"
   - Solution: `bitcoin-cli loadwallet <wallet_name>`
   - Status: 400 Bad Request

4. **Timeout** - RPC call takes >30 seconds
   - Usually: `scantxoutset()` on large wallet
   - Solution: Increase timeout or use different method
   - Status: 504 Gateway Timeout

**RPC Retry Logic:**

Not currently implemented. Should add:
```python
def rpc_call_with_retry(func, *args, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func(*args)
        except (ConnectionError, Timeout) as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

### Bitcoin RPC Performance

**Fast operations (<100ms):**
- `getblockchaininfo()`
- `validateaddress()`
- `getaddressinfo()`

**Medium operations (100ms-1s):**
- `listunspent()` on small wallet (<100 UTXOs)
- `importdescriptor()` with rescan=false

**Slow operations (1s-30s+):**
- `scantxoutset()` - scans entire UTXO set
- `importdescriptor()` with rescan=true - rescans blockchain
- `listsinceblock()` on large wallet

**Optimization strategies:**
1. Cache balance results in Redis (TTL 10 minutes)
2. Use `listunspent()` instead of `scantxoutset()` when possible
3. Import descriptors without rescan, scan separately if needed
4. Run slow operations in background (future: Celery)

---

## Error Handling and Recovery

### Error Categories

**1. Client Errors (4xx) - User's fault**
- 400 Bad Request - Invalid input
- 401 Unauthorized - Invalid auth
- 403 Forbidden - Insufficient permissions
- 404 Not Found - Resource doesn't exist
- 429 Too Many Requests - Rate limited

**2. Server Errors (5xx) - Our fault**
- 500 Internal Server Error - Unexpected exception
- 502 Bad Gateway - Upstream service down (Bitcoin RPC)
- 503 Service Unavailable - Maintenance or overload
- 504 Gateway Timeout - Operation took too long

### Error Response Format

```json
{
  "error": "error_code",
  "error_description": "Human-readable message",
  "timestamp": "2025-11-04T12:00:00Z",
  "request_id": "uuid-for-tracking"
}
```

### Recovery Patterns

**Database connection lost:**
```python
# SQLAlchemy handles this with pool pre-ping
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Test connection before use
    pool_recycle=3600    # Recycle connections after 1 hour
)
```

**Redis connection lost:**
```python
# Redis client auto-reconnects, but operations fail
try:
    redis.set('key', 'value')
except redis.ConnectionError:
    logger.error("Redis down, falling back to database")
    # Degrade gracefully: use PostgreSQL for sessions
```

**Bitcoin RPC unavailable:**
```python
@require_full_access()
def bitcoin_operation():
    rpc = get_rpc_connection()
    if not rpc:
        return jsonify({'error': 'bitcoin_rpc_unavailable'}), 503
    # Continue with RPC operation
```

**Worker crash:**
- Gunicorn detects crashed worker
- Automatically spawns new worker
- Other workers continue serving requests
- Lost: any in-memory state (CHAT_HISTORY, ONLINE_USERS for that worker)

### Logging for Debugging

**Log Levels:**
- DEBUG - Detailed info for development (SQL queries, etc.)
- INFO - Normal operations (requests, auth events)
- WARNING - Unexpected but handled (rate limit hit, validation failed)
- ERROR - Operation failed (database error, RPC error)
- CRITICAL - System failure (can't start, can't connect to DB)

**What to log:**
```python
# Good logging
logger.info(f"User {pubkey[:8]} logged in from {ip}")
logger.warning(f"Rate limit exceeded for client {client_id}")
logger.error(f"Bitcoin RPC error: {e}", exc_info=True)

# Bad logging (too verbose)
logger.debug(f"Checking if {pubkey} exists in database...")
logger.debug(f"Query result: {result}")

# Bad logging (sensitive data)
logger.info(f"User provided signature: {signature}")  # NO!
logger.info(f"JWT token: {token}")  # NO!
```

**Log file rotation:**
```python
handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=10_000_000,  # 10 MB
    backupCount=10         # Keep 10 old files
)
```

Total log storage: ~100 MB (10 MB × 10 files)

---

## Performance Characteristics

### Expected Load Capacity

**Single server (4 CPU cores, 8GB RAM):**

- **HTTP requests:** ~500-1000 req/sec (simple operations)
- **WebSocket connections:** ~5,000-10,000 concurrent
- **Database queries:** ~1,000-5,000 queries/sec (PostgreSQL)
- **Redis operations:** ~10,000-50,000 ops/sec

**Bottlenecks:**

1. **Bitcoin RPC** - Slowest component (100ms-30s per call)
2. **Database writes** - ~100-500 writes/sec before disk I/O limits
3. **Cryptographic operations** - Signature verification ~1ms each

### Optimization Techniques

**Caching:**
```python
# Cache Bitcoin balance for 10 minutes
cache_key = f"balance:{pubkey}"
balance = redis.get(cache_key)
if not balance:
    balance = get_balance_from_rpc(pubkey)
    redis.setex(cache_key, 600, balance)  # TTL 10 minutes
```

**Database indexing:**
```sql
-- Critical indexes
CREATE INDEX idx_users_pubkey ON users(pubkey);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_oauth_tokens_access_token ON oauth_tokens(access_token);
CREATE INDEX idx_oauth_codes_code ON oauth_codes(code);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
```

**Connection pooling:**
- PostgreSQL: 10 connections per worker × 4 workers = 40 total
- Each connection: ~10 MB RAM
- Total: ~400 MB for database connections

**Query optimization:**
- Use `SELECT *` sparingly - select only needed columns
- Avoid N+1 queries - use JOINs or `selectinload()`
- Use `EXPLAIN ANALYZE` to debug slow queries

### Resource Monitoring

**Memory:**
```bash
# Check Gunicorn worker memory
ps aux | grep gunicorn
# Each worker: ~200-500 MB typical

# Check PostgreSQL memory
ps aux | grep postgres
# PostgreSQL: ~100-500 MB typical
```

**Disk:**
```bash
# Check disk usage
df -h
# Watch for:
# - Bitcoin blockchain: ~500 GB
# - PostgreSQL: ~1-10 GB (depends on usage)
# - Logs: ~100 MB (with rotation)
```

**CPU:**
```bash
# Check CPU usage
top
# Gunicorn workers: 10-50% CPU each under load
# PostgreSQL: 5-20% CPU typical
# Bitcoin Core: 5-30% CPU (higher during sync)
```

---

## Monitoring and Observability

### Health Check Endpoint

```
GET /health

Response:
{
  "status": "healthy",
  "version": "1.0.0",
  "bitcoin_rpc": "connected",
  "database": "connected",
  "redis": "connected",
  "timestamp": "2025-11-04T12:00:00Z"
}
```

**Status codes:**
- 200 - All systems operational
- 503 - One or more systems down

**What to monitor:**
1. Response time >5s → System degraded
2. Status 503 → System down, investigate immediately
3. Bitcoin RPC "disconnected" → Check Bitcoin Core

### Metrics Endpoint

```
GET /metrics

Response (Prometheus format):
hodlxxi_active_websockets 127
hodlxxi_online_users 45
hodlxxi_chat_messages_total 1532
hodlxxi_lnurl_challenges_active 3
hodlxxi_oauth_tokens_active 89
```

**What to graph:**
- Active WebSocket connections (should be stable)
- Online users (fluctuates with daily pattern)
- Rate limit hits (spikes indicate potential attack)
- Token issuance rate (growth indicator)

### Audit Log Analysis

**Useful queries:**

```sql
-- Failed login attempts
SELECT user_id, ip_address, COUNT(*)
FROM audit_logs
WHERE event_type = 'login_attempt' AND success = false
GROUP BY user_id, ip_address
HAVING COUNT(*) > 10;

-- Token issuance rate
SELECT DATE_TRUNC('hour', timestamp) as hour, COUNT(*)
FROM audit_logs
WHERE event_type = 'token_issued'
GROUP BY hour
ORDER BY hour DESC
LIMIT 24;

-- Most active users
SELECT user_id, COUNT(*) as actions
FROM audit_logs
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY user_id
ORDER BY actions DESC
LIMIT 10;
```

### Alerting (To Implement)

**Critical alerts (immediate action required):**
- Service down (health check fails)
- Bitcoin RPC disconnected
- Database connection lost
- Disk space >90%

**Warning alerts (investigate soon):**
- High error rate (>5% of requests)
- Slow response time (>1s average)
- Memory usage >80%
- Certificate expiring <7 days

**Info alerts (good to know):**
- New user registered
- High OAuth token issuance (growth!)
- Unusual traffic pattern

**Alert channels:**
- Email: maintainer@hodlxxi.com
- SMS: For critical alerts only (costs money)
- Logging: All alerts logged to audit log

---

## Maintenance Operations

### Regular Tasks

**Daily:**
- Check health endpoint
- Review error logs for anomalies
- Monitor disk space

**Weekly:**
- Review audit logs for security issues
- Check for PostgreSQL slow queries
- Verify backups are running

**Monthly:**
- Update system packages (`apt update && apt upgrade`)
- Review and rotate logs if needed
- Check SSL certificate expiration
- Review Bitcoin Core version (security updates)

**Quarterly:**
- Update Python dependencies (test first!)
- Review and optimize database (VACUUM, REINDEX)
- Disaster recovery drill (restore from backup)

**Yearly:**
- Full security audit
- Review and update documentation
- Evaluate if architecture decisions still make sense

### Backup Procedures

**What to backup:**
1. **PostgreSQL database** - All user data, tokens, audit logs
2. **Redis snapshot** - Session data (optional, can rebuild)
3. **Application code** - Git repository (already backed up on GitHub)
4. **Configuration** - `.env` file (store securely, contains secrets)
5. **Bitcoin wallet** - If using Bitcoin Core wallet (store offline)

**Backup schedule:**
```bash
# PostgreSQL backup (daily at 2 AM)
0 2 * * * pg_dump hodlxxi > /backups/hodlxxi_$(date +\%Y\%m\%d).sql

# Compress old backups
0 3 * * * gzip /backups/hodlxxi_$(date -d '1 day ago' +\%Y\%m\%d).sql

# Delete backups older than 30 days
0 4 * * * find /backups -name "*.sql.gz" -mtime +30 -delete
```

**Backup storage:**
- Local: /backups (on same server)
- Remote: rsync to separate server or cloud storage
- Encrypted: GPG encrypt backups before uploading

**Test restore monthly:**
```bash
# Restore to test database
createdb hodlxxi_test
psql hodlxxi_test < /backups/hodlxxi_20251104.sql

# Verify data integrity
psql hodlxxi_test -c "SELECT COUNT(*) FROM users;"
```

---

## Conclusion

This document captures how HODLXXI works operationally. It complements the architectural decisions document by explaining the runtime behavior.

**When debugging in 2030-2042:**
1. Check logs first (`logs/app.log`)
2. Check health endpoint (`/health`)
3. Check metrics endpoint (`/metrics`)
4. Query audit logs for security events
5. Review this document for data flows and error patterns

**Keep this document updated when:**
- You change major operational behavior
- You discover new failure modes
- You implement monitoring/alerting
- You add new features that change data flows

**Trust the architecture.** It was designed for 17 years of sustainability. Don't break it unless you have to.

---

**Document History:**
- 2025-11-04: Initial operational architecture document created

**Related Documents:**
- ARCHITECTURAL_DECISIONS.md - Why things are built this way
- DEPLOYMENT_SUMMARY.md - How to deploy
- SECURITY.md - Security best practices
