"""Command line.

    python -m forecast_review               # weekly review, traces for every flagged item
    python -m forecast_review backtest      # pre-registered seasonality backtest, by retailer
    python -m forecast_review regression    # one rule change, checked against identical data
    python -m forecast_review shadow        # a candidate beside the live review, report only

Options: --seed N (synthetic data), --llm (ask a model to refute), --out DIR
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

from . import pipeline, report, synthetic, validation
from .agents import LLMRefuter, Refuter
from .config import ADOPTION, DEFAULT
from .synthetic import AS_OF


def _review(weekly, plan, args) -> None:
    refuter = LLMRefuter() if args.llm else Refuter()
    rows = pipeline.review(weekly, plan, AS_OF, refuter=refuter)
    print(report.summary(rows), end="\n\n")
    for row in rows:
        if row.proposal.flagged:
            print(report.trace(row), end="\n\n")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "review.md").write_text(report.markdown(rows, AS_OF), encoding="utf-8")
    pipeline.to_frame(rows).to_csv(out / "decisions.csv", index=False)
    pipeline.revised_plan(rows, plan).to_csv(out / "revised_plan.csv", index=False)
    print(f"Written: {out / 'review.md'}, {out / 'decisions.csv'}, {out / 'revised_plan.csv'}")


def _backtest(weekly, plan, args) -> None:
    print(f"Adoption rule, fixed before any result: seasonal must beat flat by at least "
          f"{ADOPTION.min_gain_points:.1f} WMAPE points, on at least {ADOPTION.min_items} items.\n")
    table = validation.seasonal_backtest(weekly, AS_OF)
    shown = table.rename(columns={
        "wmape_naive": "naive", "wmape_flat": "flat", "wmape_seasonal": "seasonal",
        "bias_seasonal": "bias", "value_added_vs_naive": "vs naive", "gain_vs_flat": "vs flat"})
    for col in ("naive", "flat", "seasonal", "bias"):
        shown[col] = shown[col].map("{:+.1%}".format if col == "bias" else "{:.1%}".format)
    for col in ("vs naive", "vs flat"):
        shown[col] = shown[col].map("{:+.1f}".format)
    print("WMAPE by forecast (8 weeks ahead, 4 rolling origins); gains in WMAPE points.\n")
    print(shown.to_string(index=False))
    adopted = (table["decision"] == "ADOPT").sum()
    print(f"\nSeasonal curve adopted for {adopted} of {len(table)} retailers. "
          "'vs naive' is the forecast value added over repeating last week.")


def _regression(weekly, plan, args) -> None:
    print("Change under test: protect new items from cuts for their first "
          f"{DEFAULT.new_item_weeks} weeks.\n")
    before = pipeline.review(weekly, plan, AS_OF, cfg=replace(DEFAULT, new_item_weeks=0))
    after = pipeline.review(weekly, plan, AS_OF)
    diff = validation.compare(before, after, labels=("before", "after"))
    print(diff.to_string(index=False) if len(diff) else "No differences.")
    intended = diff.empty or (diff["weeks_of_history"] < DEFAULT.new_item_weeks).all()
    print(f"\n{'PASS' if intended else 'FAIL'}: {len(diff)} item(s) changed, "
          f"{'all of them new items' if intended else 'including items the change should not touch'}.")


def _shadow(weekly, plan, args) -> None:
    print("Candidate: the same rules without the refuter. Nothing downstream is connected.\n")
    live = pipeline.review(weekly, plan, AS_OF)
    candidate = pipeline.review(weekly, plan, AS_OF, use_refuter=False)
    diff = validation.compare(live, candidate)
    print(diff.to_string(index=False) if len(diff) else "No differences this week.")
    print(f"\nWithout the refuter, {len(diff)} item(s) would have been changed this week.")


def main(argv: list[str] | None = None) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="forecast_review", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", nargs="?", default="review",
                        choices=["review", "backtest", "regression", "shadow"])
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--llm", action="store_true", help="ask a model to refute (needs ANTHROPIC_API_KEY)")
    parser.add_argument("--out", default="output")
    args = parser.parse_args(argv)

    weekly, plan = synthetic.generate(args.seed)
    {"review": _review, "backtest": _backtest,
     "regression": _regression, "shadow": _shadow}[args.command](weekly, plan, args)


if __name__ == "__main__":
    main()
