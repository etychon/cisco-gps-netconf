# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | -------------------- |
| 2.0.x   | :white_check_mark:   |
| < 2.0   | :x:                  |

## Reporting a Vulnerability

If you discover a security issue, please **do not** open a public GitHub issue.

Instead, open a [private security advisory](https://github.com/etychon/cisco-gps-netconf/security/advisories/new) on this repository, or contact the maintainer through GitHub.

## Security Notes for Operators

- **Credentials**: The CLI accepts passwords via `-p`. Prefer a dedicated NETCONF service account with least privilege. Passwords may appear in shell history and process listings; consider wrapping calls in your own secret-management layer.
- **Host key verification**: NETCONF connections use `hostkey_verify=False` by default (common for lab automation). For production, pin known host keys or use certificate-based trust where your environment supports it.
- **Output files**: JSON exports may contain precise device location data. Treat output files as sensitive operational data.
