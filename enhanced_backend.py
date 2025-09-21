"""
Enhanced HireLens Backend with Role-Based Access and Advanced Features
"""
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from typing import List, Optional, Dict, Any
import os
import shutil
from pathlib import Path
import logging
from datetime import datetime, timedelta
import json
import re
import pdfplumber
import docx2txt
from rapidfuzz import fuzz
import openai
import google.generativeai as genai
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
import uvicorn
import plotly.graph_objects as go
import plotly.express as px
from collections import Counter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="HireLens Enhanced API",
    description="AI-Powered Resume Relevance Check System with Role-Based Access",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Database setup
DATABASE_URL = "sqlite:///./hirelens_enhanced.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing - suppress bcrypt version warnings
import warnings
warnings.filterwarnings("ignore", message=".*bcrypt.*")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = "your-super-secret-jwt-key-here-make-it-very-long-and-random-enhanced"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Enhanced Database Models with Relationships
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="student")  # student or recruiter
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    jobs = relationship("Job", back_populates="recruiter")
    resumes = relationship("Resume", back_populates="student")
    evaluations = relationship("Evaluation", back_populates="user")

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255))
    description = Column(Text, nullable=False)
    requirements = Column(Text)
    skills_required = Column(JSON)
    skills_preferred = Column(JSON)
    recruiter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    # Enhanced fields for JD upload
    role_title = Column(String(255))
    description = Column(Text)
    responsibilities = Column(JSON)  # List of responsibilities
    skills = Column(JSON)  # {must_have: [], nice_to_have: []}
    qualification = Column(Text)
    experience = Column(String(255))
    location = Column(String(255))
    job_type = Column(String(100))  # full-time, internship, etc.
    duration = Column(String(100))
    compensation = Column(String(255))
    batch_eligibility = Column(String(255))
    jd_text = Column(Text)  # Full JD text
    jd_filename = Column(String(255))  # Original JD filename
    
    # Relationships
    recruiter = relationship("User", back_populates="jobs")
    evaluations = relationship("Evaluation", back_populates="job")

class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    file_type = Column(String(10), nullable=False)
    raw_text = Column(Text)
    skills = Column(JSON)
    education = Column(JSON)
    experience = Column(JSON)
    projects = Column(JSON)
    certifications = Column(JSON)
    contact_info = Column(JSON)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    version = Column(Integer, default=1)  # Version tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    is_latest = Column(Boolean, default=True)  # Mark latest version
    
    # Relationships
    student = relationship("User", back_populates="resumes")
    evaluations = relationship("Evaluation", back_populates="resume")

class Evaluation(Base):
    __tablename__ = "evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Who requested evaluation
    overall_score = Column(Float, nullable=False)
    verdict = Column(String(20), nullable=False)  # High/Medium/Low
    hard_match_score = Column(Float)
    soft_match_score = Column(Float)
    matched_skills = Column(JSON)
    missing_skills = Column(JSON)
    skill_coverage = Column(Float)
    feedback = Column(JSON)  # LLM-generated feedback
    verdict_explanation = Column(Text)  # LLM explanation of verdict
    anomaly_flags = Column(JSON)  # Detected anomalies
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    resume = relationship("Resume", back_populates="evaluations")
    job = relationship("Job", back_populates="evaluations")
    user = relationship("User", back_populates="evaluations")

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "student"  # Default to student

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    role: str

class JobCreate(BaseModel):
    title: str
    company: str
    description: str
    location: Optional[str] = None
    requirements: Optional[str] = None
    skills_required: Optional[List[str]] = []
    skills_preferred: Optional[List[str]] = []

class JobResponse(BaseModel):
    id: int
    title: str
    company: str
    location: Optional[str]
    description: str
    requirements: Optional[str]
    skills_required: Optional[List[str]]
    skills_preferred: Optional[List[str]]
    created_at: datetime
    recruiter_id: int

class ResumeResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_type: str
    version: int
    is_latest: bool
    created_at: datetime
    student_id: int

class EvaluationResponse(BaseModel):
    id: int
    resume_id: int
    job_id: int
    overall_score: float
    verdict: str
    hard_match_score: Optional[float]
    soft_match_score: Optional[float]
    matched_skills: Optional[List[str]]
    missing_skills: Optional[List[str]]
    skill_coverage: Optional[float]
    feedback: Optional[Dict[str, Any]]
    verdict_explanation: Optional[str]
    anomaly_flags: Optional[List[str]]
    created_at: datetime

class MultiJobMatchResponse(BaseModel):
    resume_id: int
    matches: List[Dict[str, Any]]  # job_id, score, verdict, job_title, company

class AnalyticsResponse(BaseModel):
    job_id: int
    total_applications: int
    high_fit_count: int
    medium_fit_count: int
    low_fit_count: int
    average_score: float
    skill_gaps: Dict[str, int]
    top_skills_matched: List[Dict[str, Any]]
    improvement_trends: List[Dict[str, Any]]

# Utility functions
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        if username is None or user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

def require_role(required_role: str):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role}"
            )
        return current_user
    return role_checker

# File processing functions
def extract_text_from_file(file_path: str, file_type: str) -> str:
    """Extract text from PDF or DOCX files"""
    try:
        if file_type.lower() == 'pdf':
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                return text
        elif file_type.lower() in ['docx', 'doc']:
            return docx2txt.process(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {e}")
        return ""

def extract_skills_from_text(text: str) -> List[str]:
    """Extract skills from resume text using simple keyword matching"""
    # Common technical skills
    skill_keywords = [
        'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node.js', 'express',
        'django', 'flask', 'fastapi', 'spring', 'spring boot', 'mysql', 'postgresql',
        'mongodb', 'redis', 'docker', 'kubernetes', 'aws', 'azure', 'gcp',
        'machine learning', 'ai', 'data science', 'pandas', 'numpy', 'tensorflow',
        'pytorch', 'scikit-learn', 'git', 'github', 'gitlab', 'jenkins', 'ci/cd',
        'rest api', 'graphql', 'microservices', 'agile', 'scrum', 'devops'
    ]
    
    found_skills = []
    text_lower = text.lower()
    
    for skill in skill_keywords:
        if skill in text_lower:
            found_skills.append(skill.title())
    
    return found_skills

def calculate_hard_match_score(resume_text: str, job_description: str) -> float:
    """Calculate hard match score using fuzzy matching"""
    try:
        # Extract skills from both texts
        resume_skills = extract_skills_from_text(resume_text)
        job_skills = extract_skills_from_text(job_description)
        
        if not job_skills:
            return 0.0
        
        # Calculate fuzzy match scores
        total_score = 0
        for job_skill in job_skills:
            best_match = 0
            for resume_skill in resume_skills:
                match_score = fuzz.ratio(job_skill.lower(), resume_skill.lower())
                best_match = max(best_match, match_score)
            total_score += best_match
        
        return (total_score / len(job_skills)) / 100.0
    except Exception as e:
        logger.error(f"Error calculating hard match score: {e}")
        return 0.0

def calculate_soft_match_score(resume_text: str, job_description: str) -> float:
    """Calculate semantic similarity score"""
    try:
        # Simple semantic matching using text similarity
        # In a real implementation, you'd use embeddings
        similarity = fuzz.ratio(resume_text.lower(), job_description.lower())
        return similarity / 100.0
    except Exception as e:
        logger.error(f"Error calculating soft match score: {e}")
        return 0.0

def generate_llm_feedback(resume_text: str, job_description: str, score: float, verdict: str) -> Dict[str, Any]:
    """Generate LLM-based feedback and suggestions"""
    try:
        # Simulate LLM feedback generation
        feedback = {
            "overall_feedback": f"Your resume shows a {verdict.lower()} fit for this position with a score of {score:.1f}/100.",
            "strengths": [
                "Strong technical background",
                "Relevant project experience",
                "Good educational foundation"
            ],
            "weaknesses": [
                "Missing some key skills mentioned in job requirements",
                "Could benefit from more specific examples",
                "Consider adding relevant certifications"
            ],
            "missing_skills": extract_skills_from_text(job_description)[:5],
            "improvement_suggestions": [
                "Highlight relevant projects that match job requirements",
                "Add specific metrics and achievements",
                "Consider taking online courses for missing skills",
                "Tailor your resume for each application",
                "Include relevant keywords from the job description"
            ],
            "verdict_explanation": f"The {verdict} verdict is based on a {score:.1f}/100 score, indicating {'strong' if score > 70 else 'moderate' if score > 40 else 'limited'} alignment with job requirements."
        }
        return feedback
    except Exception as e:
        logger.error(f"Error generating LLM feedback: {e}")
        return {"error": "Could not generate feedback"}

def detect_anomalies(resume_text: str) -> List[str]:
    """Detect potential anomalies in resume"""
    anomalies = []
    
    # Check for missing education section
    if not any(word in resume_text.lower() for word in ['education', 'degree', 'university', 'college', 'bachelor', 'master', 'phd']):
        anomalies.append("Missing education section")
    
    # Check for unrealistic claims (simple heuristics)
    if 'nobel prize' in resume_text.lower():
        anomalies.append("Unrealistic achievement claim detected")
    
    if len(resume_text.split()) < 100:
        anomalies.append("Resume appears too short")
    
    return anomalies

def parse_jd_with_spacy(jd_text: str) -> Dict[str, Any]:
    """Enhanced Job Description parsing with NLP"""
    try:
        jd_lower = jd_text.lower()
        
        # 1. Extract Job Title
        title_patterns = [
            r'(?:job title|position|role|title)[:\s]+([^.\n]+)',
            r'(?:looking for|seeking|hiring)[:\s]+([^.\n]+)',
            r'^([^.\n]+(?:engineer|developer|analyst|manager|specialist|consultant|intern|trainee))',
            r'^([^.\n]+(?:data scientist|software engineer|full stack|frontend|backend))',
        ]
        
        title = "Software Engineer"  # Default
        for pattern in title_patterns:
            match = re.search(pattern, jd_text, re.IGNORECASE | re.MULTILINE)
            if match:
                title = match.group(1).strip()
                break
        
        # 2. Extract Responsibilities
        responsibilities = []
        responsibility_sections = [
            r'(?:what you will do|responsibilities|key responsibilities|job responsibilities)[:\s]*\n([^#\n]+)',
            r'(?:role and responsibilities|your role)[:\s]*\n([^#\n]+)',
        ]
        
        for pattern in responsibility_sections:
            match = re.search(pattern, jd_text, re.IGNORECASE | re.DOTALL)
            if match:
                resp_text = match.group(1)
                # Extract bullet points
                bullets = re.findall(r'[•\-\*]\s*([^•\-\*\n]+)', resp_text)
                responsibilities.extend([bullet.strip() for bullet in bullets if bullet.strip()])
        
        # 3. Extract Skills with NER-like approach
        must_have_skills = []
        nice_to_have_skills = []
        
        # Comprehensive skill database
        all_skills = [
            # Programming Languages
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust', 'php', 'ruby',
            # Web Technologies
            'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask', 'fastapi', 'spring', 'spring boot',
            # Databases
            'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'cassandra', 'sqlite',
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git', 'github', 'gitlab', 'ci/cd',
            # Data Science & ML
            'machine learning', 'ai', 'data science', 'pandas', 'numpy', 'tensorflow', 'pytorch', 'scikit-learn',
            'spark', 'hadoop', 'kafka', 'databricks', 'tableau', 'power bi', 'matplotlib', 'seaborn',
            # Other Technologies
            'rest api', 'graphql', 'microservices', 'agile', 'scrum', 'devops', 'kubernetes', 'terraform',
            'ansible', 'prometheus', 'grafana', 'elk stack', 'splunk'
        ]
        
        # Look for must-have vs nice-to-have indicators
        must_have_indicators = ['required', 'must have', 'essential', 'mandatory', 'necessary', 'should have']
        nice_to_have_indicators = ['preferred', 'nice to have', 'bonus', 'plus', 'advantage', 'good to have']
        
        for skill in all_skills:
            if skill in jd_lower:
                # Check context around the skill
                skill_context = jd_lower[max(0, jd_lower.find(skill)-100):jd_lower.find(skill)+100]
                
                if any(indicator in skill_context for indicator in must_have_indicators):
                    must_have_skills.append(skill.title())
                elif any(indicator in skill_context for indicator in nice_to_have_indicators):
                    nice_to_have_skills.append(skill.title())
                else:
                    # Default to must-have if no clear indicator
                    must_have_skills.append(skill.title())
        
        # 4. Extract Qualifications
        qualification_patterns = [
            r'(?:qualification|education|degree|eligibility criteria)[:\s]+([^.\n]+)',
            r'(?:bachelor|master|phd|diploma|b\.tech|be|m\.tech|me)[^.\n]*',
            r'(?:computer science|mechanical engineering|electrical engineering|it|ece)[^.\n]*',
        ]
        
        qualification = None
        for pattern in qualification_patterns:
            match = re.search(pattern, jd_lower)
            if match:
                qualification = match.group(1).strip() if match.groups() else match.group(0).strip()
                break
        
        # 5. Extract Experience
        experience_patterns = [
            r'(\d+\+?\s*years?\s*experience)',
            r'(?:at least|minimum|maximum)\s*(\d+\+?\s*years?)',
            r'(\d+[-–]\d+\s*years?)',
            r'(?:fresher|entry level|0\s*years?)',
        ]
        
        experience = None
        for pattern in experience_patterns:
            match = re.search(pattern, jd_lower)
            if match:
                experience = match.group(1).strip() if match.groups() else match.group(0).strip()
                break
        
        # 6. Extract Location
        location_patterns = [
            r'(?:location|based in|work from|workplace)[:\s]+([^.\n]+)',
            r'(?:remote|hybrid|onsite|work from home)',
            r'([A-Z][a-z]+(?:\s*,\s*[A-Z][a-z]+)*)',  # City, State format
            r'(?:pune|bangalore|mumbai|delhi|hyderabad|chennai|kolkata|gurgaon|noida)',
        ]
        
        location = None
        for pattern in location_patterns:
            match = re.search(pattern, jd_text, re.IGNORECASE)
            if match:
                location = match.group(1).strip() if match.groups() else match.group(0).strip()
                break
        
        # 7. Extract Job Type
        job_type_patterns = [
            r'(?:job type|employment type|position type)[:\s]+([^.\n]+)',
            r'(?:full[-\s]?time|part[-\s]?time|internship|contract|permanent|temporary)',
            r'(?:fresher|entry level|senior|junior|mid[-\s]?level)',
        ]
        
        job_type = None
        for pattern in job_type_patterns:
            match = re.search(pattern, jd_lower)
            if match:
                job_type = match.group(1).strip() if match.groups() else match.group(0).strip()
                break
        
        # 8. Extract Duration
        duration_patterns = [
            r'(?:duration|period|tenure)[:\s]+([^.\n]+)',
            r'(\d+\s*months?)',
            r'(\d+\s*years?)',
        ]
        
        duration = None
        for pattern in duration_patterns:
            match = re.search(pattern, jd_lower)
            if match:
                duration = match.group(1).strip() if match.groups() else match.group(0).strip()
                break
        
        # 9. Extract Compensation
        compensation_patterns = [
            r'(?:salary|compensation|stipend|package)[:\s]+([^.\n]+)',
            r'(?:₹|rs\.?|rupees?)\s*[\d,]+(?:\s*per\s*month|\s*per\s*annum|\s*lpa|\s*pa)?',
            r'(\d+\s*lpa|\d+\s*per\s*annum)',
        ]
        
        compensation = None
        for pattern in compensation_patterns:
            match = re.search(pattern, jd_text, re.IGNORECASE)
            if match:
                compensation = match.group(1).strip() if match.groups() else match.group(0).strip()
                break
        
        # 10. Extract Batch Eligibility
        batch_patterns = [
            r'(?:batch|year|passing year|graduation year)[:\s]+([^.\n]+)',
            r'(?:202[0-9]|202[0-9]\s*and\s*earlier|202[0-9]\s*and\s*later)',
        ]
        
        batch_eligibility = None
        for pattern in batch_patterns:
            match = re.search(pattern, jd_lower)
            if match:
                batch_eligibility = match.group(1).strip() if match.groups() else match.group(0).strip()
                break
        
        # 11. Extract Description (first few sentences)
        description = jd_text[:500] + "..." if len(jd_text) > 500 else jd_text
        
        return {
            "title": title,
            "description": description,
            "responsibilities": responsibilities[:10],  # Limit to top 10
            "skills": {
                "must_have": must_have_skills[:15],  # Limit to top 15
                "nice_to_have": nice_to_have_skills[:15]
            },
            "qualification": qualification,
            "experience": experience,
            "location": location,
            "job_type": job_type,
            "duration": duration,
            "compensation": compensation,
            "batch_eligibility": batch_eligibility
        }
        
    except Exception as e:
        logger.error(f"Error parsing JD: {e}")
        return {
            "title": "Software Engineer",
            "description": jd_text[:500] + "..." if len(jd_text) > 500 else jd_text,
            "responsibilities": [],
            "skills": {"must_have": [], "nice_to_have": []},
            "qualification": None,
            "experience": None,
            "location": None,
            "job_type": None,
            "duration": None,
            "compensation": None,
            "batch_eligibility": None
        }

# API Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "HireLens Enhanced API is running"}

# Authentication endpoints
@app.post("/auth/register", response_model=Token)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    existing_user = db.query(User).filter(
        (User.email == user.email) | (User.username == user.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    access_token = create_access_token(data={"sub": user.username, "user_id": db_user.id})
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_id": db_user.id,
        "role": db_user.role
    }

@app.post("/auth/login", response_model=Token)
async def login(user: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    db_user = db.query(User).filter(User.username == user.username).first()
    
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(data={"sub": user.username, "user_id": db_user.id})
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_id": db_user.id,
        "role": db_user.role
    }

# Student endpoints
@app.post("/resumes", response_model=ResumeResponse)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("student")),
    db: Session = Depends(get_db)
):
    """Upload a new resume version"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check file type
    file_type = file.filename.split('.')[-1].lower()
    if file_type not in ['pdf', 'docx', 'doc']:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed")
    
    # Create upload directory
    upload_dir = Path("uploads/resumes")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{current_user.id}_{timestamp}_{file.filename}"
    file_path = upload_dir / filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Extract text
    raw_text = extract_text_from_file(str(file_path), file_type)
    skills = extract_skills_from_text(raw_text)
    
    # Mark previous versions as not latest
    db.query(Resume).filter(
        Resume.student_id == current_user.id,
        Resume.is_latest == True
    ).update({"is_latest": False})
    
    # Get next version number
    latest_version = db.query(Resume).filter(
        Resume.student_id == current_user.id
    ).order_by(Resume.version.desc()).first()
    next_version = (latest_version.version + 1) if latest_version else 1
    
    # Create resume record
    db_resume = Resume(
        filename=filename,
        original_filename=file.filename,
        file_path=str(file_path),
        file_size=file_path.stat().st_size,
        file_type=file_type,
        raw_text=raw_text,
        skills=skills,
        student_id=current_user.id,
        version=next_version,
        is_latest=True
    )
    
    db.add(db_resume)
    db.commit()
    db.refresh(db_resume)
    
    return ResumeResponse(
        id=db_resume.id,
        filename=db_resume.filename,
        original_filename=db_resume.original_filename,
        file_type=db_resume.file_type,
        version=db_resume.version,
        is_latest=db_resume.is_latest,
        created_at=db_resume.created_at,
        student_id=db_resume.student_id
    )

@app.get("/jobs", response_model=List[JobResponse])
async def get_all_jobs(db: Session = Depends(get_db)):
    """Get all active job postings (accessible by students)"""
    jobs = db.query(Job).filter(Job.is_active == True).all()
    return [
        JobResponse(
            id=job.id,
            title=job.title,
            company=job.company,
            location=job.location,
            description=job.description,
            requirements=job.requirements,
            skills_required=job.skills_required,
            skills_preferred=job.skills_preferred,
            created_at=job.created_at,
            recruiter_id=job.recruiter_id
        ) for job in jobs
    ]

@app.get("/resumes/my", response_model=List[ResumeResponse])
async def get_my_resumes(
    current_user: User = Depends(require_role("student")),
    db: Session = Depends(get_db)
):
    """Get current student's resumes"""
    resumes = db.query(Resume).filter(Resume.student_id == current_user.id).all()
    
    return [
        ResumeResponse(
            id=resume.id,
            filename=resume.filename,
            original_filename=resume.original_filename,
            file_type=resume.file_type,
            version=resume.version,
            is_latest=resume.is_latest,
            created_at=resume.created_at,
            student_id=resume.student_id
        ) for resume in resumes
    ]

@app.get("/evaluations/my", response_model=List[EvaluationResponse])
async def get_my_evaluations(
    current_user: User = Depends(require_role("student")),
    db: Session = Depends(get_db)
):
    """Get evaluations for current student's resumes"""
    evaluations = db.query(Evaluation).join(Resume).filter(
        Resume.student_id == current_user.id
    ).all()
    
    return [
        EvaluationResponse(
            id=eval.id,
            resume_id=eval.resume_id,
            job_id=eval.job_id,
            overall_score=eval.overall_score,
            verdict=eval.verdict,
            hard_match_score=eval.hard_match_score,
            soft_match_score=eval.soft_match_score,
            matched_skills=eval.matched_skills,
            missing_skills=eval.missing_skills,
            skill_coverage=eval.skill_coverage,
            feedback=eval.feedback,
            verdict_explanation=eval.verdict_explanation,
            anomaly_flags=eval.anomaly_flags,
            created_at=eval.created_at
        ) for eval in evaluations
    ]

@app.get("/evaluations/multi-match/{resume_id}", response_model=MultiJobMatchResponse)
async def get_multi_job_matches(
    resume_id: int,
    current_user: User = Depends(require_role("student")),
    db: Session = Depends(get_db)
):
    """Get best job matches for a specific resume"""
    # Verify resume belongs to current user
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.student_id == current_user.id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Get all active jobs
    jobs = db.query(Job).filter(Job.is_active == True).all()
    matches = []
    
    for job in jobs:
        # Calculate scores
        hard_score = calculate_hard_match_score(resume.raw_text, job.description)
        soft_score = calculate_soft_match_score(resume.raw_text, job.description)
        overall_score = (hard_score * 0.6 + soft_score * 0.4) * 100
        
        # Determine verdict
        if overall_score >= 70:
            verdict = "High"
        elif overall_score >= 40:
            verdict = "Medium"
        else:
            verdict = "Low"
        
        matches.append({
            "job_id": job.id,
            "job_title": job.title,
            "company": job.company,
            "score": round(overall_score, 1),
            "verdict": verdict,
            "location": job.location
        })
    
    # Sort by score descending
    matches.sort(key=lambda x: x["score"], reverse=True)
    
    return MultiJobMatchResponse(
        resume_id=resume_id,
        matches=matches[:10]  # Top 10 matches
    )

# Recruiter endpoints
@app.post("/jobs", response_model=JobResponse)
async def create_job(
    job: JobCreate,
    current_user: User = Depends(require_role("recruiter")),
    db: Session = Depends(get_db)
):
    """Create a new job posting"""
    db_job = Job(
        title=job.title,
        company=job.company,
        location=job.location,
        description=job.description,
        requirements=job.requirements,
        skills_required=job.skills_required,
        skills_preferred=job.skills_preferred,
        recruiter_id=current_user.id
    )
    
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    
    return JobResponse(
        id=db_job.id,
        title=db_job.title,
        company=db_job.company,
        location=db_job.location,
        description=db_job.description,
        requirements=db_job.requirements,
        skills_required=db_job.skills_required,
        skills_preferred=db_job.skills_preferred,
        created_at=db_job.created_at,
        recruiter_id=db_job.recruiter_id
    )

@app.post("/jobs/upload", response_model=JobResponse)
async def upload_job_description(
    file: UploadFile = File(...),
    company: str = Form(...),
    current_user: User = Depends(require_role("recruiter")),
    db: Session = Depends(get_db)
):
    """Upload and parse a Job Description file"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file type
        file_type = file.filename.split('.')[-1].lower()
        if file_type not in ['pdf', 'docx', 'doc']:
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed")
        
        # Create upload directory
        upload_dir = Path("uploads/jobs")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{current_user.id}_{timestamp}_{file.filename}"
        file_path = upload_dir / filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Extract text from JD
        jd_text = extract_text_from_file(str(file_path), file_type)
        
        if not jd_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from the file")
        
        # Parse JD using enhanced NLP
        parsed_data = parse_jd_with_spacy(jd_text)
        
        # Create job record with enhanced fields
        db_job = Job(
            title=parsed_data["title"],
            company=company,
            location=parsed_data["location"],
            description=parsed_data["description"],
            requirements=parsed_data["qualification"],
            skills_required=parsed_data["skills"]["must_have"],
            skills_preferred=parsed_data["skills"]["nice_to_have"],
            recruiter_id=current_user.id,
            # Enhanced fields
            role_title=parsed_data["title"],
            responsibilities=parsed_data["responsibilities"],
            skills=parsed_data["skills"],
            qualification=parsed_data["qualification"],
            experience=parsed_data["experience"],
            job_type=parsed_data["job_type"],
            duration=parsed_data["duration"],
            compensation=parsed_data["compensation"],
            batch_eligibility=parsed_data["batch_eligibility"],
            jd_text=jd_text,
            jd_filename=file.filename
        )
        
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        
        return JobResponse(
            id=db_job.id,
            title=db_job.title,
            company=db_job.company,
            location=db_job.location,
            description=db_job.description,
            requirements=db_job.requirements,
            skills_required=db_job.skills_required,
            skills_preferred=db_job.skills_preferred,
            created_at=db_job.created_at,
            recruiter_id=db_job.recruiter_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading JD: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/jobs/my", response_model=List[JobResponse])
async def get_my_jobs(
    current_user: User = Depends(require_role("recruiter")),
    db: Session = Depends(get_db)
):
    """Get jobs posted by current recruiter"""
    jobs = db.query(Job).filter(Job.recruiter_id == current_user.id).all()
    return [
        JobResponse(
            id=job.id,
            title=job.title,
            company=job.company,
            location=job.location,
            description=job.description,
            requirements=job.requirements,
            skills_required=job.skills_required,
            skills_preferred=job.skills_preferred,
            created_at=job.created_at,
            recruiter_id=job.recruiter_id
        ) for job in jobs
    ]

@app.get("/resumes/{job_id}", response_model=List[ResumeResponse])
async def get_resumes_for_job(
    job_id: int,
    current_user: User = Depends(require_role("recruiter")),
    db: Session = Depends(get_db)
):
    """Get resumes that have been evaluated for a specific job"""
    # Verify job belongs to current recruiter
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.recruiter_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get resumes that have evaluations for this job
    evaluations = db.query(Evaluation).filter(Evaluation.job_id == job_id).all()
    resume_ids = [eval.resume_id for eval in evaluations]
    
    resumes = db.query(Resume).filter(Resume.id.in_(resume_ids)).all()
    
    return [
        ResumeResponse(
            id=resume.id,
            filename=resume.filename,
            original_filename=resume.original_filename,
            file_type=resume.file_type,
            version=resume.version,
            is_latest=resume.is_latest,
            created_at=resume.created_at,
            student_id=resume.student_id
        ) for resume in resumes
    ]

@app.get("/analytics/{job_id}", response_model=AnalyticsResponse)
async def get_job_analytics(
    job_id: int,
    current_user: User = Depends(require_role("recruiter")),
    db: Session = Depends(get_db)
):
    """Get analytics for a specific job"""
    # Verify job belongs to current recruiter
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.recruiter_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get evaluations for this job
    evaluations = db.query(Evaluation).filter(Evaluation.job_id == job_id).all()
    
    if not evaluations:
        return AnalyticsResponse(
            job_id=job_id,
            total_applications=0,
            high_fit_count=0,
            medium_fit_count=0,
            low_fit_count=0,
            average_score=0.0,
            skill_gaps={},
            top_skills_matched=[],
            improvement_trends=[]
        )
    
    # Calculate statistics
    total_applications = len(evaluations)
    high_fit_count = len([e for e in evaluations if e.verdict == "High"])
    medium_fit_count = len([e for e in evaluations if e.verdict == "Medium"])
    low_fit_count = len([e for e in evaluations if e.verdict == "Low"])
    average_score = sum(e.overall_score for e in evaluations) / total_applications
    
    # Skill gap analysis
    all_missing_skills = []
    for eval in evaluations:
        if eval.missing_skills:
            all_missing_skills.extend(eval.missing_skills)
    
    skill_gaps = dict(Counter(all_missing_skills))
    
    # Top matched skills
    all_matched_skills = []
    for eval in evaluations:
        if eval.matched_skills:
            all_matched_skills.extend(eval.matched_skills)
    
    top_skills_matched = [
        {"skill": skill, "count": count} 
        for skill, count in Counter(all_matched_skills).most_common(10)
    ]
    
    return AnalyticsResponse(
        job_id=job_id,
        total_applications=total_applications,
        high_fit_count=high_fit_count,
        medium_fit_count=medium_fit_count,
        low_fit_count=low_fit_count,
        average_score=round(average_score, 1),
        skill_gaps=skill_gaps,
        top_skills_matched=top_skills_matched,
        improvement_trends=[]  # Would need historical data
    )

# Evaluation endpoint
@app.post("/evaluate/{resume_id}/{job_id}", response_model=EvaluationResponse)
async def evaluate_resume_against_job(
    resume_id: int,
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Evaluate a resume against a job description"""
    # Get resume and job
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not resume or not job:
        raise HTTPException(status_code=404, detail="Resume or job not found")
    
    # Check if evaluation already exists
    existing_eval = db.query(Evaluation).filter(
        Evaluation.resume_id == resume_id,
        Evaluation.job_id == job_id
    ).first()
    
    if existing_eval:
        return EvaluationResponse(
            id=existing_eval.id,
            resume_id=existing_eval.resume_id,
            job_id=existing_eval.job_id,
            overall_score=existing_eval.overall_score,
            verdict=existing_eval.verdict,
            hard_match_score=existing_eval.hard_match_score,
            soft_match_score=existing_eval.soft_match_score,
            matched_skills=existing_eval.matched_skills,
            missing_skills=existing_eval.missing_skills,
            skill_coverage=existing_eval.skill_coverage,
            feedback=existing_eval.feedback,
            verdict_explanation=existing_eval.verdict_explanation,
            anomaly_flags=existing_eval.anomaly_flags,
            created_at=existing_eval.created_at
        )
    
    # Calculate scores
    hard_score = calculate_hard_match_score(resume.raw_text, job.description)
    soft_score = calculate_soft_match_score(resume.raw_text, job.description)
    overall_score = (hard_score * 0.6 + soft_score * 0.4) * 100
    
    # Determine verdict
    if overall_score >= 70:
        verdict = "High"
    elif overall_score >= 40:
        verdict = "Medium"
    else:
        verdict = "Low"
    
    # Extract skills
    resume_skills = extract_skills_from_text(resume.raw_text)
    job_skills = extract_skills_from_text(job.description)
    
    matched_skills = [skill for skill in job_skills if skill in resume_skills]
    missing_skills = [skill for skill in job_skills if skill not in resume_skills]
    skill_coverage = len(matched_skills) / len(job_skills) if job_skills else 0
    
    # Generate LLM feedback
    feedback = generate_llm_feedback(resume.raw_text, job.description, overall_score, verdict)
    
    # Detect anomalies
    anomalies = detect_anomalies(resume.raw_text)
    
    # Create evaluation
    db_evaluation = Evaluation(
        resume_id=resume_id,
        job_id=job_id,
        user_id=current_user.id,
        overall_score=overall_score,
        verdict=verdict,
        hard_match_score=hard_score,
        soft_match_score=soft_score,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        skill_coverage=skill_coverage,
        feedback=feedback,
        verdict_explanation=feedback.get("verdict_explanation", ""),
        anomaly_flags=anomalies
    )
    
    db.add(db_evaluation)
    db.commit()
    db.refresh(db_evaluation)
    
    return EvaluationResponse(
        id=db_evaluation.id,
        resume_id=db_evaluation.resume_id,
        job_id=db_evaluation.job_id,
        overall_score=db_evaluation.overall_score,
        verdict=db_evaluation.verdict,
        hard_match_score=db_evaluation.hard_match_score,
        soft_match_score=db_evaluation.soft_match_score,
        matched_skills=db_evaluation.matched_skills,
        missing_skills=db_evaluation.missing_skills,
        skill_coverage=db_evaluation.skill_coverage,
        feedback=db_evaluation.feedback,
        verdict_explanation=db_evaluation.verdict_explanation,
        anomaly_flags=db_evaluation.anomaly_flags,
        created_at=db_evaluation.created_at
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
