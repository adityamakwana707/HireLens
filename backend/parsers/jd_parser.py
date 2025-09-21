"""
Job Description parsing utilities for HireLens
"""
import re
import json
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class JDParser:
    """Parse job descriptions and extract requirements"""
    
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
        
        self.experience_levels = [
            'entry', 'junior', 'mid', 'senior', 'lead', 'principal', 'architect',
            'intern', 'internship', 'graduate', 'fresher', 'experienced'
        ]
        
        self.employment_types = [
            'full-time', 'part-time', 'contract', 'freelance', 'internship',
            'temporary', 'permanent', 'remote', 'hybrid', 'onsite'
        ]

    def parse_jd(self, jd_text: str) -> Dict[str, Any]:
        """Parse job description and extract structured data"""
        jd_lower = jd_text.lower()
        
        return {
            'title': self._extract_job_title(jd_text),
            'company': self._extract_company(jd_text),
            'location': self._extract_location(jd_text),
            'skills_required': self._extract_required_skills(jd_lower),
            'skills_preferred': self._extract_preferred_skills(jd_lower),
            'experience_level': self._extract_experience_level(jd_lower),
            'employment_type': self._extract_employment_type(jd_lower),
            'salary_range': self._extract_salary_range(jd_text),
            'requirements': self._extract_requirements(jd_text),
            'responsibilities': self._extract_responsibilities(jd_text),
            'benefits': self._extract_benefits(jd_text)
        }

    def _extract_job_title(self, text: str) -> str:
        """Extract job title from JD"""
        # Look for common job title patterns
        title_patterns = [
            r'job title[:\s]*([^\n]+)',
            r'position[:\s]*([^\n]+)',
            r'role[:\s]*([^\n]+)',
            r'^([A-Z][^,\n]*?(?:developer|engineer|analyst|manager|specialist|coordinator|director|lead|architect)[^,\n]*?)(?:\n|$)',
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()
        
        # Fallback: first line that looks like a title
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if len(line) > 5 and len(line) < 100 and any(word in line.lower() for word in ['developer', 'engineer', 'analyst', 'manager']):
                return line
        
        return "Not specified"

    def _extract_company(self, text: str) -> str:
        """Extract company name from JD"""
        company_patterns = [
            r'company[:\s]*([^\n]+)',
            r'organization[:\s]*([^\n]+)',
            r'about\s+([A-Z][^,\n]+)',
            r'at\s+([A-Z][^,\n]+)',
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Not specified"

    def _extract_location(self, text: str) -> str:
        """Extract job location from JD"""
        location_patterns = [
            r'location[:\s]*([^\n]+)',
            r'based\s+in\s+([^\n]+)',
            r'office\s+location[:\s]*([^\n]+)',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Not specified"

    def _extract_required_skills(self, text: str) -> List[str]:
        """Extract required skills from JD"""
        required_skills = []
        
        # Look for required skills section
        required_section = re.search(r'(?:required|must have|essential|mandatory)[:\s]*(.*?)(?=\n\n|\n[A-Z]|$)', text, re.IGNORECASE | re.DOTALL)
        if required_section:
            skills_text = required_section.group(1)
            required_skills.extend(self._extract_skills_from_text(skills_text))
        
        # Also look for skills mentioned with "required" or "must"
        required_pattern = r'([a-z\s]+?)\s+(?:required|must|essential|mandatory)'
        matches = re.findall(required_pattern, text)
        for match in matches:
            skill = match.strip()
            if skill in self.skill_keywords:
                required_skills.append(skill.title())
        
        return list(set(required_skills))

    def _extract_preferred_skills(self, text: str) -> List[str]:
        """Extract preferred skills from JD"""
        preferred_skills = []
        
        # Look for preferred skills section
        preferred_section = re.search(r'(?:preferred|nice to have|good to have|plus|bonus)[:\s]*(.*?)(?=\n\n|\n[A-Z]|$)', text, re.IGNORECASE | re.DOTALL)
        if preferred_section:
            skills_text = preferred_section.group(1)
            preferred_skills.extend(self._extract_skills_from_text(skills_text))
        
        # Also look for skills mentioned with "preferred" or "nice to have"
        preferred_pattern = r'([a-z\s]+?)\s+(?:preferred|nice to have|good to have|plus|bonus)'
        matches = re.findall(preferred_pattern, text)
        for match in matches:
            skill = match.strip()
            if skill in self.skill_keywords:
                preferred_skills.append(skill.title())
        
        return list(set(preferred_skills))

    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skills from a given text"""
        found_skills = []
        
        for skill in self.skill_keywords:
            if skill in text:
                found_skills.append(skill.title())
        
        # Also look for skills mentioned in bullet points or lists
        skill_list = re.findall(r'[•\-\*]\s*([^,\n]+?)(?:\s*[,;]|\s*$)', text)
        for skill in skill_list:
            skill = skill.strip()
            if len(skill) > 2 and skill.lower() in self.skill_keywords:
                found_skills.append(skill.title())
        
        return found_skills

    def _extract_experience_level(self, text: str) -> str:
        """Extract experience level from JD"""
        for level in self.experience_levels:
            if level in text:
                return level.title()
        
        # Look for years of experience
        years_pattern = r'(\d+)[\s\-]*(?:to\s*)?(\d+)?\s*years?\s*(?:of\s*)?experience'
        match = re.search(years_pattern, text)
        if match:
            min_years = int(match.group(1))
            max_years = int(match.group(2)) if match.group(2) else min_years
            
            if min_years <= 2:
                return "Entry Level"
            elif min_years <= 5:
                return "Mid Level"
            else:
                return "Senior Level"
        
        return "Not specified"

    def _extract_employment_type(self, text: str) -> str:
        """Extract employment type from JD"""
        for emp_type in self.employment_types:
            if emp_type in text:
                return emp_type.title()
        
        return "Not specified"

    def _extract_salary_range(self, text: str) -> str:
        """Extract salary range from JD"""
        salary_patterns = [
            r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)\s*[-–]\s*\$(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*[-–]\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:per\s*)?(?:year|annually|month|monthly)',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:to\s*)?(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:per\s*)?(?:year|annually|month|monthly)'
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return f"${match.group(1)} - ${match.group(2)}"
        
        return "Not specified"

    def _extract_requirements(self, text: str) -> List[str]:
        """Extract job requirements"""
        requirements = []
        
        # Look for requirements section
        req_section = re.search(r'requirements?[:\s]*(.*?)(?=\n\n|\n[A-Z]|$)', text, re.IGNORECASE | re.DOTALL)
        if req_section:
            req_text = req_section.group(1)
            
            # Split by bullet points or new lines
            req_list = re.split(r'[•\-\*]\s*|\n\s*\d+\.\s*', req_text)
            for req in req_list:
                req = req.strip()
                if len(req) > 10:  # Filter out very short requirements
                    requirements.append(req)
        
        return requirements

    def _extract_responsibilities(self, text: str) -> List[str]:
        """Extract job responsibilities"""
        responsibilities = []
        
        # Look for responsibilities section
        resp_section = re.search(r'responsibilities?[:\s]*(.*?)(?=\n\n|\n[A-Z]|$)', text, re.IGNORECASE | re.DOTALL)
        if resp_section:
            resp_text = resp_section.group(1)
            
            # Split by bullet points or new lines
            resp_list = re.split(r'[•\-\*]\s*|\n\s*\d+\.\s*', resp_text)
            for resp in resp_list:
                resp = resp.strip()
                if len(resp) > 10:  # Filter out very short responsibilities
                    responsibilities.append(resp)
        
        return responsibilities

    def _extract_benefits(self, text: str) -> List[str]:
        """Extract job benefits"""
        benefits = []
        
        # Look for benefits section
        benefits_section = re.search(r'benefits?[:\s]*(.*?)(?=\n\n|\n[A-Z]|$)', text, re.IGNORECASE | re.DOTALL)
        if benefits_section:
            benefits_text = benefits_section.group(1)
            
            # Split by bullet points or new lines
            benefits_list = re.split(r'[•\-\*]\s*|\n\s*\d+\.\s*', benefits_text)
            for benefit in benefits_list:
                benefit = benefit.strip()
                if len(benefit) > 5:  # Filter out very short benefits
                    benefits.append(benefit)
        
        return benefits
