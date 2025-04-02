from typing import Optional
import motor.motor_asyncio
from app.services.interview_session import InterviewSession

class DatabaseService:
    def __init__(self, connection_string: str):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(connection_string)
        self.db = self.client.interview_db
        self.sessions = self.db.sessions

    async def save_session(self, session: InterviewSession) -> None:
        """Save or update an interview session"""
        await self.sessions.update_one(
            {"session_id": session.session_id},
            {"$set": session.to_dict()},
            upsert=True
        )

    async def get_session(self, session_id: str) -> Optional[InterviewSession]:
        """Retrieve an interview session by ID"""
        session_data = await self.sessions.find_one({"session_id": session_id})
        if session_data:
            return InterviewSession.from_dict(session_data)
        return None

    async def delete_session(self, session_id: str) -> None:
        """Delete an interview session"""
        await self.sessions.delete_one({"session_id": session_id}) 