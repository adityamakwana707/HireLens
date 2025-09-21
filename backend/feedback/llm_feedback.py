"""
LLM-based feedback generation for HireLens
"""
import os
from typing import Dict, List, Optional
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

load_dotenv()

logger = logging.getLogger(__name__)

class FeedbackResponse(BaseModel):
    """Structured feedback response"""
    overall_feedback: str = Field(description="Overall feedback about the resume")
    strengths: List[str] = Field(description="List of strengths in the resume")
    weaknesses: List[str] = Field(description="List of weaknesses in the resume")
    missing_skills: List[str] = Field(description="List of missing skills")
    improvement_suggestions: List[str] = Field(description="List of improvement suggestions")
    verdict_explanation: str = Field(description="Explanation of why the verdict was given")

class LLMFeedbackGenerator:
    """Generate feedback using LLM"""
    
    def __init__(self, model_provider: str = "openai"):
        """
        Initialize the feedback generator
        
        Args:
            model_provider: "openai" or "google" for model selection
        """
        self.model_provider = model_provider
        self.llm = self._initialize_llm()
        self.parser = PydanticOutputParser(pydantic_object=FeedbackResponse)
    
    def _initialize_llm(self):
        """Initialize the LLM based on provider"""
        try:
            if self.model_provider == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not found in environment variables")
                return ChatOpenAI(
                    model="gpt-3.5-turbo",
                    temperature=0.7,
                    api_key=api_key
                )
            elif self.model_provider == "google":
                api_key = os.getenv("GOOGLE_API_KEY")
                if not api_key:
                    raise ValueError("GOOGLE_API_KEY not found in environment variables")
                return ChatGoogleGenerativeAI(
                    model="gemini-pro",
                    temperature=0.7,
                    google_api_key=api_key
                )
            else:
                raise ValueError(f"Unsupported model provider: {self.model_provider}")
        except Exception as e:
            logger.error(f"Error initializing LLM: {e}")
            raise
    
    def generate_feedback(
        self,
        resume_data: Dict,
        jd_data: Dict,
        evaluation_results: Dict,
        verdict: str
    ) -> Dict[str, any]:
        """
        Generate comprehensive feedback for a resume
        
        Args:
            resume_data: Parsed resume data
            jd_data: Parsed job description data
            evaluation_results: Evaluation results with scores
            verdict: Final verdict (High/Medium/Low)
            
        Returns:
            Dictionary with structured feedback
        """
        try:
            # Prepare context for LLM
            context = self._prepare_context(resume_data, jd_data, evaluation_results, verdict)
            
            # Generate feedback using LLM
            feedback = self._generate_llm_feedback(context)
            
            return feedback
            
        except Exception as e:
            logger.error(f"Error generating feedback: {e}")
            return self._generate_fallback_feedback(evaluation_results, verdict)
    
    def _prepare_context(
        self, 
        resume_data: Dict, 
        jd_data: Dict, 
        evaluation_results: Dict,
        verdict: str
    ) -> Dict:
        """Prepare context for LLM feedback generation"""
        return {
            'resume_skills': resume_data.get('skills', []),
            'resume_experience': resume_data.get('experience', []),
            'resume_education': resume_data.get('education', []),
            'resume_projects': resume_data.get('projects', []),
            'jd_title': jd_data.get('title', ''),
            'jd_required_skills': jd_data.get('skills_required', []),
            'jd_preferred_skills': jd_data.get('skills_preferred', []),
            'jd_requirements': jd_data.get('requirements', []),
            'overall_score': evaluation_results.get('final_score', 0),
            'hard_match_score': evaluation_results.get('hard_match_score', 0),
            'soft_match_score': evaluation_results.get('soft_match_score', 0),
            'matched_skills': evaluation_results.get('matched_skills', []),
            'missing_skills': evaluation_results.get('missing_skills', []),
            'skill_coverage': evaluation_results.get('skill_coverage', 0),
            'verdict': verdict
        }
    
    def _generate_llm_feedback(self, context: Dict) -> Dict:
        """Generate feedback using LLM"""
        try:
            # Create prompt template
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=self._get_system_prompt()),
                HumanMessage(content=self._get_human_prompt(context))
            ])
            
            # Format prompt
            formatted_prompt = prompt.format_messages()
            
            # Generate response
            response = self.llm.invoke(formatted_prompt)
            
            # Parse response
            parsed_response = self.parser.parse(response.content)
            
            return {
                'overall_feedback': parsed_response.overall_feedback,
                'strengths': parsed_response.strengths,
                'weaknesses': parsed_response.weaknesses,
                'missing_skills': parsed_response.missing_skills,
                'improvement_suggestions': parsed_response.improvement_suggestions,
                'verdict_explanation': parsed_response.verdict_explanation
            }
            
        except Exception as e:
            logger.error(f"Error generating LLM feedback: {e}")
            return self._generate_fallback_feedback(context, context.get('verdict', 'Low'))
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for feedback generation"""
        return """You are an expert career counselor and resume reviewer. Your task is to provide constructive, actionable feedback on resumes for job applications.

Guidelines:
1. Be constructive and encouraging, not critical
2. Provide specific, actionable suggestions
3. Focus on skills, experience, and qualifications relevant to the job
4. Explain the reasoning behind the verdict
5. Suggest concrete improvements the candidate can make
6. Keep feedback professional and helpful
7. Highlight both strengths and areas for improvement

Format your response as structured feedback with:
- Overall feedback (2-3 sentences)
- List of strengths (3-5 items)
- List of weaknesses (3-5 items)
- Missing skills (specific skills needed)
- Improvement suggestions (3-5 actionable items)
- Verdict explanation (why this verdict was given)"""
    
    def _get_human_prompt(self, context: Dict) -> str:
        """Get human prompt with context"""
        return f"""
Please provide feedback for this resume evaluation:

JOB POSITION: {context.get('jd_title', 'Not specified')}

RESUME SKILLS: {', '.join(context.get('resume_skills', []))}
RESUME EXPERIENCE: {len(context.get('resume_experience', []))} positions
RESUME EDUCATION: {len(context.get('resume_education', []))} entries
RESUME PROJECTS: {len(context.get('resume_projects', []))} projects

JOB REQUIREMENTS:
- Required Skills: {', '.join(context.get('jd_required_skills', []))}
- Preferred Skills: {', '.join(context.get('jd_preferred_skills', []))}

EVALUATION RESULTS:
- Overall Score: {context.get('overall_score', 0)}/100
- Hard Match Score: {context.get('hard_match_score', 0)}/100
- Soft Match Score: {context.get('soft_match_score', 0)}/100
- Skill Coverage: {context.get('skill_coverage', 0)}%
- Matched Skills: {', '.join(context.get('matched_skills', []))}
- Missing Skills: {', '.join(context.get('missing_skills', []))}

VERDICT: {context.get('verdict', 'Low')}

Please provide structured feedback following the format specified in the system prompt.
"""
    
    def _generate_fallback_feedback(self, evaluation_results: Dict, verdict: str) -> Dict:
        """Generate fallback feedback when LLM fails"""
        score = evaluation_results.get('final_score', 0)
        matched_skills = evaluation_results.get('matched_skills', [])
        missing_skills = evaluation_results.get('missing_skills', [])
        
        if verdict == "High":
            overall_feedback = f"Great match! Your resume scored {score}/100 and shows strong alignment with the job requirements."
            strengths = ["Strong skill match", "Relevant experience", "Good qualifications"]
            weaknesses = ["Consider adding more specific examples", "Highlight achievements more prominently"]
        elif verdict == "Medium":
            overall_feedback = f"Good potential match with a score of {score}/100. Some improvements could strengthen your application."
            strengths = ["Some relevant skills", "Basic qualifications met"]
            weaknesses = ["Missing some key skills", "Could strengthen experience section"]
        else:
            overall_feedback = f"Score of {score}/100 indicates significant gaps. Focus on developing required skills and experience."
            strengths = ["Some transferable skills"]
            weaknesses = ["Missing most required skills", "Limited relevant experience"]
        
        return {
            'overall_feedback': overall_feedback,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'missing_skills': missing_skills[:5],  # Top 5 missing skills
            'improvement_suggestions': [
                f"Develop skills in: {', '.join(missing_skills[:3])}",
                "Add more specific examples of your achievements",
                "Tailor your resume to highlight relevant experience",
                "Consider taking relevant courses or certifications",
                "Quantify your achievements with numbers and metrics"
            ],
            'verdict_explanation': f"The {verdict} verdict is based on a {score}/100 score, with {len(matched_skills)} matched skills and {len(missing_skills)} missing skills."
        }
    
    def generate_skill_suggestions(self, missing_skills: List[str], job_title: str) -> List[str]:
        """Generate specific skill development suggestions"""
        suggestions = []
        
        for skill in missing_skills[:5]:  # Top 5 missing skills
            if skill.lower() in ['python', 'javascript', 'java', 'c++']:
                suggestions.append(f"Learn {skill} through online courses like Codecademy, Coursera, or freeCodeCamp")
            elif skill.lower() in ['react', 'angular', 'vue']:
                suggestions.append(f"Build projects with {skill} to gain hands-on experience")
            elif skill.lower() in ['aws', 'azure', 'gcp']:
                suggestions.append(f"Get certified in {skill} through official certification programs")
            elif skill.lower() in ['machine learning', 'data science']:
                suggestions.append(f"Take ML courses on Coursera or edX and work on Kaggle projects")
            else:
                suggestions.append(f"Research and practice {skill} through tutorials and projects")
        
        return suggestions
