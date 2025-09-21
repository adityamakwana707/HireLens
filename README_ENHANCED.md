# 🔍 HireLens Enhanced - AI-Powered Resume Relevance System

## 🎯 Overview

HireLens Enhanced is a comprehensive, role-based AI-powered resume relevance check system designed for hackathon competition. It provides secure, scalable, and intelligent matching between job descriptions and resumes with advanced analytics and actionable feedback.

## ✨ Key Features

### 🎓 For Students
- **Resume Upload & Version Tracking**: Upload multiple resume versions with automatic tracking
- **Job Board**: Browse all available job postings
- **AI-Powered Evaluations**: Get detailed feedback on resume-job matches
- **Multi-Job Matching**: Find best job matches for your resume
- **Improvement Suggestions**: Receive actionable advice for resume enhancement

### 👔 For Recruiters
- **Job Posting Management**: Create and manage job postings
- **Candidate Analytics**: View detailed analytics for job applications
- **Skill Gap Analysis**: Identify common missing skills among candidates
- **Fit Distribution**: Visualize candidate fit levels (High/Medium/Low)
- **Resume Evaluation**: AI-powered resume assessment against job requirements

### 🔐 Security & Access
- **Role-Based Authentication**: Secure JWT-based access control
- **Student/Recruiter Separation**: Distinct interfaces and permissions
- **Secure File Upload**: Protected resume and job description uploads
- **Session Management**: Secure token-based authentication

## 🏗️ System Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with async support
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT with role-based access control
- **File Processing**: PDF/DOCX parsing with text extraction
- **AI Integration**: LLM-powered feedback generation
- **Analytics**: Real-time data processing and insights

### Frontend (Streamlit)
- **Framework**: Streamlit with responsive design
- **Role-Based UI**: Separate interfaces for students and recruiters
- **Interactive Dashboards**: Real-time analytics and visualizations
- **File Upload**: Drag-and-drop resume and job description uploads
- **Charts & Graphs**: Plotly-powered data visualizations

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd HireLens
```

2. **Install dependencies**
```bash
pip install -r requirements-minimal.txt
```

3. **Start the system**
```bash
python run_enhanced_system.py
```

4. **Choose option 3** to run both backend and frontend

5. **Access the application**
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 📱 User Guide

### For Students

1. **Register/Login**
   - Go to http://localhost:8501
   - Register with role "student"
   - Login with your credentials

2. **Upload Resume**
   - Navigate to "Upload Resume"
   - Upload PDF or DOCX file
   - System automatically tracks versions

3. **Browse Jobs**
   - Go to "Job Board"
   - View all available positions
   - See job details and requirements

4. **Get Evaluations**
   - Go to "My Evaluations"
   - View AI-powered feedback
   - See improvement suggestions

5. **Find Job Matches**
   - Go to "Job Matches"
   - Select your resume
   - Get ranked job recommendations

### For Recruiters

1. **Register/Login**
   - Register with role "recruiter"
   - Login with your credentials

2. **Post Jobs**
   - Go to "Post Job"
   - Fill in job details
   - Add required and preferred skills

3. **Manage Jobs**
   - Go to "My Jobs"
   - View all your postings
   - Access candidate applications

4. **View Candidates**
   - Go to "Candidates"
   - Select a job
   - View and evaluate resumes

5. **Analytics Dashboard**
   - Go to "Analytics"
   - Select a job
   - View fit distribution and skill gaps

## 🔧 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login

### Student Endpoints
- `POST /resumes` - Upload resume
- `GET /jobs` - Get all jobs
- `GET /evaluations/my` - Get my evaluations
- `GET /evaluations/multi-match/{resume_id}` - Get job matches

### Recruiter Endpoints
- `POST /jobs` - Create job posting
- `GET /jobs/my` - Get my jobs
- `GET /resumes/{job_id}` - Get candidates for job
- `GET /analytics/{job_id}` - Get job analytics

### Evaluation
- `POST /evaluate/{resume_id}/{job_id}` - Evaluate resume against job

## 📊 Database Schema

### Users Table
- `id`, `username`, `email`, `hashed_password`, `role`, `is_active`, `created_at`

### Jobs Table
- `id`, `title`, `company`, `location`, `description`, `requirements`, `skills_required`, `skills_preferred`, `recruiter_id`, `created_at`, `is_active`

### Resumes Table
- `id`, `filename`, `original_filename`, `file_path`, `file_type`, `raw_text`, `skills`, `education`, `experience`, `projects`, `certifications`, `contact_info`, `student_id`, `version`, `is_latest`, `created_at`

### Evaluations Table
- `id`, `resume_id`, `job_id`, `user_id`, `overall_score`, `verdict`, `hard_match_score`, `soft_match_score`, `matched_skills`, `missing_skills`, `skill_coverage`, `feedback`, `verdict_explanation`, `anomaly_flags`, `created_at`

## 🎨 Unique Selling Points (USPs)

1. **Role-Based Access Control**: Secure separation between students and recruiters
2. **Resume Version Tracking**: Track resume improvements over time
3. **AI-Powered Feedback**: LLM-generated actionable suggestions
4. **Multi-Job Matching**: Find best job matches for any resume
5. **Skill Gap Analysis**: Identify common missing skills
6. **Anomaly Detection**: Flag unrealistic claims and missing sections
7. **Real-Time Analytics**: Live insights and visualizations
8. **Secure Architecture**: JWT authentication and role-based permissions

## 🧪 Testing

Run the comprehensive test suite:

```bash
python test_enhanced_system.py
```

Tests include:
- Student workflow
- Recruiter workflow
- Role-based access control
- Evaluation system
- API endpoints

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access**: Student/Recruiter permission separation
- **Input Validation**: Pydantic models for data validation
- **CORS Protection**: Configured for secure cross-origin requests
- **File Type Validation**: Only PDF/DOCX files allowed
- **Password Hashing**: bcrypt for secure password storage

## 📈 Analytics Features

- **Fit Distribution**: Pie charts showing High/Medium/Low fit percentages
- **Skill Gap Analysis**: Bar charts of most common missing skills
- **Top Matched Skills**: Visualization of frequently matched skills
- **Application Trends**: Historical data and improvement tracking
- **Real-Time Metrics**: Live statistics and KPIs

## 🚀 Deployment

### Local Development
```bash
python run_enhanced_system.py
```

### Production Deployment
1. Set up PostgreSQL database
2. Configure environment variables
3. Use Docker for containerization
4. Deploy to cloud platform (AWS, GCP, Azure)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🏆 Hackathon Ready

This system is designed to win hackathons with:
- **Complete Functionality**: End-to-end working system
- **Advanced Features**: AI, analytics, role-based access
- **Professional UI**: Modern, responsive design
- **Scalable Architecture**: Production-ready codebase
- **Comprehensive Testing**: Full test coverage
- **Documentation**: Complete setup and usage guides

## 📞 Support

For support or questions, please contact the development team.

---

**Built with ❤️ for Hackathon Success**