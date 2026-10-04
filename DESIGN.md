# Signal Router: design

Scores signals **per account** and routes each account to one seller. Sellers see two lists in their app: **Customers** (expand) and **Prospects** (net-new).

## Routing logic

1. **Match the signal** by `account_id`, then exact domain. A name is not trusted: Umber Vision `.com` is not account A229 `.io`.
2. **Tier the accounts from ARR:** `$250M+` Strategic, `$50–250M` Enterprise, below that Mid-Market. `<$1M` has no tier, so Mid-Market takes it.
3. **Territory, then tier, then an active rep.** Two reps for one tier split by round robin, balancing current-customer counts.
4. **Exceptions**
   - **OOO:** Rachel is the only US-Central Strategic rep, so while she's OOO, Diego covers her accounts.
   - **Ramp:** Anika's capacity of 0 is overridden. She gets 25% of APAC signal accounts (2 of 8), mid-market only. Her manager needs to sign off.
   - **Not in CRM:** We define it as Mid-Market in that region. Tier is unknown.
5. **Capacity** is checked on every assignment. Overflow waits.

## Scoring approach

| | Signal | Fit | Recency | Why |
| --- | --- | --- | --- | --- |
| Customer | 60% | 30% | 10% | What they just did matters most |
| Prospect | 45% | 45% | 10% | Fit is unproven, so it counts equally |

**Each signal scores 0–100 from its own payload, not a flat value per type.** The exact point values, each ranked with a written justification, are in [DIAGRAMS.md](DIAGRAMS.md).

- **Usage spike:** grows with the size of the increase and the request volume behind it, so a big jump on a tiny base cannot pass for a large account.
- **Competitor visit:** scores on what they did and how recently they did it.
- **Intent:** grows with intensity, how close the topic is to our product, and the source.
- **Job change:** scores by seniority of title. A departure counts less than an arrival.
- **Funding:** scores by round and check size.
- **Industry ranks** use public Fireworks customers (Cursor, Sourcegraph, Vercel, Heidi Health, DoorDash, Quora) as evidence. At 45/45, strong fit can carry a weak signal.
- **Stack the signals:** the account's signal score is a weighted sum — 1.00 × strongest + 0.25 × second + 0.12 × third, capped at 100. Each extra signal counts less than the one above it, so a pile of weak signals cannot outrank one strong one.

**Fit and recency**

- **Fit is half ARR, half industry**, so a small AI-native account in a strong industry can rise.
- **Recency is 10%** because the file covers six days. Severity moves a signal ±5.

## Failure modes

1. **Entity resolution.** 32% of signals don't match to an account. Fuzzy matching would merge the wrong Umber Vision.
2. **Coverage.** One more absence in US-Central leaves nobody.
3. **No owner column.** The existing owner would be first in line. The file does not have one.
4. **Ramp.** Anika's 25% is a judgment call and needs her manager to approve.
5. **Industry rankings.** Based on public Fireworks customers, but missing the context of the whole customer base, so may need some re-ranking.

## Out of scope for v1

Log each signal under its account in Salesforce and track pipeline. Each month, adjust signal scoring when an industry, signal, topic, or source converts above its rank, so the scoring learns from actual sales results on a cadence.

## How AI was used

- **Good for:** finding the 16 unmatched signals, the Umber Vision collision, the out-of-office and ramp gaps, and that every usage spike is a customer. Researching public Fireworks customers for the industry rankings. Creating the router, tests, and visual dashboard.
- **Where it fell short:** the first point values had no reasons, so I made it justify each one. It proposed a different fit formula per segment. I replaced that with one formula, half ARR and half industry.
- **What I decided:** the weights in the table above. The industry ranking, after using AI to research Fireworks' public customers and products. Anika gets 25% of APAC signal accounts while she ramps. Diego covers Rachel (OOO), so a signal does not sit in a queue. I also made sure every signal ranking in [DIAGRAMS.md](DIAGRAMS.md) has written justification.
