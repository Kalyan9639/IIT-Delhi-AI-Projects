"""
Database module for HireForge Pro - SQLite with user isolation.
Uses a single database with user_id isolation across all tables.
"""

import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime
import hashlib
import os
import secrets


DATABASE_FILE = "hireforge_users.db"


def get_db_connection():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database():
    """Initialize the database with required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table - stores user authentication and profile info
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            google_id TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            given_name TEXT,
            family_name TEXT,
            picture TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Jobs table - stores job postings created by users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            company_name TEXT NOT NULL,
            location TEXT,
            job_type TEXT,
            salary_range TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Candidates table - stores candidate information
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            resume_filename TEXT,
            resume_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
        )
    ''')

    # Candidate_status table - tracks candidate progress through hiring stages
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidate_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'new',
            notes TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
        )
    ''')

    # Saved_searches table - for future feature
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            search_query TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()


# ============= User Functions =============

def create_user(google_id: str, email: str, name: str,
                given_name: Optional[str] = None,
                family_name: Optional[str] = None,
                picture: Optional[str] = None) -> int:
    """Create a new user. Returns user ID."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO users (google_id, email, name, given_name, family_name, picture)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (google_id, email, name, given_name, family_name, picture))

    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id


def get_user_by_google_id(google_id: str) -> Optional[Dict[str, Any]]:
    """Get user by Google ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE google_id = ?', (google_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# ============= Job Functions =============

def create_job(user_id: int, title: str, description: str,
               company_name: str, location: Optional[str] = None,
               job_type: Optional[str] = None,
               salary_range: Optional[str] = None) -> int:
    """Create a new job posting. Returns job ID."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO jobs (user_id, title, description, company_name, location, job_type, salary_range)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, title, description, company_name, location, job_type, salary_range))

    job_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return job_id


def get_job_by_id(job_id: int) -> Optional[Dict[str, Any]]:
    """Get a job by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_jobs_by_user(user_id: int) -> List[Dict[str, Any]]:
    """Get all jobs created by a user, ordered by created_at descending."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM jobs
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_job(job_id: int, **kwargs) -> bool:
    """Update job fields. Returns True if updated."""
    if not kwargs:
        return False

    conn = get_db_connection()
    cursor = conn.cursor()

    # Build dynamic update query
    fields = []
    values = []
    for key, value in kwargs.items():
        if key in ['title', 'description', 'company_name', 'location', 'job_type', 'salary_range']:
            fields.append(f'{key} = ?')
            values.append(value)

    if not fields:
        conn.close()
        return False

    values.append(job_id)

    cursor.execute(f'''
        UPDATE jobs
        SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', values)

    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def delete_job(job_id: int) -> bool:
    """Delete a job. Returns True if deleted."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM jobs WHERE id = ?', (job_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


# ============= Candidate Functions =============

def create_candidate(user_id: int, job_id: int, full_name: str,
                     email: str, phone: Optional[str] = None,
                     resume_filename: Optional[str] = None,
                     resume_text: Optional[str] = None) -> int:
    """Create a new candidate. Returns candidate ID."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO candidates (user_id, job_id, full_name, email, phone, resume_filename, resume_text)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, job_id, full_name, email, phone, resume_filename, resume_text))

    candidate_id = cursor.lastrowid
    conn.commit()

    # Create initial status record
    cursor.execute('''
        INSERT INTO candidate_status (candidate_id, status)
        VALUES (?, 'new')
    ''', (candidate_id,))

    conn.commit()
    conn.close()
    return candidate_id


def get_candidate_by_id(candidate_id: int) -> Optional[Dict[str, Any]]:
    """Get a candidate by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.*, js.title as job_title, u.name as recruiter_name
        FROM candidates c
        LEFT JOIN jobs js ON c.job_id = js.id
        LEFT JOIN users u ON c.user_id = u.id
        WHERE c.id = ?
    ''', (candidate_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_candidates_by_job(user_id: int, job_id: int) -> List[Dict[str, Any]]:
    """Get all candidates for a specific job (recruiter's job)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.*, cs.status as current_status, cs.notes as status_notes
        FROM candidates c
        LEFT JOIN candidate_status cs ON c.id = cs.candidate_id
        WHERE c.user_id = ? AND c.job_id = ?
        ORDER BY cs.updated_at DESC
    ''', (user_id, job_id))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_candidates_by_user(user_id: int) -> List[Dict[str, Any]]:
    """Get all candidates created by a user (across all jobs)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.*, js.title as job_title, cs.status as current_status, cs.notes as status_notes
        FROM candidates c
        LEFT JOIN jobs js ON c.job_id = js.id
        LEFT JOIN candidate_status cs ON c.id = cs.candidate_id
        WHERE c.user_id = ?
        ORDER BY c.created_at DESC
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ============= Status Functions =============

def update_candidate_status(candidate_id: int, status: str,
                            notes: Optional[str] = None) -> bool:
    """Update candidate status and add optional notes."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get current status
    cursor.execute('SELECT id, status FROM candidate_status WHERE candidate_id = ?', (candidate_id,))
    existing = cursor.fetchone()

    if existing:
        # Update existing status
        cursor.execute('''
            UPDATE candidate_status
            SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE candidate_id = ?
        ''', (status, notes, candidate_id))
    else:
        # Create new status
        cursor.execute('''
            INSERT INTO candidate_status (candidate_id, status, notes)
            VALUES (?, ?, ?)
        ''', (candidate_id, status, notes))

    conn.commit()
    conn.close()
    return True


def get_candidate_status(candidate_id: int) -> Optional[Dict[str, Any]]:
    """Get current status for a candidate."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM candidate_status
        WHERE candidate_id = ?
        ORDER BY updated_at DESC
        LIMIT 1
    ''', (candidate_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None
