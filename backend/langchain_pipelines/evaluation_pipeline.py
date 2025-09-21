"""
LangChain pipeline for resume evaluation
"""
from typing import Dict, List, Any, Optional
import logging
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
import json

from backend.parsers.resume_parser import ResumeParser
from backend.parsers.jd_parser import JDParser
from backend.matchers.hard_matcher import HardMatcher
from backend.matchers.soft_matcher import SoftMatcher
from backend.utils.scoring import ScoringEngine
from backend.feedback.llm_feedback import LLMFeedbackGenerator

logger = logging.getLogger(__name__)

class EvaluationResult(BaseModel):
    """Structured evaluation result"""
    final_score: float = Field(description="Final score (0-100)")
    verdict: str = Field(description="Verdict: High, Medium, or Low")
    hard_match_score: float = Field(description="Hard match score")
    soft_match_score: float = Field(description="Soft match score")
    matched_skills: List[str] = Field(description="List of matched skills")
    missing_skills: List[str] = Field(description="List of missing skills")
    skill_coverage: float = Field(description="Skill coverage percentage")
    feedback: Dict[str, Any] = Field(description="Generated feedback")

class ResumeEvaluationPipeline:
    """Main pipeline for resume evaluation using LangChain"""
    
    def __init__(self, model_provider: str = "openai"):
        """
        Initialize the evaluation pipeline
        
        Args:
            model_provider: "openai" or "google" for LLM selection
        """
        self.resume_parser = ResumeParser()
        self.jd_parser = JDParser()
        self.hard_matcher = HardMatcher()
        self.soft_matcher = SoftMatcher()
        self.scoring_engine = ScoringEngine()
        self.feedback_generator = LLMFeedbackGenerator(model_provider)
        
        # Initialize LangChain components
        self._setup_langchain_components()
    
    def _setup_langchain_components(self):
        """Setup LangChain components for the pipeline"""
        # Create prompt template for evaluation
        self.evaluation_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert resume evaluator. Analyze the resume and job description to provide a comprehensive evaluation.

Your task is to:
1. Parse and understand the resume content
2. Extract key information from the job description
3. Perform both hard and soft matching
4. Calculate scores and determine verdict
5. Generate actionable feedback

Be thorough, accurate, and constructive in your analysis."""),
            HumanMessage(content="""Please evaluate this resume against the job description:

RESUME FILE: {resume_file_path}
JOB DESCRIPTION: {jd_text}

Provide a comprehensive evaluation including scores, verdict, and feedback.""")
        ])
    
    def evaluate_resume(
        self, 
        resume_file_path: str, 
        jd_text: str,
        jd_title: str = "",
        jd_company: str = ""
    ) -> EvaluationResult:
        """
        Evaluate a resume against a job description
        
        Args:
            resume_file_path: Path to resume file
            jd_text: Job description text
            jd_title: Job title (optional)
            jd_company: Company name (optional)
            
        Returns:
            EvaluationResult with comprehensive evaluation
        """
        try:
            logger.info(f"Starting evaluation for resume: {resume_file_path}")
            
            # Step 1: Parse resume
            resume_data = self.resume_parser.parse_file(resume_file_path)
            logger.info("Resume parsed successfully")
            
            # Step 2: Parse job description
            jd_data = self.jd_parser.parse_jd(jd_text)
            if jd_title:
                jd_data['title'] = jd_title
            if jd_company:
                jd_data['company'] = jd_company
            logger.info("Job description parsed successfully")
            
            # Step 3: Perform hard matching
            hard_match_results = self.hard_matcher.calculate_hard_match_score(
                resume_text=resume_data['raw_text'],
                jd_text=jd_text,
                resume_skills=resume_data['skills'],
                jd_required_skills=jd_data['skills_required'],
                jd_preferred_skills=jd_data['skills_preferred']
            )
            logger.info(f"Hard matching completed: {hard_match_results['overall_score']}")
            
            # Step 4: Perform soft matching
            soft_match_results = self.soft_matcher.calculate_soft_match_score(
                resume_text=resume_data['raw_text'],
                jd_text=jd_text,
                resume_skills=resume_data['skills'],
                jd_required_skills=jd_data['skills_required'],
                jd_preferred_skills=jd_data['skills_preferred']
            )
            logger.info(f"Soft matching completed: {soft_match_results['overall_score']}")
            
            # Step 5: Calculate final score
            final_score_results = self.scoring_engine.calculate_final_score(
                hard_match_score=hard_match_results['overall_score'],
                soft_match_score=soft_match_results['overall_score']
            )
            logger.info(f"Final score calculated: {final_score_results['final_score']}")
            
            # Step 6: Determine verdict
            verdict = self.scoring_engine.determine_verdict(final_score_results['final_score'])
            logger.info(f"Verdict determined: {verdict}")
            
            # Step 7: Calculate skill coverage and matches
            skill_coverage = self.scoring_engine.calculate_skill_coverage(
                resume_skills=resume_data['skills'],
                jd_required_skills=jd_data['skills_required'],
                jd_preferred_skills=jd_data['skills_preferred']
            )
            
            skill_matches = self.scoring_engine.get_matched_skills(
                resume_skills=resume_data['skills'],
                jd_required_skills=jd_data['skills_required'],
                jd_preferred_skills=jd_data['skills_preferred']
            )
            
            # Step 8: Generate feedback
            evaluation_context = {
                'final_score': final_score_results['final_score'],
                'hard_match_score': hard_match_results['overall_score'],
                'soft_match_score': soft_match_results['overall_score'],
                'matched_skills': skill_matches['all_matched'],
                'missing_skills': skill_matches['all_missing'],
                'skill_coverage': skill_coverage['overall_coverage']
            }
            
            feedback = self.feedback_generator.generate_feedback(
                resume_data=resume_data,
                jd_data=jd_data,
                evaluation_results=evaluation_context,
                verdict=verdict
            )
            logger.info("Feedback generated successfully")
            
            # Step 9: Create final result
            result = EvaluationResult(
                final_score=final_score_results['final_score'],
                verdict=verdict,
                hard_match_score=hard_match_results['overall_score'],
                soft_match_score=soft_match_results['overall_score'],
                matched_skills=skill_matches['all_matched'],
                missing_skills=skill_matches['all_missing'],
                skill_coverage=skill_coverage['overall_coverage'],
                feedback=feedback
            )
            
            logger.info(f"Evaluation completed successfully for {resume_file_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error in resume evaluation: {e}")
            raise
    
    def batch_evaluate_resumes(
        self, 
        resume_file_paths: List[str], 
        jd_text: str,
        jd_title: str = "",
        jd_company: str = ""
    ) -> List[EvaluationResult]:
        """
        Evaluate multiple resumes against a job description
        
        Args:
            resume_file_paths: List of resume file paths
            jd_text: Job description text
            jd_title: Job title (optional)
            jd_company: Company name (optional)
            
        Returns:
            List of EvaluationResult objects
        """
        results = []
        
        for i, resume_path in enumerate(resume_file_paths):
            try:
                logger.info(f"Evaluating resume {i+1}/{len(resume_file_paths)}: {resume_path}")
                result = self.evaluate_resume(resume_path, jd_text, jd_title, jd_company)
                results.append(result)
            except Exception as e:
                logger.error(f"Error evaluating resume {resume_path}: {e}")
                # Create error result
                error_result = EvaluationResult(
                    final_score=0.0,
                    verdict="Error",
                    hard_match_score=0.0,
                    soft_match_score=0.0,
                    matched_skills=[],
                    missing_skills=[],
                    skill_coverage=0.0,
                    feedback={
                        'overall_feedback': f"Error evaluating resume: {str(e)}",
                        'strengths': [],
                        'weaknesses': ["Error in processing"],
                        'missing_skills': [],
                        'improvement_suggestions': ["Please check file format and try again"],
                        'verdict_explanation': "Error occurred during evaluation"
                    }
                )
                results.append(error_result)
        
        return results
    
    def get_evaluation_summary(self, results: List[EvaluationResult]) -> Dict[str, Any]:
        """
        Get summary statistics for batch evaluation results
        
        Args:
            results: List of evaluation results
            
        Returns:
            Dictionary with summary statistics
        """
        if not results:
            return {}
        
        scores = [r.final_score for r in results]
        verdicts = [r.verdict for r in results]
        
        # Calculate statistics
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)
        min_score = min(scores)
        
        # Count verdicts
        verdict_counts = {}
        for verdict in verdicts:
            verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
        
        # Calculate percentages
        total = len(results)
        verdict_percentages = {
            verdict: (count / total) * 100 
            for verdict, count in verdict_counts.items()
        }
        
        return {
            'total_resumes': total,
            'average_score': round(avg_score, 2),
            'max_score': round(max_score, 2),
            'min_score': round(min_score, 2),
            'verdict_counts': verdict_counts,
            'verdict_percentages': verdict_percentages,
            'high_fit_count': verdict_counts.get('High', 0),
            'medium_fit_count': verdict_counts.get('Medium', 0),
            'low_fit_count': verdict_counts.get('Low', 0)
        }
