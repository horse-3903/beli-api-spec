import copy
import json
import re
from collections import Counter
from pathlib import Path

import yaml

root = Path(__file__).parent
out_dir = root.parent
spec = yaml.safe_load(open(root / "data/beli.bundled.yaml", encoding="utf8"))
rows = json.load(open(root / "data/app_api_methods.json", encoding="utf8"))
flags = json.load(open(root / "data/app_flags.json", encoding="utf8"))
verified = json.load(open(root / "data/beli_verified.json", encoding="utf8"))

API_HOST = "https://backoffice-service-t57o3dxfca-nn.a.run.app"
ONBOARD_HOST = "https://backoffice-service-onboarding-t57o3dxfca-nn.a.run.app"
RECS_HOST = "https://backoffice-service-recs-t57o3dxfca-nn.a.run.app"

TAGS = [
    ("auth", ("token", "login", "log-out", "password", "attest", "check-email", "check-username", "logged-in", "sign", "otp", "verify", "birthday", "phone")),
    ("lists", ("guide", "playlist", "published-list", "short-list", "featured-list", "hscroll", "list", "challenge", "occasion", "custom-field", "tag")),
    ("reservations", ("reservation", "res-", "business-res", "claim-res", "no-show", "venue")),
    ("ranking", ("rank", "bookmark", "comparison", "skipped", "been", "want-to-try")),
    ("business", ("business", "dish", "menu", "company", "address", "cuisine", "hours", "price", "photo", "street")),
    ("search", ("search", "cities", "city", "autocomplete", "filter-options")),
    ("feed", ("feed", "activity", "home", "banner", "slide", "post", "comment", "like")),
    ("social", ("friend", "follow", "contact", "invite", "block", "user-search", "user/search", "mutual", "suggest", "referral", "school", "college")),
    ("notifications", ("notification", "push", "device", "badge", "popup")),
    ("payments", ("payment", "subscription", "creator", "paid", "stripe", "purchase", "reward", "coupon")),
    ("profile", ("profile", "user", "settings", "account", "photo", "avatar", "cookie")),
    ("telemetry", ("error", "log", "analytics", "telemetry", "event", "issue", "api-hosts", "config")),
]


def tag_for(path, name):
    s = (path + " " + name).lower()
    for tag, keys in TAGS:
        if any(k in s for k in keys):
            return tag
    return "misc"


def norm(path):
    return re.sub(r"\{[^}]+\}", "{}", path).rstrip("/")


def humanize(name):
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)
    return s[0].upper() + s[1:].lower() if s else s


def balanced(s, i):
    depth = 0
    q = None
    while i < len(s):
        c = s[i]
        if q:
            if c == "\\":
                i += 2
                continue
            if c == q:
                q = None
        elif c in "\"'`":
            q = c
        elif c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return len(s) - 1


def split_args(s):
    out, depth, q, cur, i = [], 0, None, "", 0
    while i < len(s):
        c = s[i]
        if q:
            cur += c
            if c == "\\":
                cur += s[i + 1]
                i += 2
                continue
            if c == q:
                q = None
        elif c in "\"'`":
            q = c
            cur += c
        elif c in "([{":
            depth += 1
            cur += c
        elif c in ")]}":
            depth -= 1
            cur += c
        elif c == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += c
        i += 1
    if cur:
        out.append(cur)
    return out


def object_keys(expr):
    expr = expr.strip()
    if not expr.startswith("{"):
        return None
    inner = expr[1:-1]
    keys = []
    for part in split_args(inner):
        part = part.strip()
        if part.startswith("..."):
            keys.append("...")
            continue
        m = re.match(r"([A-Za-z_$][\w$]*|\"[^\"]+\")\s*(:|$)", part)
        if m:
            keys.append(m.group(1).strip('"'))
    return keys


def expand_template(tpl):
    m = re.search(r"\$\{([^{}]*)\?(\"[^\"]*\"|'[^']*'):(\"[^\"]*\"|'[^']*')\}", tpl)
    if not m:
        return [tpl]
    a = tpl[: m.start()] + m.group(2).strip("\"'") + tpl[m.end():]
    b = tpl[: m.start()] + m.group(3).strip("\"'") + tpl[m.end():]
    return expand_template(a) + expand_template(b)


def resolve_flags(s):
    return re.sub(r"\$\{this\.(\w+)\}", lambda m: flags.get(m.group(1), m.group(0)), s)


def mask_exprs(tpl):
    out, i = "", 0
    while i < len(tpl):
        if tpl.startswith("${", i):
            j = balanced(tpl, i + 1)
            out += "\x00"
            i = j + 1
        else:
            out += tpl[i]
            i += 1
    return out


def find_paths(src):
    found = []
    for m in re.finditer(r"this\.apiURL\s*\+\s*(\"[^\"]*\"|'[^']*')", src):
        found.append(m.group(1)[1:-1])
    for m in re.finditer(r"this\.apiURL\s*\+\s*`", src):
        end = src.find("`", m.end())
        found.append(src[m.end(): end])
    for m in re.finditer(r"`\$\{this\.apiURL\}", src):
        end = src.find("`", m.end())
        found.append(src[m.end(): end])
    for m in re.finditer(r"(?<![\w.])(\w)=this\.apiURL\+", src):
        pass
    return found


ops = []
unparsed = []
for r in rows:
    name, args, src = r["name"], r["args"], r["src"]
    vm = re.search(r"this\.(?:http\.)?(get|post|put|delete|patch)\(", src)
    if not vm:
        unparsed.append(name)
        continue
    verb = vm.group(1)
    paths = find_paths(src)
    if not paths:
        unparsed.append(name)
        continue
    call_end = balanced(src, vm.end() - 1)
    call_args = split_args(src[vm.end(): call_end])
    body = call_args[1].strip() if len(call_args) > 1 and verb in ("post", "put", "patch") else None
    body_keys = object_keys(body) if body else None
    extra_q = []
    for qm in re.finditer(r"[?&]([A-Za-z_][\w]*)=", resolve_flags(" ".join(re.findall(r"(?:\"[^\"]*\"|'[^']*'|`[^`]*`)", src)))):
        if qm.group(1) not in extra_q:
            extra_q.append(qm.group(1))
    seen_paths = set()
    for raw in paths:
        for tpl in expand_template(raw):
            tpl = resolve_flags(tpl)
            tpl = mask_exprs(tpl)
            pth, _, qs = tpl.partition("?")
            n = [0]

            def sub(m):
                n[0] += 1
                return "{p%d}" % n[0]

            pth2 = re.sub("\x00", sub, pth)
            pth2 = re.sub(r"\{(\d+)\}", lambda m: "{arg" + m.group(1) + "}", pth2)
            pth2 = "/api" + pth2 if pth2.startswith("/") else pth2
            if not pth2.startswith("/api/") or pth2 in seen_paths:
                continue
            seen_paths.add(pth2)
            primary = re.findall(r"(?:^|&)([A-Za-z_]\w*)=", qs)
            ops.append(dict(name=name, args=args, verb=verb, path=pth2, primary=primary, extra=extra_q, body=body, body_keys=body_keys))

by_norm = {}
for path, item in spec["paths"].items():
    by_norm[norm(path)] = path

stats = Counter()
added = 0
used_ids = {op.get('operationId') for it in spec['paths'].values() for m, op in it.items() if isinstance(op, dict) and m in ('get','post','put','delete','patch')}


def uid_for(name):
    cand, k = name, 2
    while cand in used_ids:
        cand = f'{name}{k}'
        k += 1
    used_ids.add(cand)
    return cand

for o in ops:
    key = norm(o["path"])
    qparams = []
    for q in o["extra"]:
        qparams.append((q, q in o["primary"]))
    if key in by_norm:
        item = spec["paths"][by_norm[key]]
        op = item.get(o["verb"])
        if op is None:
            op = {"summary": humanize(o["name"]), "operationId": uid_for(o["name"]), "tags": [tag_for(o["path"], o["name"])], "x-source": "app-code", "responses": {"200": {"description": "ok"}}}
            item[o["verb"]] = op
            stats["new verb on existing path"] += 1
        else:
            stats["merged into existing"] += 1
        have = {p.get("name") for p in (op.get("parameters") or []) if isinstance(p, dict)}
        for q, req in qparams:
            if q not in have:
                op.setdefault("parameters", []).append({"name": q, "in": "query", "required": bool(req), "schema": {"type": "string"}, "description": "Sent by the app (read from the Beli 10.2.0 client)."})
        op["x-app-method"] = o["name"]
        if o["body_keys"] and "requestBody" not in op and o["verb"] in ("post", "put", "patch"):
            op["requestBody"] = {"content": {"application/json": {"schema": {"type": "object", "properties": {k: {} for k in o["body_keys"] if k != "..."}, "description": "Fields the app sends (types unknown)."}}}}
        continue
    tag = tag_for(o["path"], o["name"])
    item = spec["paths"].setdefault(o["path"], {})
    path_params = re.findall(r"\{((?:p|arg)\d+)\}", o["path"])
    op = {
        "operationId": uid_for(o["name"]),
        "tags": [tag],
        "summary": humanize(o["name"]),
        "x-source": "app-code",
        "x-verified": False,
        "parameters": [{"name": p, "in": "path", "required": True, "schema": {"type": "string"}, "description": "Positional argument %d of the app method %s." % (i + 1, o["name"])} for i, p in enumerate(path_params)],
        "responses": {"200": {"description": "ok (response shape not documented)"}, "401": {"description": "unauthorized"}},
    }
    for q, req in qparams:
        op["parameters"].append({"name": q, "in": "query", "required": bool(req) and q not in flags.values(), "schema": {"type": "string" if q not in flags.values() else "boolean"}, "description": "Feature flag the app sends (value true)." if q in flags.values() else "Query parameter the app sends."})
    if not op["parameters"]:
        del op["parameters"]
    if o["verb"] in ("post", "put", "patch"):
        props = {k: {} for k in (o["body_keys"] or []) if k != "..."}
        sch = {"type": "object"}
        if props:
            sch["properties"] = props
        if o["body_keys"] is None and o["body"]:
            sch["description"] = "Body is passed through from the caller (`%s`); shape not extracted." % o["body"][:60].replace("`", "'")
        op["requestBody"] = {"required": False, "content": {"application/json": {"schema": sch}}}
    if re.search(r"admin|comp-time", o["path"]):
        op["x-internal"] = True
        op["description"] = "Internal/admin endpoint seen in the client code. Not for normal accounts; not exercised."
    item[o["verb"]] = op
    added += 1
    stats["new endpoint"] += 1

tags_used = sorted({op.get("tags", ["misc"])[0] for item in spec["paths"].values() for m, op in item.items() if isinstance(op, dict) and m in ("get", "post", "put", "delete", "patch")})
base_tags = {t["name"]: t for t in spec.get("tags", [])}
spec["tags"] = [base_tags.get(t, {"name": t}) for t in tags_used]

spec["info"]["title"] = "Beli API (Unofficial)"
spec["info"]["version"] = "0.2.0"
spec["info"]["description"] = (
    "Unofficial, community-maintained, reverse-engineered documentation of the Beli app backend. "
    "Not affiliated with or endorsed by Beli; it can change at any time. Use only your own account.\n\n"
    "Sources: the repository's HAR-based spec, the Beli 10.2.0 web client code, and live checks against one account. "
    "Operations tagged `x-source: app-code` were read from the client and have not been exercised; "
    "`x-verified: true` marks live-tested behaviour.\n\n"
    "Most guide calls need feature-flag query parameters, e.g. `supports_no_guide_category=true`, "
    "`supports_no_guide_city=true`, `supports_collab_guides=true`; without them the server can return an empty list.\n"
    "Requests need an `Origin` header; bursts return HTTP 429."
)
spec["servers"] = [{"url": API_HOST, "description": "Main API"}, {"url": ONBOARD_HOST, "description": "Onboarding/auth host (login for new sessions)"}, {"url": RECS_HOST, "description": "Recommendations service"}]
spec["x-feature-flags"] = flags
spec["x-live-verified"] = verified["verified"]
out = out_dir / "beli-openapi.yaml"
with open(out, "w", encoding="utf8") as f:
    yaml.safe_dump(spec, f, sort_keys=False, allow_unicode=True, width=120)
print("methods unparsed:", len(unparsed), unparsed[:15])
print(dict(stats), "| total paths now:", len(spec["paths"]))
print(out)
