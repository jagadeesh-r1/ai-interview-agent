from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from app.models.base_models import InterviewInput
from app.services.interview_session import InterviewSession
from app.services.database import DatabaseService
from pathlib import Path
import uuid
from typing import Dict, List
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
MONGODB_URL = "mongodb://localhost:27017"  # Replace with your MongoDB connection string
db_service = DatabaseService(MONGODB_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

@app.get('/')
def read_root():
    return {"message": "Welcome to AI Interview Agent!"}

@app.post('/start_interview')
async def start_interview(files: List[UploadFile] = File(...)):
    try:
        session_id = str(uuid.uuid4())
        session = InterviewSession(session_id)
        logger.info(f"Starting new interview session: {session_id}")
        
        session.initialize_session(files)

        # Generate initial questions based on resume and job post
        initial_questions = session.generate_initial_questions()
            


        
        for question in initial_questions:
            session.add_question(question)
        
        # Save session to database
        await db_service.save_session(session)
        
        return {
            "session_id": session_id,
            "message": "Interview session started",
            "first_question": session.interview_questions[0]
        }
    except Exception as e:
        logger.error(f"Error starting interview: {e}")
        raise

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    Handle WebSocket connection for the interview session
    """
    await websocket.accept()
    active_connections[session_id] = websocket
    logger.info(f"New WebSocket connection established for session: {session_id}")
    
    try:
        session = await db_service.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            # await websocket.close(code=4004, reason="Session not found")
            return

        while True:
            print("looping 1")
            try:                
                # Handle follow-up questions if any
                while session.follow_up_questions:
                    print("looping 2")
                    follow_up = session.follow_up_questions.pop(0)  # Get and remove the first follow-up
                    await websocket.send_json({
                        "type": "follow_up",
                        "question": follow_up,
                        "status": "incomplete"
                    })
                    logger.info(f"Sent follow-up question: {follow_up}")
                    
                    # Receive answer for follow-up
                    data = await websocket.receive_bytes()
                    logger.info(f"Received audio data for follow-up of length: {len(data)}")
                    
                    # Process follow-up answer
                    answer_text = session.process_answer(data)
                    logger.info(f"Processed follow-up answer: {answer_text}")
                    
                    # Add to chat history
                    session.add_to_chat_history("assistant", follow_up)
                    session.add_to_chat_history("user", answer_text)
                    
                    # Evaluate follow-up answer
                    is_satisfactory, new_follow_up = session.evaluate_answer(answer_text)
                    
                    if not is_satisfactory:
                        session.add_follow_up_question(new_follow_up)
                        continue
                    else:
                        break
                # Send current question
                current_question = session.interview_questions[session.current_question_index]
                await websocket.send_json({
                    "type": "question",
                    "question": current_question,
                    "status": "incomplete"
                })
                logger.info(f"Sent question: {current_question}")
                
                # Receive answer for main question
                data = await websocket.receive_bytes()
                logger.info(f"Received audio data of length: {len(data)}")
                
                # Process answer
                answer_text = session.process_answer(data)
                logger.info(f"Processed answer: {answer_text}")
                
                # Add to chat history
                session.add_to_chat_history("assistant", current_question)
                session.add_to_chat_history("user", answer_text)
                
                # Evaluate answer
                is_satisfactory, follow_up = session.evaluate_answer(answer_text)
                
                if not is_satisfactory:
                    session.add_follow_up_question(follow_up)
                    continue  # Continue the loop to handle the follow-up question
                
                # Move to next question only if no follow-ups are pending
                session.current_question_index += 1
                session.answers.append(answer_text)
                
                # Check if interview is complete
                if session.current_question_index >= len(session.interview_questions):
                    session.is_completed = True
                    await websocket.send_json({
                        "type": "complete",
                        "message": "Interview completed successfully",
                        "status": "completed"
                    })
                    logger.info(f"Interview completed for session: {session_id}")
                    break
                
                # Save session state
                await db_service.save_session(session)
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Error processing your answer. Please try again.",
                    "status": "error"
                })
                continue
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
        if session_id in active_connections:
            del active_connections[session_id]
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        # await websocket.close(code=4000, reason=str(e))
        if session_id in active_connections:
            del active_connections[session_id]


@app.post('/generate_questions')
async def generate_questions(files: List[UploadFile] = File(...)):
    """
    Generate initial questions for the interview based on job post
    """
    try:
        session_id = str(uuid.uuid4())
        session = InterviewSession(session_id)
        initial_questions = session.generate_recruiter_questions()
        return initial_questions
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        raise
