"""The decisions around the forecast, clean-room and on synthetic data.

Four small tools, one per write-up on the portfolio site:

    inventory      excess tiers from stock against forward demand, and 3-year aging
    plan_accuracy  how far ahead a customer's supply plan can be trusted
    coverage       days of coverage, the freight route it implies, and a supplier tier
    leakage        a forecast that looks too good, and the checks that catch it

Every parameter is an illustrative round number (see config.py). None is a production setting.
"""
