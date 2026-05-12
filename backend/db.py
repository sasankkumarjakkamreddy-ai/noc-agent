import sqlite3
import json
from datetime import datetime
from models import AuditEntry

DB_PATH = "noc_audit.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            observe_output TEXT,
            hypothesis TEXT,
            validation_result TEXT,
            remediation TEXT,
            approved INTEGER,
            approved_by TEXT,
            outcome TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_audit(entry: AuditEntry):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO audit_log 
        (incident_id, timestamp, observe_output, hypothesis, 
         validation_result, remediation, approved, approved_by, outcome)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        entry.incident_id,
        entry.timestamp.isoformat(),
        entry.observe_output,
        json.dumps(entry.hypothesis.model_dump()),
        entry.validation_result,
        json.dumps(entry.remediation.model_dump()),
        entry.approved,
        entry.approved_by,
        entry.outcome
    ))
    conn.commit()
    conn.close()

def get_audit(incident_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM audit_log WHERE incident_id = ? ORDER BY created_at DESC',
        (incident_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_audits():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM audit_log ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_approval(incident_id: str, approved: bool, approved_by: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE audit_log 
        SET approved = ?, approved_by = ?
        WHERE incident_id = ?
    ''', (1 if approved else 0, approved_by, incident_id))
    conn.commit()
    conn.close()
