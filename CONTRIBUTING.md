# Contributing

Thanks for helping improve these unofficial API specs.

## Ways to help

- Report a wrong or missing endpoint, parameter or response field
- Confirm an endpoint against a live account and say what you saw

## Ground rules

- Never include tokens, passwords, account ids, `.env` files, APKs or decompiler zips
- Do not mark a field required or nullable unless you verified it, and say whether a change is verified or inferred
- Specs are generated: change the scripts in `tools/` and regenerate both the YAML and JSON, never edit one by hand
- Validate with `openapi-spec-validator <service>/<service>-openapi.yaml`
- No em dashes in text, and keep commit messages to one short line

## Pull requests

Describe what changed, how you checked it, and which operations it touches. Use your own account only when testing, and remember all use is at your own risk.
