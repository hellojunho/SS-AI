from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("user_id"), UniqueConstraint("email"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(50), nullable=False)
    user_name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="general")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_logined: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    token: Mapped[int] = mapped_column(Integer, default=0)

    chat_records = relationship("ChatRecord", back_populates="user")
    chat_summaries = relationship("ChatSummary", back_populates="user")
    quizzes = relationship("Quiz", back_populates="user")


class ChatRecord(Base):
    __tablename__ = "chat_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chat_records")


class ChatSummary(Base):
    __tablename__ = "chat_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    summary_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chat_summaries")


class Quiz(Base):
    __tablename__ = "quizzes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    link: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    tried_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    solved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user = relationship("User", back_populates="quizzes")
    questions = relationship(
        "QuizQuestion",
        back_populates="quiz",
        cascade="all, delete-orphan",
    )


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quiz_id: Mapped[int] = mapped_column(Integer, ForeignKey("quizzes.id"))
    question: Mapped[str] = mapped_column(Text, nullable=False)
    choices: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    correct: Mapped[str] = mapped_column(Text, nullable=False)
    wrong: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    reference: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    quiz = relationship("Quiz", back_populates="questions")
    correct_entries = relationship(
        "QuizCorrect",
        back_populates="question",
        cascade="all, delete-orphan",
    )
    wrong_entries = relationship(
        "QuizWrong",
        back_populates="question",
        cascade="all, delete-orphan",
    )
    answers = relationship(
        "QuizAnswer",
        back_populates="question",
        cascade="all, delete-orphan",
    )


class QuizCorrect(Base):
    __tablename__ = "quiz_corrects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quiz_id: Mapped[int] = mapped_column(Integer, ForeignKey("quizzes.id"))
    quiz_question_id: Mapped[int] = mapped_column(Integer, ForeignKey("quiz_questions.id"))
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    quiz = relationship("Quiz")
    question = relationship("QuizQuestion", back_populates="correct_entries")


class QuizWrong(Base):
    __tablename__ = "quiz_wrongs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quiz_id: Mapped[int] = mapped_column(Integer, ForeignKey("quizzes.id"))
    quiz_question_id: Mapped[int] = mapped_column(Integer, ForeignKey("quiz_questions.id"))
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    quiz = relationship("Quiz")
    question = relationship("QuizQuestion", back_populates="wrong_entries")


class QuizAnswer(Base):
    __tablename__ = "quiz_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quiz_question_id: Mapped[int] = mapped_column(Integer, ForeignKey("quiz_questions.id"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    is_wrong: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    question = relationship("QuizQuestion", back_populates="answers")
    user = relationship("User")


class WrongQuestion(Base):
    __tablename__ = "wrong_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quiz_question_id: Mapped[int] = mapped_column(Integer, ForeignKey("quiz_questions.id"))
    question_creator_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    solver_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    correct_answer: Mapped[str] = mapped_column(Text, nullable=False)
    wrong_answer: Mapped[str] = mapped_column(Text, nullable=False)
    reference_link: Mapped[str] = mapped_column(Text, nullable=False)
    user_answers: Mapped[str] = mapped_column(Text, nullable=False)
    last_solved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    question = relationship("QuizQuestion")
