import unittest
from datetime import datetime
from pathlib import Path

from router import weights as W
from router.data import Signal
from router.pipeline import build_output, run
from router.scoring import score_signal

DATA = Path(__file__).resolve().parent.parent / "data"


class RouterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ds, cards, router = run(DATA)
        cls.out = build_output(ds, cards, router)
        cls.cards = {c["name"]: c for c in cls.out["cards"]}

    def test_breakdown_lines_add_up_to_every_score(self):
        for c in self.out["cards"]:
            total = round(sum(line["points"] for line in c["breakdown"]), 1)
            self.assertEqual(total, c["score_100"], c["name"])
            self.assertEqual(c["score"], round(c["score_100"] / 10, 1), c["name"])

    def test_caliber_worked_example(self):
        c = self.cards["Caliber Robotics"]
        self.assertEqual(c["list"], "customer")
        self.assertEqual(c["score_100"], 87.2)
        self.assertEqual([l["points"] for l in c["breakdown"]], [46.5, 9.8, 13.5, 10.5, 6.9])
        self.assertEqual(c["components"]["stacked_signals"], 93.8)
        self.assertEqual(c["components"]["fit"], 80.0)

    def test_one_card_per_account(self):
        self.assertEqual(self.out["totals"]["accounts"], 44)
        self.assertEqual(len(self.cards["Lupine Scale"]["signals"]), 3)

    def test_usage_spikes_only_on_customer_list(self):
        for c in self.out["cards"]:
            if any(s["type"] == "usage_spike" for s in c["signals"]):
                self.assertEqual(c["list"], "customer", c["name"])

    def test_name_only_match_is_not_trusted(self):
        c = self.cards["Umber Vision"]
        self.assertIsNone(c["account_id"])
        self.assertTrue(any("A229" in f for f in c["flags"]))

    def test_ooo_rep_gets_nothing_and_is_covered(self):
        rachel = next(s for s in self.out["sellers"] if s["name"] == "Rachel Park")
        self.assertEqual(rachel["cards"], 0)
        for name in ("Caliber Robotics", "Hemp Intelligence", "Tarragon Scale"):
            self.assertEqual(self.cards[name]["owner"]["name"], "Diego Morales")
            self.assertIn("temporary cover", self.cards[name]["route_reason"])

    def test_ramp_rep_gets_two_of_eight_mid_market_prospects(self):
        anika = [c for c in self.out["cards"] if c["owner"] and c["owner"]["name"] == "Anika Reddy"]
        self.assertEqual(sorted(c["name"] for c in anika), ["Chert Scale", "Osprey Grid"])
        for c in anika:
            self.assertEqual((c["list"], c["tier"]), ("prospect", "Mid-Market"))
        self.assertEqual(self.cards["Thorn Data"]["owner"]["name"], "Hiro Tanaka")

    def test_us_east_strategic_round_robin(self):
        owners = {self.cards[n]["owner"]["name"] for n in ("Grove Grid", "Yarrow Build")}
        self.assertEqual(owners, {"Alex Rivera", "Chris Walsh"})

    def test_arrival_from_customer_scores_higher(self):
        base = dict(
            signal_id="T", signal_type="job_change", account_id="", account_name="X",
            domain="x.io", region="US-East", timestamp=datetime(2026, 8, 12), severity="medium",
        )
        detail = {"person": "P", "new_title": "CTO", "direction": "arrived"}
        warm = score_signal(Signal(detail=dict(detail, previous_company="Caliber Robotics"), **base), False, {"caliberrobotics"})
        cold = score_signal(Signal(detail=dict(detail, previous_company="Nowhere Inc"), **base), False, {"caliberrobotics"})
        self.assertEqual(warm.score - cold.score, W.JOB_PREV_CUSTOMER_BONUS)
        self.assertTrue(any("customer" in label for label, _ in warm.parts))
        # departures never get the bonus
        left = score_signal(
            Signal(detail=dict(detail, previous_company="Caliber Robotics", direction="departed"), **base),
            False, {"caliberrobotics"},
        )
        self.assertFalse(any("customer" in label for label, _ in left.parts))

    def test_nothing_on_hold_and_capacity_respected(self):
        self.assertEqual(self.out["totals"]["hold_queue"], 0)
        for s in self.out["sellers"]:
            if s["status"] == "active":
                self.assertLessEqual(s["cards"], s["capacity"], s["name"])


if __name__ == "__main__":
    unittest.main()
