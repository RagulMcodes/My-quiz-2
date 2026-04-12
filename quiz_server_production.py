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
        return result
    except Exception as e:
        print(f"Error generating quiz: {e}")
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


def convert_to_multiplayer_format(llm_questions):
    """Convert LLM format to multiplayer format"""
    converted = []
    for q in llm_questions:
        try:
            correct_index = q["options"].index(q["answer"])
            correct_letter = chr(65 + correct_index)
        except ValueError:
            correct_index = next(
                (i for i, opt in enumerate(q["options"])
                 if opt.lower() == q["answer"].lower()),
                0
            )
            correct_letter = chr(65 + correct_index)

        converted.append({
            "question": q["question"],
            "options": [f"{chr(65+i)}) {opt}" for i, opt in enumerate(q["options"])],
            "correct_answer": correct_letter
        })
    return converted


# In-memory storage
rooms: Dict[str, dict] = {}
connections: Dict[str, websockets.WebSocketServerProtocol] = {}


class QuizRoom:
    def __init__(self, room_id: str, max_participants: int, host_id: str,
                 num_questions: int = 10, topic: str = "general knowledge"):
        self.room_id = room_id
        self.max_participants = max_participants
        self.host_id = host_id
        self.participants: Dict[str, dict] = {}
        self.state = "waiting"
        self.current_question_index = 0
        self.question_start_time = None
        self.answers_received: Dict[str, tuple] = {}
        self.scores: Dict[str, int] = {}
        self.questions = []
        self.num_questions = num_questions
        self.topic = topic

    def add_participant(self, user_id: str, username: str):
        if len(self.participants) < self.max_participants:
            self.participants[user_id] = {"username": username, "connected": True}
            self.scores[user_id] = 0
            return True
        return False

    def is_full(self):
        return len(self.participants) >= self.max_participants

    def record_answer(self, user_id: str, answer: str):
        if user_id not in self.answers_received:
            self.answers_received[user_id] = (answer, datetime.now())
            return True
        return False

    def get_leaderboard(self):
        """
        Returns sorted leaderboard list with username, score, and rank.
        Sent to frontend after every question and at game end.
        """
        sorted_entries = sorted(
            [
                {
                    "user_id": uid,
                    "username": self.participants[uid]["username"],
                    "score": self.scores[uid],
                }
                for uid in self.scores
            ],
            key=lambda x: x["score"],
            reverse=True,
        )
        for i, entry in enumerate(sorted_entries):
            entry["rank"] = i + 1
        return sorted_entries

    def calculate_scores_for_question(self):
        """Calculate scores for the current question based on answer timing"""
        if not self.questions or self.current_question_index >= len(self.questions):
            return {
                "correct_answer": "",
                "rankings": [],
                "scores": self.scores.copy(),
                "leaderboard": self.get_leaderboard(),
            }

        correct_answer = self.questions[self.current_question_index]["correct_answer"]

        correct_answers = []
        for user_id, (answer, timestamp) in self.answers_received.items():
            if answer.upper() == correct_answer.upper():
                correct_answers.append((user_id, timestamp))
            else:
                self.scores[user_id] -= 1

        correct_answers.sort(key=lambda x: x[1])

        for rank, (user_id, _) in enumerate(correct_answers):
            if rank == 0:
                self.scores[user_id] += 3
            elif rank == 1:
                self.scores[user_id] += 2
            elif rank == 2:
                self.scores[user_id] += 1

        return {
            "correct_answer": correct_answer,
            "rankings": [
                (user_id, self.participants[user_id]["username"], timestamp)
                for user_id, timestamp in correct_answers
            ],
            "scores": self.scores.copy(),
            "leaderboard": self.get_leaderboard(),   # ← NEW: enriched, sorted list
        }


async def broadcast_to_room(room_id: str, message: dict, exclude_user: str = None):
    room = rooms[room_id]
    disconnected = []
    for user_id in room.participants.keys():
        if user_id == exclude_user:
            continue
        if user_id in connections:
            try:
                await connections[user_id].send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected.append(user_id)
    for user_id in disconnected:
        if user_id in connections:
            del connections[user_id]


async def generate_questions_for_room(room_id: str):
    room = rooms[room_id]
    room.state = "generating"

    await broadcast_to_room(room_id, {
        "type": "generating_questions",
        "message": f"🤖 AI is generating {room.num_questions} questions about {room.topic}..."
    })

    loop = asyncio.get_event_loop()
    try:
        llm_questions = await asyncio.wait_for(
            loop.run_in_executor(None, generate_quiz, room.num_questions, room.topic),
            timeout=20.0
        )
    except asyncio.TimeoutError:
        print(f"⚠️  LLM timeout for room {room_id}, using fallback questions")
        llm_questions = generate_quiz(5, "general knowledge")
    except Exception as e:
        print(f"❌ LLM error for room {room_id}: {e}, using fallback")
        llm_questions = generate_quiz(5, "general knowledge")

    room.questions = convert_to_multiplayer_format(llm_questions)

    await broadcast_to_room(room_id, {
        "type": "questions_generated",
        "message": f"✅ Questions ready! {len(room.questions)} questions generated.",
        "num_questions": len(room.questions)
    })


async def handle_create_room(websocket, data, user_id):
    max_participants = data.get("max_participants", 2)
    username = data.get("username", f"User_{user_id[:6]}")
    num_questions = data.get("num_questions", 10)
    topic = data.get("topic", "general knowledge")

    room_id = str(uuid.uuid4())[:8].upper()
    room = QuizRoom(room_id, max_participants, user_id, num_questions, topic)
    room.add_participant(user_id, username)

    rooms[room_id] = room
    connections[user_id] = websocket

    await websocket.send(json.dumps({
        "type": "room_created",
        "room_id": room_id,
        "username": username,
        "max_participants": max_participants,
        "current_participants": 1,
        "num_questions": num_questions,
        "topic": topic
    }))
    return room_id


async def handle_join_room(websocket, data, user_id):
    room_id = data.get("room_id", "").upper()
    username = data.get("username", f"User_{user_id[:6]}")

    if room_id not in rooms:
        await websocket.send(json.dumps({"type": "error", "message": "Room not found"}))
        return None

    room = rooms[room_id]

    if room.state not in ["waiting", "generating"]:
        await websocket.send(json.dumps({"type": "error", "message": "Game already started"}))
        return None

    if not room.add_participant(user_id, username):
        await websocket.send(json.dumps({"type": "error", "message": "Room is full"}))
        return None

    connections[user_id] = websocket

    await websocket.send(json.dumps({
        "type": "room_joined",
        "room_id": room_id,
        "username": username,
        "current_participants": len(room.participants),
        "max_participants": room.max_participants,
        "num_questions": room.num_questions,
        "topic": room.topic
    }))

    await broadcast_to_room(room_id, {
        "type": "participant_joined",
        "username": username,
        "current_participants": len(room.participants),
        "max_participants": room.max_participants,
        "participants": [p["username"] for p in room.participants.values()]
    }, exclude_user=user_id)

    if room.is_full():
        # Run game loop as an independent task so this client's websocket
        # stays free to receive messages (submit_answer) during the game.
        asyncio.create_task(start_game_loop(room_id))

    return room_id


async def start_game_loop(room_id: str):
    """Generates questions then kicks off the countdown.
    Runs as a detached task so no client websocket is blocked."""
    await generate_questions_for_room(room_id)
    await asyncio.sleep(2)
    await start_game_countdown(room_id)


async def start_game_countdown(room_id: str):
    room = rooms[room_id]
    room.state = "countdown"

    await broadcast_to_room(room_id, {
        "type": "game_starting",
        "message": "All players joined! Game starting in 10 seconds..."
    })

    for i in range(10, 0, -1):
        await broadcast_to_room(room_id, {"type": "countdown", "seconds": i})
        await asyncio.sleep(1)

    await start_question(room_id)


async def start_question(room_id: str):
    room = rooms[room_id]

    if room.current_question_index >= len(room.questions):
        await end_game(room_id)
        return

    room.state = "playing"
    room.answers_received.clear()
    room.question_start_time = datetime.now()

    question_data = room.questions[room.current_question_index]

    await broadcast_to_room(room_id, {
        "type": "question",
        "question_number": room.current_question_index + 1,
        "total_questions": len(room.questions),
        "question": question_data["question"],
        "options": question_data["options"],
        "time_limit": 5
    })

    await asyncio.sleep(5)

    results = room.calculate_scores_for_question()

    await broadcast_to_room(room_id, {
        "type": "question_results",
        "correct_answer": results["correct_answer"],
        "scores": results["scores"],
        "leaderboard": results["leaderboard"],   # ← enriched leaderboard
        "rankings": [
            (uid, uname, ts.isoformat())
            for uid, uname, ts in results["rankings"][:3]
        ]
    })

    room.current_question_index += 1
    await asyncio.sleep(3)
    await start_question(room_id)


async def end_game(room_id: str):
    room = rooms[room_id]
    room.state = "finished"

    sorted_scores = sorted(
        [(uid, room.participants[uid]["username"], score)
         for uid, score in room.scores.items()],
        key=lambda x: x[2],
        reverse=True
    )

    await broadcast_to_room(room_id, {
        "type": "game_ended",
        "final_scores": [(username, score) for _, username, score in sorted_scores],
        "leaderboard": room.get_leaderboard(),   # ← final leaderboard
        "winner": sorted_scores[0][1] if sorted_scores else None
    })


async def handle_answer(websocket, data, user_id):
    room_id = data.get("room_id")
    answer = data.get("answer")

    if room_id not in rooms:
        return

    room = rooms[room_id]
    if room.state != "playing":
        return

    if room.record_answer(user_id, answer):
        await websocket.send(json.dumps({"type": "answer_recorded", "message": "Answer recorded!"}))


async def handle_client(websocket, path):
    user_id = str(uuid.uuid4())
    room_id = None

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                continue
            except Exception:
                continue

            action = data.get("action")

            if action == "create_room":
                room_id = await handle_create_room(websocket, data, user_id)
            elif action == "join_room":
                room_id = await handle_join_room(websocket, data, user_id)
            elif action == "submit_answer":
                await handle_answer(websocket, data, user_id)

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if user_id in connections:
            del connections[user_id]
        if room_id and room_id in rooms:
            room = rooms[room_id]
            if user_id in room.participants:
                room.participants[user_id]["connected"] = False
                await broadcast_to_room(room_id, {
                    "type": "participant_disconnected",
                    "message": f"{room.participants[user_id]['username']} disconnected"
                })


async def main():
    port = int(os.environ.get("PORT", 8765))
    print("🎮 AI-Powered Multiplayer Quiz Server Starting...")
    print("🤖 Using Groq LLM for question generation")
    print(f"🌐 Server running on port {port}")
    print("=" * 50)

    async with websockets.serve(
        handle_client,
        "0.0.0.0",
        port,
        ping_interval=20,
        ping_timeout=20
    ):
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server shutting down...")