from datetime import timedelta
from pathlib import Path
from uuid import uuid4
import os

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
DB_PATH = INSTANCE_DIR / "User.sqlite3"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

INSTANCE_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "vivekkali")
app.permanent_session_lifetime = timedelta(minutes=60)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = str(UPLOAD_DIR)

db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = "user"

    adhar_no = db.Column(db.String(13), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    mobile_no = db.Column(db.String(13), nullable=False)


class Sector(db.Model):
    __tablename__ = "sector"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    icon = db.Column(db.String(10), nullable=False)
    description = db.Column(db.Text, nullable=False)
    asset_note = db.Column(db.Text, nullable=False)
    theme_class = db.Column(db.String(50), nullable=False)


class Complaint(db.Model):
    __tablename__ = "complaint"

    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(200))
    status = db.Column(db.String(20), default="Pending", nullable=False)


SECTOR_SEED_DATA = [
    {
        "name": "Health",
        "icon": "🏥",
        "description": "Hospitals, clinics, ambulance services, medicine availability, and patient support systems.",
        "asset_note": "Protect patient records, emergency dashboards, and hospital service data.",
        "theme_class": "health-card",
    },
    {
        "name": "Education",
        "icon": "🎓",
        "description": "Schools, colleges, scholarship systems, digital classrooms, and student access issues.",
        "asset_note": "Report problems involving student portals, exam data, and learning platforms.",
        "theme_class": "education-card",
    },
    {
        "name": "Tourism",
        "icon": "🛕",
        "description": "Heritage places, visitor centres, booking systems, maps, signage, and local attraction support.",
        "asset_note": "Help secure tourism information boards, booking records, and visitor data.",
        "theme_class": "tourism-card",
    },
    {
        "name": "Sports",
        "icon": "🏅",
        "description": "Playgrounds, stadiums, event registrations, youth clubs, and training facility complaints.",
        "asset_note": "Cover athlete records, tournament schedules, and facility management systems.",
        "theme_class": "sports-card",
    },
    {
        "name": "Organizations",
        "icon": "🏢",
        "description": "Municipal offices, NGOs, citizen service centres, and internal process management issues.",
        "asset_note": "Flag risks to public files, office software, and organizational data access.",
        "theme_class": "organizations-card",
    },
    {
        "name": "Public Services",
        "icon": "🛡️",
        "description": "General civic systems, grievance platforms, certificates, smart kiosks, and citizen help desks.",
        "asset_note": "Use this for service interruptions, portal misuse, or document security concerns.",
        "theme_class": "services-card",
    },
]


def seed_sectors() -> None:
    existing_names = {sector.name for sector in Sector.query.all()}
    new_rows = [
        Sector(**sector_data)
        for sector_data in SECTOR_SEED_DATA
        if sector_data["name"] not in existing_names
    ]
    if new_rows:
        db.session.add_all(new_rows)
        db.session.commit()


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def current_sectors() -> list[Sector]:
    return Sector.query.order_by(Sector.id).all()


def require_login():
    if "name" not in session:
        flash("Please login first.")
        return redirect(url_for("login"))
    return None


with app.app_context():
    db.create_all()
    seed_sectors()


@app.route("/", methods=["GET"])
def home():
    return render_template("home.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    session.permanent = True

    if "name" in session:
        return redirect(url_for("complaint_category"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        mobile_no = request.form.get("mobile_no", "").strip()
        adhar_no = request.form.get("adhar_no", "").strip()

        if not name or not mobile_no or not adhar_no:
            flash("Please fill in all signup fields.")
            return redirect(url_for("signup"))

        existing_user = db.session.get(User, adhar_no)
        if existing_user:
            flash("Account already exists. Please login.")
            return redirect(url_for("login"))

        new_user = User(name=name, mobile_no=mobile_no, adhar_no=adhar_no)
        db.session.add(new_user)
        db.session.commit()

        session["name"] = new_user.name
        session["mobile_no"] = new_user.mobile_no
        session["aadhar"] = new_user.adhar_no

        flash("Signup successful.")
        return redirect(url_for("complaint_category"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.permanent = True

    if "name" in session:
        return redirect(url_for("complaint_category"))

    if request.method == "POST":
        adhar_no = request.form.get("adhar_no", "").strip()
        mobile_no = request.form.get("mobile_no", "").strip()

        found_user = db.session.get(User, adhar_no)
        if not found_user:
            flash("User not found. Please sign up first.")
            return redirect(url_for("signup"))

        if found_user.mobile_no != mobile_no:
            flash("Mobile number does not match our records.")
            return redirect(url_for("login"))

        session["name"] = found_user.name
        session["mobile_no"] = found_user.mobile_no
        session["aadhar"] = found_user.adhar_no
        flash("Logged in successfully.")
        return redirect(url_for("complaint_category"))

    return render_template("login.html")


@app.route("/cityzens", methods=["GET"])
@app.route("/citizens", methods=["GET"])
def cityzens():
    users = User.query.order_by(User.name).all()
    return render_template("citizens.html", users=users)


@app.route("/complaint_category", methods=["GET"])
def complaint_category():
    redirect_response = require_login()
    if redirect_response:
        return redirect_response

    sectors = current_sectors()
    return render_template("category.html", sectors=sectors)


@app.route("/logout", methods=["GET", "POST"])
def logout():
    if request.method == "POST":
        response = request.form.get("response")
        if response == "yes":
            session.clear()
            flash("Logged out successfully.")
            return redirect(url_for("login"))

        flash("Logout cancelled.")
        return redirect(url_for("home"))

    return render_template("logout.html")


@app.route("/complaint", methods=["GET", "POST"])
def complaint_form():
    redirect_response = require_login()
    if redirect_response:
        return redirect_response

    sectors = current_sectors()
    sector_names = [sector.name for sector in sectors]
    selected_category = request.args.get("category", "")
    if selected_category not in sector_names and sector_names:
        selected_category = sector_names[0]

    if request.method == "POST":
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "").strip()
        image = request.files.get("image")

        if category not in sector_names:
            flash("Please choose a valid sector.")
            return render_template(
                "complaint.html",
                sectors=sectors,
                selected_category=selected_category,
                current_user=session.get("name", ""),
            )

        if not description:
            flash("Please describe the issue.")
            return render_template(
                "complaint.html",
                sectors=sectors,
                selected_category=category,
                current_user=session.get("name", ""),
            )

        filename = None
        if image and image.filename:
            if not allowed_file(image.filename):
                flash("Only png, jpg, jpeg, gif, and webp files are allowed.")
                return render_template(
                    "complaint.html",
                    sectors=sectors,
                    selected_category=category,
                    current_user=session.get("name", ""),
                )

            safe_name = secure_filename(image.filename)
            filename = f"{uuid4().hex}_{safe_name}"
            image.save(UPLOAD_DIR / filename)

        new_complaint = Complaint(
            user_name=session["name"],
            category=category,
            description=description,
            image=filename,
        )
        db.session.add(new_complaint)
        db.session.commit()

        flash("Complaint submitted successfully.")
        return redirect(url_for("dashboard"))

    return render_template(
        "complaint.html",
        sectors=sectors,
        selected_category=selected_category,
        current_user=session.get("name", ""),
    )


@app.route("/dashboard", methods=["GET"])
def dashboard():
    redirect_response = require_login()
    if redirect_response:
        return redirect_response

    complaints = (
        Complaint.query.filter_by(user_name=session["name"])
        .order_by(Complaint.id.desc())
        .all()
    )
    return render_template("dashboard.html", complaints=complaints)


@app.route("/category", methods=["GET"])
def category():
    return redirect(url_for("complaint_category"))


if __name__ == "__main__":
    app.run(debug=True)
