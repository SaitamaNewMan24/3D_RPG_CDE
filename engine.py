from numpy._core.umath import spacing
import pygame
import json
import os
import random
import copy
import math
from settings import *
from inventory import Inventory
from ui import ActionBar

class DummyChannel:
    def play(self, *args, **kwargs): pass
    def stop(self): pass
    def get_busy(self): return False
    def set_volume(self, vol): pass
    def fadeout(self, time): pass

try:
    pygame.mixer.init()
    CH_WALK = pygame.mixer.Channel(1)
    CH_RAIN = pygame.mixer.Channel(2)
    CH_CRICKETS = pygame.mixer.Channel(3)
    CH_TORCHES = pygame.mixer.Channel(4) 
    MIXER_READY = True
except Exception:
    CH_WALK = DummyChannel()
    CH_RAIN = DummyChannel()
    CH_CRICKETS = DummyChannel()
    CH_TORCHES = DummyChannel()
    MIXER_READY = False

def load_audio_safe(filename):
    if not MIXER_READY: return None
    try: return pygame.mixer.Sound(filename)
    except: return None

def load_image_safe(filename):
    """Safely load an image and return it, or None if it fails"""
    try:
        return pygame.image.load(filename).convert()
    except:
        return None

SFX_PICKUP = load_audio_safe("pickup.wav")
SFX_DOOR = load_audio_safe("door.wav")
SFX_ERROR = load_audio_safe("error.wav")
SFX_USE = load_audio_safe("use.wav")
SFX_WALK = load_audio_safe("walking.mp3")
SFX_RAIN = load_audio_safe("raining.mp3")
SFX_FIREBALL = load_audio_safe("shoot_fireball.wav")
SFX_DRINK = load_audio_safe("drink.wav")
SFX_CRICKETS = load_audio_safe("Midnight_crickets.mp3")
SFX_TORCH = load_audio_safe("torches_burning_sound.mp3") 
SFX_HIT_METALLIC = load_audio_safe("sword_hit_metallic.mp3")

def get_tile_color(tile_type):
    """Return color for minimap tiles based on tile type"""
    if tile_type == TileType.EMPTY.value:
        return (50, 50, 50)  # Dark gray
    elif tile_type in [TileType.WALL_BRICK.value, TileType.WALL_STONE.value, TileType.WALL_WOOD.value,
                       TileType.WALL_BRICK_CRACKED.value, TileType.WALL_STONE_CRACKED.value, 
                       TileType.WALL_WOOD_CRACKED.value]:
        return (150, 150, 150)  # Gray for walls
    elif tile_type in [TileType.TREE.value, TileType.DEAD_TREE.value, TileType.BUSH.value]:
        return (0, 150, 0)  # Green for vegetation
    elif tile_type == TileType.ROCK.value:
        return (100, 100, 100)  # Dark gray for rocks
    elif tile_type in [TileType.ITEM_DAGGER.value, TileType.ITEM_KEY.value, TileType.ITEM_KEY_SILVER.value,
                       TileType.ITEM_KEY_GOLD.value, TileType.ITEM_KEY_DUNGEON.value, TileType.ITEM_HEALTH_POTION.value,
                       TileType.ITEM_FOOD.value, TileType.ITEM_ARTIFACT.value, TileType.ITEM_UNLIT_TORCH.value,
                       TileType.ITEM_STAFF.value, TileType.ITEM_KEY_RUSTY_2.value, TileType.ITEM_STAMINA_POTION.value]:
        return (255, 200, 50)  # Gold/yellow for items
    elif tile_type in [TileType.DOOR.value, TileType.DOOR_SILVER.value, TileType.DOOR_GOLD.value]:
        return (150, 100, 50)  # Brown for doors
    elif tile_type == TileType.PLAYER_SPAWN.value:
        return (50, 150, 255)  # Blue for player spawn
    elif tile_type == TileType.ENEMY_GHOST.value:
        return (255, 0, 0)  # Red for enemies
    elif tile_type == TileType.STAIRS.value:
        return (200, 100, 255)  # Purple for stairs
    else:
        return (50, 50, 50)  # Default dark gray

class Game:
    def __init__(self):
        pygame.init()
        pygame.mouse.set_visible(False) 
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("RPGW3D Engine")
        self.clock = pygame.time.Clock()

        # Initialize map early
        self.map = [[TileType.EMPTY.value for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
        
        self.font = pygame.font.SysFont("georgia", 16) 
        self.font_msg = pygame.font.SysFont("georgia", 20, bold=True)
        self.font_small_bold = pygame.font.SysFont("georgia", 14, bold=True)
        self.font_massive = pygame.font.SysFont("georgia", 60, bold=True)
        self.font_massive_win = pygame.font.SysFont("georgia", 50, bold=True)
        
        self.game_over_overlay = pygame.Surface((WIDTH, HEIGHT))
        self.game_over_overlay.set_alpha(200)
        self.game_over_overlay.fill((100, 0, 0))
        
        self.level_complete_overlay = pygame.Surface((WIDTH, HEIGHT))
        self.level_complete_overlay.set_alpha(180)
        self.level_complete_overlay.fill((0, 0, 0))
        
        # Stat system
        self.stat_points = 5
        self.strength = 10
        self.intelligence = 10
        self.endurance = 10
        self.show_stat_screen = False
        
        # Initialize stats
        self.recalculate_max_stats()
        self.health = self.max_health
        self.mana = self.max_mana
        self.stamina = self.max_stamina
        
        # Player position and rotation
        self.player_x = 24.0
        self.player_y = 24.0
        self.player_angle = 0.0
        
        # Create icon and sfx dictionaries for Inventory
        icons_dict = {
            "sword": load_image_safe("Sword_Icon.png"), 
            "key": load_image_safe("Key_Icon.png"), 
            "key_silver": load_image_safe("key_silver.png"), 
            "key_gold": load_image_safe("key_gold.png"),
            "key_dungeon": load_image_safe("rusty_key_to_dungeon.png"), 
            "health_potion": load_image_safe("health_potion.png"), 
            "mana_potion": load_image_safe("mana_potion.png"),
            "artifact": load_image_safe("artifact.png"), 
            "unlit_torch": None, 
            "lit_torch": None, 
            "staff": None
        }
        
        sfx_dict = {
            "door": SFX_DOOR,
            "pickup": SFX_PICKUP,
            "use": SFX_USE,
            "drink": SFX_DRINK
        }
        
        # Inventory and UI
        self.inventory = Inventory(icons_dict, sfx_dict)
        self.action_bar = ActionBar({})
        
        # Game state
        self.game_over = False
        self.level_complete = False
        self.current_level = 1
        
        # Raycasting surface
        self.raycasting_surface = pygame.Surface((WIDTH, HEIGHT))
        
        # Shadow system
        self.time_of_day = 0.0  # 0-1, where 0.5 is noon (sun at top)
        self.sun_angle = 0.0  # Direction of sun (radians)
        self.shadow_length = 2.0  # How far shadows extend
        
        # Load textures
        self.wall_texture = load_image_safe(WALL_TEXTURE_PATH)
        self.floor_dirt_texture = load_image_safe(FLOOR_DIRT_PATH)
        self.floor_grass_texture = load_image_safe(FLOOR_GRASS_PATH)
        
        # Weather system
        self.weather_type = 'none'
        self.weather_time = 0
        self.weather_particles = []
        self.weather_duration = 0
        self.next_weather_time = random.randint(2000, 4000)

    def get_initial_map_data(self):
        """Load map from JSON or create default bordered map"""
        default_map = [[TileType.EMPTY.value for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
        for i in range(MAP_SIZE):
            default_map[0][i] = default_map[MAP_SIZE-1][i] = default_map[i][0] = default_map[i][MAP_SIZE-1] = TileType.WALL_BRICK.value
        
        try:
            map_file = MAP_DATA_FILE if self.current_level == 1 else f"map_level_{self.current_level}.json"
            if os.path.exists(map_file):
                with open(map_file, "r") as f:
                    data = json.load(f)
                    # Handle both dict and list formats
                    if isinstance(data, dict):
                        map_data = data.get('map', default_map)
                    else:
                        map_data = data
                    
                    # Verify dimensions
                    if len(map_data) == MAP_SIZE and len(map_data[0]) == MAP_SIZE:
                        print(f"Map successfully loaded from {map_file}.")
                        return map_data
                    else:
                        print("Map data size mismatch! Falling back to default map.")
        except Exception as e:
            print(f"Failed to load map data: {e}")
            
        return default_map

    def recalculate_max_stats(self):
        """Recalculate max stats based on attributes"""
        self.max_health = 50 + (self.endurance * 5)
        self.max_mana = 20 + (self.intelligence * 3)
        self.max_stamina = 50 + (self.endurance * 5)
        self.melee_dmg = 20 + int(self.strength * 1.5)
        self.magic_dmg = 25 + int(self.intelligence * 2.0)

    def is_walkable(self, x, y):
        """Check if a tile is walkable"""
        grid_x = int(x)
        grid_y = int(y)
        
        if not (0 <= grid_x < MAP_SIZE and 0 <= grid_y < MAP_SIZE):
            return False
        
        tile = self.map[grid_y][grid_x]
        
        # Walls and obstacles are not walkable
        non_walkable = [
            TileType.WALL_BRICK.value, TileType.WALL_STONE.value, TileType.WALL_WOOD.value,
            TileType.WALL_BRICK_CRACKED.value, TileType.WALL_STONE_CRACKED.value, 
            TileType.WALL_WOOD_CRACKED.value, TileType.TREE.value, TileType.DEAD_TREE.value,
            TileType.BUSH.value, TileType.ROCK.value, TileType.FORCE_FIELD.value
        ]
        
        return tile not in non_walkable

    def handle_player_movement(self, keys):
        """Handle player movement based on key input"""
        old_x, old_y = self.player_x, self.player_y
        move_speed = PLAYER_SPEED
        
        # Get Alt key state
        mods = pygame.key.get_mods()
        alt_held = mods & pygame.KMOD_ALT
        
        # Forward/Backward movement
        if keys[pygame.K_w]:
            new_x = self.player_x + math.cos(self.player_angle) * move_speed
            new_y = self.player_y + math.sin(self.player_angle) * move_speed
            if self.is_walkable(new_x, new_y):
                self.player_x = new_x
                self.player_y = new_y
        
        if keys[pygame.K_s]:
            new_x = self.player_x - math.cos(self.player_angle) * move_speed
            new_y = self.player_y - math.sin(self.player_angle) * move_speed
            if self.is_walkable(new_x, new_y):
                self.player_x = new_x
                self.player_y = new_y
        
        # A and D keys - strafe with Alt, turn without Alt
        if keys[pygame.K_a]:
            if alt_held:
                # Strafe left with Alt+A
                new_x = self.player_x + math.cos(self.player_angle - math.pi / 2) * move_speed
                new_y = self.player_y + math.sin(self.player_angle - math.pi / 2) * move_speed
                if self.is_walkable(new_x, new_y):
                    self.player_x = new_x
                    self.player_y = new_y
            else:
                # Turn left with A
                self.player_angle -= PLAYER_ROTATION_SPEED
        
        if keys[pygame.K_d]:
            if alt_held:
                # Strafe right with Alt+D
                new_x = self.player_x + math.cos(self.player_angle + math.pi / 2) * move_speed
                new_y = self.player_y + math.sin(self.player_angle + math.pi / 2) * move_speed
                if self.is_walkable(new_x, new_y):
                    self.player_x = new_x
                    self.player_y = new_y
            else:
                # Turn right with D
                self.player_angle += PLAYER_ROTATION_SPEED

    def update_sun_position(self):
        """Update sun position based on time of day"""
        self.time_of_day += 0.0005  # Slow progression through day
        if self.time_of_day >= 1.0:
            self.time_of_day = 0.0
        
        # Sun moves in a circle: 0.0 = east, 0.25 = north, 0.5 = west, 0.75 = south
        self.sun_angle = self.time_of_day * 2 * math.pi

    def update_weather(self):
        """Update weather system"""
        self.weather_time += 1
        
        # Transition to new weather
        if self.weather_time >= self.next_weather_time:
            self.weather_type = random.choice(WEATHER_TYPES)
            min_dur, max_dur = WEATHER_TRANSITIONS[self.weather_type]
            self.weather_duration = random.randint(min_dur, max_dur)
            self.weather_time = 0
            self.next_weather_time = random.randint(int(min_dur * 0.5), int(max_dur * 1.5))
            self.weather_particles = []
        
        # Generate particles
        particle_count = WEATHER_INTENSITY[self.weather_type].get('count', 0)
        while len(self.weather_particles) < particle_count:
            x = random.randint(0, WIDTH)
            y = random.randint(-50, HEIGHT)
            self.weather_particles.append([x, y])
        
        # Update particle positions
        for particle in self.weather_particles[:]:
            if self.weather_type in ['rain', 'rain_heavy']:
                particle[1] += random.randint(5, 10)
                particle[0] += random.randint(-2, 2)
            elif self.weather_type == 'snow':
                particle[1] += random.randint(1, 3)
                particle[0] += random.randint(-1, 1)
            elif self.weather_type == 'sand':
                particle[1] += random.randint(2, 5)
                particle[0] += random.randint(2, 5)
            
            if particle[1] > HEIGHT:
                self.weather_particles.remove(particle)

    def get_shadow_offset(self, depth, angle_to_player):
        """Calculate shadow offset based on wall distance and sun angle"""
        # Shadow direction is opposite to sun
        shadow_direction = self.sun_angle + math.pi
        
        # Shadow length decreases with distance (closer walls = longer shadows)
        shadow_dist = max(0, (1.0 - (depth / MAX_DEPTH)) * self.shadow_length)
        
        # Calculate shadow offset
        shadow_x = math.cos(shadow_direction) * shadow_dist
        shadow_y = math.sin(shadow_direction) * shadow_dist
        
        return shadow_x, shadow_y

    def cast_ray(self, angle):
        """Cast a single ray and return the distance to the nearest wall"""
        sin_a = math.sin(angle)
        cos_a = math.cos(angle)
        
        for depth in range(1, MAX_DEPTH):
            target_x = self.player_x + cos_a * depth
            target_y = self.player_y + sin_a * depth
            
            col = int(target_x / TILE_SIZE)
            row = int(target_y / TILE_SIZE)
            
            if col < 0 or col >= MAP_SIZE or row < 0 or row >= MAP_SIZE:
                return depth
            
            # Check for walls
            tile = self.map[row][col]
            if tile in [TileType.WALL_BRICK.value, TileType.WALL_STONE.value, TileType.WALL_WOOD.value,
                       TileType.WALL_BRICK_CRACKED.value, TileType.WALL_STONE_CRACKED.value,
                       TileType.WALL_WOOD_CRACKED.value]:
                return depth
        
        return MAX_DEPTH

    def get_sun_brightness(self):
        """Get brightness multiplier based on sun position (0.3 - 1.0)"""
        # Sun is brightest at noon (time_of_day = 0.5)
        sun_height = math.sin(self.time_of_day * math.pi)  # 0 at dawn/dusk, 1 at noon
        return 0.3 + sun_height * 0.7  # Range: 0.3 to 1.0

    def render_3d_view(self):
        """Render the 3D first-person view using raycasting with textures and shadows"""
        self.raycasting_surface.fill((50, 50, 60))  # Sky/ceiling color
        
        # Draw floor
        pygame.draw.rect(self.raycasting_surface, (40, 50, 40), (0, HEIGHT // 2, WIDTH, HEIGHT // 2))
        
        # Get sun brightness for this frame
        sun_brightness = self.get_sun_brightness()
        
        # Cast rays for each column
        for i in range(NUM_RAYS):
            angle = self.player_angle - (FOV / 2) + (i * DELTA_ANGLE)
            depth = self.cast_ray(angle)
            
            # Correct for fisheye effect
            depth = depth * math.cos(angle - self.player_angle)
            
            # Calculate wall height
            if depth > 0:
                wall_height = min(int((WALL_HEIGHT_MULTIPLIER / depth)), HEIGHT)
            else:
                wall_height = HEIGHT
            
            # Draw wall slice
            col_width = WIDTH // NUM_RAYS
            x = i * col_width
            
            # Calculate shadow darkness based on sun angle relative to wall
            wall_normal = (angle + math.pi / 2)
            sun_alignment = math.cos(wall_normal - self.sun_angle)
            
            # Shadow intensity
            shadow_intensity = max(0, -sun_alignment)
            
            # Base shade from distance
            distance_shade = max(50, 255 - (depth / MAX_DEPTH) * 200)
            
            # Apply shadow
            shadow_factor = 1.0 - (shadow_intensity * 0.5)
            final_shade = distance_shade * shadow_factor * sun_brightness
            final_shade = max(20, min(255, final_shade))
            
            # Apply texture if available
            if self.wall_texture:
                # Get texture pixel based on position and depth
                tex_x = int((self.player_x + math.cos(angle) * depth) * 10) % self.wall_texture.get_width()
                tex_y = int(depth * 2) % self.wall_texture.get_height()
                try:
                    tex_color = self.wall_texture.get_at((tex_x, tex_y))
                    color = tuple(int(c * final_shade / 255) for c in tex_color[:3])
                except:
                    color = (final_shade, final_shade * 0.7, final_shade * 0.5)
            else:
                color = (final_shade, final_shade * 0.7, final_shade * 0.5)
            
            rect = pygame.Rect(x, (HEIGHT - wall_height) // 2, col_width, wall_height)
            pygame.draw.rect(self.raycasting_surface, color, rect)
        
        self.screen.blit(self.raycasting_surface, (0, 0))

    def render_weather(self):
        """Render weather particles"""
        if self.weather_type == 'none':
            return
        
        if self.weather_type in ['rain', 'rain_heavy']:
            color = RAIN_COLOR
            for particle in self.weather_particles:
                pygame.draw.line(self.screen, color, (particle[0], particle[1]), (particle[0], particle[1] + 5), 1)
        elif self.weather_type == 'snow':
            color = SNOW_COLOR
            for particle in self.weather_particles:
                pygame.draw.circle(self.screen, color, (int(particle[0]), int(particle[1])), 2)
        elif self.weather_type == 'sand':
            color = DUST_COLOR
            for particle in self.weather_particles:
                pygame.draw.circle(self.screen, color, (int(particle[0]), int(particle[1])), 1)

    def render_minimap(self):
        """Render minimap in top-right corner"""
        minimap_size = 150  # Size of minimap on screen
        minimap_tile_size = minimap_size // MAP_SIZE
        minimap_x = WIDTH - minimap_size - 10
        minimap_y = 10
        
        # Draw minimap background
        pygame.draw.rect(self.screen, (20, 20, 20), (minimap_x, minimap_y, minimap_size, minimap_size))
        pygame.draw.rect(self.screen, (200, 180, 100), (minimap_x, minimap_y, minimap_size, minimap_size), 2)
        
        # Draw map tiles
        for y in range(MAP_SIZE):
            for x in range(MAP_SIZE):
                tile_type = self.map[y][x]
                tile_color = get_tile_color(tile_type)
                
                rect = pygame.Rect(
                    minimap_x + x * minimap_tile_size,
                    minimap_y + y * minimap_tile_size,
                    minimap_tile_size,
                    minimap_tile_size
                )
                pygame.draw.rect(self.screen, tile_color, rect)
        
        # Draw player position on minimap
        player_minimap_x = int((self.player_x / TILE_SIZE) * minimap_tile_size)
        player_minimap_y = int((self.player_y / TILE_SIZE) * minimap_tile_size)
        player_pos = (minimap_x + player_minimap_x, minimap_y + player_minimap_y)
        pygame.draw.circle(self.screen, (255, 255, 255), player_pos, 3)
   
        # Draw sun direction indicator on minimap
        sun_x = minimap_x + int(math.cos(self.sun_angle) * 40)
        sun_y = minimap_y + int(math.sin(self.sun_angle) * 40)
        pygame.draw.circle(self.screen, (255, 255, 0), (sun_x, sun_y), 4)

    def render_hud(self):
        """Render HUD with styled bars and stats"""
        hud_x = 10
        hud_y = 10
        bar_width = 330
        bar_height = 60
        spacing = 5
        
        # HUD Background panel
        hud_panel = pygame.Rect(hud_x - 5, hud_y - 5, bar_width + 10, (bar_height + spacing) * 5)

        pygame.draw.rect(self.screen, (30, 30, 35), hud_panel)
        pygame.draw.rect(self.screen, (200, 180, 100), hud_panel, 3)  # Gold border
        
        # Health Bar
        health_text = self.font_small_bold.render(f"HP: {int(self.health)}/{int(self.max_health)}", True, (255, 50, 50))
        self.screen.blit(health_text, (hud_x + 5, hud_y + 5))
        
        health_bar_rect = pygame.Rect(hud_x, hud_y + 25, bar_width, bar_height)
        pygame.draw.rect(self.screen, (50, 0, 0), health_bar_rect)
        health_fill = bar_width * (self.health / self.max_health)
        pygame.draw.rect(self.screen, (255, 50, 50), (hud_x, hud_y + 25, health_fill, bar_height))
        pygame.draw.rect(self.screen, (200, 180, 100), health_bar_rect, 2)  # Gold border
        
        # Mana Bar
        mana_y = hud_y + bar_height + spacing + 30
        mana_text = self.font_small_bold.render(f"Mana: {int(self.mana)}/{int(self.max_mana)}", True, (50, 150, 255))
        self.screen.blit(mana_text, (hud_x + 5, mana_y - 20))
        
        mana_bar_rect = pygame.Rect(hud_x, mana_y, bar_width, bar_height)
        pygame.draw.rect(self.screen, (0, 50, 100), mana_bar_rect)
        mana_fill = bar_width * (self.mana / self.max_mana)
        pygame.draw.rect(self.screen, (50, 100, 255), (hud_x, mana_y, mana_fill, bar_height))
        pygame.draw.rect(self.screen, (200, 180, 100), mana_bar_rect, 2)  # Gold border
        
        # Stamina Bar
        stamina_y = mana_y + bar_height + spacing
        stamina_text = self.font_small_bold.render(f"Stamina: {int(self.stamina)}/{int(self.max_stamina)}", True, (100, 255, 100))
        self.screen.blit(stamina_text, (hud_x + 5, stamina_y))
        
        stamina_bar_rect = pygame.Rect(hud_x, stamina_y + 20, bar_width, bar_height)
        pygame.draw.rect(self.screen, (0, 50, 0), stamina_bar_rect)
        stamina_fill = bar_width * (self.stamina / self.max_stamina)
        pygame.draw.rect(self.screen, (100, 255, 100), (hud_x, stamina_y + 20, stamina_fill, bar_height))
        pygame.draw.rect(self.screen, (200, 180, 100), stamina_bar_rect, 2)  # Gold border
        
        # Level info
        level_y = stamina_y + 45
        level_text = self.font_small_bold.render(f"LVL: {self.current_level}", True, (255, 255, 100))
        self.screen.blit(level_text, (hud_x + 5, level_y))
        
        # Time of day display
        hour = int(self.time_of_day * 24)
        time_text = self.font.render(f"Time: {hour:02d}:00", True, (200, 200, 200))
        self.screen.blit(time_text, (hud_x + 5, level_y + 25))
        
        # Weather indicator
        weather_text = self.font.render(f"Weather: {self.weather_type.upper()}", True, (150, 200, 255))
        self.screen.blit(weather_text, (hud_x + 5, level_y + 50))

    def render_ui(self):
        """Render UI elements"""
        # Render minimap
        self.render_minimap()
        
        # Render HUD
        self.render_hud()
        
        # Action bar
        self.action_bar.draw(self.screen)
        
        # Inventory
        mouse_pos = pygame.mouse.get_pos()
        self.inventory.draw(self.screen, mouse_pos, self.font)

    def render_stat_screen(self):
        """Render the stat allocation screen"""
        self.screen.fill((20, 20, 25))
        
        title = self.font_massive.render("CHARACTER STATS", True, (255, 215, 0))
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
        
        y_pos = 150
        stat_color = (100, 200, 255)
        
        # Display stats and available points
        stats = [
            ("Strength", self.strength),
            ("Intelligence", self.intelligence),
            ("Endurance", self.endurance),
        ]
        
        for stat_name, stat_val in stats:
            text = self.font_msg.render(f"{stat_name}: {stat_val}", True, stat_color)
            self.screen.blit(text, (WIDTH // 2 - 150, y_pos))
            y_pos += 40
        
        # Display derived stats
        y_pos += 20
        derived_color = (200, 150, 100)
        derived = [
            (f"Max Health: {self.max_health}", derived_color),
            (f"Max Mana: {self.max_mana}", derived_color),
            (f"Melee Damage: {self.melee_dmg}", derived_color),
            (f"Magic Damage: {self.magic_dmg}", derived_color),
        ]
        
        for text_str, color in derived:
            text = self.font.render(text_str, True, color)
            self.screen.blit(text, (WIDTH // 2 - 150, y_pos))
            y_pos += 30
        
        # Available points
        points_text = self.font_msg.render(f"Points Available: {self.stat_points}", True, (0, 255, 100))
        self.screen.blit(points_text, (WIDTH // 2 - points_text.get_width() // 2, HEIGHT - 100))
        
        # Instructions
        instr = self.font.render("Press I for Inventory | Press C to close | Press ESC to quit", True, (150, 150, 150))
        self.screen.blit(instr, (WIDTH // 2 - instr.get_width() // 2, HEIGHT - 40))

    def check_item_pickup(self):
        """Check if player is on an item and pick it up"""
        tile_x = int(self.player_x / TILE_SIZE)
        tile_y = int(self.player_y / TILE_SIZE)
        
        if 0 <= tile_x < MAP_SIZE and 0 <= tile_y < MAP_SIZE:
            tile = self.map[tile_y][tile_x]
            
            if tile == TileType.ITEM_DAGGER.value:
                self.inventory.add_item("Dagger", 1, "weapon", "A sharp blade", health=0, mana=0)
                self.map[tile_y][tile_x] = TileType.EMPTY.value
                if SFX_PICKUP: SFX_PICKUP.play()
            elif tile == TileType.ITEM_HEALTH_POTION.value:
                self.health = min(self.health + 25, self.max_health)
                self.map[tile_y][tile_x] = TileType.EMPTY.value
                if SFX_DRINK: SFX_DRINK.play()
            elif tile == TileType.ITEM_FOOD.value:
                self.stamina = min(self.stamina + 20, self.max_stamina)
                self.map[tile_y][tile_x] = TileType.EMPTY.value
                if SFX_DRINK: SFX_DRINK.play()
            elif tile == TileType.STAIRS.value:
                self.level_complete = True

    def run(self):
        """Main game loop"""
        # Load map
        self.map = self.get_initial_map_data()
        self.fog_of_war = [[False for _ in range(len(self.map[0]))] for _ in range(len(self.map))]
        self.minimap_reveal_radius = 8
        self.minimap_x, self.minimap_y, self.minimap_size = WIDTH - 150, 20, 140

        # Find player spawn point
        for y in range(MAP_SIZE):
            for x in range(MAP_SIZE):
                if self.map[y][x] == TileType.PLAYER_SPAWN.value:
                    self.player_x = x * TILE_SIZE + TILE_SIZE // 2
                    self.player_y = y * TILE_SIZE + TILE_SIZE // 2
                    break
        
        running = True
        while running:
            # Event handling
            for e in pygame.event.get():
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                    return
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_c:
                        self.show_stat_screen = not self.show_stat_screen
                    elif e.key == pygame.K_i:  # INVENTORY HOTKEY
                        self.inventory.toggle()
            
            # Stat screen
            if self.show_stat_screen:
                self.render_stat_screen()
                pygame.display.flip()
                self.clock.tick(FPS)
                continue
            
            # Game over screen
            if self.game_over:
                self.screen.blit(self.game_over_overlay, (0, 0))
                game_over_text = self.font_massive.render("YOU DIED", True, (255, 0, 0))
                self.screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 50))
                restart_text = self.font.render("Press R to restart or ESC to quit", True, (200, 200, 200))
                self.screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 50))
                pygame.display.flip()
                
                for e in pygame.event.get():
                    if e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_r:
                            self.game_over = False
                            self.health = self.max_health
                            self.run()  # Restart
                            return
                        elif e.key == pygame.K_ESCAPE:
                            return
                
                self.clock.tick(FPS)
                continue
            
            # Level complete screen
            if self.level_complete:
                self.screen.blit(self.level_complete_overlay, (0, 0))
                complete_text = self.font_massive_win.render("LEVEL COMPLETE!", True, (0, 255, 100))
                self.screen.blit(complete_text, (WIDTH // 2 - complete_text.get_width() // 2, HEIGHT // 2 - 50))
                next_text = self.font.render("Press SPACE to continue or ESC to quit", True, (200, 200, 200))
                self.screen.blit(next_text, (WIDTH // 2 - next_text.get_width() // 2, HEIGHT // 2 + 50))
                pygame.display.flip()
                
                for e in pygame.event.get():
                    if e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_SPACE:
                            self.level_complete = False
                            self.current_level += 1
                            self.map = self.get_initial_map_data()
                        elif e.key == pygame.K_ESCAPE:
                            return
                
                self.clock.tick(FPS)
                continue
            
            # Normal gameplay
            keys = pygame.key.get_pressed()
            self.handle_player_movement(keys)
            self.check_item_pickup()
            
            # Update sun position
            self.update_sun_position()
            
            # Update weather
            self.update_weather()
            
            # Render
            self.render_3d_view()
            self.render_weather()
            self.render_ui()
            
            # Natural health/mana/stamina decay
            if self.stamina > 0:
                self.stamina = min(self.stamina + 0.05, self.max_stamina)
            if self.mana > 0:
                self.mana = min(self.mana + 0.1, self.max_mana)
            
            pygame.display.flip()
            self.clock.tick(FPS)
