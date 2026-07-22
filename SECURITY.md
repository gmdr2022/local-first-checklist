# Security Policy

## Supported version

Security fixes are applied to the latest release.

## Report a vulnerability privately

Use **Security → Report a vulnerability** in this repository, or open the private report form at:

https://github.com/gmdr2022/local-first-checklist/security/advisories/new

Do not place exploit details, private checklist data, credentials, or personal information in a public issue.

Include the affected version, operating system, reproduction steps, impact, and any proposed mitigation. Acknowledgement does not imply that every report is a vulnerability, but reports will be evaluated against the documented local data and file-system boundaries.

## Security boundaries

- The application reads and writes only the explicitly selected checklist file and its `.bak` sibling.
- It does not provide encryption, access control, cloud synchronization, or secure deletion.
- Anyone who can read the data file can read checklist contents.
- Recovery verifies structure and consistency; it does not prove the origin of a backup.
