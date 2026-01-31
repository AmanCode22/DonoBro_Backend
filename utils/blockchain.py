import hashlib,json,time,os,sys 
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from database import get_db

def calculate_hash(previous_hash,action_type,data_payload,timestamp):
    merged_encoded=(previous_hash+action_type+data_payload+timestamp).encode("utf-8")
    return hashlib.sha256(merged_encoded).hexdigest()

def create_block(action_type, data_dict):
    db=get_db()
    cursor=db.cursor()
    cursor.execute("SELECT block_hash FROM Ledger ORDER BY block_id DESC LIMIT 1;")
    previous_hash=cursor.fetchone()
    if previous_hash:
        previous_hash=previous_hash["block_hash"]
    else:
        previous_hash="0"*64
    timestamp = str(time.time())
    payload = json.dumps(data_dict, sort_keys=True)
    current_hash = calculate_hash(previous_hash, action_type, payload, timestamp)
    cursor.execute("INSERT INTO Ledger (previous_hash, action_type, data_payload, action_timestamp, block_hash) VALUES (?,?,?,?,?)",(previous_hash,action_type,payload,timestamp,current_hash))
    db.commit()
    cursor.close()
    