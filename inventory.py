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
            "Lit Torch": "lit_torch", "Mystic Staff": "staff"
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

    def draw(self, screen, mouse_pos, font):
        if not self.visible: return
        sw, sh = screen.get_size()
        # --- Lifted the inventory up so it doesn't overlap the action bar! ---
        self.rect.center = (sw//2, sh//2 - 40)
        
        s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        s.fill((30, 30, 35, 230))
        screen.blit(s, (self.rect.x, self.rect.y))
        pygame.draw.rect(screen, (200, 180, 100), self.rect, 3)
        
        for i in range(16):
            row, col = i // self.cols, i % self.cols
            sx = self.rect.x + 25 + col * (self.slot_size + self.margin)
            sy = self.rect.y + 50 + row * (self.slot_size + self.margin)
            s_rect = pygame.Rect(sx, sy, self.slot_size, self.slot_size)
            pygame.draw.rect(screen, (60, 60, 65), s_rect)
            pygame.draw.rect(screen, (100, 100, 110), s_rect, 2)
            
            slot = self.slots[i]
            if slot:
                icon = self.get_icon_for_item(slot)
                if icon: screen.blit(pygame.transform.scale(icon, (50, 50)), (sx + 5, sy + 5))
                if slot.get("qty", 1) > 1:
                    screen.blit(font.render(str(slot["qty"]), True, (255, 255, 255)), (sx + 40, sy + 40))
        
        # Simple hover text
        hovered = self.get_slot_at(mouse_pos)
        if hovered is not None and self.slots[hovered]:
            screen.blit(font.render(self.slots[hovered]["name"], True, (255, 215, 0)), (mouse_pos[0]+10, mouse_pos[1]+10))