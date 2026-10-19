"""Mock task store: team review queue, candidate takeaways, actions, assignments and coverage (SQLite).

Rules enforced here (brief §7, FR7, FR11, FR12):
- every saved interaction gets a team-owned review item with a deadline, whether or not extraction found anything;
- only an available author, the team lead, or a rep holding an acknowledged assignment may review or act;
- an assignment is offered, then acknowledged; a notification alone never completes it;
- offering or acknowledging again does not create duplicates;
- an action closes only with completion evidence; overdue offers escalate to the team lead.
"""
import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from .roster import Roster

SCHEMA = """
CREATE TABLE IF NOT EXISTS review_items(interaction_id TEXT PRIMARY KEY, team TEXT, author TEXT, saved_at TEXT,
    deadline TEXT, status TEXT, resolved_by TEXT, resolved_at TEXT, note TEXT);
CREATE TABLE IF NOT EXISTS candidates(id TEXT PRIMARY KEY, interaction_id TEXT, kind TEXT, payload TEXT, status TEXT,
    span_id TEXT, quotes TEXT, decided_by TEXT, decided_at TEXT, reason TEXT);
CREATE TABLE IF NOT EXISTS actions(id TEXT PRIMARY KEY, interaction_id TEXT, title TEXT, payload TEXT, team TEXT,
    created_by TEXT, approved_by TEXT, assignee TEXT, status TEXT, due TEXT, evidence TEXT, closed_at TEXT);
CREATE TABLE IF NOT EXISTS assignments(id TEXT PRIMARY KEY, work_type TEXT, work_id TEXT, to_rep TEXT, offered_by TEXT,
    offered_at TEXT, deadline TEXT, acknowledged_at TEXT, status TEXT);
CREATE TABLE IF NOT EXISTS coverage(id TEXT PRIMARY KEY, team TEXT, covers_for TEXT, covered_by TEXT, activated_by TEXT,
    activated_at TEXT);
CREATE TABLE IF NOT EXISTS availability(rep TEXT, unavailable_from TEXT, reason TEXT, PRIMARY KEY(rep, unavailable_from));
CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT, actor TEXT, event TEXT, detail TEXT);
"""


class NotAuthorized(Exception):
    pass


class TaskStore:
    def __init__(self, path: Path, roster: Roster, fresh: bool = False):
        path = Path(path)
        if fresh and path.exists():
            path.unlink()
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.roster = roster

    # ------------------------------------------------------------ helpers

    def _rows(self, sql, *args):
        return [dict(r) for r in self.db.execute(sql, args)]

    def _one(self, sql, *args):
        r = self.db.execute(sql, args).fetchone()
        return dict(r) if r else None

    def log(self, at, actor, event, **detail):
        self.db.execute("INSERT INTO events(at, actor, event, detail) VALUES (?, ?, ?, ?)",
                        (str(at), actor, event, json.dumps(detail, default=str)))
        self.db.commit()

    def events(self):
        return self._rows("SELECT at, actor, event, detail FROM events ORDER BY seq")

    # ------------------------------------------------------------ availability and authority

    def mark_unavailable(self, rep: str, at: date, reason: str):
        self.db.execute("INSERT OR IGNORE INTO availability VALUES (?, ?, ?)", (rep, str(at), reason))
        self.db.commit()
        self.log(at, rep, "unavailable", reason=reason)

    def available(self, rep: str, at: date) -> bool:
        return self._one("SELECT 1 FROM availability WHERE rep = ? AND unavailable_from <= ?", rep, str(at)) is None

    def _acknowledged(self, rep, work_type, work_id):
        return self._one("SELECT 1 FROM assignments WHERE work_type = ? AND work_id = ? AND to_rep = ? AND status = 'acknowledged'",
                         work_type, work_id, rep) is not None

    def check_review_authority(self, rep: str, interaction_id: str, at: date) -> str:
        item = self.review_item(interaction_id)
        team = self.roster.teams[item["team"]]
        if rep not in team.members:
            raise NotAuthorized(f"{rep} is not on {team.id}")
        if rep == item["author"] and self.available(rep, at):
            return "author"
        if rep == team.lead:
            return "team lead"
        if self._acknowledged(rep, "review", interaction_id):
            return "acknowledged coverage assignment"
        raise NotAuthorized(f"{rep} has no authority to review {interaction_id}: not the available author, "
                            f"not the team lead, and holds no acknowledged assignment")

    # ------------------------------------------------------------ review items and candidates

    def save_interaction(self, interaction_id, team, author, saved_at: date):
        deadline = saved_at + timedelta(days=self.roster.teams[team].review_days)
        cur = self.db.execute("INSERT OR IGNORE INTO review_items VALUES (?, ?, ?, ?, ?, 'pending review', NULL, NULL, NULL)",
                              (interaction_id, team, author, str(saved_at), str(deadline)))
        self.db.commit()
        if cur.rowcount:
            self.log(saved_at, author, "review item created", interaction=interaction_id, team=team, deadline=str(deadline))

    def review_item(self, interaction_id):
        return self._one("SELECT * FROM review_items WHERE interaction_id = ?", interaction_id)

    def add_candidate(self, cid, interaction_id, kind, payload, span_id, quotes=None):
        status = "repetition" if quotes else "candidate"
        self.db.execute("INSERT OR IGNORE INTO candidates VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL)",
                        (cid, interaction_id, kind, json.dumps(payload, default=str), status, span_id, quotes))
        self.db.commit()

    def candidates(self, interaction_id, status=None):
        rows = self._rows("SELECT * FROM candidates WHERE interaction_id = ? ORDER BY id", interaction_id)
        for r in rows:
            r["payload"] = json.loads(r["payload"])
        return [r for r in rows if status is None or r["status"] == status]

    def resolve_review(self, rep, interaction_id, at: date, decisions: dict, promote, no_action_reason=None):
        """Decide every open candidate (confirm or reject with reason). With nothing to confirm, a reason for
        'no action needed' is required. Confirmed candidates are promoted to memory by `promote`."""
        item = self.review_item(interaction_id)
        if item["status"] in ("reviewed", "no action needed"):
            return item
        how = self.check_review_authority(rep, interaction_id, at)
        open_ = self.candidates(interaction_id, "candidate")
        missing = [c["id"] for c in open_ if c["id"] not in decisions]
        if missing:
            raise ValueError(f"undecided candidates: {missing}")
        confirmed = 0
        for c in open_:
            decision = decisions[c["id"]]
            if decision == "confirm":
                promote(c, rep, at)
                confirmed += 1
                status, reason = "confirmed", None
            else:
                status, reason = "rejected", decision
            self.db.execute("UPDATE candidates SET status = ?, decided_by = ?, decided_at = ?, reason = ? WHERE id = ?",
                            (status, rep, str(at), reason, c["id"]))
        if not confirmed and not no_action_reason:
            raise ValueError("nothing confirmed: record an explicit 'no action needed' disposition with a reason")
        status = "reviewed" if confirmed else "no action needed"
        self.db.execute("UPDATE review_items SET status = ?, resolved_by = ?, resolved_at = ?, note = ? WHERE interaction_id = ?",
                        (status, rep, str(at), no_action_reason, interaction_id))
        self.db.commit()
        self.log(at, rep, "review resolved", interaction=interaction_id, status=status, authority=how, confirmed=confirmed)
        return self.review_item(interaction_id)

    # ------------------------------------------------------------ assignments and coverage

    def offer(self, work_type, work_id, to_rep, by, at: date, days=2):
        aid = f"ASG:{work_type}:{work_id}:{to_rep}"
        cur = self.db.execute("INSERT OR IGNORE INTO assignments VALUES (?, ?, ?, ?, ?, ?, ?, NULL, 'offered')",
                              (aid, work_type, work_id, to_rep, by, str(at), str(at + timedelta(days=days))))
        self.db.commit()
        if cur.rowcount:
            self.log(at, by, "assignment offered", assignment=aid)
            self.log(at, "system", "notification sent", to=to_rep, assignment=aid)
        return self.assignment(aid)

    def assignment(self, aid):
        return self._one("SELECT * FROM assignments WHERE id = ?", aid)

    def assignments(self):
        return self._rows("SELECT * FROM assignments ORDER BY id")

    def acknowledge(self, rep, aid, at: date):
        a = self.assignment(aid)
        if a["to_rep"] != rep:
            raise NotAuthorized(f"{aid} is offered to {a['to_rep']}, not {rep}")
        if a["status"] == "acknowledged":
            return a
        self.db.execute("UPDATE assignments SET status = 'acknowledged', acknowledged_at = ? WHERE id = ?", (str(at), aid))
        if a["work_type"] == "action":
            self.db.execute("UPDATE actions SET assignee = ? WHERE id = ?", (rep, a["work_id"]))
        self.db.commit()
        self.log(at, rep, "assignment acknowledged", assignment=aid)
        return self.assignment(aid)

    def activate_coverage(self, lead, team_id, covers_for, covered_by, at: date):
        team = self.roster.teams[team_id]
        if lead != team.lead:
            raise NotAuthorized(f"only {team.lead} can activate coverage for {team_id}")
        if covered_by not in team.members or not self.available(covered_by, at):
            raise ValueError(f"{covered_by} cannot cover: not an available member of {team_id}")
        cid = f"COV:{team_id}:{covers_for}:{covered_by}:{at}"
        self.db.execute("INSERT OR IGNORE INTO coverage VALUES (?, ?, ?, ?, ?, ?)", (cid, team_id, covers_for, covered_by, lead, str(at)))
        self.db.commit()
        self.log(at, lead, "coverage activated", covers_for=covers_for, covered_by=covered_by)
        offers = []
        for item in self._rows("SELECT interaction_id FROM review_items WHERE team = ? AND author = ? AND status = 'pending review'",
                               team_id, covers_for):
            offers.append(self.offer("review", item["interaction_id"], covered_by, lead, at))
        for act in self._rows("SELECT id FROM actions WHERE team = ? AND assignee = ? AND status = 'approved'", team_id, covers_for):
            offers.append(self.offer("action", act["id"], covered_by, lead, at))
        return offers

    def escalate_overdue(self, at: date):
        escalated = []
        for a in self._rows("SELECT * FROM assignments WHERE status = 'offered' AND deadline < ?", str(at)):
            self.db.execute("UPDATE assignments SET status = 'escalated' WHERE id = ?", (a["id"],))
            self.log(at, "system", "escalated to team lead", assignment=a["id"])
            escalated.append(a["id"])
        self.db.commit()
        return escalated

    # ------------------------------------------------------------ actions

    def approve_action(self, rep, action: dict, at: date, write_graph=None):
        team = self.roster.teams[action["team"]]
        if rep != team.lead:
            self.check_review_authority(rep, action["interaction_id"], at)
        if not action.get("addresses") or not action.get("sources"):
            raise ValueError("an action needs the observations or intents it addresses and their sources")
        cur = self.db.execute("INSERT OR IGNORE INTO actions VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'approved', ?, NULL, NULL)",
                              (action["id"], action["interaction_id"], action["title"], json.dumps(action, default=str),
                               action["team"], action["created_by"], rep, rep, str(action["due"])))
        self.db.commit()
        if cur.rowcount:
            self.log(at, rep, "action approved", action=action["id"])
            if write_graph:
                write_graph(action, rep, at)
        return self.action(action["id"])

    def action(self, aid):
        return self._one("SELECT * FROM actions WHERE id = ?", aid)

    def complete_action(self, rep, aid, at: date, evidence: str, write_graph=None):
        a = self.action(aid)
        if a["assignee"] != rep:
            raise NotAuthorized(f"{aid} is assigned to {a['assignee']}")
        if not evidence:
            raise ValueError("completion evidence is required; the action stays open")
        self.db.execute("UPDATE actions SET status = 'completed', evidence = ?, closed_at = ? WHERE id = ?", (evidence, str(at), aid))
        self.db.commit()
        self.log(at, rep, "action completed", action=aid, evidence=evidence)
        if write_graph:
            write_graph(aid, evidence, at)
        return self.action(aid)

    # ------------------------------------------------------------ queue (CQ6)

    def queue(self, team_id, at: date):
        out = []
        for i in self._rows("SELECT * FROM review_items WHERE team = ? ORDER BY saved_at", team_id):
            if i["status"] != "pending review":
                continue
            offers = self._rows("SELECT to_rep, status FROM assignments WHERE work_type = 'review' AND work_id = ?", i["interaction_id"])
            owner = next((o["to_rep"] for o in offers if o["status"] == "acknowledged"), None)
            if owner is None and self.available(i["author"], at):
                owner = i["author"]
            out.append({"item": i["interaction_id"], "type": "review", "status": i["status"], "owner": owner or "UNOWNED",
                        "due": i["deadline"], "overdue": i["deadline"] < str(at),
                        "handoff": ", ".join(f"{o['to_rep']}:{o['status']}" for o in offers) or "-"})
        for a in self._rows("SELECT * FROM actions WHERE team = ? AND status = 'approved' ORDER BY id", team_id):
            offers = self._rows("SELECT to_rep, status FROM assignments WHERE work_type = 'action' AND work_id = ?", a["id"])
            owner = a["assignee"] if self.available(a["assignee"], at) else "UNOWNED"
            out.append({"item": a["id"], "type": "action", "status": a["status"], "owner": owner, "due": a["due"],
                        "overdue": a["due"] < str(at), "handoff": ", ".join(f"{o['to_rep']}:{o['status']}" for o in offers) or "-"})
        return out
