"""Local repro: two persistent WS clients until game_ended (for server NDJSON logs)."""
import asyncio
import json
import sys

import websockets

URI = "ws://127.0.0.1:9876"


async def pump(name: str, ws, room_id: str):
    try:
        while True:
            raw = await asyncio.wait_for(ws.recv(), timeout=180)
            msg = json.loads(raw)
            t = msg.get("type")
            if t == "question":
                await ws.send(
                    json.dumps(
                        {"action": "submit_answer", "room_id": room_id, "answer": "A"}
                    )
                )
            if t == "game_ended":
                print(name, "saw game_ended")
                return
    except Exception as e:
        print(name, "pump error", e, file=sys.stderr)
        raise


async def main():
    async with websockets.connect(URI) as ws1:
        await ws1.send(
            json.dumps(
                {
                    "action": "create_room",
                    "username": "Host",
                    "max_participants": 2,
                    "num_questions": 2,
                    "topic": "general knowledge",
                }
            )
        )
        room_id = None
        while room_id is None:
            m = json.loads(await ws1.recv())
            if m.get("type") == "room_created":
                room_id = m["room_id"]
        print("room_id", room_id)

        async with websockets.connect(URI) as ws2:
            await ws2.send(
                json.dumps(
                    {
                        "action": "join_room",
                        "username": "Guest",
                        "room_id": room_id,
                    }
                )
            )
            jr = json.loads(await ws2.recv())
            if jr.get("type") != "room_joined":
                print("guest expected room_joined got", jr, file=sys.stderr)
                sys.exit(1)

            await asyncio.gather(
                pump("host", ws1, room_id),
                pump("guest", ws2, room_id),
            )


if __name__ == "__main__":
    asyncio.run(main())
