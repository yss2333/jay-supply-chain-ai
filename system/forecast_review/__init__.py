"""A clean-room version of a retail forecast review, on synthetic data.

signals -> rules -> investigator -> refuter -> decision, with the validation stages
that decide whether a change to any of it should ship.
"""
from .config import ADOPTION, DEFAULT, AdoptionRule, ReviewConfig
from .pipeline import ReviewRow, review

__all__ = ["ADOPTION", "DEFAULT", "AdoptionRule", "ReviewConfig", "ReviewRow", "review"]
