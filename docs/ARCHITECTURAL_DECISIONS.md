# HODLXXI Architectural Decision Records (ADRs)

**Purpose:** This document explains the reasoning behind every major architectural decision in HODLXXI. When you return to this code in 2030 or 2035, this document will help you remember why things were built this way.

**Last Updated:** 2025-11-04

**Maintenance Philosophy:** HODLXXI is designed to run for 17 years (2025-2042) with a single maintainer. Every architectural decision prioritizes long-term sustainability, simplicity, and resilience over features or growth metrics.

---

## Table of Contents

1. [Core Mission and Constraints](#core-mission-and-constraints)
2. [Technology Stack Decisions](#technology-stack-decisions)
3. [Storage Architecture](#storage-architecture)
4. [Authentication Architecture](#authentication-architecture)
5. [Security Architecture](#security-architecture)
6. [Real-Time Communication](#real-time-communication)
7. [Bitcoin Integration](#bitcoin-integration)
8. [API Design](#api-design)
9. [Deployment Architecture](#deployment-architecture)
10. [What We Deliberately Did NOT Build](#what-we-deliberately-did-not-build)

---

## Core Mission and Constraints

### The Mission

HODLXXI exists to bridge web2 and web3 by providing **Bitcoin-native authentication that speaks OAuth2**. Traditional web applications can integrate with HODLXXI without understanding Bitcoin, while users can authenticate using Bitcoin signatures or Lightning wallets instead of corporate identity providers.

This is infrastructure for human sovereignty. We are not building a startup. We are building a public utility that demonstrates Bitcoin-based identity is practical and usable.

### The Constraints

1. **Single maintainer for 17 years (2025-2042)**
   - Every architectural decision must be sustainable for one person
   - Complexity is the enemy
   - Automation is essential
   - Documentation is critical

2. **No funding or resources**
   - Server costs must remain under $100/month
   - Cannot rely on paid services or support contracts
   - Must use mature, stable, free open-source technologies

3. **No technical community**
   - Cannot rely on contributors for maintenance
   - Cannot expect pull requests or community support
   - Must be self-sufficient

4. **Non-custodial forever**
   - NEVER store private keys
   - NEVER control user funds
   - Only verify signatures and Lightning payments
   - This keeps us out of financial regulation

### The Strategy

Given these constraints, our strategy is:
- **Simplicity over features** - Do a few things perfectly rather than many things adequately
- **Mature technologies** - Use battle-tested tools that have existed 10+ years and will exist 10+ more
- **Comprehensive documentation** - Write down every decision and reason
- **Automation** - Automate everything that can be automated
- **Reference implementation** - hodlxxi.com runs the canonical version; others can deploy their own instances

---

## Technology Stack Decisions

### ADR-001: Why Python + Flask

**Decision:** Use Python 3.11+ with Flask web framework

**Reasoning:**

1. **Python's longevity** - Python has been stable for 30+ years. Python 3.x will be supported for decades. This matters for a 17-year timeline.

2. **Bitcoin libraries exist** - `python-bitcoinrpc`, `bech32`, `base58`, `cryptography` all have mature Python implementations. We don't need to implement Bitcoin primitives ourselves.

3. **Flask's simplicity** - Flask is minimal and well-documented. When you return to this code in 2032, Flask will still work the same way. Contrast with JavaScript frameworks that change every 2 years.

4. **Standard library power** - Python's standard library handles JWT, HTTP, JSON, crypto, threading - everything we need without exotic dependencies.

5. **Debugging ease** - Python is readable and debuggable. When something breaks at 2am in 2035, you'll be grateful for Python's clarity.

**Alternatives Considered:**

- **Node.js** - Too fast-moving ecosystem. NPM dependency hell. JavaScript fatigue is real.
- **Go** - Better performance, but fewer Bitcoin libraries and less readable for future-you
- **Rust** - Overkill for this workload. Harder to debug. Compilation overhead.

**Trade-offs Accepted:**

- Python is slower than Go/Rust, but our bottleneck is Bitcoin RPC and database, not Python
- Single-threaded by default, but gevent/eventlet solve this for I/O-bound work
- Requires virtual environment management

**How to Know This Was Wrong:**

If you find yourself:
- Rewriting Bitcoin primitives because libraries are broken
- Fighting Python version incompatibilities constantly
- Hitting performance walls that can't be solved with caching

Then Python might have been the wrong choice. But more likely, the libraries or deployment needs fixing.

---

### ADR-002: Why Gunicorn + Gevent Workers

**Decision:** Use Gunicorn with gevent worker class for production

**Reasoning:**

1. **WebSocket requirements** - Flask-SocketIO needs async workers for WebSocket connections. Gevent provides this without threads.

2. **Long-lived connections** - Chat and WebRTC require connections that stay open for minutes/hours. Gevent's greenlets handle thousands of these efficiently.

3. **Gunicorn maturity** - Gunicorn has been stable since 2010. It's not going anywhere. It's the standard Python WSGI server.

4. **Process-based isolation** - Multiple Gunicorn workers mean one crashed worker doesn't take down the whole app.

5. **Simple configuration** - 4 workers is enough for single-server deployment. No complex orchestration needed.

**Alternatives Considered:**

- **uWSGI** - More features but more complexity. Harder to configure correctly.
- **Pure Flask dev server** - Not production-ready. No process management.
- **Async frameworks (FastAPI, Sanic)** - Would require rewriting entire app. Flask+gevent solves the problem.

**Trade-offs Accepted:**

- Gevent uses monkey-patching which can cause subtle bugs
- Greenlets are cooperative multitasking, not true parallelism
- Memory per worker adds up (4 workers × ~200MB = 800MB baseline)

**Configuration Used:**

```bash
gunicorn --worker-class gevent --workers 4 --bind 0.0.0.0:5000 wsgi:app
```

**How to Know This Was Wrong:**

If you find yourself:
- Hitting CPU limits (not I/O limits) on a single server
- Debugging mysterious gevent monkey-patching bugs frequently
- Needing horizontal scaling beyond one server

Then you might need to reconsider the worker model or split services.

---

### ADR-003: Why PostgreSQL + Redis Together

**Decision:** Use PostgreSQL as primary database and Redis as cache/session store

**Reasoning:**

**PostgreSQL for durability:**

1. **ACID transactions** - OAuth tokens, user accounts, audit logs MUST be durable. PostgreSQL guarantees this.

2. **Complex queries** - Finding users by pubkey, listing active tokens, audit log searches all need SQL.

3. **20+ year track record** - PostgreSQL has been production-ready since the 1990s. It will outlive HODLXXI.

4. **JSON support** - User metadata can be stored as JSONB without schema migrations.

5. **Battle-tested** - Billions of deployments. Well-understood failure modes. Excellent documentation.

**Redis for speed:**

1. **Session storage** - Web sessions need fast lookup. Redis provides this with TTL built-in.

2. **Real-time presence** - ONLINE_USERS set and ACTIVE_SOCKETS mapping need sub-millisecond access for chat.

3. **Rate limiting** - Per-user rate limit counters with expiry are Redis's specialty.

4. **LNURL challenges** - 5-minute TTL on k1 challenges is natural in Redis.

5. **Message queuing** - If we add background jobs later, Redis provides this.

**Why not just one?**

- **PostgreSQL alone** - Too slow for real-time chat presence and rate limiting
- **Redis alone** - No ACID guarantees. Lose all data on crash. No complex queries.

**Alternatives Considered:**

- **SQLite** - File-based, simpler, but no concurrent writes. Not suitable for multi-worker deployment.
- **MongoDB** - No ACID at the time of decision. Less mature than PostgreSQL.
- **Just PostgreSQL** - Would work but chat performance would suffer

**Trade-offs Accepted:**

- Two systems to maintain instead of one
- Data consistency between PostgreSQL and Redis requires careful coding
- Redis is in-memory, so loses data on restart (acceptable for cache/sessions)

**How to Know This Was Wrong:**

If you find yourself:
- Constantly fighting data inconsistency between PostgreSQL and Redis
- Paying more for Redis than the entire server
- Unable to afford the memory for Redis

Then you might consolidate to PostgreSQL-only. But likely you just need better caching patterns.

---

## Storage Architecture

### ADR-004: Why db_storage.py Production + storage.py Fallback

**Decision:** Maintain two storage backends - production (db_storage.py) and in-memory fallback (storage.py)

**Reasoning:**

1. **Production reality** - db_storage.py uses PostgreSQL and is production-grade

2. **Development convenience** - storage.py allows local development without PostgreSQL running

3. **Testing simplicity** - In-memory storage makes tests faster and doesn't require database cleanup

4. **Deployment flexibility** - Can run in "demo mode" without external dependencies

**Current Problem:**

These two implementations have diverged. Some code uses one, some uses the other, and inconsistencies have appeared. This is technical debt that MUST be fixed.

**The Fix (TODO):**

1. Define a Storage interface that both implementations must satisfy
2. Make all code use `get_storage()` factory function
3. Test both implementations against the same test suite
4. Document which storage backend is active in each environment

**Why We Kept Both:**

Even with the inconsistency problem, having a fallback storage is valuable for:
- Quick local testing without infrastructure
- Demonstration scripts that "just work"
- Emergency recovery if PostgreSQL is down but app needs to start

**Alternatives Considered:**

- **Delete storage.py** - Would force PostgreSQL dependency for all development
- **Only use storage.py** - Not production-grade, loses data on restart
- **Mock PostgreSQL** - Adds complexity, tests wouldn't match production

**Trade-offs Accepted:**

- Two implementations to keep synchronized
- Risk of divergence (which happened)
- More code to maintain

**How to Know This Was Wrong:**

If you find yourself:
- Constantly fixing bugs in one storage but not the other
- Unable to run tests because PostgreSQL is required
- Spending more time on storage abstraction than on features

Then pick one storage implementation and delete the other.

---

### ADR-005: Why SQLAlchemy ORM Instead of Raw SQL

**Decision:** Use SQLAlchemy 2.0+ as ORM layer

**Reasoning:**

1. **Type safety** - Models.py defines schema in Python. Less SQL injection risk.

2. **Migration management** - Alembic (built on SQLAlchemy) handles schema changes over 17 years.

3. **Relationship mapping** - User → Sessions → Tokens relationships are automatic.

4. **Connection pooling** - SQLAlchemy manages connection lifecycle correctly.

5. **Debugging** - Can enable SQL logging to see what queries run.

**Alternatives Considered:**

- **Raw psycopg2** - Faster but requires manual connection management and SQL string building
- **Other ORMs** - Django ORM ties you to Django. Others are less mature.

**Trade-offs Accepted:**

- Slight performance overhead vs raw SQL
- Learning curve for SQLAlchemy 2.0's new API
- N+1 query problems if relationships used carelessly

**How to Know This Was Wrong:**

If you find yourself:
- Writing raw SQL for every query because ORM is too slow
- Fighting ORM behavior instead of using it
- Hitting performance walls that require query optimization beyond ORM capabilities

Then you might drop down to raw SQL for hot paths. But keep ORM for admin/CRUD operations.

---

## Authentication Architecture

### ADR-006: Why OAuth2 Instead of Simpler Auth

**Decision:** Implement full OAuth2 Authorization Code Flow with PKCE

**Reasoning:**

**This is the core value proposition.** HODLXXI exists to speak OAuth2 so normal web apps can integrate without understanding Bitcoin.

1. **Standard protocol** - OAuth2 is what every web developer already knows. Google, GitHub, Auth0 all use it.

2. **Existing client libraries** - Every language has OAuth2 clients. Apps can integrate with HODLXXI using existing code.

3. **Token-based** - Access tokens expire. Refresh tokens allow long-lived access. Revocation is built-in.

4. **Scopes for permissions** - `profile:read`, `wallet:read`, etc. allow fine-grained access control.

5. **PKCE security** - Protects against authorization code interception attacks.

**Why not simpler auth?**

We COULD have just done "send signature with every request" but then:
- Every app needs to understand Bitcoin signatures
- No token expiry or refresh mechanism
- No scope-based permissions
- No interoperability with existing OAuth ecosystems

**The Bridge Metaphor:**

HODLXXI is a bridge. One side speaks Bitcoin (signatures, Lightning, LNURL). Other side speaks OAuth2. Web apps only see the OAuth2 side. This is the entire point.

**Alternatives Considered:**

- **API keys** - Simpler but no expiry, no scopes, less secure
- **JWTs only** - Still requires custom integration
- **SAML** - Enterprise protocol, way too complex

**Trade-offs Accepted:**

- OAuth2 is complex to implement correctly
- 9,000+ lines in app.py partially due to OAuth flows
- Must maintain OIDC discovery, JWKS endpoints, token introspection, etc.

**How to Know This Was Wrong:**

If you find yourself:
- No apps integrate because OAuth2 is too complex for users
- Spending all time debugging OAuth instead of improving Bitcoin features
- Users asking "why not just use Lightning-native auth for everything?"

Then maybe OAuth2 was overkill. But more likely, the implementation just needs cleanup.

---

### ADR-007: Why LNURL-Auth Alongside OAuth

**Decision:** Support LNURL-Auth in addition to OAuth2

**Reasoning:**

1. **Lightning-native flow** - Lightning wallets (Alby, Blixt, Mutiny) can authenticate without web forms

2. **Complementary use cases** - OAuth for apps, LNURL-auth for users

3. **LUD-04 standard** - LNURL-Auth is a Lightning ecosystem standard. Supporting it shows Bitcoin-native thinking.

4. **QR code simplicity** - Scan QR, sign with wallet, authenticated. No passwords, no forms.

5. **Demonstrates the concept** - Shows that Bitcoin-based identity is practical

**Why Both?**

- **OAuth** - For applications integrating HODLXXI as identity provider
- **LNURL-Auth** - For users logging into HODLXXI itself or simple apps

These serve different audiences and don't conflict.

**Alternatives Considered:**

- **Only OAuth** - Would miss Lightning wallet users
- **Only LNURL-auth** - Can't integrate with normal web apps
- **Nostr-style auth** - Considered but LNURL-auth was more mature in 2024

**Trade-offs Accepted:**

- Two auth flows to maintain
- Confusion about when to use which
- LNURL-auth requires Lightning wallet (not everyone has one)

**How to Know This Was Wrong:**

If you find yourself:
- No one uses LNURL-auth because Lightning wallets don't support it
- LNURL-auth constantly breaking due to wallet incompatibilities
- Maintaining LNURL code takes more time than it provides value

Then consider deprecating LNURL-auth and focusing only on OAuth2.

---

### ADR-008: Why Bitcoin Signature Verification for Identity

**Decision:** User identity is Bitcoin public key. Authentication is signature verification.

**Reasoning:**

1. **No passwords** - Users don't need to remember or manage passwords. They prove ownership of pubkey by signing.

2. **Non-custodial** - We never see private keys. Users maintain sovereignty over identity.

3. **Bitcoin-native** - Works with any Bitcoin wallet. No special software required (though convenience wallets help).

4. **Cryptographically strong** - Secp256k1 signatures are battle-tested by billions of dollars in Bitcoin.

5. **Decentralized** - User's identity exists independent of HODLXXI. If HODLXXI disappears, users still have their keys.

**The Pubkey as Username:**

Traditional systems: username + password
HODLXXI: pubkey proves itself via signature

The pubkey IS the username. The signature proves you control the corresponding private key.

**Alternatives Considered:**

- **Email + password** - Centralized, requires storing hashed passwords, not Bitcoin-native
- **Nostr pubkeys** - Considered but Bitcoin wallets are more common
- **Lightning node pubkeys** - Too specialized, fewer people run Lightning nodes

**Trade-offs Accepted:**

- Most users don't understand pubkey-based auth initially
- Need wallet software to sign messages (though all Bitcoin wallets can do this)
- Lose private key = lose identity (but this is true for Bitcoin itself)

**How to Know This Was Wrong:**

If you find yourself:
- Most users can't figure out how to sign messages
- Constantly adding password-based auth "just for convenience"
- Supporting so many signature formats that verification becomes a mess

Then maybe pubkey-as-identity is too early. But more likely, UX just needs improvement.

---

## Security Architecture

### ADR-009: Why Non-Custodial Forever

**Decision:** NEVER store private keys. NEVER control user funds. Only verify signatures.

**Reasoning:**

**This is non-negotiable. It's the foundation of everything.**

1. **Legal protection** - Non-custodial means we're not a money transmitter. Not a financial service. Just infrastructure.

2. **Security model** - Can't lose what we don't have. No private keys = no keys to steal.

3. **User sovereignty** - Users control their identity. HODLXXI is just a verifier, not a custodian.

4. **Regulatory clarity** - Running a signature verifier is like running a block explorer. Not regulated like exchanges.

5. **17-year viability** - Custody requirements might change over 17 years. Non-custody is always safe.

**What This Means:**

- ✅ Verify Bitcoin signatures: YES
- ✅ Check Lightning invoices: YES
- ✅ Derive addresses from xpub: YES
- ❌ Store private keys: NEVER
- ❌ Sign transactions for users: NEVER
- ❌ Hold Bitcoin: NEVER
- ❌ Custody anything: NEVER

**Alternatives Considered:**

NONE. This is not negotiable.

**Trade-offs Accepted:**

- Can't offer "convenience" features like signing for users
- Can't do automatic payments or withdrawals
- Users must manage their own keys (good thing!)

**How to Know This Was Wrong:**

There is no scenario where storing private keys is right for HODLXXI's mission. If you find yourself considering it, you've lost the plot. Go back and re-read the mission statement.

---

### ADR-010: Why Audit Logging Everything

**Decision:** Log all authentication attempts, token operations, and security-relevant actions

**Reasoning:**

1. **Security forensics** - When something goes wrong, you need to know what happened.

2. **Abuse detection** - Patterns of failed logins, token misuse, etc. show up in audit logs.

3. **Compliance** - If regulations ever require it, we have the logs.

4. **Trust** - Users can see their own audit log (future feature).

5. **17-year timeline** - Memory fades. Logs don't. You'll forget what happened in 2027. Logs remember.

**What Gets Logged:**

- Authentication attempts (success and failure)
- OAuth token issuance and revocation
- API access with Bearer tokens
- Bitcoin RPC calls
- Security events (rate limiting, suspicious activity)

**What Doesn't Get Logged:**

- Private keys (we don't have them)
- Full request bodies (too much data)
- User passwords (we don't have them)

**Alternatives Considered:**

- **No logging** - Can't debug production issues
- **Only application logs** - Not structured for security analysis
- **Full request logging** - Too much data, privacy concerns

**Trade-offs Accepted:**

- Audit logs grow over time (plan for log rotation)
- Performance overhead of writing logs (minimal with async I/O)
- Storage costs for long-term log retention

**How to Know This Was Wrong:**

If you find yourself:
- Unable to store logs due to disk space
- Spending more time managing logs than they provide value
- Logs contain private data that causes privacy problems

Then reduce logging verbosity or implement log rotation. But don't remove audit logging entirely.

---

### ADR-011: Why Rate Limiting Per-User

**Decision:** Implement rate limiting with per-user quotas based on client tier

**Reasoning:**

1. **Abuse prevention** - Without rate limits, one user can DOS the server.

2. **Resource management** - Bitcoin RPC calls are expensive. Must prevent excessive usage.

3. **Tiered access** - FREE (100/hr), PAID (1000/hr), PREMIUM (10000/hr) allows scaling with usage.

4. **Fair access** - One user can't monopolize server resources.

**Implementation:**

- Rate limit tracking in Redis (fast lookups)
- Per-user counters with sliding windows
- HTTP 429 responses when limit exceeded
- `X-RateLimit-*` headers in responses

**Alternatives Considered:**

- **No rate limiting** - Server would be DOSed immediately
- **Global rate limiting** - One user blocks everyone
- **IP-based limiting** - Doesn't work with shared IPs (NAT, VPNs)

**Trade-offs Accepted:**

- Redis dependency for rate limit counters
- Legitimate users might hit limits (can upgrade tier)
- More complex than "no limits"

**How to Know This Was Wrong:**

If you find yourself:
- Constantly adjusting rate limits because they're too restrictive
- Rate limiting not preventing abuse (DDoS still getting through)
- Redis overhead for rate limiting exceeds benefit

Then reconsider rate limit implementation. But keep SOME rate limiting.

---

## Real-Time Communication

### ADR-012: Why WebSocket + Flask-SocketIO

**Decision:** Use Flask-SocketIO for WebSocket support, enabling real-time chat

**Reasoning:**

1. **Real-time presence** - Chat requires knowing who's online. WebSocket provides this.

2. **Low latency** - Messages appear instantly. HTTP polling would be slower.

3. **Flask integration** - Flask-SocketIO integrates cleanly with Flask app.

4. **Standard protocol** - Socket.IO has clients for every platform.

5. **Connection management** - Handles reconnection, heartbeat, etc. automatically.

**Why Chat at All?**

This is a fair question. Chat is not core to Bitcoin authentication. But:

- Demonstrates real-time capability
- Provides utility beyond just auth
- Shows WebSocket integration for others to learn from
- Creates community/network effect

**Alternatives Considered:**

- **No chat** - Simpler but less useful
- **HTTP long-polling** - Works but higher latency and server load
- **WebRTC only** - Requires signaling server anyway (which is what Socket.IO provides)

**Trade-offs Accepted:**

- WebSocket connections are long-lived (memory per connection)
- Socket.IO is a complex protocol
- Requires gevent workers (can't use sync workers)

**How to Know This Was Wrong:**

If you find yourself:
- Chat is constantly breaking and needs maintenance
- Memory usage from WebSocket connections exceeds server capacity
- No one uses chat feature

Then consider removing chat entirely. OAuth2 + Bitcoin auth is the core. Chat is extra.

---

### ADR-013: Why WebRTC + TURN Server

**Decision:** Support WebRTC for peer-to-peer voice/video with TURN fallback

**Reasoning:**

1. **P2P when possible** - WebRTC connects peers directly (low latency, no server bandwidth)

2. **TURN fallback** - When P2P fails (NAT, firewalls), TURN relays media

3. **Standard protocol** - WebRTC is built into all modern browsers

4. **Signaling via Socket.IO** - Already have WebSocket for chat. Reuse for WebRTC signaling.

**TURN Server Necessity:**

- About 8-15% of connections need TURN relay
- Without TURN, those connections fail
- TURN uses time-limited credentials (HMAC-SHA1)
- Must run TURN server separately (Coturn is common)

**Alternatives Considered:**

- **No voice/video** - Simpler but less useful
- **Server-based media relay** - Uses massive bandwidth
- **Third-party service** - Costs money and requires external dependency

**Trade-offs Accepted:**

- Need to run separate TURN server
- TURN bandwidth can be expensive for video
- WebRTC is complex (ICE, SDP, etc.)

**How to Know This Was Wrong:**

If you find yourself:
- TURN bandwidth costs exceed server budget
- Constantly debugging WebRTC connection issues
- Feature barely used

Then remove WebRTC/TURN. Chat text-only is fine. Voice/video is nice-to-have, not essential.

---

## Bitcoin Integration

### ADR-014: Why Bitcoin Core RPC Instead of Alternatives

**Decision:** Use Bitcoin Core RPC for blockchain interaction

**Reasoning:**

1. **Full node = full trust** - Running Bitcoin Core means we validate everything ourselves.

2. **RPC maturity** - Bitcoin Core RPC has been stable since 2009. Well-documented.

3. **No third-party dependency** - Don't rely on block explorers or API services (centralization risk).

4. **Descriptor support** - Modern Bitcoin Core supports descriptors for wallet operations.

5. **17-year timeline** - Bitcoin Core will exist in 2042. Block explorer APIs might not.

**What We Use RPC For:**

- Verify address ownership
- Check balances (for watch-only wallets)
- UTXO listing
- Transaction broadcasting (future feature)
- Blockchain info (height, difficulty, etc.)

**Alternatives Considered:**

- **Block explorer APIs** - Centralized, rate-limited, might disappear
- **Electrum server** - Additional complexity, less mature
- **Light clients** - Don't validate everything, trust issues

**Trade-offs Accepted:**

- Must run full Bitcoin node (disk space, bandwidth, sync time)
- RPC calls are slower than reading from local database
- Bitcoin Core upgrades might break RPC compatibility

**How to Know This Was Wrong:**

If you find yourself:
- Unable to afford disk space for Bitcoin blockchain
- Bitcoin Core RPC constantly breaking with new versions
- Need features Bitcoin Core doesn't provide

Then consider alternatives. But for 17 years, running a full node is the right choice for sovereignty.

---

### ADR-015: Why Watch-Only Wallet Support

**Decision:** Support importing watch-only wallet descriptors (xpub/zpub)

**Reasoning:**

1. **Non-custodial** - Watch-only means we can't spend. Only observe.

2. **Balance checking** - Users can display their balance without exposing private keys.

3. **Address derivation** - Can derive new receiving addresses from xpub.

4. **Descriptor standard** - Modern Bitcoin uses descriptors (wpkh, wsh, tr, etc.)

**Use Cases:**

- User wants to display Bitcoin balance on profile
- Proof of funds (verify user controls certain addresses)
- Address labeling and organization

**Alternatives Considered:**

- **No wallet features** - Simpler but less useful
- **Full wallet support** - Would require storing private keys (NEVER)
- **Manual address entry** - Works but less convenient

**Trade-offs Accepted:**

- Users must understand watch-only vs full wallet
- Can't spend from HODLXXI (good thing!)
- Bitcoin Core RPC required for balance checks

**How to Know This Was Wrong:**

If you find yourself:
- Watch-only feature constantly causing confusion
- Bitcoin Core RPC costs (time/bandwidth) exceed value provided
- Feature barely used

Then simplify or remove. Wallet features are nice-to-have, not core to mission.

---

### ADR-016: Why Proof of Funds with Privacy Levels

**Decision:** Support three privacy levels for proving funds: boolean, threshold, aggregate

**Reasoning:**

1. **Privacy options** - Not everyone wants to reveal exact balance.

2. **Use case flexibility**:
   - Boolean: "I have any Bitcoin" (minimum privacy leak)
   - Threshold: "I have more than X Bitcoin" (e.g., 1 BTC for verification)
   - Aggregate: "I have exactly X Bitcoin" (maximum transparency)

3. **PSBT-based** - Proof of Funds uses PSBT (Partially Signed Bitcoin Transaction) standard.

4. **Challenge-response** - Server creates challenge. User signs PSBT. Server verifies.

**Alternatives Considered:**

- **Only exact balance** - Privacy leak
- **No proof of funds** - Useful feature for credibility
- **Message signing only** - Proves ownership but not amount

**Trade-offs Accepted:**

- Three implementations to maintain (boolean, threshold, aggregate)
- PSBT complexity
- Users must understand privacy implications

**How to Know This Was Wrong:**

If you find yourself:
- PoF feature causing privacy problems
- PSBT verification constantly breaking
- Feature rarely used

Then simplify to message signing only. PoF is nice-to-have, not essential.

---

## API Design

### ADR-017: Why REST + OpenID Connect Discovery

**Decision:** Use REST endpoints + OIDC discovery endpoints

**Reasoning:**

1. **OIDC standard** - `.well-known/openid-configuration` is how OAuth providers advertise capabilities.

2. **Auto-configuration** - OAuth clients can auto-discover endpoints.

3. **REST simplicity** - HTTP verbs (GET/POST) match operations (read/write).

4. **Existing tooling** - Postman, curl, HTTPie all work naturally with REST.

**Key Endpoints:**

- `/.well-known/openid-configuration` - OIDC discovery
- `/oauth/jwks.json` - Public keys for JWT verification
- `/oauth/authorize` - Authorization endpoint
- `/oauth/token` - Token endpoint
- `/oauth/introspect` - Token introspection
- `/oauth/revoke` - Token revocation

**Alternatives Considered:**

- **GraphQL** - More flexible but more complex
- **gRPC** - Performance benefits but not HTTP-friendly
- **Custom protocol** - Would prevent standard client libraries from working

**Trade-offs Accepted:**

- REST is somewhat verbose (multiple round trips for OAuth flow)
- HTTP overhead vs binary protocols
- More standard = less flexibility

**How to Know This Was Wrong:**

If you find yourself:
- Constantly fighting REST/HTTP limitations
- Needing real-time updates that HTTP polling can't provide (but we have WebSocket for that)
- OAuth clients can't auto-discover due to OIDC issues

Then reconsider. But REST + OIDC is the safe, boring choice. That's good for 17 years.

---

### ADR-018: Why JWT with RS256/HS256

**Decision:** Support both RS256 (public key) and HS256 (HMAC) JWT signing

**Reasoning:**

1. **RS256 for distributed verification** - Anyone can verify JWT with public key from `/oauth/jwks.json`.

2. **HS256 for simplicity** - When tokens stay between client and HODLXXI, HMAC is simpler.

3. **Standard algorithm** - Both are IETF standards. All JWT libraries support them.

4. **Rotation capability** - Can rotate signing keys without breaking all tokens.

**When to Use Which:**

- **RS256** - When third parties need to verify tokens (API gateways, microservices)
- **HS256** - When only client and HODLXXI verify tokens (simpler key management)

**Alternatives Considered:**

- **Only RS256** - More complex key management
- **Only HS256** - Doesn't support distributed verification
- **EdDSA** - Newer but less widely supported in 2024

**Trade-offs Accepted:**

- Must maintain both signing algorithms
- Key rotation complexity
- Must expose public keys via JWKS endpoint

**How to Know This Was Wrong:**

If you find yourself:
- Constantly rotating keys due to compromise
- JWT signature verification breaking across different libraries
- Key management overhead exceeding benefit

Then pick one algorithm and stick with it. But having both provides flexibility.

---

## Deployment Architecture

### ADR-019: Why Single-Server Deployment

**Decision:** Design for single server deployment, not distributed systems

**Reasoning:**

1. **Cost** - One server costs $50-100/month. Multiple servers cost much more.

2. **Simplicity** - No load balancer, no service discovery, no distributed tracing.

3. **Single maintainer** - One person can manage one server. Distributed systems require teams.

4. **Sufficient capacity** - Modern VPS can handle thousands of users with vertical scaling.

5. **17-year timeline** - Simple systems survive longer.

**Single Server Components:**

```
┌────────────────────────────────────┐
│         Reverse Proxy (Nginx)      │  ← TLS termination
├────────────────────────────────────┤
│    Gunicorn + Flask + SocketIO     │  ← Application
├────────────────────────────────────┤
│         PostgreSQL + Redis         │  ← Data layer
├────────────────────────────────────┤
│          Bitcoin Core RPC          │  ← Blockchain
├────────────────────────────────────┤
│           TURN Server              │  ← WebRTC (optional)
└────────────────────────────────────┘
```

All on one box.

**Alternatives Considered:**

- **Kubernetes cluster** - Massive overkill. Requires team to manage.
- **Serverless** - Not suitable for WebSocket, Bitcoin Core, or long-running connections.
- **Multi-server** - Costs more, more complex, unnecessary for expected load.

**Trade-offs Accepted:**

- Single point of failure (acceptable - this is reference implementation, not AWS)
- Vertical scaling only (add RAM/CPU to same server)
- Downtime during server maintenance (acceptable - announce maintenance window)

**When to Revisit:**

If HODLXXI grows to >10,000 active users, reconsider. But for 17-year mission, single server is right.

**How to Know This Was Wrong:**

If you find yourself:
- Constantly hitting resource limits on largest available VPS
- Downtime unacceptable due to critical usage
- Geographic distribution needed (users in Asia + USA)

Then consider multi-region deployment. But you'll need funding and team for that.

---

### ADR-020: Why Docker Optional, Not Required

**Decision:** Docker is optional deployment method, not the only way

**Reasoning:**

1. **Multiple deployment options** - Docker, virtualenv, system packages all work.

2. **Server flexibility** - Can deploy directly on Ubuntu without Docker complexity.

3. **Resource efficiency** - No Docker overhead if deploying directly.

4. **Simplicity** - `python app.py` is simpler than Docker Compose for small deployments.

**When to Use Docker:**

- Reproducible deployments
- Isolation from system packages
- Easy rollback to previous version
- Development environment matching production

**When Not to Use Docker:**

- Minimal server (Docker overhead matters)
- Direct deployment preferred
- Don't want to learn Docker

**Trade-offs Accepted:**

- Two deployment methods to document
- Docker image must be maintained
- Docker adds slight complexity

**How to Know This Was Wrong:**

If you find yourself:
- Constantly fixing deployment differences between Docker and virtualenv
- Docker image out of date with code changes
- Maintaining two deployment paths exceeds benefit

Then pick one deployment method. Delete the other documentation.

---

### ADR-021: Why Nginx Reverse Proxy

**Decision:** Use Nginx in front of Gunicorn for TLS and static assets

**Reasoning:**

1. **TLS termination** - Nginx handles HTTPS. Gunicorn doesn't need to.

2. **Static assets** - Nginx serves JS/CSS/images faster than Flask.

3. **Rate limiting** - Nginx can rate limit at network layer (faster than application).

4. **WebSocket proxying** - Nginx can proxy WebSocket connections correctly.

5. **Maturity** - Nginx has been stable since 2004. Not going anywhere.

**Configuration Pattern:**

```nginx
server {
    listen 443 ssl http2;
    server_name hodlxxi.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /static/ {
        alias /app/static/;
    }

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**Alternatives Considered:**

- **No reverse proxy** - Gunicorn exposed directly. No TLS, no static file optimization.
- **Caddy** - Simpler but less mature. Automatic TLS is nice though.
- **Traefik** - Good for Docker but unnecessary for single server.

**Trade-offs Accepted:**

- Must configure Nginx correctly
- Another service to monitor
- TLS certificate renewal (certbot helps)

**How to Know This Was Wrong:**

If you find yourself:
- Nginx constantly misconfigured
- TLS certificate renewal failing
- Simpler reverse proxy would work

Then consider Caddy. But Nginx is battle-tested and well-documented.

---

## What We Deliberately Did NOT Build

### Non-Decision 001: No User Interface Framework

**What We Didn't Do:** Use React, Vue, Angular, etc.

**Why Not:**

- HODLXXI is primarily an API service
- Admin pages are minimal and rare
- JavaScript framework churn would require constant updates
- Plain HTML + vanilla JS is simpler and lasts longer

**What We Use Instead:**

- Jinja2 templates (built into Flask)
- Vanilla JavaScript for interactive bits
- Bootstrap CSS for styling (optional)

**When to Revisit:**

If HODLXXI grows a complex admin dashboard, then a framework makes sense. But for API service, keep it simple.

---

### Non-Decision 002: No Background Job Queue

**What We Didn't Do:** Celery, RQ, or similar task queues

**Why Not:**

- No long-running background jobs currently needed
- Adds complexity (worker processes, message broker)
- Can add later if needed (Redis already available)

**What We Use Instead:**

- Synchronous processing (fast enough)
- Redis for caching (already have it)
- Cron jobs for scheduled tasks (if needed)

**When to Revisit:**

If we need to:
- Send emails (auth codes, notifications)
- Process blockchain data asynchronously
- Generate reports in background

Then add Celery. But don't pre-optimize.

---

### Non-Decision 003: No Microservices

**What We Didn't Do:** Split into separate services (auth service, wallet service, chat service)

**Why Not:**

- Single maintainer can't manage multiple services
- Network calls between services add latency
- Distributed systems are exponentially more complex
- Monolith is simpler to deploy and debug

**What We Use Instead:**

- Modular monolith (separate modules in one codebase)
- Clear boundaries between functional areas
- Can split later if needed

**When to Revisit:**

If we need to:
- Scale different components independently
- Have multiple teams working on different services
- Deploy changes without affecting other services

Then consider microservices. But monolith is right for single maintainer.

---

### Non-Decision 004: No NoSQL Database

**What We Didn't Do:** MongoDB, Cassandra, DynamoDB, etc.

**Why Not:**

- SQL is better for relational data (users → sessions → tokens)
- PostgreSQL's JSONB handles unstructured data if needed
- NoSQL adds complexity without clear benefit
- PostgreSQL is simpler to backup and restore

**What We Use Instead:**

- PostgreSQL for everything
- Redis for cache/session store (key-value is fine here)

**When to Revisit:**

If we need to:
- Store massive amounts of unstructured data
- Scale writes beyond single PostgreSQL server
- Geographic distribution with eventual consistency

Then consider NoSQL. But PostgreSQL serves us fine.

---

### Non-Decision 005: No Blockchain Indexer

**What We Didn't Do:** Build custom blockchain indexer like block explorers have

**Why Not:**

- Bitcoin Core RPC provides what we need
- Indexing entire blockchain requires massive storage
- Would need to maintain sync logic
- Adds complexity without clear benefit

**What We Use Instead:**

- Bitcoin Core RPC for blockchain queries
- Watch-only wallets for address monitoring
- Third-party block explorers for UI links (not critical path)

**When to Revisit:**

If we need to:
- Query historical transactions at scale
- Build block explorer features
- Support non-Bitcoin chains

Then consider indexer. But RPC works fine for our needs.

---

### Non-Decision 006: No Lightning Node Integration (Yet)

**What We Didn't Do:** Run LND or CLN node as part of HODLXXI

**Why Not:**

- Lightning Network is still evolving
- Channel management requires constant attention
- LNURL-auth doesn't require running a node
- Would add significant operational complexity

**What We Use Instead:**

- LNURL-auth verifies signatures (no node needed)
- Future: could integrate LND for payments
- Users run their own Lightning wallets

**When to Revisit:**

If we want to:
- Accept Lightning payments for premium tiers
- Provide Lightning wallet services
- Build Lightning-native features

Then integrate LND. But LNURL-auth works without it.

---

### Non-Decision 007: No Multi-Tenancy

**What We Didn't Do:** Build system where others run isolated HODLXXI instances on our infrastructure

**Why Not:**

- hodlxxi.com is reference implementation
- Others should run their own servers
- Multi-tenancy adds massive complexity
- Don't want to be responsible for others' uptime

**What We Use Instead:**

- Open source code
- Deployment documentation
- Others fork and deploy independently

**When to Revisit:**

If there's demand for hosted service AND funding to support it, reconsider. But reference implementation model is better for mission.

---

## Conclusion: Architecture for 17 Years

This document captures the reasoning behind HODLXXI's architecture as of November 2025. When you return to this code in 2030, 2035, or 2040, read this document first.

**The Core Principles:**

1. **Simplicity** - Simple systems survive. Complex systems fail.
2. **Maturity** - Use technologies that have existed 10+ years and will exist 10+ more.
3. **Non-custodial** - Never store private keys. Never control funds.
4. **Standard protocols** - OAuth2, OIDC, JWT, Bitcoin, Lightning standards.
5. **Single maintainer** - Every decision assumes one person managing everything.
6. **Public utility** - This is infrastructure for human freedom, not a business.

**When Architecture Decisions Should Change:**

- If maintaining code exceeds the value it provides
- If technologies become unmaintained or obsolete
- If usage patterns differ drastically from assumptions
- If regulatory environment requires changes

But don't change for change's sake. Boring architecture is good architecture for 17 years.

**The Mission Remains:**

HODLXXI bridges web2 and web3. It speaks OAuth2 to applications and Bitcoin to users. It demonstrates that Bitcoin-based identity is practical. It provides an alternative to corporate authentication.

This architecture serves that mission. Protect it. Maintain it. Keep it running.

---

**Document History:**

- 2025-11-04: Initial ADR document created
- Future updates: Document all major architectural changes here

**Contact for Clarifications:**

If you're reading this in 2035 and have questions, hopefully past-you left better contact info. But the reasoning is captured here. Trust it.
