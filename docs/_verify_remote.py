# -*- coding: utf-8 -*-
"""
Verify that the remote tree matches the local working copy, blob for blob.

For every tracked file we compute the git blob hash locally and compare it with
the sha recorded in the remote tree. A mismatch means the push did not carry the
current content.
"""
import os, io, sys, json, hashlib, subprocess
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = r"E:\论文5\repo\s2ds-eval-audit"
GIT = r"C:\Users\陈正洋\.workbuddy\binaries\PortableGit\versions\1.2.0\cmd\git.exe"
TOKEN = os.environ.get("GH_TOKEN", "")
OWNER, NAME = "czy326", "s2ds-eval-audit"


def blob_sha(raw):
    h = hashlib.sha1()
    h.update(b"blob %d\x00" % len(raw))
    h.update(raw)
    return h.hexdigest()


ls = subprocess.run([GIT, "-c", "core.quotepath=false", "ls-files"],
                    cwd=REPO, capture_output=True, text=True,
                    encoding="utf-8").stdout
tracked = [f for f in ls.split("\n") if f.strip()]
tracked = [f[1:-1] if f.startswith('"') and f.endswith('"') else f for f in tracked]

local = {}
for rel in tracked:
    p = os.path.join(REPO, *rel.split("/"))
    local[rel] = blob_sha(open(p, "rb").read())

H = {"Authorization": "Bearer " + TOKEN, "User-Agent": "verify",
     "Accept": "application/vnd.github+json"}
u = f"https://api.github.com/repos/{OWNER}/{NAME}/git/trees/main?recursive=1"
tree = json.loads(urllib.request.urlopen(
    urllib.request.Request(u, headers=H), timeout=60).read())
remote = {x["path"]: x["sha"] for x in tree["tree"] if x["type"] == "blob"}

only_local = sorted(set(local) - set(remote))
only_remote = sorted(set(remote) - set(local))
diff = sorted(k for k in set(local) & set(remote) if local[k] != remote[k])

print(f"local files      : {len(local)}")
print(f"remote files     : {len(remote)}")
print(f"missing on remote: {len(only_local)}")
for f in only_local[:10]:
    print("   -", f)
print(f"extra on remote  : {len(only_remote)}")
for f in only_remote[:10]:
    print("   +", f)
print(f"content mismatches: {len(diff)}")
for f in diff[:10]:
    print("   !", f)
print("\nVERDICT:", "IDENTICAL" if not (only_local or only_remote or diff) else "DIFFERS")
