# 🤖 AI-Powered Multiplayer Quiz Game

A real-time multiplayer quiz game that uses **Groq LLM** to dynamically generate questions on any topic! Compete with friends in a WebSocket-powered quiz with instant scoring.

## ✨ Key Features

- **🤖 AI Question Generation**: Questions generated in real-time using Groq's LLaMA 3.3 70B model
- **📚 Custom Topics**: Choose from predefined topics or create your own
- **🎮 Multiplayer Rooms**: Create or join rooms with 2-10 players
- **⚡ Real-time Competition**: WebSocket-based instant communication
- **⏱️ Timed Questions**: 5 seconds per question
- **🏆 Smart Scoring**:
  - 1st correct answer: **+3 points** 🥇
  - 2nd correct answer: **+2 points** 🥈
  - 3rd correct answer: **+1 point** 🥉
  - Other correct answers: **0 points**
  - Wrong answers: **-1 point** ❌
- **📊 Live Leaderboard**: See rankings update in real-time
- **⏳ Auto-start**: Game begins automatically when all players join

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- Groq API key (free tier available)

### Installation

1. **Clone or download the files**

2. **Install dependencies**:
```bash
pip install -r requirements_llm.txt
```

3. **Set up your Groq API key**:

   a. Get your free API key from [Groq Console](https://console.groq.com/keys)
   
   b. Create a `.env` file in the project directory:
   ```bash
   cp .env.example .env
   ```
   
   c. Edit `.env` and add your API key:
   ```
   GROQ_API_KEY=your_actual_api_key_here
   ```

### Running the Game

**Step 1: Start the Server**
```bash
python quiz_server_llm.py
```

You should see:
```
🎮 AI-Powered Multiplayer Quiz Server Starting...
🤖 Using Groq LLM for question generation
🌐 Server running on ws://localhost:8765
==================================================
```

**Step 2: Start Clients (in separate terminals)**
```bash
python quiz_client_llm.py
```

## 🎯 How to Play

### Creating a Room

1. Run the client: `python quiz_client_llm.py`
2. Choose option `1` to create a room
3. Enter your username
4. Set number of players (2-10)
5. Set number of questions (5-20)
6. Choose a topic:
   - General Knowledge
   - Science & Technology
   - History & Geography
   - Sports & Entertainment
   - Custom Topic
7. Share the Room ID with other players!

### Joining a Room

1. Run the client: `python quiz_client_llm.py`
2. Choose option `2` to join a room
3. Enter your username
4. Enter the Room ID from the host

### Gameplay Flow

1. **Lobby Phase**: Wait for all players to join
2. **Question Generation**: AI generates questions (a few seconds)
3. **Countdown**: 10-second countdown before game starts
4. **Questions**: Answer within 5 seconds per question
5. **Results**: See correct answers and updated scores
6. **Final Rankings**: View the leaderboard at the end

## 📋 Example Gameplay

```
🤖 AI-POWERED MULTIPLAYER QUIZ 🤖
==================================================

What would you like to do?
1. Create a new room
2. Join an existing room

Enter your choice (1 or 2): 1

==================================================
🎮 CREATE A NEW ROOM
==================================================
Enter your username: Alice
Enter number of participants (2-10): 3
Enter number of questions (5-20): 10

📚 Quiz Topic Options:
1. General Knowledge (default)
2. Science & Technology
3. History & Geography
4. Sports & Entertainment
5. Custom Topic

Choose topic (1-5, press Enter for default): 2

⏳ Creating room for 3 players...
🤖 AI will generate 10 questions about: science and technology

✅ Room created successfully!
🔑 Room ID: A7B2C3D4
👤 Username: Alice
📚 Topic: science and technology
❓ Questions: 10
👥 Waiting for 3 players...
📊 Players in lobby: 1/3

💡 Share this Room ID with other players!

👋 Bob joined the room!
📊 Players in lobby: 2/3

👋 Charlie joined the room!
📊 Players in lobby: 3/3

🤖 AI is generating 10 questions about science and technology...
⏳ Please wait...

✅ Questions ready! 10 questions generated.

🎉 All players joined! Game starting in 10 seconds...
⏰ Starting in 10...

============================================================
❓ QUESTION 1/10
============================================================

What does DNA stand for?

  A) Deoxyribonucleic Acid
  B) Deoxyribose Nucleic Acid
  C) Dynamic Nuclear Acid
  D) Deoxygenated Nuclear Acid

⏰ Time limit: 5 seconds
============================================================

👉 Your answer (A/B/C/D): A
✅ Answer submitted!

============================================================
✅ CORRECT ANSWER: A
============================================================

🏆 FASTEST CORRECT ANSWERS:
  🥇 Alice (+3 points)
  🥈 Bob (+2 points)
  🥉 Charlie (+1 point)

============================================================
📊 CURRENT SCORES
============================================================
🥇   3 points
🥈   2 points
🥉   1 points
============================================================

⏳ Next question in 3 seconds...
```

## 🔧 Customization

### Adjusting Question Generation

Edit `quiz_server_llm.py` to customize the prompt:

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", """Generate {num_questions} random general knowledge multiple choice questions.

Rules:
- Exactly {num_questions} questions
- 4 options per question
- Only one correct answer
- Mix easy, medium, and hard difficulty
- Diverse topics (science, history, geography, sports, entertainment, etc.)
- Make questions engaging and educational

Return ONLY valid JSON...
"""),
    ("user", "Generate quiz with {num_questions} questions about {topic}")
])
```

### Changing Time Limits

In `quiz_server_llm.py`, modify these values:

```python
# Line ~355 - Question time limit
await broadcast_to_room(room_id, {
    "type": "question",
    "time_limit": 5  # Change to desired seconds
})
await asyncio.sleep(5)  # Must match time_limit

# Line ~367 - Delay between questions
await asyncio.sleep(3)  # Change delay here

# Line ~346 - Game start countdown
for i in range(10, 0, -1):  # Change 10 to desired countdown
```

### Customizing Scoring System

Modify the `calculate_scores_for_question()` method:

```python
# Award different points
points = [5, 3, 1]  # 1st=5, 2nd=3, 3rd=1

# Change wrong answer penalty
self.scores[user_id] -= 2  # -2 instead of -1
```

### Adding Custom Topics

In `quiz_client_llm.py`, expand the topic menu:

```python
print("📚 Quiz Topic Options:")
print("1. General Knowledge (default)")
print("2. Science & Technology")
print("3. History & Geography")
print("4. Sports & Entertainment")
print("5. Movies & TV Shows")  # Add new option
print("6. Custom Topic")

topic_map = {
    "1": "general knowledge",
    "2": "science and technology",
    "3": "history and geography",
    "4": "sports and entertainment",
    "5": "movies and TV shows",  # Add mapping
    "": "general knowledge"
}
```

## 🌐 Network Configuration

### Allow Remote Connections

**In `quiz_server_llm.py`**, change:
```python
async with websockets.serve(handle_client, "0.0.0.0", 8765):
```

**In `quiz_client_llm.py`**, change:
```python
self.websocket = await websockets.connect("ws://SERVER_IP:8765")
```

Replace `SERVER_IP` with your server's IP address.

## 🔍 How It Works

### Architecture

```
┌─────────────┐
│   Client 1  │─┐
└─────────────┘ │
┌─────────────┐ │    WebSocket     ┌──────────────┐
│   Client 2  │─┼──────────────────│    Server    │
└─────────────┘ │                  │  (quiz_      │
┌─────────────┐ │                  │   server_    │
│   Client N  │─┘                  │   llm.py)    │
└─────────────┘                    └──────┬───────┘
                                          │
                                          │ API Call
                                          ▼
                                   ┌──────────────┐
                                   │   Groq LLM   │
                                   │  (LLaMA 3.3) │
                                   └──────────────┘
```

### Question Generation Flow

1. **Room Creation**: Host creates room and specifies topic
2. **Players Join**: All players join the lobby
3. **AI Generation**: Server calls Groq API to generate questions
4. **Conversion**: Questions converted to multiple-choice format
5. **Game Start**: Questions distributed to all players
6. **Real-time Scoring**: Answers collected and scored instantly

### Data Flow

```python
# LLM Response Format
[
    {
        "question": "What is the capital of France?",
        "options": ["London", "Berlin", "Paris", "Madrid"],
        "answer": "Paris"
    }
]

# Converted to Multiplayer Format
[
    {
        "question": "What is the capital of France?",
        "options": ["A) London", "B) Berlin", "C) Paris", "D) Madrid"],
        "correct_answer": "C"
    }
]
```

## 🐛 Troubleshooting

### API Key Issues

**Problem**: `Authentication error` or `Invalid API key`
- **Solution**: Check your `.env` file and ensure your Groq API key is correct

### Question Generation Fails

**Problem**: `Error generating quiz` or timeout
- **Solution**: Check your internet connection and Groq API status
- **Fallback**: System uses backup questions if LLM fails

### Connection Issues

**Problem**: `Connection refused` or `Failed to connect`
- **Solution**: Make sure `quiz_server_llm.py` is running first

### Room Not Found

**Problem**: `Room not found` error when joining
- **Solution**: Verify the Room ID is correct (case-sensitive)

### Slow Question Generation

**Problem**: Takes a long time to generate questions
- **Solution**: Normal for first request. Groq API typically responds in 2-5 seconds
- **Tip**: Reduce number of questions if needed

## 💡 Tips for Best Experience

1. **API Limits**: Groq free tier has rate limits. Don't generate too many questions at once
2. **Topic Specificity**: More specific topics produce better questions (e.g., "Ancient Roman History" vs "History")
3. **Player Count**: 3-5 players works best for competitive gameplay
4. **Question Count**: 10-15 questions is ideal for one game session
5. **Network**: Use stable internet connection for smooth gameplay

## 🚀 Advanced Features Ideas

Extend this project with:
- **Persistent Leaderboards**: Save scores to a database
- **Tournament Mode**: Multi-round elimination
- **Team Play**: Teams compete against each other
- **Power-ups**: Special abilities during gameplay
- **Spectator Mode**: Watch games in progress
- **Question Difficulty Levels**: Easy/Medium/Hard questions
- **Custom Question Banks**: Upload your own questions
- **Voice Chat**: Integrate voice communication
- **Web UI**: Browser-based interface instead of terminal

## 📊 Performance

- **Question Generation**: ~2-5 seconds (depends on Groq API)
- **Latency**: <100ms for answer submission (local network)
- **Concurrent Rooms**: Supports multiple simultaneous games
- **Players per Room**: Up to 10 players

## 🔐 Security Notes

- **API Keys**: Never commit `.env` file to version control
- **Input Validation**: Server validates all user inputs
- **Rate Limiting**: Consider adding rate limits for production use

## 📜 License

Free to use and modify for personal and educational projects!

## 🤝 Contributing

Feel free to fork and improve! Areas for enhancement:
- Better error handling and recovery
- Reconnection logic for dropped connections
- More sophisticated scoring algorithms
- UI/UX improvements
- Additional game modes

## 🆘 Support

Having issues? Check:
1. Python version (3.7+)
2. Dependencies installed (`pip install -r requirements_llm.txt`)
3. `.env` file configured correctly
4. Server is running before starting clients
5. Groq API is accessible

## 🎓 Educational Use

This project demonstrates:
- WebSocket real-time communication
- Async/await patterns in Python
- LLM integration with LangChain
- Client-server architecture
- State management in multiplayer games

Perfect for learning about:
- Real-time applications
- AI/LLM integration
- Game development
- Network programming

---

**Enjoy your AI-powered quiz battles! 🎉🤖**
