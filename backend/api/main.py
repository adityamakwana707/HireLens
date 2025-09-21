"""
FastAPI main application for HireLens
"""
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from pathlib import Path
import logging

from backend.db.database import get_db, create_tables
from backend.db.models import User, Job, Resume, Evaluation
from backend.auth.dependencies import get_current_active_user, require_role
from backend.langchain_pipelines.evaluation_pipeline import ResumeEvaluationPipeline, EvaluationResult
from backend.parsers.resume_parser import ResumeParser
from backend.parsers.jd_parser import JDParser
from backend.auth.security import create_access_token, get_password_hash, verify_password
from pydantic import BaseModel, EmailStr
from datetime import timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="HireLens API",
    description="AI-Powered Resume Relevance Check System",
    version="1.0.0"
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

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "recruiter"

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class JobCreate(BaseModel):
    title: str
    company: str
    description: str
    location: Optional[str] = None
    requirements: Optional[str] = None

class JobResponse(BaseModel):
    id: int
    title: str
    company: str
    location: Optional[str]
    description: str
    requirements: Optional[str]
    skills_required: List[str]
    skills_preferred: List[str]
    created_at: str

class ResumeResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_type: str
    skills: List[str]
    created_at: str

class EvaluationResponse(BaseModel):
    id: int
    resume_id: int
    job_id: int
    overall_score: float
    verdict: str
    hard_match_score: float
    soft_match_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    skill_coverage: float
    feedback: dict
    created_at: str

# Initialize evaluation pipeline
evaluation_pipeline = ResumeEvaluationPipeline()

# Create upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.on_event("startup")
async def startup_event():
    """Initialize database and create tables"""
    try:
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

# Authentication endpoints
@app.post("/auth/register", response_model=Token)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user.email) | (User.username == user.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )
    
    # Create new user
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
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.username, "user_id": db_user.id}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/login", response_model=Token)
async def login(user: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    # Find user
    db_user = db.query(User).filter(User.username == user.username).first()
    
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.username, "user_id": db_user.id}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# Job Description endpoints
@app.post("/jobs/", response_model=JobResponse)
async def create_job(
    job: JobCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new job description"""
    # Parse job description to extract skills
    jd_parser = JDParser()
    parsed_jd = jd_parser.parse_jd(job.description)
    
    # Create job in database
    db_job = Job(
        title=job.title,
        company=job.company,
        location=job.location,
        description=job.description,
        requirements=job.requirements,
        skills_required=parsed_jd.get('skills_required', []),
        skills_preferred=parsed_jd.get('skills_preferred', []),
        user_id=current_user.id
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
        skills_required=db_job.skills_required or [],
        skills_preferred=db_job.skills_preferred or [],
        created_at=db_job.created_at.isoformat()
    )

@app.get("/jobs/", response_model=List[JobResponse])
async def get_jobs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all jobs for current user"""
    jobs = db.query(Job).filter(Job.user_id == current_user.id).all()
    
    return [
        JobResponse(
            id=job.id,
            title=job.title,
            company=job.company,
            location=job.location,
            description=job.description,
            requirements=job.requirements,
            skills_required=job.skills_required or [],
            skills_preferred=job.skills_preferred or [],
            created_at=job.created_at.isoformat()
        )
        for job in jobs
    ]

# Resume upload and parsing endpoints
@app.post("/resumes/upload", response_model=ResumeResponse)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload and parse a resume"""
    # Validate file type
    if not file.filename.endswith(('.pdf', '.docx')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are allowed"
        )
    
    # Save file
    file_path = UPLOAD_DIR / f"{current_user.id}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Parse resume
        resume_parser = ResumeParser()
        parsed_data = resume_parser.parse_file(str(file_path))
        
        # Save to database
        db_resume = Resume(
            filename=file_path.name,
            original_filename=file.filename,
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            file_type=file.filename.split('.')[-1],
            raw_text=parsed_data.get('raw_text', ''),
            skills=parsed_data.get('skills', []),
            education=parsed_data.get('education', []),
            experience=parsed_data.get('experience', []),
            projects=parsed_data.get('projects', []),
            certifications=parsed_data.get('certifications', []),
            contact_info=parsed_data.get('contact_info', {}),
            user_id=current_user.id
        )
        
        db.add(db_resume)
        db.commit()
        db.refresh(db_resume)
        
        return ResumeResponse(
            id=db_resume.id,
            filename=db_resume.filename,
            original_filename=db_resume.original_filename,
            file_type=db_resume.file_type,
            skills=db_resume.skills or [],
            created_at=db_resume.created_at.isoformat()
        )
        
    except Exception as e:
        # Clean up file on error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error parsing resume: {str(e)}"
        )

@app.get("/resumes/", response_model=List[ResumeResponse])
async def get_resumes(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all resumes for current user"""
    resumes = db.query(Resume).filter(Resume.user_id == current_user.id).all()
    
    return [
        ResumeResponse(
            id=resume.id,
            filename=resume.filename,
            original_filename=resume.original_filename,
            file_type=resume.file_type,
            skills=resume.skills or [],
            created_at=resume.created_at.isoformat()
        )
        for resume in resumes
    ]

# Evaluation endpoints
@app.post("/evaluate/{resume_id}/{job_id}", response_model=EvaluationResponse)
async def evaluate_resume(
    resume_id: int,
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Evaluate a resume against a job description"""
    # Get resume and job
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    try:
        # Perform evaluation
        result = evaluation_pipeline.evaluate_resume(
            resume_file_path=resume.file_path,
            jd_text=job.description,
            jd_title=job.title,
            jd_company=job.company
        )
        
        # Save evaluation to database
        db_evaluation = Evaluation(
            resume_id=resume_id,
            job_id=job_id,
            overall_score=result.final_score,
            hard_match_score=result.hard_match_score,
            soft_match_score=result.soft_match_score,
            verdict=result.verdict,
            matched_skills=result.matched_skills,
            missing_skills=result.missing_skills,
            skill_coverage=result.skill_coverage,
            feedback=result.feedback
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
            matched_skills=db_evaluation.matched_skills or [],
            missing_skills=db_evaluation.missing_skills or [],
            skill_coverage=db_evaluation.skill_coverage,
            feedback=db_evaluation.feedback or {},
            created_at=db_evaluation.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error evaluating resume: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during evaluation: {str(e)}"
        )

@app.get("/evaluations/", response_model=List[EvaluationResponse])
async def get_evaluations(
    job_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all evaluations for current user, optionally filtered by job"""
    query = db.query(Evaluation).join(Resume).filter(Resume.user_id == current_user.id)
    
    if job_id:
        query = query.filter(Evaluation.job_id == job_id)
    
    evaluations = query.all()
    
    return [
        EvaluationResponse(
            id=eval.id,
            resume_id=eval.resume_id,
            job_id=eval.job_id,
            overall_score=eval.overall_score,
            verdict=eval.verdict,
            hard_match_score=eval.hard_match_score,
            soft_match_score=eval.soft_match_score,
            matched_skills=eval.matched_skills or [],
            missing_skills=eval.missing_skills or [],
            skill_coverage=eval.skill_coverage,
            feedback=eval.feedback or {},
            created_at=eval.created_at.isoformat()
        )
        for eval in evaluations
    ]

# Batch evaluation endpoint
@app.post("/evaluate/batch/{job_id}", response_model=List[EvaluationResponse])
async def batch_evaluate_resumes(
    job_id: int,
    resume_ids: List[int],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Evaluate multiple resumes against a job description"""
    # Get job
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Get resumes
    resumes = db.query(Resume).filter(
        Resume.id.in_(resume_ids),
        Resume.user_id == current_user.id
    ).all()
    
    if not resumes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No valid resumes found"
        )
    
    try:
        # Perform batch evaluation
        resume_paths = [resume.file_path for resume in resumes]
        results = evaluation_pipeline.batch_evaluate_resumes(
            resume_file_paths=resume_paths,
            jd_text=job.description,
            jd_title=job.title,
            jd_company=job.company
        )
        
        # Save evaluations to database
        db_evaluations = []
        for i, result in enumerate(results):
            db_evaluation = Evaluation(
                resume_id=resumes[i].id,
                job_id=job_id,
                overall_score=result.final_score,
                hard_match_score=result.hard_match_score,
                soft_match_score=result.soft_match_score,
                verdict=result.verdict,
                matched_skills=result.matched_skills,
                missing_skills=result.missing_skills,
                skill_coverage=result.skill_coverage,
                feedback=result.feedback
            )
            db_evaluations.append(db_evaluation)
        
        db.add_all(db_evaluations)
        db.commit()
        
        # Return evaluation responses
        return [
            EvaluationResponse(
                id=eval.id,
                resume_id=eval.resume_id,
                job_id=eval.job_id,
                overall_score=eval.overall_score,
                verdict=eval.verdict,
                hard_match_score=eval.hard_match_score,
                soft_match_score=eval.soft_match_score,
                matched_skills=eval.matched_skills or [],
                missing_skills=eval.missing_skills or [],
                skill_coverage=eval.skill_coverage,
                feedback=eval.feedback or {},
                created_at=eval.created_at.isoformat()
            )
            for eval in db_evaluations
        ]
        
    except Exception as e:
        logger.error(f"Error in batch evaluation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during batch evaluation: {str(e)}"
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "HireLens API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)