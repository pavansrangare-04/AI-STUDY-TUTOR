from datetime import datetime
from models import db, Quiz, QuizQuestion, QuizAttempt, Subject, Topic, Conversation, Message


class QuizEngine:
    """Evaluates quiz attempts, calculates analytics, and generates study recommendations."""

    @staticmethod
    def evaluate_quiz(quiz_id, user_id, user_answers: dict):
        """
        user_answers: dict of {question_id_str: selected_option_str} e.g. {"1": "B", "2": "C"}
        """
        quiz = Quiz.query.get_or_404(quiz_id)
        questions = quiz.questions.all()

        if not questions:
            raise ValueError("This quiz contains no questions.")

        score = 0
        total = len(questions)
        breakdown = []

        for q in questions:
            selected = user_answers.get(str(q.id), "").strip().upper()
            is_correct = selected == q.correct_option

            if is_correct:
                score += 1

            options = {
                "A": q.option_a,
                "B": q.option_b,
                "C": q.option_c,
                "D": q.option_d,
            }

            breakdown.append({
                "question_id": q.id,
                "question_text": q.question_text,
                "selected_option": selected,
                "selected_text": options.get(selected, "No answer selected"),
                "correct_option": q.correct_option,
                "correct_text": options.get(q.correct_option, ""),
                "is_correct": is_correct,
                "explanation": q.explanation,
            })

        accuracy_pct = round((score / total) * 100.0, 1)

        # Save Attempt in DB
        attempt = QuizAttempt(
            user_id=user_id,
            quiz_id=quiz.id,
            score=score,
            total_questions=total,
            accuracy_pct=accuracy_pct,
            completed_at=datetime.utcnow(),
        )
        attempt.answers = breakdown
        db.session.add(attempt)
        db.session.commit()

        return {
            "attempt_id": attempt.id,
            "quiz_id": quiz.id,
            "quiz_title": quiz.title,
            "subject_name": quiz.subject.name,
            "score": score,
            "total": total,
            "accuracy_pct": accuracy_pct,
            "breakdown": breakdown,
        }

    @staticmethod
    def get_user_analytics(user_id):
        """Compute real, verified learning progress and quiz analytics for user."""
        # 1. Questions asked
        user_conversations = Conversation.query.filter_by(user_id=user_id).all()
        conversation_ids = [c.id for c in user_conversations]

        total_questions_asked = 0
        if conversation_ids:
            total_questions_asked = Message.query.filter(
                Message.conversation_id.in_(conversation_ids),
                Message.sender == "user"
            ).count()

        # 2. Quiz Attempts
        attempts = QuizAttempt.query.filter_by(user_id=user_id).order_by(QuizAttempt.completed_at.desc()).all()
        total_quizzes = len(attempts)

        avg_accuracy = 0.0
        if total_quizzes > 0:
            avg_accuracy = round(sum(a.accuracy_pct for a in attempts) / total_quizzes, 1)

        # 3. Subject-wise performance
        subject_stats = {}
        for a in attempts:
            sub = a.quiz.subject
            if sub.id not in subject_stats:
                subject_stats[sub.id] = {
                    "subject_id": sub.id,
                    "subject_name": sub.name,
                    "subject_code": sub.code,
                    "attempts": 0,
                    "total_score": 0,
                    "total_questions": 0,
                }
            subject_stats[sub.id]["attempts"] += 1
            subject_stats[sub.id]["total_score"] += a.score
            subject_stats[sub.id]["total_questions"] += a.total_questions

        subject_breakdown = []
        for s in subject_stats.values():
            pct = round((s["total_score"] / s["total_questions"]) * 100.0, 1) if s["total_questions"] > 0 else 0
            subject_breakdown.append({
                "name": s["subject_name"],
                "code": s["subject_code"],
                "attempts": s["attempts"],
                "accuracy": pct,
            })

        # 4. Weak & Strong Topics Identification
        weak_topics = []
        strong_topics = []
        for a in attempts:
            sub_name = a.quiz.subject.name
            quiz_title = a.quiz.title
            if a.accuracy_pct < 65:
                weak_topics.append({
                    "subject": sub_name,
                    "topic": quiz_title,
                    "accuracy": a.accuracy_pct,
                    "reason": f"Scored {a.accuracy_pct}% on {quiz_title}. Review core definitions and retry.",
                })
            elif a.accuracy_pct >= 80:
                strong_topics.append({
                    "subject": sub_name,
                    "topic": quiz_title,
                    "accuracy": a.accuracy_pct,
                })

        # 5. Personalized Recommendations
        recommendations = []
        if weak_topics:
            for wt in weak_topics[:3]:
                recommendations.append({
                    "title": f"Revise: {wt['topic']}",
                    "subject": wt["subject"],
                    "badge": "Priority Revision",
                    "reason": wt["reason"],
                    "action_url": f"/subjects",
                })
        elif total_quizzes > 0:
            recommendations.append({
                "title": "Advance to Higher Difficulty Quizzes",
                "subject": "All Subjects",
                "badge": "Mastery",
                "reason": f"Great job! Your current average accuracy is {avg_accuracy}%. Challenge yourself with advanced topics.",
                "action_url": "/quizzes",
            })
        else:
            # Onboarding recommendation when no quiz attempts exist
            recommendations.append({
                "title": "Take Your First Diagnostic Quiz",
                "subject": "Operating Systems or DSA",
                "badge": "Getting Started",
                "reason": "Complete a 5-question quiz in the Quiz Center so the AI Tutor can analyze your strengths and tailor explanations to your level.",
                "action_url": "/quizzes",
            })

        return {
            "total_conversations": len(user_conversations),
            "total_questions_asked": total_questions_asked,
            "total_quizzes_attempted": total_quizzes,
            "average_accuracy": avg_accuracy,
            "subject_breakdown": subject_breakdown,
            "weak_topics": weak_topics[:5],
            "strong_topics": strong_topics[:5],
            "recommendations": recommendations,
            "recent_attempts": [
                {
                    "id": a.id,
                    "quiz_title": a.quiz.title,
                    "subject_name": a.quiz.subject.name,
                    "score": f"{a.score}/{a.total_questions}",
                    "accuracy": a.accuracy_pct,
                    "date": a.completed_at.strftime("%b %d, %Y - %H:%M"),
                }
                for a in attempts[:6]
            ],
        }
