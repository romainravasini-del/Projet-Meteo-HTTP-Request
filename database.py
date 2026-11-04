"""Module de gestion de la base de données SQLite pour l'Observatoire Météo."""

import sqlite3
from typing import Any, Dict, List, Optional

DEFAULT_DB_PATH = "meteo.db"


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Crée et retourne une connexion SQLite avec support des clés étrangères et Row factory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Initialise la structure de la base de données (tables villes et releves)."""
    conn = get_connection(db_path)
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS villes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL UNIQUE,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS releves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ville_id INTEGER NOT NULL,
                temperature REAL NOT NULL,
                vitesse_vent REAL NOT NULL,
                date_heure TEXT NOT NULL,
                FOREIGN KEY (ville_id) REFERENCES villes (id) ON DELETE CASCADE
            );
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_releves_ville_id ON releves (ville_id);
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_releves_date_heure ON releves (date_heure);
        """)
    return conn


def insert_ville(conn: sqlite3.Connection, nom: str, latitude: float, longitude: float) -> int:
    """Insère une nouvelle ville ou retourne l'identifiant de la ville existante."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO villes (nom, latitude, longitude)
        VALUES (?, ?, ?)
        ON CONFLICT(nom) DO UPDATE SET
            latitude = excluded.latitude,
            longitude = excluded.longitude;
    """, (nom.strip(), float(latitude), float(longitude)))
    conn.commit()

    # Récupérer l'ID de la ville
    cursor.execute("SELECT id FROM villes WHERE nom = ?", (nom.strip(),))
    row = cursor.fetchone()
    return int(row["id"])


def get_villes(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Retourne la liste de toutes les villes enregistrées."""
    cursor = conn.cursor()
    cursor.execute("SELECT id, nom, latitude, longitude FROM villes ORDER BY nom ASC;")
    return [dict(row) for row in cursor.fetchall()]


def get_ville_by_id(conn: sqlite3.Connection, ville_id: int) -> Optional[Dict[str, Any]]:
    """Récupère une ville par son identifiant."""
    cursor = conn.cursor()
    cursor.execute("SELECT id, nom, latitude, longitude FROM villes WHERE id = ?;", (ville_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def get_ville_by_nom(conn: sqlite3.Connection, nom: str) -> Optional[Dict[str, Any]]:
    """Récupère une ville par son nom."""
    cursor = conn.cursor()
    cursor.execute("SELECT id, nom, latitude, longitude FROM villes WHERE LOWER(nom) = LOWER(?);", (nom.strip(),))
    row = cursor.fetchone()
    return dict(row) if row else None


def insert_releve(
    conn: sqlite3.Connection,
    ville_id: int,
    temperature: float,
    vitesse_vent: float,
    date_heure: str,
) -> int:
    """Insère un relevé météorologique associé à une ville."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO releves (ville_id, temperature, vitesse_vent, date_heure)
        VALUES (?, ?, ?, ?);
    """, (ville_id, float(temperature), float(vitesse_vent), date_heure))
    conn.commit()
    return cursor.lastrowid


def get_releves_by_ville(
    conn: sqlite3.Connection,
    ville_id: int,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Récupère les relevés récents pour une ville donnée."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, ville_id, temperature, vitesse_vent, date_heure
        FROM releves
        WHERE ville_id = ?
        ORDER BY date_heure DESC, id DESC
        LIMIT ?;
    """, (ville_id, limit))
    return [dict(row) for row in cursor.fetchall()]


def get_dernier_releve(conn: sqlite3.Connection, ville_id: int) -> Optional[Dict[str, Any]]:
    """Récupère le relevé le plus récent pour une ville."""
    releves = get_releves_by_ville(conn, ville_id, limit=1)
    return releves[0] if releves else None


def get_statistiques_ville(conn: sqlite3.Connection, ville_id: int) -> Optional[Dict[str, Any]]:
    """Calcule des statistiques agrégées pour une ville (moyenne, min, max)."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COUNT(r.id) AS total_releves,
            ROUND(AVG(r.temperature), 2) AS temperature_moyenne,
            MIN(r.temperature) AS temperature_min,
            MAX(r.temperature) AS temperature_max,
            ROUND(AVG(r.vitesse_vent), 2) AS vent_moyen,
            MAX(r.vitesse_vent) AS vent_max
        FROM releves r
        WHERE r.ville_id = ?;
    """, (ville_id,))
    row = cursor.fetchone()
    if not row or row["total_releves"] == 0:
        return None
    return dict(row)


def get_statistiques_globales(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Retourne des statistiques globales sur l'ensemble de la base."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COUNT(DISTINCT v.id) AS total_villes,
            COUNT(r.id) AS total_releves,
            ROUND(AVG(r.temperature), 2) AS temperature_moyenne,
            MIN(r.temperature) AS temperature_min,
            MAX(r.temperature) AS temperature_max,
            ROUND(AVG(r.vitesse_vent), 2) AS vent_moyen,
            MAX(r.vitesse_vent) AS vent_max
        FROM villes v
        LEFT JOIN releves r ON v.id = r.ville_id;
    """)
    stats = dict(cursor.fetchone())

    # Relevé le plus chaud
    cursor.execute("""
        SELECT v.nom AS ville, r.temperature, r.date_heure
        FROM releves r
        JOIN villes v ON r.ville_id = v.id
        ORDER BY r.temperature DESC
        LIMIT 1;
    """)
    stats["releve_plus_chaud"] = dict(cursor.fetchone()) if stats["total_releves"] > 0 else None

    # Relevé le plus froid
    cursor.execute("""
        SELECT v.nom AS ville, r.temperature, r.date_heure
        FROM releves r
        JOIN villes v ON r.ville_id = v.id
        ORDER BY r.temperature ASC
        LIMIT 1;
    """)
    stats["releve_plus_froid"] = dict(cursor.fetchone()) if stats["total_releves"] > 0 else None

    # Relevé le plus venteux
    cursor.execute("""
        SELECT v.nom AS ville, r.vitesse_vent, r.date_heure
        FROM releves r
        JOIN villes v ON r.ville_id = v.id
        ORDER BY r.vitesse_vent DESC
        LIMIT 1;
    """)
    stats["releve_plus_venteux"] = dict(cursor.fetchone()) if stats["total_releves"] > 0 else None

    return stats

