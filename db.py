"""
Lightweight MySQL connection helper built on PyMySQL.

Why PyMySQL instead of Flask-MySQLdb?
- Pure Python, no C extension to compile -> much easier to install
  (`pip install pymysql` just works everywhere, including Windows).
- Drop-in DB-API 2.0 interface, so the rest of the code stays simple.
"""

import pymysql
import pymysql.cursors
from flask import g, current_app


def get_db():
    """Return a request-scoped MySQL connection (created once per request)."""
    if "db" not in g:
        g.db = pymysql.connect(
            host=current_app.config["MYSQL_HOST"],
            user=current_app.config["MYSQL_USER"],
            password=current_app.config["MYSQL_PASSWORD"],
            database=current_app.config["MYSQL_DB"],
            port=current_app.config["MYSQL_PORT"],
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
        )
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    """Register the teardown handler so connections close after each request."""
    app.teardown_appcontext(close_db)


def query(sql, params=None, fetchone=False, commit=False):
    """
    Small convenience wrapper so routes don't repeat cursor boilerplate.

    query("SELECT * FROM users WHERE email=%s", (email,), fetchone=True)
    query("INSERT INTO users (...) VALUES (...)", (...), commit=True)
    """
    db = get_db()
    with db.cursor() as cur:
        cur.execute(sql, params or ())
        if commit:
            db.commit()
            return cur.lastrowid
        return cur.fetchone() if fetchone else cur.fetchall()
