"""
EduManage - Student Management System
Full-Stack Project: Python (Flask + SQLAlchemy + JWT) backend, HTML/CSS/JS frontend,
with a companion .NET (C#) console tool that consumes the REST API.

Run:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000 in your browser.

Default admin login:  username: admin   password: admin123
"""

from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
import jwt
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "edumanage-super-secret-key-change-in-production"

db = SQLAlchemy(app)

#MODELS:

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="admin")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    roll_number = db.Column(db.String(30), unique=True, nullable=False)
    department = db.Column(db.String(80), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    attendance_percent = db.Column(db.Float, default=100.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "roll_number": self.roll_number,
            "department": self.department,
            "year": self.year,
            "email": self.email,
            "attendance_percent": self.attendance_percent,
        }


# ---------------------------------------------------------------------------
# JWT auth helpers


def create_token(user):
    payload = {
        "user_id": user.id,
        "username": user.username,
        "exp": datetime.utcnow() + timedelta(hours=8),
    }
    return jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        if not token:
            return jsonify({"message": "Token is missing"}), 401
        try:
            jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Frontend routes (serve HTML pages)
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# ---------------------------------------------------------------------------
# Auth API
# ---------------------------------------------------------------------------

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    username = data.get("username", "")
    password = data.get("password", "")

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"message": "Invalid username or password"}), 401

    token = create_token(user)
    return jsonify({"token": token, "username": user.username})


# ---------------------------------------------------------------------------
# Student REST API (CRUD) - consumed by the frontend AND the .NET console tool
# ---------------------------------------------------------------------------

@app.route("/api/students", methods=["GET"])
@token_required
def get_students():
    students = Student.query.order_by(Student.id).all()
    return jsonify([s.to_dict() for s in students])


@app.route("/api/students/<int:student_id>", methods=["GET"])
@token_required
def get_student(student_id):
    student = Student.query.get_or_404(student_id)
    return jsonify(student.to_dict())


@app.route("/api/students", methods=["POST"])
@token_required
def add_student():
    data = request.get_json(force=True)
    try:
        student = Student(
            name=data["name"],
            roll_number=data["roll_number"],
            department=data["department"],
            year=int(data["year"]),
            email=data["email"],
            attendance_percent=float(data.get("attendance_percent", 100.0)),
        )
        db.session.add(student)
        db.session.commit()
        return jsonify(student.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Could not add student: {e}"}), 400


@app.route("/api/students/<int:student_id>", methods=["PUT"])
@token_required
def update_student(student_id):
    student = Student.query.get_or_404(student_id)
    data = request.get_json(force=True)
    student.name = data.get("name", student.name)
    student.department = data.get("department", student.department)
    student.year = int(data.get("year", student.year))
    student.email = data.get("email", student.email)
    student.attendance_percent = float(data.get("attendance_percent", student.attendance_percent))
    db.session.commit()
    return jsonify(student.to_dict())


@app.route("/api/students/<int:student_id>", methods=["DELETE"])
@token_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    return jsonify({"message": "Student deleted"})


# ---------------------------------------------------------------------------
# A public (no-auth) summary endpoint - this is what the .NET console tool
# calls to demonstrate cross-stack / cross-language API integration.
# ---------------------------------------------------------------------------

@app.route("/api/public/report-data", methods=["GET"])
def public_report_data():
    students = Student.query.order_by(Student.department, Student.name).all()
    return jsonify([s.to_dict() for s in students])


# ---------------------------------------------------------------------------
# Database bootstrap
# ---------------------------------------------------------------------------

def seed_database():
    db.create_all()

    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", role="admin")
        admin.set_password("admin123")
        db.session.add(admin)

    if Student.query.count() == 0:
        sample_students = [
            Student(name="Arjun Kumar", roll_number="ECE001", department="ECE", year=3, email="arjun@example.com", attendance_percent=92.5),
            Student(name="Divya Ramesh", roll_number="CSE002", department="CSE", year=2, email="divya@example.com", attendance_percent=88.0),
            Student(name="Karthik S", roll_number="ECE003", department="ECE", year=4, email="karthik@example.com", attendance_percent=95.2),
            Student(name="Priya Menon", roll_number="IT004", department="IT", year=1, email="priya@example.com", attendance_percent=79.4),
        ]
        db.session.bulk_save_objects(sample_students)

    db.session.commit()


if __name__ == "__main__":
    with app.app_context():
        seed_database()
    app.run(debug=True, host="127.0.0.1", port=5000)
