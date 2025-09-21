"""
Streamlit frontend for HireLens
"""
import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
from typing import List, Dict, Any
import io

# Configure page
st.set_page_config(
    page_title="HireLens - AI Resume Evaluator",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-card {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
    }
    .warning-card {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
    }
    .danger-card {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)

class HireLensApp:
    """Main Streamlit application class"""
    
    def __init__(self):
        self.api_base_url = API_BASE_URL
        self.token = None
        self.user_info = None
    
    def login(self, username: str, password: str) -> bool:
        """Login user"""
        try:
            response = requests.post(
                f"{self.api_base_url}/auth/login",
                json={"username": username, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                st.session_state.token = self.token
                return True
            else:
                st.error("Invalid username or password")
                return False
        except Exception as e:
            st.error(f"Login failed: {str(e)}")
            return False
    
    def register(self, username: str, email: str, password: str, role: str = "recruiter") -> bool:
        """Register new user"""
        try:
            response = requests.post(
                f"{self.api_base_url}/auth/register",
                json={
                    "username": username,
                    "email": email,
                    "password": password,
                    "role": role
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                st.session_state.token = self.token
                return True
            else:
                st.error("Registration failed. Username or email may already exist.")
                return False
        except Exception as e:
            st.error(f"Registration failed: {str(e)}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token"""
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}
    
    def get_jobs(self) -> List[Dict]:
        """Get all jobs"""
        try:
            response = requests.get(
                f"{self.api_base_url}/jobs/",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            st.error(f"Error fetching jobs: {str(e)}")
            return []
    
    def create_job(self, title: str, company: str, description: str, location: str = "") -> bool:
        """Create new job"""
        try:
            response = requests.post(
                f"{self.api_base_url}/jobs/",
                json={
                    "title": title,
                    "company": company,
                    "description": description,
                    "location": location
                },
                headers=self.get_headers()
            )
            return response.status_code == 200
        except Exception as e:
            st.error(f"Error creating job: {str(e)}")
            return False
    
    def upload_resume(self, file) -> bool:
        """Upload resume"""
        try:
            files = {"file": (file.name, file.getvalue(), file.type)}
            response = requests.post(
                f"{self.api_base_url}/resumes/upload",
                files=files,
                headers=self.get_headers()
            )
            return response.status_code == 200
        except Exception as e:
            st.error(f"Error uploading resume: {str(e)}")
            return False
    
    def get_resumes(self) -> List[Dict]:
        """Get all resumes"""
        try:
            response = requests.get(
                f"{self.api_base_url}/resumes/",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            st.error(f"Error fetching resumes: {str(e)}")
            return []
    
    def evaluate_resume(self, resume_id: int, job_id: int) -> Dict:
        """Evaluate resume against job"""
        try:
            response = requests.post(
                f"{self.api_base_url}/evaluate/{resume_id}/{job_id}",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            st.error(f"Error evaluating resume: {str(e)}")
            return None
    
    def batch_evaluate(self, job_id: int, resume_ids: List[int]) -> List[Dict]:
        """Batch evaluate resumes"""
        try:
            response = requests.post(
                f"{self.api_base_url}/evaluate/batch/{job_id}",
                json=resume_ids,
                headers=self.get_headers()
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            st.error(f"Error in batch evaluation: {str(e)}")
            return []
    
    def get_evaluations(self, job_id: int = None) -> List[Dict]:
        """Get evaluations"""
        try:
            url = f"{self.api_base_url}/evaluations/"
            if job_id:
                url += f"?job_id={job_id}"
            
            response = requests.get(url, headers=self.get_headers())
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            st.error(f"Error fetching evaluations: {str(e)}")
            return []

def main():
    """Main application function"""
    app = HireLensApp()
    
    # Initialize session state
    if 'token' not in st.session_state:
        st.session_state.token = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'login'
    
    app.token = st.session_state.token
    
    # Header
    st.markdown('<h1 class="main-header">🔍 HireLens</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">AI-Powered Resume Relevance Check System</p>', unsafe_allow_html=True)
    
    # Authentication
    if not app.token:
        show_auth_page(app)
    else:
        show_main_app(app)

def show_auth_page(app: HireLensApp):
    """Show authentication page"""
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🔐 Login")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_clicked = st.form_submit_button("Login")
            
            if login_clicked:
                if app.login(username, password):
                    st.success("Login successful!")
                    st.rerun()
    
    with col2:
        st.subheader("📝 Register")
        with st.form("register_form"):
            reg_username = st.text_input("Username", key="reg_username")
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            reg_role = st.selectbox("Role", ["recruiter", "student"], key="reg_role")
            register_clicked = st.form_submit_button("Register")
            
            if register_clicked:
                if app.register(reg_username, reg_email, reg_password, reg_role):
                    st.success("Registration successful!")
                    st.rerun()

def show_main_app(app: HireLensApp):
    """Show main application"""
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Dashboard", "Job Management", "Resume Management", "Evaluations", "Analytics"]
    )
    
    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.token = None
        st.rerun()
    
    # Route to appropriate page
    if page == "Dashboard":
        show_dashboard(app)
    elif page == "Job Management":
        show_job_management(app)
    elif page == "Resume Management":
        show_resume_management(app)
    elif page == "Evaluations":
        show_evaluations(app)
    elif page == "Analytics":
        show_analytics(app)

def show_dashboard(app: HireLensApp):
    """Show dashboard page"""
    st.header("📊 Dashboard")
    
    # Get data
    jobs = app.get_jobs()
    resumes = app.get_resumes()
    evaluations = app.get_evaluations()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Jobs", len(jobs))
    
    with col2:
        st.metric("Total Resumes", len(resumes))
    
    with col3:
        st.metric("Total Evaluations", len(evaluations))
    
    with col4:
        if evaluations:
            avg_score = sum(eval['overall_score'] for eval in evaluations) / len(evaluations)
            st.metric("Average Score", f"{avg_score:.1f}")
        else:
            st.metric("Average Score", "N/A")
    
    # Recent evaluations
    if evaluations:
        st.subheader("📈 Recent Evaluations")
        
        # Create DataFrame
        df = pd.DataFrame(evaluations)
        df['created_at'] = pd.to_datetime(df['created_at'])
        df = df.sort_values('created_at', ascending=False).head(10)
        
        # Display table
        st.dataframe(
            df[['resume_id', 'job_id', 'overall_score', 'verdict', 'created_at']],
            use_container_width=True
        )
        
        # Score distribution
        st.subheader("📊 Score Distribution")
        fig = px.histogram(df, x='overall_score', nbins=20, title="Score Distribution")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No evaluations yet. Upload resumes and jobs to get started!")

def show_job_management(app: HireLensApp):
    """Show job management page"""
    st.header("💼 Job Management")
    
    # Create new job
    with st.expander("➕ Create New Job", expanded=True):
        with st.form("create_job_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input("Job Title")
                company = st.text_input("Company")
                location = st.text_input("Location (Optional)")
            
            with col2:
                description = st.text_area("Job Description", height=200)
            
            if st.form_submit_button("Create Job"):
                if title and company and description:
                    if app.create_job(title, company, description, location):
                        st.success("Job created successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to create job")
                else:
                    st.error("Please fill in all required fields")
    
    # List jobs
    st.subheader("📋 Your Jobs")
    jobs = app.get_jobs()
    
    if jobs:
        for job in jobs:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{job['title']}** at {job['company']}")
                    if job['location']:
                        st.write(f"📍 {job['location']}")
                    st.write(f"📅 Created: {job['created_at'][:10]}")
                
                with col2:
                    st.write(f"Required Skills: {len(job['skills_required'])}")
                    st.write(f"Preferred Skills: {len(job['skills_preferred'])}")
                
                with col3:
                    if st.button(f"Evaluate Resumes", key=f"eval_{job['id']}"):
                        st.session_state.selected_job = job
                        st.rerun()
    else:
        st.info("No jobs created yet. Create your first job above!")

def show_resume_management(app: HireLensApp):
    """Show resume management page"""
    st.header("📄 Resume Management")
    
    # Upload resume
    with st.expander("📤 Upload Resume", expanded=True):
        uploaded_file = st.file_uploader(
            "Choose a resume file",
            type=['pdf', 'docx'],
            help="Upload PDF or DOCX resume files"
        )
        
        if uploaded_file is not None:
            if st.button("Upload Resume"):
                if app.upload_resume(uploaded_file):
                    st.success("Resume uploaded and parsed successfully!")
                    st.rerun()
                else:
                    st.error("Failed to upload resume")
    
    # List resumes
    st.subheader("📋 Your Resumes")
    resumes = app.get_resumes()
    
    if resumes:
        for resume in resumes:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.write(f"**{resume['original_filename']}**")
                    st.write(f"Type: {resume['file_type'].upper()}")
                    st.write(f"📅 Uploaded: {resume['created_at'][:10]}")
                
                with col2:
                    if resume['skills']:
                        st.write("Skills:")
                        st.write(", ".join(resume['skills'][:5]))
                        if len(resume['skills']) > 5:
                            st.write(f"... and {len(resume['skills']) - 5} more")
                    else:
                        st.write("No skills extracted")
                
                with col3:
                    if st.button(f"View Details", key=f"view_{resume['id']}"):
                        st.session_state.selected_resume = resume
                        st.rerun()
    else:
        st.info("No resumes uploaded yet. Upload your first resume above!")

def show_evaluations(app: HireLensApp):
    """Show evaluations page"""
    st.header("🔍 Resume Evaluations")
    
    # Job selection
    jobs = app.get_jobs()
    if not jobs:
        st.warning("No jobs available. Create a job first!")
        return
    
    selected_job_id = st.selectbox(
        "Select Job to Evaluate Against",
        options=[job['id'] for job in jobs],
        format_func=lambda x: next(job['title'] for job in jobs if job['id'] == x)
    )
    
    # Get resumes for selected job
    resumes = app.get_resumes()
    if not resumes:
        st.warning("No resumes available. Upload resumes first!")
        return
    
    # Batch evaluation
    if st.button("🚀 Evaluate All Resumes"):
        with st.spinner("Evaluating resumes..."):
            resume_ids = [resume['id'] for resume in resumes]
            results = app.batch_evaluate(selected_job_id, resume_ids)
            
            if results:
                st.success(f"Successfully evaluated {len(results)} resumes!")
                st.rerun()
            else:
                st.error("Failed to evaluate resumes")
    
    # Individual evaluation
    st.subheader("📊 Individual Evaluation")
    selected_resume_id = st.selectbox(
        "Select Resume to Evaluate",
        options=[resume['id'] for resume in resumes],
        format_func=lambda x: next(resume['original_filename'] for resume in resumes if resume['id'] == x)
    )
    
    if st.button("🔍 Evaluate Resume"):
        with st.spinner("Evaluating resume..."):
            result = app.evaluate_resume(selected_resume_id, selected_job_id)
            
            if result:
                st.success("Evaluation completed!")
                display_evaluation_result(result)
            else:
                st.error("Failed to evaluate resume")
    
    # Show existing evaluations
    st.subheader("📈 Evaluation Results")
    evaluations = app.get_evaluations(selected_job_id)
    
    if evaluations:
        # Create DataFrame
        df = pd.DataFrame(evaluations)
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            verdict_filter = st.selectbox("Filter by Verdict", ["All", "High", "Medium", "Low"])
        with col2:
            min_score = st.slider("Minimum Score", 0, 100, 0)
        
        # Apply filters
        if verdict_filter != "All":
            df = df[df['verdict'] == verdict_filter]
        df = df[df['overall_score'] >= min_score]
        
        # Display results
        for _, eval_result in df.iterrows():
            display_evaluation_card(eval_result)
    else:
        st.info("No evaluations for this job yet. Run evaluations above!")

def display_evaluation_result(result: Dict):
    """Display evaluation result"""
    st.subheader("🎯 Evaluation Result")
    
    # Score and verdict
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Overall Score", f"{result['overall_score']:.1f}/100")
    
    with col2:
        st.metric("Hard Match", f"{result['hard_match_score']:.1f}/100")
    
    with col3:
        st.metric("Soft Match", f"{result['soft_match_score']:.1f}/100")
    
    # Verdict
    verdict_color = {
        "High": "success",
        "Medium": "warning", 
        "Low": "danger"
    }
    
    st.markdown(f"""
    <div class="{verdict_color.get(result['verdict'], 'info')}-card">
        <h4>Verdict: {result['verdict']}</h4>
    </div>
    """, unsafe_allow_html=True)
    
    # Skills analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("✅ Matched Skills")
        if result['matched_skills']:
            for skill in result['matched_skills']:
                st.write(f"• {skill}")
        else:
            st.write("No skills matched")
    
    with col2:
        st.subheader("❌ Missing Skills")
        if result['missing_skills']:
            for skill in result['missing_skills']:
                st.write(f"• {skill}")
        else:
            st.write("All required skills matched!")
    
    # Feedback
    if result['feedback']:
        st.subheader("💡 AI Feedback")
        
        feedback = result['feedback']
        
        if 'overall_feedback' in feedback:
            st.write(feedback['overall_feedback'])
        
        if 'strengths' in feedback and feedback['strengths']:
            st.subheader("💪 Strengths")
            for strength in feedback['strengths']:
                st.write(f"• {strength}")
        
        if 'weaknesses' in feedback and feedback['weaknesses']:
            st.subheader("🔧 Areas for Improvement")
            for weakness in feedback['weaknesses']:
                st.write(f"• {weakness}")
        
        if 'improvement_suggestions' in feedback and feedback['improvement_suggestions']:
            st.subheader("🚀 Suggestions")
            for suggestion in feedback['improvement_suggestions']:
                st.write(f"• {suggestion}")

def display_evaluation_card(eval_result: pd.Series):
    """Display evaluation card"""
    with st.container():
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            st.write(f"**Resume ID:** {eval_result['resume_id']}")
            st.write(f"**Job ID:** {eval_result['job_id']}")
        
        with col2:
            st.metric("Score", f"{eval_result['overall_score']:.1f}")
        
        with col3:
            verdict_color = {
                "High": "🟢",
                "Medium": "🟡",
                "Low": "🔴"
            }
            st.write(f"{verdict_color.get(eval_result['verdict'], '⚪')} {eval_result['verdict']}")
        
        with col4:
            if st.button("View Details", key=f"details_{eval_result['id']}"):
                st.session_state.selected_evaluation = eval_result
                st.rerun()

def show_analytics(app: HireLensApp):
    """Show analytics page"""
    st.header("📊 Analytics")
    
    # Get all evaluations
    evaluations = app.get_evaluations()
    
    if not evaluations:
        st.info("No evaluations available for analytics")
        return
    
    # Create DataFrame
    df = pd.DataFrame(evaluations)
    df['created_at'] = pd.to_datetime(df['created_at'])
    
    # Overall statistics
    st.subheader("📈 Overall Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Evaluations", len(df))
    
    with col2:
        avg_score = df['overall_score'].mean()
        st.metric("Average Score", f"{avg_score:.1f}")
    
    with col3:
        high_fit = len(df[df['verdict'] == 'High'])
        st.metric("High Fit", high_fit)
    
    with col4:
        medium_fit = len(df[df['verdict'] == 'Medium'])
        st.metric("Medium Fit", medium_fit)
    
    # Score distribution
    st.subheader("📊 Score Distribution")
    fig = px.histogram(df, x='overall_score', nbins=20, title="Score Distribution")
    st.plotly_chart(fig, use_container_width=True)
    
    # Verdict distribution
    st.subheader("🎯 Verdict Distribution")
    verdict_counts = df['verdict'].value_counts()
    fig = px.pie(values=verdict_counts.values, names=verdict_counts.index, title="Verdict Distribution")
    st.plotly_chart(fig, use_container_width=True)
    
    # Time series analysis
    st.subheader("📅 Evaluations Over Time")
    daily_evaluations = df.groupby(df['created_at'].dt.date).size().reset_index()
    daily_evaluations.columns = ['Date', 'Count']
    
    fig = px.line(daily_evaluations, x='Date', y='Count', title="Daily Evaluations")
    st.plotly_chart(fig, use_container_width=True)
    
    # Top missing skills
    st.subheader("🔍 Top Missing Skills")
    all_missing_skills = []
    for skills in df['missing_skills']:
        all_missing_skills.extend(skills)
    
    if all_missing_skills:
        skill_counts = pd.Series(all_missing_skills).value_counts().head(10)
        fig = px.bar(x=skill_counts.values, y=skill_counts.index, orientation='h', title="Top Missing Skills")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No missing skills data available")

if __name__ == "__main__":
    main()
