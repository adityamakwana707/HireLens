"""
Hard matching algorithms for resume-JD comparison
"""
import re
from typing import List, Dict, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from rank_bm25 import BM25Okapi
from rapidfuzz import fuzz, process
import numpy as np
import logging

logger = logging.getLogger(__name__)

class HardMatcher:
    """Hard matching using TF-IDF, BM25, and Fuzzy matching"""
    
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            max_features=1000
        )
    
    def calculate_hard_match_score(
        self, 
        resume_text: str, 
        jd_text: str,
        resume_skills: List[str],
        jd_required_skills: List[str],
        jd_preferred_skills: List[str] = None
    ) -> Dict[str, float]:
        """
        Calculate hard match score using multiple algorithms
        
        Args:
            resume_text: Raw resume text
            jd_text: Raw job description text
            resume_skills: List of skills from resume
            jd_required_skills: List of required skills from JD
            jd_preferred_skills: List of preferred skills from JD
            
        Returns:
            Dictionary with scores and details
        """
        if jd_preferred_skills is None:
            jd_preferred_skills = []
        
        # Calculate different types of scores
        tfidf_score = self._calculate_tfidf_score(resume_text, jd_text)
        bm25_score = self._calculate_bm25_score(resume_text, jd_text)
        skill_match_score = self._calculate_skill_match_score(
            resume_skills, jd_required_skills, jd_preferred_skills
        )
        fuzzy_score = self._calculate_fuzzy_score(resume_text, jd_text)
        
        # Weighted combination of scores
        weights = {
            'tfidf': 0.25,
            'bm25': 0.25,
            'skill_match': 0.35,
            'fuzzy': 0.15
        }
        
        overall_score = (
            tfidf_score * weights['tfidf'] +
            bm25_score * weights['bm25'] +
            skill_match_score * weights['skill_match'] +
            fuzzy_score * weights['fuzzy']
        )
        
        return {
            'overall_score': round(overall_score, 2),
            'tfidf_score': round(tfidf_score, 2),
            'bm25_score': round(bm25_score, 2),
            'skill_match_score': round(skill_match_score, 2),
            'fuzzy_score': round(fuzzy_score, 2),
            'weights': weights
        }
    
    def _calculate_tfidf_score(self, resume_text: str, jd_text: str) -> float:
        """Calculate TF-IDF similarity score"""
        try:
            # Clean and preprocess texts
            resume_clean = self._preprocess_text(resume_text)
            jd_clean = self._preprocess_text(jd_text)
            
            if not resume_clean or not jd_clean:
                return 0.0
            
            # Create TF-IDF vectors
            corpus = [resume_clean, jd_clean]
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(corpus)
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(
                tfidf_matrix[0].toarray().flatten(),
                tfidf_matrix[1].toarray().flatten()
            )
            
            return similarity * 100  # Convert to 0-100 scale
            
        except Exception as e:
            logger.error(f"Error calculating TF-IDF score: {e}")
            return 0.0
    
    def _calculate_bm25_score(self, resume_text: str, jd_text: str) -> float:
        """Calculate BM25 similarity score"""
        try:
            # Tokenize texts
            resume_tokens = self._tokenize_text(resume_text)
            jd_tokens = self._tokenize_text(jd_text)
            
            if not resume_tokens or not jd_tokens:
                return 0.0
            
            # Create BM25 index
            corpus = [resume_tokens, jd_tokens]
            bm25 = BM25Okapi(corpus)
            
            # Calculate BM25 score for resume against JD
            scores = bm25.get_scores(resume_tokens)
            jd_score = scores[1]  # Score against JD (index 1)
            
            # Normalize to 0-100 scale
            max_score = max(scores) if len(scores) > 0 else 1
            normalized_score = (jd_score / max_score) * 100 if max_score > 0 else 0
            
            return min(normalized_score, 100)
            
        except Exception as e:
            logger.error(f"Error calculating BM25 score: {e}")
            return 0.0
    
    def _calculate_skill_match_score(
        self, 
        resume_skills: List[str], 
        jd_required_skills: List[str],
        jd_preferred_skills: List[str]
    ) -> float:
        """Calculate skill matching score"""
        if not jd_required_skills and not jd_preferred_skills:
            return 0.0
        
        # Normalize skills to lowercase for comparison
        resume_skills_lower = [skill.lower().strip() for skill in resume_skills]
        jd_required_lower = [skill.lower().strip() for skill in jd_required_skills]
        jd_preferred_lower = [skill.lower().strip() for skill in jd_preferred_skills]
        
        # Calculate required skills match
        required_matches = 0
        for skill in jd_required_lower:
            if any(self._skill_fuzzy_match(skill, resume_skill) for resume_skill in resume_skills_lower):
                required_matches += 1
        
        # Calculate preferred skills match
        preferred_matches = 0
        for skill in jd_preferred_lower:
            if any(self._skill_fuzzy_match(skill, resume_skill) for resume_skill in resume_skills_lower):
                preferred_matches += 1
        
        # Calculate weighted score
        total_required = len(jd_required_lower)
        total_preferred = len(jd_preferred_lower)
        
        if total_required == 0 and total_preferred == 0:
            return 0.0
        
        # Required skills have higher weight (70%) than preferred skills (30%)
        required_score = (required_matches / total_required * 100) if total_required > 0 else 0
        preferred_score = (preferred_matches / total_preferred * 100) if total_preferred > 0 else 0
        
        # Weighted combination
        if total_required > 0 and total_preferred > 0:
            final_score = (required_score * 0.7) + (preferred_score * 0.3)
        elif total_required > 0:
            final_score = required_score
        else:
            final_score = preferred_score
        
        return min(final_score, 100)
    
    def _calculate_fuzzy_score(self, resume_text: str, jd_text: str) -> float:
        """Calculate fuzzy matching score"""
        try:
            # Extract key phrases from both texts
            resume_phrases = self._extract_key_phrases(resume_text)
            jd_phrases = self._extract_key_phrases(jd_text)
            
            if not resume_phrases or not jd_phrases:
                return 0.0
            
            # Calculate fuzzy matching scores
            total_score = 0
            match_count = 0
            
            for jd_phrase in jd_phrases:
                best_match = process.extractOne(
                    jd_phrase, 
                    resume_phrases, 
                    scorer=fuzz.token_sort_ratio
                )
                
                if best_match and best_match[1] > 60:  # Threshold for good match
                    total_score += best_match[1]
                    match_count += 1
            
            if match_count == 0:
                return 0.0
            
            average_score = total_score / match_count
            return min(average_score, 100)
            
        except Exception as e:
            logger.error(f"Error calculating fuzzy score: {e}")
            return 0.0
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for matching"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _tokenize_text(self, text: str) -> List[str]:
        """Tokenize text for BM25"""
        if not text:
            return []
        
        # Simple tokenization
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens
    
    def _skill_fuzzy_match(self, skill1: str, skill2: str, threshold: int = 80) -> bool:
        """Check if two skills match using fuzzy matching"""
        return fuzz.ratio(skill1, skill2) >= threshold or \
               fuzz.partial_ratio(skill1, skill2) >= threshold or \
               fuzz.token_sort_ratio(skill1, skill2) >= threshold
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text"""
        if not text:
            return []
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        
        # Extract phrases (2-4 words)
        phrases = []
        for sentence in sentences:
            words = sentence.strip().split()
            for i in range(len(words) - 1):
                for j in range(i + 2, min(i + 5, len(words) + 1)):
                    phrase = ' '.join(words[i:j])
                    if len(phrase) > 5:  # Filter out very short phrases
                        phrases.append(phrase.strip())
        
        return phrases[:50]  # Limit to top 50 phrases
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except:
            return 0.0
