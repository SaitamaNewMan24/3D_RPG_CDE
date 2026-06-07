import pygame

class Inventory:
    def __init__(self, icons_dict, sfx_dict):
        self.slots = [None] * 16 
        self.visible = False
        self.rect = pygame.Rect(0, 0, 340, 340) 
        self.icons = icons_dict
        self.sfx = sfx_dict
        self.cols, self.rows = 4, 4
        self.slot_size, self.margin = 60, 15
        self.hovered_slot_index = None
        
    def toggle(self):
        self.visible = not self.visible
        if self.visible and self.sfx.get("door"): self.sfx["door"].play()
            
    def add_item(self, name, qty, item_type, desc, health=0, mana=0):
        for slot in self.slots:
            if slot and slot["name"] == name and slot["type"] not in ["weapon", "artifact"]:
                slot["qty"] += qty
                return True
        for i in range(len(self.slots)):
            if self.slots[i] is None:
                self.slots[i] = {"name": name, "qty": qty, "type": item_type, "desc": desc, "health": health, "mana": mana, "equipped": False}
                return True
        return False

    def get_icon_for_item(self, item):
        n = item["name"]
        icons = {
            "Sword": "sword", "Brass Key": "key", "Silver Key": "key_silver", 
            "Gold Key": "key_gold", "Rusty Dungeon Key": "key_dungeon",
            "Health Potion": "health_potion", "Mana Potion": "mana_potion", 
            "Mystic Artifact": "artifact", "Unlit Torch": "unlit_torch", 
            "Lit Torch": "lit_torch", "Mystic Staff": "staff", "Dagger": "sword"
        }
        return self.icons.get(icons.get(n))

    def get_slot_at(self, pos):
        if not self.visible: return None
        mx, my = pos
        for i in range(16):
            row, col = i // self.cols, i % self.cols
            sx = self.rect.x + 25 + col * (self.slot_size + self.margin)
            sy = self.rect.y + 50 + row * (self.slot_size + self.margin)
            if pygame.Rect(sx, sy, self.slot_size, self.slot_size).collidepoint(mx, my): return i
        return None

    def get_equipped_weapon(self):
        for slot in self.slots:
            if slot and slot.get("equipped") and slot.get("type") == "weapon":
                return slot
        return None

    def find_item_by_name(self, name):
        for i, slot in enumerate(self.slots):
            if slot and slot["name"] == name:
                return i, slot
        return None, None

    def draw_tooltip(self, screen, mouse_pos, font_small, font_large, item):
        """Draw a styled tooltip box for the hovered item"""
        tooltip_width = 220
        tooltip_height = 100
        padding = 10
        
        # Tooltip position - offset from mouse
        tooltip_x = mouse_pos[0] + 15
        tooltip_y = mouse_pos[1] + 15
        
        # Keep tooltip on screen
        if tooltip_x + tooltip_width > screen.get_width():
            tooltip_x = mouse_pos[0] - tooltip_width - 15
        if tooltip_y + tooltip_height > screen.get_height():
            tooltip_y = mouse_pos[1] - tooltip_height - 15
        
        # Draw tooltip background with dark style
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        pygame.draw.rect(screen, (30, 30, 35), tooltip_rect)
        pygame.draw.rect(screen, (200, 180, 100), tooltip_rect, 2)  # Gold border
        
        # Draw item name (yellow/gold)
        item_name = font_large.render(item["name"], True, (255, 215, 0))
        screen.blit(item_name, (tooltip_x + padding, tooltip_y + padding))
        
        # Draw item type and description (light gray)
        item_type_text = font_small.render(f"Type: {item['type'].upper()}", True, (200, 200, 200))
        screen.blit(item_type_text, (tooltip_x + padding, tooltip_y + padding + 25))
        
        # Draw description
        desc_text = font_small.render(item["desc"], True, (180, 180, 180))
        screen.blit(desc_text, (tooltip_x + padding, tooltip_y + padding + 45))
        
        # Draw quantity if > 1
        if item.get("qty", 1) > 1:
            qty_text = font_small.render(f"Qty: {item['qty']}", True, (100, 255, 100))
            screen.blit(qty_text, (tooltip_x + padding, tooltip_y + padding + 65))

    def draw(self, screen, mouse_pos, font):
        if not self.visible: return
        sw, sh = screen.get_size()
        # --- Lifted the inventory up so it doesn't overlap the action bar! ---
        self.rect.center = (sw//2, sh//2 - 40)
        
        # Create a more stylized background surface with semi-transparency
        s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        s.fill((30, 30, 35, 230))
        screen.blit(s, (self.rect.x, self.rect.y))
        # Draw gold border for that classic RPG look
        pygame.draw.rect(screen, (200, 180, 100), self.rect, 3)
        
        # Track hovered slot for tooltip
        self.hovered_slot_index = self.get_slot_at(mouse_pos)
        
        for i in range(16):
            row, col = i // self.cols, i % self.cols
            sx = self.rect.x + 25 + col * (self.slot_size + self.margin)
            sy = self.rect.y + 50 + row * (self.slot_size + self.margin)
            s_rect = pygame.Rect(sx, sy, self.slot_size, self.slot_size)
            
            # Highlight hovered slot with a lighter border
            if i == self.hovered_slot_index:
                pygame.draw.rect(screen, (60, 60, 65), s_rect)
                pygame.draw.rect(screen, (150, 200, 255), s_rect, 3)  # Blue highlight
            else:
                pygame.draw.rect(screen, (60, 60, 65), s_rect)
                pygame.draw.rect(screen, (100, 100, 110), s_rect, 2)
            
            slot = self.slots[i]
            if slot:
                icon = self.get_icon_for_item(slot)
                if icon: screen.blit(pygame.transform.scale(icon, (50, 50)), (sx + 5, sy + 5))
                if slot.get("qty", 1) > 1:
                    # Draw quantity number in bottom-right corner
                    qty_font = pygame.font.SysFont("georgia", 14, bold=True)
                    qty_text = qty_font.render(str(slot["qty"]), True, (100, 255, 100))
                    screen.blit(qty_text, (sx + 40, sy + 40))
        
        # Draw tooltip on hover
        if self.hovered_slot_index is not None and self.slots[self.hovered_slot_index]:
            font_small = pygame.font.SysFont("georgia", 12)
            font_large = pygame.font.SysFont("georgia", 14, bold=True)
            self.draw_tooltip(screen, mouse_pos, font_small, font_large, self.slots[self.hovered_slot_index])
