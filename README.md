# HODLXXI - Bitcoin API with OAuth2 & LNURL-Auth

> A comprehensive Bitcoin Lightning Network API with OAuth2/OpenID Connect and LNURL-Auth authentication

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)](https://flask.palletsprojects.com/)

## Overview

HODLXXI is a production-ready Bitcoin API that combines traditional OAuth2/OpenID Connect authentication with Lightning Network's LNURL-Auth, providing a seamless authentication experience for both web and Lightning wallet users.

### Key Features

- **🔐 Multi-Auth System**: OAuth2/OIDC + LNURL-Auth (LUD-04)
- **⚡ Lightning Network**: Full Bitcoin Lightning integration
- **💬 Real-time Chat**: WebSocket-based encrypted messaging
- **🔒 Proof of Funds**: Cryptographic balance verification
- **🛡️ Enterprise Security**: Rate limiting, signature verification, MFA ready
- **📊 Production Ready**: Comprehensive monitoring, logging, and error handling

## Quick Start

### Prerequisites

- Python 3.8+
- Bitcoin Core (with RPC enabled)
- PostgreSQL or SQLite (for production)

### Installation

```bash
# Clone the repository
git clone https://github.com/hodlxxidemo/hodlxxi.com.git
cd hodlxxi.com

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your Bitcoin RPC credentials

# Run the application
python app/app.py
```

### Docker Setup (Recommended)

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

## Documentation

Comprehensive documentation is available in the `/app` directory:

| Document | Description | Size |
|----------|-------------|------|
| [📖 Complete Documentation](app/README.md) | Full documentation index and quick start | 14 KB |
| [🔌 API Reference](app/API_RESPONSE_EXAMPLES.md) | All endpoints with request/response examples | 17 KB |
| [❌ Error Codes](app/ERROR_CODE_DOCUMENTATION.md) | Complete error code reference | 24 KB |
| [🔐 OAuth2/LNURL Spec](app/OAUTH_LNURL_SPECIFICATION.md) | OAuth2/OIDC and LNURL-Auth implementation | 48 KB |
| [🔒 Security Guide](app/SECURITY_REQUIREMENTS.md) | Security architecture and best practices | 31 KB |
| [🎫 Token Policies](app/TOKEN_POLICIES.md) | Token lifecycle and refresh mechanisms | 33 KB |
| [🚀 Production Deployment](app/PRODUCTION_DEPLOYMENT.md) | Complete deployment guide | 29 KB |
| [📄 Privacy Policy](app/PRIVACY_POLICY.md) | Privacy policy template | 9 KB |
| [📜 Terms of Service](app/TERMS_OF_SERVICE.md) | Terms of service template | 15 KB |

**Total Documentation**: 190+ KB across 9 comprehensive files

## Features

### Authentication Methods

#### 1. LNURL-Auth (Lightning Wallet)
```javascript
// Create LNURL-auth session
const response = await fetch('/api/lnurl-auth/create', {
  method: 'POST'
});
const { lnurl, session_id } = await response.json();

// Display QR code to user
// User scans with Lightning wallet
// Poll for authentication completion
```

#### 2. OAuth2/OpenID Connect
```javascript
// Traditional OAuth2 flow
const authUrl = `/oauth/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&scope=openid profile wallet:read`;
window.location = authUrl;

// Handle callback and exchange code for tokens
const tokens = await exchangeCodeForTokens(code);
```

### API Endpoints

- **Authentication**: `/api/lnurl-auth/*`, `/oauth/*`
- **Wallet Operations**: `/api/wallet/*`
- **Chat System**: `/api/chat/*`
- **Proof of Funds**: `/api/pof/*`
- **User Management**: `/api/users/*`

See [API_RESPONSE_EXAMPLES.md](app/API_RESPONSE_EXAMPLES.md) for complete endpoint documentation.

### WebSocket Events

Real-time updates via Socket.IO:

```javascript
socket.on('chat_message', (data) => {
  console.log('New message:', data);
});

socket.on('wallet_update', (data) => {
  console.log('Balance changed:', data);
});
```

## Configuration

### Environment Variables

Key configuration options (see [.env.example](.env.example) for full list):

```bash
# Bitcoin RPC
RPC_USER=your_rpc_user
RPC_PASSWORD=your_rpc_password
RPC_HOST=127.0.0.1
RPC_PORT=8332
RPC_WALLET=your_wallet_name

# Flask
FLASK_SECRET_KEY=your_secret_key_here
FLASK_ENV=production

# Security
RATE_LIMIT_ENABLED=true
CORS_ORIGINS=https://yourdomain.com
```

## Security

HODLXXI implements defense-in-depth security:

- ✅ Cryptographic signature verification
- ✅ Rate limiting (configurable per endpoint)
- ✅ CORS and CSRF protection
- ✅ Encrypted session management
- ✅ Bitcoin wallet encryption
- ✅ TLS/SSL enforced in production
- ✅ Comprehensive audit logging

See [SECURITY_REQUIREMENTS.md](app/SECURITY_REQUIREMENTS.md) for complete security documentation.

### Reporting Security Issues

Please report security vulnerabilities to **security@hodlxxi.com**. See [SECURITY.md](SECURITY.md) for details.

## Development

### Project Structure

```
hodlxxi.com/
├── app/
│   ├── app.py                          # Main Flask application (9000+ lines)
│   ├── static/                         # Static assets
│   │   ├── matrix_rain.js
│   │   └── matrix_warp.js
│   └── [documentation files]
├── requirements.txt                    # Python dependencies
├── .env.example                        # Environment template
├── Dockerfile                          # Docker container config
├── docker-compose.yml                  # Docker Compose setup
└── README.md                           # This file
```

### Running Tests

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run with coverage
pytest --cov=app tests/
```

### Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Deployment

### Production Checklist

Before deploying to production, review:

- [ ] [Production Deployment Guide](app/PRODUCTION_DEPLOYMENT.md)
- [ ] [Security Requirements](app/SECURITY_REQUIREMENTS.md)
- [ ] All secrets in environment variables (not committed)
- [ ] SSL/TLS certificates configured
- [ ] Bitcoin Core node synced and secured
- [ ] Firewall rules configured
- [ ] Monitoring and alerting set up
- [ ] Backup system configured and tested

### Deployment Methods

**Docker** (Recommended):
```bash
docker-compose -f docker-compose.prod.yml up -d
```

**Systemd**:
```bash
sudo systemctl enable hodlxxi
sudo systemctl start hodlxxi
```

See [PRODUCTION_DEPLOYMENT.md](app/PRODUCTION_DEPLOYMENT.md) for detailed deployment instructions.

## API Integration Examples

### Python

```python
import requests

# Authenticate
response = requests.post('https://api.hodlxxi.com/oauth/token', json={
    'grant_type': 'client_credentials',
    'client_id': 'your_client_id',
    'client_secret': 'your_client_secret'
})
access_token = response.json()['access_token']

# Make authenticated request
headers = {'Authorization': f'Bearer {access_token}'}
balance = requests.get('https://api.hodlxxi.com/api/wallet/balance', headers=headers)
print(balance.json())
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

// OAuth2 authentication
const tokenResponse = await axios.post('https://api.hodlxxi.com/oauth/token', {
  grant_type: 'client_credentials',
  client_id: 'your_client_id',
  client_secret: 'your_client_secret'
});

const accessToken = tokenResponse.data.access_token;

// Make API call
const balance = await axios.get('https://api.hodlxxi.com/api/wallet/balance', {
  headers: { Authorization: `Bearer ${accessToken}` }
});
```

## Monitoring

HODLXXI includes comprehensive monitoring:

- **Prometheus** metrics endpoint: `/metrics`
- **Health check**: `/health`
- **Structured logging** with rotation
- **Error tracking** with detailed context

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: See [app/README.md](app/README.md)
- **Issues**: [GitHub Issues](https://github.com/hodlxxidemo/hodlxxi.com/issues)
- **Discussions**: [GitHub Discussions](https://github.com/hodlxxidemo/hodlxxi.com/discussions)
- **Email**: support@hodlxxi.com

## Roadmap

- [ ] Multi-signature wallet support
- [ ] Lightning Channel management UI
- [ ] Advanced analytics dashboard
- [ ] Mobile SDKs (iOS/Android)
- [ ] Webhook support for events
- [ ] GraphQL API endpoint

## Acknowledgments

- Bitcoin Core team
- Lightning Network developers
- Flask and Python community
- LNURL specification contributors

## Learn More

- [Bitcoin Core Documentation](https://bitcoin.org/en/developer-documentation)
- [Lightning Network](https://lightning.network/)
- [LNURL Specification](https://github.com/lnurl/luds)
- [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [OpenID Connect](https://openid.net/connect/)

---

**Made with ⚡ by the HODLXXI Team**

**HODL wisely, code securely** 🔐
