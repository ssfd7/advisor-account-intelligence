"""Advisor Account Intelligence: phase 1 demo (no LLM).

Synthetic fixtures are ingested into a LadybugDB graph with provenance and two kinds of time; a mock task store
holds the team queue. See solution/DEMO.md.
"""
from pathlib import Path

SOLUTION = Path(__file__).resolve().parents[1]
DATA = SOLUTION / "data"
STATE = SOLUTION / ".data"
GRAPH_DB = STATE / "graph.lbug"
TASK_DB = STATE / "tasks.sqlite"
