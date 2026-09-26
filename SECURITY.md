# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of HCS MovieForge seriously. If you believe you have found a security vulnerability, please do NOT create a public issue on GitHub.

Instead, please report the vulnerability privately by sending an email to:
**timfromhcs@gmail.com**

Please include:
- A description of the issue and potential impact
- Detailed steps to reproduce the vulnerability or proof-of-concept
- Any suggestions for remediation

You should receive an acknowledgment within 48 hours.

## Local Secret Protection

HCS MovieForge runs local-first and does not transmit project data or credentials to third-party cloud services without explicit configuration. All secret credentials (e.g., GitHub tokens, Hugging Face tokens) MUST be stored in `.env` or system keyrings and never committed to version control.
