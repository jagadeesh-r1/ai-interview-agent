# AI Interview Agent

An intelligent interview system that conducts automated technical interviews using AI. The system analyzes candidate resumes and job postings to generate relevant interview questions, evaluates responses in real-time, and provides a natural interview experience through voice interaction.

## Features

- **Smart Question Generation**: Automatically generates relevant interview questions based on job requirements and candidate profiles
- **Real-time Voice Interaction**: Supports voice-based Q&A using speech-to-text and text-to-speech
- **Intelligent Follow-ups**: Dynamically generates follow-up questions based on candidate responses
- **Context-Aware Evaluation**: Evaluates answers considering job requirements and candidate experience
- **Session Management**: Maintains interview sessions with complete chat history
- **MongoDB Integration**: Stores interview sessions and results for future reference

## Prerequisites

- Python 3.8 or higher
- MongoDB running locally or a MongoDB Atlas connection string
- Ollama installed and running locally with the deepseek-r1 model
- FFmpeg installed for audio processing

## Installation

1. Clone the repository:
```bash
git clone https://github.com/jagadeesh-r1/ai-interview-agent.git
cd ai-interview-agent
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install FFmpeg:
- **Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install ffmpeg
```
- **macOS**:
```bash
brew install ffmpeg
```
- **Windows**: Download from [FFmpeg website](https://ffmpeg.org/download.html)

5. Install Ollama and the required model:
```bash
# Install Ollama (follow instructions at https://ollama.ai)
# Then pull the deepseek-r1 model
ollama pull deepseek-r1
```

6. Set up MongoDB:
- Install MongoDB locally or use MongoDB Atlas
- Update the `MONGODB_URL` in `main.py` with your connection string

## Project Structure

```
ai-interview-agent/
├── app/
│   ├── models/
│   │   └── base_models.py
│   ├── services/
│   │   ├── document_parser.py
│   │   ├── database.py
│   │   └── interview_session.py
│   └── uploads/
├── main.py
├── requirements.txt
└── README.md
```

## Running the Application

1. Start MongoDB:
```bash
# If running locally
mongod
```

2. Start Ollama:
```bash
ollama serve
```

3. Start the FastAPI server:
```bash
uvicorn main:app --reload
```

The server will start at `http://localhost:8000`

## API Endpoints

### 1. Start Interview
```http
POST /start_interview
Content-Type: multipart/form-data

files: [resume.pdf, job_post.pdf]
```
- Starts a new interview session
- Returns session ID and first question

### 2. WebSocket Connection
```http
WebSocket /ws/{session_id}
```
- Establishes real-time communication for the interview
- Handles questions, answers, and follow-ups

### 3. Generate Questions
```http
POST /generate_questions
Content-Type: multipart/form-data

files: [resume.pdf, job_post.pdf]
```
- Generates interview questions based on resume and job post
- Returns structured questions with categories and difficulty levels

## Usage Example

1. Start the interview:
```python
import requests

files = {
    'files': [
        ('resume.pdf', open('path/to/resume.pdf', 'rb')),
        ('job_post.pdf', open('path/to/job_post.pdf', 'rb'))
    ]
}

response = requests.post('http://localhost:8000/start_interview', files=files)
session_id = response.json()['session_id']
```

2. Connect to WebSocket:
```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/${session_id}`);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'question') {
        // Handle question
    } else if (data.type === 'follow_up') {
        // Handle follow-up
    }
};

// Send audio answer
ws.send(audioData);
```

## Environment Variables

Create a `.env` file in the root directory:
```env
MONGODB_URL=mongodb://localhost:27017
OLLAMA_MODEL=deepseek-r1
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI Whisper for speech recognition
- Ollama for LLM capabilities
- FastAPI for the web framework
- MongoDB for data storage