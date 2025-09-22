import os
from livekit import api
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS
from livekit.api import LiveKitAPI, ListRoomsRequest
import uuid

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def generate_room_name(rooms):
    name = "room-" + str(uuid.uuid4())[:8]
    while name in rooms:
        name = "room-" + str(uuid.uuid4())[:8]
    return name

def get_rooms():
    api_client = LiveKitAPI()
    # Note: LiveKitAPI.list_rooms is async, so you cannot call it directly synchronously.
    # You need to use an async event loop or switch to a fully async framework like Quart.
    # Alternatively, call the LiveKit REST API with requests or httpx synchronously.
    # For demo, let's use synchronous httpx:

    import httpx

    base_url = os.getenv("LIVEKIT_URL", "https://your-livekit-server")
    headers = {
        "Authorization": f"Bearer {os.getenv('LIVEKIT_API_KEY')}"
    }

    url = f"{base_url}/rooms"
    # This might need an API key/secret in headers depending on your LiveKit setup.

    try:
        response = httpx.get(url)
        response.raise_for_status()
        data = response.json()
        return [room["name"] for room in data.get("rooms", [])]
    except Exception as e:
        print("Failed to fetch rooms:", e)
        return []

@app.route("/getToken")
def get_token():
    name = request.args.get("name", "my name")
    room = request.args.get("room", None)
    
    rooms = get_rooms()
    if not room:
        room = generate_room_name(rooms)

    token = api.AccessToken(
        os.getenv("LIVEKIT_API_KEY"),
        os.getenv("LIVEKIT_API_SECRET")
    ).with_identity(name).with_name(name).with_grants(
        api.VideoGrants(room_join=True, room=room)
    )
    
    return jsonify({"token": token.to_jwt(), "room": room})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
