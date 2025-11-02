# HODLXXI - Universal Bitcoin Identity Layer

> A production-intended Bitcoin API combining OAuth2/OpenID Connect with Lightning Network authentication

## ⚠️ ALPHA WARNING

**This software is in active development and should be considered ALPHA quality.**

- ⚠️ **NO CUSTODY**: This system never holds or controls user funds. All operations are non-custodial.
- ⚠️ **DO NOT TRUST WITH FUNDS**: Use only with watch-only wallets for testing and development.
- ⚠️ **API SURFACE WILL CHANGE**: Endpoints, request/response formats, and authentication flows may change without notice.
- ⚠️ **SECURITY REVIEW ONGOING**: This code has not undergone formal security audit. Do not use in production without thorough review.
- ⚠️ **TEST ENVIRONMENT ONLY**: Intended for development, testing, and experimentation on testnet/regtest.

**For production use**: Wait for v1.0 stable release after security audit completion.

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![Bitcoin](https://img.shields.io/badge/bitcoin-24.0+-orange.svg)](https://bitcoin.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

[**Documentation**](app/README.md) •
[**Quick Start**](#quick-start) •
[**API Reference**](app/API_RESPONSE_EXAMPLES.md) •
[**Architecture**](ARCHITECTURE.md) •
[**Contributing**](CONTRIBUTING.md)

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Demo](#demo)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Architecture](#architecture)
- [Development](#development)
- [Deployment](#deployment)
- [Testing](#testing)
- [Contributing](#contributing)
- [Changelog](#changelog)
- [Support](#support)
- [License](#license)

---

## 🌟 Overview

HODLXXI is a **universal Bitcoin identity layer** that bridges Web2 and Web3 authentication systems. It provides a comprehensive API for building Bitcoin-powered applications with security-focused design, combining traditional OAuth2/OIDC authentication with Lightning Network's LNURL-Auth protocol.

### Why HODLXXI?

- **🔐 Universal Authentication**: Support both traditional OAuth2 and Lightning Network authentication in one system
- **⚡ Lightning Integration**: Native LNURL-Auth (LUD-04) support for seamless Lightning wallet authentication
- **🔒 Non-Custodial**: Never store or control user private keys - cryptographic verification only
- **🛡️ Security-Focused**: Design emphasizes rate limiting, signature verification, and audit logging capabilities
- **📊 Alpha Quality**: Under active development with test coverage in progress
- **🚀 Developer Friendly**: 190+ KB of comprehensive documentation with examples

---

## ✨ Features

### Authentication & Authorization

- **🔐 OAuth2/OpenID Connect Provider**
  - Authorization code flow (basic implementation)
  - Discovery endpoint (`/.well-known/openid-configuration`) - *planned*
  - Support for `openid`, `profile`, and `email` scopes
  - **Roadmap**: PKCE support, token refresh with rotation, JWKS endpoint

- **⚡ LNURL-Auth Integration (LUD-04)**
  - Lightning Network authentication
  - QR code generation
  - Cryptographic signature verification
  - Seamless wallet integration

- **✍️ Bitcoin Signature Verification**
  - Native Bitcoin cryptographic signatures
  - Message signing and verification
  - Public key-based identity

### Bitcoin Operations

- **💼 Wallet Management**
  - Multi-wallet support
  - Encrypted wallet operations
  - Address generation and management
  - Transaction history
  - Balance queries

- **🔍 Proof of Funds (Non-Custodial)**
  - PSBT-based balance verification
  - Multiple privacy levels (boolean, threshold, aggregate)
  - Challenge-response authentication
  - Time-limited proofs (1 hour validity)
  - No custody required

### Communication

- **💬 Real-time Chat**
  - WebSocket-based messaging
  - User-to-user direct messaging
  - Channel/room support
  - Encrypted message transmission
  - Typing indicators and read receipts
  - Message history

### Security & Monitoring

- **🛡️ Security Features**
  - CORS configuration support
  - Session management
  - Input validation and sanitization
  - Signature verification for Bitcoin/Lightning operations
  - **Roadmap**: Comprehensive rate limiting, CSRF protection, TLS enforcement, formal audit logging

- **📊 Observability**
  - Health check endpoint (basic)
  - Request/response logging
  - **Roadmap**: Prometheus metrics endpoint, performance metrics, error tracking dashboard

---

## 🎥 Demo

**Coming Soon**: Live demo deployment at https://demo.hodlxxi.com

### Screenshots

<div align="center">
<table>
  <tr>
    <td><b>OAuth2 Flow</b></td>
    <td><b>LNURL-Auth</b></td>
    <td><b>Proof of Funds</b></td>
  </tr>
  <tr>
    <td><i>Coming soon</i></td>
    <td><i>Coming soon</i></td>
    <td><i>Coming soon</i></td>
  </tr>
</table>
</div>

---

## 🔗 Bitcoin Node Requirements

HODLXXI requires a Bitcoin Core node with specific configuration:

### Required Bitcoin Core Setup

- **Version**: Bitcoin Core 24.0 or higher
- **RPC Access**: Must be accessible via RPC (enabled by default)
- **Watch-Only Wallets**: All wallets MUST be watch-only (`disable_private_keys=true`)
  ```bash
  bitcoin-cli createwallet "mywallet" false false "" false true
  ```
- **No Private Keys**: HODLXXI never handles, stores, or requires private keys
- **Network**: Recommended to start with testnet or regtest for development

### Recommended Bitcoin Core Configuration

For optimal functionality, configure Bitcoin Core with:

- **Descriptor Wallets**: Required for covenant explorer and advanced features
  ```
  # bitcoin.conf
  descriptors=1
  ```
- **Transaction Index**: Required for proof-of-funds verification
  ```
  # bitcoin.conf
  txindex=1
  ```
- **RPC Configuration**:
  ```
  # bitcoin.conf
  server=1
  rpcuser=your_rpc_user
  rpcpassword=your_secure_password
  rpcallowip=127.0.0.1
  rpcport=8332
  ```

### Security Notes

- ✅ **Non-Custodial by Design**: HODLXXI never takes custody of user funds
- ✅ **Watch-Only Operation**: All wallet operations use public keys only
- ✅ **Cryptographic Verification**: Identity verification through signatures, never private key exposure
- ⚠️ **Network Isolation**: For production, ensure Bitcoin RPC is not exposed to public internet
- ⚠️ **Access Control**: Use strong RPC credentials and firewall rules

---

## 🚀 Quick Start

### Prerequisites

- **Python** 3.8 or higher
- **Bitcoin Core** 24.0+ (configured as described above)
- **PostgreSQL** 15+ (or in-memory storage for development)
- **Redis** 7+ (optional, for production caching)

### Installation

#### Option 1: Local Installation (Recommended for Alpha)

```bash
# Clone the repository
git clone https://github.com/alnostru/Universal-Bitcoin-Identity-Layer.git
cd Universal-Bitcoin-Identity-Layer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Bitcoin RPC credentials
# (Note: In-memory storage is used by default for alpha - no database setup required)

# Run the application
python app/app.py
```

#### Option 2: Docker Deployment

**Status**: Docker deployment is currently in development.

Docker configuration files (`Dockerfile` and `docker-compose.yml`) are provided but should be considered experimental. For alpha testing, please use the local installation method above.

Docker deployment will be production-ready in a future release.

### First Steps

1. **Access the API**:
   ```bash
   curl http://localhost:5000/health
   ```

2. **Get OpenID Configuration**:
   ```bash
   curl http://localhost:5000/.well-known/openid-configuration
   ```

3. **Try LNURL-Auth**:
   ```bash
   curl http://localhost:5000/api/lnurl-auth/login
   ```

4. **View Metrics** (optional):
   ```bash
   curl http://localhost:5000/metrics
   ```

### Example Usage

#### Python Client

```python
import requests

# 1. LNURL-Auth Login
response = requests.get('http://localhost:5000/api/lnurl-auth/login')
challenge = response.json()

# User signs challenge with Lightning wallet...

# 2. Verify signature
response = requests.get(
    'http://localhost:5000/api/lnurl-auth/verify',
    params={
        'k1': challenge['k1'],
        'sig': signature,
        'key': public_key
    }
)
session_token = response.json()['session_token']

# 3. Use authenticated API
headers = {'Authorization': f'Bearer {session_token}'}
profile = requests.get('http://localhost:5000/api/users/profile', headers=headers)
print(profile.json())
```

#### JavaScript Client

```javascript
// 1. Get LNURL-Auth challenge
const challengeResponse = await fetch('http://localhost:5000/api/lnurl-auth/login');
const { k1, callback } = await challengeResponse.json();

// User scans QR code with Lightning wallet...

// 2. After wallet callback, get session
const sessionResponse = await fetch('/api/session');
const { access_token } = await sessionResponse.json();

// 3. Use authenticated API
const profileResponse = await fetch('http://localhost:5000/api/users/profile', {
    headers: { 'Authorization': `Bearer ${access_token}` }
});
const profile = await profileResponse.json();
console.log(profile);
```

---

## 📚 Documentation

HODLXXI includes **190+ KB** of comprehensive documentation across 9 files:

| Document | Size | Description |
|----------|------|-------------|
| [**Complete Documentation**](app/README.md) | 14 KB | Documentation index and quick start |
| [**API Reference**](app/API_RESPONSE_EXAMPLES.md) | 17 KB | All endpoints with request/response examples |
| [**Error Codes**](app/ERROR_CODE_DOCUMENTATION.md) | 24 KB | Complete error code reference (1000-7099) |
| [**OAuth2/LNURL Spec**](app/OAUTH_LNURL_SPECIFICATION.md) | 48 KB | Authentication implementation details |
| [**Security Guide**](app/SECURITY_REQUIREMENTS.md) | 31 KB | Security architecture and best practices |
| [**Token Policies**](app/TOKEN_POLICIES.md) | 33 KB | Token lifecycle and refresh mechanisms |
| [**Production Deployment**](app/PRODUCTION_DEPLOYMENT.md) | 29 KB | Complete deployment guide |
| [**Privacy Policy**](app/PRIVACY_POLICY.md) | 9 KB | Privacy policy template |
| [**Terms of Service**](app/TERMS_OF_SERVICE.md) | 15 KB | Terms of service template |

### Additional Documentation

- [**Architecture**](ARCHITECTURE.md) - System architecture and design
- [**Changelog**](CHANGELOG.md) - Version history and release notes
- [**Testing Guide**](TESTING.md) - Comprehensive testing documentation
- [**Troubleshooting**](TROUBLESHOOTING.md) - Common issues and solutions
- [**Contributing**](CONTRIBUTING.md) - Contribution guidelines
- [**Code of Conduct**](CODE_OF_CONDUCT.md) - Community guidelines

---

## 🏗️ Architecture

HODLXXI follows a modular, layered architecture designed for security and scalability:

```
┌─────────────────────────────────────────────────────┐
│                 Client Applications                  │
│  (Web Apps, Mobile Apps, Lightning Wallets)         │
└──────────────────┬──────────────────────────────────┘
                   │
                   │ HTTPS / WebSocket
                   │
┌──────────────────┴──────────────────────────────────┐
│            API Gateway / Load Balancer               │
│  (Rate Limiting, TLS Termination, DDoS Protection)  │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────┐
│              HODLXXI Application Layer               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │  OAuth2  │ │  LNURL   │ │  Wallet  │            │
│  │  Module  │ │  Module  │ │  Module  │            │
│  └──────────┘ └──────────┘ └──────────┘            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │   PoF    │ │   Chat   │ │   API    │            │
│  │  Module  │ │  Module  │ │  Module  │            │
│  └──────────┘ └──────────┘ └──────────┘            │
└──────────┬──────────────────────┬───────────────────┘
           │                      │
┌──────────┴──────────┐  ┌───────┴────────────────────┐
│   PostgreSQL        │  │  Bitcoin Core Node         │
│   (Database)        │  │  (Blockchain & RPC)        │
└─────────────────────┘  └────────────────────────────┘
```

**Key Components:**
- **OAuth2/OIDC Module**: Authorization and token management
- **LNURL Module**: Lightning Network authentication
- **Wallet Module**: Bitcoin wallet operations
- **PoF Module**: Proof of funds verification
- **Chat Module**: Real-time messaging

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 🛠️ Development

### Development Setup

```bash
# Clone and setup
git clone https://github.com/alnostru/Universal-Bitcoin-Identity-Layer.git
cd Universal-Bitcoin-Identity-Layer

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Setup pre-commit hooks
pre-commit install

# Configure for development
cp .env.example .env
export FLASK_ENV=development
export FLASK_DEBUG=1

# Start Bitcoin regtest
bitcoind -regtest -daemon -server -rpcuser=test -rpcpassword=test

# Run the app
python app/app.py
```

### Code Style

We use [Black](https://github.com/psf/black) for code formatting:

```bash
# Format code
black app/

# Check formatting
black --check app/

# Lint
flake8 app/
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test category
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run in watch mode
ptw
```

See [TESTING.md](TESTING.md) for comprehensive testing documentation.

---

## 🚀 Deployment

### Production Deployment

See [PRODUCTION_DEPLOYMENT.md](app/PRODUCTION_DEPLOYMENT.md) for complete production deployment guide.

**Quick production setup:**

```bash
# 1. Clone and configure
git clone https://github.com/alnostru/Universal-Bitcoin-Identity-Layer.git
cd Universal-Bitcoin-Identity-Layer
cp .env.example .env

# 2. Configure production environment
export FLASK_ENV=production
# Edit .env with production settings

# 3. Setup SSL/TLS
certbot certonly --standalone -d your-domain.com

# 4. Deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# 5. Verify deployment
curl https://your-domain.com/health
```

### Environment Variables

Key environment variables (see `.env.example` for full list):

```bash
# Flask
FLASK_ENV=production
SECRET_KEY=<generate-secure-key>

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/hodlxxi

# Bitcoin Core
BITCOIN_RPC_USER=<your-user>
BITCOIN_RPC_PASSWORD=<your-password>
BITCOIN_RPC_HOST=localhost
BITCOIN_RPC_PORT=8332

# Security
CORS_ORIGINS=https://your-app.com
RATE_LIMIT_DEFAULT=100/hour
```

### Monitoring

HODLXXI includes built-in monitoring:

- **Health Check**: `GET /health`
- **Metrics**: `GET /metrics` (Prometheus format)
- **Logs**: JSON-formatted application logs

Example Grafana dashboard configuration available in `/monitoring/grafana/`.

---

## 🧪 Testing

HODLXXI testing framework in development:

- **Unit Tests**: In progress
- **Integration Tests**: In progress
- **E2E Tests**: In progress
- **Security Tests**: Planned
- **Performance Tests**: Planned

**Current Status**: Test coverage in active development. Contributions welcome!

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run specific test categories
pytest tests/unit/           # Unit tests
pytest tests/integration/    # Integration tests
pytest tests/e2e/           # End-to-end tests
pytest tests/security/      # Security tests
```

See [TESTING.md](TESTING.md) for detailed testing documentation.

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Contribution Guide

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests
4. **Run tests**: `pytest`
5. **Commit**: `git commit -m 'Add amazing feature'`
6. **Push**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Development Guidelines

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use [Black](https://github.com/psf/black) for code formatting
- Write tests for new features
- Update documentation as needed
- Follow [conventional commits](https://www.conventionalcommits.org/)

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for community guidelines.

---

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

### Latest Release: v1.0.0 (2025-10-31)

**Highlights:**
- ✅ Complete OAuth2/OIDC implementation
- ✅ LNURL-Auth integration (LUD-04)
- ✅ Proof of Funds non-custodial verification
- ✅ Real-time chat with WebSocket
- ✅ 190+ KB comprehensive documentation
- ✅ Production-ready with monitoring

---

## 📞 Support

### Getting Help

- **📖 Documentation**: Check [app/README.md](app/README.md) first
- **🐛 Bug Reports**: [Create an issue](https://github.com/alnostru/Universal-Bitcoin-Identity-Layer/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/alnostru/Universal-Bitcoin-Identity-Layer/discussions)
- **📧 Email**: support@hodlxxi.com
- **🔒 Security**: security@hodlxxi.com (for security issues only)

### Troubleshooting

Common issues and solutions: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 🗺️ Roadmap

### Core Security & Standards (Priority)

- [ ] **PKCE Support**: OAuth2 PKCE (Proof Key for Code Exchange) for public clients
- [ ] **JWKS Endpoint**: JSON Web Key Set for public key discovery
- [ ] **Rotating Refresh Tokens**: Secure token refresh with automatic rotation
- [ ] **Comprehensive Rate Limiting**: Per-endpoint rate limiting with Redis backend
- [ ] **CSRF Protection**: Cross-Site Request Forgery protection for all state-changing operations
- [ ] **TLS Enforcement**: Strict HTTPS/TLS requirements for production
- [ ] **Formal Audit Logging**: Structured audit log streaming and retention
- [ ] **Security Audit**: Professional third-party security assessment

### Observability & Operations

- [ ] **Prometheus Metrics**: `/metrics` endpoint with comprehensive application metrics
- [ ] **Grafana Dashboards**: Pre-built dashboards for monitoring
- [ ] **Health Check Enhancements**: Detailed health checks for all dependencies
- [ ] **Structured Logging**: JSON-formatted logs for better parsing
- [ ] **Error Tracking Integration**: Sentry/rollbar integration

### Compliance & Documentation

- [ ] **SOC2 Compliance Path**: Documentation and controls for SOC2 Type II
- [ ] **SLA Framework**: Service Level Agreement definitions and monitoring
- [ ] **99.9% Uptime Target**: High availability architecture and monitoring

### Feature Enhancements

- [ ] **Multi-signature Wallet Support**: Advanced multi-sig descriptor support
- [ ] **Lightning Channel Management UI**: Channel opening, closing, and monitoring
- [ ] **Mobile SDKs**: Native iOS and Android SDKs
- [ ] **Webhook Support**: Event-driven webhooks for integrations
- [ ] **GraphQL API**: Alternative API interface
- [ ] **Advanced Proof of Funds**: Enhanced privacy levels and aggregation
- [ ] **Extended Lightning Wallet Integration**: Support for more Lightning implementations

See [GitHub Projects](https://github.com/alnostru/Universal-Bitcoin-Identity-Layer/projects) for detailed roadmap and progress tracking.

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 HODLXXI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

---

## 🙏 Acknowledgments

- **Bitcoin Core Team** - For the robust Bitcoin implementation
- **Lightning Network Developers** - For LNURL specification
- **Flask Community** - For the excellent web framework
- **Open Source Community** - For inspiration and collaboration

---

## 🔗 Links

- **Website**: https://hodlxxi.com
- **Documentation**: [app/README.md](app/README.md)
- **GitHub**: https://github.com/alnostru/Universal-Bitcoin-Identity-Layer
- **Issue Tracker**: https://github.com/alnostru/Universal-Bitcoin-Identity-Layer/issues
- **Bitcoin Core**: https://bitcoin.org/en/developer-documentation
- **Lightning Network**: https://lightning.network/
- **LNURL Specification**: https://github.com/lnurl/luds
- **OAuth 2.0 RFC**: https://tools.ietf.org/html/rfc6749
- **OpenID Connect**: https://openid.net/connect/

---

<div align="center">

**Made with ⚡ by the HODLXXI Team**

**HODL wisely, code securely** 🔐

[⬆ Back to Top](#hodlxxi---universal-bitcoin-identity-layer)

</div>
