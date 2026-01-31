from flask import Blueprint,request,render_template,session,redirect,url_for,flash
from database import get_db
from utils.notification import send_wake_up_signal
import hashlib
from utils.blockchain import create_block
from utils.helper import check_fields

bp=Blueprint("web_hospital_bp",__name__)

@bp.route("/login",methods=["GET","POST"])
def login_hospital():
    if "hospital_id" in session:
        return redirect(url_for(".dashboard_route"))
    if request.method=="GET":
        return render_template("login.html")
    fields=["hospital_id","password"]
    check=check_fields(fields,request.form)
    if check!=True:
        flash(f"{check} is required","error")
        return render_template("login.html")
    db=get_db()
    cursor=db.cursor()
    cursor.execute("SELECT * FROM Hospitals WHERE hospital_id=?",(request.form["hospital_id"],))
    data=cursor.fetchone()
    if not data:
        flash("Invalid hospital ID",'error')
        return render_template("login.html")
    if hashlib.md5(request.form["password"].encode()).hexdigest()!=data["auth_key_hash"]:
        flash("Invalid password","error")
        return render_template("login.html")
    session["hospital_id"]=request.form["hospital_id"]
    return redirect(url_for(".dashboard_route"))

@bp.route("/dashboard")
def dashboard_route():
    if "hospital_id" not in session:
        return redirect(url_for(".login_hospital"))
    db=get_db()
    cursor=db.cursor()
    cursor.execute('SELECT name,sector_hash FROM Hospitals WHERE hospital_id=?',(session["hospital_id"],))
    h_row=cursor.fetchone()
    if not h_row:
        session.clear()
        return redirect(url_for(".login_hospital"))
    sector_hash=h_row["sector_hash"]
    hospital_name=h_row["name"]
    cursor.execute('SELECT * FROM Requests WHERE status="Active" AND verified_by_hospital_id IS NULL')
    req_all=cursor.fetchall()
    cursor.execute("SELECT r.* FROM Requests AS r JOIN Users AS u ON r.patient_id=u.anon_id WHERE u.sector_hash=?",(sector_hash,))
    req_sector=cursor.fetchall()
    cursor.execute("SELECT * FROM Users WHERE verified_by_hospital_id IS NULL")
    users_all=cursor.fetchall()
    cursor.execute("SELECT * FROM Users WHERE verified_by_hospital_id IS NULL AND sector_hash=?",(sector_hash,))
    users_sector=cursor.fetchall()
    return render_template("dashboard.html",pending_requests=req_all,pending_req_sector=req_sector,sector_hash=sector_hash,pending_users=users_all,pending_user_sector=users_sector,hospital_name=hospital_name)

@bp.route("/verify/request",methods=["POST"])
def verify_request():
    if "hospital_id" not in session:
        return redirect(url_for(".login_hospital"))
    req_id=request.form.get("request_id")
    if not req_id:
        return redirect(url_for(".dashboard_route"))
    db=get_db()
    cursor=db.cursor()
    cursor.execute('UPDATE Requests SET verified_by_hospital_id=? WHERE request_id=?',(session["hospital_id"],req_id))
    db.commit()
    cursor.execute("SELECT patient_id FROM Requests WHERE request_id=?",(req_id,))
    p_row=cursor.fetchone()
    if p_row:
        cursor.execute("SELECT sector_hash FROM Users WHERE anon_id=?",(p_row["patient_id"],))
        u_row=cursor.fetchone()
        if u_row:
            cursor.execute("SELECT device_id FROM Users WHERE sector_hash=? AND role='Donor'",(u_row["sector_hash"],))
            donors=cursor.fetchall()
            for d in donors:
                send_wake_up_signal(d["device_id"],"VERIFIED_ALERT",{"request_id":req_id})
    create_block("VERIFY_REQUEST", {"request_id": req_id, "hospital_id": session["hospital_id"]})
    return redirect(url_for(".dashboard_route"))

@bp.route("/verify/user",methods=["POST"])
def verify_user():
    if "hospital_id" not in session:
        return redirect(url_for(".login_hospital"))
    uid=request.form.get("user_id")
    if not uid:
        return redirect(url_for(".dashboard_route"))
    db=get_db()
    cursor=db.cursor()
    cursor.execute("UPDATE Users SET verified_by_hospital_id=? WHERE anon_id=?",(session["hospital_id"],uid))
    cursor.execute("UPDATE Requests SET verified_by_hospital_id=? WHERE patient_id=? AND status='Active'",(session["hospital_id"],uid))
    db.commit()
    cursor.execute("SELECT device_id FROM Users WHERE anon_id=?",(uid,))
    u_row=cursor.fetchone()
    if u_row:
        send_wake_up_signal(u_row["device_id"],"USER_VERIFIED")
    create_block("VERIFY_USER", {"anon_id": uid, "hospital_id": session["hospital_id"]})
    return redirect(url_for(".dashboard_route"))