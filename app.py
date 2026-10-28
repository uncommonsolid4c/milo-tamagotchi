#!/usr/bin/env python3
"""Milo the Tamagotchi, homelab edition. stdlib-only Python.

Serves the pet UI and a small JSON API. State lives in pet.json next to this
file, rewritten atomically on every mutation.

Deliberate difference from the web artifact it replaces: NO background decay,
no sickness simulation, no hidden model. State changes only on actions, and
the rules are the ones below, in plain sight:
  feed  -> hunger -20 (floor 0), happiness +5 (cap 100)
  clean -> poops to 0
  play  -> rock-paper-scissors vs the server; win +5, draw +1, lose -3 happiness
  sleep -> toggles sleeping / mood
  diary -> appends an entry (milo or user voice)
The pet was seeded from the artifact's live state on 2026-10-27, diary and all.
"""
import json
import os
import random
import sys
import threading
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, "pet.json")
LOCK = threading.Lock()
FOODS = ["cold brew", "home bento", "cookie", "midnight ramen", "taco truck", "debug donut"]
CHOICES = ["rock", "paper", "scissors"]
BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}


def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load():
    with open(STATE_FILE) as f:
        return json.load(f)


def save(data):
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, STATE_FILE)


def day_label(pet):
    born = datetime.fromisoformat(pet["bornAt"].replace("Z", "+00:00"))
    days = (datetime.now(timezone.utc) - born).days + 1
    return "DAY %d" % max(days, 1)


def append_log(data, kind, label):
    entries = data["log"]
    nid = (entries[-1]["id"] + 1) if entries else 1
    entries.append({"id": nid, "kind": kind, "label": label, "createdAt": now_iso()})
    data["log"] = entries[-100:]


def pet_view(data):
    pet = dict(data["pet"])
    pet["dayLabel"] = day_label(pet)
    return pet


def touch(data):
    data["pet"]["updatedAt"] = now_iso()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=HERE, **kw)

    def log_message(self, *a):
        pass

    def send_json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = 0
        raw = self.rfile.read(n) if n > 0 else b"{}"
        try:
            return json.loads(raw or b"{}")
        except ValueError:
            return None

    def do_GET(self):
        p = urlparse(self.path).path
        if p == "/api/state":
            with LOCK:
                data = load()
            self.send_json({"pet": pet_view(data), "recentLog": data["log"][-10:][::-1]})
        elif p == "/api/diary":
            with LOCK:
                data = load()
            self.send_json({"entries": data["diary"][::-1]})
        elif p == "/api/log":
            with LOCK:
                data = load()
            self.send_json({"log": data["log"][::-1]})
        elif p.startswith("/api/"):
            self.send_json({"error": "unknown endpoint"}, status=404)
        else:
            super().do_GET()

    def do_POST(self):
        p = urlparse(self.path).path
        body = self.read_json()
        if body is None:
            self.send_json({"error": "bad json"}, status=400)
            return
        with LOCK:
            data = load()
            pet = data["pet"]
            if p == "/api/feed":
                food = body.get("food")
                if food not in FOODS:
                    self.send_json({"error": "unknown food"}, status=400)
                    return
                pet["hunger"] = max(0, pet["hunger"] - 20)
                pet["happiness"] = min(100, pet["happiness"] + 5)
                append_log(data, "feed", "Fed " + food)
                touch(data)
                save(data)
                self.send_json({"pet": pet_view(data), "message": "Fed " + food})
            elif p == "/api/clean":
                n = pet["poops"]
                pet["poops"] = 0
                if n > 0:
                    append_log(data, "clean", "Cleaned %d poop%s" % (n, "" if n == 1 else "s"))
                touch(data)
                save(data)
                self.send_json({"pet": pet_view(data),
                                "message": ("Cleaned %d poop%s" % (n, "" if n == 1 else "s"))
                                if n > 0 else "Already clean"})
            elif p == "/api/play":
                choice = body.get("choice")
                if choice not in CHOICES:
                    self.send_json({"error": "choose rock, paper, or scissors"}, status=400)
                    return
                server = random.choice(CHOICES)
                if choice == server:
                    outcome, delta = "draw", 1
                elif BEATS[choice] == server:
                    outcome, delta = "win", 5
                else:
                    outcome, delta = "lose", -3
                pet["happiness"] = min(100, max(0, pet["happiness"] + delta))
                append_log(data, "play", "Rock-paper-scissors: " + outcome)
                touch(data)
                save(data)
                self.send_json({"pet": pet_view(data), "you": choice,
                                "server": server, "outcome": outcome})
            elif p == "/api/sleep":
                pet["sleeping"] = not pet["sleeping"]
                pet["mood"] = "sleeping" if pet["sleeping"] else "awake"
                append_log(data, "sleep" if pet["sleeping"] else "wake",
                           "Went to sleep" if pet["sleeping"] else "Woke up")
                touch(data)
                save(data)
                self.send_json({"pet": pet_view(data)})
            elif p == "/api/diary":
                author = body.get("author")
                text = (body.get("body") or "").strip()
                if author not in ("milo", "user") or not text or len(text) > 2000:
                    self.send_json({"error": "author must be milo or user, body 1-2000 chars"},
                                   status=400)
                    return
                entries = data["diary"]
                nid = (entries[-1]["id"] + 1) if entries else 1
                entry = {"id": nid, "author": author, "body": text, "createdAt": now_iso()}
                entries.append(entry)
                touch(data)
                save(data)
                self.send_json({"entry": entry})
            else:
                self.send_json({"error": "unknown endpoint"}, status=404)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8126
    with LOCK:
        data = load()
        if not any(e.get("kind") == "move" for e in data["log"]):
            append_log(data, "move", "Milo moved to the homelab")
            touch(data)
            save(data)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
