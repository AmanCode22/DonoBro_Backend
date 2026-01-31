from flask import Blueprint,request,render_template,session,redirect,url_for,flash
import hashlib
import os
from dotenv import load_dotenv
from database import get_db
from utils.helper import generate_unique_hospital_id,check_fields
from utils.blockchain import create_block

load_dotenv()

bp=Blueprint("admin_blueprint",__name__)

@bp.route("/login",methods=["POST","GET"])
def login_admin():
    if session.get("is_admin"):
        return redirect(url_for(".dashboard_admin"))
    if request.method=="GET":
        return render_template("login_admin.html")
    if request.form.get("admin_password")==os.getenv("ADMIN_PASSWORD"):
        session["is_admin"]=True
        return redirect(url_for(".dashboard_admin"))
    else:
        flash("Invalid password","error")
        return render_template("login_admin.html")
@bp.route("/create",methods=["POST"])
def create_hospital():
    if not session.get("is_admin"):
        return redirect(url_for(".login_admin"))
    fields_required=["name","location","sector_hash","password"]
    check=check_fields(fields_required,request.form)
    if check!=True:
        flash(f"{check} cannot be empty.", "error")
        return redirect(url_for(".dashboard_admin"))
    db=get_db()
    hospital_id=generate_unique_hospital_id(db.cursor())
    cursor=db.cursor()
    password_hash=hashlib.md5(request.form["password"].encode()).hexdigest()
    cursor.execute("INSERT INTO Hospitals (hospital_id,name,location,sector_hash,auth_key_hash) VALUES (?,?,?,?,?);",(hospital_id,request.form["name"],request.form["location"],request.form["sector_hash"],password_hash))
    db.commit()
    cursor.close()
    create_block("HOSPITAL_CREATED", {"id": hospital_id, "name": request.form["name"]})
    flash(f"Hospital {hospital_id} Created Successfully!", "success")
    return redirect(url_for(".dashboard_admin"))
@bp.route("/dashboard")
def dashboard_admin():
    if not session.get("is_admin"):
        return redirect(url_for(".login_admin"))
    db=get_db()
    cursor=db.cursor()
    cursor.execute("SELECT * FROM Hospitals;")
    hospitals=cursor.fetchall()
    cursor.close()
    return render_template("admin_dashboard.html",hospitals=hospitals)
@bp.route("/delete",methods=["POST"])
def delete_hospital():
    if not session.get("is_admin"):
        return redirect(url_for(".login_admin"))
    hospital_id=request.form["hospital_id"]
    db=get_db()
    cursor=db.cursor()
    cursor.execute("DELETE FROM Hospitals WHERE hospital_id = ?",(hospital_id,))
    cursor.execute("UPDATE Users SET verified_by_hospital_id = NULL WHERE verified_by_hospital_id = ?",(hospital_id,))
    cursor.execute("UPDATE Requests SET verified_by_hospital_id = NULL WHERE verified_by_hospital_id = ?",(hospital_id,))
    db.commit()
    cursor.close()
    create_block("HOSPITAL_DELETED", {"id": hospital_id})
    flash(f"Hospital {hospital_id} Deleted Successfully!", "success")
    return redirect(url_for(".dashboard_admin"))