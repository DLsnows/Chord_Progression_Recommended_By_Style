"""Session and branch management with SQLite persistence.

Schema: sessions, branches, chord_selections — see plan section 5 for details.
"""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    style_genre_tag TEXT NOT NULL,
    style_decade INTEGER NOT NULL,
    style_section TEXT NOT NULL,
    style_file TEXT NOT NULL,
    style_root_file TEXT NOT NULL,
    style_starting_probs TEXT NOT NULL DEFAULT '{}',
    active_branch_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS branches (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    parent_branch_id TEXT REFERENCES branches(id) ON DELETE SET NULL,
    fork_position INTEGER NOT NULL DEFAULT 0,
    label TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chord_selections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id TEXT NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    chord_name TEXT NOT NULL,
    chord_idx INTEGER NOT NULL,
    candidates_json TEXT NOT NULL DEFAULT '[]',
    selected_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_branches_session ON branches(session_id);
CREATE INDEX IF NOT EXISTS idx_selections_branch ON chord_selections(branch_id);
CREATE INDEX IF NOT EXISTS idx_selections_branch_pos
    ON chord_selections(branch_id, position);
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SessionManager:
    """Manages recommendation sessions, branches, and chord selections in SQLite."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        self._init_db()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.executescript(SCHEMA_SQL)

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    def create_session(self, style_group: dict[str, Any]) -> dict[str, Any]:
        """Create a new session with a root branch. Returns full session state."""
        session_id = uuid.uuid4().hex[:12]
        branch_id = uuid.uuid4().hex[:12]
        now = _now_iso()

        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO sessions
                   (id, style_genre_tag, style_decade, style_section,
                    style_file, style_root_file, style_starting_probs,
                    active_branch_id, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    session_id,
                    style_group["genre_tag"],
                    style_group["decade"],
                    style_group["section"],
                    style_group["file"],
                    style_group.get("root_file", ""),
                    json.dumps(style_group.get("starting_probs", {})),
                    branch_id,
                    now,
                    now,
                ),
            )
            conn.execute(
                """INSERT INTO branches (id, session_id, parent_branch_id,
                       fork_position, label, created_at)
                   VALUES (?, ?, NULL, 0, ?, ?)""",
                (branch_id, session_id, "main", now),
            )
            conn.commit()

        return self.get_session(session_id)

    def get_session(self, session_id: str) -> dict[str, Any]:
        """Get full session state with all branches and their chord sequences."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            if not row:
                raise KeyError(f"Session not found: {session_id}")

            session = dict(row)
            session["style_starting_probs"] = json.loads(
                session["style_starting_probs"]
            )

            # Branches
            branches = conn.execute(
                "SELECT * FROM branches WHERE session_id = ? ORDER BY created_at",
                (session_id,),
            ).fetchall()

            session["branches"] = []
            for br in branches:
                branch = dict(br)
                selections = conn.execute(
                    """SELECT * FROM chord_selections
                       WHERE branch_id = ? ORDER BY position""",
                    (br["id"],),
                ).fetchall()
                branch["chords"] = [
                    {
                        "position": s["position"],
                        "chord_name": s["chord_name"],
                        "chord_idx": s["chord_idx"],
                        "candidates": json.loads(s["candidates_json"]),
                        "selected_at": s["selected_at"],
                    }
                    for s in selections
                ]
                session["branches"].append(branch)

            session["active_branch_id"] = session.pop("active_branch_id")
            return session

    def list_sessions(
        self, limit: int = 20, offset: int = 0
    ) -> list[dict[str, Any]]:
        """List sessions with brief summaries."""
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT s.*, b.label as active_branch_label
                   FROM sessions s
                   LEFT JOIN branches b ON b.id = s.active_branch_id
                   ORDER BY s.updated_at DESC
                   LIMIT ? OFFSET ?""",
                (limit, offset),
            ).fetchall()
            return [dict(r) for r in rows]

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and its branches/selections (CASCADE)."""
        with self._get_conn() as conn:
            cur = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            conn.commit()
            return cur.rowcount > 0

    def _update_ts(self, conn: sqlite3.Connection, session_id: str) -> None:
        conn.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (_now_iso(), session_id),
        )

    # ------------------------------------------------------------------
    # Branches
    # ------------------------------------------------------------------

    def create_branch(
        self, session_id: str, fork_position: int, label: str = ""
    ) -> dict[str, Any]:
        """Fork a new branch from the active branch at fork_position.

        The new branch inherits chord selections at positions <= fork_position
        from the active branch and becomes the new active branch.
        """
        branch_id = uuid.uuid4().hex[:12]
        now = _now_iso()

        with self._get_conn() as conn:
            session = conn.execute(
                "SELECT active_branch_id FROM sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
            if not session:
                raise KeyError(f"Session not found: {session_id}")

            parent_id = session["active_branch_id"]

            # Create the branch
            conn.execute(
                """INSERT INTO branches (id, session_id, parent_branch_id,
                       fork_position, label, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (branch_id, session_id, parent_id, fork_position, label, now),
            )

            # Inherit chord selections up to fork_position
            conn.execute(
                """INSERT INTO chord_selections
                       (branch_id, position, chord_name, chord_idx,
                        candidates_json, selected_at)
                   SELECT ?, position, chord_name, chord_idx,
                          candidates_json, selected_at
                   FROM chord_selections
                   WHERE branch_id = ? AND position <= ?""",
                (branch_id, parent_id, fork_position),
            )

            # Set as active
            conn.execute(
                "UPDATE sessions SET active_branch_id = ?, updated_at = ? WHERE id = ?",
                (branch_id, now, session_id),
            )
            conn.commit()
            return self.get_session(session_id)

    def switch_branch(self, session_id: str, branch_id: str) -> dict[str, Any]:
        """Switch the active branch for a session."""
        with self._get_conn() as conn:
            # Verify branch belongs to this session
            br = conn.execute(
                "SELECT id FROM branches WHERE id = ? AND session_id = ?",
                (branch_id, session_id),
            ).fetchone()
            if not br:
                raise KeyError(f"Branch {branch_id} not in session {session_id}")

            conn.execute(
                "UPDATE sessions SET active_branch_id = ?, updated_at = ? WHERE id = ?",
                (branch_id, _now_iso(), session_id),
            )
            conn.commit()
            return self.get_session(session_id)

    def rename_branch(
        self, session_id: str, branch_id: str, label: str
    ) -> dict[str, Any]:
        """Rename a branch."""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE branches SET label = ? WHERE id = ? AND session_id = ?",
                (label, branch_id, session_id),
            )
            self._update_ts(conn, session_id)
            conn.commit()
            return self.get_session(session_id)

    def delete_branch(self, session_id: str, branch_id: str) -> dict[str, Any]:
        """Delete a branch. Refuses if it is the last branch in the session."""
        with self._get_conn() as conn:
            count = conn.execute(
                "SELECT COUNT(*) as c FROM branches WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            if count["c"] <= 1:
                raise ValueError("Cannot delete the last branch in a session")

            # Get current active
            active = conn.execute(
                "SELECT active_branch_id FROM sessions WHERE id = ?",
                (session_id,),
            ).fetchone()

            conn.execute(
                "DELETE FROM branches WHERE id = ? AND session_id = ?",
                (branch_id, session_id),
            )

            # If we deleted the active branch, switch to the first remaining
            if active and active["active_branch_id"] == branch_id:
                new_active = conn.execute(
                    "SELECT id FROM branches WHERE session_id = ? ORDER BY created_at LIMIT 1",
                    (session_id,),
                ).fetchone()
                if new_active:
                    conn.execute(
                        "UPDATE sessions SET active_branch_id = ? WHERE id = ?",
                        (new_active["id"], session_id),
                    )

            self._update_ts(conn, session_id)
            conn.commit()
            return self.get_session(session_id)

    # ------------------------------------------------------------------
    # Chord selections
    # ------------------------------------------------------------------

    def select_chord(
        self,
        session_id: str,
        branch_id: str,
        chord_idx: int,
        chord_name: str,
        candidates: list[dict[str, Any]],
    ) -> dict[str, str]:
        """Record a chord selection at the next position in the branch."""
        now = _now_iso()
        with self._get_conn() as conn:
            # Determine next position
            max_pos = conn.execute(
                "SELECT MAX(position) as mp FROM chord_selections WHERE branch_id = ?",
                (branch_id,),
            ).fetchone()
            next_pos = (max_pos["mp"] or 0) + 1

            conn.execute(
                """INSERT INTO chord_selections
                       (branch_id, position, chord_name, chord_idx,
                        candidates_json, selected_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    branch_id,
                    next_pos,
                    chord_name,
                    chord_idx,
                    json.dumps(candidates),
                    now,
                ),
            )
            self._update_ts(conn, session_id)
            conn.commit()
            return {"position": str(next_pos), "chord_name": chord_name, "chord_idx": str(chord_idx)}

    def undo_chord(self, session_id: str, branch_id: str) -> dict[str, Any] | None:
        """Remove the last chord selection from a branch. Returns the undone chord or None."""
        with self._get_conn() as conn:
            last = conn.execute(
                """SELECT id, position, chord_name, chord_idx
                   FROM chord_selections
                   WHERE branch_id = ?
                   ORDER BY position DESC LIMIT 1""",
                (branch_id,),
            ).fetchone()
            if not last:
                return None

            conn.execute("DELETE FROM chord_selections WHERE id = ?", (last["id"],))
            self._update_ts(conn, session_id)
            conn.commit()
            return {
                "position": last["position"],
                "chord_name": last["chord_name"],
                "chord_idx": last["chord_idx"],
            }
