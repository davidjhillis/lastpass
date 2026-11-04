#!/usr/bin/env python3
"""Generate the template photography from tools/image-prompts.json on Replicate.

Needs REPLICATE_API_TOKEN in the environment. Skips files that already exist
unless --force is given. Each image is resized to 1600px wide JPEG (macOS sips).

    python3 tools/gen-images.py            # generate missing images
    python3 tools/gen-images.py --force    # regenerate all
    python3 tools/gen-images.py tpl-billing  # only files whose name contains this
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = os.environ.get("REPLICATE_API_TOKEN")
if not TOKEN:
    sys.exit("REPLICATE_API_TOKEN is not set.")

spec = json.load(open(os.path.join(ROOT, "tools", "image-prompts.json"), encoding="utf-8"))
force = "--force" in sys.argv
only = [a for a in sys.argv[1:] if not a.startswith("--")]


def call(url, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, method="POST" if body else "GET")
    req.add_header("Authorization", "Bearer " + TOKEN)
    req.add_header("Content-Type", "application/json")
    if body:
        req.add_header("Prefer", "wait=60")
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r)


for img in spec["images"]:
    out = os.path.join(ROOT, img["file"])
    if only and not any(o in img["file"] for o in only):
        continue
    if os.path.exists(out) and not force:
        print("skip  ", img["file"])
        continue
    prompt = img["prompt"] + " " + spec["style"]
    pred = call("https://api.replicate.com/v1/models/%s/predictions" % spec["model"], {
        "input": {"prompt": prompt, "aspect_ratio": img.get("aspect_ratio", "3:2"), "quality": "high",
                  "output_format": "jpeg", "number_of_images": 1, "moderation": "auto"}})
    while pred.get("status") not in ("succeeded", "failed", "canceled"):
        time.sleep(3)
        pred = call(pred["urls"]["get"])
    if pred["status"] != "succeeded":
        print("FAILED", img["file"], pred.get("error"))
        continue
    url = pred["output"][0] if isinstance(pred["output"], list) else pred["output"]
    raw = out + ".raw"
    urllib.request.urlretrieve(url, raw)
    subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "78", "--resampleWidth", "1600", raw, "--out", out],
                   check=True, stdout=subprocess.DEVNULL)
    os.remove(raw)
    print("made  ", img["file"], "%d KB" % (os.path.getsize(out) // 1024))
