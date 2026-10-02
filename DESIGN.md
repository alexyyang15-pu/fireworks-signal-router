# Signal Router: design

Scores signals **per account** and routes each account to one seller. Sellers see two ranked lists: **Customers** (expand or protect) and **Prospects** (open). Every score is broken into "+X points" lines that add up to the number. Diagrams and full tables are in [DIAGRAMS.md](DIAGRAMS.md); every weight is in [`router/weights.py`](router/weights.py).

## Routing logic

1. **Match** by `account_id`, then exact domain. Name alone is not trusted: Umber Vision `.com` is not account A229 `.io`, so it is flagged instead of merged. 16 of 50 signals don't match.
2. **One card per account.** 50 signals become 44 cards.
3. **Tier from ARR:** `$250M+` Strategic, `$50–250M` Enterprise, below that Mid-Market. `<$1M` has no tier on the roster, so the nearest owner (Mid-Market) takes it.
4. **Territory, then tier, then an active rep.** US-East Strategic has two reps (Alex Rivera, Chris Walsh). Round robin balances customer cards first.
5. **Exceptions**
   - **OOO:** Rachel Park gets nothing. She is the only US-Central Strategic rep, so the next tier down (Diego Morales) covers her 3 accounts, flagged as temporary.
   - **Ramp:** Anika Reddy's capacity of 0 is deliberately overridden, because APAC is 90 accounts against Hiro Tanaka's cap of 50. She gets **25% of APAC signal accounts (2 of 8)**: matched mid-market prospects only. No customers, no Strategic accounts, no usage spikes. Both cards are flagged for manager review.
   - **Not in CRM:** a customer usage spike goes to the region's senior rep, since the revenue may be large. Everything else goes to Mid-Market. Tier is marked unknown.
6. **Capacity** is the max book size, checked on every assignment. Overflow goes to a hold queue. With 50 signals, nobody hits their cap.

## Scoring approach

| | Signal | Fit | Recency | Why |
|---|---|---|---|---|
| Customer | 60% | 30% | 10% | Their usage already proves fit, so what they just did matters most |
| Prospect | 45% | 45% | 10% | Fit is unproven, so it counts as much as the signal |

- **Stack:** the strongest signal counts at 1.00, the 2nd at 0.25, the 3rd at 0.12, capped at 100. More signals add conviction with diminishing returns: three medium signals tie one great signal, not triple it.
- **Fit = 50% ARR + 50% industry**, for everyone. The even split lets small AI-native accounts in strong industries rise, since inference revenue grows with them. Chert Scale is prospect #2.
- **Recency at 10%** only breaks ties, because the file covers six days.
- **Severity hint moves a signal ±5.** The payload sets the score: Meridian at +354% labeled "low" outranks Cedar at +78% labeled "high."

**Signal strength, highest to lowest:**

| | Signal | Points | Why it ranks here |
|---|---|---|---|
| 1 | Usage spike | 70 + growth + volume | Observed usage on a paying customer: a fact, not an inference |
| 2 | Competitor evaluation | pricing page 82 to benchmark download 46, plus freshness | Active vendor shopping. Together AI, Replicate, and Anyscale get +6 over OpenAI because that deal is winnable on price and speed |
| 3 | Intent topic | 50 + intensity×30 + topic + source | **Topic = product fit:** inference, serving, or fine-tuning +10; RAG (adjacent) +4. **Source = confidence in the data:** G2 and 6sense +6 (purpose-built in-market data); Harmonic +3 (coverage, not evaluation); web traffic 0 (noisiest) |
| 4 | New senior hire | CTO or Head of AI 78; VP or Director 68; Staff 40 | A new budget owner revisits the stack in their first 90 days. Staff engineers don't buy. The row's account is where the person joined; "departed" refers to their previous company |
| 5 | Funding | Series A 42 to Series D 66, + up to 15 for size | Budget timing, not intent |

**Industry ladder** (DevTools 100 down to Energy 10) is anchored on public Fireworks customers (Cursor, Sourcegraph, Vercel, Heidi Health, DoorDash, Quora), not on how many accounts each industry has in the book.

**Known tradeoff:** at 45/45, strong fit can carry a weak signal. Alabaster Mind (DevTools, `$250M+`, one funding event) is #7, ahead of Iris Secure (a Together AI comparison 4 days ago, but not in the CRM).

## Failure modes: where this breaks first

1. **Entity resolution.** 32% of signals don't match an account. Fuzzy matching would merge the wrong Umber Vision. Neutral fit means a hot signal can rank low because of missing data.
2. **Coverage.** One absence puts Strategic accounts on a mid-market rep, and Diego ends up holding 12 of 44 cards. A second absence in US-Central leaves no one to cover.
3. **No owner column.** For customers, the existing owner should beat territory. Without it, an account can land on a new rep.
4. **The ramp override.** Capacity 0 is the manager's call, and the 25% share is a judgment call.
5. **The weights are judgment, not data.** The industry ladder rests on customer logos, not revenue.
6. **Scale.** Routing the full 300-account book overflows APAC on day one. The hold queue catches it, but nothing rebalances.

## Closing the loop (out of scope; these weights are a first draft)

- Log every card with its breakdown, owner, and seller action. Join to Salesforce: opened pipeline, closed won, closed lost, or no action.
- Each quarter, compare conversion by score band and by each component: industry, signal type, topic, source, and severity. Then move weights where the gap is real. An industry converting above its rank moves up. A source or topic that predicts pipeline gains points. A signal type that never converts loses weight.
- Guardrails: a minimum sample before any change, a cap on how far a weight moves per cycle, and a small random holdout so the model doesn't only learn from what it already promoted.
- Later, fit a logistic model with readable coefficients so the "+X points" explanation survives.

## What I'd do differently

Route customers to their real owner before territory. Add a fuzzy-match review queue instead of neutral fit. Decay signals by age instead of using a linear window. Post to Slack as a bot DM with the same buttons the local page mocks.

## How AI was used

- **Good for:** profiling the files (it found the 16 unmatched signals, the Umber Vision collision, the OOO and ramp gaps, and that every usage spike is a customer); researching Fireworks' public customers; writing the router, tests, and page.
- **Where it failed:** its first point values had no stated reasons. I made it justify each one or change it, which is where "topic = fit, source = confidence" came from. It proposed a separate fit formula per segment, which I simplified to one. Its first proof-point lines overstated the case studies, so I rewrote them to match the sources.
- **What I decided myself:** the blend weights, scoring per account, separate customer and prospect views, Anika's 25% share, and the transparent breakdown.
