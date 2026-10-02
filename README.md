# Fireworks Signal Router

Scores raw GTM signals per account and routes each account to the right seller. The output is a seller dashboard with two ranked lists, Customers and Prospects. Each card shows a "+X points" breakdown of its score, a research brief, a draft email, a Salesforce link, and a Slack alert preview.

- [DESIGN.md](DESIGN.md): routing logic, scoring approach, failure modes, what's next
- [DIAGRAMS.md](DIAGRAMS.md): flow diagrams plus every formula and ranking table

## Run it

Python 3.9+ with the standard library only. No installs.

```bash
python3 -m router serve        # build, then open http://localhost:8000
python3 -m router build        # just write out/queue.json, out/queue.csv, out/index.html
python3 -m unittest -v         # tests: Caliber worked example, routing exceptions, breakdowns add up
```

`out/index.html` is self-contained, so you can also open it directly in a browser. Use `--port 8765` if port 8000 is taken.

## Inputs

`data/accounts.csv`, `data/sellers.csv`, and `data/signals.csv` were converted from the provided spreadsheets:

```bash
python3 scripts/xlsx_to_csv.py "Copy of accounts.xlsx" data/accounts.csv
```

Point the router at other files with `--data DIR`.

## Outputs

| File | For |
|---|---|
| `out/index.html` | Seller dashboard: Customers / Prospects tabs, segment filter, "Viewing as" rep picker, Slack preview |
| `out/queue.json` | Every card with score, breakdown lines, owner, routing reason, flags, brief, email |
| `out/queue.csv` | The same queue flattened, for a spreadsheet or CRM import |

## Code map

| File | Does |
|---|---|
| `router/weights.py` | Every weight and point table, in one place |
| `router/data.py` | Loads the CSVs |
| `router/scoring.py` | Per-signal formulas, account stack, fit, recency, and the "+X points" lines |
| `router/routing.py` | Matching, one card per account, territory and tier routing, OOO cover, ramp share |
| `router/content.py` | Brief, play, draft email, Salesforce link, Slack text |
| `router/render.py` | The dashboard |
