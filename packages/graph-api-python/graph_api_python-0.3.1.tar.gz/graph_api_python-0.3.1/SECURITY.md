# Security policy for the graph-api-python project

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible for receiving such patches depends on the CVSS v3.0 Rating:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

Please report (suspected) security vulnerabilities to **[security@yourdomain.com](mailto:security@yourdomain.com)** or through [GitHub Security Advisories](https://github.com/damylen/graph-api-python/security/advisories/new). You will receive a response from us within 48 hours. If the issue is confirmed, we will release a patch as soon as possible depending on complexity but historically within a few days.

## Security Features

This project includes several security measures:

### Automated Security Scanning
- **Bandit**: Static security analysis for Python code
- **Safety**: Known security vulnerabilities in dependencies
- **pip-audit**: OSV database scanning for vulnerabilities
- **GitHub Security Advisories**: Automated vulnerability scanning
- **Dependabot**: Automated dependency updates

### Secure Development Practices
- All GitHub Actions use pinned versions and minimal permissions
- Dependencies are regularly updated through Dependabot
- Code changes require review through pull requests
- Automated security scans run on all commits

### Security Headers and Best Practices
- No sensitive data in configuration files
- Secure defaults for all configurations
- Input validation and sanitization
- Proper error handling without information leakage

## Security Contacts

For security-related questions or concerns, please contact:
- **Primary**: [security@yourdomain.com](mailto:security@yourdomain.com)  
- **GitHub**: [@damylen](https://github.com/damylen)

## Acknowledgments

We appreciate the security research community and encourage responsible disclosure of security vulnerabilities.