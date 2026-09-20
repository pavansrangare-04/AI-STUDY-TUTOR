from datetime import datetime
import json
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="student")  # "student", "admin"
    learning_level = db.Column(db.String(20), default="intermediate")  # "beginner", "intermediate", "advanced"
    explanation_style = db.Column(db.String(30), default="detailed")  # "concise", "detailed", "step_by_step"
    theme_preference = db.Column(db.String(10), default="dark")  # "dark", "light"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    conversations = db.relationship("Conversation", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    quiz_attempts = db.relationship("QuizAttempt", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "learning_level": self.learning_level,
            "explanation_style": self.explanation_style,
            "theme_preference": self.theme_preference,
        }


class Subject(db.Model):
    __tablename__ = "subjects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    icon = db.Column(db.String(40), default="cpu")
    description = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    topics = db.relationship("Topic", backref="subject", lazy="dynamic", cascade="all, delete-orphan")
    materials = db.relationship("StudyMaterial", backref="subject", lazy="dynamic", cascade="all, delete-orphan")
    quizzes = db.relationship("Quiz", backref="subject", lazy="dynamic", cascade="all, delete-orphan")
    conversations = db.relationship("Conversation", backref="subject", lazy="dynamic")


class Topic(db.Model):
    __tablename__ = "topics"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, default="")
    order = db.Column(db.Integer, default=0)

    materials = db.relationship("StudyMaterial", backref="topic", lazy="dynamic")
    quizzes = db.relationship("Quiz", backref="topic", lazy="dynamic")


class StudyMaterial(db.Model):
    __tablename__ = "study_materials"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey("topics.id"), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text, default="")
    file_type = db.Column(db.String(20), default="note")  # "note", "upload", "guide"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    chunks = db.relationship("MaterialChunk", backref="material", lazy="dynamic", cascade="all, delete-orphan")


class MaterialChunk(db.Model):
    __tablename__ = "material_chunks"

    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey("study_materials.id"), nullable=False)
    chunk_index = db.Column(db.Integer, default=0)
    chunk_text = db.Column(db.Text, nullable=False)
    keywords = db.Column(db.Text, default="")


class Conversation(db.Model):
    __tablename__ = "conversations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=True)
    title = db.Column(db.String(200), nullable=False, default="New Conversation")
    is_archived = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = db.relationship(
        "Message",
        backref="conversation",
        lazy="dynamic",
        order_by="Message.created_at.asc()",
        cascade="all, delete-orphan",
    )


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id"), nullable=False)
    sender = db.Column(db.String(20), nullable=False)  # "user", "assistant"
    content = db.Column(db.Text, nullable=False)
    sources_json = db.Column(db.Text, default="[]")
    is_grounded = db.Column(db.Boolean, default=False)
    rating = db.Column(db.String(20), nullable=True)  # "helpful", "unhelpful"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def sources(self):
        try:
            return json.loads(self.sources_json or "[]")
        except Exception:
            return []

    @sources.setter
    def sources(self, value):
        self.sources_json = json.dumps(value or [])


class Quiz(db.Model):
    __tablename__ = "quizzes"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey("topics.id"), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    difficulty = db.Column(db.String(20), default="medium")  # "easy", "medium", "hard"
    time_limit_mins = db.Column(db.Integer, default=10)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    questions = db.relationship("QuizQuestion", backref="quiz", lazy="dynamic", cascade="all, delete-orphan")
    attempts = db.relationship("QuizAttempt", backref="quiz", lazy="dynamic", cascade="all, delete-orphan")


class QuizQuestion(db.Model):
    __tablename__ = "quiz_questions"

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id"), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(255), nullable=False)
    option_b = db.Column(db.String(255), nullable=False)
    option_c = db.Column(db.String(255), nullable=False)
    option_d = db.Column(db.String(255), nullable=False)
    correct_option = db.Column(db.String(2), nullable=False)  # "A", "B", "C", "D"
    explanation = db.Column(db.Text, nullable=False)


class QuizAttempt(db.Model):
    __tablename__ = "quiz_attempts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id"), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    accuracy_pct = db.Column(db.Float, nullable=False)
    answers_json = db.Column(db.Text, default="{}")
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def answers(self):
        try:
            return json.loads(self.answers_json or "{}")
        except Exception:
            return {}

    @answers.setter
    def answers(self, value):
        self.answers_json = json.dumps(value or {})
