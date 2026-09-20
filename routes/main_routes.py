from flask import Blueprint, render_template, redirect, url_for, g
from auth import login_required
from models import Subject, Conversation, Quiz
from quiz_engine import QuizEngine
from ai_provider import AIProvider

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def dashboard():
    user = g.user
    recent_chats = (
        Conversation.query.filter_by(user_id=user.id, is_archived=False)
        .order_by(Conversation.updated_at.desc())
        .limit(4)
        .all()
    )

    subjects = Subject.query.all()
    quizzes = Quiz.query.all()
    analytics = QuizEngine.get_user_analytics(user.id)
    ai_status = AIProvider.get_active_provider_info()

    return render_template(
        "dashboard.html",
        user=user,
        recent_chats=recent_chats,
        subjects=subjects,
        quizzes=quizzes,
        analytics=analytics,
        ai_status=ai_status,
    )
