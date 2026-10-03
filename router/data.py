import csv
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Account:
    account_id: str
    name: str
    domain: str
    industry: str
    arr_band: str
    region: str
    is_customer: bool
    segment: str


@dataclass
class Seller:
    seller_id: str
    name: str
    territory: str
    tiers: List[str]
    capacity: int
    status: str


@dataclass
class Signal:
    signal_id: str
    signal_type: str
    account_id: str
    account_name: str
    domain: str
    region: str
    timestamp: datetime
    severity: str
    detail: Dict = field(default_factory=dict)


@dataclass
class Dataset:
    accounts: Dict[str, Account]
    sellers: List[Seller]
    signals: List[Signal]

    def account_by_domain(self, domain: str) -> Optional[Account]:
        domain = domain.strip().lower()
        for account in self.accounts.values():
            if account.domain.lower() == domain:
                return account
        return None

    @property
    def customer_names(self) -> set:
        return {norm_name(a.name) for a in self.accounts.values() if a.is_customer}


def norm_name(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _rows(path: Path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def load(data_dir: Path) -> Dataset:
    accounts = {}
    for r in _rows(data_dir / "accounts.csv"):
        accounts[r["account_id"]] = Account(
            account_id=r["account_id"],
            name=r["account_name"],
            domain=r["domain"],
            industry=r["industry"],
            arr_band=r["arr_band"],
            region=r["region"],
            is_customer=r["is_customer"].strip() in ("1", "1.0", "true", "True"),
            segment=r["segment_hint"],
        )

    sellers = [
        Seller(
            seller_id=r["seller_id"],
            name=r["name"],
            territory=r["territory"],
            tiers=[t for t in r["tiers"].split("|") if t],
            capacity=int(float(r["capacity"] or 0)),
            status=r["status"].strip(),
        )
        for r in _rows(data_dir / "sellers.csv")
    ]

    signals = [
        Signal(
            signal_id=r["signal_id"],
            signal_type=r["signal_type"],
            account_id=r["account_id"].strip(),
            account_name=r["account_name"],
            domain=r["domain"],
            region=r["region"],
            timestamp=_parse_time(r["timestamp"]),
            severity=r["severity_hint"].strip().lower(),
            detail=json.loads(r["detail"]) if r["detail"] else {},
        )
        for r in _rows(data_dir / "signals.csv")
    ]

    return Dataset(accounts=accounts, sellers=sellers, signals=signals)
