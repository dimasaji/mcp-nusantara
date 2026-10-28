"""Existing backup entrypoints must produce independently restorable SQLite files."""
import importlib
import shutil
import sqlite3
from pathlib import Path

import pytest


@pytest.mark.parametrize('module_name', [
    'app.knowledge.production_kb',
    'app.knowledge.production_embedding_bridge',
    'app.knowledge.official_knowledge_ingestion',
])
def test_backup_restores_all_committed_wal_transactions(tmp_path, monkeypatch, module_name):
    module = importlib.import_module(module_name)
    root = Path(__file__).resolve().parents[1]
    for name,value in vars(module).copy().items():
        if isinstance(value,Path) and value.is_relative_to(root/'data'):
            monkeypatch.setattr(module,name,tmp_path/'metadata'/value.relative_to(root/'data'))
    source = tmp_path/'live.db'
    monkeypatch.setattr(module,'DB_PATH',source,raising=False)
    monkeypatch.setattr(module,'KB_ROOT',tmp_path/'kb',raising=False)
    monkeypatch.setattr(module,'BACKUP_ROOT',tmp_path/'backups',raising=False)
    (tmp_path/'kb').mkdir()
    connection = sqlite3.connect(source)
    try:
        connection.execute('PRAGMA journal_mode=WAL')
        connection.execute('PRAGMA wal_autocheckpoint=0')
        connection.execute('CREATE TABLE proof (value TEXT)')
        connection.commit()
        connection.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        connection.execute("INSERT INTO proof VALUES ('committed after checkpoint')")
        connection.commit()
        backup = module.backup_database(source) if module_name.endswith('official_knowledge_ingestion') else module.backup_database()
        restored = tmp_path/'restored.db'
        shutil.copy2(backup,restored)
        with sqlite3.connect(restored) as database:
            assert database.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            assert database.execute('SELECT value FROM proof').fetchall()==[('committed after checkpoint',)]
        assert connection.execute('SELECT COUNT(*) FROM proof').fetchone()[0]==1
    finally:
        connection.close()
