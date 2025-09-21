"""
Resume parsing utilities for HireLens
"""
import pdfplumber
import docx2txt
import re
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ResumeParser:
    """Parse resumes from PDF and DOCX files"""
    
    def __init__(self):
        self.skill_keywords = [
            # Programming Languages
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust',
            'swift', 'kotlin', 'scala', 'r', 'matlab', 'perl', 'bash', 'powershell',
            
            # Web Technologies
            'html', 'css', 'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask',
            'spring', 'laravel', 'asp.net', 'jquery', 'bootstrap', 'tailwind', 'sass', 'less',
            
            # Databases
            'mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 'oracle', 'sql server',
            'cassandra', 'elasticsearch', 'dynamodb', 'neo4j',
            
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git', 'github', 'gitlab',
            'terraform', 'ansible', 'chef', 'puppet', 'ci/cd', 'devops',
            
            # Data Science & ML
            'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'keras', 'opencv',
            'matplotlib', 'seaborn', 'plotly', 'jupyter', 'spark', 'hadoop',
            
            # Mobile Development
            'android', 'ios', 'react native', 'flutter', 'xamarin', 'ionic',
            
            # Other Technologies
            'linux', 'windows', 'macos', 'api', 'rest', 'graphql', 'microservices',
            'agile', 'scrum', 'jira', 'confluence', 'slack', 'figma', 'photoshop'
        ]
        
        self.education_keywords = [
            'education', 'degree', 'bachelor', 'master', 'phd', 'diploma', 'certificate',
            'university', 'college', 'institute', 'school', 'graduation', 'gpa', 'cgpa'
        ]
        
        self.experience_keywords = [
            'experience', 'work', 'employment', 'career', 'professional', 'internship',
            'freelance', 'consultant', 'contract', 'volunteer', 'projects'
        ]

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """Parse resume file and extract structured data"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Extract text based on file type
        if file_path.suffix.lower() == '.pdf':
            text = self._extract_pdf_text(file_path)
        elif file_path.suffix.lower() in ['.docx', '.doc']:
            text = self._extract_docx_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")
        
        # Parse the extracted text
        parsed_data = self._parse_text(text)
        parsed_data['raw_text'] = text
        parsed_data['file_type'] = file_path.suffix.lower()
        
        return parsed_data

    def _extract_pdf_text(self, file_path: Path) -> str:
        """Extract text from PDF file"""
        try:
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text.strip()
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            raise

    def _extract_docx_text(self, file_path: Path) -> str:
        """Extract text from DOCX file"""
        try:
            return docx2txt.process(str(file_path))
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {e}")
            raise

    def _parse_text(self, text: str) -> Dict[str, Any]:
        """Parse extracted text and extract structured information"""
        text_lower = text.lower()
        
        return {
            'skills': self._extract_skills(text_lower),
            'education': self._extract_education(text),
            'experience': self._extract_experience(text),
            'projects': self._extract_projects(text),
            'certifications': self._extract_certifications(text),
            'contact_info': self._extract_contact_info(text)
        }

    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text"""
        found_skills = []
        
        for skill in self.skill_keywords:
            if skill in text:
                found_skills.append(skill.title())
        
        # Also look for skills mentioned in specific sections
        skills_section = re.search(r'skills?[:\s]*(.*?)(?=\n\n|\n[A-Z]|$)', text, re.IGNORECASE | re.DOTALL)
        if skills_section:
            skills_text = skills_section.group(1)
            # Extract individual skills from the skills section
            skill_list = re.findall(r'\b\w+(?:\s+\w+)*\b', skills_text)
            for skill in skill_list:
                if len(skill) > 2 and skill.lower() not in [s.lower() for s in found_skills]:
                    found_skills.append(skill.title())
        
        return list(set(found_skills))

    def _extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education information"""
        education = []
        
        # Look for education section
        education_section = re.search(r'education[:\s]*(.*?)(?=\n\n|\n[A-Z]|$)', text, re.IGNORECASE | re.DOTALL)
        if education_section:
            edu_text = education_section.group(1)
            
            # Extract degree information
            degree_patterns = [
                r'(bachelor[^,\n]*)',
                r'(master[^,\n]*)',
                r'(phd[^,\n]*)',
                r'(diploma[^,\n]*)',
                r'(certificate[^,\n]*)'
            ]
            
            for pattern in degree_patterns:
                matches = re.findall(pattern, edu_text, re.IGNORECASE)
                for match in matches:
                    education.append({
                        'degree': match.strip(),
                        'institution': 'Not specified',
                        'year': 'Not specified'
                    })
        
        return education

    def _extract_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract work experience information"""
        experience = []
        
        # Look for experience section
        exp_section = re.search(r'experience[:\s]*(.*?)(?=\n\n|\n[A-Z]|$)', text, re.IGNORECASE | re.DOTALL)
        if exp_section:
            exp_text = exp_section.group(1)
            
            # Extract job titles and companies
            job_pattern = r'([A-Z][^,\n]*?)\s*at\s*([A-Z][^,\n]*?)(?:\s*\([^)]*\))?'
            matches = re.findall(job_pattern, exp_text)
            
            for title, company in matches:
                experience.append({
                    'title': title.strip(),
                    'company': company.strip(),
                    'duration': 'Not specified',
                    'description': 'Not specified'
                })
        
        return experience

    def _extract_projects(self, text: str) -> List[Dict[str, str]]:
        """Extract project information"""
        projects = []
        
        # Look for projects section
        projects_section = re.search(r'projects?[:\s]*(.*?)(?=\n\n|\n[A-Z]|$)', text, re.IGNORECASE | re.DOTALL)
        if projects_section:
            projects_text = projects_section.group(1)
            
            # Extract project names and descriptions
            project_pattern = r'([A-Z][^,\n]*?)[:\s]*(.*?)(?=\n[A-Z]|\n\n|$)'
            matches = re.findall(project_pattern, projects_text)
            
            for name, description in matches:
                projects.append({
                    'name': name.strip(),
                    'description': description.strip()[:200] + '...' if len(description.strip()) > 200 else description.strip(),
                    'technologies': 'Not specified'
                })
        
        return projects

    def _extract_certifications(self, text: str) -> List[Dict[str, str]]:
        """Extract certification information"""
        certifications = []
        
        # Look for certifications section
        cert_section = re.search(r'certifications?[:\s]*(.*?)(?=\n\n|\n[A-Z]|$)', text, re.IGNORECASE | re.DOTALL)
        if cert_section:
            cert_text = cert_section.group(1)
            
            # Extract certification names
            cert_list = re.findall(r'([A-Z][^,\n]*?)(?:\s*\([^)]*\))?', cert_text)
            for cert in cert_list:
                if len(cert.strip()) > 3:
                    certifications.append({
                        'name': cert.strip(),
                        'issuer': 'Not specified',
                        'date': 'Not specified'
                    })
        
        return certifications

    def _extract_contact_info(self, text: str) -> Dict[str, str]:
        """Extract contact information"""
        contact = {}
        
        # Email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            contact['email'] = email_match.group()
        
        # Phone
        phone_pattern = r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            contact['phone'] = phone_match.group()
        
        # LinkedIn
        linkedin_pattern = r'linkedin\.com/in/[A-Za-z0-9-]+'
        linkedin_match = re.search(linkedin_pattern, text)
        if linkedin_match:
            contact['linkedin'] = linkedin_match.group()
        
        # GitHub
        github_pattern = r'github\.com/[A-Za-z0-9-]+'
        github_match = re.search(github_pattern, text)
        if github_match:
            contact['github'] = github_match.group()
        
        return contact
