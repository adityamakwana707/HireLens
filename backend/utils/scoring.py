"""
Scoring utilities for HireLens
"""
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class ScoringEngine:
    """Calculate final scores and verdicts for resume-JD matching"""
    
    def __init__(self):
        self.verdict_thresholds = {
            'high': 75,
            'medium': 50,
            'low': 0
        }
    
    def calculate_final_score(
        self, 
        hard_match_score: float, 
        soft_match_score: float,
        hard_weight: float = 0.5,
        soft_weight: float = 0.5
    ) -> Dict[str, float]:
        """
        Calculate final weighted score from hard and soft match scores
        
        Args:
            hard_match_score: Hard match score (0-100)
            soft_match_score: Soft match score (0-100)
            hard_weight: Weight for hard match (default 0.5)
            soft_weight: Weight for soft match (default 0.5)
            
        Returns:
            Dictionary with final score and breakdown
        """
        # Ensure weights sum to 1
        total_weight = hard_weight + soft_weight
        if total_weight > 0:
            hard_weight = hard_weight / total_weight
            soft_weight = soft_weight / total_weight
        else:
            hard_weight = soft_weight = 0.5
        
        # Calculate weighted final score
        final_score = (hard_match_score * hard_weight) + (soft_match_score * soft_weight)
        
        return {
            'final_score': round(final_score, 2),
            'hard_match_score': round(hard_match_score, 2),
            'soft_match_score': round(soft_match_score, 2),
            'hard_weight': hard_weight,
            'soft_weight': soft_weight
        }
    
    def determine_verdict(self, final_score: float) -> str:
        """
        Determine verdict based on final score
        
        Args:
            final_score: Final score (0-100)
            
        Returns:
            Verdict string (High, Medium, Low)
        """
        if final_score >= self.verdict_thresholds['high']:
            return 'High'
        elif final_score >= self.verdict_thresholds['medium']:
            return 'Medium'
        else:
            return 'Low'
    
    def calculate_skill_coverage(
        self, 
        resume_skills: List[str], 
        jd_required_skills: List[str],
        jd_preferred_skills: List[str] = None
    ) -> Dict[str, float]:
        """
        Calculate skill coverage percentage
        
        Args:
            resume_skills: List of skills from resume
            jd_required_skills: List of required skills from JD
            jd_preferred_skills: List of preferred skills from JD
            
        Returns:
            Dictionary with coverage percentages
        """
        if jd_preferred_skills is None:
            jd_preferred_skills = []
        
        # Normalize skills to lowercase
        resume_skills_lower = [skill.lower().strip() for skill in resume_skills]
        jd_required_lower = [skill.lower().strip() for skill in jd_required_skills]
        jd_preferred_lower = [skill.lower().strip() for skill in jd_preferred_skills]
        
        # Calculate required skills coverage
        required_matches = 0
        for skill in jd_required_lower:
            if any(self._skill_match(skill, resume_skill) for resume_skill in resume_skills_lower):
                required_matches += 1
        
        required_coverage = (required_matches / len(jd_required_lower) * 100) if jd_required_lower else 0
        
        # Calculate preferred skills coverage
        preferred_matches = 0
        for skill in jd_preferred_lower:
            if any(self._skill_match(skill, resume_skill) for resume_skill in resume_skills_lower):
                preferred_matches += 1
        
        preferred_coverage = (preferred_matches / len(jd_preferred_lower) * 100) if jd_preferred_lower else 0
        
        # Calculate overall coverage
        total_jd_skills = len(jd_required_lower) + len(jd_preferred_lower)
        total_matches = required_matches + preferred_matches
        overall_coverage = (total_matches / total_jd_skills * 100) if total_jd_skills > 0 else 0
        
        return {
            'required_coverage': round(required_coverage, 2),
            'preferred_coverage': round(preferred_coverage, 2),
            'overall_coverage': round(overall_coverage, 2),
            'required_matches': required_matches,
            'preferred_matches': preferred_matches,
            'total_matches': total_matches
        }
    
    def get_matched_skills(
        self, 
        resume_skills: List[str], 
        jd_required_skills: List[str],
        jd_preferred_skills: List[str] = None
    ) -> Dict[str, List[str]]:
        """
        Get matched and missing skills
        
        Args:
            resume_skills: List of skills from resume
            jd_required_skills: List of required skills from JD
            jd_preferred_skills: List of preferred skills from JD
            
        Returns:
            Dictionary with matched and missing skills
        """
        if jd_preferred_skills is None:
            jd_preferred_skills = []
        
        # Normalize skills to lowercase
        resume_skills_lower = [skill.lower().strip() for skill in resume_skills]
        jd_required_lower = [skill.lower().strip() for skill in jd_required_skills]
        jd_preferred_lower = [skill.lower().strip() for skill in jd_preferred_skills]
        
        # Find matched skills
        matched_required = []
        matched_preferred = []
        
        for skill in jd_required_lower:
            for resume_skill in resume_skills_lower:
                if self._skill_match(skill, resume_skill):
                    matched_required.append(skill.title())
                    break
        
        for skill in jd_preferred_lower:
            for resume_skill in resume_skills_lower:
                if self._skill_match(skill, resume_skill):
                    matched_preferred.append(skill.title())
                    break
        
        # Find missing skills
        missing_required = [skill.title() for skill in jd_required_lower if skill not in matched_required]
        missing_preferred = [skill.title() for skill in jd_preferred_lower if skill not in matched_preferred]
        
        return {
            'matched_required': matched_required,
            'matched_preferred': matched_preferred,
            'missing_required': missing_required,
            'missing_preferred': missing_preferred,
            'all_matched': matched_required + matched_preferred,
            'all_missing': missing_required + missing_preferred
        }
    
    def _skill_match(self, skill1: str, skill2: str) -> bool:
        """Check if two skills match (exact or partial)"""
        skill1 = skill1.lower().strip()
        skill2 = skill2.lower().strip()
        
        # Exact match
        if skill1 == skill2:
            return True
        
        # Partial match (one contains the other)
        if skill1 in skill2 or skill2 in skill1:
            return True
        
        # Check for common variations
        variations = {
            'javascript': ['js', 'ecmascript'],
            'python': ['py'],
            'c++': ['cpp', 'c plus plus'],
            'c#': ['csharp', 'c sharp'],
            'html': ['html5'],
            'css': ['css3'],
            'react': ['reactjs', 'react.js'],
            'node.js': ['nodejs', 'node'],
            'machine learning': ['ml', 'machinelearning'],
            'artificial intelligence': ['ai', 'artificialintelligence'],
            'data science': ['datascience'],
            'web development': ['webdev', 'web development'],
            'mobile development': ['mobiledev', 'mobile development']
        }
        
        for key, variants in variations.items():
            if (skill1 == key and skill2 in variants) or (skill2 == key and skill1 in variants):
                return True
        
        return False
    
    def calculate_experience_score(
        self, 
        resume_experience: List[Dict], 
        jd_experience_level: str
    ) -> float:
        """
        Calculate experience score based on resume experience and JD requirements
        
        Args:
            resume_experience: List of experience entries from resume
            jd_experience_level: Required experience level from JD
            
        Returns:
            Experience score (0-100)
        """
        if not resume_experience or not jd_experience_level:
            return 0.0
        
        # Calculate total years of experience
        total_years = 0
        for exp in resume_experience:
            # Extract years from duration (simplified)
            duration = exp.get('duration', '')
            years = self._extract_years_from_duration(duration)
            total_years += years
        
        # Map JD experience level to years
        jd_years_map = {
            'entry': 0,
            'junior': 1,
            'mid': 3,
            'senior': 5,
            'lead': 7,
            'principal': 10,
            'architect': 10
        }
        
        required_years = jd_years_map.get(jd_experience_level.lower(), 0)
        
        if total_years >= required_years:
            return 100.0
        elif required_years > 0:
            return min((total_years / required_years) * 100, 100.0)
        else:
            return 50.0  # Default score if no specific requirement
    
    def _extract_years_from_duration(self, duration: str) -> float:
        """Extract years from duration string"""
        if not duration:
            return 0.0
        
        duration = duration.lower()
        
        # Look for year patterns
        import re
        
        # Pattern for "X years" or "X year"
        year_match = re.search(r'(\d+(?:\.\d+)?)\s*years?', duration)
        if year_match:
            return float(year_match.group(1))
        
        # Pattern for "X months" - convert to years
        month_match = re.search(r'(\d+(?:\.\d+)?)\s*months?', duration)
        if month_match:
            return float(month_match.group(1)) / 12
        
        # Pattern for date ranges (simplified)
        date_range_match = re.search(r'(\d{4})\s*[-–]\s*(\d{4})', duration)
        if date_range_match:
            start_year = int(date_range_match.group(1))
            end_year = int(date_range_match.group(2))
            return end_year - start_year
        
        return 0.0
