# Security Policy

## Supported Versions

We release security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**Please do NOT report security vulnerabilities through public GitHub issues.**

We take security seriously. If you discover a security vulnerability, please follow these steps:

### 1. Email Us

Send details to: **security@hodlxxi.com**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)
- Your contact information

### 2. What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 1 week
- **Regular Updates**: Every 7 days until resolved
- **Resolution Timeline**: Varies by severity
  - Critical: 7 days
  - High: 30 days
  - Medium: 90 days
  - Low: Next release cycle

### 3. Responsible Disclosure

We ask that you:
- Give us reasonable time to fix the issue
- Don't publicly disclose until we've released a fix
- Don't exploit the vulnerability
- Act in good faith

### 4. Recognition

Security researchers who responsibly disclose vulnerabilities will be:
- Acknowledged in our SECURITY.md (unless you prefer to remain anonymous)
- Listed in release notes for the fix
- Eligible for our bug bounty program (details below)

## Security Best Practices

### For Users/Operators

#### Production Deployment

1. **Never commit secrets** - Use environment variables
2. **Use HTTPS/TLS** - Always encrypt traffic
3. **Secure Bitcoin RPC** - Use strong passwords, firewall rules
4. **Keep updated** - Apply security patches promptly
5. **Monitor logs** - Watch for suspicious activity
6. **Use strong secrets** - Generate cryptographically secure keys
7. **Backup regularly** - Maintain secure backups
8. **Limit access** - Follow principle of least privilege

#### Essential Security Configurations

```bash
# Generate secure Flask secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Set secure environment variables
export FLASK_SECRET_KEY="your_secure_key_here"
export RATE_LIMIT_ENABLED=true
export CSRF_PROTECTION=true
export CORS_ORIGINS="https://yourdomain.com"
```

See [SECURITY_REQUIREMENTS.md](app/SECURITY_REQUIREMENTS.md) for comprehensive security guidelines.

### For Developers/Contributors

#### Secure Coding Guidelines

1. **Input Validation**
   - Validate all user inputs
   - Use parameterized queries
   - Sanitize data before display

2. **Authentication & Authorization**
   - Verify signatures properly
   - Check permissions on all endpoints
   - Use secure session management

3. **Cryptography**
   - Use established libraries (never roll your own crypto)
   - Use secure random number generators
   - Follow current best practices

4. **Dependencies**
   - Keep dependencies updated
   - Review security advisories
   - Use `safety check` and `bandit`

5. **Error Handling**
   - Don't leak sensitive information in errors
   - Log security events
   - Handle edge cases

#### Code Review Checklist

- [ ] No hardcoded secrets or credentials
- [ ] Input validation on all user inputs
- [ ] Proper authentication/authorization checks
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities
- [ ] Rate limiting on sensitive endpoints
- [ ] Secure random number generation
- [ ] Proper error handling
- [ ] Logging of security events
- [ ] HTTPS enforced where needed

## Known Security Considerations

### Bitcoin Operations

- **Private Key Security**: Never log or expose private keys
- **RPC Security**: Secure Bitcoin Core RPC with strong passwords and firewall
- **Transaction Validation**: Always validate transactions before broadcasting
- **Wallet Encryption**: Use encrypted wallets in production

### Authentication

- **LNURL-Auth**: Session timeout enforced (5 minutes default)
- **OAuth2**: Short-lived access tokens with refresh token rotation
- **Signature Verification**: All signatures cryptographically verified
- **Rate Limiting**: Implemented on all authentication endpoints

### API Security

- **CORS**: Configure strict CORS policies in production
- **CSRF**: CSRF protection enabled for state-changing operations
- **Rate Limiting**: Per-IP and per-user rate limits
- **Input Validation**: All inputs validated and sanitized

### Data Protection

- **Encryption at Rest**: Sensitive data encrypted in database
- **Encryption in Transit**: HTTPS/TLS required in production
- **Session Security**: Secure session cookies with httpOnly and secure flags
- **Secrets Management**: Environment variables, never committed to repo

## Security Features

### Implemented

- ✅ Cryptographic signature verification
- ✅ Rate limiting (configurable)
- ✅ CORS protection
- ✅ CSRF protection
- ✅ Session management with timeouts
- ✅ Input validation and sanitization
- ✅ Comprehensive audit logging
- ✅ Secure password hashing (for OAuth clients)
- ✅ Token expiration and rotation
- ✅ Bitcoin wallet encryption support

### Planned

- 🔄 Multi-factor authentication (MFA)
- 🔄 Hardware security module (HSM) support
- 🔄 Advanced anomaly detection
- 🔄 Automated security testing
- 🔄 Security headers optimization

## Vulnerability Disclosure Timeline

When a vulnerability is reported:

1. **Day 0**: Vulnerability reported
2. **Day 1-2**: Acknowledgment sent to reporter
3. **Day 3-7**: Vulnerability assessed and validated
4. **Day 7-X**: Fix developed and tested
5. **Day X**: Security patch released
6. **Day X+7**: Public disclosure (coordinated with reporter)

## Security Updates

Security updates are released as:
- **Critical**: Immediate patch release
- **High**: Patch within 7 days
- **Medium**: Included in next minor release
- **Low**: Included in regular release cycle

Subscribe to security advisories:
- Watch this repository for security updates
- Follow [@hodlxxi](https://twitter.com/hodlxxi) on Twitter
- Subscribe to our security mailing list: security-announce@hodlxxi.com

## Bug Bounty Program

### Scope

In scope:
- HODLXXI API (hodlxxi.com)
- Authentication vulnerabilities
- Bitcoin transaction vulnerabilities
- Data exposure issues
- Injection vulnerabilities
- Cryptographic issues

Out of scope:
- Social engineering
- Physical attacks
- DDoS attacks
- Vulnerabilities in third-party services
- Issues in deprecated versions

### Rewards

Reward amounts based on severity:

| Severity | Bounty Range |
|----------|--------------|
| Critical | $500 - $2000 |
| High     | $250 - $500  |
| Medium   | $100 - $250  |
| Low      | $50 - $100   |

*Actual amount determined by impact and quality of report*

### Rules

1. Follow responsible disclosure
2. Don't access user data
3. Don't perform destructive testing
4. Don't test on production (use staging/testnet)
5. One vulnerability per report
6. First reporter gets the bounty

## Security Resources

### Documentation

- [Security Requirements](app/SECURITY_REQUIREMENTS.md) - Comprehensive security guide
- [Production Deployment](app/PRODUCTION_DEPLOYMENT.md) - Secure deployment practices
- [Token Policies](app/TOKEN_POLICIES.md) - Token security
- [OAuth Specification](app/OAUTH_LNURL_SPECIFICATION.md) - Authentication security

### External Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Bitcoin Security](https://bitcoin.org/en/secure-your-wallet)
- [LNURL Security](https://github.com/lnurl/luds)
- [OAuth 2.0 Security](https://tools.ietf.org/html/rfc6819)

## Contact

- **Security Issues**: security@hodlxxi.com
- **General Support**: support@hodlxxi.com
- **PGP Key**: Available at https://hodlxxi.com/pgp-key.asc

## Hall of Fame

We recognize security researchers who have helped improve HODLXXI security:

| Researcher | Vulnerability | Date |
|------------|---------------|------|
| *Your name could be here* | | |

---

**Thank you for helping keep HODLXXI and our users safe!**
