import os
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
if not app.config["SECRET_KEY"]:
    raise RuntimeError("Set a strong SECRET_KEY environment variable before starting the app.")

database_url = os.environ.get("DATABASE_URL", "sqlite:///illuminati_qa.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config.update(
    SQLALCHEMY_DATABASE_URI=database_url,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
    MAX_CONTENT_LENGTH=32 * 1024,
)

db = SQLAlchemy(app)
CSRFProtect(app)
limiter = Limiter(get_remote_address, app=app, default_limits=["120 per hour"])

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(10), nullable=False)  # question or answer
    display_name = db.Column(db.String(60), nullable=False)
    content = db.Column(db.String(2000), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("submission.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    parent = db.relationship("Submission", remote_side=[id], backref="answers")

def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    return wrapped

@app.route("/")
def index():
    questions = Submission.query.filter_by(kind="question").order_by(Submission.created_at.desc()).all()
    return render_template("index.html", questions=questions)

@app.route("/ask", methods=["POST"])
@limiter.limit("10 per hour")
def ask():
    name = request.form.get("display_name", "").strip()
    content = request.form.get("content", "").strip()
    if not name or len(name) > 60 or not content or len(content) > 2000:
        flash("Please enter a display name (up to 60 characters) and a question (up to 2,000 characters).", "error")
        return redirect(url_for("index"))
    db.session.add(Submission(kind="question", display_name=name, content=content))
    db.session.commit()
    flash("Your question was submitted.", "success")
    return redirect(url_for("index"))

@app.route("/answer/<int:question_id>", methods=["POST"])
@limiter.limit("20 per hour")
def answer(question_id):
    question = Submission.query.filter_by(id=question_id, kind="question").first_or_404()
    name = request.form.get("display_name", "").strip()
    content = request.form.get("content", "").strip()
    if not name or len(name) > 60 or not content or len(content) > 2000:
        flash("Please enter a display name and an answer (up to 2,000 characters).", "error")
        return redirect(url_for("index"))
    db.session.add(Submission(kind="answer", display_name=name, content=content, question_id=question.id))
    db.session.commit()
    flash("Your answer was submitted.", "success")
    return redirect(url_for("index"))

@app.route("/admin/login", methods=["GET", "POST"])
@limiter.limit("8 per minute")
def admin_login():
    if request.method == "POST":
        expected_hash = os.environ.get("ADMIN_PASSWORD_HASH", "")
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        expected_user = os.environ.get("ADMIN_USERNAME", "mridul")
        if expected_hash and username == expected_user and check_password_hash(expected_hash, password):
            session.clear()
            session["is_admin"] = True
            session.permanent = True
            flash("Signed in.", "success")
            return redirect(url_for("admin"))
        flash("Invalid admin credentials. Check your deployment environment variables.", "error")
    return render_template("admin_login.html")

@app.route("/admin")
@admin_required
def admin():
    questions = Submission.query.filter_by(kind="question").order_by(Submission.created_at.desc()).all()
    answers = Submission.query.filter_by(kind="answer").order_by(Submission.created_at.desc()).all()
    return render_template("admin.html", questions=questions, answers=answers)

@app.route("/admin/logout", methods=["POST"])
@admin_required
def admin_logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("index"))

@app.route("/admin/delete/<int:item_id>", methods=["POST"])
@admin_required
def delete_submission(item_id):
    item = db.session.get(Submission, item_id)
    if item:
        # Remove replies first if deleting a question.
        if item.kind == "question":
            Submission.query.filter_by(question_id=item.id).delete()
        db.session.delete(item)
        db.session.commit()
        flash("Submission deleted.", "success")
    return redirect(url_for("admin"))

@app.errorhandler(413)
def too_large(_error):
    return "Request too large. Please keep submissions under 2,000 characters.", 413

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=False)
