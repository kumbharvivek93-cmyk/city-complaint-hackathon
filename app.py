from flask import Flask,render_template,redirect,request,url_for,session,flash,Request
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
import os
from werkzeug.utils import secure_filename

app=Flask(__name__)
app.secret_key="vivekkali"
app.permanent_session_lifetime=timedelta(minutes=60)
app.config["SQLALCHEMY_DATABASE_URI"]='sqlite:///User.sqlite3'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=False
UPLOAD_FOLDER = "static/uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

db=SQLAlchemy(app)

class User(db.Model):
    name=db.Column(db.String(50))
    mobile_no=db.Column(db.String(13))
    adhar_no=db.Column(db.String(13),primary_key=True)
    
    def __init__(self,name,mobile_no,adhar_no):
        self.name=name
        self.mobile_no=mobile_no
        self.adhar_no=adhar_no

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50))
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    image = db.Column(db.String(200))   
    status = db.Column(db.String(20), default="Pending")



@app.route("/",methods=["GET","POST"])
def home():
    
    return render_template("home.html")


@app.route("/signup", methods=["GET","POST"])
def signup():
    session.permanent=True
    if request.method=="POST":
        name=request.form.get("name")
        mobile_no=request.form.get("mobile_no")
        adhar_no=request.form.get("adhar_no")

        new_user=User(
            name=name,
            mobile_no=mobile_no,
            adhar_no=adhar_no
        )
        session["name"]=name
        session["mobile_no"]=mobile_no
        session["aadhar"]=adhar_no

        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for("complaint"))
    else:
        if "name" in session:
            return redirect(url_for("complaint"))
        else :
            return render_template("signup.html")


@app.route("/login",methods=["GET","POST"])
def login():
    session.permanent=True
    if request.method=="POST":
        adhar_no=request.form.get("adhar_no")
        mobile_no=request.form.get("mobile_no")

        user=User.query.filter_by(adhar_no=adhar_no).first()
        if user and user.mobile_no ==mobile_no :
            flash("logged in successfully !")
            session["name"] = user.name
            session["mobile_no"] = user.mobile_no
            session["aadhar"] = user.adhar_no
            return redirect(url_for("complaint"))
        else:
            flash("user not found !")
            return redirect(url_for("signup"))
    else :
        if "name" in session:
            return redirect(url_for("complaint"))
        else :
            return render_template("login.html")

@app.route("/cityzens",methods=["GET","POST"])
def cityzens():
    user=User.query.all()
    return render_template("citizens.html",users=user)


@app.route("/logout",methods=["GET","POST"])
def logout():
    session.permanent=True
    if request.method=="POST":
        res=request.form.get("responce")
        session["res"]=res

        if res=="yes":
            session.clear()
            flash("logged out !!")
            return redirect(url_for("login"))
        else :
            flash("logout cancelled ! ")
            return redirect(url_for("home"))
    else:
        if "res" not in session:
            return render_template("logout.html")
        else:
            return render_template("logout.html")

@app.route("/complaint", methods=["GET", "POST"])
def complaint():
    if "name" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        category = request.form.get("category")
        description = request.form.get("description")

        file = request.files.get('image')

        filename = None
        if file and file.filename != "":
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_complaint = Complaint(
            user_name=session["name"],
            category=category,
            description=description,
            image=filename   
        )

        db.session.add(new_complaint)
        db.session.commit()

        flash("Complaint submitted!")
        return redirect(url_for("dashboard"))

    return render_template("complaint.html")

@app.route("/dashboard")
def dashboard():
    if "name" not in session:
        flash("Please login first!")
        return redirect(url_for("login"))

    user_name = session["name"]
    complaints = Complaint.query.filter_by(user_name=user_name).all()

    return render_template("dashboard.html", complaints=complaints)


if __name__=="__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
