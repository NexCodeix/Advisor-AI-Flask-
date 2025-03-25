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

connected_users_sid_data = {}

connected_user = {}

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
    data = {
        "message": "Connected!",
        "sid": sid,
    }
    emit("server", data, room=sid)


@socketio.on("register")
def handle_register(data):
    data = json.loads(data)
    print("DATA --> ", data)
    user_id = data.get("user_id")
    room = f"room_{user_id}"
    sid = request.sid
    connected_user[user_id] = request.sid
    connected_users_sid_data[sid] = user_id
    emit("server", {"message": "registered"}, room=sid)


@socketio.on("message")
def handle_message(data):
    print("DATA --> ", data)

    data = json.loads(data)
    print("DATA --> ", data)
    
    event = data.get("event")
    ai_data = data.get("data")
    prompt = ai_data.get("prompt")
    user_id = data.get("user_id")
    image_url = ai_data.get("image_url")

    if event == "generate-ai-images":
        print("Generating AI Images")

        init_image = adapter.add_image(image_url)
        lst = []
        prompt_variations = [
            f"{prompt}, ultra-detailed, cinematic lighting",
            f"{prompt}, surreal and dreamy, artistic brush strokes",
            f"{prompt}, futuristic and hyper-realistic, 8K resolution",
            f"{prompt}, in the style of a Renaissance painting",
            f"{prompt}, vibrant cyberpunk aesthetic, neon reflections"
        ]

        for i, prompt in enumerate(prompt_variations):
            url = adapter.create_ai_image(prompt, init_image, i)
            data = {
                "command": "asynchonous data sending",
                "sid": request.sid,
                "url": url,
            }
            data["for_user_id"] = user_id
            lst.append(url)
            emit('server', data, room=connected_user[user_id])
            socketio.sleep(0)

        data = {
            "command": "data send success",
            "sid": request.sid,
        }
        data["for_user_id"] = connected_users_sid_data[request.sid]
        emit('server', data, room=connected_user[user_id])
        socketio.sleep(0)

@socketio.on('disconnect')
def handle_disconnect():
    print("❌ Client disconnected")



@socketio.on("my_event")
def checkping():
    print("From event")
    for x in range(5):
        cmd = 'ping -c 1 8.8.8.8|head -2|tail -1'
        listing1 = subprocess.run(cmd,stdout=subprocess.PIPE,text=True,shell=True)
        sid = request.sid
        emit('server', {"data1":x, "data":listing1.stdout}, room=sid)
        socketio.sleep(1)


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
