# Beli (com.beliapp.myapp 10.2.0) API notes

Sources: the MIT-licensed [beli-api](https://github.com/ProjectBarks/beli-api) HAR-based spec (140 operations), static analysis of the decompiled 10.2.0 web bundle (Capacitor/Angular, `main.*.js`), and live GET checks against one account.

The spec is OpenAPI 3.1.0 (Tabelog is 3.0.3). 433 operations, 23 schemas.

## Verified versus inferred

| Marker | Meaning |
|---|---|
| `x-verified: true` | GET answered HTTP 200 on a live account and the response shape was inferred from the real body (139 endpoints) |
| `x-source: app-code` | Read from the client code, never executed |
| `x-live-status` | Live status for GETs that did not return 200 (11 endpoints, see below) |
| `x-live-verified` (root) | Table of hand-checked findings |

Response schemas inferred from live bodies carry no `required` lists and no nullability guarantees. Write endpoints (about 140) are unverified, apart from `POST /api/add-bookmark/` and login.

## Client setup

| Item | Value |
|---|---|
| Main API host | `https://backoffice-service-t57o3dxfca-nn.a.run.app` |
| Onboarding/login host | `backoffice-service-onboarding-...` (the SDK's `connect()` handles it) |
| Recommendations host | `backoffice-service-recs-...` |
| Auth | `POST /api/token/` returns access and refresh JWTs, sent as `Authorization: Bearer` |
| Required header | `Origin` (without it the server answers 403) |
| Throttling | Bursts return 429; space calls about 3 to 6 seconds apart |
| Missing params | HTTP 400 with the plain body `Missing parameters` |
| Pagination | Django REST Framework: `{count, next, previous, results}`, sometimes `{results}` or a bare array |
| Empty bodies | Some writes return 200 with an empty body, which breaks strict JSON parsers |

## Feature flags

The app appends boolean query flags to guide calls, listed under `x-feature-flags`: `playlists_v2`, `vguides`, `supports_no_guide_category`, `supports_no_guide_city`, `supports_collab_guides`, `supports_ask_for_recs_guides` (plus `_1`, `_2`), `supports_auto_bookmark`. Without them `GET /api/user-guide/` returns an empty list.

## Guides

- `GET /api/user-guide/?user_id=` lists a user's guides (verified)
- `GET /api/user-guide-items/?user_id=` lists their items (verified)
- `GET /api/user-guide-list-view/?list_id=&viewer=` returns one guide in full (verified)
- `POST /api/user-guide/`, `PUT /api/update-user-guide/{id}/`, `PUT` and `POST /api/user-guide-items/`: create, edit, add and remove, from app code only
- `GET /api/published-list/` is Beli's own curated lists, not the user's guides

## Referrals

`GET /api/user/user-referral-link/`, `invites-remaining/{uuid}/`, `pending-invites/{uuid}/`, `claim-rewards-config/`, and `POST /api/missing-referral/` with `{username, referrer}`. Referral credit is decided server side; the claim endpoint only files a request.

## Unresolved GETs (non-200 on the live account)

Business GET (405), `user-business-photo`, `playlists`, school and company lookups (need emails), `user-field-photo`, `business-address-data`, `comments-page-quick-link` (needs a notification id), `delivery/place-details` (needs a place id), `playlist-list-view` for non-guide use, `creator-subscription-config` (needs a creator account). Each carries a note in its description.

## Skipped on purpose

The live probe skipped any GET whose name suggests a side effect (log, delete, mark, claim, send, reset, token, upload, and similar), so those response shapes come from code only.

## Inputs kept in `tools/data/`

| File | Origin |
|---|---|
| `beli.bundled.yaml` | Base spec from the beli-api repo (MIT) |
| `app_api_methods.json` | Output of `extract_app_api.py` over the decompiled bundle |
| `app_flags.json` | The 18 feature-flag names found in the bundle |
| `get_shapes*.json` | Response schemas inferred from live GET calls (types only, no account data) |
| `beli_verified.json` | Hand-checked findings and base notes |

The probe scripts that produced `get_shapes*.json` log in with real credentials and are not included.
