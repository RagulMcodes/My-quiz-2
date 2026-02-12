import asyncio
import websockets
import json
import sys
from datetime import datetime

class QuizClient:
    def __init__(self):
        self.websocket = None
        self.room_id = None
        self.username = None
        self.connected = False
        
    async def connect(self):
        """Connect to the WebSocket server"""
        try:
            self.websocket = await websockets.connect("ws://localhost:8765")
            self.connected = True
            print("✅ Connected to AI-powered quiz server!")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to server: {e}")
            print("Make sure the server is running on ws://localhost:8765")
            return False
    
    async def send_message(self, message):
        """Send a message to the server"""
        if self.websocket:
            await self.websocket.send(json.dumps(message))
    
    async def create_room(self):
        """Create a new room"""
        print("\n" + "="*50)
        print("🎮 CREATE A NEW ROOM")
        print("="*50)
        
        self.username = input("Enter your username: ").strip()
        if not self.username:
            self.username = f"Player_{datetime.now().strftime('%H%M%S')}"
        
        while True:
            try:
                max_participants = int(input("Enter number of participants (2-10): "))
                if 2 <= max_participants <= 10:
                    break
                print("❌ Please enter a number between 2 and 10")
            except ValueError:
                print("❌ Please enter a valid number")
        
        while True:
            try:
                num_questions = int(input("Enter number of questions (5-20): "))
                if 5 <= num_questions <= 20:
                    break
                print("❌ Please enter a number between 5 and 20")
            except ValueError:
                print("❌ Please enter a valid number")
        
        print("\n📚 Quiz Topic Options:")
        print("1. General Knowledge (default)")
        print("2. Science & Technology")
        print("3. History & Geography")
        print("4. Sports & Entertainment")
        print("5. Custom Topic")
        
        topic_choice = input("\nChoose topic (1-5, press Enter for default): ").strip()
        
        topic_map = {
            "1": "general knowledge",
            "2": "science and technology",
            "3": "history and geography",
            "4": "sports and entertainment",
            "": "general knowledge"
        }
        
        if topic_choice == "5":
            topic = input("Enter custom topic: ").strip() or "general knowledge"
        else:
            topic = topic_map.get(topic_choice, "general knowledge")
        
        await self.send_message({
            "action": "create_room",
            "username": self.username,
            "max_participants": max_participants,
            "num_questions": num_questions,
            "topic": topic
        })
        
        print(f"\n⏳ Creating room for {max_participants} players...")
        print(f"🤖 AI will generate {num_questions} questions about: {topic}")
    
    async def join_room(self):
        """Join an existing room"""
        print("\n" + "="*50)
        print("🚪 JOIN A ROOM")
        print("="*50)
        
        self.username = input("Enter your username: ").strip()
        if not self.username:
            self.username = f"Player_{datetime.now().strftime('%H%M%S')}"
        
        room_id = input("Enter room ID: ").strip().upper()
        
        await self.send_message({
            "action": "join_room",
            "username": self.username,
            "room_id": room_id
        })
        
        print(f"\n⏳ Joining room {room_id}...")
    
    async def handle_question(self, data):
        """Handle incoming question"""
        print("\n" + "="*60)
        print(f"❓ QUESTION {data['question_number']}/{data['total_questions']}")
        print("="*60)
        print(f"\n{data['question']}\n")
        
        for option in data['options']:
            print(f"  {option}")
        
        print(f"\n⏰ Time limit: {data['time_limit']} seconds")
        print("="*60)
        
        # Start async input task
        asyncio.create_task(self.get_answer())
    
    async def get_answer(self):
        """Get answer from user with timeout"""
        try:
            # Use asyncio to read input without blocking
            answer = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: input("\n👉 Your answer (A/B/C/D): ").strip().upper()
                ),
                timeout=5.0
            )
            
            if answer in ['A', 'B', 'C', 'D']:
                await self.send_message({
                    "action": "submit_answer",
                    "room_id": self.room_id,
                    "answer": answer
                })
                print("✅ Answer submitted!")
            else:
                print("❌ Invalid answer format")
        except asyncio.TimeoutError:
            print("\n⏱️  Time's up!")
        except Exception as e:
            print(f"❌ Error submitting answer: {e}")
    
    def display_scores(self, scores):
        """Display current scores"""
        print("\n" + "="*60)
        print("📊 CURRENT SCORES")
        print("="*60)
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        for i, (user_id, score) in enumerate(sorted_scores, 1):
            rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
            print(f"{rank_emoji} {score:3d} points")
        print("="*60)
    
    async def handle_message(self, message):
        """Handle incoming messages from server"""
        msg_type = message.get("type")
        
        if msg_type == "room_created":
            self.room_id = message["room_id"]
            print(f"\n✅ Room created successfully!")
            print(f"🔑 Room ID: {self.room_id}")
            print(f"👤 Username: {message['username']}")
            print(f"📚 Topic: {message.get('topic', 'general knowledge')}")
            print(f"❓ Questions: {message.get('num_questions', 10)}")
            print(f"👥 Waiting for {message['max_participants']} players...")
            print(f"📊 Players in lobby: {message['current_participants']}/{message['max_participants']}")
            print("\n💡 Share this Room ID with other players!")
        
        elif msg_type == "room_joined":
            self.room_id = message["room_id"]
            print(f"\n✅ Joined room successfully!")
            print(f"🔑 Room ID: {self.room_id}")
            print(f"👤 Username: {message['username']}")
            print(f"📚 Topic: {message.get('topic', 'general knowledge')}")
            print(f"❓ Questions: {message.get('num_questions', 10)}")
            print(f"📊 Players in lobby: {message['current_participants']}/{message['max_participants']}")
        
        elif msg_type == "participant_joined":
            print(f"\n👋 {message['username']} joined the room!")
            print(f"📊 Players in lobby: {message['current_participants']}/{message['max_participants']}")
            print(f"👥 Players: {', '.join(message['participants'])}")
        
        elif msg_type == "participant_disconnected":
            print(f"\n⚠️  {message['message']}")
        
        elif msg_type == "generating_questions":
            print(f"\n{message['message']}")
            print("⏳ Please wait...")
        
        elif msg_type == "questions_generated":
            print(f"\n{message['message']}")
        
        elif msg_type == "game_starting":
            print(f"\n🎉 {message['message']}")
        
        elif msg_type == "countdown":
            seconds = message['seconds']
            print(f"⏰ Starting in {seconds}...", end='\r')
        
        elif msg_type == "question":
            await self.handle_question(message)
        
        elif msg_type == "answer_recorded":
            # Already handled in get_answer
            pass
        
        elif msg_type == "question_results":
            print("\n" + "="*60)
            print("✅ CORRECT ANSWER:", message['correct_answer'])
            print("="*60)
            
            if message['rankings']:
                print("\n🏆 FASTEST CORRECT ANSWERS:")
                for i, (user_id, username, timestamp) in enumerate(message['rankings'], 1):
                    emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                    points = 3 if i == 1 else 2 if i == 2 else 1
                    print(f"  {emoji} {username} (+{points} points)")
            
            self.display_scores(message['scores'])
            print("\n⏳ Next question in 3 seconds...")
        
        elif msg_type == "game_ended":
            print("\n" + "="*60)
            print("🎊 GAME OVER! 🎊")
            print("="*60)
            print("\n🏆 FINAL RANKINGS:\n")
            
            for i, (username, score) in enumerate(message['final_scores'], 1):
                if i == 1:
                    print(f"🥇 1st Place: {username} - {score} points ⭐")
                elif i == 2:
                    print(f"🥈 2nd Place: {username} - {score} points")
                elif i == 3:
                    print(f"🥉 3rd Place: {username} - {score} points")
                else:
                    print(f"   {i}th Place: {username} - {score} points")
            
            if message['winner']:
                print(f"\n🎉 Congratulations {message['winner']}! 🎉")
            
            print("\n" + "="*60)
            print("Thanks for playing! 👋")
            print("="*60)
        
        elif msg_type == "error":
            print(f"\n❌ Error: {message['message']}")
            self.connected = False
    
    async def listen(self):
        """Listen for messages from server"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_message(data)
        except websockets.exceptions.ConnectionClosed:
            print("\n❌ Connection to server lost")
            self.connected = False
    
    async def run(self):
        """Main client loop"""
        print("="*50)
        print("🤖 AI-POWERED MULTIPLAYER QUIZ 🤖")
        print("="*50)
        
        if not await self.connect():
            return
        
        print("\nWhat would you like to do?")
        print("1. Create a new room")
        print("2. Join an existing room")
        
        while True:
            choice = input("\nEnter your choice (1 or 2): ").strip()
            if choice in ['1', '2']:
                break
            print("❌ Please enter 1 or 2")
        
        if choice == '1':
            await self.create_room()
        else:
            await self.join_room()
        
        # Start listening for messages
        await self.listen()


async def main():
    client = QuizClient()
    try:
        await client.run()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
