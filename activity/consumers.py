import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Chat, ChatMessage
from .serializers import ChatMessageSerializer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.visitor_id = self.scope['url_route']['kwargs']['visitor_id']
        self.room_group_name = f'chat_{self.visitor_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        print(f"WebSocket connected for visitor: {self.visitor_id}")

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"WebSocket disconnected for visitor: {self.visitor_id}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json.get('message', '')
            chat_id = text_data_json.get('chat_id')

            if chat_id and message:
                # Save message to database
                chat_message = await self.save_message(chat_id, message)
                
                # Send message to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': ChatMessageSerializer(chat_message).data
                    }
                )
        except Exception as e:
            print(f"Error in receive: {e}")

    async def chat_message(self, event):
        try:
            message = event['message']
            # Send message to WebSocket
            await self.send(text_data=json.dumps({
                'type': 'chat.message',
                'message': message
            }))
            print(f"Message sent to WebSocket: {message}")
        except Exception as e:
            print(f"Error in chat_message: {e}")

    @database_sync_to_async
    def save_message(self, chat_id, message):
        from .models import Chat, ChatMessage
        chat = Chat.objects.get(id=chat_id)
        chat_message = ChatMessage.objects.create(
            chat=chat,
            message=message,
            is_admin=False
        )
        chat.update_last_message(message)
        return chat_message 

class AdminChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        chat = await self.get_chat()
        if chat:
            # Store visitor_id for later use
            self.visitor_id = chat.visitor_id
            # Join both chat rooms to ensure messages are received
            self.admin_room = f'admin_chat_{self.chat_id}'
            self.visitor_room = f'chat_{self.visitor_id}'
            
            await self.channel_layer.group_add(self.admin_room, self.channel_name)
            await self.channel_layer.group_add(self.visitor_room, self.channel_name)
            await self.accept()
        else:
            await self.close()

    @database_sync_to_async
    def get_chat(self):
        try:
            return Chat.objects.get(id=self.chat_id)
        except Chat.DoesNotExist:
            return None

    async def disconnect(self, close_code):
        if hasattr(self, 'admin_room'):
            await self.channel_layer.group_discard(self.admin_room, self.channel_name)
        if hasattr(self, 'visitor_room'):
            await self.channel_layer.group_discard(self.visitor_room, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data['message']
            
            # Save admin message to database
            chat_message = await self.save_admin_message(self.chat_id, message)
            serialized_message = ChatMessageSerializer(chat_message).data
            
            # Send message to both admin and visitor rooms
            message_data = {
                'type': 'chat.message',
                'message': serialized_message
            }
            
            await self.channel_layer.group_send(self.admin_room, message_data)
            await self.channel_layer.group_send(self.visitor_room, message_data)
            
        except Exception as e:
            print(f"Error processing message: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat.message',
            'message': event['message']
        }))

    @database_sync_to_async
    def save_admin_message(self, chat_id, message):
        chat = Chat.objects.get(id=chat_id)
        chat_message = ChatMessage.objects.create(
            chat=chat,
            message=message,
            is_admin=True
        )
        chat.update_last_message(message)
        return chat_message 