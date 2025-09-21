"""
SQLAlchemy models for HireLens
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="recruiter")  # recruiter, student, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    resumes = relationship("Resume", back_populates="user")
    jobs = relationship("Job", back_populates="user")

class Job(Base):
    """Job Description model"""
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255))
    description = Column(Text, nullable=False)
    requirements = Column(Text)
    skills_required = Column(JSON)  # List of required skills
    skills_preferred = Column(JSON)  # List of preferred skills
    experience_level = Column(String(50))  # Entry, Mid, Senior
    employment_type = Column(String(50))  # Full-time, Part-time, Contract
    salary_range = Column(String(100))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="jobs")
    evaluations = relationship("Evaluation", back_populates="job")

class Resume(Base):
    """Resume model"""
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    file_type = Column(String(10), nullable=False)  # pdf, docx
    
    # Parsed content
    raw_text = Column(Text)
    skills = Column(JSON)  # List of extracted skills
    education = Column(JSON)  # Education details
    experience = Column(JSON)  # Work experience
    projects = Column(JSON)  # Projects
    certifications = Column(JSON)  # Certifications
    contact_info = Column(JSON)  # Contact information
    
    # Metadata
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="resumes")
    evaluations = relationship("Evaluation", back_populates="resume")

class Evaluation(Base):
    """Resume evaluation results"""
    __tablename__ = "evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    
    # Scores
    overall_score = Column(Float, nullable=False)  # 0-100
    hard_match_score = Column(Float)  # 0-100
    soft_match_score = Column(Float)  # 0-100
    
    # Verdict
    verdict = Column(String(20), nullable=False)  # High, Medium, Low
    
    # Detailed results
    matched_skills = Column(JSON)  # List of matched skills
    missing_skills = Column(JSON)  # List of missing skills
    skill_coverage = Column(Float)  # Percentage of skills covered
    
    # Feedback
    feedback = Column(Text)  # LLM-generated feedback
    improvement_suggestions = Column(JSON)  # List of suggestions
    strengths = Column(JSON)  # List of strengths
    weaknesses = Column(JSON)  # List of weaknesses
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    resume = relationship("Resume", back_populates="evaluations")
    job = relationship("Job", back_populates="evaluations")

class FeedbackHistory(Base):
    """Track feedback and improvements over time"""
    __tablename__ = "feedback_history"
    
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    
    # Version tracking
    version_number = Column(Integer, nullable=False)
    previous_score = Column(Float)
    current_score = Column(Float, nullable=False)
    score_improvement = Column(Float)
    
    # Feedback details
    feedback_text = Column(Text, nullable=False)
    improvements_made = Column(JSON)  # List of improvements
    new_skills_added = Column(JSON)  # List of new skills
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    resume = relationship("Resume")
    job = relationship("Job")
