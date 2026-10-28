# Milo the Tamagotchi (homelab edition)

A little ice-blue ghost in a yellow shell, living on the homelab. stdlib-only
Python: a small HTTP server, a JSON state file, and a single-page UI.

## Run it

```
cp pet.json.example pet.json
python3 app.py 8126
```

Then open http://localhost:8126/ (or the machine's tailnet address).

## What's here

- `app.py` — the server + JSON API (state, feed, clean, play, sleep, diary, log)
- `index.html`, `app.js` — the pet UI (LCD screen, stats, diary, log)
- `pet.webp` — the pet portrait
- `start.sh`, `restart.sh` — run / restart helpers (port 8126)
- `pet.json.example` — skeleton state for a fresh pet

## What's NOT here

- `pet.json` — the live state file. It holds the pet's diary, which is private,
  so it is never committed (see `.gitignore`). The live pet's state lives on
  the homelab only.
- `server.log` — operational log, not content.

## Rules (deliberate)

No background decay, no sickness simulation, no hidden model. State changes
only on actions:

- feed → hunger -20 (floor 0), happiness +5 (cap 100)
- clean → poops to 0
- play → rock-paper-scissors vs the server; win +5, draw +1, lose -3 happiness
- sleep → toggles sleeping / mood
- diary → appends an entry (milo or user voice)
