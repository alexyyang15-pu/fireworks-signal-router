# Fireworks Signal Router

Scores raw GTM signals per account and routes each account to the right seller. The output is a seller dashboard with two ranked lists, Customers and Prospects. Each card shows a "+X points" breakdown of its score, a research brief, a draft email, a Salesforce link, and a Slack alert preview.

- [DESIGN.md](DESIGN.md): routing logic, scoring approach, failure modes, what's next
- [DIAGRAMS.md](DIAGRAMS.md): flow diagrams plus every formula and ranking table

## Run it

Python 3.9+ with the standard library only. No installs. From a clone of this repo:

```bash
git clone https://github.com/alexyyang15-pu/fireworks-signal-router.git
cd fireworks-signal-router
python3 -m router serve
```

That writes the outputs, then serves the dashboard. Open **http://localhost:8000** in a browser. If 8000 is taken:

```bash
python3 -m router serve --port 8765
```

Then open **http://localhost:8765**. Run every command from the repo root so `python3 -m router` can find the package. The CSVs are already in `data/`; you do not need to convert the original spreadsheets.

```bash
python3 -m router build        # just write out/queue.json, out/queue.csv, out/index.html
python3 -m unittest -v         # tests: Caliber worked example, routing exceptions, breakdowns add up
```

`out/index.html` is self-contained, so you can also open that file directly in a browser.

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
