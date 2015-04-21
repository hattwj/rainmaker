from sqlalchemy import func
from sqlalchemy.sql import text, update
from rainmaker.db.main import SyncFile, HostFile, SyncPart, HostPart

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

q_match_sync = """
    SELECT 
        t1.id,
        t2.id AS cmp_id, 
        t2.version AS cmp_ver
    FROM host_files t1
    LEFT JOIN sync_files t2
        ON t1.rel_path = t2.rel_path
        AND t1.file_hash = t2.file_hash 
        AND t1.is_dir = t2.is_dir
        AND t1.file_size = t2.file_size
    WHERE t2.id IS NOT NULL
        AND t1.host_id = :t1_id
        AND t1.cmp_id IS NULL
        AND t2.sync_id = :t2_id
"""

def sync_match(session, sync_id, host_id):
    ''' Match host files to sync files that are the same '''
    engine = session.get_bind()
    conn = engine.connect()
    with conn.begin():
        host_files = engine.execute(q_match_sync, t2_id=sync_id, t1_id=host_id)
        for hid, cmp_id, cmp_ver in host_files:
            u = update(HostFile).where(HostFile.id==hid).values(cmp_id=cmp_id, cmp_ver=cmp_ver)
            conn.execute(u)


def find_last_changed(session, sync_id, host_id):
    sp = session.query(func.max(SyncPart.updated_at)).filter(
        SyncFile.sync_id == sync_id).scalar()
    sp = sp if sp else 0
    sf = session.query(func.max(SyncFile.updated_at)).filter(
        SyncFile.sync_id == sync_id).scalar()
    sp = sf if sf and sf > sp else sp

    hp = session.query(func.max(HostPart.updated_at)).filter(
            HostFile.host_id == host_id).scalar()
    hp = hp if hp else 0
    hf = session.query(func.max(HostFile.updated_at)).filter(
            HostFile.host_id == host_id).scalar()
    hp = hf if hf and hf > hp else hp
    return (sp, hp)
