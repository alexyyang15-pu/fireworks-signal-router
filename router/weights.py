"""Every scoring and routing weight in one place.

DESIGN.md, DIAGRAMS.md, and the "Why this score" panel all quote these values.
Change a number here and every output follows.
"""

# Account blend. Customers and prospects are ranked in separate lists.
BLEND = {
    "customer": {"signal": 0.60, "fit": 0.30, "recency": 0.10},
    "prospect": {"signal": 0.45, "fit": 0.45, "recency": 0.10},
}

# Fit is the same formula for everyone.
FIT_MIX = {"arr": 0.50, "industry": 0.50}

# Signals on one account stack with diminishing returns; the 4th+ add nothing.
STACK_WEIGHTS = [1.00, 0.25, 0.12]
SIGNAL_CAP = 100.0

# Recency maps the account's newest signal onto this range across the file's time window.
RECENCY_FLOOR = 40.0
RECENCY_CEILING = 100.0

SEVERITY_POINTS = {"high": 5, "medium": 0, "low": -5}

# --- intent_topic: base + intensity x scale + topic + source + severity
INTENT_BASE = 50
INTENT_INTENSITY_SCALE = 30
INTENT_TOPIC_POINTS = {
    "GPU alternatives": 10,
    "LLM inference cost optimization": 10,
    "model serving latency": 10,
    "fine-tuning platform": 10,
    "function calling API": 10,
    "open-source LLM hosting": 10,
    "RAG pipeline infrastructure": 4,
}
INTENT_SOURCE_POINTS = {"G2": 6, "6sense": 6, "Harmonic": 3, "web_traffic": 0}

# --- funding_event: round + min(cap, amount / divisor) + severity
FUNDING_ROUND_POINTS = {
    "Seed Extension": 32,
    "Series A": 42,
    "Series B": 50,
    "Series C": 58,
    "Series D": 66,
}
FUNDING_AMOUNT_DIVISOR = 10
FUNDING_AMOUNT_CAP = 15

# --- competitor_evaluation: action + competitor + freshness + severity
COMPETITOR_ACTION_POINTS = {
    "pricing_page_visit": 82,
    "comparison_search": 74,
    "docs_read": 58,
    "benchmark_download": 46,
}
COMPETITOR_POINTS = {"Together AI": 6, "Replicate": 6, "Anyscale": 6, "OpenAI": 0}
# (max days since last signal, points); first match wins, else STALE.
COMPETITOR_FRESHNESS = [(7, 10), (14, 5), (21, 0)]
COMPETITOR_STALE_POINTS = -8

# --- job_change: points by the new hire's title, + severity
JOB_TITLE_POINTS = {
    "CTO": 78,
    "Head of AI": 78,
    "VP Infrastructure": 68,
    "Director of ML Platform": 68,
    "Chief Architect": 68,
    "Staff ML Engineer": 40,
}
JOB_TITLE_DEFAULT = 40

# --- usage_spike: base + min(cap, pct / divisor) + volume + severity
USAGE_BASE = 70
USAGE_PCT_DIVISOR = 20
USAGE_PCT_CAP = 20
# (min requests_7d, points); first match wins.
USAGE_VOLUME_POINTS = [(40000, 8), (20000, 5), (10000, 3)]

# --- fit inputs
ARR_POINTS = {
    "<$1M": 25,
    "$1M-$10M": 45,
    "$10M-$50M": 60,
    "$50M-$250M": 75,
    "$250M+": 90,
}
ARR_UNKNOWN = 50

# Anchored on public Fireworks customer proof and spend logic, not on book counts.
INDUSTRY_POINTS = {
    "DevTools": 100,
    "AI/ML": 88,
    "HealthTech": 76,
    "Logistics": 70,
    "Media": 58,
    "Cybersecurity": 55,
    "Telecom": 48,
    "FinTech": 36,
    "E-commerce": 30,
    "InsurTech": 28,
    "HR Tech": 22,
    "LegalTech": 20,
    "Manufacturing": 18,
    "Education": 12,
    "Energy": 10,
}
INDUSTRY_UNKNOWN = 40

# --- routing
TIER_BY_ARR = {
    "$250M+": "Strategic",
    "$50M-$250M": "Enterprise",
    "$10M-$50M": "Mid-Market",
    "$1M-$10M": "Mid-Market",
    "<$1M": "Mid-Market",
}
# When every rep for a tier is OOO, cover with the next tier down in the same territory.
COVER_TIER = {"Strategic": "Enterprise", "Enterprise": "Mid-Market"}
# Ramping reps get this share of their territory's signal accounts, mid-market matched prospects only.
RAMP_SHARE = 0.25
