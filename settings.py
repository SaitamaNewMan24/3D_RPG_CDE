import math
from enum import Enum

# --- Performance & World ---
MAP_SIZE = 48
TILE_SIZE = 64
WIDTH = 1024
HEIGHT = 768
FPS = 60
FOV = math.pi / 3
NUM_RAYS = 150
DELTA_ANGLE = FOV / NUM_RAYS
MAX_DEPTH = 800
PLAYER_SPEED = 3.5
PLAYER_ROTATION_SPEED = 0.05
WALL_HEIGHT_MULTIPLIER = 21000
PARTICLE_EPSILON = 0.0001

# --- Weather ---
RAIN_COLOR = (150, 180, 220)
SNOW_COLOR = (255, 255, 255)
DUST_COLOR = (180, 160, 120)
WEATHER_TYPES = ['none', 'rain', 'rain_heavy', 'snow', 'sand']
WEATHER_INTENSITY = {'none': {'count': 0}, 'rain': {'count': 150}, 'rain_heavy': {'count': 400}, 'snow': {'count': 200}, 'sand': {'count': 300}}
WEATHER_TRANSITIONS = {'none': (2000, 4000), 'rain': (1000, 2000), 'rain_heavy': (1000, 1500), 'snow': (1500, 3000), 'sand': (800, 1500)}

class FloorTextureType(Enum):
    DIRT = 1; STONE = 2; WOOD = 3; GRASS = 4

class TileType(Enum):
    EMPTY = 0; WALL_BRICK = 1; WALL_STONE = 2; WALL_WOOD = 3
    DOOR = 4; DOOR_SILVER = 5; DOOR_GOLD = 6
    TREE = 10; DEAD_TREE = 11; BUSH = 12; ROCK = 13
    STANDING_TORCH = 14; WALL_TORCH = 15
    ITEM_DAGGER = 20; ITEM_KEY = 21; ITEM_KEY_SILVER = 22; ITEM_KEY_GOLD = 23
    ITEM_KEY_DUNGEON = 24; ITEM_HEALTH_POTION = 25; ITEM_FOOD = 26; ITEM_ARTIFACT = 27
    ITEM_UNLIT_TORCH = 28; ITEM_STAFF = 29
    ITEM_KEY_RUSTY_2 = 30; ITEM_STAMINA_POTION = 31
    WALL_BRICK_CRACKED = 40; WALL_STONE_CRACKED = 41; WALL_WOOD_CRACKED = 42
    STAIRS = 43; FORCE_FIELD = 44
    PLAYER_SPAWN = 50; ENEMY_GHOST = 60

# --- Asset Paths ---
WALL_TEXTURE_PATH = "Brick_Wall_64x64.png"
FLOOR_DIRT_PATH = "Dirt_Road_64x64.png"
FLOOR_GRASS_PATH = "Grass_Ground_64x64.png" 
CLOUD_SPRITE_PATH = "clouds_pixel.png"
TREE_LEAFY_PATHS = ["LeafyTree_1.png", "LeafyTree_2.png", "LeafyTree_3.png", "LeafyTree_4.png", "LeafyTree_5.png", "LeafyTree_6.png"]
TREE_DEAD_PATH = "DeadTree.png"
BUSH_PATHS = ["bush.png", "bush_2.png"]
ROCK_PATH = "rocks.png"
SWORD_PATH = "Sword_Icon.png"
KEY_PATH = "Key_Icon.png"
KEY_SILVER_PATH = "key_silver.png"
KEY_GOLD_PATH = "key_gold.png"
RUSTY_KEY_PATH = "rusty_key_to_dungeon.png"
RUSTY_KEY_2_PATH = "rusty_key_2.png"
MANA_POTION_PATH = "mana_potion.png"
HEALTH_POTION_PATH = "health_potion.png"
STAMINA_POTION_PATH = "stamina_potion.png"
ARTIFACT_PATH = "artifact.png"
FIREBALL_PATH = "fireball.png"
ENEMY_GHOST_PATH = "ghost_enemy_1.png"
MAP_DATA_FILE = "map_data.json"