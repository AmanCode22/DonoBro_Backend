import sqlite3
import os
from dotenv import load_dotenv
from flask import g,current_app
import click

load_dotenv()

def init_db():
    conn=get_db()
    with current_app.open_resource("schema.sql","r") as f:
        schema_commands=f.read()
    cursor = conn.cursor()
    cursor.executescript(schema_commands)
    conn.commit()
    conn.close()

def get_db():
    if 'db' not in g:
        g.db=sqlite3.connect(os.getenv("DATABASE_URL"),detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db=g.pop("db",None)
    if db is not None:
        db.close()

@click.command('init-db')
def init_db_command():
    if os.path.exists(os.getenv("DATABASE_URL")):
        os.remove(os.getenv("DATABASE_URL"))
    init_db()
    click.echo('Initialized the database.')