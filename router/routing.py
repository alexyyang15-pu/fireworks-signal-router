import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from . import weights as W
from .data import Account, Dataset, Seller, Signal
from .scoring import AccountScore, score_account


@dataclass
class Card:
    key: str
    account: Optional[Account]
    name: str
    domain: str
    region: str
    is_customer: bool
    segment: str
    tier: str
    signals: List[Signal]
    match: str
    score: Optional[AccountScore] = None
    owner: Optional[Seller] = None
    route_reason: str = ""
    flags: List[str] = field(default_factory=list)

    @property
    def matched(self) -> bool:
        return self.account is not None

    @property
    def list_name(self) -> str:
        return "customer" if self.is_customer else "prospect"


def match_signal(ds: Dataset, signal: Signal) -> Tuple[Optional[Account], str]:
    """account_id first, then exact domain. A name-only hit is not trusted."""
    if signal.account_id and signal.account_id in ds.accounts:
        return ds.accounts[signal.account_id], "account_id"
    by_domain = ds.account_by_domain(signal.domain)
    if by_domain:
        return by_domain, "domain"
    return None, "unmatched"


def build_cards(ds: Dataset) -> List[Card]:
    grouped: Dict[str, List[Signal]] = defaultdict(list)
    accounts: Dict[str, Optional[Account]] = {}
    how: Dict[str, str] = {}
    for s in ds.signals:
        account, method = match_signal(ds, s)
        key = account.account_id if account else "UNMATCHED:" + s.domain.lower()
        grouped[key].append(s)
        accounts[key] = account
        how.setdefault(key, method)

    times = [s.timestamp for s in ds.signals]
    window = (min(times), max(times))
    names = {a.name.lower(): a for a in ds.accounts.values()}

    cards = []
    for key, signals in grouped.items():
        account = accounts[key]
        first = signals[0]
        if account:
            is_customer = account.is_customer
            tier = W.TIER_BY_ARR.get(account.arr_band, "Unknown")
            card = Card(
                key=key, account=account, name=account.name, domain=account.domain,
                region=account.region, is_customer=is_customer, segment=account.segment,
                tier=tier, signals=signals, match=how[key],
            )
        else:
            is_customer = any(
                s.signal_type == "usage_spike" and s.detail.get("is_customer") is True for s in signals
            )
            card = Card(
                key=key, account=None, name=first.account_name, domain=first.domain,
                region=first.region, is_customer=is_customer, segment="Unknown",
                tier="Unknown", signals=signals, match="unmatched",
            )
            card.flags.append("Fit unknown: account not in CRM")
            twin = names.get(first.account_name.lower())
            if twin:
                card.flags.append(
                    "Name matches %s (%s, %s) but the domain differs; confirm before merging"
                    % (twin.account_id, twin.name, twin.domain)
                )
        card.score = score_account(account, signals, is_customer, window, customer_names=ds.customer_names)
        cards.append(card)

    cards.sort(key=lambda c: (-c.score.total, c.name))
    return cards


class Router:
    def __init__(self, sellers: List[Seller]):
        self.sellers = sellers
        self.load: Dict[str, int] = defaultdict(int)
        self.load_by_list: Dict[Tuple[str, str], int] = defaultdict(int)

    def active(self, territory: str) -> List[Seller]:
        return [s for s in self.sellers if s.territory == territory and s.status == "active"]

    def _has_room(self, seller: Seller) -> bool:
        return self.load[seller.seller_id] < seller.capacity

    def _pick(self, candidates: List[Seller], card: Card) -> Optional[Seller]:
        """Round robin among equals: fewest cards of this list, then fewest overall."""
        open_reps = [s for s in candidates if self._has_room(s)]
        if not open_reps:
            return None
        return min(
            open_reps,
            key=lambda s: (self.load_by_list[(s.seller_id, card.list_name)], self.load[s.seller_id], s.seller_id),
        )

    def assign(self, card: Card, seller: Seller, reason: str):
        card.owner = seller
        card.route_reason = reason
        self.load[seller.seller_id] += 1
        self.load_by_list[(seller.seller_id, card.list_name)] += 1

    def route(self, card: Card):
        region = card.region

        if not card.matched:
            pool = [s for s in self.active(region) if "Mid-Market" in s.tiers]
            why = "Unmatched signal: mid-market rep in %s, tier unknown" % region
            rep = self._pick(pool, card)
            if rep:
                self.assign(card, rep, why)
            return

        everyone = [s for s in self.sellers if s.territory == region and card.tier in s.tiers]
        pool = [s for s in everyone if s.status == "active"]
        if pool:
            reason = "%s / %s" % (region, card.tier)
            if len(pool) > 1:
                reason += " (round robin: %s)" % " / ".join(s.name for s in pool)
            rep = self._pick(pool, card)
            if rep:
                self.assign(card, rep, reason)
            return

        cover_tier = W.COVER_TIER.get(card.tier)
        cover = [s for s in self.active(region) if cover_tier in s.tiers]
        rep = self._pick(cover, card)
        if rep:
            away = ", ".join("%s (%s)" % (s.name, s.status) for s in everyone) or "no rep"
            self.assign(card, rep, "%s / %s: temporary cover for %s" % (region, card.tier, away))
            card.flags.append("Temporary cover while %s is out" % away)


def ramp_cards(cards: List[Card], ramp_rep: Seller) -> List[Card]:
    """Highest-scoring matched mid-market prospects in the ramp rep's territory."""
    territory_cards = [c for c in cards if c.region == ramp_rep.territory]
    allowance = math.floor(W.RAMP_SHARE * len(territory_cards))
    eligible = [
        c for c in territory_cards
        if c.matched and not c.is_customer and c.tier == "Mid-Market"
    ]
    return sorted(eligible, key=lambda c: -c.score.total)[:allowance]


def route_all(ds: Dataset, cards: List[Card]) -> Router:
    router = Router(ds.sellers)

    for rep in (s for s in ds.sellers if s.status == "ramp"):
        picks = ramp_cards(cards, rep)
        share = len(picks), len([c for c in cards if c.region == rep.territory])
        for card in picks:
            router.assign(
                card, rep,
                "%s ramp starter book: %d of %d %s signal accounts, mid-market prospects only"
                % (rep.name, share[0], share[1], rep.territory),
            )
            card.flags.append("%s is ramping; manager reviews before outreach" % rep.name)

    for card in cards:
        if card.owner is None:
            router.route(card)

    for card in cards:
        if card.owner is None:
            card.route_reason = "No eligible active rep with capacity"
            card.flags.append("Hold queue: needs manager assignment")
    return router
