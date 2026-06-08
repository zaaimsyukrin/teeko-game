import asyncio
import websockets
import json
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        res = await client.post("http://127.0.0.1:8000/create-room",
                                json={"player_id": "zaaim", "game_type": "ai"})
        room_id = res.json()["room_id"]
        print("Room:", room_id)

    uri = f"ws://127.0.0.1:8000/ws/{room_id}/zaaim"
    async with websockets.connect(uri) as ws:
        # get initial state
        msg = await ws.recv()
        print("Initial:", json.loads(msg))

        # send a move (drop phase, place at row 2 col 2)
        await ws.send(json.dumps({
            "type": "move",
            "dest": [2, 2],
            "src": None
        }))

        # get state after human move
        msg = await ws.recv()
        print("After human move:", json.loads(msg))

        # get state after AI move
        msg = await ws.recv()
        print("After AI move:", json.loads(msg))

asyncio.run(test())