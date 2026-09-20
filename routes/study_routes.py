from flask import Blueprint, render_template, jsonify, g
from auth import login_required
from models import Subject, Topic, StudyMaterial

study_bp = Blueprint("study", __name__)


@study_bp.route("/subjects")
@login_required
def subjects_list():
    subjects = Subject.query.all()
    return render_template("subjects.html", user=g.user, subjects=subjects)


@study_bp.route("/subjects/<int:subject_id>")
@login_required
def subject_detail(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    topics = subject.topics.order_by(Topic.order.asc()).all()
    materials = subject.materials.order_by(StudyMaterial.created_at.desc()).all()
    quizzes = subject.quizzes.all()

    return render_template(
        "subject_detail.html",
        user=g.user,
        subject=subject,
        topics=topics,
        materials=materials,
        quizzes=quizzes,
    )


@study_bp.route("/api/study/materials/<int:material_id>")
@login_required
def get_material_json(material_id):
    mat = StudyMaterial.query.get_or_404(material_id)
    return jsonify({
        "id": mat.id,
        "title": mat.title,
        "subject": mat.subject.name,
        "topic": mat.topic.name if mat.topic else "General",
        "content": mat.content,
        "summary": mat.summary,
        "created_at": mat.created_at.strftime("%b %d, %Y"),
    })
