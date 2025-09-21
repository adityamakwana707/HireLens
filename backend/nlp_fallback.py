"""
Fallback NLP functionality for when SpaCy is not available
This ensures the app continues to work even without SpaCy model
"""
import re
import nltk
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class FallbackNLP:
    """Fallback NLP processor when SpaCy is not available"""
    
    def __init__(self):
        self.setup_nltk()
    
    def setup_nltk(self):
        """Setup NLTK packages"""
        try:
            nltk_packages = ['punkt', 'averaged_perceptron_tagger', 'stopwords']
            for package in nltk_packages:
                try:
                    nltk.data.find(f'tokenizers/{package}')
                except LookupError:
                    nltk.download(package, quiet=True)
        except Exception as e:
            logger.warning(f"NLTK setup failed: {e}")
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills using regex patterns when SpaCy is not available"""
        # Common technical skills patterns
        skill_patterns = [
            r'\b(?:Python|Java|JavaScript|C\+\+|C#|PHP|Ruby|Go|Rust|Swift|Kotlin)\b',
            r'\b(?:React|Angular|Vue|Node\.js|Django|Flask|Spring|Laravel|Express)\b',
            r'\b(?:SQL|MySQL|PostgreSQL|MongoDB|Redis|Elasticsearch)\b',
            r'\b(?:AWS|Azure|GCP|Docker|Kubernetes|Jenkins|Git)\b',
            r'\b(?:Machine Learning|AI|Data Science|Analytics|Statistics)\b',
            r'\b(?:Project Management|Agile|Scrum|Leadership|Communication)\b'
        ]
        
        skills = set()
        for pattern in skill_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            skills.update(matches)
        
        return list(skills)
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using regex patterns"""
        entities = {
            'organizations': [],
            'locations': [],
            'dates': [],
            'emails': [],
            'phones': []
        }
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        entities['emails'] = re.findall(email_pattern, text)
        
        # Phone pattern
        phone_pattern = r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'
        entities['phones'] = re.findall(phone_pattern, text)
        
        # Date pattern
        date_pattern = r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b'
        entities['dates'] = re.findall(date_pattern, text, re.IGNORECASE)
        
        return entities
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenize text using NLTK"""
        try:
            from nltk.tokenize import word_tokenize
            return word_tokenize(text)
        except Exception:
            # Fallback to simple whitespace tokenization
            return text.split()
    
    def get_pos_tags(self, text: str) -> List[tuple]:
        """Get part-of-speech tags using NLTK"""
        try:
            from nltk.tokenize import word_tokenize
            from nltk.tag import pos_tag
            tokens = word_tokenize(text)
            return pos_tag(tokens)
        except Exception:
            return []

def get_nlp_processor():
    """Get the best available NLP processor"""
    try:
        import spacy
        nlp = spacy.load('en_core_web_sm')
        logger.info("Using SpaCy NLP processor")
        return nlp
    except Exception as e:
        logger.warning(f"SpaCy not available: {e}")
        logger.info("Using fallback NLP processor")
        return FallbackNLP()
