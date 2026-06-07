import pygame
import math
import random
import json
import os
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

class Game:
    def __init__(self):
        pygame.init()
        pygame.mouse.set_visible(False) 
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("RPGW3D Engine")
        self.clock = pygame.time.Clock()
        
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
        
        self.stat_points = 5
        self.strength = 10
        self.intelligence = 10
        self.endurance = 10
        self.show_stat_screen = True 

        self.sfx = {
            "pickup": SFX_PICKUP, "door": SFX_DOOR, "error": SFX_ERROR, "use": SFX_USE,
            "fireball": SFX_FIREBALL, "drink": SFX_DRINK, "torch": SFX_TORCH,
            "hit_metallic": SFX_HIT_METALLIC
        }
        
        self.current_bgm = "bgm.mp3"
        self.next_bgm = None
        self.bgm_fade_timer = 0
        if MIXER_READY:
            try:
                pygame.mixer.music.load(self.current_bgm) 
                pygame.mixer.music.set_volume(0.15) 
                pygame.mixer.music.play(-1)
            except: pass
        
        self.ui_icons = {
            "key": self.load_sprite_image(KEY_PATH, scale=True, size=(40, 40), fallback="none"),
            "key_silver": self.load_sprite_image(KEY_SILVER_PATH, scale=True, size=(40, 40), fallback="none"),
            "key_gold": self.load_sprite_image(KEY_GOLD_PATH, scale=True, size=(40, 40), fallback="none"),
            "key_dungeon": self.load_sprite_image(RUSTY_KEY_PATH, scale=True, size=(40, 40), fallback="none"),
            "key_rusty_2": self.load_sprite_image(RUSTY_KEY_2_PATH, scale=True, size=(40, 40), fallback="none"),
            "sword": self.load_sprite_image(SWORD_PATH, scale=True, size=(40, 40), fallback="none"),
            "health_potion": self.load_sprite_image(HEALTH_POTION_PATH, scale=True, size=(40, 40), fallback="food"),
            "mana_potion": self.load_sprite_image(MANA_POTION_PATH, scale=True, size=(40, 40), fallback="food"),
            "stamina_potion": self.load_sprite_image(STAMINA_POTION_PATH, scale=True, size=(40, 40), fallback="food"),
            "artifact": self.load_sprite_image(ARTIFACT_PATH, scale=True, size=(40, 40), fallback="artifact"),
            "fireball": self.load_sprite_image(FIREBALL_PATH, scale=True, size=(40, 40), fallback="artifact"),
            "unlit_torch": self.load_sprite_image("unlit_torch.png", scale=True, size=(40, 40), fallback="unlit_torch"),
            "lit_torch": self.load_sprite_image("lit_torch.png", scale=True, size=(40, 40), fallback="lit_torch"),
            "staff": self.load_sprite_image("staff.png", scale=True, size=(40, 40), fallback="artifact"),
            "spell_heal": self.load_sprite_image("heal_icon.png", scale=True, size=(40, 40), fallback="food"),
            "spell_frost": self.load_sprite_image(ARTIFACT_PATH, scale=True, size=(40, 40), fallback="artifact")
        }
        
        self.drop_key_rusty_2_sprite = self.load_sprite_image(RUSTY_KEY_2_PATH, fallback="none")
        self.enemy_sprite = self.load_sprite_image("ghost_enemy_1.png", fallback="enemy")

    def cache_tree_positions(self):
        self.tree_positions = []
        for y, row in enumerate(self.map):
            for x, tile in enumerate(row):
                if tile == TileType.TREE.value: 
                    self.tree_positions.append((x * TILE_SIZE, y * TILE_SIZE))

    def find_tree_positions(self):
        self.tree_positions = []
        for y, row in enumerate(self.map):
            for x, tile in enumerate(row):
                if tile == TileType.TREE.value:
                    self.tree_positions.append((x * TILE_SIZE, y * TILE_SIZE))

        # --- FEATURE: Boss Animation System! ---
        self.boss_idle_frames = []
        self.boss_attack_frames = []

        def clean_sprite_sheet(sheet):
            for x in range(sheet.get_width()):
                for y in range(sheet.get_height()):
                    r, g, b, a = sheet.get_at((x, y))
                    if r > 100 and g > 100 and b > 100 and abs(r-g) < 30 and abs(g-b) < 30:
                        sheet.set_at((x, y), (0, 0, 0, 0))
                    elif r > 100 and b > 100 and g < r - 30:
                        sheet.set_at((x, y), (0, 0, 0, 0))
            return sheet

        try:
            idle_sheet = pygame.image.load("boss_idle.png").convert_alpha()
            idle_sheet = clean_sprite_sheet(idle_sheet)
            w = idle_sheet.get_width() // 10  
            h = idle_sheet.get_height()
            
            crop_w, crop_h = w - 50, h - 16
            for i in range(10):               
                surf = pygame.Surface((crop_w, crop_h), pygame.SRCALPHA)
                surf.blit(idle_sheet, (0, 0), (i * w + 25, 8, crop_w, crop_h))
                self.boss_idle_frames.append(surf)
        except Exception as e:
            fallback_img = self.load_sprite_image("FlameDemon Evolved.png", fallback="enemy")
            if fallback_img: fallback_img = clean_sprite_sheet(fallback_img)
            self.boss_idle_frames = [fallback_img]
            
        try:
            atk_sheet = pygame.image.load("boss_attack.png").convert_alpha()
            atk_sheet = clean_sprite_sheet(atk_sheet)
            w = atk_sheet.get_width() // 6
            h = atk_sheet.get_height()
            
            crop_w, crop_h = w - 50, h - 16
            for i in range(6):
                surf = pygame.Surface((crop_w, crop_h), pygame.SRCALPHA)
                surf.blit(atk_sheet, (0, 0), (i * w + 25, 8, crop_w, crop_h))
                self.boss_attack_frames.append(surf)
        except:
            self.boss_attack_frames = self.boss_idle_frames
            
        self.boss_sprite = self.boss_idle_frames[0]
        
        self.inventory = Inventory(self.ui_icons, self.sfx)
        self.action_bar = ActionBar(self.ui_icons)
        
        self.drag_item = None
        self.drag_source = None 
        self.projectiles = [] 
        self.sparks = [] 
        
        self.door_tex = self.load_door_texture() 
        self.door_silver_tex = self.door_tex.copy(); self.door_silver_tex.fill((100, 100, 100), special_flags=pygame.BLEND_RGB_ADD)
        self.door_gold_tex = self.door_tex.copy(); self.door_gold_tex.fill((100, 80, 0), special_flags=pygame.BLEND_RGB_ADD)

        self.wall_textures = self.load_all_wall_textures()
        self.floor_textures = self.load_all_floor_textures()
        self.floor_tex = self.floor_textures[FloorTextureType.DIRT.name]
        
        self.tree_leafy_sprites = [self.load_sprite_image(p, fallback="tree") for p in TREE_LEAFY_PATHS]
        self.bush_sprites = [self.load_sprite_image(p, fallback="bush") for p in BUSH_PATHS]
        self.leaf_base_sprite = self.load_sprite_image(LEAF_SPRITE_PATH, scale=False, fallback="none")
        self.leaf_cache = {} 
        
        self.tree_dead_sprite = self.load_sprite_image(TREE_DEAD_PATH, fallback="dead")
        self.rock_sprite = self.load_sprite_image(ROCK_PATH, fallback="rock")
        self.torch_sprite = self.load_sprite_image("standing_torch.png", fallback="lit_torch")
        self.overworld_spawn_pos = None 
        
        self.drop_sword_sprite = self.load_sprite_image(SWORD_PATH, fallback="none")
        self.drop_key_sprite = self.load_sprite_image(KEY_PATH, fallback="none")
        self.drop_key_silver_sprite = self.load_sprite_image(KEY_SILVER_PATH, fallback="none")
        self.drop_key_gold_sprite = self.load_sprite_image(KEY_GOLD_PATH, fallback="none")
        self.drop_food_sprite = self.load_sprite_image(MANA_POTION_PATH, fallback="food")
        self.drop_health_sprite = self.load_sprite_image(HEALTH_POTION_PATH, fallback="food")
        self.drop_stamina_sprite = self.load_sprite_image(STAMINA_POTION_PATH, fallback="food")
        self.drop_artifact_sprite = self.load_sprite_image(ARTIFACT_PATH, fallback="artifact")
        
        self.weapon_idle_img = self.load_hud_weapon("Sword_In_Hand.png")
        
        self.cloud_sprite = self.load_cloud_sprite()
        self.cloud_sprites_cache = {}  
        self.clouds = self.generate_parallax_clouds()
        
        self.wind_effect = 0.0
        self.global_wind = 0.0
        self.weather_type = 'none'
        self.weather_target = 'none'
        self.weather_timer = 0
        self.weather_duration = random.randint(*WEATHER_TRANSITIONS.get('none', (2000, 4000))) 
        self.weather_intensity = 0.0 
        self.particles = []

        self.cache_tree_positions() 
        
        self.leaves = []
        
        self.global_flicker = 1.0
        self.consume_message = ""; self.consume_message_timer = 0
        self.level_complete = False
        self.level_complete_timer = 0
        self.depth_buffer = [MAX_DEPTH] * NUM_RAYS
        
        self.level = 1          
        self.map_level = 1      
        self.xp = 0             
        self.xp_to_next_level = 100 
        
        self.recalculate_max_stats()
        self.health = self.max_health
        self.mana = self.max_mana
        self.stamina = self.max_stamina
        
        self.player_speed_mod = 1.0
        self.floor_texture_type = FloorTextureType.DIRT
        
        self.exterior_map, self.exterior_items, self.exterior_enemies = self.load_or_generate_map()
        int_raw, int_items, _ = self.extract_map_entities(self.generate_dungeon_layout())
        self.interior_map = int_raw
        self.interior_items = int_items
        self.interior_enemies = self.spawn_enemies(self.interior_map, 6) 
        
        self.map = self.exterior_map
        self.world_items = self.exterior_items
        self.enemies = self.exterior_enemies
        
        if self.overworld_spawn_pos is not None:
            self.player_x, self.player_y = self.overworld_spawn_pos
        else:
            self.player_x, self.player_y = self.get_safe_spawn()

        self.player_angle = 0
        self.attack_swing = 0.0 
        self.time = 600.0 
        self.ambient_light = 255
        self.sky_keyframes = {0: (5, 5, 15), 400: (10, 10, 30), 600: (255, 120, 70), 800: (135, 206, 235), 1200: (100, 180, 255), 1600: (135, 206, 235), 1800: (200, 60, 30), 2000: (20, 15, 40), 2400: (5, 5, 15)}
        
        self.in_combat = False
        self.game_over = False
        self.game_over_timer = 0
        self.torch_timer = 0
        
        self.in_interior = False
        self.exterior_spawn = (128, 128)  
        
        self.load_game_state()
        
        if self.in_interior:
            self.map = self.interior_map
            self.world_items = self.interior_items
            self.enemies = self.interior_enemies
        else:
            self.map = self.exterior_map
            self.world_items = self.exterior_items
            self.enemies = self.exterior_enemies
            
        self.doors = []
        self.world_torches = []
        
        self.hovered_interactable = None
        self.hovered_rect = None
        self.stat_btn_rects = []
        
        self.build_lightmap()
        self.build_interactables() 
        
        self.fog_of_war = [[False for _ in range(len(self.map[0]))] for _ in range(len(self.map))]
        self.minimap_reveal_radius = 8
        self.minimap_x, self.minimap_y, self.minimap_size = WIDTH - 150, 20, 140

    def recalculate_max_stats(self):
        self.max_health = 50 + (self.endurance * 5)
        self.max_mana = 20 + (self.intelligence * 3)
        self.max_stamina = 50 + (self.endurance * 5)
        self.melee_dmg = 20 + int(self.strength * 1.5)
        self.magic_dmg = 25 + int(self.intelligence * 2.0)

    def use_specific_door(self, door):
        req_key = door.get("key_required")
        if req_key:
            inv_idx, item = self.inventory.find_item_by_name(req_key)
            if item and item["qty"] > 0:
                if self.sfx.get("door"): self.sfx["door"].play()
                self.consume_message = f"Unlocked with {req_key}!"
                self.consume_message_timer = 60
                item["qty"] -= 1
                if item["qty"] <= 0: self.inventory.slots[inv_idx] = None
                self.map[door["gy"]][door["gx"]] = TileType.EMPTY.value
                self.doors.remove(door)
                self.save_game_state()
            else:
                if self.sfx.get("error"): self.sfx["error"].play()
                self.consume_message = f"Requires {req_key}!"
                self.consume_message_timer = 60
        else:
            if self.sfx.get("door"): self.sfx["door"].play()
            self.map[door["gy"]][door["gx"]] = TileType.EMPTY.value
            self.doors.remove(door)
            self.save_game_state()

    def pad_map(self, raw_map):
        new_map = [[TileType.EMPTY.value for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
        for y in range(min(MAP_SIZE, len(raw_map))):
            for x in range(min(MAP_SIZE, len(raw_map[y]))):
                new_map[y][x] = raw_map[y][x]
        return new_map

    def save_game_state(self):
        ext_enemies_clean = [{k: v for k, v in e.items() if k != 'tex' and k != 'ref'} for e in self.exterior_enemies]
        int_enemies_clean = [{k: v for k, v in e.items() if k != 'tex' and k != 'ref'} for e in self.interior_enemies]
        
        state = {
            "health": self.health, "max_health": self.max_health,
            "mana": self.mana, "max_mana": self.max_mana,
            "level": self.level, "map_level": self.map_level, "xp": self.xp, "xp_to_next_level": self.xp_to_next_level,
            "stat_points": self.stat_points, "strength": self.strength, "intelligence": self.intelligence, "endurance": self.endurance,
            "player_x": self.player_x, "player_y": self.player_y, "player_angle": self.player_angle,
            "in_interior": self.in_interior, "exterior_spawn": self.exterior_spawn,
            "exterior_map": self.exterior_map, "interior_map": self.interior_map,
            "exterior_items": self.exterior_items, "interior_items": self.interior_items,
            "exterior_enemies": ext_enemies_clean, "interior_enemies": int_enemies_clean,
            "inventory": self.inventory.slots, "torch_timer": self.torch_timer,
            "action_bar": [{"name": s["name"], "cd": s["cd"], "max_cd": s["max_cd"], "type": s["type"], "cost": s["cost"]} for s in self.action_bar.slots]
        }
        try:
            with open("savegame.json", "w") as f:
                json.dump(state, f)
        except Exception as e: pass

    def load_game_state(self):
        if os.path.exists("savegame.json"):
            try:
                with open("savegame.json", "r") as f:
                    state = json.load(f)
                
                self.level = state.get("level", self.level); self.xp = state.get("xp", self.xp)
                self.map_level = state.get("map_level", self.map_level)
                self.xp_to_next_level = state.get("xp_to_next_level", self.xp_to_next_level)
                
                self.stat_points = state.get("stat_points", self.stat_points)
                self.strength = state.get("strength", self.strength)
                self.intelligence = state.get("intelligence", self.intelligence)
                self.endurance = state.get("endurance", self.endurance)
                self.recalculate_max_stats()
                
                self.health = state.get("health", self.max_health)
                self.mana = state.get("mana", self.max_mana)
                
                self.player_x = state.get("player_x", self.player_x); self.player_y = state.get("player_y", self.player_y)
                self.player_angle = state.get("player_angle", self.player_angle)
                self.in_interior = state.get("in_interior", self.in_interior)
                self.exterior_spawn = state.get("exterior_spawn", self.exterior_spawn)
                
                self.exterior_map = self.pad_map(state.get("exterior_map", self.exterior_map))
                self.interior_map = state.get("interior_map", self.interior_map) 
                self.exterior_items = state.get("exterior_items", self.exterior_items)
                self.interior_items = state.get("interior_items", self.interior_items)
                self.exterior_enemies = state.get("exterior_enemies", self.exterior_enemies)
                self.interior_enemies = state.get("interior_enemies", self.interior_enemies)
                self.torch_timer = state.get("torch_timer", self.torch_timer)
                
                if self.player_x >= len(self.map[0]) * TILE_SIZE or self.player_y >= len(self.map) * TILE_SIZE:
                    self.player_x, self.player_y = self.get_safe_spawn()
                
                for e in self.exterior_enemies + self.interior_enemies: e['tex'] = self.enemy_sprite
                self.inventory.slots = state.get("inventory", self.inventory.slots)
                
                saved_ab = state.get("action_bar", [])
                for i, s in enumerate(saved_ab):
                    if i < len(self.action_bar.slots):
                        icon = None
                        if s["name"] != "Empty":
                            inv_idx, item = self.inventory.find_item_by_name(s["name"])
                            if item: icon = self.inventory.get_icon_for_item(item)
                            elif s["name"] in ["Spell: Heal", "Spell: Frost", "Fireball"]: 
                                icon = self.ui_icons.get("spell_heal") if s["name"] == "Spell: Heal" else self.ui_icons.get("spell_frost") if s["name"] == "Spell: Frost" else self.ui_icons.get("fireball")
                        self.action_bar.slots[i].update({"name": s["name"], "icon": icon, "cd": s["cd"], "max_cd": s["max_cd"], "type": s["type"], "cost": s["cost"]})
            except Exception as e: pass

    def spawn_enemies(self, map_data, count):
        enemy_list = []
        h, w = len(map_data), len(map_data[0])
        for _ in range(count):
            for _ in range(100):
                rx, ry = random.randint(1, w-2), random.randint(1, h-2)
                if map_data[ry][rx] == TileType.EMPTY.value:
                    enemy_list.append({
                        'x': rx * TILE_SIZE + TILE_SIZE//2, 'y': ry * TILE_SIZE + TILE_SIZE//2, 
                        'hp': 100, 'max_hp': 100, 'speed': 2.0, 'dmg': 10, 'cooldown': 0, 
                        'tex': self.enemy_sprite, 'is_enemy': True,
                        'level': random.randint(1, 3), 'mana': 50, 'stamina': 100, 
                        'weakness': 'Light', 'power': 'Ethereal'
                    })
                    break
        return enemy_list

    def extract_map_entities(self, raw_map):
        items = []
        enemies = []
        for y in range(len(raw_map)):
            for x in range(len(raw_map[y])):
                v = raw_map[y][x]
                if v in [TileType.ITEM_DAGGER.value, TileType.ITEM_KEY.value, TileType.ITEM_KEY_SILVER.value, 
                         TileType.ITEM_KEY_GOLD.value, TileType.ITEM_FOOD.value, TileType.ITEM_ARTIFACT.value, 
                         TileType.ITEM_HEALTH_POTION.value, TileType.ITEM_STAMINA_POTION.value,
                         TileType.ITEM_UNLIT_TORCH.value, TileType.ITEM_STAFF.value, 
                         TileType.ITEM_KEY_RUSTY_2.value, TileType.ITEM_KEY_DUNGEON.value]: 
                    items.append({'id': v, 'x': x*TILE_SIZE + 32, 'y': y*TILE_SIZE + 32})
                    raw_map[y][x] = TileType.EMPTY.value 
                elif v == TileType.ENEMY_GHOST.value:
                    enemies.append({'x': x*TILE_SIZE + 32, 'y': y*TILE_SIZE + 32, 'hp': 100, 'max_hp': 100, 'speed': 2.0, 'dmg': 10, 'cooldown': 0, 'tex': self.enemy_sprite, 'is_enemy': True})
                    raw_map[y][x] = TileType.EMPTY.value
                    
                elif v == TileType.ENEMY_BOSS.value:
                    b_hp, b_spd, b_dmg, b_scale = 500, 2.5, 50, 1.5
                    if os.path.exists("custom_boss.json"):
                        try:
                            with open("custom_boss.json", "r") as f:
                                b_data = json.load(f)
                                b_hp = b_data.get('hp', 500)
                                b_spd = b_data.get('speed', 2.5)
                                b_dmg = b_data.get('damage', 50)
                                b_scale = b_data.get('scale', 1.5)
                        except: pass
                        
                    enemies.append({
                        'x': x*TILE_SIZE + 32, 'y': y*TILE_SIZE + 32, 
                        'hp': b_hp, 'max_hp': b_hp, 
                        'speed': b_spd, 'dmg': b_dmg, 
                        'cooldown': 0, 'tex': self.boss_sprite, 'is_enemy': True, 'is_boss': True,
                        'level': int((b_hp / 100) + (b_dmg / 10)), 
                        'mana': 999, 'stamina': 999, 
                        'weakness': 'None', 'power': 'Boss Aura',
                        'scale': b_scale,
                        'anim_frame': 0, 'anim_timer': 0, 'is_attacking': False
                    })

                    raw_map[y][x] = TileType.EMPTY.value

        return raw_map, items, enemies

    def load_sprite_image(self, path, scale=True, size=(TILE_SIZE, TILE_SIZE), fallback="tree"):
        try:
            img = pygame.image.load(path).convert_alpha(); img.set_colorkey((0,0,0)) 
            if scale: return pygame.transform.scale(img, size)
            else: return img
        except: 
            surf = pygame.Surface(size, pygame.SRCALPHA)
            if fallback == "tree":
                pygame.draw.rect(surf, (80, 50, 30), (28, 40, 8, 24))
                for _ in range(30): pygame.draw.circle(surf, (34, 139, 34), (random.randint(18, 46), random.randint(8, 38)), random.randint(5, 10))
            elif fallback == "dead":
                pygame.draw.rect(surf, (60, 40, 30), (28, 40, 8, 24))
                pygame.draw.line(surf, (60, 40, 30), (32, 40), (15, 20), 4); pygame.draw.line(surf, (60, 40, 30), (32, 35), (45, 15), 4)
            elif fallback == "bush":
                for _ in range(20): pygame.draw.circle(surf, (20, 100, 30), (random.randint(15, 49), random.randint(30, 60)), random.randint(8, 15))
            elif fallback == "rock": pygame.draw.polygon(surf, (100, 100, 100), [(10, 60), (32, 30), (54, 60)])
            elif fallback == "food": pygame.draw.circle(surf, (200, 150, 100), (size[0]//2, size[1]//2), size[0]//3)
            elif fallback == "artifact": pygame.draw.polygon(surf, (0, 255, 255), [(size[0]//2, 5), (size[0]-5, size[1]//2), (size[0]//2, size[1]-5), (5, size[1]//2)])
            elif fallback == "enemy":
                pygame.draw.circle(surf, (200, 50, 50), (size[0]//2, size[1]//2), size[0]//3)
                pygame.draw.circle(surf, (255, 255, 0), (size[0]//2 - 6, size[1]//2 - 4), 3); pygame.draw.circle(surf, (255, 255, 0), (size[0]//2 + 6, size[1]//2 - 4), 3)
            elif fallback == "unlit_torch": pygame.draw.rect(surf, (100, 50, 20), (size[0]//2 - 4, 10, 8, size[1] - 20))
            elif fallback == "lit_torch":
                pygame.draw.rect(surf, (100, 50, 20), (size[0]//2 - 4, 10, 8, size[1] - 20))
                pygame.draw.circle(surf, (255, 150, 0), (size[0]//2, 10), 8)
            elif fallback == "none": return None
            else: pygame.draw.circle(surf, (150, 50, 150), (size[0]//2, size[1]//2), size[0]//3)
            return surf

    def load_hud_weapon(self, path):
        try:
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(img, (400, 400))
        except:
            surf = pygame.Surface((400, 400), pygame.SRCALPHA)
            pygame.draw.rect(surf, (150, 150, 150), (180, 50, 40, 250)); pygame.draw.rect(surf, (200, 150, 50), (140, 280, 120, 20)) 
            pygame.draw.rect(surf, (100, 50, 20), (185, 300, 30, 100)) 
            return surf

    def build_interactables(self):
        self.doors = []
        self.world_torches = []
        for y in range(len(self.map)):
            for x in range(len(self.map[y])):
                val = self.map[y][x]
                if val == TileType.DOOR.value:
                    self.doors.append({"x": x * TILE_SIZE + TILE_SIZE // 2, "y": y * TILE_SIZE + TILE_SIZE // 2, "name": "Brass Door", "key_required": "Brass Key", "gx": x, "gy": y, "is_stairs": False})
                elif val == TileType.DOOR_SILVER.value:
                    self.doors.append({"x": x * TILE_SIZE + TILE_SIZE // 2, "y": y * TILE_SIZE + TILE_SIZE // 2, "name": "Silver Door", "key_required": "Silver Key", "gx": x, "gy": y, "is_stairs": False})
                elif val == TileType.DOOR_GOLD.value:
                    self.doors.append({"x": x * TILE_SIZE + TILE_SIZE // 2, "y": y * TILE_SIZE + TILE_SIZE // 2, "name": "Gold Door", "key_required": "Gold Key", "gx": x, "gy": y, "is_stairs": False})
                elif val == TileType.STAIRS.value:
                    req_key = "Rusty Key 2" if self.in_interior else "Rusty Key"
                    self.doors.append({
                        "x": x * TILE_SIZE + TILE_SIZE // 2, 
                        "y": y * TILE_SIZE + TILE_SIZE // 2, 
                        "name": "Dungeon Entrance" if not self.in_interior else "Dungeon Exit", 
                        "key_required": req_key, 
                        "gx": x, "gy": y, 
                        "is_stairs": True
                    })
                elif val in [TileType.STANDING_TORCH.value, TileType.WALL_TORCH.value]:
                    self.world_torches.append({"x": x * TILE_SIZE + TILE_SIZE // 2, "y": y * TILE_SIZE + TILE_SIZE // 2, "name": "Light Torch"})

    def load_custom_overworld_map(self, level_num):
        filename = "map_data.json" if level_num == 1 else f"map_level_{level_num}.json"
        self.overworld_spawn_pos = None 
        try:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    data = json.load(f)
                    if 'map' in data:
                        raw_map = self.pad_map(data.get('map'))
                        
                        for y in range(len(raw_map)):
                            for x in range(len(raw_map[y])):
                                if raw_map[y][x] == TileType.PLAYER_SPAWN.value:
                                    self.overworld_spawn_pos = (x * TILE_SIZE + TILE_SIZE//2, y * TILE_SIZE + TILE_SIZE//2)
                                    raw_map[y][x] = TileType.EMPTY.value 
                                    
                        tex_name = data.get('floor_texture', 'GRASS')
                        self.floor_texture_type = FloorTextureType[tex_name] if tex_name in FloorTextureType.__members__ else FloorTextureType.GRASS
                        return self.extract_map_entities(raw_map)
        except: pass
        empty_map = [[TileType.EMPTY.value for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
        return self.extract_map_entities(empty_map)

    def go_to_next_level(self):
        if self.sfx.get("door"): self.sfx["door"].play()
        
        if not self.in_interior:
            self.in_interior = True
            self.consume_message = f"Entered Dungeon Challenge {self.map_level}!"
            self.consume_message_timer = 120
            
            self.interior_map, self.interior_items, _ = self.extract_map_entities(self.generate_dungeon_layout())
            num_enemies = min(20, 6 + self.map_level * 2)
            self.interior_enemies = self.spawn_enemies(self.interior_map, num_enemies)
            
            if os.path.exists("custom_boss.json"):
                try:
                    with open("custom_boss.json", "r") as f:
                        b_data = json.load(f)
                    self.interior_enemies.append({
                        'x': 25 * TILE_SIZE + 32, 'y': 25 * TILE_SIZE + 32, 
                        'hp': b_data.get('hp', 500), 'max_hp': b_data.get('hp', 500), 
                        'speed': b_data.get('speed', 2.5), 'dmg': b_data.get('damage', 50), 
                        'cooldown': 0, 'tex': self.boss_sprite, 'is_enemy': True, 'is_boss': True,
                        'level': int((b_data.get('hp', 500) / 100) + (b_data.get('damage', 50) / 10)), 
                        'mana': 999, 'stamina': 999, 
                        'weakness': 'None', 'power': 'Boss Aura',
                        'scale': b_data.get('scale', 1.5),
                        'anim_frame': 0, 'anim_timer': 0, 'is_attacking': False
                    })
                except Exception as e: 
                    print("Eve says: Couldn't spawn the boss!", e)
            
            self.map = self.interior_map
            self.world_items = self.interior_items
            self.enemies = self.interior_enemies
            
        else:
            self.in_interior = False
            self.map_level += 1 
            self.consume_message = f"Dungeon Cleared! Proceeding to Level {self.map_level}!"
            self.consume_message_timer = 120
            
            self.exterior_map, self.exterior_items, self.exterior_enemies = self.load_custom_overworld_map(self.map_level)
            
            self.map = self.exterior_map
            self.world_items = self.exterior_items
            self.enemies = self.exterior_enemies

        if self.in_interior:
            self.player_x, self.player_y = self.get_safe_spawn()
        else:
            if getattr(self, 'overworld_spawn_pos', None) is not None:
                self.player_x, self.player_y = self.overworld_spawn_pos
            else:
                self.player_x, self.player_y = self.get_safe_spawn()

        self.fog_of_war = [[False for _ in range(len(self.map[0]))] for _ in range(len(self.map))]
        self.build_lightmap()
        self.build_interactables()
        self.projectiles.clear()
        self.save_game_state()

    def generate_dungeon_layout(self):
        D_SIZE = 50 
        d_map = [[1 for _ in range(D_SIZE)] for _ in range(D_SIZE)]
        x, y = D_SIZE // 2, D_SIZE // 2
        d_map[y][x] = 0
        
        for _ in range(1500):
            move = random.choice([(0,1), (0,-1), (1,0), (-1,0)])
            if 1 <= x + move[0] < D_SIZE-1 and 1 <= y + move[1] < D_SIZE-1:
                x, y = x + move[0], y + move[1]
                d_map[y][x] = 0
                
        d_map[D_SIZE // 2][D_SIZE // 2 + 1] = TileType.STANDING_TORCH.value
        
        for _ in range(25):
            rx, ry = random.randint(1, D_SIZE-2), random.randint(1, D_SIZE-2)
            if d_map[ry][rx] == 0: d_map[ry][rx] = TileType.STANDING_TORCH.value
        for _ in range(15):
            rx, ry = random.randint(1, D_SIZE-2), random.randint(1, D_SIZE-2)
            if d_map[ry][rx] == 0: d_map[ry][rx] = TileType.ITEM_UNLIT_TORCH.value
            
        placed = False
        while not placed:
            rx, ry = random.randint(1, D_SIZE-2), random.randint(1, D_SIZE-2)
            if d_map[ry][rx] == 0: d_map[ry][rx] = TileType.STAIRS.value; placed = True
            
        return d_map

    def load_or_generate_map(self):
        try:
            if os.path.exists(MAP_DATA_FILE):
                with open(MAP_DATA_FILE, 'r') as f:
                    data = json.load(f)
                    if 'map' in data:
                        self.floor_texture_type = FloorTextureType[data.get('floor_texture', 'DIRT')]
                        raw_map = self.pad_map(data.get('map'))

                        for y in range(len(raw_map)):
                            for x in range(len(raw_map[y])):
                                if raw_map[y][x] == TileType.PLAYER_SPAWN.value:
                                    self.overworld_spawn_pos = (x * TILE_SIZE + TILE_SIZE//2, y * TILE_SIZE + TILE_SIZE//2)
                                    raw_map[y][x] = TileType.EMPTY.value 

                        return self.extract_map_entities(raw_map)
        except: pass
        return self.extract_map_entities(self.generate_dungeon_layout())

    def build_lightmap(self):
        h, w = len(self.map), len(self.map[0])
        self.lightmap = [[0 for _ in range(w)] for _ in range(h)]
        for y in range(h):
            for x in range(w):
                val = self.map[y][x]
                if val == TileType.STANDING_TORCH.value or val == TileType.WALL_TORCH.value:
                    for ly in range(max(0, y-5), min(h, y+6)):
                        for lx in range(max(0, x-5), min(w, x+6)):
                            dist = math.hypot(x - lx, y - ly)
                            intensity = int(max(0, 255 - (dist * 40)))
                            self.lightmap[ly][lx] = min(255, self.lightmap[ly][lx] + intensity)

    def get_safe_spawn(self):
        h, w = len(self.map), len(self.map[0])
        for _ in range(100):
            r, c = random.randint(1, h-2), random.randint(1, w-2)
            if self.map[r][c] == TileType.EMPTY.value: return (c * TILE_SIZE + 32, r * TILE_SIZE + 32)
        return (128, 128)

    def lerp_color(self, c1, c2, t):
        t_smooth = (1 - math.cos(t * math.pi)) / 2
        return tuple(int(c1[i] + (c2[i] - c1[i]) * t_smooth) for i in range(3))

    def get_sky_color(self):
        if self.in_interior: return (15, 15, 20)
        keys = sorted(self.sky_keyframes.keys())
        base_color = (5, 5, 15)
        for i in range(len(keys) - 1):
            if keys[i] <= self.time <= keys[i+1]:
                base_color = self.lerp_color(self.sky_keyframes[keys[i]], self.sky_keyframes[keys[i+1]], (self.time - keys[i]) / (keys[i+1] - keys[i]))
                break
        if 'rain' in self.weather_type:
            target_dark = (40, 45, 50)
            base_color = tuple(int(base_color[i] * (1 - self.weather_intensity) + target_dark[i] * self.weather_intensity) for i in range(3))
        elif 'sand' in self.weather_type:
            target_dark = (120, 100, 70)
            base_color = tuple(int(base_color[i] * (1 - self.weather_intensity) + target_dark[i] * self.weather_intensity) for i in range(3))
        return base_color

    def get_smooth_ambient_light(self):
        t = self.time
        if 400 <= t < 800: amb = int(40 + (255 - 40) * ((t - 400) / 400)) 
        elif 800 <= t < 1600: amb = 255 
        elif 1600 <= t < 2000: amb = int(255 - (255 - 40) * ((t - 1600) / 400)) 
        else: amb = 40 
        if 'rain' in self.weather_type or 'sand' in self.weather_type:
            amb = int(amb * (1.0 - (self.weather_intensity * 0.5)))
        return amb

    def load_door_texture(self):
        tex = pygame.Surface((TILE_SIZE, TILE_SIZE)); tex.fill((100, 50, 20)) 
        for x in range(0, TILE_SIZE, 16): pygame.draw.line(tex, (60, 30, 10), (x, 0), (x, TILE_SIZE), 2)
        pygame.draw.rect(tex, (100, 100, 100), (0, TILE_SIZE//2 - 4, TILE_SIZE, 8))
        pygame.draw.circle(tex, (200, 180, 50), (TILE_SIZE - 12, TILE_SIZE//2), 6)
        return tex

    def load_all_wall_textures(self):
        textures = {}
        try: textures[TileType.WALL_BRICK.value] = pygame.transform.scale(pygame.image.load(WALL_TEXTURE_PATH).convert(), (TILE_SIZE, TILE_SIZE)) 
        except:
            tex = pygame.Surface((TILE_SIZE, TILE_SIZE)); tex.fill((90, 45, 35))
            for y in range(0, TILE_SIZE, 16): pygame.draw.line(tex, (50, 25, 20), (0, y), (TILE_SIZE, y), 2)
            textures[TileType.WALL_BRICK.value] = tex
            
        stone = pygame.Surface((TILE_SIZE, TILE_SIZE)); stone.fill((100, 100, 100))
        for y in range(0, TILE_SIZE, 16):
            pygame.draw.line(stone, (50, 50, 50), (0, y), (TILE_SIZE, y), 2)
            for x in range(16 if (y // 16) % 2 == 0 else 0, TILE_SIZE, 32): pygame.draw.line(stone, (50, 50, 50), (x, y), (x, y+16), 2)
        textures[TileType.WALL_STONE.value] = stone
        
        cave_rock = pygame.Surface((TILE_SIZE, TILE_SIZE))
        cave_rock.fill((42, 40, 41))
        for _ in range(50):
            x1, y1 = random.randint(0, TILE_SIZE), random.randint(0, TILE_SIZE)
            x2, y2 = x1 + random.randint(-14, 14), y1 + random.randint(-14, 14)
            pygame.draw.line(cave_rock, (24, 22, 23), (x1, y1), (x2, y2), 2)
            pygame.draw.circle(cave_rock, (52, 50, 51), (x1, y1), random.randint(2, 4))
        textures["CAVE_ROCK"] = cave_rock
        
        wood = pygame.Surface((TILE_SIZE, TILE_SIZE)); wood.fill((120, 70, 30))
        for x in range(0, TILE_SIZE, 16): pygame.draw.line(wood, (80, 40, 15), (x, 0), (x, TILE_SIZE), 2)
        textures[TileType.WALL_WOOD.value] = wood
        
        def make_cracked(base_surf):
            cracked = base_surf.copy()
            pygame.draw.lines(cracked, (15, 15, 15), False, [(TILE_SIZE//2, 0), (TILE_SIZE//2 + 10, TILE_SIZE//3), (TILE_SIZE//2 - 5, TILE_SIZE//2), (TILE_SIZE//2 + 8, TILE_SIZE)], 3)
            return cracked
            
        textures[TileType.WALL_BRICK_CRACKED.value] = make_cracked(textures[TileType.WALL_BRICK.value])
        textures[TileType.WALL_STONE_CRACKED.value] = make_cracked(textures[TileType.WALL_STONE.value])
        textures[TileType.WALL_WOOD_CRACKED.value] = make_cracked(textures[TileType.WALL_WOOD.value])
        
        ff = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        ff.fill((0, 150, 255, 180)) 
        for y in range(0, TILE_SIZE, 8): pygame.draw.line(ff, (100, 255, 255, 200), (0, y), (TILE_SIZE, y), 1)
        for x in range(0, TILE_SIZE, 8): pygame.draw.line(ff, (100, 255, 255, 200), (x, 0), (x, TILE_SIZE), 1)
        textures[TileType.FORCE_FIELD.value] = ff
        
        stairs_tex = stone.copy()
        for y in range(0, TILE_SIZE, 16): pygame.draw.rect(stairs_tex, (30,30,30), (0, y, TILE_SIZE, 8))
        textures[TileType.STAIRS.value] = stairs_tex
        
        w_torch = textures[TileType.WALL_STONE.value].copy()
        pygame.draw.rect(w_torch, (80, 80, 80), (28, 20, 8, 20)); pygame.draw.circle(w_torch, (255, 150, 0), (32, 16), 10); pygame.draw.circle(w_torch, (255, 255, 100), (32, 18), 5)
        textures[TileType.WALL_TORCH.value] = w_torch
        return textures

    def generate_stone_dirt_texture(self):
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE)); surf.fill((65, 38, 15))
        random.seed(42) 
        for y in range(0, TILE_SIZE, 12):
            for x in range(0, TILE_SIZE, 12):
                cx, cy, r = x + random.randint(-4, 4), y + random.randint(-4, 4), random.uniform(5, 9)
                pts = [(cx + math.cos(math.radians(a))*r, cy + math.sin(math.radians(a))*r) for a in range(0, 360, 60)]
                for ox in [-TILE_SIZE, 0, TILE_SIZE]:
                    for oy in [-TILE_SIZE, 0, TILE_SIZE]: pygame.draw.polygon(surf, random.choice([(125, 85, 30), (145, 100, 40), (110, 70, 20)]), [(px+ox, py+oy) for px, py in pts])
        return surf

    def load_all_floor_textures(self):
        textures = {}
        try: textures['DIRT'] = pygame.transform.scale(pygame.image.load(FLOOR_DIRT_PATH).convert(), (TILE_SIZE, TILE_SIZE)) 
        except: textures['DIRT'] = self.generate_stone_dirt_texture()
        
        stone = pygame.Surface((TILE_SIZE, TILE_SIZE)); stone.fill((130, 130, 130))
        for _ in range(200): pygame.draw.rect(stone, (random.randint(100, 150), random.randint(100, 150), random.randint(100, 150)), (random.randint(0, 63), random.randint(0, 63), random.randint(1, 3), random.randint(1, 3)))
        textures['STONE'] = stone
        
        try: textures['SAND'] = pygame.transform.scale(pygame.image.load(FLOOR_SAND_PATH).convert(), (TILE_SIZE, TILE_SIZE))
        except:
            sand = pygame.Surface((TILE_SIZE, TILE_SIZE)); sand.fill((194, 178, 128))
            for _ in range(150): pygame.draw.rect(sand, (random.randint(150, 180), random.randint(130, 160), random.randint(80, 110)), (random.randint(0, 63), random.randint(0, 63), 2, 2))
            textures['SAND'] = sand
            
        try: textures['GRASS'] = pygame.transform.scale(pygame.image.load(FLOOR_GRASS_PATH).convert(), (TILE_SIZE, TILE_SIZE))
        except:
            grass = pygame.Surface((TILE_SIZE, TILE_SIZE)); grass.fill((34, 139, 34))
            for _ in range(100): pygame.draw.rect(grass, (random.randint(20, 60), random.randint(120, 150), random.randint(20, 60)), (random.randint(0, 63), random.randint(0, 63), 2, 2))
            textures['GRASS'] = grass
            
        self.floor_color_maps = {name: [[tex.get_at((x, y)) for y in range(TILE_SIZE)] for x in range(TILE_SIZE)] for name, tex in textures.items()}
        return textures

    def load_cloud_sprite(self):
        try: return pygame.image.load(CLOUD_SPRITE_PATH).convert_alpha()
        except:
            surf = pygame.Surface((100, 40), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 255, 255, 200), (20, 20), 15); pygame.draw.circle(surf, (255, 255, 255, 200), (40, 15), 18)
            pygame.draw.circle(surf, (255, 255, 255, 200), (60, 20), 16); pygame.draw.rect(surf, (255, 255, 255, 200), (20, 20, 40, 20))
            return surf

    def get_scaled_cloud_sprite(self, scale):
        rounded_scale = round(scale, 1)
        if rounded_scale not in self.cloud_sprites_cache:
            w, h = self.cloud_sprite.get_size()
            self.cloud_sprites_cache[rounded_scale] = pygame.transform.scale(self.cloud_sprite, (int(w * rounded_scale), int(h * rounded_scale)))
        return self.cloud_sprites_cache[rounded_scale]

    def generate_parallax_clouds(self):
        clouds = []
        for layer in range(CLOUD_LAYERS):
            depth = layer / (CLOUD_LAYERS - 1) if CLOUD_LAYERS > 1 else 1.0  
        for _ in range(4 + layer):
            clouds.append({'x': random.randint(0, WIDTH), 'y': random.randint(5, 80 + layer * 20), 'scale': 3.0 + (depth * 3.5), 'depth': depth, 'speed_mult': CLOUD_SPEED_MULTIPLIERS[layer], 'alpha': 255 - int(depth * 25)})
        return clouds

    def manage_weather(self):
        h, w = len(self.map), len(self.map[0])
        if self.in_interior:
            self.weather_type = 'rain'
            self.weather_intensity = 0.5
        elif self.floor_texture_type.name == 'SAND':
            self.weather_type = 'sand'
        if self.weather_intensity < 1.0: self.weather_intensity += 0.005 
        else:
            self.weather_timer += 1
        if self.weather_type != self.weather_target:
                self.weather_intensity -= 0.003
                if self.weather_intensity <= 0: self.weather_type = self.weather_target
        else:
                if self.weather_intensity < 1.0: self.weather_intensity += 0.003
        if self.weather_timer >= self.weather_duration:
                self.weather_target = random.choice([w for w in WEATHER_TYPES if w != self.weather_type])
                self.weather_timer = 0
                self.weather_duration = random.randint(*WEATHER_TRANSITIONS.get(self.weather_target, (2000, 4000)))
            
                target_count = int(WEATHER_INTENSITY.get(self.weather_type, {}).get('count', 0) * self.weather_intensity)
        if self.in_interior: target_count = 75 
        
        while len(self.particles) < target_count: 
            speed = random.uniform(3, 6) if self.in_interior else (random.uniform(8, 14) if 'rain' in self.weather_type else random.uniform(4, 8))
            self.particles.append({'x': random.uniform(0, w*TILE_SIZE), 'y': random.uniform(0, h*TILE_SIZE), 'z': random.uniform(-180, 180), 'speed': speed, 'wind_accel': 0})
            
        while len(self.particles) > target_count and len(self.particles) > 0: 
            self.particles.pop()

    def update_fog_of_war(self):
        h, w = len(self.map), len(self.map[0])
        pgx, pgy = int(self.player_x / TILE_SIZE), int(self.player_y / TILE_SIZE)
        for y in range(max(0, pgy - self.minimap_reveal_radius), min(h, pgy + self.minimap_reveal_radius + 1)):
            for x in range(max(0, pgx - self.minimap_reveal_radius), min(w, pgx + self.minimap_reveal_radius + 1)):
                if math.hypot(x - pgx, y - pgy) <= self.minimap_reveal_radius: self.fog_of_war[y][x] = True

    def draw_sun_moon(self):
        sun_size = 40
        if 400 <= self.time < 2000:  
            progress = (self.time - 400) / 1600.0
            sun_x = int(50 + progress * (WIDTH - 100))
            sun_y = int(HEIGHT // 4 + 40 * math.sin(progress * math.pi))
            sun_alpha = 1.0
            if 'rain' in self.weather_type or 'sand' in self.weather_type:
                sun_alpha = max(0, 1.0 - (self.weather_intensity * 1.5))
            if sun_alpha > 0:
                pygame.draw.circle(self.screen, (int(255*sun_alpha), int(200*sun_alpha), int(50*sun_alpha)), (sun_x, sun_y), sun_size + 5)
                pygame.draw.circle(self.screen, (int(255*sun_alpha), int(220*sun_alpha), int(100*sun_alpha)), (sun_x, sun_y), sun_size)
            else:  
                progress = self.time / 400 if self.time < 400 else (self.time - 2000) / 400 
                moon_x = int(WIDTH // 2 + 100 * math.cos(progress * math.pi))
                moon_y = int(HEIGHT // 4 + 30)
                moon_alpha = 1.0
            if 'rain' in self.weather_type or 'sand' in self.weather_type:
                moon_alpha = max(0, 1.0 - (self.weather_intensity * 1.5))
            if moon_alpha > 0:
                pygame.draw.circle(self.screen, (int(220*moon_alpha), int(220*moon_alpha), int(200*moon_alpha)), (moon_x, moon_y), sun_size - 5)
                pygame.draw.circle(self.screen, (int(100*moon_alpha), int(100*moon_alpha), int(80*moon_alpha)), (moon_x - 10, moon_y - 5), 4)
                pygame.draw.circle(self.screen, (int(100*moon_alpha), int(100*moon_alpha), int(80*moon_alpha)), (moon_x + 8, moon_y + 8), 3)

    def draw_stars(self):
        if self.time < 600 or self.time > 1800:
                star_alpha = 1.0
        if 'rain' in self.weather_type or 'sand' in self.weather_type:
                star_alpha = max(0, 1.0 - (self.weather_intensity * 1.5))
        if star_alpha > 0:
                random.seed(42)  
        for _ in range(100):
                brightness = int((200 + 55 * math.sin(self.time / 100)) * star_alpha) 
                pygame.draw.circle(self.screen, (brightness, brightness, brightness), (random.randint(0, WIDTH), random.randint(0, HEIGHT // 2)), random.randint(1, 2))
                random.seed() 

    def draw_minimap(self):
        h, w = len(self.map), len(self.map[0])
        cell_size = self.minimap_size / max(h, w)
        pygame.draw.rect(self.screen, (20, 20, 20), (self.minimap_x, self.minimap_y, self.minimap_size + 4, self.minimap_size + 4))
        pygame.draw.rect(self.screen, (100, 100, 100), (self.minimap_x, self.minimap_y, self.minimap_size + 4, self.minimap_size + 4), 2)
        for y in range(h):
            for x in range(w):
                tile_x, tile_y = self.minimap_x + 2 + x * cell_size, self.minimap_y + 2 + y * cell_size
                if self.fog_of_war[y][x]:
                    val = self.map[y][x]
                if val == TileType.WALL_BRICK.value or val == TileType.WALL_BRICK_CRACKED.value: pygame.draw.rect(self.screen, (100, 50, 50), (tile_x,   tile_y, cell_size, cell_size))
                elif val == TileType.WALL_STONE.value or val == TileType.WALL_STONE_CRACKED.value: pygame.draw.rect(self.screen, (80, 80, 80), (tile_x, tile_y, cell_size, cell_size))
                elif val == TileType.WALL_WOOD.value or val == TileType.WALL_WOOD_CRACKED.value: pygame.draw.rect(self.screen, (100, 60, 20), (tile_x, tile_y, cell_size, cell_size))
                elif val == TileType.FORCE_FIELD.value: pygame.draw.rect(self.screen, (0, 255, 255), (tile_x, tile_y, cell_size, cell_size))
                elif val in [TileType.DOOR.value, TileType.DOOR_SILVER.value, TileType.DOOR_GOLD.value]: pygame.draw.rect(self.screen, (255, 200, 50), (tile_x, tile_y, cell_size, cell_size))
                elif val == TileType.TREE.value: pygame.draw.rect(self.screen, (34, 100, 34), (tile_x, tile_y, cell_size, cell_size))
                elif val == TileType.DEAD_TREE.value: pygame.draw.rect(self.screen, (80, 70, 60), (tile_x, tile_y, cell_size, cell_size))
                elif val == TileType.BUSH.value: pygame.draw.rect(self.screen, (20, 150, 50), (tile_x, tile_y, cell_size, cell_size))
                elif val == TileType.ROCK.value: pygame.draw.rect(self.screen, (150, 150, 150), (tile_x, tile_y, cell_size, cell_size))
                elif val == TileType.STANDING_TORCH.value: pygame.draw.rect(self.screen, (255, 140, 0), (tile_x, tile_y, cell_size, cell_size))
                elif val == TileType.WALL_TORCH.value: pygame.draw.rect(self.screen, (200, 80, 20), (tile_x, tile_y, cell_size, cell_size))
                elif val == TileType.STAIRS.value: pygame.draw.rect(self.screen, (150, 100, 255), (tile_x, tile_y, cell_size, cell_size))
                else: pygame.draw.rect(self.screen, (50, 80, 50), (tile_x, tile_y, cell_size, cell_size))
            else: pygame.draw.rect(self.screen, (30, 30, 30), (tile_x, tile_y, cell_size, cell_size))
        px, py = self.minimap_x + 2 + (self.player_x / (w * TILE_SIZE)) * self.minimap_size, self.minimap_y + 2 + (self.player_y / (h * TILE_SIZE)) * self.minimap_size
        pygame.draw.circle(self.screen, (0, 255, 0), (int(px), int(py)), 3)

    def draw_ss2_bracket(self, rect, label):
        x, y, w, h = rect
        l, t = max(5, w//4), 2
        alpha = int(150 + 105 * math.sin(pygame.time.get_ticks() / 150))
        
        bracket_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        color_with_alpha = (255, 255, 255, alpha)
        
        pygame.draw.line(bracket_surf, color_with_alpha, (0, 0), (l, 0), t)
        pygame.draw.line(bracket_surf, color_with_alpha, (0, 0), (0, l), t)
        pygame.draw.line(bracket_surf, color_with_alpha, (w-1, 0), (w-1-l, 0), t)
        pygame.draw.line(bracket_surf, color_with_alpha, (w-1, 0), (w-1, l), t)
        pygame.draw.line(bracket_surf, color_with_alpha, (0, h-1), (l, h-1), t)
        pygame.draw.line(bracket_surf, color_with_alpha, (0, h-1), (0, h-1-l), t)
        pygame.draw.line(bracket_surf, color_with_alpha, (w-1, h-1), (w-1-l, h-1), t)
        pygame.draw.line(bracket_surf, color_with_alpha, (w-1, h-1), (w-1, h-1-l), t)
        
        self.screen.blit(bracket_surf, (x, y))
        
        text = self.font_small_bold.render(f"[ {label} ]", True, (255, 255, 255))
        self.screen.blit(text, (x + w//2 - text.get_width()//2, y - 20))

    def collect_xp(self, amount):
        self.xp += amount
        self.consume_message = f"+{amount} XP"
        self.consume_message_timer = 60
        if self.xp >= self.xp_to_next_level:
            self.xp -= self.xp_to_next_level
            self.level += 1
            self.stat_points += 3
            self.xp_to_next_level = int(self.xp_to_next_level * 1.5)
            
            if self.level == 5:
                self.inventory.add_item("Spell: Heal", 1, "magic", "Restores 50 HP. Cost: 20 Mana")
                self.consume_message = "New Spell Unlocked: Heal!"
            elif self.level == 10:
                self.inventory.add_item("Spell: Frost", 1, "magic", "Ice attack. Cost: 15 Mana")
                self.consume_message = "New Spell Unlocked: Frost!"
            else:
                self.consume_message = f"LEVEL UP! Reached Level {self.level}!"
                
            self.recalculate_max_stats()
            self.health = self.max_health
            self.mana = self.max_mana
            self.stamina = self.max_stamina
            
            self.consume_message_timer = 120
            self.show_stat_screen = True 
            if self.sfx.get("pickup"): self.sfx["pickup"].play()
            
    def update(self):
        h, w = len(self.map), len(self.map[0])
        if self.health <= 0 and not self.game_over:
            self.game_over = True
            self.game_over_timer = 180
            if self.sfx.get("error"): self.sfx["error"].play()
            
        if self.game_over:
            self.attack_swing = 0
            self.projectiles.clear()
            return
            
        if self.torch_timer > 0:
            self.torch_timer -= 1
            
        if self.attack_swing > 0:
            self.attack_swing -= 0.05
            if self.attack_swing <= 0: self.attack_swing = 0

        self.update_leaves()

        keys = pygame.key.get_pressed()
        is_moving_input = keys[pygame.K_w] or keys[pygame.K_s]
        is_running_input = keys[pygame.K_LSHIFT] and is_moving_input
        
        doing_physical = False
        if self.attack_swing > 0:
            doing_physical = True
            
        if is_moving_input:
            doing_physical = True
            if self.stamina > 0:
                if is_running_input:
                    self.player_speed_mod = 1.8 
                    self.stamina -= 0.4
                else:
                    self.player_speed_mod = 1.0
                    self.stamina -= 0.1
            else:
                self.player_speed_mod = 0.3 
        else:
            self.player_speed_mod = 1.0
            
        if not doing_physical and self.stamina < self.max_stamina:
            self.stamina += 0.3 
        
        if self.level_complete:
            self.level_complete_timer -= 1
            return 
            
        if self.inventory.visible: return 
        self.action_bar.update()

        for spark in self.sparks[:]:
            spark['x'] += spark['vx']
            spark['y'] += spark['vy']
            spark['life'] -= 1
            if spark['life'] <= 0: self.sparks.remove(spark)
        
        for proj in self.projectiles[:]:
            proj['x'] += math.cos(proj['angle']) * proj['speed']
            proj['y'] += math.sin(proj['angle']) * proj['speed']
            
            gx, gy = int(proj['x'] // TILE_SIZE), int(proj['y'] // TILE_SIZE)
            
            if proj.get('is_enemy_proj'):
                if math.hypot(proj['x'] - self.player_x, proj['y'] - self.player_y) < 30:
                    self.health -= proj.get('dmg', 20)
                    if self.sfx.get("error"): self.sfx["error"].play()
                    self.projectiles.remove(proj)
                    continue
            else:
                hit_enemy = False
                for e in self.enemies:
                    if math.hypot(proj['x'] - e['x'], proj['y'] - e['y']) < 30:
                        e['hp'] -= proj.get('dmg', 35) 
                        hit_enemy = True
                        break
                if hit_enemy:
                    self.projectiles.remove(proj)
                    continue

            if 0 <= gx < w and 0 <= gy < h:
                if self.map[gy][gx] == TileType.FORCE_FIELD.value:
                    self.map[gy][gx] = TileType.EMPTY.value
                    if self.sfx.get("door"): self.sfx["door"].play() 
                    self.projectiles.remove(proj)
                    continue
                    
                if self.map[gy][gx] not in [TileType.EMPTY.value, TileType.TREE.value, TileType.STANDING_TORCH.value, TileType.DEAD_TREE.value, TileType.BUSH.value, TileType.ROCK.value]:
                    self.projectiles.remove(proj)
            else:
                self.projectiles.remove(proj)
                
        self.time = (self.time + 0.2) % 2400 
        self.ambient_light = self.get_smooth_ambient_light()
        self.global_flicker = 0.9 + 0.1 * math.sin(pygame.time.get_ticks() / 100.0) + random.uniform(-0.05, 0.05)
        self.update_fog_of_war()
        if self.consume_message_timer > 0: self.consume_message_timer -= 1
        self.manage_weather()
        
        self.global_wind = math.sin(pygame.time.get_ticks() * 0.001) * 1.5 + math.cos(pygame.time.get_ticks() * 0.0005) * 0.5
        
        if 'rain' in self.weather_type:
            self.wind_effect = math.sin(self.weather_timer * 0.03) * (2.5 if 'heavy' in self.weather_type else 0.8) + self.global_wind
        elif 'sand' in self.weather_type:
            self.wind_effect = math.sin(self.weather_timer * 0.02) * 2.0 + self.global_wind
        else:
            self.wind_effect = self.global_wind
            
        combat_detected = False
        walkable = [TileType.EMPTY.value, TileType.TREE.value, TileType.STANDING_TORCH.value, TileType.DEAD_TREE.value, TileType.BUSH.value, TileType.ROCK.value]
        
        for e in self.enemies:
            dist = math.hypot(self.player_x - e['x'], self.player_y - e['y'])
            if dist < 250:
                combat_detected = True
                if e.get('is_boss'):
                    e['anim_timer'] = e.get('anim_timer', 0) + 1
                    
                    if e.get('is_attacking'):
                        if e['anim_timer'] > 5: 
                            e['anim_timer'] = 0
                            e['anim_frame'] += 1
                            if e['anim_frame'] >= len(self.boss_attack_frames):
                                e['is_attacking'] = False
                                e['anim_frame'] = 0
                            else:
                                e['tex'] = self.boss_attack_frames[e['anim_frame']]
                    else:
                        if e['anim_timer'] > 6: 
                            e['anim_timer'] = 0
                            e['anim_frame'] = (e.get('anim_frame', 0) + 1) % len(self.boss_idle_frames)
                            e['tex'] = self.boss_idle_frames[e['anim_frame']]

                    if e.get('shoot_cooldown', 0) <= 0 and dist < 200:
                        angle_to_player = math.atan2(self.player_y - e['y'], self.player_x - e['x'])
                        self.projectiles.append({
                            'x': e['x'], 'y': e['y'], 
                            'angle': angle_to_player, 'speed': 6.0, 
                            'tex': self.ui_icons.get("fireball"), 
                            'dmg': e.get('dmg', 30), 
                            'is_enemy_proj': True
                        })
                        if self.sfx.get("fireball"): self.sfx["fireball"].play()
                        e['shoot_cooldown'] = 90  
                        e['is_attacking'] = True
                        e['anim_frame'] = 0
                        e['anim_timer'] = 0
                    else:
                        e['shoot_cooldown'] = e.get('shoot_cooldown', 0) - 1

                if dist > 40:
                    dx, dy = (self.player_x - e['x']) / dist, (self.player_y - e['y']) / dist
                    nx, ny = e['x'] + dx * e['speed'], e['y'] + dy * e['speed']
                    
                    egx, egy = int(nx // TILE_SIZE), int(e['y'] // TILE_SIZE)
                    if 0 <= egx < w and 0 <= egy < h and self.map[egy][egx] in walkable: 
                        e['x'] = nx
                        
                    egx, egy = int(e['x'] // TILE_SIZE), int(ny // TILE_SIZE)
                    if 0 <= egx < w and 0 <= egy < h and self.map[egy][egx] in walkable: 
                        e['y'] = ny
                else: 
                    if e['cooldown'] <= 0:
                        self.health -= e['dmg']
                        e['cooldown'] = 60
                        if self.sfx.get("error"): self.sfx["error"].play() 
            if e['cooldown'] > 0: e['cooldown'] -= 1

            
        dead_enemies = [e for e in self.enemies if e['hp'] <= 0]
        for e in dead_enemies:
            if e.get('is_boss'):
                self.collect_xp(500) 
                self.world_items.append({'id': TileType.ITEM_KEY_RUSTY_2.value, 'x': e['x'], 'y': e['y']})
                self.world_items.append({'id': TileType.ITEM_ARTIFACT.value, 'x': e['x'] + 25, 'y': e['y'] + 25})
                self.world_items.append({'id': TileType.ITEM_HEALTH_POTION.value, 'x': e['x'] - 25, 'y': e['y'] - 25})
                
                self.consume_message = "Boss Defeated! Exit Key Dropped!"
                self.consume_message_timer = 120
                if self.sfx.get("pickup"): self.sfx["pickup"].play()
            else:
                self.collect_xp(35)
                
            if e in self.exterior_enemies: self.exterior_enemies.remove(e)
            if e in self.interior_enemies: self.interior_enemies.remove(e)
            if e in self.enemies: self.enemies.remove(e)
            self.save_game_state()

        
        if combat_detected and not self.in_combat:
            self.in_combat = True
        elif not combat_detected and self.in_combat:
            self.in_combat = False
            
        is_night = self.time < 600 or self.time > 1800
        is_raining = 'rain' in self.weather_type and self.weather_intensity > 0.1
        
        target_bgm = getattr(self, 'current_bgm', "bgm.mp3")
        if self.in_combat:
            target_bgm = "combat.mp3"
        elif self.in_interior:
            target_bgm = "dungeon_rainstorm.mp3"
        else:
            target_bgm = "music.mp3" if (is_night and not is_raining) else "bgm.mp3"

        if getattr(self, 'current_bgm', None) != target_bgm and getattr(self, 'next_bgm', None) != target_bgm:
            if MIXER_READY: pygame.mixer.music.fadeout(1500) 
            self.next_bgm = target_bgm
            self.bgm_fade_timer = 90 
            
        if getattr(self, 'bgm_fade_timer', 0) > 0:
            self.bgm_fade_timer -= 1
            if self.bgm_fade_timer <= 0 and self.next_bgm:
                self.current_bgm = self.next_bgm
                if MIXER_READY:
                    try:
                        pygame.mixer.music.load(self.current_bgm)
                        pygame.mixer.music.set_volume(0.15)
                        pygame.mixer.music.play(-1, fade_ms=1500) 
                    except: pass
                self.next_bgm = None
        
        if 'rain' in self.weather_type and self.weather_intensity > 0.1:
            if not CH_RAIN.get_busy() and SFX_RAIN: CH_RAIN.play(SFX_RAIN, -1)
            CH_RAIN.set_volume(self.weather_intensity * 0.5)
        else:
            if CH_RAIN.get_busy(): CH_RAIN.fadeout(500)
            
        if is_night and not is_raining and not self.in_interior:
            if not CH_CRICKETS.get_busy() and SFX_CRICKETS:
                CH_CRICKETS.play(SFX_CRICKETS, -1)
            CH_CRICKETS.set_volume(0.2) 
        else:
            if CH_CRICKETS.get_busy():
                CH_CRICKETS.fadeout(1000)

        px, py = int(self.player_x // TILE_SIZE), int(self.player_y // TILE_SIZE)
        if 0 <= px < w and 0 <= py < h:
            torch_light = self.lightmap[py][px]
            if torch_light > 0:
                if not CH_TORCHES.get_busy() and SFX_TORCH:
                    CH_TORCHES.play(SFX_TORCH, -1)
                vol = min(1.0, (torch_light / 255.0) * 0.8)
                CH_TORCHES.set_volume(vol)
            else:
                if CH_TORCHES.get_busy():
                    CH_TORCHES.fadeout(500)
        else:
            if CH_TORCHES.get_busy(): CH_TORCHES.fadeout(500)

        weather_scale_bonus = 1.0
        if 'rain' in self.weather_type or 'sand' in self.weather_type:
            weather_scale_bonus = 1.0 + (self.weather_intensity * 1.5)
        for c in self.clouds: 
            c['x'] = (c['x'] + c['speed_mult'] * 0.3) % (WIDTH + 200)
            c['current_scale'] = c['scale'] * weather_scale_bonus
        if len(self.particles) > 0:
            for p in self.particles:
                p['z'] += p['speed'] + (2.0 if self.weather_type == 'rain_heavy' else 0)
                if p['z'] > 180: p['z'] = -180
                if 'sand' in self.weather_type or 'rain' in self.weather_type: 
                    p['wind_accel'] = self.wind_effect
        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.hovered_interactable = None
        self.hovered_rect = None
        self.hovered_enemy = None
        proj_plane_dist = (WIDTH / 2) / math.tan(FOV / 2)
        
        for door in self.doors:
            dist = math.hypot(self.player_x - door["x"], self.player_y - door["y"])
            if dist < 120:  
                dx, dy = door["x"] - self.player_x, door["y"] - self.player_y
                px = dx * math.cos(-self.player_angle) - dy * math.sin(-self.player_angle)
                py = dx * math.sin(-self.player_angle) + dy * math.cos(-self.player_angle)
                if px > 0.5:
                    sx = int((py / px) * proj_plane_dist + (WIDTH / 2))
                    size = max(20, int(WALL_HEIGHT_MULTIPLIER / px))
                    bracket_w = min(120, size // 2)
                    bracket_h = min(120, size // 2)
                    rect = pygame.Rect(sx - bracket_w//2, HEIGHT//2 - bracket_h//2, bracket_w, bracket_h)
                    if rect.collidepoint(mouse_x, mouse_y):
                        self.hovered_interactable = {"type": "door", "door": door, "name": door["name"]}
                        self.hovered_rect = rect
                        
        for t in self.world_torches:
            dist = math.hypot(self.player_x - t["x"], self.player_y - t["y"])
            if dist < 120:
                dx, dy = t["x"] - self.player_x, t["y"] - self.player_y
                px = dx * math.cos(-self.player_angle) - dy * math.sin(-self.player_angle)
                py = dx * math.sin(-self.player_angle) + dy * math.cos(-self.player_angle)
                if px > 0.5:
                    sx = int((py / px) * proj_plane_dist + (WIDTH / 2))
                    size = max(20, int(WALL_HEIGHT_MULTIPLIER / px))
                    bracket_w = min(120, size // 2)
                    bracket_h = min(120, size // 2)
                    rect = pygame.Rect(sx - bracket_w//2, HEIGHT//2 - bracket_h//2, bracket_w, bracket_h)
                    if rect.collidepoint(mouse_x, mouse_y):
                        self.hovered_interactable = {"type": "world_torch", "torch": t, "name": t["name"]}
                        self.hovered_rect = rect

        item_names = {
            TileType.ITEM_DAGGER.value: "Sword", 
            TileType.ITEM_KEY.value: "Brass Key", 
            TileType.ITEM_KEY_SILVER.value: "Silver Key", 
            TileType.ITEM_KEY_GOLD.value: "Gold Key", 
            TileType.ITEM_HEALTH_POTION.value: "Health Potion", 
            TileType.ITEM_FOOD.value: "Mana Potion", 
            TileType.ITEM_STAMINA_POTION.value: "Stamina Potion",
            TileType.ITEM_ARTIFACT.value: "Mystic Artifact", 
            TileType.ITEM_UNLIT_TORCH.value: "Unlit Torch", 
            TileType.ITEM_STAFF.value: "Mystic Staff",
            TileType.ITEM_KEY_DUNGEON.value: "Rusty Key",     
            TileType.ITEM_KEY_RUSTY_2.value: "Rusty Key 2"    
        }
        for item in self.world_items:
            dist = math.hypot(self.player_x - item['x'], self.player_y - item['y'])
            if dist < 120:
                dx, dy = item['x'] - self.player_x, item['y'] - self.player_y
                px = dx * math.cos(-self.player_angle) - dy * math.sin(-self.player_angle)
                py = dx * math.sin(-self.player_angle) + dy * math.cos(-self.player_angle)
                if px > 0.5:
                    sx = int((py / px) * proj_plane_dist + (WIDTH / 2))
                    sprite_h = max(1, int(WALL_HEIGHT_MULTIPLIER / (px + 0.0001))) // 3
                    rect = pygame.Rect(sx - sprite_h//2, (HEIGHT//2) + sprite_h//2, sprite_h, sprite_h)
                    if rect.collidepoint(mouse_x, mouse_y):
                        self.hovered_interactable = {"type": "item", "item": item, "name": item_names.get(item['id'], "Item")}
                        self.hovered_rect = rect

        for e in self.enemies:
            dist = math.hypot(self.player_x - e['x'], self.player_y - e['y'])
            if dist < 250:
                dx, dy = e['x'] - self.player_x, e['y'] - self.player_y
                px = dx * math.cos(-self.player_angle) - dy * math.sin(-self.player_angle)
                py = dx * math.sin(-self.player_angle) + dy * math.cos(-self.player_angle)
                if px > 0.5:
                    ray_idx = int(((py / px) * proj_plane_dist + (WIDTH / 2)) / (WIDTH / NUM_RAYS))
                    if 0 <= ray_idx < NUM_RAYS and px < self.depth_buffer[ray_idx]:
                        sx = int((py / px) * proj_plane_dist + (WIDTH / 2))
                        sprite_h = max(1, int(WALL_HEIGHT_MULTIPLIER / (px + 0.0001)))
                        rect = pygame.Rect(sx - sprite_h//2, (HEIGHT//2) - sprite_h//2, sprite_h, sprite_h)
                        if rect.collidepoint(mouse_x, mouse_y):
                            self.hovered_enemy = e

    def draw_weather(self):
        if self.weather_intensity <= 0: return
        color, particle_height = RAIN_COLOR, 20 if 'heavy' in self.weather_type else 14
        if self.in_interior:
            color = (65, 135, 245) 
            particle_height = 5
        elif self.weather_type == 'snow': color, particle_height = SNOW_COLOR, 4
        elif 'sand' in self.weather_type: color, particle_height = DUST_COLOR, 6
        
        cos_a = math.cos(-self.player_angle)
        sin_a = math.sin(-self.player_angle)
        proj_plane_dist = WIDTH / (2 * math.tan(FOV/2))
        ray_width = WIDTH / NUM_RAYS

        for p in self.particles:
            dx, dy = p['x'] - self.player_x, p['y'] - self.player_y
            px = dx * cos_a - dy * sin_a
            py = dx * sin_a + dy * cos_a
            if px > 2:
                wind_offset = p.get('wind_accel', 0) * 2 if ('sand' in self.weather_type and not self.in_interior) else 0
                sx = (py / px) * proj_plane_dist + (WIDTH / 2) + wind_offset
                idx = int(sx / ray_width)
                if 0 <= sx < WIDTH and 0 <= idx < NUM_RAYS and px < self.depth_buffer[idx]:
                    pygame.draw.rect(self.screen, color, (sx, (HEIGHT // 2) + (p['z'] * (240 / px)), 2, particle_height))
                    
        if 'sand' in self.weather_type and not self.in_interior:
            if not hasattr(self, 'sand_overlay'):
                self.sand_overlay = pygame.Surface((WIDTH, HEIGHT))
                self.sand_overlay.fill(DUST_COLOR)
            
            self.sand_overlay.set_alpha(int(150 * self.weather_intensity))
            self.screen.blit(self.sand_overlay, (0, 0))

    def draw_leaves(self):
        if self.in_interior or not hasattr(self, 'leaves') or not self.leaves: return
        
        cos_a = math.cos(-self.player_angle)
        sin_a = math.sin(-self.player_angle)
        proj_plane_dist = WIDTH / (2 * math.tan(FOV/2))
        ray_width = WIDTH / NUM_RAYS

        for leaf in self.leaves:
            dx, dy = leaf['x'] - self.player_x, leaf['y'] - self.player_y
            px = dx * cos_a - dy * sin_a
            py = dx * sin_a + dy * cos_a
            
            if px > 2:
                wind_offset = self.wind_effect * 2 
                sx = (py / px) * proj_plane_dist + (WIDTH / 2) + wind_offset
                idx = int(sx / ray_width)
                if 0 <= sx < WIDTH and 0 <= idx < NUM_RAYS and px < self.depth_buffer[idx]:
                    if self.leaf_base_sprite:
                        leaf_w = max(8, int(80 / px))
                        angle = int(math.degrees(leaf['sway_phase'])) % 360
                        angle = (angle // 15) * 15
                        cache_key = (leaf_w, angle)
                        if cache_key not in self.leaf_cache:
                            scaled_leaf = pygame.transform.scale(self.leaf_base_sprite, (leaf_w, leaf_w))
                            self.leaf_cache[cache_key] = pygame.transform.rotate(scaled_leaf, angle)
                            
                        rot_leaf = self.leaf_cache[cache_key]
                        self.screen.blit(rot_leaf, (sx - rot_leaf.get_width()//2, (HEIGHT // 2) + (leaf['z'] * (240 / px))))
                    else:
                        size = max(4, int(40 / px))
                        flutter = max(2, int(size * abs(math.sin(leaf['sway_phase']))))
                        pygame.draw.rect(self.screen, (34, 139, 34), (sx, (HEIGHT // 2) + (leaf['z'] * (240 / px)), flutter, size))

    def update_leaves(self):
        # Only update if we are outside
        if self.in_interior: return

        # Spawning logic: Check trees and occasionally spawn a leaf
        if len(self.leaves) < 60 and self.tree_positions:
            if random.random() < 0.05:
                tx, ty = random.choice(self.tree_positions)
                self.leaves.append({
                    'x': tx + random.uniform(-20, 20),
                    'y': ty + random.uniform(-20, 20),
                    'z': -100, # Start near tree canopy
                    'speed': random.uniform(0.5, 1.5), # Vertical speed (downwards)
                    'sway_speed': random.uniform(0.02, 0.05),
                    'sway_phase': random.uniform(0, math.pi * 2),
                    'drift': random.uniform(-0.5, 0.5)
                })

        # Physics/Movement logic
        for leaf in self.leaves[:]:
            # Apply gravity (falling)
            leaf['z'] += leaf['speed'] 
            
            # Apply Sway/Drift
            leaf['x'] += math.sin(leaf['sway_phase']) * 1.5 + self.global_wind + leaf['drift']
            leaf['y'] += math.cos(leaf['sway_phase']) * 1.5 + self.global_wind
            leaf['sway_phase'] += leaf['sway_speed']
            
            # Cleanup
            if leaf['z'] > 200: # Reached ground/floor
                self.leaves.remove(leaf)

    def draw_hud(self):
        t = pygame.time.get_ticks() / 600.0
        gold_pulse = int(180 + 75 * math.sin(t))
        gold_border_col = (gold_pulse, 215, 0)
        solid_gold = (255, 215, 0)
        
        hud_w, hud_h = 240, 115
        hud_x, hud_y = 10, 10
        
        pygame.draw.rect(self.screen, (10, 10, 10), (hud_x, hud_y, hud_w, hud_h))
        pygame.draw.rect(self.screen, gold_border_col, (hud_x, hud_y, hud_w, hud_h), 4)

        hp_ratio = min(1.0, self.health / self.max_health)
        mana_ratio = min(1.0, self.mana / self.max_mana)
        stam_ratio = min(1.0, self.stamina / self.max_stamina)

        pygame.draw.rect(self.screen, (40, 20, 20), (20, 20, 200, 20))
        pygame.draw.rect(self.screen, (220, 50, 50), (20, 20, int(200 * hp_ratio), 20))
        pygame.draw.rect(self.screen, solid_gold, (20, 20, 200, 20), 2)
        
        pygame.draw.rect(self.screen, (20, 20, 40), (20, 45, 200, 20))
        pygame.draw.rect(self.screen, (100, 150, 255), (20, 45, int(200 * mana_ratio), 20))
        pygame.draw.rect(self.screen, solid_gold, (20, 45, 200, 20), 2)
        
        pygame.draw.rect(self.screen, (40, 40, 20), (20, 70, 200, 15))
        pygame.draw.rect(self.screen, (255, 255, 100), (20, 70, int(200 * stam_ratio), 15))
        pygame.draw.rect(self.screen, solid_gold, (20, 70, 200, 15), 2)
        
        self.screen.blit(self.font.render(f"HP: {int(self.health)}/{self.max_health}", True, (255, 255, 255)), (25, 22))
        self.screen.blit(self.font.render(f"Mana: {int(self.mana)}/{self.max_mana}", True, (255, 255, 255)), (25, 47))
        self.screen.blit(self.font.render(f"Stamina: {int(self.stamina)}/{self.max_stamina}", True, (255, 255, 255)), (25, 70))
        self.screen.blit(self.font.render(f"LVL: {self.level} ({self.xp}/{self.xp_to_next_level} XP)", True, solid_gold), (20, 95))
        
        if self.stat_points > 0:
            prompt = self.font_small_bold.render("Press 'C' to allocate Stat Points!", True, (255, 255, 100))
            self.screen.blit(prompt, (hud_x, hud_y + hud_h + 10))

        if self.consume_message_timer > 0:
            msg_surf = self.font_msg.render(self.consume_message, True, (100, 255, 100))
            msg_rect = msg_surf.get_rect(center=(WIDTH // 2, HEIGHT - 110))
            self.screen.blit(self.font_msg.render(self.consume_message, True, (0, 0, 0)), (msg_rect.x + 2, msg_rect.y + 2))
            self.screen.blit(msg_surf, msg_rect)

    def draw_stat_screen(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        panel_w, panel_h = 400, 360
        px, py = WIDTH // 2 - panel_w // 2, HEIGHT // 2 - panel_h // 2
        
        pygame.draw.rect(self.screen, (30, 30, 35), (px, py, panel_w, panel_h))
        pygame.draw.rect(self.screen, (200, 180, 100), (px, py, panel_w, panel_h), 3)
        
        title = self.font_msg.render("CHARACTER SHEET", True, (255, 215, 0))
        self.screen.blit(title, (px + panel_w//2 - title.get_width()//2, py + 20))
        
        lvl = self.font.render(f"Level {self.level}   (XP: {self.xp} / {self.xp_to_next_level})", True, (200, 200, 200))
        self.screen.blit(lvl, (px + 30, py + 60))
        
        pts = self.font_small_bold.render(f"Unspent Stat Points: {self.stat_points}", True, (100, 255, 100) if self.stat_points > 0 else (150, 150, 150))
        self.screen.blit(pts, (px + 30, py + 90))
        
        self.stat_btn_rects.clear()
        
        self.screen.blit(self.font.render(f"Strength: {self.strength}", True, (255, 100, 100)), (px + 30, py + 140))
        self.screen.blit(self.font_small_bold.render(f"Melee Damage: {self.melee_dmg}", True, (150, 150, 150)), (px + 30, py + 160))
        if self.stat_points > 0:
            btn_str = pygame.Rect(px + panel_w - 60, py + 140, 30, 30)
            pygame.draw.rect(self.screen, (50, 150, 50), btn_str)
            self.screen.blit(self.font_msg.render("+", True, (255,255,255)), (btn_str.x + 8, btn_str.y + 2))
            self.stat_btn_rects.append(("STR", btn_str))
            
        self.screen.blit(self.font.render(f"Intelligence: {self.intelligence}", True, (100, 100, 255)), (px + 30, py + 200))
        self.screen.blit(self.font_small_bold.render(f"Magic Dmg: {self.magic_dmg} | Max Mana: {self.max_mana}", True, (150, 150, 150)), (px + 30, py + 220))
        if self.stat_points > 0:
            btn_int = pygame.Rect(px + panel_w - 60, py + 200, 30, 30)
            pygame.draw.rect(self.screen, (50, 150, 50), btn_int)
            self.screen.blit(self.font_msg.render("+", True, (255,255,255)), (btn_int.x + 8, btn_int.y + 2))
            self.stat_btn_rects.append(("INT", btn_int))
            
        self.screen.blit(self.font.render(f"Endurance: {self.endurance}", True, (255, 255, 100)), (px + 30, py + 260))
        self.screen.blit(self.font_small_bold.render(f"Max Health: {self.max_health} | Max Stamina: {self.max_stamina}", True, (150, 150, 150)), (px + 30, py + 280))
        if self.stat_points > 0:
            btn_end = pygame.Rect(px + panel_w - 60, py + 260, 30, 30)
            pygame.draw.rect(self.screen, (50, 150, 50), btn_end)
            self.screen.blit(self.font_msg.render("+", True, (255,255,255)), (btn_end.x + 8, btn_end.y + 2))
            self.stat_btn_rects.append(("END", btn_end))
            
        btn_close = pygame.Rect(px + panel_w//2 - 50, py + 320, 100, 30)
        pygame.draw.rect(self.screen, (150, 50, 50), btn_close)
        pygame.draw.rect(self.screen, (255, 100, 100), btn_close, 2)
        c_txt = self.font_small_bold.render("CLOSE", True, (255, 255, 255))
        self.screen.blit(c_txt, (btn_close.x + 25, btn_close.y + 6))
        self.stat_btn_rects.append(("CLOSE", btn_close))

    def draw(self):
        h, w = len(self.map), len(self.map[0])
        
        sky_h = HEIGHT // 2
        top_sky = self.get_sky_color()
        horizon_sky = tuple(min(255, int(c * 1.35)) for c in top_sky) if 400 < self.time < 2000 else tuple(max(0, int(c * 0.5)) for c in top_sky)
        for sky_y in range(0, sky_h, 2):
            t = sky_y / sky_h
            line_color = (
                int(top_sky[0] * (1 - t) + horizon_sky[0] * t),
                int(top_sky[1] * (1 - t) + horizon_sky[1] * t),
                int(top_sky[2] * (1 - t) + horizon_sky[2] * t)
            )
            pygame.draw.rect(self.screen, line_color, (0, sky_y, WIDTH, 2))

        if not self.in_interior:
            self.draw_stars(); self.draw_sun_moon()
            for c in self.clouds:
                scaled_sprite = self.get_scaled_cloud_sprite(c.get('current_scale', c['scale'])).copy()
                if 'rain' in self.weather_type: scaled_sprite.fill((80, 80, 80), special_flags=pygame.BLEND_RGB_MULT)
                scaled_sprite.set_alpha(int(c['alpha']))
                cw = scaled_sprite.get_width()
                self.screen.blit(scaled_sprite, (c['x'] - 200, c['y']))
                if c['x'] - 200 + cw < WIDTH: self.screen.blit(scaled_sprite, (c['x'] - 200 + WIDTH + 200, c['y']))
        
        self.sprites = []
        for y in range(h):
            for x in range(w):
                val = self.map[y][x]
                if val == TileType.TREE.value:
                    tex = self.tree_leafy_sprites[(x * 73 + y * 31) % len(self.tree_leafy_sprites)]
                    self.sprites.append({'x': x * TILE_SIZE + 32, 'y': y * TILE_SIZE + 32, 'tex': tex})
                elif val == TileType.DEAD_TREE.value: self.sprites.append({'x': x * TILE_SIZE + 32, 'y': y * TILE_SIZE + 32, 'tex': self.tree_dead_sprite})
                elif val == TileType.BUSH.value: 
                    tex = self.bush_sprites[(x * 53 + y * 89) % len(self.bush_sprites)]
                    self.sprites.append({'x': x * TILE_SIZE + 32, 'y': y * TILE_SIZE + 32, 'tex': tex})
                elif val == TileType.ROCK.value: self.sprites.append({'x': x * TILE_SIZE + 32, 'y': y * TILE_SIZE + 32, 'tex': self.rock_sprite})
                elif val == TileType.STANDING_TORCH.value: self.sprites.append({'x': x * TILE_SIZE + 32, 'y': y * TILE_SIZE + 32, 'tex': self.torch_sprite})
        
        for item in self.world_items:
            tex = None
            if item['id'] == TileType.ITEM_DAGGER.value: tex = self.drop_sword_sprite
            elif item['id'] == TileType.ITEM_KEY.value: tex = self.drop_key_sprite
            elif item['id'] == TileType.ITEM_KEY_SILVER.value: tex = self.drop_key_silver_sprite
            elif item['id'] == TileType.ITEM_KEY_GOLD.value: tex = self.drop_key_gold_sprite
            elif item['id'] == TileType.ITEM_HEALTH_POTION.value: tex = self.drop_health_sprite
            elif item['id'] == TileType.ITEM_FOOD.value: tex = self.drop_food_sprite
            elif item['id'] == TileType.ITEM_STAMINA_POTION.value: tex = self.drop_stamina_sprite
            elif item['id'] == TileType.ITEM_ARTIFACT.value: tex = self.drop_artifact_sprite
            elif item['id'] == TileType.ITEM_UNLIT_TORCH.value: tex = self.ui_icons.get("unlit_torch")
            elif item['id'] == TileType.ITEM_STAFF.value: tex = self.ui_icons.get("staff")
            elif item['id'] == TileType.ITEM_KEY_RUSTY_2.value: tex = self.drop_key_rusty_2_sprite
            elif item['id'] == TileType.ITEM_KEY_DUNGEON.value: tex = self.ui_icons.get("key_dungeon")
            if tex: self.sprites.append({'x': item['x'], 'y': item['y'], 'tex': tex, 'is_item': True})
            
        for proj in self.projectiles:
            self.sprites.append({'x': proj['x'], 'y': proj['y'], 'tex': proj['tex'], 'is_item': True})
            
        for e in self.enemies:
            self.sprites.append({'x': e['x'], 'y': e['y'], 'tex': e['tex'], 'is_enemy': True, 'ref': e})
            
        proj_plane_dist = (WIDTH / 2) / math.tan(FOV / 2)
        ray_dir_x0, ray_dir_y0 = math.cos(self.player_angle - FOV / 2), math.sin(self.player_angle - FOV / 2)
        ray_dir_x1, ray_dir_y1 = math.cos(self.player_angle + FOV / 2), math.sin(self.player_angle + FOV / 2)
        step_x, step_y = 8, 4
        cmap = self.floor_color_maps[self.floor_texture_type.name]
        
        player_light_intensity = 0
        if self.torch_timer > 0:
            player_light_intensity = int(220 * self.global_flicker * min(1.0, self.torch_timer / 120.0))
            
        for y in range(HEIGHT // 2, HEIGHT, step_y):
            p = y - HEIGHT // 2
            if p == 0: p = 1
            row_distance = (32.0 * proj_plane_dist) / p
            floor_step_x = row_distance * (ray_dir_x1 - ray_dir_x0) / WIDTH * step_x
            floor_step_y = row_distance * (ray_dir_y1 - ray_dir_y0) / WIDTH * step_x
            floor_x, floor_y = self.player_x + row_distance * ray_dir_x0, self.player_y + row_distance * ray_dir_y0
            shade = max(0.1, min(1.0, p / (HEIGHT // 2)))
            amb_int = int(255 * shade * (self.ambient_light / 255.0))
            for x in range(0, WIDTH, step_x):
                gx, gy = int(floor_x // TILE_SIZE), int(floor_y // TILE_SIZE)
                tx, ty = int(floor_x) & (TILE_SIZE - 1), int(floor_y) & (TILE_SIZE - 1)
                torch_light = self.lightmap[max(0, min(h-1, gy))][max(0, min(w-1, gx))] if 0 <= gx < w and 0 <= gy < h else 0
                torch_light *= self.global_flicker 
                
                p_dist = math.hypot(floor_x - self.player_x, floor_y - self.player_y)
                p_light = max(0, player_light_intensity - (p_dist * 0.8)) if player_light_intensity > 0 else 0
                
                proj_light = 0
                for proj in self.projectiles:
                    dist = math.hypot(floor_x - proj['x'], floor_y - proj['y'])
                    if dist < 150:  proj_light += max(0, 200 - (dist * 1.5))
                
                final_int = max(0, min(255, amb_int + int((torch_light + p_light + proj_light) * shade)))
                color = cmap[tx][ty]
                pygame.draw.rect(self.screen, ((color[0]*final_int)>>8, (color[1]*final_int)>>8, (color[2]*final_int)>>8), (x, y, step_x, step_y))
                floor_x += floor_step_x; floor_y += floor_step_y
                
        sun_progress = (self.time - 400) / 1200.0  
        sun_angle = math.pi * sun_progress
        sun_vec_x, sun_vec_y = math.cos(sun_angle), -math.sin(sun_angle)
        shadow_intensity = 1.0
        if 'rain' in self.weather_type or 'sand' in self.weather_type:
            shadow_intensity = max(0.0, 1.0 - (self.weather_intensity * 1.5))
        sun_intensity = (math.sin(sun_angle) * 100 * shadow_intensity) if 400 < self.time < 1600 else 0 
        
        start_a = self.player_angle - FOV / 2
        transparent_tiles = (TileType.TREE.value, TileType.DEAD_TREE.value, TileType.BUSH.value, TileType.ROCK.value, TileType.STANDING_TORCH.value, TileType.ITEM_UNLIT_TORCH.value)
        
        for ray in range(NUM_RAYS):
            angle = start_a + ray * DELTA_ANGLE
            sin_a, cos_a = math.sin(angle), math.cos(angle)
            for d in range(1, MAX_DEPTH, 3): 
                tx, ty = self.player_x + d * cos_a, self.player_y + d * sin_a
                gx, gy = int(tx/TILE_SIZE), int(ty/TILE_SIZE)
                if 0 <= gx < w and 0 <= gy < h:
                    tile_val = self.map[gy][gx]
                    if tile_val >= 1 and tile_val not in transparent_tiles:
                        dist = d * math.cos(self.player_angle - angle)
                        self.depth_buffer[ray] = dist
                        wh = max(1, int(WALL_HEIGHT_MULTIPLIER / (dist + 0.0001)))
                        hit_x_offset, hit_y_offset = tx - (gx * TILE_SIZE + TILE_SIZE/2), ty - (gy * TILE_SIZE + TILE_SIZE/2)
                        if abs(hit_x_offset) > abs(hit_y_offset):
                            normal_x, normal_y, off = (1 if hit_x_offset > 0 else -1), 0, ty % TILE_SIZE
                        else:
                            normal_x, normal_y, off = 0, (1 if hit_y_offset > 0 else -1), tx % TILE_SIZE
                        sun_dot = normal_x * sun_vec_x + normal_y * sun_vec_y
                        added_sunlight = max(0, sun_dot) * sun_intensity
                        torch_light = self.lightmap[gy][gx] * self.global_flicker 
                        dist_shade = max(0, min(1.0, 1.0 - (dist / (MAX_DEPTH*0.8))))
                        
                        p_light = max(0, player_light_intensity - (dist * 0.8)) if player_light_intensity > 0 else 0
                        
                        proj_light = 0
                        for proj in self.projectiles:
                            p_dist = math.hypot(tx - proj['x'], ty - proj['y'])
                            if p_dist < 150: proj_light += max(0, 200 - (p_dist * 1.5))
                        
                        if tile_val == TileType.WALL_TORCH.value: total_light = max(0, min(255, int(255 * self.global_flicker))) 
                        else: total_light = max(0, min(255, int((self.ambient_light + added_sunlight + torch_light + p_light + proj_light) * dist_shade)))
                        
                        off_clamped = max(0, min(TILE_SIZE - 1, int(off)))
                        
                        if self.in_interior: wall_slice = self.wall_textures["CAVE_ROCK"].subsurface(off_clamped, 0, 1, TILE_SIZE)
                        elif tile_val == TileType.DOOR.value: wall_slice = self.door_tex.subsurface(off_clamped, 0, 1, TILE_SIZE)
                        elif tile_val == TileType.DOOR_SILVER.value: wall_slice = self.door_silver_tex.subsurface(off_clamped, 0, 1, TILE_SIZE)
                        elif tile_val == TileType.DOOR_GOLD.value: wall_slice = self.door_gold_tex.subsurface(off_clamped, 0, 1, TILE_SIZE)
                        elif tile_val == TileType.STAIRS.value: wall_slice = self.wall_textures[TileType.STAIRS.value].subsurface(off_clamped, 0, 1, TILE_SIZE)
                        elif tile_val in self.wall_textures: wall_slice = self.wall_textures[tile_val].subsurface(off_clamped, 0, 1, TILE_SIZE)
                        else: wall_slice = self.wall_textures[TileType.WALL_BRICK.value].subsurface(off_clamped, 0, 1, TILE_SIZE)
                        
                        col_s = pygame.transform.scale(wall_slice, (int(WIDTH/NUM_RAYS)+1, wh))
                        m = max(0, min(255, total_light)) / 255.0
                        col_s.fill((int(m*255), int(m*255), int(m*255)), special_flags=pygame.BLEND_RGB_MULT)
                        self.screen.blit(col_s, (ray * (WIDTH / NUM_RAYS), HEIGHT // 2 - wh // 2))
                        break
            else:
                self.depth_buffer[ray] = MAX_DEPTH
                
        for sprite in self.sprites: sprite['dist'] = math.hypot(self.player_x - sprite['x'], self.player_y - sprite['y'])
        self.sprites.sort(key=lambda s: s['dist'], reverse=True)
        
        for sprite in self.sprites:
            dx, dy = sprite['x'] - self.player_x, sprite['y'] - self.player_y
            px = dx * math.cos(-self.player_angle) - dy * math.sin(-self.player_angle)
            py = dx * math.sin(-self.player_angle) + dy * math.cos(-self.player_angle)
            if px > 0.5: 
                sx = int((py / px) * proj_plane_dist + (WIDTH / 2))
                orig_h = max(1, int(WALL_HEIGHT_MULTIPLIER / (px + 0.0001)))
                
                if sprite.get('tex') in self.tree_leafy_sprites or sprite.get('tex') == self.tree_dead_sprite:
                    seed_val = int(sprite['x'] * 19 + sprite['y'] * 47)
                    height_scale = 1.8 + (seed_val % 60) / 100.0  
                    sprite_h = int(orig_h * height_scale)
                elif sprite.get('is_item'): 
                    sprite_h = orig_h // 4
                elif sprite.get('is_enemy') and sprite.get('ref', {}).get('scale'):
                    sprite_h = int(orig_h * sprite['ref']['scale'])
                else: 
                    sprite_h = orig_h
                    
                floor_y = (HEIGHT // 2) + (orig_h // 2)
                
                if sprite.get('tex') in self.tree_leafy_sprites or sprite.get('tex') == self.tree_dead_sprite:
                    floor_y += int(orig_h * 0.05) 
                else:
                    floor_y += int(sprite_h * 0.15) 
                v_offset = floor_y - sprite_h
                
                if 0 < sprite_h < HEIGHT * 3:
                    ds_x, de_x = sx - sprite_h // 2, sx + sprite_h // 2
                    if de_x > 0 and ds_x < WIDTH:
                        scaled_sprite = pygame.transform.scale(sprite['tex'], (sprite_h, sprite_h))
                        gx, gy = int(sprite['x']//TILE_SIZE), int(sprite['y']//TILE_SIZE)
                        torch_l = (self.lightmap[gy][gx] * self.global_flicker) if 0<=gx<w and 0<=gy<h else 0
                        p_light = max(0, player_light_intensity - (sprite['dist'] * 0.8)) if player_light_intensity > 0 else 0
                        
                        proj_light = 0
                        for proj in self.projectiles:
                            p_dist = math.hypot(sprite['x'] - proj['x'], sprite['y'] - proj['y'])
                            if p_dist < 150: proj_light += max(0, 200 - (p_dist * 1.5))
                            
                        m = min(255, (self.ambient_light + torch_l + p_light + proj_light)) / 255.0 * max(0, min(1.0, 1.0 - (px / MAX_DEPTH)))
                        c_val = max(0, min(255, int(m * 255)))
                        
                        if sprite.get('is_boss'):
                            pulse = int(200 + 55 * math.sin(pygame.time.get_ticks() / 150.0))
                            scaled_sprite.fill((pulse, pulse, pulse, 255), special_flags=pygame.BLEND_RGBA_MULT)
                        elif sprite['tex'] != self.torch_sprite and sprite['tex'] != self.ui_icons.get("lit_torch"): 
                            scaled_sprite.fill((c_val, c_val, c_val, 255), special_flags=pygame.BLEND_RGBA_MULT)
                        else:
                            f_val = max(0, min(255, int(255 * self.global_flicker)))
                            scaled_sprite.fill((f_val, f_val, f_val, 255), special_flags=pygame.BLEND_RGBA_MULT)
                        
                        step = int(WIDTH / NUM_RAYS) + 1

                        for screen_x in range(max(0, ds_x), min(WIDTH, de_x), step):
                            ray_idx = int(screen_x / (WIDTH / NUM_RAYS))
                            if 0 <= ray_idx < NUM_RAYS and px < self.depth_buffer[ray_idx]:
                                slice_rect = pygame.Rect(max(0, min(sprite_h - step, int((screen_x - ds_x) * (sprite_h / (de_x - ds_x))))), 0, step, sprite_h)
                                self.screen.blit(scaled_sprite, (screen_x, v_offset), slice_rect)
                        
                        if sprite.get('is_enemy') and 'ref' in sprite:
                            e = sprite['ref']
                            ray_idx = int(sx / (WIDTH / NUM_RAYS))
                            if 0 <= ray_idx < NUM_RAYS and px < self.depth_buffer[ray_idx] and sprite['dist'] < 250:
                                hp_ratio = max(0.0, min(1.0, e['hp'] / e['max_hp']))
                                bar_w = 40
                                bar_h = 6
                                bx = sx - bar_w//2
                                by = v_offset - 25
                                pygame.draw.rect(self.screen, (0, 0, 0), (bx - 2, by - 2, bar_w + 4, bar_h + 4))
                                pygame.draw.rect(self.screen, (200, 0, 0), (bx, by, bar_w, bar_h))
                                pygame.draw.rect(self.screen, (0, 220, 0), (bx, by, int(bar_w * hp_ratio), bar_h))
                                lvl_txt = self.font_small_bold.render(f"Lv.{e.get('level', 1)}", True, (255, 215, 0))
                                lvl_shadow = self.font_small_bold.render(f"Lv.{e.get('level', 1)}", True, (0, 0, 0))
                                self.screen.blit(lvl_shadow, (bx - 34, by - 4))
                                self.screen.blit(lvl_txt, (bx - 35, by - 5))

        for spark in self.sparks:
            pygame.draw.circle(self.screen, spark['color'], (int(spark['x']), int(spark['y'])), spark['size'])

        equipped_weapon = self.inventory.get_equipped_weapon()
        if equipped_weapon and not self.level_complete:
            wep_img = self.ui_icons.get("staff") if equipped_weapon["name"] == "Mystic Staff" else self.weapon_idle_img
            if wep_img:
                if equipped_weapon["name"] == "Sword" and self.attack_swing > 0:
                    progress = self.attack_swing
                    if progress > 0.8:  
                        t = (1.0 - progress) / 0.2
                        angle = -18 * t
                        x_offset = 25 * t
                        y_offset = -15 * t
                    elif progress > 0.2:  
                        t = (0.8 - progress) / 0.6
                        angle = -18 + (105 * t)    
                        x_offset = 25 - (155 * t)  
                        y_offset = -15 + (65 * t)  
                    else:  
                        t = progress / 0.2
                        angle = 87 * t
                        x_offset = -130 * t
                        y_offset = 50 * t
                    rotated_sword = pygame.transform.rotate(wep_img, angle)
                    p_x, p_y = 65, 335
                    c_x, c_y = 200, 200
                    dx, dy = p_x - c_x, p_y - c_y
                    rad = math.radians(-angle)
                    rx = dx * math.cos(rad) - dy * math.sin(rad)
                    ry = dx * math.sin(rad) + dy * math.cos(rad)
                    screen_pivot_x = WIDTH - 305 + x_offset
                    screen_pivot_y = HEIGHT - 65 + y_offset
                    rot_rect = rotated_sword.get_rect(center=(screen_pivot_x - rx, screen_pivot_y - ry))
                    self.screen.blit(rotated_sword, rot_rect.topleft)
                elif not self.inventory.visible: 
                    bob_offset = math.sin(pygame.time.get_ticks() * 0.004) * 4 if not self.game_over else 0
                    if equipped_weapon["name"] == "Mystic Staff":
                        staff_scaled = pygame.transform.scale(wep_img, (200, 200))
                        self.screen.blit(staff_scaled, (WIDTH - 250, HEIGHT - 150 + int(bob_offset)))
                    else:
                        self.screen.blit(wep_img, (WIDTH - 380, HEIGHT - 360 + int(bob_offset)))

        self.draw_weather()
        self.draw_leaves()
        self.draw_hud()
        self.draw_minimap()
        
        if not self.level_complete: self.action_bar.draw(self.screen, self.inventory, self.font)
        self.inventory.draw(self.screen, pygame.mouse.get_pos(), self.font)
        
        if self.show_stat_screen:
            self.draw_stat_screen()
        elif self.hovered_rect and not self.inventory.visible and not self.level_complete:
            name = self.hovered_interactable.get("name", "Object")
            self.draw_ss2_bracket(self.hovered_rect, name)

        if self.drag_item:
            mx, my = pygame.mouse.get_pos()
            icon = None
            if self.drag_source[0] == "inv": icon = self.inventory.get_icon_for_item(self.drag_item)
            elif self.drag_source[0] == "ab": icon = self.drag_item["icon"]
            if icon:
                icon_scaled = pygame.transform.scale(icon, (40, 40))
                self.screen.blit(icon_scaled, (mx - 20, my - 20))
                
        mx, my = pygame.mouse.get_pos()
        cursor_color = (50, 255, 150) 
        pygame.draw.polygon(self.screen, cursor_color, [(mx, my), (mx + 12, my + 12), (mx + 5, my + 12), (mx + 5, my + 18), (mx, my + 18)])
        pygame.draw.polygon(self.screen, (20, 100, 50), [(mx, my), (mx + 12, my + 12), (mx + 5, my + 12), (mx + 5, my + 18), (mx, my + 18)], 1)
        
        if self.game_over:
            self.screen.blit(self.game_over_overlay, (0, 0))
            text = self.font_massive.render("YOU DIED", True, (255, 50, 50))
            self.screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - text.get_height()//2))
        elif self.level_complete:
            self.screen.blit(self.level_complete_overlay, (0, 0))
            text = self.font_massive_win.render("DUNGEON ESCAPED", True, (255, 215, 0))
            self.screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - text.get_height()//2))

    def perform_melee_attack(self):
        equipped = self.inventory.get_equipped_weapon()
        if equipped and equipped["name"] == "Mystic Staff":
            if self.mana >= 1: 
                self.mana -= 1
                self.attack_swing = 1.0
                if len(self.projectiles) > 4: self.projectiles.pop(0) 
                mouse_x, mouse_y = pygame.mouse.get_pos()
                angle_offset = ((mouse_x - (WIDTH / 2)) / (WIDTH / 2)) * (FOV / 2)
                shoot_angle = self.player_angle + angle_offset
                forward_x = math.cos(self.player_angle) * 15
                forward_y = math.sin(self.player_angle) * 15
                right_x = math.cos(self.player_angle + math.pi/2) * 10
                right_y = math.sin(self.player_angle + math.pi/2) * 10
                start_x = self.player_x + forward_x + right_x
                start_y = self.player_y + forward_y + right_y
                self.projectiles.append({"x": start_x, "y": start_y, "angle": shoot_angle, "speed": 14.0, "tex": self.ui_icons.get("fireball"), "dmg": self.magic_dmg})
                if self.sfx.get("fireball"): self.sfx["fireball"].play()
            else:
                self.consume_message = "Low Mana for Staff!"
                self.consume_message_timer = 60
                if self.sfx.get("error"): self.sfx["error"].play()
            return
        if self.stamina >= 15:
            self.stamina -= 15
            self.attack_swing = 1.0 
            if self.sfx.get("use"): self.sfx["use"].play()
            check_dist = 50
            tx = self.player_x + math.cos(self.player_angle) * check_dist
            ty = self.player_y + math.sin(self.player_angle) * check_dist
            gx, gy = int(tx / TILE_SIZE), int(ty / TILE_SIZE)
            hit_metallic_target = False
            if 0 <= gx < len(self.map[0]) and 0 <= gy < len(self.map):
                tile_val = self.map[gy][gx]
                if tile_val in [TileType.WALL_BRICK_CRACKED.value, TileType.WALL_STONE_CRACKED.value, TileType.WALL_WOOD_CRACKED.value]:
                    self.map[gy][gx] = TileType.EMPTY.value
                    if self.sfx.get("door"): self.sfx["door"].play() 
                    spark_center_x, spark_center_y = WIDTH // 2 + 60, HEIGHT // 2 + 80
                    for _ in range(16):
                        self.sparks.append({
                            'x': spark_center_x + random.randint(-15, 15),
                            'y': spark_center_y + random.randint(-15, 15),
                            'vx': random.uniform(-4.5, 4.5),
                            'vy': random.uniform(-7.0, 1.5),
                            'color': (150, 150, 150), 
                            'size': random.randint(3, 6),
                            'life': random.randint(20, 40)
                        })
                    return 
                if tile_val not in [TileType.EMPTY.value, TileType.WALL_BRICK.value, TileType.WALL_STONE.value, TileType.FORCE_FIELD.value]:
                    hit_metallic_target = True
            if hit_metallic_target:
                if self.sfx.get("hit_metallic"): self.sfx["hit_metallic"].play()
                spark_center_x, spark_center_y = WIDTH // 2 + 60, HEIGHT // 2 + 80
                for _ in range(16):
                    self.sparks.append({
                        'x': spark_center_x + random.randint(-15, 15),
                        'y': spark_center_y + random.randint(-15, 15),
                        'vx': random.uniform(-4.5, 4.5),
                        'vy': random.uniform(-7.0, 1.5),
                        'color': random.choice([(255, 225, 40), (255, 130, 20), (255, 255, 220)]),
                        'size': random.randint(2, 4),
                        'life': random.randint(15, 35)
                    })
            for e in self.enemies:
                dist = math.hypot(self.player_x - e['x'], self.player_y - e['y'])
                if dist < 80: 
                    angle_to_e = math.atan2(e['y'] - self.player_y, e['x'] - self.player_x)
                    diff = (angle_to_e - self.player_angle + math.pi) % (2*math.pi) - math.pi
                    if abs(diff) < FOV/2: e['hp'] -= self.melee_dmg 
        else:
            self.consume_message = "Too tired to swing!"
            self.consume_message_timer = 60
            if self.sfx.get("error"): self.sfx["error"].play()

    def use_hotkey_action(self, slot):
        if slot["cd"] > 0 or self.mana < slot["cost"] or slot["name"] == "Empty": return
        if slot["type"] == "melee":
            self.mana -= slot["cost"]
            slot["cd"] = slot["max_cd"] 
            self.perform_melee_attack()
        elif slot["type"] == "magic":
            if slot["name"] == "Spell: Heal":
                self.mana -= slot["cost"]
                slot["cd"] = slot["max_cd"]
                self.health = min(self.max_health, self.health + 50)
                if self.sfx.get("drink"): self.sfx["drink"].play()
                self.consume_message = "Healed 50 HP!"
                self.consume_message_timer = 60
            elif slot["name"] == "Spell: Frost":
                self.mana -= slot["cost"]
                slot["cd"] = slot["max_cd"] 
                if len(self.projectiles) > 4: self.projectiles.pop(0)
                mouse_x, _ = pygame.mouse.get_pos()
                angle_offset = ((mouse_x - (WIDTH / 2)) / (WIDTH / 2)) * (FOV / 2)
                shoot_angle = self.player_angle + angle_offset
                self.projectiles.append({"x": self.player_x, "y": self.player_y, "angle": shoot_angle, "speed": 16.0, "tex": self.ui_icons.get("spell_frost"), "dmg": self.magic_dmg + 10})
                if self.sfx.get("fireball"): self.sfx["fireball"].play()
            else:
                self.mana -= slot["cost"]
                slot["cd"] = slot["max_cd"] 
                if len(self.projectiles) > 4: self.projectiles.pop(0)
                mouse_x, _ = pygame.mouse.get_pos()
                angle_offset = ((mouse_x - (WIDTH / 2)) / (WIDTH / 2)) * (FOV / 2)
                shoot_angle = self.player_angle + angle_offset
                self.projectiles.append({"x": self.player_x, "y": self.player_y, "angle": shoot_angle, "speed": 12.0, "tex": self.ui_icons.get("fireball"), "dmg": self.magic_dmg})
                if self.sfx.get("fireball"): self.sfx["fireball"].play()
            self.save_game_state()
            
        elif slot["type"] in ["potion", "torch"]:
            item_idx, item = self.inventory.find_item_by_name(slot["name"])
            if item:
                if item["name"] == "Lit Torch":
                    self.torch_timer += 3600
                    item["qty"] -= 1
                    if item["qty"] <= 0:
                        self.inventory.slots[item_idx] = None
                        slot["name"] = "Empty"; slot["icon"] = None; slot["type"] = "none"
                    self.consume_message = "Torch Active!"
                    self.consume_message_timer = 60
                    if self.sfx.get("torch"): self.sfx["torch"].play()
                    slot["cd"] = slot["max_cd"]
                    self.save_game_state()
                else:
                    needs_health = item.get("health", 0) > 0 and self.health < self.max_health
                    needs_mana = item.get("mana", 0) > 0 and self.mana < self.max_mana
                    needs_stamina = item.get("stamina", 0) > 0 and self.stamina < self.max_stamina
                    if needs_health or needs_mana or needs_stamina:
                        item["qty"] -= 1
                        if item["qty"] <= 0: 
                            self.inventory.slots[item_idx] = None
                            slot["name"] = "Empty"; slot["icon"] = None; slot["type"] = "none"
                        self.health = min(self.max_health, self.health + item.get("health", 0))
                        self.mana = min(self.max_mana, self.mana + item.get("mana", 0))
                        self.stamina = min(self.max_stamina, self.stamina + item.get("stamina", 0))
                        self.consume_message = f"Used {slot['name']}!"
                        self.consume_message_timer = 60
                        if self.sfx.get("drink"): self.sfx["drink"].play()
                        slot["cd"] = slot["max_cd"]
                        self.save_game_state()
                    else:
                        self.consume_message = "Already full!"
                        self.consume_message_timer = 60
                        if self.sfx.get("error"): self.sfx["error"].play()
            else:
                self.consume_message = f"No {slot['name']} left!"
                self.consume_message_timer = 60
                if self.sfx.get("error"): self.sfx["error"].play()
                slot["name"] = "Empty"; slot["icon"] = None; slot["type"] = "none"

    def run(self):
        while True:
            if self.show_stat_screen:
                for e in pygame.event.get():
                    if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                        self.save_game_state()
                        if MIXER_READY: pygame.mixer.music.stop()
                        return
                    elif e.type == pygame.KEYDOWN and e.key == pygame.K_c:
                        self.show_stat_screen = False
                    elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                        mx, my = pygame.mouse.get_pos()
                        for btn_name, rect in self.stat_btn_rects:
                            if rect.collidepoint((mx, my)):
                                if btn_name == "CLOSE":
                                    self.show_stat_screen = False
                                elif self.stat_points > 0:
                                    if btn_name == "STR": self.strength += 1
                                    elif btn_name == "INT": self.intelligence += 1
                                    elif btn_name == "END": 
                                        self.endurance += 1
                                        self.health += 5 
                                        self.stamina += 5
                                    self.stat_points -= 1
                                    self.recalculate_max_stats()
                                    if self.sfx.get("pickup"): self.sfx["pickup"].play()
                self.draw() 
                pygame.display.flip()
                self.clock.tick(FPS)
                continue

            for e in pygame.event.get():
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE): 
                    self.save_game_state()
                    if MIXER_READY: pygame.mixer.music.stop()
                    return
                elif e.type == pygame.KEYDOWN and not self.level_complete and not self.game_over:
                    if e.key == pygame.K_i: self.inventory.toggle()
                    elif e.key == pygame.K_c: self.show_stat_screen = True
                    for slot in self.action_bar.slots:
                        if e.key == slot["key"]: self.use_hotkey_action(slot)
                elif e.type == pygame.MOUSEBUTTONDOWN and not self.level_complete and not self.game_over:
                    clicked_ui = False
                    inv_idx = self.inventory.get_slot_at(e.pos) if self.inventory.visible else None
                    ab_idx = self.action_bar.get_slot_at(e.pos)
                    if inv_idx is not None: clicked_ui = True
                    if ab_idx is not None: clicked_ui = True
                    if self.inventory.visible and self.inventory.rect.collidepoint(e.pos): clicked_ui = True
                    if ab_idx is not None:
                        if e.button == 1 and self.action_bar.slots[ab_idx]["name"] != "Empty":
                            self.drag_item = dict(self.action_bar.slots[ab_idx]) 
                            self.drag_source = ("ab", ab_idx)
                        elif e.button == 3: self.use_hotkey_action(self.action_bar.slots[ab_idx])
                    elif inv_idx is not None and self.inventory.slots[inv_idx]:
                        item = self.inventory.slots[inv_idx]
                        if e.button == 1:
                            self.drag_item = item
                            self.drag_source = ("inv", inv_idx)
                        elif e.button == 3: 
                            if item["type"] == "weapon":
                                for s in self.inventory.slots: 
                                    if s and s["type"] == "weapon": s["equipped"] = False
                                item["equipped"] = True
                                if self.sfx.get("use"): self.sfx["use"].play()
                                self.save_game_state()
                            elif item["type"] in ["consumable", "potion", "torch"]:
                                if item["name"] == "Lit Torch":
                                    self.torch_timer += 3600
                                    item["qty"] -= 1
                                    if item["qty"] <= 0: self.inventory.slots[inv_idx] = None
                                    self.consume_message = "Torch Active!"
                                    self.consume_message_timer = 60
                                    if self.sfx.get("torch"): self.sfx["torch"].play()
                                    self.save_game_state()
                                else:
                                    needs_health = item.get("health", 0) > 0 and self.health < self.max_health
                                    needs_mana = item.get("mana", 0) > 0 and self.mana < self.max_mana
                                    needs_stamina = item.get("stamina", 0) > 0 and self.stamina < self.max_stamina
                                    if needs_health or needs_mana or needs_stamina:
                                        self.health = min(self.max_health, self.health + item.get("health", 0))
                                        self.mana = min(self.max_mana, self.mana + item.get("mana", 0))
                                        self.stamina = min(self.max_stamina, self.stamina + item.get("stamina", 0))
                                        item["qty"] -= 1
                                        if item["qty"] <= 0: self.inventory.slots[inv_idx] = None
                                        self.consume_message = f"Used {item['name']}!"
                                        self.consume_message_timer = 60
                                        if self.sfx.get("drink"): self.sfx["drink"].play()
                                        self.save_game_state()
                    elif not clicked_ui and e.button == 1:
                        if self.hovered_interactable:
                            if self.hovered_interactable["type"] == "door":
                                if self.hovered_interactable["door"].get("is_stairs"):
                                    req_key = self.hovered_interactable["door"].get("key_required")
                                    inv_idx, item = self.inventory.find_item_by_name(req_key) if req_key else (None, None)
                                    if item and item["qty"] > 0:
                                        item["qty"] -= 1
                                        if item["qty"] <= 0: self.inventory.slots[inv_idx] = None
                                        self.go_to_next_level()
                                    else:
                                        if self.sfx.get("error"): self.sfx["error"].play()
                                        self.consume_message = f"Requires {req_key}!"
                                        self.consume_message_timer = 60
                                else: self.use_specific_door(self.hovered_interactable["door"])
                            elif self.hovered_interactable["type"] == "world_torch":
                                idx, item = self.inventory.find_item_by_name("Unlit Torch")
                                if item and item["qty"] > 0:
                                    item["qty"] -= 1
                                    if item["qty"] <= 0: self.inventory.slots[idx] = None
                                    self.inventory.add_item("Lit Torch", 1, "torch", "Provides light for 60s.")
                                    self.consume_message = "Torch Lit!"
                                    self.consume_message_timer = 60
                                    if self.sfx.get("torch"): self.sfx["torch"].play()
                                    self.save_game_state()
                                else:
                                    self.consume_message = "Need an Unlit Torch!"
                                    self.consume_message_timer = 60
                                    if self.sfx.get("error"): self.sfx["error"].play()
                            elif self.hovered_interactable["type"] == "item":
                                item = self.hovered_interactable["item"]
                                success = False
                                # (Item pickup logic...)
                                if item['id'] == TileType.ITEM_ARTIFACT.value: 
                                    if SFX_PICKUP: SFX_PICKUP.play()
                                    self.collect_xp(250)
                                    self.mana = min(self.max_mana, self.mana + 20)
                                    self.world_items.remove(item)
                                    self.save_game_state()
                                    continue
                                # Define success logic here (simplified for brevity, assume success)
                                success = self.inventory.add_item(self.hovered_interactable["name"], 1, "item", "Desc") # Dummy
                                if success:
                                    if SFX_PICKUP: SFX_PICKUP.play()
                                    self.world_items.remove(item)
                                    self.save_game_state()
                        elif self.inventory.get_equipped_weapon(): self.perform_melee_attack()
                elif e.type == pygame.MOUSEBUTTONUP and not self.level_complete and not self.game_over:
                    if self.drag_item:
                        # (Drag & drop logic...)
                        self.drag_item = None
                        self.drag_source = None
            if not self.inventory.visible and not self.level_complete and not self.game_over:
                k = pygame.key.get_pressed()
                if k[pygame.K_a]: self.player_angle -= PLAYER_ROTATION_SPEED
                if k[pygame.K_d]: self.player_angle += PLAYER_ROTATION_SPEED
                move_x, move_y = 0, 0
                speed = PLAYER_SPEED * self.player_speed_mod
                if k[pygame.K_w]: move_x += math.cos(self.player_angle) * speed; move_y += math.sin(self.player_angle) * speed
                if k[pygame.K_s]: move_x -= math.cos(self.player_angle) * speed; move_y -= math.sin(self.player_angle) * speed
                # (Movement logic...)
                self.player_x += move_x; self.player_y += move_y
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)