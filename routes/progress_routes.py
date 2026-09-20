from flask import Blueprint, render_template, g
from auth import login_required
from quiz_engine import QuizEngine

progress_bp = Blueprint("progress", __name__)


@progress_bp.route("/progress")
@login_required
def progress_view():
    analytics = QuizEngine.get_user_analytics(g.user.id)
    return render_template("progress.html", user=g.user, analytics=analytics)
