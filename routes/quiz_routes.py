from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, g
from auth import login_required
from models import Quiz, QuizAttempt
from quiz_engine import QuizEngine

quiz_bp = Blueprint("quiz", __name__)


@quiz_bp.route("/quizzes")
@login_required
def quiz_list():
    quizzes = Quiz.query.all()
    user_attempts = (
        QuizAttempt.query.filter_by(user_id=g.user.id)
        .order_by(QuizAttempt.completed_at.desc())
        .all()
    )

    # Map quiz_id to latest attempt
    latest_attempts = {}
    for a in user_attempts:
        if a.quiz_id not in latest_attempts:
            latest_attempts[a.quiz_id] = a

    return render_template(
        "quiz_list.html",
        user=g.user,
        quizzes=quizzes,
        latest_attempts=latest_attempts,
        history=user_attempts[:8],
    )


@quiz_bp.route("/quizzes/<int:quiz_id>")
@login_required
def take_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = quiz.questions.all()

    if not questions:
        flash("This quiz currently has no questions.", "warning")
        return redirect(url_for("quiz.quiz_list"))

    return render_template("quiz_view.html", user=g.user, quiz=quiz, questions=questions)


@quiz_bp.route("/api/quiz/<int:quiz_id>/submit", methods=["POST"])
@login_required
def submit_quiz(quiz_id):
    data = request.get_json() or {}
    answers = data.get("answers", {})  # {"1": "A", "2": "B"}

    try:
        result = QuizEngine.evaluate_quiz(quiz_id, g.user.id, answers)
        return jsonify({"success": True, "result": result})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 400


@quiz_bp.route("/quizzes/results/<int:attempt_id>")
@login_required
def quiz_result(attempt_id):
    attempt = QuizAttempt.query.filter_by(id=attempt_id, user_id=g.user.id).first_or_404()
    return render_template("quiz_result.html", user=g.user, attempt=attempt)
