import json
import re
import sys
import zipfile
from pathlib import Path

ZIP = Path(sys.argv[1])
OUT = Path(sys.argv[2])
BASE = "resources/com.beliapp.myapp.apk/assets/public/"
MAIN = BASE + "main.023e08bee205e408.js"

z = zipfile.ZipFile(ZIP)
t = z.read(MAIN).decode("utf8", "ignore")


def skip_string(s, i):
    q = s[i]
    i += 1
    while i < len(s):
        c = s[i]
        if c == "\\":
            i += 2
            continue
        if q == "`" and c == "$" and s[i + 1: i + 2] == "{":
            i = match_brace(s, i + 1)
            continue
        if c == q:
            return i + 1
        i += 1
    return i


def match_brace(s, i):
    depth = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c in "\"'`":
            i = skip_string(s, i)
            continue
        if c == "/" and s[i + 1: i + 2] == "/":
            i = s.find("\n", i)
            if i < 0:
                return n
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return n


i = t.find("getUserGuides(t){")
cls_start = t.rfind("class ", 0, i)
j = t.find("{", cls_start)
cls_end = match_brace(t, j)
body = t[j + 1: cls_end - 1]
print("class body chars", len(body), file=sys.stderr)

methods = {}
pos = 0
head = re.compile(r"(?:async\s+)?([A-Za-z_$][\w$]*)\(([^)]*)\)\{")
while pos < len(body):
    m = head.match(body, pos)
    if m and m.group(1) not in ("if", "for", "while", "switch", "catch", "function"):
        end = match_brace(body, m.end() - 1)
        methods[m.group(1)] = (m.group(2), body[m.end(): end - 1])
        pos = end
    else:
        pos += 1
print("methods", len(methods), file=sys.stderr)

VERBS = ("get", "post", "put", "delete", "patch")
rows = []
for name, (args, src) in methods.items():
    verbs = re.findall(r"this\.(get|post|put|delete|patch)\(", src)
    if "apiURL" not in src and "Host" not in src and "priorityHost" not in src:
        continue
    rows.append({"name": name, "args": args, "src": src, "verbs": verbs})
json.dump(rows, open(OUT, "w", encoding="utf8"), ensure_ascii=False)
print("api-ish methods", len(rows), file=sys.stderr)
