import pygame
import json
import os
from settings import * # FIX: This now properly imports FPS along with WIDTH and HEIGHT!

class BossDesigner:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("RPGW3D - Elite Boss Designer")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("georgia", 20, bold=True)
        self.font_small = pygame.font.SysFont("georgia", 16)
        
        self.boss_data = {
            "name": "Dark Overlord",
            "hp": 500,
            "damage": 50,
            "speed": 2.5,
            "scale": 1.5,
            "texture": "ghost_enemy_1.png"
        }
        
        self.buttons = []
        self.setup_ui()
        self.message = ""
        self.message_timer = 0
        
    def setup_ui(self):
        self.buttons.clear()
        
        # Y-positions for rows
        y_hp = 120
        y_dmg = 180
        y_spd = 240
        y_scl = 300
        
        # Minus buttons
        self.buttons.append({"action": "hp_minus", "rect": pygame.Rect(400, y_hp, 30, 30), "label": "-"})
        self.buttons.append({"action": "dmg_minus", "rect": pygame.Rect(400, y_dmg, 30, 30), "label": "-"})
        self.buttons.append({"action": "spd_minus", "rect": pygame.Rect(400, y_spd, 30, 30), "label": "-"})
        self.buttons.append({"action": "scl_minus", "rect": pygame.Rect(400, y_scl, 30, 30), "label": "-"})
        
        # Plus buttons
        self.buttons.append({"action": "hp_plus", "rect": pygame.Rect(550, y_hp, 30, 30), "label": "+"})
        self.buttons.append({"action": "dmg_plus", "rect": pygame.Rect(550, y_dmg, 30, 30), "label": "+"})
        self.buttons.append({"action": "spd_plus", "rect": pygame.Rect(550, y_spd, 30, 30), "label": "+"})
        self.buttons.append({"action": "scl_plus", "rect": pygame.Rect(550, y_scl, 30, 30), "label": "+"})
        
        # System buttons
        self.buttons.append({"action": "save", "rect": pygame.Rect(WIDTH//2 - 160, 380, 150, 40), "label": "SAVE BOSS"})
        self.buttons.append({"action": "exit", "rect": pygame.Rect(WIDTH//2 + 10, 380, 150, 40), "label": "EXIT"})

    def handle_click(self, action):
        if action == "hp_minus": self.boss_data["hp"] = max(100, self.boss_data["hp"] - 50)
        elif action == "hp_plus": self.boss_data["hp"] += 50
        elif action == "dmg_minus": self.boss_data["damage"] = max(5, self.boss_data["damage"] - 5)
        elif action == "dmg_plus": self.boss_data["damage"] += 5
        elif action == "spd_minus": self.boss_data["speed"] = max(0.5, round(self.boss_data["speed"] - 0.2, 1))
        elif action == "spd_plus": self.boss_data["speed"] = round(self.boss_data["speed"] + 0.2, 1)
        elif action == "scl_minus": self.boss_data["scale"] = max(0.5, round(self.boss_data["scale"] - 0.1, 1))
        elif action == "scl_plus": self.boss_data["scale"] = round(self.boss_data["scale"] + 0.1, 1)
        elif action == "save":
            try:
                with open("custom_boss.json", "w") as f:
                    json.dump(self.boss_data, f, indent=4)
                self.message = "Elite Boss Saved to custom_boss.json!"
                self.message_timer = 120
            except:
                self.message = "Error Saving Boss!"
                self.message_timer = 120

    def draw(self):
        self.screen.fill((20, 20, 25))
        
        # Header
        title = pygame.font.SysFont("georgia", 40, bold=True).render("ELITE BOSS DESIGNER", True, (255, 100, 100))
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 30))
        
        # Draw Labels & Values
        y_pos = [120, 180, 240, 300]
        labels = ["Health Points", "Attack Damage", "Movement Speed", "Sprite Scale"]
        values = [str(self.boss_data["hp"]), str(self.boss_data["damage"]), str(self.boss_data["speed"]), str(self.boss_data["scale"])]
        
        for i in range(4):
            # Label
            lbl_surf = self.font.render(labels[i], True, (200, 200, 200))
            self.screen.blit(lbl_surf, (200, y_pos[i] + 5))
            
            # Value Box
            val_rect = pygame.Rect(440, y_pos[i], 100, 30)
            pygame.draw.rect(self.screen, (10, 10, 15), val_rect)
            pygame.draw.rect(self.screen, (100, 100, 100), val_rect, 2)
            
            val_surf = self.font.render(values[i], True, (255, 215, 0))
            self.screen.blit(val_surf, (val_rect.centerx - val_surf.get_width()//2, val_rect.centery - val_surf.get_height()//2))

        # Draw Buttons
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            hover = btn["rect"].collidepoint(mouse_pos)
            
            if btn["action"] in ["save", "exit"]:
                bg_color = (150, 50, 50) if btn["action"] == "exit" else (50, 150, 50)
                if hover: bg_color = (min(255, bg_color[0]+40), min(255, bg_color[1]+40), min(255, bg_color[2]+40))
                pygame.draw.rect(self.screen, bg_color, btn["rect"])
                pygame.draw.rect(self.screen, (255, 255, 255), btn["rect"], 2)
            else:
                bg_color = (60, 60, 70) if not hover else (100, 100, 120)
                pygame.draw.rect(self.screen, bg_color, btn["rect"])
                pygame.draw.rect(self.screen, (200, 200, 200), btn["rect"], 1)
                
            txt_surf = self.font.render(btn["label"], True, (255, 255, 255))
            self.screen.blit(txt_surf, (btn["rect"].centerx - txt_surf.get_width()//2, btn["rect"].centery - txt_surf.get_height()//2))

        if self.message_timer > 0:
            self.message_timer -= 1
            msg_surf = self.font.render(self.message, True, (100, 255, 100))
            self.screen.blit(msg_surf, (WIDTH//2 - msg_surf.get_width()//2, HEIGHT - 40))

        pygame.display.flip()

    def run(self):
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    return
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    for btn in self.buttons:
                        if btn["rect"].collidepoint(mouse_pos):
                            if btn["action"] == "exit":
                                return
                            self.handle_click(btn["action"])
            self.draw()
            self.clock.tick(FPS)