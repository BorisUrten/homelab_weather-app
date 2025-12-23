# Security Policy

## Supported Versions

Only the latest version of the Weather Monitoring System is currently supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a vulnerability, please do **NOT** open an issue.

Instead, please report it responsibly:

1. Email the details to `security@example.com` (Replace with your actual email in a real scenario)
2. Include steps to reproduce the issue
3. Allow us 90 days to release a patch before public disclosure

We will acknowledge your report within 48 hours.

## Security Features

This project implements several security best practices by default:

### Container Security
- **Non-root User**: The application container runs as a non-privileged user (UID 1000).
- **Minimal Base Image**: Uses `python:3.9-slim` to reduce attack surface.
- **No Privileged Mode**: Containers run without privileged access.

### Kubernetes Security
- **Secrets Management**: Sensitive data (API keys, passwords) are stored in Kubernetes Secrets.
- **Read-Only Filesystem**: The root filesystem can be mounted read-only (configured in deployment).
- **Resource Limits**: CPU and memory limits are enforced to prevent DoS.

### Application Security
- **Input Validation**: API responses are parsed and validated before use.
- **Dependencies**: Dependencies are pinned to specific versions in `requirements.txt`.
- **Environment Isolation**: Configuration is decoupled from code via environment variables.

## Best Practices for Deployment

When deploying this system to a production environment, we recommend:

1. **Network Policies**: Implement strict NetworkPolicies to isolate the database.
2. **Sealed Secrets**: Use Bitnami Sealed Secrets or an external secret store (Vault/AWS/GCP).
3. **TLS**: Enable TLS for the Ingress controller and database connections.
4. **Scanning**: regularly scan container images for vulnerabilities (e.g., with Trivy or Snyk).
