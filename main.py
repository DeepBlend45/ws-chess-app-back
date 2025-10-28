from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI()

# CORS設定（Vueフロント用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite標準ポート
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーム単位で接続を管理
rooms = {}  # { room_id: [WebSocket, WebSocket] }

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()

    # 初回接続ならルーム作成
    if room_id not in rooms:
        rooms[room_id] = []

    room = rooms[room_id]

    # ルームが満員の場合は拒否
    if len(room) >= 2:
        await websocket.send_text(json.dumps({"type": "error", "message": "Room full"}))
        await websocket.close()
        return

    # 接続追加
    room.append(websocket)
    player_color = "white" if len(room) == 1 else "black"

    # 色をプレイヤーに送信
    await websocket.send_text(json.dumps({
        "type": "assign_color",
        "color": player_color
    }))

    print(f"Player {player_color} joined room {room_id}")

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # moveイベントを全員に転送
            if message.get("type") == "move":
                for client in room:
                    if client != websocket:
                        await client.send_text(json.dumps(message))

    except WebSocketDisconnect:
        print(f"Player {player_color} disconnected from room {room_id}")
        room.remove(websocket)
        # 誰もいなくなったらルーム削除
        if not room:
            del rooms[room_id]
