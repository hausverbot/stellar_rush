from channels.generic.websocket import AsyncWebsocketConsumer

from .game import Game, GameManager, Player
import random
import json
import uuid
import logging
import asyncio

# Initialize a game manager to handle multiple game instances
game_manager = GameManager()
logging.basicConfig(level=logging.INFO)


class GameConsumer(AsyncWebsocketConsumer):
    player: Player = None
    game: Game = None
    room: str = ""

    async def send_to_group(self, topic, payload):
        # Send a message to all members of the room group
        await self.channel_layer.group_send(self.room, {'type': "game_event", 'topic': topic, 'payload': payload})

    async def connect(self):
        # Handle a new WebSocket connection
        self.room = self.scope['url_route']['kwargs']['room_name']
        self.game = game_manager.get(self.room)

        # Create a new game if one doesn't exist for the room
        if self.game is None:
            self.game = game_manager.create(self.room)

        # Add a new player to the game
        self.player = self.game.player_joined()

        await asyncio.sleep(2.0)

        # Notify the group that a new player has joined
        await self.send_to_group('player_joined', {'player_id': self.player.id})

        # Join room group
        await self.channel_layer.group_add(
            self.room,
            self.channel_name
        )

        # Accept the WebSocket connection
        await self.accept()

    async def disconnect(self, close_code):
        # Handle WebSocket disconnection
        await self.send_to_group('player_left', {'player_id': self.player.id})

        # Leave room group
        await self.channel_layer.group_discard(
            self.room,
            self.channel_name
        )

        # Remove the player from the game
        game_manager.get(self.room).player_left(self.player.id)

    async def receive(self, text_data):
        # Handle messages received from the WebSocket
        text_data_json = json.loads(text_data)
        message_type = text_data_json['topic']
        payload = text_data_json['payload']
        player_id = text_data_json['player_id']

        # Ensure the message has content and a player ID
        #if payload == {} or "player_id" not in text_data_json:
        #    return

        if message_type == 'connect':
            logging.info(f"Player id {player_id} connected. ")
            # Send initial game state to the new player
            await self.send(text_data=json.dumps({
                'type': 'game_event',
                'topic': 'init',
                'player_id': self.player.id,
                'game_state': self.game.state,
                'players': self.game.get_players(),
                'stars': self.game.get_stars(),
                'bombs': self.game.get_bombs()
            }))
            logging.info(f"Player id {player_id}, Players: {self.game.get_players()}, "
                         f"Stars: {self.game.get_stars()}, Bombs:{self.game.get_bombs()}.")
            print("connect")
        elif message_type == 'movement':
            # Handle player movement
            player: Player = self.game.players.get(player_id)
            player.set_position(payload['x'], payload['y'], payload['facing'])
            await self.send(text_data=json.dumps({
                'type': 'game_event',
                'topic': 'ack',
                'req_id': text_data_json['req_id']
            }))
            await self.send_to_group('player_movement', {'payload': payload, 'player_id': player_id})
            logging.info(text_data_json)
        elif message_type == 'start_game':
            # Handle game start
            if self.game.state == Game.RUNNING:
                return

            self.game.start()

            await self.send_to_group('game_start', {'payload': {
                'stars': self.game.get_stars(),
                'bombs': self.game.get_bombs()
            }})

        elif message_type == 'collect_star':
            # Handle star collection by a player
            star_id = payload['star_id']
            print(f"player_id: {player_id}")
            is_next_round = self.game.collect_star(star_id, player_id)

            if is_next_round:
                await self.send_to_group('next_round', {
                    'stars': self.game.get_stars(),
                    'bombs': self.game.get_bombs()
                })
            else:
                await self.send_to_group('star_collected', {'star_id': star_id})

        elif message_type == 'hit_bomb':
            # Handle a player hitting a bomb
            bomb_id = payload['bomb_id']
            is_game_over = self.game.hit_bomb(bomb_id, player_id)

            if is_game_over:
                await self.send_to_group('game_over', {})
            else:
                await self.send_to_group('bomb_hit', {'player_id': player_id, 'bomb_id': bomb_id})

    async def game_event(self, event):
        # Send a game event message to the WebSocket
        message = event['payload']
        message['topic'] = event['topic']
        await self.send(text_data=json.dumps(message))
