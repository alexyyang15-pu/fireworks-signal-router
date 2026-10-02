"""Seller-facing copy built from the signal payloads. Templates, no model calls."""

from urllib.parse import quote

from .routing import Card

SALESFORCE_BASE = "https://fireworks.lightning.force.com/lightning"

PLAYS = {
    "usage_spike": "Expansion: usage is climbing. Offer a capacity and pricing review before they hit limits.",
    "competitor_evaluation": "Displacement: they are evaluating a competitor now. Lead with a speed and cost benchmark.",
    "intent_topic": "Education: they are researching what we sell. Send the matching proof point and offer a technical session.",
    "job_change_arrived": "New buyer: introduce Fireworks in their first 90 days, before vendors are locked in.",
    "job_change_departed": "Seat opening: a leader left. Find who owns the decision now and get in front of their replacement early.",
    "funding_event": "Timing: fresh budget. Anchor on scaling inference cost as they grow.",
}

PROOF_BY_TOPIC = {
    "fine-tuning platform": "Notion fine-tuned on Fireworks and cut latency from about 2s to 350ms",
    "model serving latency": "Notion fine-tuned on Fireworks and cut latency from about 2s to 350ms",
    "function calling API": "Vercel's v0 auto-fixer, a fine-tuned function-calling model on Fireworks, got 40x faster end to end",
    "LLM inference cost optimization": "Cresta cut cost up to 100x versus GPT-4 with Fireworks Multi-LoRA",
    "GPU alternatives": "Cursor serves Fast Apply on Fireworks at about 1,000 tokens/sec",
    "open-source LLM hosting": "Quora saw a 3x response-time speedup after moving open models to Fireworks",
    "RAG pipeline infrastructure": "Notion runs AI workflows for 100M+ users on Fireworks",
}
DEFAULT_PROOF = "Cursor, Notion, and Vercel run production inference on Fireworks"


def _play_key(signal):
    if signal.signal_type == "job_change":
        return "job_change_" + signal.detail.get("direction", "arrived")
    return signal.signal_type


def play(card: Card) -> str:
    top = card.score.signals[0].signal
    return PLAYS.get(_play_key(top), "Review the signal and decide on outreach.")


def proof_point(card: Card) -> str:
    for s in card.signals:
        topic = s.detail.get("topic")
        if topic in PROOF_BY_TOPIC:
            return PROOF_BY_TOPIC[topic]
    return DEFAULT_PROOF


def brief(card: Card) -> str:
    who = card.account
    if who:
        status = "existing customer" if card.is_customer else "prospect"
        opener = "%s: %s %s, %s, %s ARR, %s segment." % (
            card.name, card.region, status, who.industry, who.arr_band, who.segment,
        )
    else:
        opener = "%s (%s) is not in the CRM yet; ARR and industry are unknown." % (card.name, card.domain)

    happened = "; ".join(s.headline for s in card.score.signals)
    return "%s What happened: %s. Play: %s Proof point: %s." % (opener, happened, play(card), proof_point(card))


def _contact(card: Card) -> str:
    for s in card.signals:
        if s.signal_type == "job_change" and s.detail.get("direction") == "arrived":
            return s.detail.get("person", "")
    return ""


def email(card: Card) -> dict:
    top = card.score.signals[0].signal
    d = top.detail
    name = _contact(card)
    greeting = "Hi %s," % name.split()[0] if name else "Hi there,"
    proof = proof_point(card)

    if top.signal_type == "usage_spike":
        subject = "Your Fireworks usage is up %g%%" % d.get("pct_increase_vs_baseline", 0)
        hook = (
            "I noticed traffic on %s is up %g%% over baseline this week. Happy to review capacity, "
            "dedicated deployments, and pricing so the growth stays fast and predictable."
            % (d.get("endpoint", "your endpoints"), d.get("pct_increase_vs_baseline", 0))
        )
    elif top.signal_type == "competitor_evaluation":
        subject = "Benchmarking inference options for %s" % card.name
        hook = (
            "If you are comparing inference providers right now, I can share a head-to-head on latency "
            "and cost for your workload. %s." % proof
        )
    elif top.signal_type == "intent_topic":
        subject = "%s at %s" % (d.get("topic", "Inference").capitalize(), card.name)
        hook = (
            "Teams looking at %s usually care about speed and cost per token. %s. "
            "Worth a 20-minute technical session?" % (d.get("topic", "inference"), proof)
        )
    elif top.signal_type == "job_change" and d.get("direction") == "arrived":
        subject = "Congrats on the new role at %s" % card.name
        hook = (
            "Congrats on joining as %s. New platform leaders often revisit their inference stack early. "
            "%s. Open to comparing notes?" % (d.get("new_title", "a new leader"), proof)
        )
    elif top.signal_type == "job_change":
        subject = "Who is picking up AI infrastructure at %s?" % card.name
        hook = (
            "I saw %s moved on from the %s role. Who is picking up their inference and model "
            "infrastructure work? Happy to brief them. %s." % (d.get("person", "a teammate"), d.get("new_title", "platform"), proof)
        )
    else:
        subject = "Congrats on the %s" % d.get("round", "raise")
        hook = (
            "Congrats on the %s. As usage scales, inference cost is often the first line item to grow. "
            "%s. Worth a quick conversation?" % (d.get("round", "raise"), proof)
        )

    body = "%s\n\n%s\n\nBest,\n%s" % (greeting, hook, card.owner.name if card.owner else "")
    return {
        "subject": subject,
        "body": body,
        "mailto": "mailto:?subject=%s&body=%s" % (quote(subject), quote(body)),
    }


def salesforce_url(card: Card) -> str:
    if card.account:
        return "%s/r/Account/%s/view" % (SALESFORCE_BASE, card.account.account_id)
    return "%s/o/Account/new?defaultFieldValues=Name=%s,Website=%s" % (
        SALESFORCE_BASE, quote(card.name), quote(card.domain),
    )


def slack_message(card: Card) -> str:
    top = card.score.signals[0]
    extra = len(card.signals) - 1
    more = " (+%d more)" % extra if extra else ""
    return "%s scored %.1f / 10. %s%s. %s" % (card.name, card.score.display, top.headline, more, play(card))
