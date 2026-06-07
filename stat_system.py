"""
Stat System - Handles character stat allocation and progression.
"""

import pygame


class StatAllocator:
    """Manages stat allocation UI and logic"""
    
    def __init__(self, font_huge, font_msg, font_small, width, height):
        self.font_huge = font_huge
        self.font_msg = font_msg
        self.font_small = font_small
        self.width = width
        self.height = height
        
        # Stat values
        self.stat_points = 5
        self.strength = 10
        self.intelligence = 10
        self.endurance = 10
        
        # Button setup
        self.stat_names = ["Strength", "Intelligence", "Endurance"]
        self.button_size = 40
        self.button_spacing = 10
        self.buttons = {}
        self._setup_buttons()
    
    def _setup_buttons(self):
        """Create UI buttons for stat allocation"""
        base_y = 220
        button_width = self.button_size
        button_height = self.button_size
        
        for i, stat_name in enumerate(self.stat_names):
            y = base_y + i * 80
            stat_key = stat_name.lower()
            
            # Minus button
            self.buttons[f"{stat_key}_minus"] = pygame.Rect(
                100, y, button_width, button_height
            )
            
            # Plus button
            self.buttons[f"{stat_key}_plus"] = pygame.Rect(
                300, y, button_width, button_height
            )
    
    def handle_click(self, pos):
        """Handle mouse click on buttons"""
        for button_name, button_rect in self.buttons.items():
            if button_rect.collidepoint(pos):
                self._process_button_click(button_name)
                return True
        return False
    
    def _process_button_click(self, button_name):
        """Process a button click"""
        if self.stat_points <= 0 and "plus" in button_name:
            return  # Can't allocate if no points left
        
        if "strength" in button_name:
            if "plus" in button_name:
                self.strength += 1
                self.stat_points -= 1
            elif "minus" in button_name and self.strength > 1:
                self.strength -= 1
                self.stat_points += 1
        
        elif "intelligence" in button_name:
            if "plus" in button_name:
                self.intelligence += 1
                self.stat_points -= 1
            elif "minus" in button_name and self.intelligence > 1:
                self.intelligence -= 1
                self.stat_points += 1
        
        elif "endurance" in button_name:
            if "plus" in button_name:
                self.endurance += 1
                self.stat_points -= 1
            elif "minus" in button_name and self.endurance > 1:
                self.endurance -= 1
                self.stat_points += 1
    
    def draw(self, screen):
        """Draw the stat allocation screen"""
        screen.fill((20, 20, 30))
        
        # Title
        title = self.font_huge.render("ALLOCATE STATS", True, (200, 150, 0))
        screen.blit(title, (self.width//2 - title.get_width()//2, 50))
        
        # Points available
        points_text = self.font_msg.render(
            f"Points Available: {self.stat_points}", 
            True, 
            (100, 200, 100) if self.stat_points > 0 else (200, 100, 100)
        )
        screen.blit(points_text, (50, 150))
        
        # Stat rows
        y_offset = 220
        stat_values = [self.strength, self.intelligence, self.endurance]
        
        for i, (name, value) in enumerate(zip(self.stat_names, stat_values)):
            y = y_offset + i * 80
            
            # Stat name and value
            stat_text = self.font_msg.render(f"{name}: {value}", True, (255, 255, 255))
            screen.blit(stat_text, (150, y))
            
            # Minus button
            minus_rect = self.buttons[f"{name.lower()}_minus"]
            mouse_pos = pygame.mouse.get_pos()
            is_hover_minus = minus_rect.collidepoint(mouse_pos)
            pygame.draw.rect(screen, (100, 100, 120) if is_hover_minus else (60, 60, 80), minus_rect)
            pygame.draw.rect(screen, (150, 150, 150), minus_rect, 2)
            minus_text = self.font_msg.render("-", True, (255, 255, 255))
            screen.blit(minus_text, (
                minus_rect.centerx - minus_text.get_width()//2,
                minus_rect.centery - minus_text.get_height()//2
            ))
            
            # Plus button
            plus_rect = self.buttons[f"{name.lower()}_plus"]
            is_hover_plus = plus_rect.collidepoint(mouse_pos)
            button_color = (100, 100, 120) if is_hover_plus else (60, 60, 80)
            if self.stat_points == 0 and not is_hover_plus:
                button_color = (40, 40, 60)  # Grayed out
            pygame.draw.rect(screen, button_color, plus_rect)
            pygame.draw.rect(screen, (150, 150, 150), plus_rect, 2)
            plus_text = self.font_msg.render("+", True, (255, 255, 255))
            screen.blit(plus_text, (
                plus_rect.centerx - plus_text.get_width()//2,
                plus_rect.centery - plus_text.get_height()//2
            ))
            
            # Derived stats from this stat
            if name == "Strength":
                melee_dmg = 20 + int(value * 1.5)
                derived = self.font_small.render(f"Melee Damage: {melee_dmg}", True, (200, 100, 100))
            elif name == "Intelligence":
                magic_dmg = 25 + int(value * 2.0)
                derived = self.font_small.render(f"Magic Damage: {magic_dmg}", True, (100, 150, 200))
            else:  # Endurance
                max_hp = 50 + (value * 5)
                max_stam = 50 + (value * 5)
                derived = self.font_small.render(f"Health: {max_hp} | Stamina: {max_stam}", True, (100, 200, 100))
            
            screen.blit(derived, (150, y + 35))
        
        # Instructions
        info = self.font_small.render("Press C to close and start game", True, (150, 150, 150))
        screen.blit(info, (50, 500))
    
    def get_stats(self):
        """Return current stat values"""
        return {
            "strength": self.strength,
            "intelligence": self.intelligence,
            "endurance": self.endurance
        }
    
    def reset_to_defaults(self):
        """Reset stats to defaults"""
        self.stat_points = 5
        self.strength = 10
        self.intelligence = 10
        self.endurance = 10
