from flask import Blueprint, request,session
from database import get_db
from utils.notification import send_wake_up_signal,generate_stream_ticket
from utils.blockchain import create_block
import uuid,hashlib
from utils.helper import check_fields_api,generate_unique_device_id,generate_unique_anon_id,verify_user_sso_token,generate_unique_sso_token

bp = Blueprint("api_users_bp", __name__)

@bp.route("/register", methods=["POST"])
def register_api():
    providing_id=False
    json_data = request.get_json()
    fields_to_check = ["anon_id", "role", "blood_type", "sector_hash","password"]
    check=check_fields_api(fields_to_check,json_data)
    if check!=True:
        return check
    db = get_db()
    cursor=db.cursor()
    cursor.execute("SELECT 1 FROM Users WHERE anon_id= ?;",(json_data["anon_id"],))
    if not cursor.fetchone():
        providing_id=True
        json_data["anon_id"]=generate_unique_anon_id(db.cursor(),json_data["anon_id"].split("-")[0])
    device_id=generate_unique_device_id(db.cursor())
    cursor.execute(
        "INSERT INTO Users (anon_id, role, blood_type, sector_hash, device_id,auth_key) VALUES (?, ?, ?, ?, ?)",
        (json_data["anon_id"], json_data["role"], json_data["blood_type"], json_data["sector_hash"],device_id,hashlib.md5(json_data["password"].encode()).hexdigest())
    )
    sso_token=generate_unique_sso_token(db.cursor())
    cursor.execute("INSERT INTO auth_tokens_users (user_id,sso_token) VALUES (?,?)",(json_data["anon_id"],sso_token))
    db.commit()
    cursor.close()
    create_block("USER_REGISTERED",{"user_id":json_data["anon_id"]})
    create_block("CREATE_NEW_SSO_USER",{"anon_id":json_data["anon_id"],"sso_token":sso_token})
    if providing_id:
        return {"status":"success","device_id":device_id,"anon_id":json_data["anon_id"],"sso_token":sso_token}
    return {"status": "success","device_id":device_id,"anon_id":None,"sso_token":sso_token}

@bp.route("/login",methods=["POST"])
def login_api():
    json_data=request.get_json()
    fields_to_check=["user_id","password"]
    check=check_fields_api(fields_to_check,json_data)
    if check!=True:
        return check
    db=get_db()
    cursor=db.cursor()
    cursor.execute("SELECT auth_key FROM Users WHERE anon_id=?;",(json_data["user_id"],))
    auth_key_stored=cursor.fetchone()
    if not auth_key_stored:
        return {"status":"error","message":"Given anonymous id is not registered."}
    if auth_key_stored["auth_key"]!=hashlib.md5(json_data["password"].encode()).hexdigest():
        return {"status":"error","message":"Invalid password."}
    sso=generate_unique_sso_token(db.cursor())
    cursor.execute("INSERT OR REPLACE INTO auth_tokens_users (user_id, sso_token) VALUES (?, ?)", (json_data["user_id"], sso))
    create_block("RENEW_USER_SSO",{"anon_id":json_data["user_id"],"sso_token":sso})
    return {"status":"success","sso_token":sso}

@bp.route("/grid",methods=["POST"])
def grid_route():
    json_data=request.get_json()
    if not json_data.get("sso_token"):
        return {"status":"error","message":"Send sso_token for authentication."}
    if not json_data.get("user_id"):
        return {"status":"error","message":"Send user_id for authentication."}
    auth_verify=verify_user_sso_token(get_db(),json_data["sso_token"],json_data["user_id"])
    if not auth_verify:
        return {"status":"error","message":"SSO Token invalid!"}
    if auth_verify[1]!=json_data["sso_token"]:
        return {"status":"sso_update","sso_token":auth_verify[1]}
    sector_hash = json_data.get("sector_hash")
    if not sector_hash:
        return {"status": "error", "message": "Sector hash cannot be empty."}
    db = get_db()
    cursor = db.execute("SELECT anon_id, blood_type FROM Users WHERE sector_hash = ? AND role = 'Donor'", (sector_hash,))
    data = cursor.fetchall()
    return {"status": "success", "result": [dict(row) for row in data]}

@bp.route("/request", methods=["POST"])
def request_route():
    json_data = request.get_json()
    if not json_data.get("sso_token"):
        return {"status":"error","message":"Send sso_token for authentication."}
    if not json_data.get("user_id"):
        return {"status":"error","message":"Send user_id for authentication."}
    auth_verify=verify_user_sso_token(get_db(),json_data["sso_token"],json_data["user_id"])
    if not auth_verify:
        return {"status":"error","message":"SSO Token invalid!"}
    if auth_verify[1]!=json_data["sso_token"]:
        return {"status":"sso_update","sso_token":auth_verify[1]}
    fields_required = ["blood_type", "resource_type", "urgency"]
    check=check_fields_api(fields_required,json_data)
    if check!=True:
        return check
    db = get_db()
    request_id = str(uuid.uuid4())
    db.execute(
        "INSERT INTO Requests (request_id, patient_id, need, resource_type, urgency) VALUES (?, ?, ?, ?, ?)",
        (request_id, json_data["user_id"], json_data["blood_type"], json_data["resource_type"], json_data["urgency"])
    )
    db.commit()
    create_block("REQUEST_CREATED",{"request_id":request_id})
    patient_row = db.execute("SELECT sector_hash FROM Users WHERE anon_id = ?", (json_data["user_id"],)).fetchone()
    if patient_row:
        patient_sector = patient_row["sector_hash"]
        donors = db.execute("SELECT device_id FROM Users WHERE role = 'Donor' AND sector_hash = ? AND anon_id != ?", (patient_sector, json_data["user_id"])).fetchall()
        for i in donors:
            send_wake_up_signal(i["device_id"], "NEW_REQUEST", {"request_id": request_id, "blood": json_data["blood_type"], "resource": json_data["resource_type"], "level": json_data["urgency"]})
    return {"status": "success", "request_id": request_id}

@bp.route("/chat", methods=["POST"])
def chat_route():
    json_data = request.get_json()
    if not json_data.get("sso_token"):
        return {"status":"error","message":"Send sso_token for authentication."}
    if not json_data.get("user_id"):
        return {"status":"error","message":"Send user_id for authentication."}
    auth_verify=verify_user_sso_token(get_db(),json_data["sso_token"],json_data["user_id"])
    if not auth_verify:
        return {"status":"error","message":"SSO Token invalid!"}
    if auth_verify[1]!=json_data["sso_token"]:
        return {"status":"sso_update","sso_token":auth_verify[1]}
    fields_required = [ "recipient_id", "encrypted_message","encrypted_content_police"]
    check=check_fields_api(fields_required,json_data)
    if check!=True:
        return check
    db = get_db()
    message_id = str(uuid.uuid4())
    evidence_id=str(uuid.uuid4())
    db.execute(
        "INSERT INTO Inbox (message_id, sender_id, recipient_id, encrypted_content) VALUES (?, ?, ?, ?)",
        (message_id, json_data["user_id"], json_data["recipient_id"], json_data["encrypted_message"])
    )
    db.execute('INSERT INTO PoliceEvidence (evidence_id, related_message_id, sender_id, encrypted_packet_police) VALUES (?, ?, ?, ?)',(evidence_id,message_id,json_data["user_id"],json_data["encrypted_content_police"]))
    db.commit()
    recipient = db.execute("SELECT device_id FROM Users WHERE anon_id = ?", (json_data["recipient_id"],)).fetchone()
    if recipient:
        send_wake_up_signal(recipient["device_id"], "NEW_MESSAGE", {"sender_id": json_data["user_id"]})
    create_block("MSG_SENT",{"sender_id":json_data["user_id"],"recipient_id":json_data["recipient_id"],"msg_id":message_id})
    return {"status": "success"}

@bp.route("/logout",methods=["POST"])
def logout_api():
    json_data = request.get_json()
    if not json_data.get("sso_token"):
        return {"status":"error","message":"Send sso_token for authentication."}
    if not json_data.get("user_id"):
        return {"status":"error","message":"Send user_id for authentication."}
    db=get_db()
    cursor=db.cursor()
    cursor.execute("SELECT sso_token FROM auth_tokens_users WHERE user_id=?;",(json_data["user_id"],))
    original_sso=cursor.fetchone()
    if not original_sso:
        return {"status":"error","message":"Invalid SSO!"}
    cursor.execute("DELETE FROM auth_tokens_users WHERE user_id=?",(json_data["user_id"],))
    db.commit()
    cursor.close()
    return {"status":"success"}

@bp.route("/get_stream_ticket",methods=["POST"])
def generate_stream_tickets():
    json_data = request.get_json()
    if not json_data.get("sso_token"):
        return {"status":"error","message":"Send sso_token for authentication."}
    if not json_data.get("user_id"):
        return {"status":"error","message":"Send user_id for authentication."}
    auth_verify=verify_user_sso_token(get_db(),json_data["sso_token"],json_data["user_id"])
    if not auth_verify:
        return {"status":"error","message":"SSO Token invalid!"}
    if auth_verify[1]!=json_data["sso_token"]:
        return {"status":"sso_update","sso_token":auth_verify[1]}
    ticket=generate_stream_ticket(json_data["user_id"])
    return {"status":"success","stream_ticket":ticket}
