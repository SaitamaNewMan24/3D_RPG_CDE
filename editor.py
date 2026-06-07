import pygame
import json
import copy
import os
import random
from settings import *

class MapEditor:
    def __init__(self):
        pygame.init()
        self.base_cell_size = 24
        
        self.editor_width = 1200
        self.editor_height = 800
        self.left_panel_w = 200
        self.right_panel_w = 260
        
        self.screen = pygame.display.set_mode((self.editor_width, self.editor_height))
        pygame.display.set_caption("RPGW3D Map Editor")
        self.clock = pygame.time.Clock()
        
        self.font_tiny = pygame.font.SysFont("georgia", 10, bold=True)
        self.font = pygame.font.SysFont("georgia", 12)
        self.font_med = pygame.font.SysFont("georgia", 14, bold=True)
        self.font_large = pygame.font.SysFont("georgia", 16, bold=True)
        
        self.map = [[TileType.EMPTY.value for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
        self.active_tile = TileType.WALL_BRICK.value
        self.fill_mode = False
        self.floor_texture = "GRASS"
        self.history = []
        self.editor_message = ""
        self.editor_message_timer = 0
        
        self.current_level_num = 1
        self.camera_x = self.left_panel_w + 20
        self.camera_y = 20
        self.zoom = 1.0
        self.is_panning = False
        self.pan_start_mouse = (0, 0)
        self.pan_start_camera = (0, 0)
        self.scaled_sprites_cache = {}
        
        self.tree_leafy_sprites = [self.load_sprite(p, fallback="tree") for p in TREE_LEAFY_PATHS]
        self.bush_sprites = [self.load_sprite(p, fallback="bush") for p in BUSH_PATHS]
        
        self.sprites = {
            TileType.DEAD_TREE.value: self.load_sprite(TREE_DEAD_PATH, fallback="dead"),
            TileType.ROCK.value: self.load_sprite(ROCK_PATH, fallback="rock"),
            TileType.ITEM_DAGGER.value: self.load_sprite(SWORD_PATH, fallback="none"),
            TileType.ITEM_KEY.value: self.load_sprite(KEY_PATH, fallback="none"),
            TileType.ITEM_KEY_SILVER.value: self.load_sprite(KEY_SILVER_PATH, fallback="none"),
            TileType.ITEM_KEY_GOLD.value: self.load_sprite(KEY_GOLD_PATH, fallback="none"),
            TileType.ITEM_KEY_DUNGEON.value: self.load_sprite(RUSTY_KEY_PATH, fallback="none"),
            TileType.ITEM_KEY_RUSTY_2.value: self.load_sprite(RUSTY_KEY_2_PATH, fallback="none"),
            TileType.ITEM_FOOD.value: self.load_sprite(MANA_POTION_PATH, fallback="food"), 
            TileType.ITEM_HEALTH_POTION.value: self.load_sprite(HEALTH_POTION_PATH, fallback="food"),
            TileType.ITEM_STAMINA_POTION.value: self.load_sprite(STAMINA_POTION_PATH, fallback="food"),
            TileType.ITEM_ARTIFACT.value: self.load_sprite(ARTIFACT_PATH, fallback="artifact"),
            TileType.ITEM_UNLIT_TORCH.value: self.load_sprite("unlit_torch.png", fallback="unlit_torch"),
            TileType.ITEM_STAFF.value: self.load_sprite("staff.png", fallback="artifact"),
            TileType.STANDING_TORCH.value: self.load_sprite("standing_torch.png", fallback="lit_torch"),
            TileType.WALL_TORCH.value: self.load_sprite("wall_torch.png", fallback="lit_torch"),
            TileType.ENEMY_GHOST.value: self.load_sprite(ENEMY_GHOST_PATH, fallback="enemy")
        }
        
        self.tile_names = {
            TileType.WALL_BRICK.value: "Brick Wall", TileType.WALL_STONE.value: "Stone Wall",
            TileType.WALL_WOOD.value: "Wood Wall", TileType.DOOR.value: "Brass Dr",
            TileType.DOOR_SILVER.value: "Silver Dr", TileType.DOOR_GOLD.value: "Gold Dr",
            TileType.STAIRS.value: "Stairs Down", TileType.TREE.value: "Tree", 
            TileType.DEAD_TREE.value: "Dead Tree", TileType.BUSH.value: "Bush", 
            TileType.ROCK.value: "Rock", TileType.EMPTY.value: "Eraser", 
            TileType.STANDING_TORCH.value: "S Torch", TileType.WALL_TORCH.value: "W Torch", 
            TileType.ITEM_DAGGER.value: "Sword", TileType.ITEM_KEY.value: "B Key", 
            TileType.ITEM_KEY_SILVER.value: "S Key", TileType.ITEM_KEY_GOLD.value: "G Key", 
            TileType.ITEM_KEY_DUNGEON.value: "Dgn Key", TileType.ITEM_KEY_RUSTY_2.value: "Rust Key2",
            TileType.ITEM_HEALTH_POTION.value: "H Potion", 
            TileType.ITEM_FOOD.value: "M Potion", TileType.ITEM_STAMINA_POTION.value: "S Potion",
            TileType.ITEM_ARTIFACT.value: "Artifact", 
            TileType.ITEM_UNLIT_TORCH.value: "U Torch", TileType.ITEM_STAFF.value: "Staff",
            TileType.PLAYER_SPAWN.value: "P Spawn", TileType.ENEMY_GHOST.value: "Ghost",
            TileType.WALL_BRICK_CRACKED.value: "Crck Brick", TileType.WALL_STONE_CRACKED.value: "Crck Stone",
            TileType.WALL_WOOD_CRACKED.value: "Crck Wood", TileType.FORCE_FIELD.value: "Force Field"
        }
        
        self.buttons = []
        self.setup_ui()
        self.load_map()

    def load_sprite(self, path, fallback="tree"):
        size = (TILE_SIZE, TILE_SIZE)
        try:
            img = pygame.image.load(path).convert_alpha()
            img.set_colorkey((0,0,0))
            return img
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
            elif fallback == "rock":
                pygame.draw.polygon(surf, (100, 100, 100), [(10, 60), (32, 30), (54, 60)])
            elif fallback == "food":
                pygame.draw.circle(surf, (200, 150, 100), (size[0]//2, size[1]//2), size[0]//3)
            elif fallback == "artifact":
                pygame.draw.polygon(surf, (0, 255, 255), [(size[0]//2, 5), (size[0]-5, size[1]//2), (size[0]//2, size[1]-5), (5, size[1]//2)])
            elif fallback == "unlit_torch":
                pygame.draw.rect(surf, (100, 50, 20), (size[0]//2 - 4, 10, 8, size[1] - 20))
            elif fallback == "lit_torch":
                pygame.draw.rect(surf, (100, 50, 20), (size[0]//2 - 4, 10, 8, size[1] - 20))
                pygame.draw.circle(surf, (255, 150, 0), (size[0]//2, 10), 8)
            elif fallback == "enemy":
                pygame.draw.circle(surf, (200, 50, 50), (size[0]//2, size[1]//2), size[0]//3)
                pygame.draw.circle(surf, (255, 255, 0), (size[0]//2 - 6, size[1]//2 - 4), 3)
                pygame.draw.circle(surf, (255, 255, 0), (size[0]//2 + 6, size[1]//2 - 4), 3)
            elif fallback == "none":
                return None
            else:
                pygame.draw.circle(surf, (150, 50, 150), (size[0]//2, size[1]//2), size[0]//3)
            return surf

    def get_scaled_sprite(self, val, size, x=0, y=0):
        if val == TileType.TREE.value:
            orig = self.tree_leafy_sprites[(x * 73 + y * 31) % len(self.tree_leafy_sprites)]
            key = (val, size, (x * 73 + y * 31) % len(self.tree_leafy_sprites))
        elif val == TileType.BUSH.value:
            orig = self.bush_sprites[(x * 53 + y * 89) % len(self.bush_sprites)]
            key = (val, size, (x * 53 + y * 89) % len(self.bush_sprites))
        else:
            if val not in self.sprites: return None 
            orig = self.sprites[val]
            if orig is None: return None
            key = (val, size, 0)
            
        if key not in self.scaled_sprites_cache:
            self.scaled_sprites_cache[key] = pygame.transform.scale(orig, (size, size))
        return self.scaled_sprites_cache[key]

    def setup_ui(self):
        def create_grid(items, start_x, start_y, cols, w, h, x_pad, y_pad, text=False, is_floor=False):
            cx, cy = start_x, start_y
            for i, (name, val) in enumerate(items):
                color = None
                if is_floor:
                    if val == "floor_DIRT": color = (80, 60, 40)
                    elif val == "floor_STONE": color = (60, 60, 60)
                    elif val == "floor_SAND": color = (194, 178, 128)
                    elif val == "floor_GRASS": color = (40, 60, 40)
                
                self.buttons.append({"name": name, "action": val, "rect": pygame.Rect(cx, cy, w, h), "color": color, "text": text})
                cx += w + x_pad
                if (i + 1) % cols == 0:
                    cx = start_x
                    cy += h + y_pad

        lx = 10
        self.buttons.append({"name": "EXIT TO MENU", "action": "exit", "rect": pygame.Rect(lx, 10, self.left_panel_w - 20, 40), "color": (220, 50, 50), "text": True})
        
        sys_items = [("SAVE MAP", "save"), ("Undo", "undo"), ("CLEAR", "clear"), ("WIPE SAVE", "wipe_save"), ("LVL UP", "lvl_up"), ("LVL DOWN", "lvl_down")]
        create_grid(sys_items, lx, 80, 2, 85, 30, 5, 5, text=True)

        # --- FIX: Adjusted left panel spacing to remove overlapping elements ---
        tool_items = [("Erase", TileType.EMPTY.value), ("Fill", "fill"), ("P Spawn", TileType.PLAYER_SPAWN.value)]
        create_grid(tool_items, lx, 210, 2, 85, 30, 5, 5, text=True)

        enemy_items = [("Ghost", TileType.ENEMY_GHOST.value)]
        create_grid(enemy_items, lx + 10, 310, 4, 40, 40, 5, 5, text=False)
        
        rx = self.editor_width - self.right_panel_w + 10
        
        items_list = [
            ("Sword", TileType.ITEM_DAGGER.value), ("Staff", TileType.ITEM_STAFF.value), 
            ("H Potion", TileType.ITEM_HEALTH_POTION.value), ("M Potion", TileType.ITEM_FOOD.value), ("S Potion", TileType.ITEM_STAMINA_POTION.value),
            ("B Key", TileType.ITEM_KEY.value), ("S Key", TileType.ITEM_KEY_SILVER.value), ("G Key", TileType.ITEM_KEY_GOLD.value),
            ("Dgn Key", TileType.ITEM_KEY_DUNGEON.value), ("Rust Key2", TileType.ITEM_KEY_RUSTY_2.value),
            ("Artifact", TileType.ITEM_ARTIFACT.value), ("U Torch", TileType.ITEM_UNLIT_TORCH.value)
        ]
        create_grid(items_list, rx, 65, 5, 40, 40, 5, 5, text=False)
        
        world_list = [
            ("Tree", TileType.TREE.value), ("Dead Tree", TileType.DEAD_TREE.value), 
            ("Bush", TileType.BUSH.value), ("Rock", TileType.ROCK.value),
            ("S Torch", TileType.STANDING_TORCH.value), ("W Torch", TileType.WALL_TORCH.value)
        ]
        create_grid(world_list, rx, 230, 5, 40, 40, 5, 5, text=False)

        walls_list = [
            ("Brick", TileType.WALL_BRICK.value), ("Stone", TileType.WALL_STONE.value), ("Wood", TileType.WALL_WOOD.value),
            ("Brass Dr", TileType.DOOR.value), ("Silver Dr", TileType.DOOR_SILVER.value), ("Gold Dr", TileType.DOOR_GOLD.value),
            ("Stairs", TileType.STAIRS.value), 
            ("Crck Brick", TileType.WALL_BRICK_CRACKED.value), ("Crck Stone", TileType.WALL_STONE_CRACKED.value), 
            ("Crck Wood", TileType.WALL_WOOD_CRACKED.value), ("Force Field", TileType.FORCE_FIELD.value)
        ]
        create_grid(walls_list, rx, 350, 5, 40, 40, 5, 5, text=False)
        
        floor_list = [
            ("Dirt", "floor_DIRT"), ("Stone", "floor_STONE"), ("Sand", "floor_SAND"), ("Grass", "floor_GRASS")
        ]
        create_grid(floor_list, rx, 515, 4, 50, 50, 5, 5, text=True, is_floor=True)

    def load_map(self):
        filename = MAP_DATA_FILE if self.current_level_num == 1 else f"map_level_{self.current_level_num}.json"
        self.history.clear()
        try:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.map = self.pad_map(data.get('map', self.map))
                        self.floor_texture = data.get('floor_texture', 'GRASS')
                    else:
                        self.map = self.pad_map(data)
            else:
                self.map = [[TileType.EMPTY.value for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
        except Exception as e: pass

    def pad_map(self, map_data):
        """Ensure map has correct dimensions"""
        if not map_data:
            return [[TileType.EMPTY.value for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
        
        result = [[TileType.EMPTY.value for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
        for y in range(min(len(map_data), MAP_SIZE)):
            for x in range(min(len(map_data[y]), MAP_SIZE)):
                result[y][x] = map_data[y][x]
        return result

    def save_map(self):
        filename = MAP_DATA_FILE if self.current_level_num == 1 else f"map_level_{self.current_level_num}.json"
        with open(filename, 'w') as f:
            json.dump({'map': self.map, 'floor_texture': self.floor_texture}, f, indent=2)

    def push_history(self):
        self.history.append(copy.deepcopy(self.map))
        if len(self.history) > 20: self.history.pop(0)

    def undo(self):
        if self.history: 
            self.map = self.history.pop()
            self.editor_message = "Undo applied."
            self.editor_message_timer = 90

    def flood_fill(self, start_x, start_y, target_val, fill_val):
        if target_val == fill_val: return
        q = [(start_x, start_y)]
        while q:
            x, y = q.pop(0)
            if self.map[y][x] == target_val:
                self.map[y][x] = fill_val
                if x > 0: q.append((x-1, y))
                if x < MAP_SIZE - 1: q.append((x+1, y))
                if y > 0: q.append((x, y-1))
                if y < MAP_SIZE - 1: q.append((x, y+1))

    def handle_button_click(self, btn):
        act = btn["action"]
        if act == "exit": return "exit"
        elif act == "save": 
            self.save_map()
            self.editor_message = f"Level {self.current_level_num} Saved!"
            self.editor_message_timer = 120
        elif act == "undo": self.undo()
        elif act == "fill": self.fill_mode = True
        elif act == "lvl_up":
            self.save_map()
            self.current_level_num += 1
            self.load_map()
            self.editor_message = f"Moved to Level {self.current_level_num}!"
            self.editor_message_timer = 120
        elif act == "lvl_down":
            if self.current_level_num > 1:
                self.save_map()
                self.current_level_num -= 1
                self.load_map()
                self.editor_message = f"Moved to Level {self.current_level_num}!"
                self.editor_message_timer = 120
            else:
                self.editor_message = "Already at Level 1!"
                self.editor_message_timer = 90
        elif act == "clear":
            self.push_history()
            self.map = [[TileType.EMPTY.value for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
            self.editor_message = "Map Cleared!"
            self.editor_message_timer = 90
        elif act == "wipe_save":
            try:
                if os.path.exists("savegame.json"): os.remove("savegame.json")
                self.editor_message = "Game Save Wiped!"
                self.editor_message_timer = 120
            except: pass
        elif isinstance(act, str) and act.startswith("floor_"):
            # FIX: Improved floor texture parsing with error checking
            parts = act.split("_")
            if len(parts) >= 2:
                self.floor_texture = parts[1]
            else:
                self.editor_message = "Invalid floor texture!"
                self.editor_message_timer = 90
        else:
            self.active_tile = act
            self.fill_mode = False
        return None

    def draw(self):
        self.screen.fill((30, 30, 35)) 
        
        map_rect = pygame.Rect(self.left_panel_w, 0, self.editor_width - self.left_panel_w - self.right_panel_w, self.editor_height)
        self.screen.set_clip(map_rect)
        
        current_cell_size = int(self.base_cell_size * self.zoom)
        floor_colors = {"DIRT": (80, 60, 40), "STONE": (60, 60, 60), "SAND": (194, 178, 128), "GRASS": (40, 60, 40)}
        base_color = floor_colors.get(self.floor_texture, (40, 60, 40))
        
        for y in range(MAP_SIZE):
            for x in range(MAP_SIZE):
                rect_x = self.camera_x + x * current_cell_size
                rect_y = self.camera_y + y * current_cell_size
                if rect_x > self.editor_width - self.right_panel_w or rect_y > self.editor_height or rect_x + current_cell_size < self.left_panel_w or rect_y + current_cell_size < 0:
                    continue
                rect = pygame.Rect(rect_x, rect_y, current_cell_size, current_cell_size)
                val = self.map[y][x]
                pygame.draw.rect(self.screen, base_color, rect) 
                
                if val != TileType.EMPTY.value:
                    sprite = self.get_scaled_sprite(val, current_cell_size, x, y)
                    if sprite: self.screen.blit(sprite, rect.topleft)
                    else:
                        t_col = (100, 100, 100)
                        if val == TileType.WALL_BRICK.value: t_col = (200, 100, 50)
                        elif val == TileType.WALL_STONE.value: t_col = (120, 120, 120)
                        elif val == TileType.WALL_WOOD.value: t_col = (139, 69, 19)
                        elif val == TileType.WALL_BRICK_CRACKED.value: t_col = (150, 50, 30)
                        elif val == TileType.WALL_STONE_CRACKED.value: t_col = (80, 80, 80)
                        elif val == TileType.WALL_WOOD_CRACKED.value: t_col = (90, 45, 10)
                        elif val == TileType.FORCE_FIELD.value: t_col = (0, 255, 255)
                        elif val == TileType.DOOR.value: t_col = (255, 200, 50)
                        elif val == TileType.DOOR_SILVER.value: t_col = (200, 200, 200)
                        elif val == TileType.DOOR_GOLD.value: t_col = (255, 215, 0)
                        elif val == TileType.STAIRS.value: t_col = (150, 100, 255)
                        elif val == TileType.STANDING_TORCH.value: t_col = (255, 140, 0)
                        elif val == TileType.WALL_TORCH.value: t_col = (200, 80, 20)
                        elif val == TileType.ITEM_UNLIT_TORCH.value: t_col = (139, 69, 19)
                        elif val == TileType.ITEM_STAFF.value: t_col = (100, 200, 255)
                        elif val == TileType.ITEM_KEY_SILVER.value: t_col = (200, 200, 200)
                        elif val == TileType.ITEM_KEY_GOLD.value: t_col = (255, 215, 0)
                        elif val == TileType.ITEM_KEY_DUNGEON.value: t_col = (100, 50, 50)
                        elif val == TileType.PLAYER_SPAWN.value: t_col = (0, 255, 200) 
                        pygame.draw.rect(self.screen, t_col, rect)
                pygame.draw.rect(self.screen, (60, 60, 60), rect, 1)

        self.screen.set_clip(None)
        
        pygame.draw.rect(self.screen, (20, 20, 25), (0, 0, self.left_panel_w, self.editor_height))
        pygame.draw.line(self.screen, (200, 180, 100), (self.left_panel_w, 0), (self.left_panel_w, self.editor_height), 2)

        pygame.draw.rect(self.screen, (20, 20, 25), (self.editor_width - self.right_panel_w, 0, self.right_panel_w, self.editor_height))
        pygame.draw.line(self.screen, (200, 180, 100), (self.editor_width - self.right_panel_w, 0), (self.editor_width - self.right_panel_w, self.editor_height), 2)
        
        rx = self.editor_width - self.right_panel_w + 10
        
        # --- FIX: Moved Level info into the right-hand bar so it doesn't overlap the map ---
        floor_text = self.font_large.render(f"Level: {self.current_level_num} | Floor: {self.floor_texture}", True, (150, 255, 150))
        self.screen.blit(floor_text, (rx, 15))  
        
        self.screen.blit(self.font_med.render("ITEMS", True, (200, 200, 200)), (rx, 45))
        self.screen.blit(self.font_med.render("WORLD OBJECTS", True, (200, 200, 200)), (rx, 210))
        self.screen.blit(self.font_med.render("WALLS & DOORS", True, (200, 200, 200)), (rx, 330))
        self.screen.blit(self.font_med.render("FLOOR BRUSH", True, (200, 200, 200)), (rx, 495))
        
        lx = 10
        self.screen.blit(self.font_med.render("SYSTEM", True, (200, 200, 200)), (lx, 60))
        self.screen.blit(self.font_med.render("TOOLS", True, (200, 200, 200)), (lx, 190))
        self.screen.blit(self.font_med.render("ENEMIES", True, (200, 200, 200)), (lx, 290))
        
        for btn in self.buttons:
            bg_col = btn.get("color")
            is_active_tool = (not self.fill_mode and btn["action"] == self.active_tile) or (self.fill_mode and btn["action"] == "fill")
            is_active_floor = isinstance(btn["action"], str) and btn["action"].startswith("floor_") and btn["action"].split("_")[1] == self.floor_texture

            if not bg_col:
                if is_active_tool or is_active_floor: bg_col = (160, 140, 100)
                else: bg_col = (60, 60, 70)

            pygame.draw.rect(self.screen, bg_col, btn["rect"])
            
            if not btn.get("text"):
                sprite = self.get_scaled_sprite(btn["action"], btn["rect"].width - 8)
                if sprite:
                    self.screen.blit(sprite, (btn["rect"].x + 4, btn["rect"].y + 4))
                else:
                    val = btn["action"]
                    t_col = None
                    if val == TileType.WALL_BRICK.value: t_col = (200, 100, 50)
                    elif val == TileType.WALL_STONE.value: t_col = (120, 120, 120)
                    elif val == TileType.WALL_WOOD.value: t_col = (139, 69, 19)
                    elif val == TileType.WALL_BRICK_CRACKED.value: t_col = (150, 50, 30)
                    elif val == TileType.WALL_STONE_CRACKED.value: t_col = (80, 80, 80)
                    elif val == TileType.WALL_WOOD_CRACKED.value: t_col = (90, 45, 10)
                    elif val == TileType.FORCE_FIELD.value: t_col = (0, 255, 255)
                    elif val == TileType.DOOR.value: t_col = (255, 200, 50)
                    elif val == TileType.DOOR_SILVER.value: t_col = (200, 200, 200)
                    elif val == TileType.DOOR_GOLD.value: t_col = (255, 215, 0)
                    elif val == TileType.STAIRS.value: t_col = (150, 100, 255)
                    
                    if t_col:
                        inner_rect = pygame.Rect(btn["rect"].x + 4, btn["rect"].y + 4, btn["rect"].width - 8, btn["rect"].height - 8)
                        pygame.draw.rect(self.screen, t_col, inner_rect)
                        pygame.draw.rect(self.screen, (30, 30, 30), inner_rect, 1)

                    words = btn["name"].split()
                    y_offset = btn["rect"].centery - (len(words) * 10) // 2
                    for word in words:
                        bg_txt = self.font_tiny.render(word, True, (0, 0, 0))
                        txt = self.font_tiny.render(word, True, (255, 255, 255))
                        cx = btn["rect"].centerx - txt.get_width()//2
                        self.screen.blit(bg_txt, (cx + 1, y_offset + 1))
                        self.screen.blit(txt, (cx, y_offset))
                        y_offset += 10

            if btn.get("text"):
                words = btn["name"].split()
                if len(words) > 1 and btn["rect"].width <= 60:
                    y_offset = btn["rect"].centery - (len(words) * 14) // 2
                    for word in words:
                        bg_txt = self.font.render(word, True, (0, 0, 0))
                        txt = self.font.render(word, True, (255, 255, 255))
                        cx = btn["rect"].centerx - txt.get_width()//2
                        self.screen.blit(bg_txt, (cx + 1, y_offset + 1))
                        self.screen.blit(txt, (cx, y_offset))
                        y_offset += 14
                else:
                    bg_txt = self.font.render(btn["name"], True, (0, 0, 0))
                    txt = self.font.render(btn["name"], True, (255, 255, 255))
                    cx = btn["rect"].centerx - txt.get_width()//2
                    cy = btn["rect"].centery - txt.get_height()//2
                    self.screen.blit(bg_txt, (cx + 1, cy + 1))
                    self.screen.blit(txt, (cx, cy))

            if is_active_tool or is_active_floor: 
                pygame.draw.rect(self.screen, (255, 255, 200), btn["rect"], 3)
            else:
                pygame.draw.rect(self.screen, (30, 30, 35), btn["rect"], 1)

        info_bar_height = 35
        pygame.draw.rect(self.screen, (40, 35, 30), (self.left_panel_w, self.editor_height - info_bar_height, self.editor_width - self.left_panel_w - self.right_panel_w, info_bar_height))
        # FIX: Fixed syntax error - missing closing parenthesis
        pygame.draw.line(self.screen, (200, 180, 100), (self.left_panel_w, self.editor_height - info_bar_height), (self.editor_width - self.right_panel_w, self.editor_height - info_bar_height), 2)
        
        tool_name = self.tile_names.get(self.active_tile, "Unknown Tool")
        if self.fill_mode: tool_name = f"Flood Fill ({tool_name})"
        
        info_text = self.font_large.render(f"Currently Selected: {tool_name}", True, (255, 255, 200))
        self.screen.blit(info_text, (self.left_panel_w + 20, self.editor_height - 26))
        
        if self.editor_message_timer > 0:
            self.editor_message_timer -= 1
            msg_text = self.font_large.render(self.editor_message, True, (255, 255, 100))
            self.screen.blit(msg_text, (self.editor_width - self.right_panel_w - msg_text.get_width() - 20, self.editor_height - 26))

        pygame.display.flip()

    def run(self):
        mouse_down = False
        while True:
            pos = pygame.mouse.get_pos()
            for e in pygame.event.get():
                if e.type == pygame.QUIT: return "exit"
                elif e.type == pygame.MOUSEWHEEL:
                    if pos[0] >= self.left_panel_w and pos[0] <= self.editor_width - self.right_panel_w and pos[1] <= self.editor_height - 35: 
                        old_zoom = self.zoom
                        self.zoom += e.y * 0.1
                        self.zoom = max(0.5, min(self.zoom, 5.0))
                        wx = (pos[0] - self.camera_x) / old_zoom
                        wy = (pos[1] - self.camera_y) / old_zoom
                        self.camera_x = pos[0] - wx * self.zoom
                        self.camera_y = pos[1] - wy * self.zoom
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    if e.button == 1: 
                        mouse_down = True
                        clicked_toolbar = False
                        for btn in self.buttons:
                            if btn["rect"].collidepoint(pos):
                                clicked_toolbar = True
                                if self.handle_button_click(btn) == "exit": return "exit"
                                break
                        if not clicked_toolbar and pos[0] >= self.left_panel_w and pos[0] <= self.editor_width - self.right_panel_w and pos[1] <= self.editor_height - 35:
                            gx = int((pos[0] - self.camera_x) // (self.base_cell_size * self.zoom))
                            gy = int((pos[1] - self.camera_y) // (self.base_cell_size * self.zoom))
                            if 0 <= gx < MAP_SIZE and 0 <= gy < MAP_SIZE:
                                self.push_history() 
                                if self.fill_mode: self.flood_fill(gx, gy, self.map[gy][gx], self.active_tile)
                                else: self.map[gy][gx] = self.active_tile
                    elif e.button in (2, 3): 
                        self.is_panning = True
                        self.pan_start_mouse = pos
                        self.pan_start_camera = (self.camera_x, self.camera_y)
                elif e.type == pygame.MOUSEBUTTONUP:
                    if e.button == 1: mouse_down = False
                    elif e.button in (2, 3): self.is_panning = False
                elif e.type == pygame.MOUSEMOTION:
                    if self.is_panning:
                        dx = pos[0] - self.pan_start_mouse[0]
                        dy = pos[1] - self.pan_start_mouse[1]
                        self.camera_x = self.pan_start_camera[0] + dx
                        self.camera_y = self.pan_start_camera[1] + dy
                    elif mouse_down and not self.fill_mode and pos[0] >= self.left_panel_w and pos[0] <= self.editor_width - self.right_panel_w and pos[1] <= self.editor_height - 35:
                        gx = int((pos[0] - self.camera_x) // (self.base_cell_size * self.zoom))
                        gy = int((pos[1] - self.camera_y) // (self.base_cell_size * self.zoom))
                        if 0 <= gx < MAP_SIZE and 0 <= gy < MAP_SIZE:
                            self.map[gy][gx] = self.active_tile
            self.draw()
            self.clock.tick(60)
