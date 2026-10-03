import csv
import json
from pathlib import Path

from . import content
from . import weights as W
from .data import load
from .routing import build_cards, route_all


def run(data_dir: Path):
    ds = load(data_dir)
    cards = build_cards(ds)
    router = route_all(ds, cards)
    return ds, cards, router


def card_to_dict(card, rank):
    a = card.account
    return {
        "key": card.key,
        "rank": rank,
        "list": card.list_name,
        "account_id": a.account_id if a else None,
        "name": card.name,
        "domain": card.domain,
        "region": card.region,
        "segment": card.segment,
        "tier": card.tier,
        "industry": a.industry if a else None,
        "arr_band": a.arr_band if a else None,
        "match": card.match,
        "score": card.score.display,
        "score_100": card.score.total,
        "components": {
            "stacked_signals": round(card.score.stacked, 1),
            "fit": round(card.score.fit, 1),
            "arr_points": card.score.arr_points,
            "industry_points": card.score.industry_points,
            "recency": round(card.score.recency, 1),
        },
        "owner": {"id": card.owner.seller_id, "name": card.owner.name} if card.owner else None,
        "route_reason": card.route_reason,
        "flags": card.flags,
        "signals": [
            {
                "signal_id": s.signal.signal_id,
                "type": s.signal.signal_type,
                "timestamp": s.signal.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "severity_hint": s.signal.severity,
                "headline": s.headline,
                "score": round(s.score, 1),
                "contribution": card.score.lines[i].points,
                "parts": [{"label": l, "points": round(p, 1)} for l, p in s.parts],
                "detail": s.signal.detail,
            }
            for i, s in enumerate(card.score.signals)
        ],
        "breakdown": [line.to_dict() for line in card.score.lines],
        "play": content.play(card),
        "brief": content.brief(card),
        "email": content.email(card),
        "salesforce_url": content.salesforce_url(card),
        "slack": content.slack_message(card),
    }


def build_output(ds, cards, router):
    rows = []
    for list_name in ("customer", "prospect"):
        ranked = [c for c in cards if c.list_name == list_name]
        rows += [card_to_dict(c, i + 1) for i, c in enumerate(ranked)]

    sellers = []
    for s in ds.sellers:
        mine = [c for c in cards if c.owner and c.owner.seller_id == s.seller_id]
        sellers.append({
            "id": s.seller_id,
            "name": s.name,
            "territory": s.territory,
            "tiers": s.tiers,
            "status": s.status,
            "capacity": s.capacity,
            "cards": len(mine),
            "customers": sum(1 for c in mine if c.is_customer),
            "prospects": sum(1 for c in mine if not c.is_customer),
        })

    times = [s.timestamp for s in ds.signals]
    return {
        "window": [min(times).strftime("%Y-%m-%d"), max(times).strftime("%Y-%m-%d")],
        "totals": {
            "signals": len(ds.signals),
            "accounts": len(cards),
            "customers": sum(1 for c in cards if c.is_customer),
            "prospects": sum(1 for c in cards if not c.is_customer),
            "unmatched_signals": sum(len(c.signals) for c in cards if not c.matched),
            "hold_queue": sum(1 for c in cards if c.owner is None),
        },
        "weights": {"blend": W.BLEND, "fit_mix": W.FIT_MIX, "stack": W.STACK_WEIGHTS},
        "sellers": sellers,
        "cards": rows,
    }


def write_outputs(output, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "queue.json").write_text(json.dumps(output, indent=2))

    with open(out_dir / "queue.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "list", "rank", "score", "account", "account_id", "region", "tier", "segment",
            "owner", "signals", "top_signal", "route_reason", "flags",
        ])
        for c in output["cards"]:
            w.writerow([
                c["list"], c["rank"], c["score"], c["name"], c["account_id"] or "", c["region"],
                c["tier"], c["segment"], c["owner"]["name"] if c["owner"] else "HOLD",
                len(c["signals"]), c["signals"][0]["headline"], c["route_reason"], " | ".join(c["flags"]),
            ])

    from .render import render_html
    (out_dir / "index.html").write_text(render_html(output))
