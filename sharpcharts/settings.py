"""Brand-wide switches.

USE_TEAM_LOGOS: official team logos on helmets/badges. Turn OFF (False) before any sponsorship,
affiliate deal or other monetization: one switch removes logos from every post type.
"""
import os

USE_TEAM_LOGOS = os.environ.get("USE_TEAM_LOGOS", "true").strip().lower() != "false"
