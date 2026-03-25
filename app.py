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

class user(db.Model):
    name=db.Column(db.String(50))
    mobile_no=db.Column(db.String(13))
    adhar_no=db.Column(db.String(13),primary_key=True)
    
    def __init__(self,name,mobile_no,adhar_no):
        self.name=name
        self.mobile_no=mobile_no
        self.adhar_no=adhar_no

class complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50))
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    image = db.Column(db.String(200))   
    status = db.Column(db.String(20), default="Pending")

with app.app_context():
    db.create_all()



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

        new_user=user(
            name=name,
            mobile_no=mobile_no,
            adhar_no=adhar_no
        )
        session["name"]=name
        session["mobile_no"]=mobile_no
        session["aadhar"]=adhar_no

        try:
            db.session.add(new_user)
            db.session.commit()
            print("user addin in database !!")
        except Exception as e:
            db.session.rollback()
            print(e)
        
        return redirect(url_for("Complaint"))
    else:
        if "name" in session:
            return redirect(url_for("Complaint"))
        else :
            return render_template("signup.html")


@app.route("/login",methods=["GET","POST"])
def login():
    session.permanent=True
    if request.method=="POST":
        adhar_no=request.form.get("adhar_no")
        mobile_no=request.form.get("mobile_no")

        user=user.query.filter_by(adhar_no=adhar_no).first()
        if user and user.mobile_no ==mobile_no :
            flash("logged in successfully !")
            session["name"] = user.name
            session["mobile_no"] = user.mobile_no
            session["aadhar"] = user.adhar_no
            return redirect(url_for("Complaint"))
        else:
            flash("user not found !")
            return redirect(url_for("signup"))
    else :
        if "name" in session:
            return redirect(url_for("Complaint"))
        else :
            return render_template("login.html")

@app.route("/cityzens",methods=["GET","POST"])
def cityzens():
    user=user.query.all()
    return render_template("citizens.html",users=user)

@app.route("/complaint_category",methods=["GET","POST"])
def complaint_category():
    if "name" in session:
        flash("lets do it ! ")
        return render_template("category.html")
    else:
        flash("you are not logged in !!")
        return render_template("login.html")


@app.route("/logout",methods=["GET","POST"])
def logout():
    session.permanent=True
    if request.method=="POST":
        res=request.form.get("response")
        session["res"]=res

        if res=="yes":
            session.pop("name",None)
            session.pop("aadhar",None)
            session.pop("mobile_no",None)
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
def Complaint():
    if request.method == "POST":
        name = request.form.get("user_name")
        category = request.form.get("category")
        description = request.form.get("description")
        image = request.files.get("image")
        session["name"]=name
        session["ncategoryame"]=category
        session["description"]=description
        


        filename = None
        if image and image.filename != "":
            filename = secure_filename(image.filename)
            image.save(os.path.join("static/uploads", filename))

        new_complaint = complaint(
            user_name=name,
            category=category,
            description=description,
            image=filename
        )
        try :
            db.session.add(new_complaint)
            db.session.commit()
            print("complaint adde in database !!")
        except Exception as e:
            db.session.rollback()
            print(e)


        return redirect(url_for("dashboard"))

    return render_template("complaint.html")

@app.route("/dashboard",methods=["GET","POST"])
def dashboard():
    if "name" not in session:
        flash("Please login first!")
        return redirect(url_for("login"))

    user_name = session["name"]

    complaints = complaint.query.filter_by(user_name=user_name).all()

    if complaints:
        flash("Complaint submitted successfully! Thank you 🙏")
    else:
        flash("You have not submitted any complaint!")

    return render_template("dashboard.html", complaints=complaints)


if __name__=="__main__":
    app.run(debug=True)


# this is modified version build to run multithreaded on gunicorn etc for deployment    ~ spyder aidev vivek sir love you all 
