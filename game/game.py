from uuid import uuid4
import random
import logging


class Entity:
    id: str
    x: float
    y: float

    def __init__(self) -> None:
        # Initialize an Entity with a unique ID and default position (0, 0)
        self.id = uuid4().hex
        self.x = 0.00
        self.y = 0.00

    def set_position(self, x: float, y: float, facing: str = None):
        # Set the position of the Entity
        self.x = x
        self.y = y


class Player(Entity):
    facing: str
    alive: bool
    score: int

    def __init__(self) -> None:
        super().__init__()
        # Initialize Player with default attributes
        self.facing = "front"
        self.alive = True
        self.score = 0

    def set_position(self, x: float, y: float, facing: str):
        # Set the position of the Entity
        self.x = x
        self.y = y
        self.facing = facing

    def add_score(self, amount: int):
        # Add score to the Player
        self.score = self.score + amount

    def to_dict(self) -> dict:
        # Convert Player attributes to dictionary
        ret = dict()
        ret["id"] = self.id
        ret["x"] = self.x
        ret["y"] = self.y
        ret["facing"] = self.facing
        ret["alive"] = self.alive
        ret["score"] = self.score
        return ret


class Bomb(Entity):
    vx: float
    vy: float
    hit: bool

    def __init__(self) -> None:
        super().__init__()
        # Initialize Bomb with default velocity and hit status
        self.vx = 0.00
        self.vy = 0.00
        self.hit = False


class Star(Entity):
    collected = bool()

    def __init__(self) -> None:
        super().__init__()
        # Initialize Star with default collected status
        self.collected = False

    def to_dict(self) -> dict:
        # Convert Star attributes to dictionary
        ret = dict()
        ret["id"] = self.id
        ret["x"] = self.x
        ret["y"] = self.y
        ret["collected"] = self.collected
        return ret


class Game:
    READY = 0x01
    RUNNING = 0x02
    OVER = 0x03

    state: str
    round: int
    players: dict[Player]
    stars: dict[Star]
    bombs: dict[Bomb]

    def __init__(self) -> None:
        # Initialize Game with default state and round, and empty collections for players, stars, and bombs
        self.state = self.READY
        self.round = 0
        self.players = {}
        self.stars = {}
        self.bombs = {}

    def start(self) -> None:
        # Start the game, set state to RUNNING, and initiate the first round
        self.state = self.RUNNING
        self.round = 1
        self.spawn_stars()
        logging.info(f"Game started with stars: {self.get_stars()}")

    def game_over(self) -> None:
        # End the game, set state to OVER
        self.state = self.OVER
        self.delete_stars()
        self.delete_bombs()

    def next_round(self) -> None:
        # Proceed to the next round, spawn stars and a bomb with random velocity
        self.round = self.round + 1
        self.delete_stars()
        self.spawn_stars()
        vx = random.randint(-200, 200)
        self.spawn_bomb(400, 300, vx, 0)
        logging.info(f"New round {self.round}")

    def player_joined(self) -> Player:
        # Add a new player to the game
        player = Player()
        self.players[player.id] = player
        return player

    def player_left(self, id: str) -> None:
        # Remove a player from the game by ID
        player: Player = self.players.get(id)
        if player == None:
            return
        del self.players[id]

        # End the game if no players are left
        if len(self.players) == 0:
            self.game_over()

    def get_players(self) -> dict:
        # Get a dictionary of all players and their attributes
        players = dict()
        for player in self.players.values():
            players[player.id] = player.to_dict()
        return players

    def at_least_one_player_alive(self) -> bool:
        # Check if at least one player is alive
        for player in self.players.values():
            if player.alive:
                return True
        return False

    def spawn_star(self, x: float, y: float) -> Star:
        # Create and position a new star in the game
        star = Star()
        star.set_position(x, y)
        self.stars[star.id] = star
        return star

    def collect_star(self, star_id: str, player_id: str) -> bool:
        # Handle star collection by a player, check if all stars are collected to proceed to next round
        star: Star = self.stars.get(star_id)
        player: Player = self.players.get(player_id)
        if star is None or player is None:
            return None
        star.collected = True
        player.add_score(10)

        if self.all_stars_collected():
            self.next_round()
            return True
        return False

    def all_stars_collected(self) -> bool:
        # Check if all stars in the game are collected
        for star in self.stars.values():
            if not star.collected:
                return False
        return True

    def spawn_stars(self) -> None:
        # Spawn 12 stars at specific intervals
        for i in range(12):
            self.spawn_star(12 + i * 70, 0)

    def get_stars(self) -> dict:
        # Get a dictionary of all stars and their attributes
        stars = dict()
        for star in self.stars.values():
            stars[star.id] = star.to_dict()
        return stars

    def delete_stars(self) -> None:
        # Delete all stars from the game
        self.stars = {}

    def spawn_bomb(self, x: float, y: float, vx: float, vy: float) -> Bomb:
        # Create and position a new bomb in the game
        bomb = Bomb()
        bomb.set_position(x, y)
        bomb.vx = vx
        bomb.vy = vy
        self.bombs[bomb.id] = bomb
        return bomb

    def hit_bomb(self, bomb_id: str, player_id: str) -> bool:
        # Handle a player getting hit by a bomb, check if the game is over
        bomb: Bomb = self.bombs.get(bomb_id)
        player: Player = self.players.get(player_id)
        if bomb is None or player is None:
            return None
        bomb.hit = True
        player.alive = False

        if not self.at_least_one_player_alive():
            self.game_over()
            return True
        return False

    def get_bombs(self) -> dict:
        # Get a dictionary of all bombs and their attributes
        bombs = dict()
        for bomb in self.bombs.values():
            bombs[bomb.id] = bomb.__dict__
        return bombs

    def delete_bombs(self) -> None:
        # Delete all bombs from the game
        self.bombs = {}


class GameManager:
    games: dict[Game]

    def __init__(self) -> None:
        # Initialize GameManager with an empty collection of games
        self.games = {}

    def create(self, room) -> Game:
        # Create a new game for a given room
        game = Game()
        self.games[room] = game
        return game

    def get(self, room) -> Game:
        # Retrieve the game associated with a given room
        game: Game = self.games.get(room)
        return game
