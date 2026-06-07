"""
Combat System - Handles spells, abilities, cooldowns, and damage calculations.
"""

import math
from enum import Enum


class SpellType(Enum):
    FIREBALL = "fireball"
    HEAL = "heal"
    NONE = "none"


class Spell:
    """Represents a castable spell"""
    
    def __init__(self, name, spell_type, mana_cost, cooldown, damage, heal_amount=0):
        self.name = name
        self.spell_type = spell_type
        self.mana_cost = mana_cost
        self.cooldown = cooldown
        self.current_cooldown = 0
        self.damage = damage
        self.heal_amount = heal_amount
    
    def update(self):
        """Reduce cooldown"""
        if self.current_cooldown > 0:
            self.current_cooldown -= 1
    
    def can_cast(self):
        """Check if spell is ready to cast"""
        return self.current_cooldown == 0
    
    def cast(self, player_mana):
        """Attempt to cast spell. Returns True if successful."""
        if not self.can_cast():
            return False
        if player_mana < self.mana_cost:
            return False
        
        self.current_cooldown = self.cooldown
        return True
    
    def get_cooldown_percent(self):
        """Return cooldown as percentage (0.0 to 1.0)"""
        if self.cooldown == 0:
            return 0.0
        return self.current_cooldown / self.cooldown


class CombatSystem:
    """Manages player combat stats and spell system"""
    
    def __init__(self, strength=10, intelligence=10, endurance=10):
        self.strength = strength
        self.intelligence = intelligence
        self.endurance = endurance
        
        # Derived stats
        self.update_stats()
        
        # Spells
        self.spells = {
            "fireball": Spell("Fireball", SpellType.FIREBALL, 10, 60, 25),
            "heal": Spell("Heal", SpellType.HEAL, 20, 120, 0, heal_amount=40),
        }
        
        # Combat state
        self.active_projectiles = []
    
    def update_stats(self):
        """Recalculate derived combat stats"""
        self.max_health = 50 + (self.endurance * 5)
        self.max_mana = 20 + (self.intelligence * 3)
        self.max_stamina = 50 + (self.endurance * 5)
        self.melee_damage = 20 + int(self.strength * 1.5)
        self.magic_damage = 25 + int(self.intelligence * 2.0)
    
    def allocate_stat_point(self, stat_name):
        """
        Allocate a stat point. Returns True if successful.
        
        Args:
            stat_name: "strength", "intelligence", or "endurance"
        """
        if hasattr(self, stat_name):
            setattr(self, stat_name, getattr(self, stat_name) + 1)
            self.update_stats()
            return True
        return False
    
    def cast_spell(self, spell_name, player_x, player_y, player_angle, current_mana):
        """
        Attempt to cast a spell. Returns (success, projectile_or_none, mana_used)
        
        Args:
            spell_name: Name of spell to cast
            player_x, player_y: Player position
            player_angle: Direction player is facing
            current_mana: Current mana available
        """
        if spell_name not in self.spells:
            return False, None, 0
        
        spell = self.spells[spell_name]
        
        if not spell.can_cast():
            return False, None, 0
        
        if current_mana < spell.mana_cost:
            return False, None, 0
        
        # Cast successful
        spell.cast(current_mana)
        
        # Create projectile for fireball
        if spell.spell_type == SpellType.FIREBALL:
            projectile = Projectile(
                x=player_x,
                y=player_y,
                angle=player_angle,
                damage=spell.damage,
                speed=8.0,
                max_range=30.0
            )
            self.active_projectiles.append(projectile)
            return True, projectile, spell.mana_cost
        
        # Heal spell doesn't create projectile
        elif spell.spell_type == SpellType.HEAL:
            return True, None, spell.mana_cost
        
        return False, None, 0
    
    def update_projectiles(self):
        """Update all active projectiles and remove expired ones"""
        expired = []
        for i, proj in enumerate(self.active_projectiles):
            proj.update()
            if proj.is_expired():
                expired.append(i)
        
        # Remove expired projectiles (iterate backwards to avoid index issues)
        for i in reversed(expired):
            self.active_projectiles.pop(i)
    
    def get_projectiles_for_rendering(self):
        """Return list of projectiles that are still active"""
        return [p for p in self.active_projectiles if not p.is_expired()]
    
    def update(self):
        """Update combat system (cooldowns, projectiles, etc.)"""
        for spell in self.spells.values():
            spell.update()
        self.update_projectiles()


class Projectile:
    """Represents a projectile (fireball, arrow, etc.)"""
    
    def __init__(self, x, y, angle, damage, speed=5.0, max_range=50.0):
        self.x = x
        self.y = y
        self.angle = angle
        self.damage = damage
        self.speed = speed
        self.max_range = max_range
        self.distance_traveled = 0.0
        self.radius = 0.25
        self.alive = True
    
    def update(self):
        """Update projectile position"""
        if not self.alive:
            return
        
        import math
        move_dist = self.speed * 0.016  # Approximate dt
        self.x += math.cos(self.angle) * move_dist
        self.y += math.sin(self.angle) * move_dist
        self.distance_traveled += move_dist
        
        if self.distance_traveled >= self.max_range:
            self.alive = False
    
    def is_expired(self):
        """Check if projectile is no longer active"""
        return not self.alive
    
    def check_collision(self, obj_x, obj_y, obj_radius=0.3):
        """Check if projectile collides with an object"""
        import math
        dist = math.sqrt((self.x - obj_x)**2 + (self.y - obj_y)**2)
        return dist < (self.radius + obj_radius)


class Enemy:
    """Base class for enemies"""
    
    def __init__(self, x, y, enemy_type="ghost"):
        self.x = x
        self.y = y
        self.enemy_type = enemy_type
        self.health = 50
        self.max_health = 50
        self.damage = 10
        self.speed = 2.0
        self.detection_range = 15.0
        self.attack_range = 1.5
        self.attack_cooldown = 0
        self.attack_speed = 60  # frames between attacks
        self.alive = True
        self.state = "idle"  # idle, chasing, attacking
    
    def update(self, player_x, player_y):
        """Update enemy AI"""
        if not self.alive:
            return
        
        import math
        
        # Calculate distance to player
        dx = player_x - self.x
        dy = player_y - self.y
        dist_to_player = math.sqrt(dx**2 + dy**2)
        
        # Update attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        
        # AI logic
        if dist_to_player < self.detection_range:
            if dist_to_player < self.attack_range:
                self.state = "attacking"
            else:
                self.state = "chasing"
                # Move toward player
                if dist_to_player > 0:
                    move_dist = self.speed * 0.016
                    self.x += (dx / dist_to_player) * move_dist
                    self.y += (dy / dist_to_player) * move_dist
        else:
            self.state = "idle"
    
    def take_damage(self, damage):
        """Apply damage to enemy"""
        self.health -= damage
        if self.health <= 0:
            self.alive = False
            return True  # Enemy died
        return False
    
    def can_attack(self):
        """Check if enemy can perform attack"""
        return self.attack_cooldown == 0
    
    def attack(self):
        """Perform attack action"""
        if self.can_attack():
            self.attack_cooldown = self.attack_speed
            return True
        return False
