from pydantic import BaseModel
from fastapi import UploadFile
from typing import List

class InterviewInput(BaseModel):
    files: List[UploadFile]

class InterviewOutput(BaseModel):
    interview_questions: list[str]
    interview_answers: list[str]
