from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from models import db, User

auth_bp = Blueprint("auth", __name__)


def get_current_user():
    """Retrieve the currently logged-in user from session."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


def login_required(view_func):
    @wraps(view_func)
    def decorated_view(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        return view_func(*args, **kwargs)
    return decorated_view


def admin_required(view_func):
    @wraps(view_func)
    def decorated_view(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in with administrator privileges.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        user = get_current_user()
        if not user or not user.is_admin:
            flash("Access denied: Administrator privileges required.", "danger")
            return redirect(url_for("main.dashboard"))
        return view_func(*args, **kwargs)
    return decorated_view


@auth_bp.before_app_request
def load_logged_in_user():
    g.user = get_current_user()


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username_or_email = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

        if user and user.check_password(password):
            session.clear()
            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role
            flash(f"Welcome back, {user.username}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.dashboard"))

        flash("Invalid username/email or password.", "danger")

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        learning_level = request.form.get("learning_level", "intermediate")
        explanation_style = request.form.get("explanation_style", "detailed")

        if len(username) < 3:
            flash("Username must be at least 3 characters.", "danger")
            return render_template("register.html")
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("register.html")

        if User.query.filter_by(username=username).first():
            flash("That username is already registered. Please choose another.", "danger")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "danger")
            return render_template("register.html")

        new_user = User(
            username=username,
            email=email,
            role="student",
            learning_level=learning_level,
            explanation_style=explanation_style,
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        session.clear()
        session["user_id"] = new_user.id
        session["username"] = new_user.username
        session["role"] = new_user.role
        flash("Registration successful! Welcome to Virtual AI Tutor.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("register.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = g.user
    if request.method == "POST":
        learning_level = request.form.get("learning_level", user.learning_level)
        explanation_style = request.form.get("explanation_style", user.explanation_style)
        theme_preference = request.form.get("theme_preference", user.theme_preference)
        new_password = request.form.get("new_password", "").strip()

        user.learning_level = learning_level
        user.explanation_style = explanation_style
        user.theme_preference = theme_preference

        if new_password:
            if len(new_password) < 6:
                flash("New password must be at least 6 characters.", "danger")
                return render_template("profile.html", user=user)
            user.set_password(new_password)
            flash("Preferences and password updated successfully!", "success")
        else:
            flash("Preferences updated successfully!", "success")

        db.session.commit()
        return redirect(url_for("auth.profile"))

    return render_template("profile.html", user=user)
