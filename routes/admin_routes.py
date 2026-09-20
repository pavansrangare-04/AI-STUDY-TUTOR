from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from auth import admin_required
from models import db, Subject, Topic, StudyMaterial, MaterialChunk, Quiz, QuizAttempt, User
from rag_engine import RAGEngine

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin")
@admin_required
def admin_dashboard():
    subjects = Subject.query.all()
    topics = Topic.query.all()
    materials = StudyMaterial.query.order_by(StudyMaterial.created_at.desc()).all()
    total_chunks = MaterialChunk.query.count()
    total_quizzes = Quiz.query.count()
    total_attempts = QuizAttempt.query.count()
    total_users = User.query.count()

    return render_template(
        "admin.html",
        user=g.user,
        subjects=subjects,
        topics=topics,
        materials=materials,
        stats={
            "users": total_users,
            "subjects": len(subjects),
            "topics": len(topics),
            "materials": len(materials),
            "chunks": total_chunks,
            "quizzes": total_quizzes,
            "attempts": total_attempts,
        },
    )


@admin_bp.route("/admin/subjects/create", methods=["POST"])
@admin_required
def create_subject():
    name = request.form.get("name", "").strip()
    code = request.form.get("code", "").strip().upper()
    icon = request.form.get("icon", "book").strip()
    description = request.form.get("description", "").strip()

    if not name or not code:
        flash("Subject name and code are required.", "danger")
        return redirect(url_for("admin.admin_dashboard"))

    if Subject.query.filter((Subject.name == name) | (Subject.code == code)).first():
        flash("A subject with that name or code already exists.", "danger")
        return redirect(url_for("admin.admin_dashboard"))

    sub = Subject(name=name, code=code, icon=icon, description=description)
    db.session.add(sub)
    db.session.commit()
    flash(f"Subject '{name}' created successfully!", "success")
    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.route("/admin/topics/create", methods=["POST"])
@admin_required
def create_topic():
    subject_id = request.form.get("subject_id")
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()

    if not subject_id or not name:
        flash("Subject and topic name are required.", "danger")
        return redirect(url_for("admin.admin_dashboard"))

    topic = Topic(subject_id=int(subject_id), name=name, description=description)
    db.session.add(topic)
    db.session.commit()
    flash(f"Topic '{name}' created successfully!", "success")
    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.route("/admin/materials/create", methods=["POST"])
@admin_required
def create_material():
    subject_id = request.form.get("subject_id")
    topic_id = request.form.get("topic_id")
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    summary = request.form.get("summary", "").strip()

    # Check for file upload
    uploaded_file = request.files.get("file")
    if uploaded_file and uploaded_file.filename:
        try:
            file_content = uploaded_file.read().decode("utf-8", errors="ignore")
            if not content:
                content = file_content
            if not title:
                title = uploaded_file.filename.rsplit(".", 1)[0]
        except Exception as exc:
            flash(f"Error reading uploaded file: {exc}", "danger")
            return redirect(url_for("admin.admin_dashboard"))

    if not subject_id or not title or not content:
        flash("Subject, title, and content/file are required.", "danger")
        return redirect(url_for("admin.admin_dashboard"))

    topic_id_val = int(topic_id) if topic_id and topic_id.isdigit() else None

    mat = StudyMaterial(
        subject_id=int(subject_id),
        topic_id=topic_id_val,
        title=title,
        content=content,
        summary=summary or content[:200] + "...",
        file_type="upload" if uploaded_file and uploaded_file.filename else "note",
    )
    db.session.add(mat)
    db.session.commit()

    # Index material chunks for RAG
    RAGEngine.index_material(mat.id, content)

    flash(f"Study Material '{title}' created and indexed into RAG chunks successfully!", "success")
    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.route("/admin/materials/<int:material_id>/delete", methods=["POST"])
@admin_required
def delete_material(material_id):
    mat = StudyMaterial.query.get_or_404(material_id)
    title = mat.title
    db.session.delete(mat)
    db.session.commit()
    flash(f"Study material '{title}' deleted.", "info")
    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.route("/admin/reindex-all", methods=["POST"])
@admin_required
def reindex_all():
    materials = StudyMaterial.query.all()
    for mat in materials:
        RAGEngine.index_material(mat.id, mat.content)
    flash(f"Successfully re-indexed {len(materials)} study guides into RAG vector chunks.", "success")
    return redirect(url_for("admin.admin_dashboard"))
