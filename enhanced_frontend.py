"""
Enhanced HireLens Frontend with Role-Based Access
"""
import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import base64

# Configuration
API_BASE_URL = "http://localhost:8000"
UPLOAD_DIR = "uploads"

# Initialize session state
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None

def get_headers():
    """Get headers with authentication token"""
    if st.session_state.access_token:
        return {"Authorization": f"Bearer {st.session_state.access_token}"}
    return {}

def make_api_request(method, endpoint, data=None, files=None):
    """Make API request with comprehensive error handling"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        headers = get_headers()
        
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            if files:
                response = requests.post(url, headers=headers, data=data, files=files, timeout=60)
            else:
                response = requests.post(url, headers=headers, json=data, timeout=30)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 201:
            return response.json()
        elif response.status_code == 401:
            st.error("🔐 Session expired. Please login again.")
            st.session_state.access_token = None
            st.session_state.user_role = None
            st.session_state.user_id = None
            st.rerun()
        elif response.status_code == 403:
            st.error("🚫 Access denied. You don't have permission to perform this action.")
            return None
        elif response.status_code == 404:
            st.error("❌ Resource not found. Please check your request.")
            return None
        elif response.status_code == 400:
            try:
                error_data = response.json()
                if "detail" in error_data:
                    st.error(f"❌ Bad Request: {error_data['detail']}")
                else:
                    st.error(f"❌ Bad Request: {response.text}")
            except:
                st.error(f"❌ Bad Request: {response.text}")
            return None
        elif response.status_code == 422:
            try:
                error_data = response.json()
                if "detail" in error_data:
                    st.error(f"❌ Validation Error: {error_data['detail']}")
                else:
                    st.error(f"❌ Validation Error: {response.text}")
            except:
                st.error(f"❌ Validation Error: {response.text}")
            return None
        elif response.status_code == 500:
            st.error("🔧 Server Error: Something went wrong on our end. Please try again later.")
            return None
        else:
            st.error(f"❌ API Error ({response.status_code}): {response.text}")
            return None
    except requests.exceptions.Timeout:
        st.error("⏰ Request timeout. The server is taking too long to respond.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("🔌 Connection error. Please check if the server is running.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"🌐 Network error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"💥 Unexpected error: {str(e)}")
        return None

def login_page():
    """Login/Register page"""
    st.title("🔍 HireLens - AI-Powered Resume Relevance System")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_submitted = st.form_submit_button("Login")
            
            if login_submitted:
                if username and password:
                    data = {"username": username, "password": password}
                    response = make_api_request("POST", "/auth/login", data)
                    
                    if response:
                        st.session_state.access_token = response["access_token"]
                        st.session_state.user_role = response["role"]
                        st.session_state.user_id = response["user_id"]
                        st.success("Login successful!")
                        st.rerun()
                else:
                    st.error("Please fill in all fields")
    
    with tab2:
        st.subheader("Register")
        with st.form("register_form"):
            username = st.text_input("Username", key="reg_username")
            email = st.text_input("Email", key="reg_email")
            password = st.text_input("Password", type="password", key="reg_password")
            role = st.selectbox("Role", ["student", "recruiter"], key="reg_role")
            register_submitted = st.form_submit_button("Register")
            
            if register_submitted:
                if username and email and password:
                    data = {
                        "username": username,
                        "email": email,
                        "password": password,
                        "role": role
                    }
                    response = make_api_request("POST", "/auth/register", data)
                    
                    if response:
                        st.session_state.access_token = response["access_token"]
                        st.session_state.user_role = response["role"]
                        st.session_state.user_id = response["user_id"]
                        st.success("Registration successful!")
                        st.rerun()
                else:
                    st.error("Please fill in all fields")

def student_dashboard():
    """Student dashboard"""
    st.title("🎓 Student Dashboard")
    
    # Sidebar navigation
    with st.sidebar:
        st.header("Navigation")
        page = st.selectbox("Choose a page", [
            "📄 Upload Resume",
            "💼 Job Board",
            "📊 My Evaluations",
            "🎯 Job Matches"
        ])
    
    if page == "📄 Upload Resume":
        upload_resume_page()
    elif page == "💼 Job Board":
        job_board_page()
    elif page == "📊 My Evaluations":
        my_evaluations_page()
    elif page == "🎯 Job Matches":
        job_matches_page()

def recruiter_dashboard():
    """Recruiter dashboard"""
    st.title("👔 Recruiter Dashboard")
    
    # Sidebar navigation
    with st.sidebar:
        st.header("Navigation")
        page = st.selectbox("Choose a page", [
            "📝 Post Job",
            "📋 My Jobs",
            "👥 Candidates",
            "📈 Analytics"
        ])
        
        # Quick upload section in sidebar
        st.markdown("---")
        st.subheader("⚡ Quick Upload")
        st.markdown("Upload a JD file quickly:")
        
        # Use session state to handle quick upload
        if 'quick_upload_triggered' not in st.session_state:
            st.session_state.quick_upload_triggered = False
        
        quick_company = st.text_input("Company", placeholder="e.g., Tech Corp", key="quick_company")
        quick_file = st.file_uploader(
            "JD File",
            type=['pdf', 'docx', 'doc'],
            key="quick_file"
        )
        
        if st.button("🚀 Quick Upload", key="quick_upload_btn"):
            if quick_file and quick_company:
                files_quick = {"file": (quick_file.name, quick_file.getvalue(), quick_file.type)}
                data_quick = {"company": quick_company}
                
                with st.spinner("Quick parsing..."):
                    response_quick = make_api_request("POST", "/jobs/upload", data=data_quick, files=files_quick)
                
                if response_quick:
                    st.success("✅ Quick upload successful!")
                    st.write(f"**Job ID:** {response_quick['id']}")
                    st.write(f"**Title:** {response_quick['title']}")
                    st.write(f"**Company:** {response_quick['company']}")
                    st.session_state.quick_upload_triggered = True
                    st.rerun()
                else:
                    st.error("❌ Quick upload failed. Please try again.")
            else:
                st.error("Please provide both company name and file.")
    
    if page == "📝 Post Job":
        post_job_page()
    elif page == "📋 My Jobs":
        my_jobs_page()
    elif page == "👥 Candidates":
        candidates_page()
    elif page == "📈 Analytics":
        analytics_page()

def upload_resume_page():
    """Upload resume page for students"""
    st.header("📄 Upload Resume")
    st.markdown("Upload your resume to get AI-powered evaluations against job postings.")
    
    with st.form("upload_resume_form"):
        uploaded_file = st.file_uploader(
            "Choose a resume file",
            type=['pdf', 'docx', 'doc'],
            help="Supported formats: PDF, DOCX, DOC"
        )
        
        submit_button = st.form_submit_button("Upload Resume")
        
        if submit_button and uploaded_file:
            # Prepare file for upload
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            
            response = make_api_request("POST", "/resumes", files=files)
            
            if response:
                st.success(f"Resume uploaded successfully! Version {response['version']}")
                st.info(f"File: {response['original_filename']}")

def job_board_page():
    """Job board page for students"""
    st.header("💼 Job Board")
    st.markdown("Browse all available job postings and apply.")
    
    # Fetch jobs
    jobs = make_api_request("GET", "/jobs")
    
    if jobs:
        for job in jobs:
            with st.expander(f"{job['title']} at {job['company']}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Company:** {job['company']}")
                    st.write(f"**Location:** {job['location'] or 'Not specified'}")
                    st.write(f"**Posted:** {job['created_at'][:10]}")
                    
                    if job['description']:
                        st.write("**Description:**")
                        st.write(job['description'][:300] + "..." if len(job['description']) > 300 else job['description'])
                    
                    if job['requirements']:
                        st.write("**Requirements:**")
                        st.write(job['requirements'][:200] + "..." if len(job['requirements']) > 200 else job['requirements'])
                
                with col2:
                    if job['skills_required']:
                        st.write("**Required Skills:**")
                        for skill in job['skills_required'][:5]:
                            st.write(f"• {skill}")
                    
                    # Apply button
                    if st.button(f"Apply for this Job", key=f"apply_{job['id']}"):
                        # Get user's latest resume
                        resumes = make_api_request("GET", "/resumes/my")
                        if resumes:
                            # Find the latest resume
                            latest_resume = next((r for r in resumes if r['is_latest']), None)
                            if latest_resume:
                                # Trigger evaluation
                                with st.spinner("Evaluating your resume against this job..."):
                                    eval_response = make_api_request("POST", f"/evaluate/{latest_resume['id']}/{job['id']}")
                                
                                if eval_response:
                                    st.success(f"✅ Application submitted and evaluated for {job['title']} at {job['company']}!")
                                    st.info(f"Your match score: {eval_response['overall_score']:.1f}/100 ({eval_response['verdict']} fit)")
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to evaluate your resume. Please try again.")
                            else:
                                st.error("❌ No resume found. Please upload a resume first.")
                        else:
                            st.error("❌ No resume found. Please upload a resume first.")
                
                st.markdown("---")
    else:
        st.info("No jobs available at the moment.")

def my_evaluations_page():
    """My evaluations page for students"""
    st.header("📊 My Evaluations")
    st.markdown("View AI-powered evaluations of your resumes against job postings.")
    
    # Fetch evaluations
    evaluations = make_api_request("GET", "/evaluations/my")
    
    if evaluations:
        for eval in evaluations:
            # Get job details
            job = make_api_request("GET", f"/jobs")
            job_title = "Unknown Job"
            if job:
                job_info = next((j for j in job if j['id'] == eval['job_id']), None)
                if job_info:
                    job_title = f"{job_info['title']} at {job_info['company']}"
            
            # Color code verdict
            verdict_color = {
                "High": "🟢",
                "Medium": "🟡", 
                "Low": "🔴"
            }.get(eval['verdict'], "⚪")
            
            with st.expander(f"{verdict_color} {job_title} - Score: {eval['overall_score']:.1f}/100"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Overall Score:** {eval['overall_score']:.1f}/100")
                    st.write(f"**Verdict:** {eval['verdict']}")
                    
                    if eval['hard_match_score']:
                        st.write(f"**Hard Match:** {eval['hard_match_score']:.1%}")
                    if eval['soft_match_score']:
                        st.write(f"**Soft Match:** {eval['soft_match_score']:.1%}")
                    
                    if eval['matched_skills']:
                        st.write("**Matched Skills:**")
                        for skill in eval['matched_skills'][:5]:
                            st.write(f"✅ {skill}")
                    
                    if eval['missing_skills']:
                        st.write("**Missing Skills:**")
                        for skill in eval['missing_skills'][:5]:
                            st.write(f"❌ {skill}")
                
                with col2:
                    if eval['feedback']:
                        st.write("**AI Feedback:**")
                        feedback = eval['feedback']
                        if 'overall_feedback' in feedback:
                            st.write(feedback['overall_feedback'])
                        
                        if 'strengths' in feedback:
                            st.write("**Strengths:**")
                            for strength in feedback['strengths'][:3]:
                                st.write(f"• {strength}")
                        
                        if 'improvement_suggestions' in feedback:
                            st.write("**Suggestions:**")
                            for suggestion in feedback['improvement_suggestions'][:3]:
                                st.write(f"• {suggestion}")
                
                if eval['verdict_explanation']:
                    st.write("**Verdict Explanation:**")
                    st.write(eval['verdict_explanation'])
                
                if eval['anomaly_flags']:
                    st.warning("**Anomalies Detected:**")
                    for anomaly in eval['anomaly_flags']:
                        st.write(f"⚠️ {anomaly}")
                
                st.write(f"**Evaluated:** {eval['created_at'][:19]}")
    else:
        st.info("No evaluations found. Upload a resume and apply for jobs to get evaluations.")

def job_matches_page():
    """Job matches page for students"""
    st.header("🎯 Job Matches")
    st.markdown("Find the best job matches for your resume.")
    
    # Get user's resumes
    resumes = make_api_request("GET", "/resumes/my")
    
    if resumes:
        resume_options = {f"Version {r['version']} - {r['original_filename']}": r['id'] for r in resumes if r['is_latest']}
        
        if resume_options:
            selected_resume = st.selectbox("Select a resume", list(resume_options.keys()))
            
            if st.button("Find Job Matches"):
                resume_id = resume_options[selected_resume]
                matches = make_api_request("GET", f"/evaluations/multi-match/{resume_id}")
                
                if matches and matches['matches']:
                    st.success(f"Found {len(matches['matches'])} job matches!")
                    
                    for i, match in enumerate(matches['matches'][:10], 1):
                        verdict_color = {
                            "High": "🟢",
                            "Medium": "🟡",
                            "Low": "🔴"
                        }.get(match['verdict'], "⚪")
                        
                        with st.expander(f"{i}. {verdict_color} {match['job_title']} - {match['score']:.1f}/100"):
                            st.write(f"**Company:** {match['company']}")
                            st.write(f"**Location:** {match['location'] or 'Not specified'}")
                            st.write(f"**Match Score:** {match['score']:.1f}/100")
                            st.write(f"**Fit Level:** {match['verdict']}")
                            
                            # Progress bar for score
                            progress = match['score'] / 100
                            st.progress(progress)
                else:
                    st.info("No job matches found.")
        else:
            st.info("No resumes found. Please upload a resume first.")
    else:
        st.info("No resumes found. Please upload a resume first.")

def post_job_page():
    """Post job page for recruiters"""
    st.header("📝 Post New Job")
    st.markdown("Create a new job posting to attract candidates.")
    
    # Tabs for different job creation methods
    tab1, tab2, tab3 = st.tabs(["📄 Upload Job Description", "✏️ Manual Entry", "📦 Bulk Upload"])
    
    with tab1:
        st.subheader("Upload Job Description File")
        st.markdown("Upload a PDF or DOCX file containing the job description. Our AI will extract the details automatically.")
        
        with st.form("upload_jd_form"):
            company = st.text_input("Company *", placeholder="e.g., Tech Corp")
            uploaded_file = st.file_uploader(
                "Choose a Job Description file",
                type=['pdf', 'docx', 'doc'],
                help="Supported formats: PDF, DOCX, DOC"
            )
            
            submit_button = st.form_submit_button("Upload & Parse Job Description")
            
            if submit_button and uploaded_file and company:
                # Prepare file for upload
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                data = {"company": company}
                
                with st.spinner("Parsing job description..."):
                    response = make_api_request("POST", "/jobs/upload", data=data, files=files)
                
                if response:
                    st.success("✅ Job Description uploaded, parsed, and saved to database successfully!")
                    
                    # Display parsed information in a structured way
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("📋 Parsed Job Details")
                        st.write(f"**Job ID:** {response['id']}")
                        st.write(f"**Title:** {response['title']}")
                        st.write(f"**Company:** {response['company']}")
                        if response['location']:
                            st.write(f"**Location:** {response['location']}")
                        if response['skills_required']:
                            st.write(f"**Required Skills:** {', '.join(response['skills_required'][:5])}")
                    
                    with col2:
                        st.subheader("🔍 AI Parsing Results")
                        st.write("**Extracted Fields:**")
                        st.write("✅ Job Title")
                        st.write("✅ Company")
                        st.write("✅ Location")
                        st.write("✅ Skills (Must-have & Nice-to-have)")
                        st.write("✅ Qualifications")
                        st.write("✅ Experience Requirements")
                        st.write("✅ Job Type")
                        st.write("✅ Duration")
                        st.write("✅ Compensation")
                        st.write("✅ Batch Eligibility")
                    
                    st.info("💡 The job has been automatically parsed and saved to the database! It's now available in the Job Board for students to view and apply!")
                    
                    # Add option to upload another job
                    st.markdown("---")
                    st.subheader("📄 Upload Another Job Description")
                    st.markdown("Want to upload another job description? Use the form above to upload another JD file.")
            elif submit_button:
                st.error("Please provide both company name and job description file.")
    
    with tab2:
        st.subheader("Manual Job Entry")
        st.markdown("Fill in the job details manually.")
        
        with st.form("post_job_form"):
            title = st.text_input("Job Title *", placeholder="e.g., Software Engineer")
            company = st.text_input("Company *", placeholder="e.g., Tech Corp")
            location = st.text_input("Location", placeholder="e.g., San Francisco, CA")
            
            description = st.text_area(
                "Job Description *",
                placeholder="Describe the role, responsibilities, and what you're looking for...",
                height=150
            )
            
            requirements = st.text_area(
                "Requirements",
                placeholder="List specific requirements, qualifications, and experience needed...",
                height=100
            )
            
            skills_required = st.text_input(
                "Required Skills (comma-separated)",
                placeholder="e.g., Python, React, SQL, Machine Learning"
            )
            
            skills_preferred = st.text_input(
                "Preferred Skills (comma-separated)",
                placeholder="e.g., AWS, Docker, Kubernetes, Agile"
            )
            
            submit_button = st.form_submit_button("Post Job")
            
            if submit_button:
                if title and company and description:
                    data = {
                        "title": title,
                        "company": company,
                        "location": location,
                        "description": description,
                        "requirements": requirements,
                        "skills_required": [s.strip() for s in skills_required.split(",") if s.strip()],
                        "skills_preferred": [s.strip() for s in skills_preferred.split(",") if s.strip()]
                    }
                    
                    response = make_api_request("POST", "/jobs", data)
                    
                    if response:
                        st.success("Job posted successfully!")
                        st.info(f"Job ID: {response['id']}")
                        
                        # Add continue uploading option
                        st.markdown("---")
                        st.subheader("📄 Continue Uploading")
                        st.markdown("Want to upload another job description or create another manual job?")
                        
                        col5, col6 = st.columns(2)
                        
                        with col5:
                            if st.button("📄 Upload Another JD File", key="continue_upload_jd"):
                                st.info("💡 Use the 'Upload Job Description' tab above to upload another JD file.")
                        
                        with col6:
                            if st.button("✏️ Create Another Manual Job", key="continue_manual_job"):
                                st.info("💡 Fill out the form above again to create another manual job posting.")
                    else:
                        st.error("Please fill in all required fields (marked with *)")
    
    with tab3:
        st.subheader("📦 Bulk Upload Multiple Job Descriptions")
        st.markdown("Upload multiple JD files at once for efficient job posting.")
        
        with st.form("bulk_upload_form"):
            st.write("**Upload multiple JD files:**")
            bulk_files = st.file_uploader(
                "Choose multiple Job Description files",
                type=['pdf', 'docx', 'doc'],
                accept_multiple_files=True,
                help="Select multiple files to upload at once"
            )
            
            bulk_company = st.text_input("Default Company (for all files)", placeholder="e.g., Tech Corp")
            
            bulk_submit = st.form_submit_button("📦 Upload All Files")
            
            if bulk_submit and bulk_files and bulk_company:
                if len(bulk_files) > 10:
                    st.error("❌ Maximum 10 files allowed per bulk upload.")
                else:
                    st.write(f"📁 Uploading {len(bulk_files)} files...")
                    
                    success_count = 0
                    failed_count = 0
                    
                    for i, file in enumerate(bulk_files, 1):
                        with st.spinner(f"Processing file {i}/{len(bulk_files)}: {file.name}"):
                            files_bulk = {"file": (file.name, file.getvalue(), file.type)}
                            data_bulk = {"company": bulk_company}
                            
                            response_bulk = make_api_request("POST", "/jobs/upload", data=data_bulk, files=files_bulk)
                            
                            if response_bulk:
                                success_count += 1
                                st.success(f"✅ File {i}: {file.name} - Job ID: {response_bulk['id']}")
                            else:
                                failed_count += 1
                                st.error(f"❌ File {i}: {file.name} - Upload failed")
                    
                    st.markdown("---")
                    st.subheader("📊 Bulk Upload Results")
                    col7, col8 = st.columns(2)
                    
                    with col7:
                        st.metric("✅ Successful", success_count)
                    
                    with col8:
                        st.metric("❌ Failed", failed_count)
                    
                    if success_count > 0:
                        st.success(f"🎉 Successfully uploaded {success_count} job descriptions!")
                        st.info("💡 All successful jobs are now available in the Job Board for students to view and apply!")
                    
                    if failed_count > 0:
                        st.warning(f"⚠️ {failed_count} files failed to upload. Please check the files and try again.")
            elif bulk_submit:
                st.error("Please provide both company name and at least one file.")

def my_jobs_page():
    """My jobs page for recruiters"""
    st.header("📋 My Job Postings")
    st.markdown("Manage your job postings and view applications.")
    
    # Fetch recruiter's jobs
    jobs = make_api_request("GET", "/jobs/my")
    
    if jobs:
        for job in jobs:
            with st.expander(f"{job['title']} at {job['company']}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Job ID:** {job['id']}")
                    st.write(f"**Company:** {job['company']}")
                    st.write(f"**Location:** {job['location'] or 'Not specified'}")
                    st.write(f"**Posted:** {job['created_at'][:10]}")
                    
                    if job['description']:
                        st.write("**Description:**")
                        st.write(job['description'][:300] + "..." if len(job['description']) > 300 else job['description'])
                
                with col2:
                    if job['skills_required']:
                        st.write("**Required Skills:**")
                        for skill in job['skills_required'][:5]:
                            st.write(f"• {skill}")
                    
                    if st.button(f"View Candidates", key=f"candidates_{job['id']}"):
                        st.session_state.selected_job_id = job['id']
                        st.rerun()
    else:
        st.info("No jobs posted yet. Create your first job posting!")

def candidates_page():
    """Candidates page for recruiters"""
    st.header("👥 Candidates")
    
    if 'selected_job_id' in st.session_state:
        job_id = st.session_state.selected_job_id
        st.write(f"Viewing candidates for Job ID: {job_id}")
        
        # Get resumes for this job
        resumes = make_api_request("GET", f"/resumes/{job_id}")
        
        if resumes:
            st.success(f"Found {len(resumes)} candidates!")
            
            for resume in resumes:
                with st.expander(f"Resume: {resume['original_filename']} (Version {resume['version']})"):
                    st.write(f"**File:** {resume['original_filename']}")
                    st.write(f"**Type:** {resume['file_type'].upper()}")
                    st.write(f"**Version:** {resume['version']}")
                    st.write(f"**Uploaded:** {resume['created_at'][:19]}")
                    
                    if st.button(f"Evaluate Resume", key=f"eval_{resume['id']}"):
                        # Trigger evaluation
                        eval_response = make_api_request("POST", f"/evaluate/{resume['id']}/{job_id}")
                        if eval_response:
                            st.success("Evaluation completed!")
                            st.rerun()
        else:
            st.info("No candidates have applied for this job yet.")
    else:
        st.info("Select a job from 'My Jobs' to view candidates.")

def analytics_page():
    """Analytics page for recruiters"""
    st.header("📈 Analytics Dashboard")
    st.markdown("View insights and analytics for your job postings.")
    
    # Get recruiter's jobs
    jobs = make_api_request("GET", "/jobs/my")
    
    if jobs:
        job_options = {f"{job['title']} at {job['company']}": job['id'] for job in jobs}
        selected_job = st.selectbox("Select a job for analytics", list(job_options.keys()))
        
        if st.button("Generate Analytics"):
            job_id = job_options[selected_job]
            analytics = make_api_request("GET", f"/analytics/{job_id}")
            
            if analytics:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Applications", analytics['total_applications'])
                
                with col2:
                    st.metric("High Fit", analytics['high_fit_count'])
                
                with col3:
                    st.metric("Medium Fit", analytics['medium_fit_count'])
                
                with col4:
                    st.metric("Low Fit", analytics['low_fit_count'])
                
                # Average score
                st.metric("Average Score", f"{analytics['average_score']:.1f}/100")
                
                # Fit distribution pie chart
                if analytics['total_applications'] > 0:
                    fig_pie = px.pie(
                        values=[analytics['high_fit_count'], analytics['medium_fit_count'], analytics['low_fit_count']],
                        names=['High Fit', 'Medium Fit', 'Low Fit'],
                        title="Candidate Fit Distribution",
                        color_discrete_map={'High Fit': '#2E8B57', 'Medium Fit': '#FFD700', 'Low Fit': '#DC143C'}
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                # Skill gaps
                if analytics['skill_gaps']:
                    st.subheader("Most Common Skill Gaps")
                    skill_gaps_df = pd.DataFrame(
                        list(analytics['skill_gaps'].items()),
                        columns=['Skill', 'Count']
                    ).sort_values('Count', ascending=True)
                    
                    fig_bar = px.bar(
                        skill_gaps_df.tail(10),
                        x='Count',
                        y='Skill',
                        orientation='h',
                        title="Top 10 Missing Skills"
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                # Top matched skills
                if analytics['top_skills_matched']:
                    st.subheader("Most Matched Skills")
                    matched_skills_df = pd.DataFrame(analytics['top_skills_matched'])
                    
                    fig_matched = px.bar(
                        matched_skills_df,
                        x='count',
                        y='skill',
                        orientation='h',
                        title="Top Matched Skills"
                    )
                    st.plotly_chart(fig_matched, use_container_width=True)
            else:
                st.error("No analytics data available for this job.")
    else:
        st.info("No jobs posted yet. Create a job posting to see analytics.")

def main():
    """Main application"""
    st.set_page_config(
        page_title="HireLens Enhanced",
        page_icon="🔍",
        layout="wide"
    )
    
    # Check if user is logged in
    if not st.session_state.access_token:
        login_page()
    else:
        # Show logout button
        with st.sidebar:
            st.write(f"Logged in as: **{st.session_state.user_role.title()}**")
            if st.button("Logout"):
                st.session_state.access_token = None
                st.session_state.user_role = None
                st.session_state.user_id = None
                st.rerun()
        
        # Route to appropriate dashboard
        if st.session_state.user_role == "student":
            student_dashboard()
        elif st.session_state.user_role == "recruiter":
            recruiter_dashboard()
        else:
            st.error("Invalid user role")

if __name__ == "__main__":
    main()
