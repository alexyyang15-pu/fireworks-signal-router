# Signal Router: design

Scores signals **per account** and routes each account to one seller. Sellers see two lists: **Customers** (expand) and **Prospects** (net-new). Rankings of industry, signals, and their individual point values are in DIAGRAMS.md.

## Routing logic

1. **Match** by `account_id`, then exact domain. A name is not trusted: Umber Vision `.com` is not account A229 `.io`.
2. **Tier from ARR:** `$250M+` Strategic, `$50–250M` Enterprise, below that Mid-Market. `<$1M` has no tier, so Mid-Market takes it.
3. **Territory, then tier, then an active rep.** Two reps for one tier split by round robin, customers first.
4. **Exceptions**
   - **OOO:** A seller should jump on the signal. Rachel is the only US-Central Strategic rep, so Diego covers her accounts.
   - **Ramp:** Anika's capacity of 0 is overridden. She gets 25% of APAC signal accounts (2 of 8), mid-market only. Her manager needs to sign off.
   - **Not in CRM:** Mid-Market in that region, including usage spikes. Tier is unknown.
5. **Capacity** is checked on every assignment. Overflow waits.

## Scoring approach

| | Signal | Fit | Recency | Why |
| --- | --- | --- | --- | --- |
| Customer | 60% | 30% | 10% | They're already a customer, so what they just did matters most |
| Prospect | 45% | 45% | 10% | Fit is unproven, so it counts as much as the signal |

- **Stack:** strongest 1.00, second 0.25, third 0.12, cap 100. Extra signals count less than the one above them.
- **Fit is half ARR, half industry**, so a small AI-native account in a strong industry can rise.
- **Recency is 10%** because the file covers six days. Severity moves a signal ±5. Meridian at +354% labeled low still beats Cedar at +78% labeled high.
- **Industry ranks** use public Fireworks customers (Cursor, Sourcegraph, Vercel, Heidi Health, DoorDash, Quora). At 45/45, strong fit can carry a weak signal, and logos can rank an industry above its real share of customers.

## Failure modes

1. **Entity resolution.** 32% of signals don't match. Fuzzy matching would merge the wrong Umber Vision.
2. **Coverage.** Diego holds 12 of 44 accounts. One more absence in US-Central leaves nobody. Preventing that is the manager's job.
3. **No owner column.** The existing owner would be first in line. The file does not have one.
4. **Ramp.** Anika's 25% is a judgment call and needs her manager.

## Out of scope

Log each account against Salesforce pipeline. Each month, move a weight when an industry, signal, topic, or source converts above its rank. Rep actions also affect pipeline, so this is a regular review, not an automatic rewrite.

## What I'd do differently

- Route customers to their real owner before territory.
- Review fuzzy matches instead of treating unknown fit as neutral.

## How AI was used

- **Good for:** finding the 16 unmatched signals, the Umber Vision collision, the out-of-office and ramp gaps, and that every usage spike is a customer. Researching public Fireworks customers for the industry ladder. Writing the router, tests, and dashboard.
- **Where it fell short:** the first point values had no reasons, so I made it justify each one. It proposed a different fit formula per segment. I replaced that with one formula, half ARR and half industry.
- **What I decided:** the weights in the table above. The industry ranking, after using AI to research Fireworks' public customers and products. Anika gets 25% of APAC signal accounts while she ramps. Diego covers Rachel (OOO), so a signal does not sit in a queue.
