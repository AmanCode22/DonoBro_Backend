from flask import Flask,render_template,redirect,Response,request
from database import close_db,init_db_command
from dotenv import load_dotenv
import os
from routes.api_routes import bp as api_bp
from routes.web_hospital import bp as hospital_bp
from routes.admin_routes import bp as admin_bp
import utils.notification as notifications

load_dotenv()

app=Flask("DonorBro_Backend")

app.teardown_appcontext(close_db)
app.cli.add_command(init_db_command)

app.secret_key=os.getenv("SECRET_KEY")

app.register_blueprint(api_bp,url_prefix="/api")
app.register_blueprint(hospital_bp,url_prefix="/hospital")
app.register_blueprint(admin_bp, url_prefix="/admin")


@app.route("/")
def index_route():
    return render_template("index_main.html")
@app.route("/under_maintenance")
def maintenance_route():
    return render_template("under_maintenance.html")
@app.route("/favicon.ico")
def favicon_redirect():
    return redirect("/static/icon.png")
@app.route('/events')
def events():
    stream_ticket=request.args.get("stream_ticket")
    if not stream_ticket:
        return "Unauthorized", 403

    
    resp=Response(
        notifications.stream_for_user(stream_ticket),
        mimetype='text/event-stream'
    )
    resp.headers['Cache-Control'] = 'no-cache'
    resp.headers['X-Accel-Buffering']="no"
    return resp
if __name__=="__main__":
    app.run("0.0.0.0")