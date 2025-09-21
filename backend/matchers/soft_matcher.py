"""
Soft matching using semantic similarity and embeddings
"""
import os
from typing import List, Dict, Tuple, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class SoftMatcher:
    """Soft matching using semantic similarity and embeddings"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the soft matcher with a sentence transformer model
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        self.model = None
        self.index = None
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model"""
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded model: {self.model_name}")
        except Exception as e:
            logger.error(f"Error loading model {self.model_name}: {e}")
            # Fallback to a smaller model
            try:
                self.model = SentenceTransformer("paraphrase-MiniLM-L6-v2")
                logger.info("Loaded fallback model: paraphrase-MiniLM-L6-v2")
            except Exception as e2:
                logger.error(f"Error loading fallback model: {e2}")
                raise
    
    def calculate_soft_match_score(
        self, 
        resume_text: str, 
        jd_text: str,
        resume_skills: List[str],
        jd_required_skills: List[str],
        jd_preferred_skills: List[str] = None
    ) -> Dict[str, float]:
        """
        Calculate soft match score using semantic similarity
        
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
        
        try:
            # Calculate different types of semantic scores
            text_similarity = self._calculate_text_similarity(resume_text, jd_text)
            skill_similarity = self._calculate_skill_similarity(
                resume_skills, jd_required_skills, jd_preferred_skills
            )
            context_similarity = self._calculate_context_similarity(resume_text, jd_text)
            
            # Weighted combination of scores
            weights = {
                'text_similarity': 0.4,
                'skill_similarity': 0.4,
                'context_similarity': 0.2
            }
            
            overall_score = (
                text_similarity * weights['text_similarity'] +
                skill_similarity * weights['skill_similarity'] +
                context_similarity * weights['context_similarity']
            )
            
            return {
                'overall_score': round(overall_score, 2),
                'text_similarity': round(text_similarity, 2),
                'skill_similarity': round(skill_similarity, 2),
                'context_similarity': round(context_similarity, 2),
                'weights': weights
            }
            
        except Exception as e:
            logger.error(f"Error calculating soft match score: {e}")
            return {
                'overall_score': 0.0,
                'text_similarity': 0.0,
                'skill_similarity': 0.0,
                'context_similarity': 0.0,
                'weights': weights
            }
    
    def _calculate_text_similarity(self, resume_text: str, jd_text: str) -> float:
        """Calculate semantic similarity between resume and JD text"""
        try:
            if not resume_text or not jd_text:
                return 0.0
            
            # Generate embeddings
            resume_embedding = self.model.encode([resume_text])
            jd_embedding = self.model.encode([jd_text])
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(
                resume_embedding[0], 
                jd_embedding[0]
            )
            
            return similarity * 100  # Convert to 0-100 scale
            
        except Exception as e:
            logger.error(f"Error calculating text similarity: {e}")
            return 0.0
    
    def _calculate_skill_similarity(
        self, 
        resume_skills: List[str], 
        jd_required_skills: List[str],
        jd_preferred_skills: List[str]
    ) -> float:
        """Calculate semantic similarity between skills"""
        try:
            if not resume_skills or (not jd_required_skills and not jd_preferred_skills):
                return 0.0
            
            # Combine required and preferred skills
            all_jd_skills = jd_required_skills + jd_preferred_skills
            
            # Generate embeddings for skills
            resume_skill_embeddings = self.model.encode(resume_skills)
            jd_skill_embeddings = self.model.encode(all_jd_skills)
            
            # Calculate similarity matrix
            similarity_matrix = self._cosine_similarity_matrix(
                resume_skill_embeddings, 
                jd_skill_embeddings
            )
            
            # Find best matches for each JD skill
            max_similarities = np.max(similarity_matrix, axis=0)
            
            # Weight required skills more heavily
            required_count = len(jd_required_skills)
            preferred_count = len(jd_preferred_skills)
            
            if required_count > 0 and preferred_count > 0:
                required_similarities = max_similarities[:required_count]
                preferred_similarities = max_similarities[required_count:]
                
                # Weighted average (70% required, 30% preferred)
                avg_required = np.mean(required_similarities)
                avg_preferred = np.mean(preferred_similarities)
                final_score = (avg_required * 0.7) + (avg_preferred * 0.3)
            else:
                final_score = np.mean(max_similarities)
            
            return final_score * 100  # Convert to 0-100 scale
            
        except Exception as e:
            logger.error(f"Error calculating skill similarity: {e}")
            return 0.0
    
    def _calculate_context_similarity(self, resume_text: str, jd_text: str) -> float:
        """Calculate context similarity by comparing key sections"""
        try:
            # Extract key sections from both texts
            resume_sections = self._extract_key_sections(resume_text)
            jd_sections = self._extract_key_sections(jd_text)
            
            if not resume_sections or not jd_sections:
                return 0.0
            
            # Calculate similarity for each section
            section_similarities = []
            
            for jd_section in jd_sections:
                best_similarity = 0.0
                for resume_section in resume_sections:
                    # Generate embeddings for sections
                    jd_embedding = self.model.encode([jd_section])
                    resume_embedding = self.model.encode([resume_section])
                    
                    # Calculate similarity
                    similarity = self._cosine_similarity(
                        jd_embedding[0], 
                        resume_embedding[0]
                    )
                    
                    best_similarity = max(best_similarity, similarity)
                
                section_similarities.append(best_similarity)
            
            # Return average similarity
            return np.mean(section_similarities) * 100
            
        except Exception as e:
            logger.error(f"Error calculating context similarity: {e}")
            return 0.0
    
    def _extract_key_sections(self, text: str) -> List[str]:
        """Extract key sections from text for context matching"""
        sections = []
        
        # Split text into paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        # Filter paragraphs by length and content
        for paragraph in paragraphs:
            if len(paragraph) > 50:  # Minimum length
                # Check if paragraph contains relevant content
                if any(keyword in paragraph.lower() for keyword in [
                    'experience', 'skills', 'education', 'project', 'responsibility',
                    'requirement', 'qualification', 'achievement', 'certification'
                ]):
                    sections.append(paragraph)
        
        return sections[:10]  # Limit to top 10 sections
    
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
    
    def _cosine_similarity_matrix(self, embeddings1: np.ndarray, embeddings2: np.ndarray) -> np.ndarray:
        """Calculate cosine similarity matrix between two sets of embeddings"""
        try:
            # Normalize embeddings
            embeddings1_norm = embeddings1 / np.linalg.norm(embeddings1, axis=1, keepdims=True)
            embeddings2_norm = embeddings2 / np.linalg.norm(embeddings2, axis=1, keepdims=True)
            
            # Calculate similarity matrix
            similarity_matrix = np.dot(embeddings1_norm, embeddings2_norm.T)
            
            return similarity_matrix
        except:
            return np.zeros((len(embeddings1), len(embeddings2)))
    
    def get_similar_skills(
        self, 
        resume_skills: List[str], 
        jd_skills: List[str], 
        threshold: float = 0.7
    ) -> List[Tuple[str, str, float]]:
        """
        Find similar skills between resume and JD
        
        Args:
            resume_skills: List of skills from resume
            jd_skills: List of skills from JD
            threshold: Similarity threshold for matching
            
        Returns:
            List of tuples (resume_skill, jd_skill, similarity_score)
        """
        try:
            if not resume_skills or not jd_skills:
                return []
            
            # Generate embeddings
            resume_embeddings = self.model.encode(resume_skills)
            jd_embeddings = self.model.encode(jd_skills)
            
            # Calculate similarity matrix
            similarity_matrix = self._cosine_similarity_matrix(
                resume_embeddings, 
                jd_embeddings
            )
            
            # Find matches above threshold
            matches = []
            for i, resume_skill in enumerate(resume_skills):
                for j, jd_skill in enumerate(jd_skills):
                    similarity = similarity_matrix[i, j]
                    if similarity >= threshold:
                        matches.append((resume_skill, jd_skill, similarity))
            
            # Sort by similarity score
            matches.sort(key=lambda x: x[2], reverse=True)
            
            return matches
            
        except Exception as e:
            logger.error(f"Error finding similar skills: {e}")
            return []
