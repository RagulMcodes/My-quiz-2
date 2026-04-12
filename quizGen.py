import asyncio
import json
import websockets
from datetime import datetime
import uuid
from typing import Dict
import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

load_dotenv()

# Initialize LLM
llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0.9
)

parser = JsonOutputParser(pydantic_object={
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "question": {"type": "string"},
            "options": {
                "type": "array",
                "items": {"type": "string"}
            },
            "answer": {"type": "string"}
        },
        "required": ["question", "options", "answer"]
    }
})

prompt = ChatPromptTemplate.from_messages([
    ("system", """Generate {num_questions} random general knowledge multiple choice questions.

Rules:
- Exactly {num_questions} questions
- 4 options per question
- Only one correct answer
- Mix easy, medium, and hard difficulty
- Diverse topics (science, history, geography, sports, entertainment, etc.)

Return ONLY valid JSON in this format:
[
  {{
    "question": "Question text",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer": "Correct option text"
  }}
]
"""),
    ("user", "Generate quiz with {num_questions} questions about {topic}")
])

chain = prompt | llm | parser



def generate_quiz(num_questions=10, topic="general knowledge"):
    """Generate quiz using LLM"""
    try:
        result = chain.invoke({"num_questions": num_questions, "topic": topic})
    except Exception as e:
        print(f"Error generating quiz: {e}")
        # Fallback questions
        return [
            {
                "question": "What is the capital of France?",
                "options": ["London", "Berlin", "Paris", "Madrid"],
                "answer": "Paris"
            },
            {
                "question": "What is 2 + 2?",
                "options": ["3", "4", "5", "6"],
                "answer": "4"
            }
        ]

generate_quiz(10,"cs")
print(generate_quiz())




questions = result

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()



    except WebSocketDisconnect:
        print("User disconnected")