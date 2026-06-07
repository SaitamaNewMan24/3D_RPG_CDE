import pygame
import math
from settings import *

class ActionBar:
    def __init__(self, icons_dict):
        self.icons = icons_dict
        # Expanded to 6 slots for that MMO feel!
        self.slots = [
            {"key": pygame.K_1, "label": "1", "name": "Empty", "icon": None, "cd": 0, "max_cd": 30, "type": "none", "cost": 0},
            {"key": pygame.K_2, "label": "2", "name": "Fireball", "icon": icons_dict.get("fireball") if icons_dict else None, "cd": 0, "max_cd": 60, "type": "magic", "cost": 10},
            {"key": pygame.K_3, "label": "3", "name": "Empty", "icon": None, "cd": 0, "max_cd": 120, "type": "none", "cost": 0},
            {"key": pygame.K_4, "label": "4", "name": "Empty", "icon": None, "cd": 0, "max_cd": 10, "type": "none", "cost": 0},
            {"key": pygame.K_5, "label": "5", "name": "Empty", "icon": None, "cd": 0, "max_cd": 10, "type": "none", "cost": 0},
            {"key": pygame.K_6, "label": "6", "name": "Empty", "icon": None, "cd": 0, "max_cd": 10, "type": "none", "cost": 0}
        ]
        self.slot_size = 50
        self.spacing = 10

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            for i, slot in enumerate(self.slots):
                if event.key == slot["key"]:
                    return i
        return None

    def check_click(self, pos):
        total_width = (len(self.slots) * self.slot_size) + ((len(self.slots) - 1) * self.spacing)
        start_x = (WIDTH // 2) - (total_width // 2)
        start_y = HEIGHT - self.slot_size - 20 

        for i in range(len(self.slots)):
            x = start_x + (i * (self.slot_size + self.spacing))
            rect = pygame.Rect(x, start_y, self.slot_size, self.slot_size)
            if rect.collidepoint(pos):
                return i
        return None

    def update(self):
        for slot in self.slots:
            if slot["cd"] > 0: slot["cd"] -= 1

    def draw(self, screen):
        total_width = (len(self.slots) * self.slot_size) + ((len(self.slots) - 1) * self.spacing)
        start_x = (WIDTH // 2) - (total_width // 2)
        start_y = HEIGHT - self.slot_size - 20 

        for i, slot in enumerate(self.slots):
            x = start_x + (i * (self.slot_size + self.spacing))
            rect = pygame.Rect(x, start_y, self.slot_size, self.slot_size)
            
            pygame.draw.rect(screen, (40, 30, 20), rect)
            pygame.draw.rect(screen, (150, 150, 150), rect, 2)
            
            if slot["icon"]:
                icon_scaled = pygame.transform.scale(slot["icon"], (self.slot_size - 4, self.slot_size - 4))
                screen.blit(icon_scaled, (x + 2, start_y + 2))
            
            if slot["cd"] > 0:
                cd_ratio = slot["cd"] / slot["max_cd"]
                cd_height = int(self.slot_size * cd_ratio)
                s = pygame.Surface((self.slot_size, cd_height), pygame.SRCALPHA)
                s.fill((0, 0, 0, 150))
                screen.blit(s, (x, start_y + self.slot_size - cd_height))
            
            font = pygame.font.SysFont("georgia", 14, bold=True)
            text = font.render(slot["label"], True, (255, 255, 255))
            screen.blit(text, (x + 5, start_y + 5))

class TargetHUD:
    """
    Manages on-screen targeting brackets for items, enemies, and interactables.
    """
    def __init__(self, screen):
        self.screen = screen
        self.font_small_bold = pygame.font.SysFont("georgia", 14, bold=True)
        
    def draw_ss2_bracket(self, rect, label):
        """Draws an animated System Shock 2 style bracket around a target."""
        x, y, w, h = rect
        l, t = max(5, w//4), 2
        # Pulsing alpha effect based on current time
        alpha = int(150 + 105 * math.sin(pygame.time.get_ticks() / 150))
        
        bracket_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        color_with_alpha = (255, 255, 255, alpha)
        
        # Draw the 4 corners of the bracket
        pygame.draw.line(bracket_surf, color_with_alpha, (0, 0), (l, 0), t)
        pygame.draw.line(bracket_surf, color_with_alpha, (0, 0), (0, l), t)
        pygame.draw.line(bracket_surf, color_with_alpha, (w-1, 0), (w-1-l, 0), t)
        pygame.draw.line(bracket_surf, color_with_alpha, (w-1, 0), (w-1, l), t)
        pygame.draw.line(bracket_surf, color_with_alpha, (0, h-1), (l, h-1), t)
        pygame.draw.line(bracket_surf, color_with_alpha, (0, h-1), (0, h-1-l), t)
        pygame.draw.line(bracket_surf, color_with_alpha, (w-1, h-1), (w-1-l, h-1), t)
        pygame.draw.line(bracket_surf, color_with_alpha, (w-1, h-1), (w-1, h-1-l), t)
        
        self.screen.blit(bracket_surf, (x, y))
        
        # Render target label above the bracket
        text = self.font_small_bold.render(f"[ {label} ]", True, (255, 255, 255))
        self.screen.blit(text, (x + w//2 - text.get_width()//2, y - 20))