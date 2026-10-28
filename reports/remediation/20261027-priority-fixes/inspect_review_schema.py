import json
import sqlite3
import sys
from pathlib import Path

database = Path(sys.argv[1]).resolve()
uri = database.as_uri() + "?mode=ro"
with sqlite3.connect(uri, uri=True) as connection:
    connection.execute("PRAGMA query_only = ON")
    columns = connection.execute("PRAGMA table_info(sop_review_events)").fetchall()
    table = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='sop_review_events'"
    ).fetchone()
    print(json.dumps({
        "database": str(database),
        "table_sql": table[0] if table else None,
        "columns": [
            {"position": row[0], "name": row[1], "type": row[2], "not_null": bool(row[3]),
             "default": row[4], "primary_key": bool(row[5])}
            for row in columns
        ],
    }, indent=2))
