from typing import List, Optional, Any
from datetime import datetime
from app.models.base_models import InterviewInput
from app.services.document_parser import ResumeParser, JobPostParser
import whisper
from pathlib import Path
import os
import tempfile
import logging
import ollama
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize whisper model
try:
    whisper_model = whisper.load_model("small")
    logger.info("Whisper model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load whisper model: {e}")
    whisper_model = None

UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

class InterviewSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.resume_text: Optional[str] = None
        self.job_post_text: Optional[str] = None
        self.interview_questions: List[str] = []
        self.current_question_index: int = 0
        self.answers: List[str] = []
        self.follow_up_questions: List[str] = []
        self.is_completed: bool = False
        self.chat_history: List[dict] = []

    def initialize_session(self, interview_input: InterviewInput) -> None:
        """Initialize the session with resume and job post"""
        try:
            resume_parser = ResumeParser(interview_input[0])
            job_post_parser = JobPostParser(interview_input[1])
            
            self.resume_text = resume_parser.parse()
            self.job_post_text = job_post_parser.parse()
            logger.info("Session initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize session: {e}")
            raise

    def generate_recruiter_questions(self) -> Any:
        """Generate initial questions based on resume and job post"""
        try:
            # Prepare the context for the model
            context = f"""
            Job Post: {self.job_post_text}
            Candidate's Resume: {self.resume_text}
            
            Generate a list of 10 - 15 interview questions in JSON format with the following structure:
            {{
                "questions": [
                    {{
                        "question": string,
                        "category": string,
                        "difficulty": "easy" | "medium" | "hard",
                        "purpose": string
                    }}
                ]
            }}
            
            Guidelines for questions:
            - A list of survey questions tailored to gather further information from recruiters or hiring managers. The questions should cover:
            - Clarification on specific responsibilities or skills.
            - Expectations for the ideal candidate’s experience and soft skills.
            - Details about the company culture or team structure that might impact hiring.
            - Any other key factors not explicitly mentioned in the job post.
            """
            
            # Get questions from Ollama
            response = ollama.chat(
                model='deepseek-r1',
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are an expert technical interviewer. Generate relevant interview questions based on the job requirements and candidate\'s background.'
                    },
                    {
                        'role': 'user',
                        'content': context
                    }
                ]
            )
            
            # Parse the response
            # print(response)
            try:
                json_content = response['message']['content'].split('```json')[1].split('```')[0]
                print(json_content)
                questions_data = json.loads(json_content)
                logger.info(f"Generated {len(questions_data['questions'])} questions")
                
                # Extract just the questions from the structured data
                # questions = [q['question'] for q in questions_data['questions']]
                
                # Log the questions for debugging
                # for i, q in enumerate(questions, 1):
                #     logger.info(f"Question {i}: {q}")
                
                return questions_data
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Ollama response: {e}")
                # Fallback to some default questions if parsing fails
                return None
                
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            # Return default questions in case of any error
            return None



    def generate_initial_questions(self) -> List[str]:
        """Generate initial questions based on resume and job post"""
        try:
            # Prepare the context for the model
            context = f"""
            Job Post: {self.job_post_text}
            Candidate's Resume: {self.resume_text}
            
            Generate a list of 5 - 7 technical interview questions(not coding questions) in JSON format with the following structure:
            {{
                "questions": [
                    {{
                        "question": string,
                        "category": string,
                        "difficulty": "easy" | "medium" | "hard",
                        "purpose": string
                    }}
                ]
            }}
            
            Guidelines for questions:
            1. The questions should be based on the job post and candidate's resume.
            2. Be Technical in nature.
            3. Be easy to understand.
            4. Be relevant to the job post.

            """
            
            # Get questions from Ollama
            response = ollama.chat(
                model='deepseek-r1',
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are an expert technical interviewer. Generate relevant interview questions based on the job requirements and candidate\'s background.'
                    },
                    {
                        'role': 'user',
                        'content': context
                    }
                ]
            )
            
            # Parse the response
            # print(response)
            try:
                json_content = response['message']['content'].split('```json')[1].split('```')[0]
                print(json_content)
                questions_data = json.loads(json_content)
                logger.info(f"Generated {len(questions_data['questions'])} questions")
                
                # Extract just the questions from the structured data
                questions = [q['question'] for q in questions_data['questions']]
                
                # Log the questions for debugging
                for i, q in enumerate(questions, 1):
                    logger.info(f"Question {i}: {q}")
                
                return questions
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Ollama response: {e}")
                # Fallback to some default questions if parsing fails
                return [
                    "Tell me about your experience with the technologies mentioned in the job post.",
                    "What projects have you worked on that are most relevant to this position?",
                    "How do you handle tight deadlines and multiple priorities?",
                    "Describe a challenging technical problem you've solved recently.",
                    "How do you stay updated with the latest technologies in your field?"
                ]
                
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            # Return default questions in case of any error
            return [
                "Tell me about your experience with the technologies mentioned in the job post.",
                "What projects have you worked on that are most relevant to this position?",
                "How do you handle tight deadlines and multiple priorities?",
                "Describe a challenging technical problem you've solved recently.",
                "How do you stay updated with the latest technologies in your field?"
            ]

    def add_question(self, question: str) -> None:
        """Add a new interview question"""
        self.interview_questions.append(question)

    def add_follow_up_question(self, question: str) -> None:
        """Add a follow-up question"""
        self.follow_up_questions.append(question)

    def process_answer(self, answer: bytes) -> str:
        """Process the candidate's answer from audio bytes to text"""
        if not whisper_model:
            raise RuntimeError("Whisper model not loaded")

        try:
            # Create a temporary file with a unique name
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(answer)
                temp_file_path = temp_file.name

            logger.info(f"Processing audio file: {temp_file_path}")
            
            # Transcribe the audio
            result = whisper_model.transcribe(temp_file_path)
            transcript = result.get("text", "").strip()
            
            logger.info(f"Transcription completed: {transcript[:100]}...")
            
            # Clean up the temporary file
            os.unlink(temp_file_path)
            
            return transcript if transcript else "No speech detected"
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            raise

    def evaluate_answer(self, answer: str) -> tuple[bool, Optional[str]]:
        """Evaluate the candidate's answer and determine if follow-up is needed"""
        try:
            current_question = self.interview_questions[self.current_question_index]
            
            # Prepare the context for the model
            context = f"""
            Question: {current_question}
            Answer: {answer}
            
            Evaluate the candidate's answer and provide feedback in JSON format with the following structure:
            {{
                "is_satisfactory": boolean,
                "follow_up_question": string or null,
                "feedback": string
            }}
            
            Consider:
            1. The candidate's answer should be relevant to the question.
            2. The candidate's answer should be technical in nature.
            3. The candidate's answer should be easy to understand.
            4. The candidate's answer should be relevant to the job post.
            """
            
            # Get evaluation from Ollama
            response = ollama.chat(
                model='deepseek-r1',
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are an expert technical interviewer. Evaluate the candidate\'s answer and provide structured feedback.'
                    },
                    {
                        'role': 'user',
                        'content': context
                    }
                ]
            )
            
            # Parse the response
            # print(response)
            try:
                json_content = response['message']['content'].split('```json')[1].split('```')[0]
                print(json_content)
                evaluation = json.loads(json_content)
                logger.info(f"Evaluation result: {evaluation}")

                if evaluation['is_satisfactory'] == 'false' or evaluation['is_satisfactory'] == False:
                    is_satisfactory = False
                else:
                    is_satisfactory = True
                
                return is_satisfactory, evaluation['follow_up_question']
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Ollama response: {e}")
                return True, None
                
        except Exception as e:
            logger.error(f"Error evaluating answer: {e}")
            print(response)
            return True, None

    def add_to_chat_history(self, role: str, content: str) -> None:
        """Add a message to the chat history"""
        self.chat_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

    def to_dict(self) -> dict:
        """Convert session to dictionary for storage"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "resume_text": self.resume_text,
            "job_post_text": self.job_post_text,
            "interview_questions": self.interview_questions,
            "current_question_index": self.current_question_index,
            "answers": self.answers,
            "follow_up_questions": self.follow_up_questions,
            "is_completed": self.is_completed,
            "chat_history": self.chat_history
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'InterviewSession':
        """Create a session instance from dictionary"""
        session = cls(data["session_id"])
        session.created_at = datetime.fromisoformat(data["created_at"])
        session.resume_text = data["resume_text"]
        session.job_post_text = data["job_post_text"]
        session.interview_questions = data["interview_questions"]
        session.current_question_index = data["current_question_index"]
        session.answers = data["answers"]
        session.follow_up_questions = data["follow_up_questions"]
        session.is_completed = data["is_completed"]
        session.chat_history = data["chat_history"]
        return session 