# sync_router.py
from fastapi import APIRouter, HTTPException, Depends
from models import SyncPushPayload, SyncPullPayload
from db import get_conn
import datetime
import uuid

router = APIRouter()

# push handler
@router.post("/sync/push")
def sync_push(payload: SyncPushPayload, current_user: dict = Depends(lambda: None)):
    device_id = payload.device_id
    table = payload.table
    items = payload.items or []
    conn = get_conn(); cur = conn.cursor()
    applied = {}
    for it in items:
        local_id = it.local_id
        data = it.data
        data['handled_by'] = current_user.get('username') if current_user else None
        created = data.get('created_at') or datetime.datetime.utcnow().isoformat()
        keys = list(data.keys())
        cols = ",".join(keys + ['created_at','remote_token'])
        placeholders = ",".join(['?'] * (len(keys) + 2))
        remote_token = str(uuid.uuid4())
        vals = [data[k] for k in keys] + [created, remote_token]
        try:
            cur.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", vals)
            rid = cur.lastrowid
            applied[str(local_id)] = rid
            # update partners counters if applicable
            if table == 'pan_records' and data.get('agent_code'):
                cur.execute("UPDATE d2na_partners SET pan_count = COALESCE(pan_count,0)+1, total_transactions = COALESCE(total_transactions,0)+1, last_update = ? WHERE partner_code = ?", (datetime.datetime.utcnow().isoformat(), data.get('agent_code')))
            if table == 'kotak_records' and data.get('agent_code'):
                cur.execute("UPDATE d2na_partners SET kotak_count = COALESCE(kotak_count,0)+1, total_transactions = COALESCE(total_transactions,0)+1, last_update = ? WHERE partner_code = ?", (datetime.datetime.utcnow().isoformat(), data.get('agent_code')))
        except Exception as e:
            print("push insert error", e)
    conn.commit(); conn.close()
    return {"applied": applied}

@router.post("/sync/pull")
def sync_pull(payload: SyncPullPayload, current_user: dict = Depends(lambda: None)):
    since = payload.since or '1970-01-01T00:00:00Z'
    conn = get_conn(); cur = conn.cursor()
    res = {}
    tables = ['d2na_army_logs', 'pan_records', 'kotak_records', 'd2na_partners']
    for t in tables:
        try:
            cur.execute(f"SELECT * FROM {t} WHERE created_at > ? ORDER BY created_at ASC", (since,))
            rows = cur.fetchall()
            out = []
            for r in rows:
                d = dict(r)
                remote_id = d.pop('id', None)
                out.append({'remote_id': remote_id, 'data': d})
            res[t] = out
        except Exception:
            res[t] = []
    conn.close()
    return res

