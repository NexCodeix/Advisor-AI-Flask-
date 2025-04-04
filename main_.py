import json
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from utils import fetch_and_verify_image, generate_image
from adapter import StabilityAIAdapter
import subprocess

app = Flask(__name__)
socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*", transports=["websocket"])

adapter = StabilityAIAdapter()
adapter.enable_memory_efficiency()

connected_users = {}

connected_users_sid_data = {}


@app.route("/")
def hello():
    return render_template("index.html")


@app.route("/get-ai-images/", methods=["POST", ])
def get_ai_images_api_view():
    data = json.loads(request.data)
    prompt = data.get("prompt")
    image = data.get("image")

    if not prompt:
        return jsonify({"message": "Provide a Prompt"}), 403

    if not image:
        return jsonify({"message": "Provide a image"}), 403
    
    try:
        image = fetch_and_verify_image(image)
    except ValueError as e:
        return jsonify({"message": "Invalid image url provided"}), 200

    return jsonify({"message": "successfull"}), 200



@socketio.on('connect')
def handle_connect():
    print("✅ Client connected")
    sid = request.sid
    print(f"✅ Client connected: {sid}")


@socketio.on("register")
def handle_register(data):
    data = json.loads(data)
    user_id = data.get("user_id")
    room = f"room_{user_id}"
    connected_users[request.sid] = user_id
    join_room(room)
    print(f"👤 User {user_id} joined room {room}")
    emit("server", {"message": "registered", "user_id": user_id, "command": "ping"}, room=room)


@socketio.on("message")
def handle_message(data):
    data = json.loads(data)
    print("DATA --> ", data)
    
    event = data.get("event")
    ai_data = data.get("data")
    prompt = ai_data.get("prompt")
    user_id = data.get("user_id")
    image_url = ai_data.get("image_url")
    room = f"room_{user_id}"
    if event == "generate-ai-images":
        start_background_task(generate_image_in_background, data, prompt, image_url, room, user_id, request.sid)
        print("Completed Background tasking")

@socketio.on('disconnect')
def handle_disconnect():
    for i, j in connected_users.items():
        if i == request.sid:
            print("❌ Client disconnected User ID: ", j)
            room = f"room_{j}"
            # socketio.emit("user_disconnected", {"user_id": j}, room=room)
            emit("server", {"message": f"User {j} has disconnected", "command": "reconnect", "user_id": j}, broadcast=True)
            break


@socketio.on("ping")
def handle_ping(data):
    """Responds to keep-alive pings"""
    print("Data Received from Django", data)
    try:
        user_id = connected_users[request.sid]
    except KeyError as e:
        print(e)
        return None

    room = f"room_{user_id}"
    print(f"🔄 Received ping from {user_id}")
    emit("pong", {"message": "Pong!"}, room=room)  # Reply with "pong"


@socketio.on("my_event")
def checkping():
    print("From event")
    for x in range(5):
        cmd = 'ping -c 1 8.8.8.8|head -2|tail -1'
        listing1 = subprocess.run(cmd,stdout=subprocess.PIPE,text=True,shell=True)
        sid = request.sid
        emit('server', {"data1":x, "data":listing1.stdout}, room=sid)
        socketio.sleep(1)


def start_background_task(func, *args):
    socketio.start_background_task(func, *args)
    print("Started background tasking")


def generate_image_in_background(data, prompt, image_url, room, user_id, sid):
    init_image = adapter.add_image(image_url)
    lst = []
    prompt_variations = [
        f"{prompt}, ultra-detailed, cinematic lighting",
        f"{prompt}, surreal and dreamy, artistic brush strokes",
        f"{prompt}, futuristic and hyper-realistic, 8K resolution",
        f"{prompt}, in the style of a Renaissance painting",
        f"{prompt}, vibrant cyberpunk aesthetic, neon reflections",
        "",
        "",
        "",
    ]

    for i, prompt in enumerate(prompt_variations):
        url = adapter.create_ai_image(prompt, init_image, user_id)
        print(f"Generated AI Images for {user_id}")
        data = {
            "command": "asynchonous data sending",
            "sid": sid,
            "url": url,
        }
        data["for_user_id"] = user_id
        lst.append(url)
        socketio.emit('server', data, room=room)
        socketio.sleep(0)
        print("Emmitting to room: ", room)

    data = {
        "command": "data send success",
        "sid": sid,
    }
    data["for_user_id"] = user_id
    socketio.emit('server', data, room=room)
    socketio.sleep(0)

# @socketio.on('start_generation')
# def handle_image_generation(data):
#     print("Sending data")
#     """ Handle the request to generate images """
#     num_images = data.get('num_images', 1)  # Get number of images to generate

#     for i in range(num_images):
#         img_data = generate_image()  # Generate an image
#         emit('image_generated', {'image': img_data, 'index': i + 1})  # Send it


if __name__ == '__main__':
   socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
