# Security Policy

## Supported versions

Only the latest release gets security fixes. If you can, check that the issue still happens on it before reporting.

## Reporting a vulnerability

Please do not open a public issue. Report it privately through [GitHub private vulnerability reporting](https://github.com/mhajder/pyekw/security/advisories/new).

Include the affected version, how to reproduce it and what an attacker could do with it.

I aim to acknowledge a report within 7 days and will keep you updated until it is fixed and released.

## Scope

In scope is this library, for example:

- input that makes a function hang or use excessive CPU or memory (for example a slow regular expression in `extract_kw_numbers`)
- input that is accepted as a valid KW number when it should be rejected
- a compromised release or dependency in the published package

Vulnerabilities in the eKW system itself belong with the Polish Ministry of Justice.
