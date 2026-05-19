"""SQLite database for persisting anonymization sessions, comments, and inference data."""
import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "anonymization.db")


def get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            persona_json TEXT DEFAULT '{}',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            index_num INTEGER NOT NULL,
            original_text TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            risk_score REAL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS anonymization_rounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comment_id INTEGER NOT NULL REFERENCES comments(id) ON DELETE CASCADE,
            round_num INTEGER NOT NULL,
            anonymized_text TEXT NOT NULL,
            max_confidence REAL DEFAULT 0,
            privacy_protection REAL,
            utility_preservation REAL,
            text_quality REAL,
            inference_blocking REAL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS attacker_inferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            round_id INTEGER NOT NULL REFERENCES anonymization_rounds(id) ON DELETE CASCADE,
            attribute TEXT NOT NULL,
            inference_text TEXT,
            guesses_json TEXT DEFAULT '[]',
            confidence INTEGER DEFAULT 1,
            blocked INTEGER DEFAULT 0,
            ground_truth TEXT
        );

        CREATE TABLE IF NOT EXISTS reasoning_chains (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            round_id INTEGER NOT NULL REFERENCES anonymization_rounds(id) ON DELETE CASCADE,
            attribute TEXT NOT NULL,
            target_guess TEXT,
            blocked INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS chain_nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chain_id INTEGER NOT NULL REFERENCES reasoning_chains(id) ON DELETE CASCADE,
            node_index INTEGER NOT NULL,
            node_type TEXT NOT NULL,
            text TEXT NOT NULL,
            evidence TEXT,
            confidence INTEGER
        );
    """)
    conn.commit()
    conn.close()


# ---- SAVE ----

def save_session(session_id: str, persona: Dict[str, str] = None) -> None:
    conn = get_conn()
    persona_json = json.dumps(persona or {}, ensure_ascii=False)
    conn.execute(
        "INSERT OR REPLACE INTO sessions (id, persona_json, updated_at) VALUES (?, ?, datetime('now'))",
        (session_id, persona_json)
    )
    conn.commit()
    conn.close()


def save_comment(session_id: str, index_num: int, original_text: str,
                 status: str = 'pending', risk_score: float = 0) -> int:
    conn = get_conn()
    c = conn.execute(
        "INSERT INTO comments (session_id, index_num, original_text, status, risk_score) VALUES (?,?,?,?,?)",
        (session_id, index_num, original_text, status, risk_score)
    )
    conn.commit()
    cid = c.lastrowid
    conn.close()
    return cid


def save_round(comment_id: int, round_num: int, anonymized_text: str,
               max_confidence: float = 0, quality: Dict = None) -> int:
    conn = get_conn()
    q = quality or {}
    c = conn.execute(
        """INSERT INTO anonymization_rounds
           (comment_id, round_num, anonymized_text, max_confidence,
            privacy_protection, utility_preservation, text_quality, inference_blocking)
           VALUES (?,?,?,?,?,?,?,?)""",
        (comment_id, round_num, anonymized_text, max_confidence,
         q.get("privacy_protection"), q.get("utility_preservation"),
         q.get("text_quality"), q.get("inference_blocking"))
    )
    conn.commit()
    rid = c.lastrowid
    conn.close()
    return rid


def save_inference(round_id: int, attribute: str, inference_text: str,
                   guesses: List[str], confidence: int, blocked: bool,
                   ground_truth: str = None) -> int:
    conn = get_conn()
    c = conn.execute(
        """INSERT INTO attacker_inferences (round_id, attribute, inference_text, guesses_json, confidence, blocked, ground_truth)
           VALUES (?,?,?,?,?,?,?)""",
        (round_id, attribute, inference_text, json.dumps(guesses, ensure_ascii=False),
         confidence, 1 if blocked else 0, ground_truth)
    )
    conn.commit()
    iid = c.lastrowid
    conn.close()
    return iid


def save_chain_with_nodes(round_id: int, attribute: str, target_guess: str,
                          blocked: bool, nodes: List[Dict]) -> int:
    conn = get_conn()
    c = conn.execute(
        "INSERT INTO reasoning_chains (round_id, attribute, target_guess, blocked) VALUES (?,?,?,?)",
        (round_id, attribute, target_guess, 1 if blocked else 0)
    )
    chain_id = c.lastrowid
    for i, node in enumerate(nodes):
        conn.execute(
            "INSERT INTO chain_nodes (chain_id, node_index, node_type, text, evidence, confidence) VALUES (?,?,?,?,?,?)",
            (chain_id, i, node.get("type", ""), node.get("text", ""),
             node.get("evidence"), node.get("confidence"))
        )
    conn.commit()
    conn.close()
    return chain_id


# ---- LOAD ----

def list_sessions() -> List[Dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT s.id, s.persona_json, s.created_at, s.updated_at, COUNT(c.id) as comment_count FROM sessions s LEFT JOIN comments c ON c.session_id = s.id GROUP BY s.id ORDER BY s.updated_at DESC"
    ).fetchall()
    conn.close()
    return [{"id": r["id"], "persona": json.loads(r["persona_json"] or "{}"),
             "created_at": r["created_at"], "updated_at": r["updated_at"],
             "comment_count": r["comment_count"]} for r in rows]


def load_session(session_id: str) -> Optional[Dict]:
    conn = get_conn()
    s = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if not s:
        conn.close()
        return None

    result = {
        "session_id": s["id"],
        "persona": json.loads(s["persona_json"] or "{}"),
        "created_at": s["created_at"],
        "comments": []
    }

    comments = conn.execute(
        "SELECT * FROM comments WHERE session_id = ? ORDER BY index_num", (session_id,)
    ).fetchall()

    for c in comments:
        comment_data = {
            "index": c["index_num"],
            "original_text": c["original_text"],
            "status": c["status"],
            "risk_score": c["risk_score"],
            "rounds": []
        }

        rounds = conn.execute(
            "SELECT * FROM anonymization_rounds WHERE comment_id = ? ORDER BY round_num", (c["id"],)
        ).fetchall()

        for r in rounds:
            round_data = {
                "round_num": r["round_num"],
                "anonymized_text": r["anonymized_text"],
                "max_confidence": r["max_confidence"],
                "quality": {
                    "privacy_protection": r["privacy_protection"],
                    "utility_preservation": r["utility_preservation"],
                    "text_quality": r["text_quality"],
                    "inference_blocking": r["inference_blocking"],
                },
                "inferences": [],
                "chains": []
            }

            inferences = conn.execute(
                "SELECT * FROM attacker_inferences WHERE round_id = ?", (r["id"],)
            ).fetchall()
            for inf in inferences:
                round_data["inferences"].append({
                    "attribute": inf["attribute"],
                    "inference_text": inf["inference_text"],
                    "guesses": json.loads(inf["guesses_json"] or "[]"),
                    "confidence": inf["confidence"],
                    "blocked": bool(inf["blocked"]),
                    "ground_truth": inf["ground_truth"],
                })

            chains = conn.execute(
                "SELECT * FROM reasoning_chains WHERE round_id = ?", (r["id"],)
            ).fetchall()
            for ch in chains:
                nodes = conn.execute(
                    "SELECT * FROM chain_nodes WHERE chain_id = ? ORDER BY node_index", (ch["id"],)
                ).fetchall()
                round_data["chains"].append({
                    "attribute": ch["attribute"],
                    "target_guess": ch["target_guess"],
                    "blocked": bool(ch["blocked"]),
                    "nodes": [
                        {"type": n["node_type"], "text": n["text"],
                         "evidence": n["evidence"], "confidence": n["confidence"]}
                        for n in nodes
                    ]
                })

            comment_data["rounds"].append(round_data)

        result["comments"].append(comment_data)

    conn.close()
    return result


def delete_session(session_id: str) -> bool:
    conn = get_conn()
    c = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    deleted = c.rowcount > 0
    conn.close()
    return deleted


# ---- Auto-save after anonymization ----

def auto_save_result(session_id: str, persona: Dict, comments_data: List[Dict]) -> None:
    """Save or update a complete session with all comments, rounds, and inferences."""
    save_session(session_id, persona)

    conn = get_conn()
    # Delete existing comments for this session to replace with updated data
    conn.execute("DELETE FROM comments WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()

    for c_data in comments_data:
        cid = save_comment(session_id, c_data["index"], c_data["original_text"],
                          c_data.get("status", "done"), c_data.get("risk_score", 0))
        for r_data in c_data.get("rounds", []):
            rid = save_round(cid, r_data["round_num"], r_data["anonymized_text"],
                            r_data.get("max_confidence", 0), r_data.get("quality"))
            for inf in r_data.get("inferences", []):
                save_inference(rid, inf["attribute"], inf.get("inference_text", ""),
                              inf.get("guesses", []), inf.get("confidence", 1),
                              inf.get("blocked", False), inf.get("ground_truth"))
            for ch in r_data.get("chains", []):
                save_chain_with_nodes(rid, ch["attribute"], ch.get("target_guess", ""),
                                     ch.get("blocked", False), ch.get("nodes", []))


# Initialize on import
init_db()
