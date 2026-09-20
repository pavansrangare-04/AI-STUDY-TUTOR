from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, g
from auth import login_required
from models import db, Conversation, Message, Subject
from ai_provider import AIProvider

chat_bp = Blueprint("chat", __name__)


def group_conversations_by_date(conversations):
    """Categorize conversations into Today, Yesterday, Previous 7 Days, and Older."""
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)
    yesterday_start = today_start - timedelta(days=1)
    seven_days_ago = today_start - timedelta(days=7)

    grouped = {
        "Today": [],
        "Yesterday": [],
        "Previous 7 Days": [],
        "Older": [],
    }

    for conv in conversations:
        dt = conv.updated_at or conv.created_at
        if dt >= today_start:
            grouped["Today"].append(conv)
        elif dt >= yesterday_start:
            grouped["Yesterday"].append(conv)
        elif dt >= seven_days_ago:
            grouped["Previous 7 Days"].append(conv)
        else:
            grouped["Older"].append(conv)

    return {k: v for k, v in grouped.items() if v}


@chat_bp.route("/chat")
@chat_bp.route("/chat/<int:conversation_id>")
@login_required
def chat_view(conversation_id=None):
    user = g.user
    conversations = (
        Conversation.query.filter_by(user_id=user.id, is_archived=False)
        .order_by(Conversation.updated_at.desc())
        .all()
    )

    current_conv = None
    if conversation_id:
        current_conv = Conversation.query.filter_by(id=conversation_id, user_id=user.id).first()

    if not current_conv and conversations:
        current_conv = conversations[0]

    messages = []
    if current_conv:
        messages = current_conv.messages.all()

    grouped_chats = group_conversations_by_date(conversations)
    subjects = Subject.query.all()
    ai_status = AIProvider.get_active_provider_info()

    return render_template(
        "chat.html",
        user=user,
        conversations=conversations,
        grouped_chats=grouped_chats,
        current_conversation=current_conv,
        messages=messages,
        subjects=subjects,
        ai_status=ai_status,
    )


@chat_bp.route("/api/chat/new", methods=["POST"])
@login_required
def new_conversation():
    data = request.get_json() or {}
    subject_id = data.get("subject_id")
    title = data.get("title", "New Conversation")

    conv = Conversation(
        user_id=g.user.id,
        subject_id=subject_id if subject_id else None,
        title=title,
    )
    db.session.add(conv)
    db.session.commit()

    return jsonify({
        "success": True,
        "id": conv.id,
        "title": conv.title,
        "created_at": conv.created_at.strftime("%b %d, %H:%M"),
    })


@chat_bp.route("/api/chat/<int:conversation_id>/message", methods=["POST"])
@login_required
def send_message(conversation_id):
    conv = Conversation.query.filter_by(id=conversation_id, user_id=g.user.id).first_or_404()
    data = request.get_json() or {}
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"success": False, "error": "Question cannot be empty."}), 400

    # 1. Save User Message
    user_msg = Message(
        conversation_id=conv.id,
        sender="user",
        content=question,
    )
    db.session.add(user_msg)
    db.session.flush()

    # If first message, auto-generate chat title from question
    if conv.messages.count() <= 1:
        words = question.split()
        short_title = " ".join(words[:6])
        if len(words) > 6:
            short_title += "..."
        conv.title = short_title

    # 2. Retrieve history context
    history = conv.messages.all()

    # 3. Call AI Provider
    result = AIProvider.generate_response(
        question=question,
        conversation_history=history,
        subject_id=conv.subject_id,
        user_level=g.user.learning_level,
        user_style=g.user.explanation_style,
    )

    # 4. Save Assistant Message
    assistant_msg = Message(
        conversation_id=conv.id,
        sender="assistant",
        content=result.get("content") or "No response generated. Please try again.",
        is_grounded=result.get("is_grounded", False),
    )
    assistant_msg.sources = result["sources"]
    db.session.add(assistant_msg)

    conv.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "success": True,
        "message_id": assistant_msg.id,
        "content": assistant_msg.content,
        "sources": assistant_msg.sources,
        "is_grounded": assistant_msg.is_grounded,
        "provider": result["provider"],
        "model": result["model"],
        "suggested_followups": result["suggested_followups"],
        "chat_title": conv.title,
    })


@chat_bp.route("/api/chat/<int:conversation_id>/rename", methods=["POST"])
@login_required
def rename_conversation(conversation_id):
    conv = Conversation.query.filter_by(id=conversation_id, user_id=g.user.id).first_or_404()
    data = request.get_json() or {}
    new_title = data.get("title", "").strip()

    if not new_title:
        return jsonify({"success": False, "error": "Title cannot be empty."}), 400

    conv.title = new_title[:180]
    db.session.commit()
    return jsonify({"success": True, "title": conv.title})


@chat_bp.route("/api/chat/<int:conversation_id>/delete", methods=["POST", "DELETE"])
@login_required
def delete_conversation(conversation_id):
    conv = Conversation.query.filter_by(id=conversation_id, user_id=g.user.id).first_or_404()
    db.session.delete(conv)
    db.session.commit()
    return jsonify({"success": True})


@chat_bp.route("/api/chat/<int:conversation_id>/feedback", methods=["POST"])
@login_required
def message_feedback(conversation_id):
    Conversation.query.filter_by(id=conversation_id, user_id=g.user.id).first_or_404()
    data = request.get_json() or {}
    msg_id = data.get("message_id")
    rating = data.get("rating")  # "helpful", "unhelpful"

    msg = Message.query.filter_by(id=msg_id, conversation_id=conversation_id).first_or_404()
    msg.rating = rating
    db.session.commit()
    return jsonify({"success": True, "rating": msg.rating})


@chat_bp.route("/api/chat/search")
@login_required
def search_conversations():
    q = request.args.get("q", "").strip().lower()
    if not q:
        return jsonify({"results": []})

    user_convs = Conversation.query.filter_by(user_id=g.user.id).all()
    results = []
    for conv in user_convs:
        # Match title
        if q in conv.title.lower():
            results.append({
                "id": conv.id,
                "title": conv.title,
                "match_type": "title",
                "updated_at": conv.updated_at.strftime("%b %d"),
            })
            continue

        # Match recent messages
        for msg in conv.messages:
            if q in msg.content.lower():
                snippet = msg.content
                idx = snippet.lower().find(q)
                start = max(0, idx - 40)
                end = min(len(snippet), idx + 80)
                results.append({
                    "id": conv.id,
                    "title": conv.title,
                    "match_type": "message",
                    "snippet": "..." + snippet[start:end] + "...",
                    "updated_at": conv.updated_at.strftime("%b %d"),
                })
                break

    return jsonify({"results": results[:10]})
