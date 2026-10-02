"""Read-only database evidence for the presentation; never exports profile rows."""
import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import mysql.connector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'frontend/src/presentation/evidence.json'


def main():
    conn = mysql.connector.connect(host=os.getenv('DB_HOST', '127.0.0.1'),
        user=os.getenv('DB_USER', 'root'), password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'steamscope'))
    cur = conn.cursor(dictionary=True)
    cur.execute('SET TRANSACTION READ ONLY')
    cur.execute('START TRANSACTION WITH CONSISTENT SNAPSHOT')
    def query(sql, params=()):
        cur.execute(sql, params)
        return cur.fetchall()
    tables = query('SELECT TABLE_NAME AS name FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_TYPE="BASE TABLE" ORDER BY TABLE_NAME')
    for table in tables:
        name = table['name']
        table['count'] = query(f'SELECT COUNT(*) AS n FROM `{name}`')[0]['n']
        table['columns'] = query('''SELECT COLUMN_NAME AS name,COLUMN_TYPE AS type,
            IS_NULLABLE AS nullable,COLUMN_KEY AS `key` FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s ORDER BY ORDINAL_POSITION''', (name,))
        table['ddl'] = query(f'SHOW CREATE TABLE `{name}`')[0]['Create Table']
    fks = query('''SELECT k.TABLE_NAME AS child,k.COLUMN_NAME AS child_key,
        k.REFERENCED_TABLE_NAME AS parent,k.REFERENCED_COLUMN_NAME AS parent_key,
        k.CONSTRAINT_NAME AS name,r.DELETE_RULE AS delete_rule
        FROM information_schema.KEY_COLUMN_USAGE k
        JOIN information_schema.REFERENTIAL_CONSTRAINTS r
        ON r.CONSTRAINT_SCHEMA=k.CONSTRAINT_SCHEMA AND r.CONSTRAINT_NAME=k.CONSTRAINT_NAME
        WHERE k.TABLE_SCHEMA=DATABASE() AND k.REFERENCED_TABLE_NAME IS NOT NULL
        ORDER BY k.TABLE_NAME,k.ORDINAL_POSITION''')
    for fk in fks:
        fk['orphans'] = query(f'''SELECT COUNT(*) AS n FROM `{fk['child']}` c
            LEFT JOIN `{fk['parent']}` p ON p.`{fk['parent_key']}`=c.`{fk['child_key']}`
            WHERE c.`{fk['child_key']}` IS NOT NULL AND p.`{fk['parent_key']}` IS NULL''')[0]['n']
    quality = query('''SELECT COUNT(*) AS games,COUNT(DISTINCT app_id) AS unique_ids,
        SUM(name IS NULL OR TRIM(name)='') AS missing_names,
        SUM(price IS NULL) AS unknown_prices,SUM(release_date IS NULL) AS unknown_dates
        FROM game''')[0]
    sql = '''SELECT g.name, COUNT(*) AS owners
FROM `library` l
JOIN game g ON g.app_id = l.app_id
GROUP BY g.app_id, g.name
ORDER BY owners DESC, g.app_id
LIMIT 5;'''
    ranking = query(sql)
    genre_sql = '''SELECT gr.name AS genre, COUNT(*) AS games
FROM genre gr
JOIN game_genre gg ON gg.genre_id = gr.genre_id
GROUP BY gr.genre_id, gr.name
ORDER BY games DESC, gr.name
LIMIT 5;'''
    genre_result = query(genre_sql)
    result = dict(captured_at=datetime.now(ZoneInfo('Asia/Kolkata')).isoformat(),
        tables=tables, foreign_keys=fks, quality=quality,
        query_examples=[dict(title='Which games are most owned?',sql=sql,rows=ranking),
                        dict(title='Which genres have the most games?',sql=genre_sql,rows=genre_result)])
    conn.rollback()
    cur.close()
    conn.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, default=str) + '\n')
    print(json.dumps(dict(tables=len(tables), foreign_keys=len(fks),
        orphan_rows=sum(f['orphans'] for f in fks), quality=quality,
        counts={t['name']: t['count'] for t in tables}), indent=2, default=str))


if __name__ == '__main__':
    main()
