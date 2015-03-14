from sqlalchemy.sql import text
from rainmaker.db.main import SyncFile, HostFile

q_sync_diff = """
    SELECT t1.*
    FROM %(t1)s_files t1
    LEFT JOIN %(t2)s_files t2
        ON t1.rel_path = t2.rel_path
        AND t1.file_hash = t2.file_hash 
        AND t1.is_dir = t2.is_dir
        AND t1.file_size = t2.file_size
        AND t2.%(t2)s_id = :t2_id
    WHERE t2.id IS NULL
        AND t1.%(t1)s_id = :t1_id
"""

q_diff_sync = q_sync_diff % {'t1':'sync', 't2':'host'} 
q_diff_host = q_sync_diff % {'t1':'host', 't2':'sync'}


def sync_diff(session, sync_id, host_id):
    sync_files = session.query(SyncFile).from_statement(
        text(q_diff_sync)).\
        params(t1_id=sync_id, t2_id=host_id).all()
    host_files = session.query(HostFile).from_statement(
        text(q_diff_host)).\
        params(t2_id=sync_id, t1_id=host_id).all()
    return (sync_files, host_files)
