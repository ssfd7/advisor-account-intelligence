"""Team roster and relationship assignments (manual settings in phase 1; no HR or calendar integration)."""
from dataclasses import dataclass
from pathlib import Path

import yaml

from . import DATA


@dataclass
class Team:
    id: str
    name: str
    lead: str
    owner: str
    sme: str
    members: list
    relationships: list
    review_days: int


class Roster:
    def __init__(self, path: Path = DATA / "reference" / "roster.yaml"):
        raw = yaml.safe_load(Path(path).read_text())
        self.teams = {t["id"]: Team(**t) for t in raw["teams"]}
        self.reps = {r["id"]: r["name"] for r in raw["reps"]}
        self.roles = {r["id"]: r["role"] for r in raw["reps"]}
        self.smes = {r["id"] for r in raw["reps"] if r.get("sme")}

    def teams_of(self, rep: str) -> list:
        return [t for t in self.teams.values() if rep in t.members]

    def scope(self, rep: str) -> set:
        """Firms and advisors a rep may retrieve: those assigned to the rep's teams."""
        return {p for t in self.teams_of(rep) for p in t.relationships}

    def team_for_party(self, party: str):
        return next((t for t in self.teams.values() if party in t.relationships), None)
