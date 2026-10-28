# AGENTS.md: beli

OpenAPI 3.1 spec for the Beli app backend (`com.beliapp.myapp` 10.2.0), reverse engineered from the decompiled app plus live GET checks.

## Layout

- `beli-openapi.yaml` and `beli-openapi.json`: the spec, identical content. Generated, do not hand edit.
- `NOTES.md`: human notes on auth, feature flags and what is verified.
- `tools/extract_app_api.py`: parses the decompiled JS bundle into `tools/data/app_api_methods.json`. Usage: `python tools/extract_app_api.py <decompiled.zip> tools/data/app_api_methods.json`.
- `tools/build_openapi.py`: merges app-code endpoints into the base spec `tools/data/beli.bundled.yaml` (from the MIT-licensed beli-api repo).
- `tools/merge_shapes.py`: adds response schemas from `tools/data/get_shapes*.json`, applies tag overrides and notes, writes both YAML and JSON.

## Rebuild order

```bash
python beli/tools/build_openapi.py
python beli/tools/merge_shapes.py
openapi-spec-validator beli/beli-openapi.yaml
```

## Conventions

- `x-verified: true` means a GET returned 200 on a live account. `x-source: app-code` means read from the client and never run. Do not promote an operation to verified without a real call.
- Guide calls need the feature-flag query parameters listed under `x-feature-flags`.
- The API needs an `Origin` header and returns 429 on bursts.
- The probe scripts that built `get_shapes*.json` use real credentials and are intentionally not in this repo. Never add credentials or account ids to specs or data files.

## Rules

- Never commit tokens, `.env` files, saved login state, APKs or zips. The root `.gitignore` covers these.
- Specs come from code, not live traffic unless stated. Do not mark fields required or nullable unless verified, and say clearly what is verified versus inferred.
- After changing a spec, validate it with `openapi-spec-validator`. Keep YAML and JSON in sync by regenerating both from the scripts, never by editing one by hand.
- Do not use em dashes in any text. Keep commit messages to one short line, with no Co-Authored-By trailers. Only commit when asked.
