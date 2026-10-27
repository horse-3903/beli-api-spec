import json
from pathlib import Path
import yaml

root = Path(__file__).parent
out_dir = root.parent
spec = yaml.safe_load(open(out_dir / "beli-openapi.yaml", encoding="utf8"))
shapes = json.load(open(root / "data/get_shapes.json", encoding="utf8"))
shapes.update(json.load(open(root / "data/get_shapes_fix.json", encoding="utf8")))
for extra in ("get_shapes_chain.json", "get_shapes_chain2.json", "get_shapes_chain3.json"):
    for p, e in json.load(open(root / "data" / extra, encoding="utf8")).items():
        if e.get("status") == 200 or p not in shapes or shapes[p].get("status") != 200:
            shapes[p] = e
ACT_HOST = "https://backoffice-service-t57o3dxfca-nn.a.run.app"
TAG_OVERRIDES = {
    "/api/rec-score/": "ranking", "/api/monthly-recap/{p1}/": "feed", "/api/dining-calendar-month/{p1}/": "feed",
    "/api/validate-url/": "business", "/api/judy-welcome-page/": "feed", "/api/admin-map-social-url/": "business",
    "/api/rec-ask/{p1}/": "lists", "/api/check-share-visit-added/": "feed", "/api/table-rating-share-data/": "feed",
    "/api/version/": "telemetry", "/api/delivery/check-availability/": "business", "/api/delivery/place-details/": "business",
    "/api/restrictions/": "profile", "/api/dietary-restriction-options/": "profile", "/api/faq/": "telemetry",
    "/api/leaderboard/{p1}/{p2}/{p3}/": "social", "/api/leaderboard/{p1}/": "social", "/api/nominations/": "social",
    "/api/onboarding-order/{p1}/": "auth", "/api/validate-google-maps-url/": "business", "/api/google-authorization-url/": "auth",
    "/api/onboarding-selections-progress/": "auth", "/api/feature-credits-available/": "payments", "/api/unlock-feature-choice/": "payments",
}
for p, t in TAG_OVERRIDES.items():
    for m, op in spec["paths"].get(p, {}).items():
        if m in ("get", "post", "put", "delete", "patch"):
            op["tags"] = [t]

SUPP = {
    ("get", "/api/attest/challenge/"): dict(tags=["auth"], summary="Get a device attestation challenge for login", operationId="getAttestChallengeForLogin",
        parameters=[{"name": "device_id", "in": "query", "required": True, "schema": {"type": "string"}}],
        description="The app asks for a challenge before login and may attach an attestation to POST /api/token/. Email/password login worked without it on a plain client."),
    ("post", "/api/user/reset-password/send-mail/"): dict(tags=["auth"], summary="Send a password reset email", operationId="sendResetPasswordEmail",
        body={"email": {"type": "string"}, "phone": {"type": "string"}}, description="Not called. Triggers an email to the account."),
    ("post", "/api/business-photo/"): dict(tags=["business"], summary="Upload a business photo (multipart)", operationId="uploadBusinessPhoto",
        description="Bearer token header, multipart body built by the app. Not called."),
    ("post", "/activity/"): dict(tags=["telemetry"], summary="Client activity/telemetry event", operationId="logActivity",
        body={"user": {"type": "string"}, "device": {"type": "string"}, "field_name": {"type": "string"}, "person": {}, "business": {}, "info": {}, "json_info": {"type": "object"}, "playlist": {}, "version": {"type": "string"}, "page": {"type": "string"}},
        description="Posted to the activity host by the app on screen views and taps. Not called."),
}
for (verb, path), s in SUPP.items():
    op = {"operationId": s["operationId"], "tags": s["tags"], "summary": s["summary"], "x-source": "app-code", "x-verified": False, "description": s.get("description", ""),
          "responses": {"200": {"description": "ok"}, "401": {"description": "unauthorized"}}}
    if s.get("parameters"):
        op["parameters"] = s["parameters"]
    if s.get("body"):
        op["requestBody"] = {"content": {"application/json": {"schema": {"type": "object", "properties": s["body"]}}}}
    spec["paths"].setdefault(path, {})[verb] = op

ok = bad = 0
for path, ent in shapes.items():
    op = spec["paths"].get(path, {}).get("get")
    if not op:
        continue
    st = ent.get("status")
    have = {p.get("name") for p in op.get("parameters", [])}
    if st == 200 and ent.get("schema"):
        op["responses"]["200"] = {"description": "ok (shape observed live)", "content": {"application/json": {"schema": ent["schema"]}}}
        op["x-verified"] = True
        op.pop("x-live-status", None)
        for n in ent.get("params", []):
            if n not in have:
                op.setdefault("parameters", []).append({"name": n, "in": "query", "required": True, "schema": {"type": "string"}, "description": "Needed for a 200 in live tests."})
        ok += 1
    else:
        op["x-live-status"] = {"status": st, "note": ent.get("note", "")}
        bad += 1

# the rec-score GET needs the user/business/category trio; playlist-list-view is for non-guide playlists only
pl = spec["paths"].get("/api/playlist-list-view/", {}).get("get")
if pl:
    pl["description"] = "For ordinary playlists. For a user guide id use /api/user-guide-list-view/; this returns HTTP 500 for guide ids."
NOTES = {
    "/api/business-contact-data/": "`field` must be a valid contact field; `website` works. `phone`, `email`, `instagram`, `PHONE_NO`, `address` are rejected.",
    "/api/business-address-data/": "`field` is validated server-side; address, street, city variants tried were all rejected (Invalid field). Valid values not found.",
    "/api/business/": "GET with `id=<business id>` returned 405 in live tests; the app reads one business via POST /api/business/ or via search-app and business-friend-text.",
    "/api/user/bio/": "Identifier param is `id` (not `user_id`). Returns an empty body for a user with no bio.",
    "/api/user/member/": "Identifier param is `id`.",
    "/api/follow/": "Filters: `follower=<uuid>` and/or `followed=<uuid>`.",
    "/api/creator-subscription-config/": "Server error unless the account is a creator with Stripe plans (`creator=<uuid>`).",
    "/api/delivery/place-details/": "Needs a `place_id` from /api/delivery/places-autocomplete/ plus the same `session_token`; autocomplete returned no predictions for `input=ramen tokyo`, so this was not exercised.",
    "/api/school/": "Needs `school_email`; not tried (would look up a real school email).",
    "/api/company/": "Needs `company_email`; not tried.",
    "/api/user-field-photo/": "Needs `field_name`, whose valid values are unknown.",
}
for p, n in NOTES.items():
    for m, op in spec["paths"].get(p, {}).items():
        if m == "get":
            op["description"] = (op.get("description", "") + " " + n).strip()
with open(out_dir / "beli-openapi.yaml", "w", encoding="utf8") as f:
    yaml.safe_dump(spec, f, sort_keys=False, allow_unicode=True, width=120)
with open(out_dir / "beli-openapi.json", "w", encoding="utf8") as f:
    json.dump(spec, f, ensure_ascii=False, indent=2)
print("shapes merged:", ok, "| still non-200:", bad)
