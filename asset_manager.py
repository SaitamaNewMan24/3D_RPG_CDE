"""
Asset Manager - Handles loading, caching, and management of game assets.
Includes textures, sprites, icons, and audio files.
"""

import pygame
import os
from enum import Enum


class AssetType(Enum):
    TEXTURE = "texture"
    SPRITE = "sprite"
    ICON = "icon"
    AUDIO = "audio"


class AssetManager:
    """Centralized asset loading and caching system"""
    
    def __init__(self):
        self.textures = {}
        self.sprites = {}
        self.icons = {}
        self.audio = {}
        self.missing_asset_placeholder = None
        self._create_placeholder()
    
    def _create_placeholder(self):
        """Create a placeholder surface for missing assets"""
        self.missing_asset_placeholder = pygame.Surface((64, 64))
        self.missing_asset_placeholder.fill((255, 0, 255))  # Magenta
        pygame.draw.rect(self.missing_asset_placeholder, (0, 0, 0), (0, 0, 64, 64), 2)
    
    def load_image(self, filename, asset_type=AssetType.TEXTURE, alpha=False):
        """
        Load image with caching. Returns cached asset if already loaded.
        
        Args:
            filename: Path to image file
            asset_type: Type of asset (TEXTURE, SPRITE, ICON)
            alpha: Whether to preserve alpha channel
            
        Returns:
            pygame.Surface or placeholder if file not found
        """
        cache = getattr(self, f"{asset_type.name.lower()}s", {})
        
        if filename in cache:
            return cache[filename]
        
        if not os.path.exists(filename):
            print(f"[AssetManager] Missing asset: {filename}")
            return self.missing_asset_placeholder
        
        try:
            img = pygame.image.load(filename)
            img = img.convert_alpha() if alpha else img.convert()
            cache[filename] = img
            print(f"[AssetManager] Loaded {asset_type.value}: {filename}")
            return img
        except Exception as e:
            print(f"[AssetManager] Failed to load {filename}: {e}")
            return self.missing_asset_placeholder
    
    def load_audio(self, filename):
        """
        Load audio file with caching.
        
        Args:
            filename: Path to audio file
            
        Returns:
            pygame.mixer.Sound or None if loading failed
        """
        if filename in self.audio:
            return self.audio[filename]
        
        if not os.path.exists(filename):
            print(f"[AssetManager] Missing audio: {filename}")
            return None
        
        try:
            sound = pygame.mixer.Sound(filename)
            self.audio[filename] = sound
            print(f"[AssetManager] Loaded audio: {filename}")
            return sound
        except Exception as e:
            print(f"[AssetManager] Failed to load audio {filename}: {e}")
            return None
    
    def get_texture(self, filename):
        """Get or load a texture"""
        return self.load_image(filename, AssetType.TEXTURE, alpha=False)
    
    def get_sprite(self, filename):
        """Get or load a sprite with alpha channel"""
        return self.load_image(filename, AssetType.SPRITE, alpha=True)
    
    def get_icon(self, filename):
        """Get or load an icon with alpha channel"""
        return self.load_image(filename, AssetType.ICON, alpha=True)
    
    def get_sound(self, filename):
        """Get or load a sound effect"""
        return self.load_audio(filename)
    
    def build_icon_dict(self):
        """
        Build a dictionary of commonly used icons for inventory.
        Returns dict with item name -> icon surface mapping.
        """
        icon_files = {
            "ancient artifact": "artifact.png",
            "health potion": "health_potion.png",
            "mana potion": "mana_potion.png",
            "dagger": "dagger.png",
            "key": "key.png",
            "key silver": "key_silver.png",
            "key gold": "key_gold.png",
        }
        
        icons_dict = {}
        for item_name, filename in icon_files.items():
            icon = self.get_icon(filename)
            if icon is not self.missing_asset_placeholder:
                icons_dict[item_name] = icon
        
        return icons_dict
    
    def clear_cache(self):
        """Clear all asset caches"""
        self.textures.clear()
        self.sprites.clear()
        self.icons.clear()
        self.audio.clear()


# Global asset manager instance
_asset_manager = None


def get_asset_manager():
    """Get or create the global asset manager"""
    global _asset_manager
    if _asset_manager is None:
        _asset_manager = AssetManager()
    return _asset_manager
