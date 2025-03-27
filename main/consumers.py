import json
import time
import threading
import socketio
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async, async_to_sync
from .adapter import create_ai_image

class AIConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        await self.accept()
        self.room_group_name = f'web_ai_{self.scope['client'][1]}'
        print("Group Name: ", self.room_group_name)
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        print("Group Added")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def send_message(self, event):
        print("From Send Message --> ", event)
        await self.send(text_data=json.dumps(event))

    async def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        command = text_data_json["command"]

        command_type = {
            "generate_image": self.generate_image
        }

        try:
            await command_type[command](text_data_json)
        except Exception as e:
            await self.send(
                {
                    "type": "websocket.close",
                }
            )

        return None

    async def generate_image(self, event):
        for i in range(5):  # Generate 5 images
            url = await self.create_ai_image("Generate an image of truck", None, f"{i}-{self.room_group_name}")
            print(f"Sending {url} to {self.room_group_name}")

            await self.send(text_data=json.dumps({"url": url}))
        
    async def create_ai_image(self, prompt, image, i):
        url = await create_ai_image(prompt, image, i)
        return url
