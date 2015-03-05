from sqlalchemy.sql import text
from rainmaker.db.main import SyncFile, HostFile

q_sync_diff = """
    SELECT m1.*
    FROM %(t1)s_files m1
    LEFT JOIN %(t2)s_files m2
        ON m1.rel_path = m2.rel_path
        AND m1.file_hash = m2.file_hash 
        AND m1.is_dir = m2.is_dir
        AND m1.file_size = m2.file_size
        AND m1.next_id IS NULL
        AND m2.%(t2)s_id = :t2_id
        AND m2.next_id IS NULL
    WHERE m2.id IS NULL
        AND m1.next_id IS NULL
        AND m1.%(t1)s_id = :t1_id
"""

def sync_diff(session, sync_id, host_id):
    sync_files = session.query(SyncFile).from_statement(
        text(q_sync_diff % {'t1':'sync', 't2':'host'} )).\
        params(t1_id=sync_id, t2_id=host_id).all()
    host_files = session.query(HostFile).from_statement(
        text(q_sync_diff % {'t1':'host', 't2':'sync'} )).\
        params(t2_id=sync_id, t1_id=host_id).all()
    return (sync_files, host_files)
