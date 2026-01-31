import secrets
import string
import uuid
import time
from utils.blockchain import create_block

def generate_hospital_id():
    alphabet = string.ascii_uppercase + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(12))
    return f"HOSPITAL-{random_part}"

def generate_unique_hospital_id(cursor):
    hospital_id=generate_hospital_id()
    
    cursor.execute("SELECT 1 FROM Hospitals WHERE hospital_id=?",(hospital_id,))
    is_unique=cursor.fetchone()
    while is_unique:
        hospital_id=generate_hospital_id()
        cursor.execute("SELECT 1 FROM Hospitals WHERE hospital_id=?",(hospital_id,))
        is_unique=cursor.fetchone()
    cursor.close()
    return hospital_id

def check_fields(fields,json_data):
    for i in fields:
        if not json_data.get(i,None):
            return i
    return True

def check_fields_api(fields,json_data):
    for i in fields:
        if not json_data.get(i,None):
            return {"status":"error","message":f"{i} cannot be empty."}
    return True


def generate_unique_device_id(cursor):
    device_id=str(uuid.uuid4())
    
    cursor.execute("SELECT 1 FROM Users WHERE device_id=?",(device_id,))
    is_unique=cursor.fetchone()
    while is_unique:
        device_id=str(uuid.uuid4())
        cursor.execute("SELECT 1 FROM Users WHERE device_id=?",(device_id,))
        is_unique=cursor.fetchone()
    cursor.close()
    return device_id

def generate_anon_id(type):
    alphabet = string.ascii_uppercase + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(10))
    return f"{type}-{random_part}"
def generate_unique_anon_id(cursor,type):
    anon_id=generate_anon_id()
    
    cursor.execute("SELECT 1 FROM Users WHERE anon_id=?",(anon_id,))
    is_unique=cursor.fetchone()
    while is_unique:
        anon_id=generate_anon_id()
        cursor.execute("SELECT 1 FROM Users WHERE anon_id=?",(anon_id,))
        is_unique=cursor.fetchone()
    cursor.close()
    return anon_id

def verify_user_sso_token(db,sso_token,user_id):
    cursor=db.cursor()
    cursor.execute("SELECT * FROM auth_tokens_users WHERE user_id=?;",(user_id,))
    sso_token_orignal=cursor.fetchone()
    if not sso_token_orignal:
        return False
    if sso_token_orignal["sso_token"]!=sso_token:
        return False,None
    if (int(time.time())-int(sso_token_orignal["created_at"]))>=2592000:
        new_sso=generate_unique_sso_token(db.cursor())
        cursor.execute("UPDATE auth_token_users SET sso_token=? WHERE user_id=?",(new_sso,user_id))
        create_block("RENEW_SSO_USER",{"anon_id":user_id,"sso_token":new_sso})
        db.commit()
        cursor.close()
        return True,new_sso
    return True,sso_token
    
def generate_unique_sso_token(cursor):
    sso_token=str(uuid.uuid4())
    cursor.execute("SELECT 1 FROM auth_token_users WHERE sso_token=?",(sso_token,))
    is_unique=cursor.fetchone()
    while is_unique:
        sso_token=str(uuid.uuid4())
        cursor.execute("SELECT 1 FROM auth_token_users WHERE sso_token=?",(sso_token,))
        is_unique=cursor.fetchone()
    cursor.close()
    return sso_token
