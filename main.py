from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict, List
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# rooms: room_id -> {"players": List[WebSocket], "colors": Dict[WebSocket, str]}
rooms: Dict[str, Dict] = {}

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()
    print("WS Connected!")

    if room_id not in rooms:
        rooms[room_id] = {"players": [], "colors": {}}

    room = rooms[room_id]
    players = room["players"]
    colors = room["colors"]

    # # 空きがあれば色を割り当てる
    # if len(players) >= 2:
    #     await websocket.send_text(json.dumps({"type":"full"}))
    #     await websocket.close()
    #     return

    color = "white" if "white" not in colors.values() else "black"
    colors[websocket] = color
    players.append(websocket)

    # 接続したクライアントに自分の色を通知
    await websocket.send_text(json.dumps({"type":"assign_color","color":color}))
    print("WS Color send!")

    try:
        while True:
            data = await websocket.receive_text()
            # 他プレイヤーにのみ送信
            for conn in players:
                if conn != websocket:
                    await conn.send_text(data)
    except WebSocketDisconnect:
        players.remove(websocket)
        del colors[websocket]
