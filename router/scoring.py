from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple

from . import weights as W
from .data import Account, Signal, norm_name

Part = Tuple[str, float]

COMPETITOR_PHRASES = {
    "pricing_page_visit": "Visited %s pricing page",
    "comparison_search": "Searched %s comparisons",
    "docs_read": "Read %s docs",
    "benchmark_download": "Downloaded %s benchmark",
}


@dataclass
class SignalScore:
    signal: Signal
    score: float
    headline: str
    parts: List[Part]


@dataclass
class Line:
    label: str
    points: float
    rule: str
    parts: List[Part] = field(default_factory=list)

    def to_dict(self):
        return {
            "label": self.label,
            "points": self.points,
            "rule": self.rule,
            "parts": [{"label": l, "points": round(p, 1)} for l, p in self.parts],
        }


@dataclass
class AccountScore:
    signals: List[SignalScore]
    stacked: float
    arr_points: float
    industry_points: float
    fit: float
    recency: float
    total: float
    display: float
    lines: List[Line]


def _severity(signal: Signal) -> Part:
    return ("Severity hint %s" % signal.severity, W.SEVERITY_POINTS.get(signal.severity, 0))


def _first_match(thresholds, value, default, compare):
    for limit, points in thresholds:
        if compare(value, limit):
            return points
    return default


def score_signal(signal: Signal, is_customer: bool, customer_names=frozenset()) -> SignalScore:
    d = signal.detail
    t = signal.signal_type

    if t == "intent_topic":
        topic, source = d.get("topic", ""), d.get("source", "")
        intensity = float(d.get("intensity_score", 0))
        topic_pts = W.INTENT_TOPIC_POINTS.get(topic, 0)
        topic_kind = "direct workload" if topic_pts >= 10 else ("adjacent" if topic_pts else "off-topic")
        parts = [
            ("Intent base", W.INTENT_BASE),
            ("Intensity %.2f x %d" % (intensity, W.INTENT_INTENSITY_SCALE), intensity * W.INTENT_INTENSITY_SCALE),
            ("Topic: %s (%s)" % (topic, topic_kind), topic_pts),
            ("Source: %s" % source, W.INTENT_SOURCE_POINTS.get(source, 0)),
        ]
        headline = 'Researching "%s"' % topic

    elif t == "funding_event":
        rnd = d.get("round", "")
        amount = float(d.get("amount_usd_m", 0))
        parts = [
            ("Round: %s" % rnd, W.FUNDING_ROUND_POINTS.get(rnd, 40)),
            (
                "Amount $%gM / %d (cap %d)" % (amount, W.FUNDING_AMOUNT_DIVISOR, W.FUNDING_AMOUNT_CAP),
                min(W.FUNDING_AMOUNT_CAP, amount / W.FUNDING_AMOUNT_DIVISOR),
            ),
        ]
        headline = "Raised %s, $%gM" % (rnd, amount)

    elif t == "competitor_evaluation":
        competitor, action = d.get("competitor", ""), d.get("action", "")
        days = int(d.get("days_since_last_signal", 0))
        fresh = _first_match(W.COMPETITOR_FRESHNESS, days, W.COMPETITOR_STALE_POINTS, lambda v, lim: v <= lim)
        parts = [
            ("Action: %s" % action.replace("_", " "), W.COMPETITOR_ACTION_POINTS.get(action, 50)),
            ("%d days since last signal" % days, fresh),
        ]
        verb = COMPETITOR_PHRASES.get(action, action.replace("_", " ") + ": %s")
        headline = "%s (%d days since last signal)" % (verb % competitor, days)

    elif t == "job_change":
        title, direction = d.get("new_title", ""), d.get("direction", "")
        person, prev = d.get("person", ""), d.get("previous_company", "")
        title_points = W.JOB_ARRIVAL_POINTS.get(title, W.JOB_ARRIVAL_DEFAULT)
        if direction == "arrived":
            parts = [("Arrived: %s" % title, title_points)]
            if prev and norm_name(prev) in customer_names:
                parts.append(("Previous company %s is a customer" % prev, W.JOB_PREV_CUSTOMER_BONUS))
            headline = "New %s: %s (from %s)" % (title, person, prev)
        else:
            parts = [(
                "Departed: %s (%d x %g, seat opening)" % (title, title_points, W.JOB_DEPARTURE_SHARE),
                title_points * W.JOB_DEPARTURE_SHARE,
            )]
            note = "champion risk, seat opening" if is_customer else "seat opening"
            headline = "%s %s left (%s)" % (title, person, note)

    elif t == "usage_spike":
        pct = float(d.get("pct_increase_vs_baseline", 0))
        requests = int(d.get("requests_7d", 0))
        endpoint = d.get("endpoint", "")
        volume = _first_match(W.USAGE_VOLUME_POINTS, requests, 0, lambda v, lim: v >= lim)
        parts = [
            ("Usage base (observed product usage)", W.USAGE_BASE),
            (
                "+%g%% vs baseline / %d (cap %d)" % (pct, W.USAGE_PCT_DIVISOR, W.USAGE_PCT_CAP),
                min(W.USAGE_PCT_CAP, pct / W.USAGE_PCT_DIVISOR),
            ),
            ("Volume: %s requests in 7 days" % format(requests, ","), volume),
        ]
        headline = "Usage up %g%% on %s (%s requests in 7 days)" % (pct, endpoint, format(requests, ","))

    else:
        parts = [("Unrecognized signal type: %s" % t, 30)]
        headline = t

    parts.append(_severity(signal))
    return SignalScore(signal=signal, score=sum(p for _, p in parts), headline=headline, parts=parts)


def _round_lines(raw: List[float]) -> Tuple[List[float], float]:
    """Round each line to 0.1 so the rounded lines add up to the rounded total."""
    total = round(sum(raw), 1)
    tenths = [int(v * 10 // 1) for v in raw]
    remainder = int(round(total * 10)) - sum(tenths)
    order = sorted(range(len(raw)), key=lambda i: raw[i] * 10 - tenths[i], reverse=True)
    for i in order[: max(0, remainder)]:
        tenths[i] += 1
    return [t / 10 for t in tenths], total


def score_account(
    account: Optional[Account],
    signals: List[Signal],
    is_customer: bool,
    window: Tuple[datetime, datetime],
    customer_names=frozenset(),
) -> AccountScore:
    blend = W.BLEND["customer" if is_customer else "prospect"]
    scored = sorted(
        (score_signal(s, is_customer, customer_names) for s in signals), key=lambda s: s.score, reverse=True
    )

    contributions = []
    for weight, s in zip(W.STACK_WEIGHTS, scored):
        contributions.append((weight, s, weight * s.score))
    raw_stack = sum(c for _, _, c in contributions)
    stacked = min(W.SIGNAL_CAP, raw_stack)

    if account:
        arr_pts = W.ARR_POINTS.get(account.arr_band, W.ARR_UNKNOWN)
        ind_pts = W.INDUSTRY_POINTS.get(account.industry, W.INDUSTRY_UNKNOWN)
        arr_label, ind_label = "ARR %s" % account.arr_band, "Industry: %s" % account.industry
    else:
        arr_pts, ind_pts = W.ARR_UNKNOWN, W.INDUSTRY_UNKNOWN
        arr_label, ind_label = "ARR unknown (not in CRM)", "Industry unknown (not in CRM)"
    fit = W.FIT_MIX["arr"] * arr_pts + W.FIT_MIX["industry"] * ind_pts

    start, end = window
    newest = max(s.timestamp for s in signals)
    span = (end - start).total_seconds() or 1
    position = (newest - start).total_seconds() / span
    recency = W.RECENCY_FLOOR + (W.RECENCY_CEILING - W.RECENCY_FLOOR) * position

    ordinals = ["strongest signal", "2nd signal", "3rd signal"]
    raw_lines = []
    for i, (weight, s, _) in enumerate(contributions):
        rule = "%.1f x %.2f stack x %.2f signal weight" % (s.score, weight, blend["signal"])
        label = "%s (%s)" % (s.headline, ordinals[i])
        raw_lines.append((label, weight * s.score * blend["signal"], rule, s.parts))
    for s in scored[len(W.STACK_WEIGHTS):]:
        raw_lines.append(("%s (4th+ signal, not counted)" % s.headline, 0.0, "beyond the stack", s.parts))
    if raw_stack > W.SIGNAL_CAP:
        raw_lines.append((
            "Signal cap at %d" % W.SIGNAL_CAP,
            -(raw_stack - W.SIGNAL_CAP) * blend["signal"],
            "stacked %.1f capped to %d" % (raw_stack, W.SIGNAL_CAP),
            [],
        ))
    raw_lines.append((
        arr_label,
        arr_pts * W.FIT_MIX["arr"] * blend["fit"],
        "%d x %.2f ARR share x %.2f fit weight" % (arr_pts, W.FIT_MIX["arr"], blend["fit"]),
        [],
    ))
    raw_lines.append((
        ind_label,
        ind_pts * W.FIT_MIX["industry"] * blend["fit"],
        "%d x %.2f industry share x %.2f fit weight" % (ind_pts, W.FIT_MIX["industry"], blend["fit"]),
        [],
    ))
    raw_lines.append((
        "Recency: newest signal %s" % newest.strftime("%b %d"),
        recency * blend["recency"],
        "%.1f x %.2f recency weight" % (recency, blend["recency"]),
        [],
    ))

    rounded, total = _round_lines([p for _, p, _, _ in raw_lines])
    lines = [Line(label=l, points=r, rule=rule, parts=parts) for (l, _, rule, parts), r in zip(raw_lines, rounded)]

    return AccountScore(
        signals=scored,
        stacked=stacked,
        arr_points=arr_pts,
        industry_points=ind_pts,
        fit=fit,
        recency=recency,
        total=total,
        display=round(total / 10, 1),
        lines=lines,
    )
