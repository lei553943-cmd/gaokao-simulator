"""三局猜拳 WebSocket 服务器."""
import asyncio
import json
import uuid
import websockets
from websockets import serve

ROOMS = {}
HOST, PORT = "0.0.0.0", 19876


async def handler(ws):
    player_id = str(uuid.uuid4())[:6]
    room_id = None
    print(f"[+] {player_id}")
    try:
        async for raw in ws:
            msg = json.loads(raw)
            a = msg.get("action")
            if a == "create":
                room_id = _new_room()
                ROOMS[room_id]["players"].append({"id": player_id, "ws": ws, "picks": None, "ready": False})
                await ws.send(json.dumps({"type": "created", "room": room_id, "player": player_id}))
            elif a == "join":
                room_id = msg.get("room")
                r = ROOMS.get(room_id)
                if not r: await ws.send(json.dumps({"type": "error", "msg": "房间不存在"})); continue
                if len(r["players"]) >= 2: await ws.send(json.dumps({"type": "error", "msg": "房间已满"})); continue
                r["players"].append({"id": player_id, "ws": ws, "picks": None, "ready": False})
                await ws.send(json.dumps({"type": "joined", "room": room_id, "player": player_id}))
                for p in r["players"]:
                    if p["id"] != player_id: await p["ws"].send(json.dumps({"type": "opponent_joined"}))
            elif a == "pick":
                r = ROOMS.get(room_id)
                if not r: continue
                for p in r["players"]:
                    if p["id"] == player_id: p["picks"] = msg.get("picks"); p["ready"] = True; break
                if all(p["ready"] for p in r["players"]) and len(r["players"]) == 2: await _resolve(r)
    except websockets.exceptions.ConnectionClosed: pass
    finally:
        if room_id and room_id in ROOMS:
            r = ROOMS[room_id]
            r["players"] = [p for p in r["players"] if p["id"] != player_id]
            if not r["players"]: del ROOMS[room_id]
            else:
                for p in r["players"]:
                    try: await p["ws"].send(json.dumps({"type": "opponent_left"}))
                    except: pass
        print(f"[-] {player_id}")


async def _resolve(r):
    beats = {"rock": "scissors", "scissors": "paper", "paper": "rock"}
    p0, p1 = r["players"]
    results, w0, w1 = [], 0, 0
    for i in range(3):
        a, b = p0["picks"][i], p1["picks"][i]
        if a == b: results.append("draw")
        elif beats[a] == b: results.append("win"); w0 += 1
        else: results.append("lose"); w1 += 1
    for i, p in enumerate(r["players"]):
        payload = {"type": "result", "my_picks": p["picks"], "opp_picks": r["players"][1 - i]["picks"]}
        if i == 0: payload["results"] = results; payload["my_wins"] = w0; payload["opp_wins"] = w1
        else: payload["results"] = ["win" if rv == "lose" else "lose" if rv == "win" else "draw" for rv in results]; payload["my_wins"] = w1; payload["opp_wins"] = w0
        await p["ws"].send(json.dumps(payload))
    for p in r["players"]: p["picks"] = None; p["ready"] = False


def _new_room():
    rid = str(uuid.uuid4())[:4].upper()
    while rid in ROOMS: rid = str(uuid.uuid4())[:4].upper()
    ROOMS[rid] = {"players": []}
    return rid


async def main():
    print(f"猜拳服务器 ws://{HOST}:{PORT}")
    async with serve(handler, HOST, PORT):
        await asyncio.get_running_loop().create_future()


if __name__ == "__main__":
    asyncio.run(main())
