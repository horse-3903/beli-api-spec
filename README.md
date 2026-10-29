<div align="center">

# Beli API: Unofficial OpenAPI Spec

Unofficial Beli API documentation as an OpenAPI 3.1 spec: 433 operations for the Beli restaurant ranking app backend, ready for Swagger UI, Postman or SDK generation.

[![OpenAPI](https://img.shields.io/badge/OpenAPI-3.1-6BA539?style=flat-square&logo=openapiinitiative&logoColor=white)](beli-openapi.yaml)
[![Python](https://img.shields.io/badge/Python_3.10-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/github/license/horse-3903/beli-api-spec?style=flat-square)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/horse-3903/beli-api-spec?style=flat-square)](../../commits)

</div>

---

## Overview

**Beli API** is a reverse-engineered, unofficial OpenAPI description of the backend used by the Beli app (`com.beliapp.myapp` 10.2.0), covering login, search, bookmarks, restaurant ratings, guides, lists, social, referrals and more. It combines the HAR-based [beli-api](https://github.com/ProjectBarks/beli-api) spec with endpoints read from the decompiled app and live checks on a real account. Use it to generate a Beli API client or SDK in any language with `openapi-generator`.

---

## Features

- **433 operations** - 140 from observed traffic plus endpoints read from the app's JavaScript bundle
- **139 live-verified GETs** - response schemas inferred from real responses, marked `x-verified: true`
- **Guide endpoints** - list, read, create and edit Beli guides, including the feature-flag query parameters the server requires
- **Referral endpoints** - referral link, invites remaining and the missing-referral claim
- **Honest about gaps** - `x-source: app-code` marks operations never executed, and `x-live-status` marks GETs that failed

---

## Tech Stack

![OpenAPI](https://img.shields.io/badge/OpenAPI-6BA539?style=for-the-badge&logo=openapiinitiative&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![YAML](https://img.shields.io/badge/YAML-CB171E?style=for-the-badge&logo=yaml&logoColor=white)

---

## Getting Started

### Prerequisites

- Python 3.10+
- `pip install pyyaml openapi-spec-validator`

### Use the spec

Open `beli-openapi.yaml` (or `beli-openapi.json`) in Swagger UI, Postman or Insomnia, or generate a client:

```bash
npx @openapitools/openapi-generator-cli generate -i beli-openapi.yaml -g python -o beli-client
```

### Regenerate

```bash
python tools/build_openapi.py
python tools/merge_shapes.py
openapi-spec-validator beli-openapi.yaml
```

---

## Project Structure

```
beli-api-spec/
├── beli-openapi.yaml        # OpenAPI 3.1 spec
├── beli-openapi.json        # same spec as JSON
├── NOTES.md                 # auth, feature flags, verified versus inferred
├── AGENTS.md                # instructions for AI coding agents
└── tools/
    ├── extract_app_api.py   # pulls API methods from the decompiled JS bundle
    ├── build_openapi.py     # merges app endpoints into the base spec
    ├── merge_shapes.py      # adds live response schemas, writes YAML and JSON
    └── data/                # base spec, extracted methods, flags, inferred shapes
```

---

## Authentication

| Item | Value |
|---|---|
| Login | `POST /api/token/` with email and password returns access and refresh JWTs |
| Header | `Authorization: Bearer <access token>` |
| Required header | `Origin` (requests without it get HTTP 403) |
| Rate limit | Bursts return HTTP 429; space calls 3 to 6 seconds apart |

See [NOTES.md](NOTES.md) for the rest. Unofficial and not affiliated with Beli. Use only your own account.

---

## Disclaimer

**Use at your own risk.** Calling these APIs outside the official app may violate the service's terms and can lead to rate limiting, a suspended or banned account, or loss of data. The authors accept no responsibility for any consequences to your account. Use only your own account, and never share your credentials or tokens.

---

## Related

- [tabelog-api-spec](https://github.com/horse-3903/tabelog-api-spec): the sibling unofficial API spec
- [openapi-catalog](https://github.com/horse-3903/openapi-catalog): index of all unofficial API specs
