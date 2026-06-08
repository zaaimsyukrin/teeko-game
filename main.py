from teeko_app import TeekoPlayer
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import random
import string
import json
from dataclasses import dataclass, field
from typing import Optional

app = FastAPI()

# to fix CORS blocking by backend
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# /??
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

# ── Room state ──
@dataclass
class Room:
    room_id: str
    board: list = field(default_factory=lambda: [[' ']*5 for _ in range(5)])
    piece_count: int = 0
    current_turn: str = 'b'
    players: dict = field(default_factory=dict)
    connections: dict = field(default_factory=dict)
    game_over: bool = False
    winner: Optional[str] = None
    mode: str = 'waiting'  # 'waiting' | 'playing' | 'ai'
    chat: list = field(default_factory=list) 
    ai: Optional[TeekoPlayer] = None

rooms: dict[str, Room] = {}

# spits out random room code
def make_room_code():
    res = ''.join(random.choices(string.ascii_uppercase, k=5))
    while res in rooms:
        res = ''.join(random.choices(string.ascii_uppercase, k=5))
    return res

@app.post("/create-room")
async def create_room(body: dict):
    player_id = body.get("player_id", "p1")
    mode = body.get("game_type", "multiplayer")
    
    room_id = make_room_code()
    room = Room(room_id=room_id)
    
    room.players[player_id] = 'b'
    
    if mode == 'ai':
        room.ai = TeekoPlayer()
        room.mode = 'ai'
    
    rooms[room_id] = room
    
    return {"room_id": room_id, "piece": 'b'}

@app.post("/join-room")
async def join_room(body: dict):
    player_id = body.get("player_id", "p2")
    room_id = body.get("room_id")
    room = rooms.get(room_id)
    
    # if room doesn't exist, error
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # if room is full, error
    if len(room.players) >= 2:
        raise HTTPException(status_code=400, detail="Room is full")
    
    # player who joins a room is red
    room.players[player_id] = 'r'
    room.mode = 'playing'
    
    return {"room_id": room_id, "piece": 'r'}

async def broadcast(room: Room, message: dict):
    for player_id, ws in room.connections.items():
        await ws.send_text(json.dumps(message))

def state_dict(room: Room):
    return {
        "board": room.board,
        "piece_count": room.piece_count,
        "current_turn": room.current_turn,
        "players": room.players,
        "game_over": room.game_over,
        "winner": room.winner,
        "mode": room.mode,
        "chat": room.chat
    }

def check_winner(room: Room):
    checker = TeekoPlayer()
    result = checker.game_value(room.board)
    if result == 1:
        for pid, piece in room.players.items():
            if piece == 'r':
                room.winner = pid
        room.game_over = True
    elif result == -1:
        for pid, piece in room.players.items():
            if piece == 'b':
                room.winner = pid
        room.game_over = True

@app.websocket("/ws/{room_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, player_id: str):
    await websocket.accept()
    
    room = rooms.get(room_id)
    if room is None:
        await websocket.close()
        return
    
    # store this player's connection
    room.connections[player_id] = websocket
    await broadcast(room, {"type": "state", "data": state_dict(room)})
    
    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            mtype = msg.get("type")
            
            if mtype == "move":
                if room.game_over:
                    continue
                dest = msg.get("dest")  # [row, col]
                src = msg.get("src")    # [row, col] or None in drop phase
                
                # validate player's turn
                my_piece = room.players.get(player_id)
                if room.current_turn != my_piece:
                    continue

                # validate destination is empty
                if room.board[dest[0]][dest[1]] != ' ':
                    continue

                # update board
                room.board[dest[0]][dest[1]] = my_piece
                if src:
                    room.board[src[0]][src[1]] = ' '
                
                # after move
                if room.piece_count < 8:
                    room.piece_count += 1

                # check win condition
                check_winner(room)
                
                # switch turn only if game is still going
                if not room.game_over:
                    room.current_turn = 'r' if my_piece == 'b' else 'b'

                # broadcast
                await broadcast(room, {"type": "state", "data": state_dict(room)})

                # ------ AI MOVES --------
                if room.mode == 'ai' and not room.game_over:
                    move = room.ai.best_response(room.board)
                    
                    # drop phase
                    if len(move) == 1:
                        room.board[move[0][0]][move[0][1]] = 'r'

                    # all-pieces-on-board phase
                    elif len(move) == 2:
                        dst = move[0]
                        src = move[1]
                        room.board[dst[0]][dst[1]] = 'r' 
                        room.board[src[0]][src[1]] = ' '

                    # after move
                    if room.piece_count < 8:
                        room.piece_count += 1

                    # check win condition
                    check_winner(room)

                    # change turn
                    room.current_turn = 'b'

                    await broadcast(room, {"type": "state", "data": state_dict(room)})

            
            elif mtype == "chat":
                text = msg.get("text")
                room.chat.append({"player": player_id, "text": text})
                await broadcast(room, {"type": "chat", "data": {"player": player_id, "text": text}})

    
    except WebSocketDisconnect:
        room.connections.pop(player_id, None)
        await broadcast(room, {"type": "player_left", "player_id": player_id})


