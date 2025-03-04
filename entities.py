import pygame
import random
import math
from logger import game_logger
import time
import sys

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((40, 40))
        self.image.fill((0, 0, 255))  # Blue player
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        # Core stats
        self.max_health = 100
        self.health = self.max_health
        self.speed = 5
        self.damage = 10
        
        # Elemental properties
        self.wetness = 0  # 0-100 scale
        self.fire_resistance = 0  # Derived from wetness
        self.has_obsidian_armor = False
        self.obsidian_armor_level = 0  # 0-100 scale
        
        # Tracking stats
        self.current_area = "BEACH"  # BEACH, VOLCANO, ABYSS
        self.damage_dealt = 0
        self.damage_taken = 0
        
        # Add progression tracking
        self.progression = {
            "areas_visited": {"BEACH"},
            "total_movement": 0,
            "attacks_performed": 0,
            "damage_dealt_by_area": {"BEACH": 0, "VOLCANO": 0, "ABYSS": 0},
            "damage_taken_by_enemy_type": {"water": 0, "lava": 0, "abyss": 0},
            "time_in_areas": {"BEACH": 0, "VOLCANO": 0, "ABYSS": 0},
            "deaths": 0,
            "obsidian_formed_events": 0,
            "wetness_max_reached": 0,
            "area_transitions": []
        }
        
        # Session tracking
        self.session_start_time = time.time()
        self.last_area_time = time.time()
        self.last_health = self.health
        self.last_position = (self.rect.x, self.rect.y)
        self.last_state_log = time.time()
        self.last_action_time = time.time()  # For detecting player inactivity
        
        # Log initial state with full details
        game_logger.debug("STATE_player_initialized", {
            "position": {"x": self.rect.x, "y": self.rect.y},
            "health": self.health,
            "max_health": self.max_health,
            "speed": self.speed,
            "damage": self.damage,
            "wetness": self.wetness,
            "fire_resistance": self.fire_resistance,
            "obsidian_armor": self.obsidian_armor_level,
            "current_area": self.current_area,
            "session_id": id(self),
            "memory_size": sys.getsizeof(self)
        }, "high")
        
        # Log initial state (legacy method)
        game_logger.log_player_state(self)
    
    def update(self, keys):
        """Update player position based on keyboard input"""
        # Log initial state
        pre_pos = {"x": self.rect.x, "y": self.rect.y}
        pre_wetness = self.wetness
        pre_fire_resistance = self.fire_resistance
        pre_health = self.health
        
        # First run checks for analytics
        current_time = time.time()
        time_since_last_log = current_time - self.last_state_log
        inactive_threshold = 5.0  # seconds
        
        # Check for player inactivity for tutorial suggestions
        if current_time - self.last_action_time > inactive_threshold:
            # Player hasn't moved in a while, might be stuck
            game_logger.debug("STATE_player_inactive", {
                "inactive_duration": current_time - self.last_action_time,
                "position": {"x": self.rect.x, "y": self.rect.y},
                "current_area": self.current_area,
                "health": self.health,
                "wetness": self.wetness,
                "obsidian_armor": self.obsidian_armor_level
            }, "high")
        
        # Track time spent in current area
        self.progression["time_in_areas"][self.current_area] += time_since_last_log
        
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]:
            dx = -self.speed
        if keys[pygame.K_RIGHT]:
            dx = self.speed
        if keys[pygame.K_UP]:
            dy = -self.speed
        if keys[pygame.K_DOWN]:
            dy = self.speed
            
        # Log movement input
        if dx != 0 or dy != 0:
            self.last_action_time = current_time  # Reset inactivity timer
            game_logger.debug("STATE_player_movement_input", {
                "raw_dx": dx,
                "raw_dy": dy,
                "speed": self.speed,
                "is_diagonal": dx != 0 and dy != 0,
                "current_area": self.current_area,
                "timestamp": current_time
            }, "low")
            
        # Normalize diagonal movement
        if dx != 0 and dy != 0:
            dx = dx * 0.7071  # 1/sqrt(2)
            dy = dy * 0.7071
            
        self.rect.x += dx
        self.rect.y += dy
        
        # Update total movement for progression tracking
        if dx != 0 or dy != 0:
            movement_distance = math.sqrt(dx*dx + dy*dy)
            self.progression["total_movement"] += movement_distance
        
        # Log position after movement
        if dx != 0 or dy != 0:
            game_logger.debug("STATE_player_position_changed", {
                "old_position": pre_pos,
                "new_position": {"x": self.rect.x, "y": self.rect.y},
                "delta": {"dx": dx, "dy": dy},
                "total_movement": self.progression["total_movement"],
                "current_area": self.current_area
            }, "low")
        
        # Keep player on screen
        orig_x, orig_y = self.rect.x, self.rect.y
        screen_width, screen_height = pygame.display.get_surface().get_size()
        self.rect.x = max(0, min(self.rect.x, screen_width - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, screen_height - self.rect.height))
        
        # Log boundary correction if needed
        if orig_x != self.rect.x or orig_y != self.rect.y:
            game_logger.debug("STATE_player_boundary_collision", {
                "attempted_position": {"x": orig_x, "y": orig_y},
                "corrected_position": {"x": self.rect.x, "y": self.rect.y},
                "screen_bounds": {"width": screen_width, "height": screen_height},
                "current_area": self.current_area
            }, "normal")
        
        # Update derived stats
        self.fire_resistance = self.wetness * 0.9  # 90% conversion of wetness to fire resistance
        
        # Decay wetness slightly over time
        if self.wetness > 0:
            old_wetness = self.wetness
            self.wetness = max(0, self.wetness - 0.1)
            
            # Log wetness decay
            if abs(old_wetness - self.wetness) > 0.001:  # Only log meaningful changes
                game_logger.debug("STATE_player_wetness_decay", {
                    "old_wetness": old_wetness,
                    "new_wetness": self.wetness,
                    "decay_amount": old_wetness - self.wetness,
                    "fire_resistance": self.fire_resistance,
                    "current_area": self.current_area
                }, "low")
                
        # Track important delta changes for tutorial and analysis
        # These are changes significant enough to potentially trigger tutorial elements
        if current_time - self.last_state_log >= 1.0:  # Log state deltas at most once per second
            # Check if health has changed significantly
            if abs(pre_health - self.health) > 0:
                game_logger.debug("DELTA_player_health", {
                    "delta": self.health - pre_health,
                    "old_health": pre_health,
                    "new_health": self.health,
                    "percent_change": (self.health - pre_health) / max(1, pre_health) * 100,
                    "current_area": self.current_area,
                    "timestamp": current_time
                }, "high")
            
            # Check for wetness/fire resistance changes
            if abs(pre_wetness - self.wetness) > 5:
                # Significant wetness change
                game_logger.debug("DELTA_player_wetness", {
                    "delta": self.wetness - pre_wetness,
                    "old_wetness": pre_wetness,
                    "new_wetness": self.wetness,
                    "old_fire_resistance": pre_fire_resistance,
                    "new_fire_resistance": self.fire_resistance,
                    "current_area": self.current_area
                }, "high")
                
                # Track max wetness for progression
                if self.wetness > self.progression["wetness_max_reached"]:
                    self.progression["wetness_max_reached"] = self.wetness
                    game_logger.debug("STATE_player_progression", {
                        "type": "wetness_milestone",
                        "value": self.wetness,
                        "current_area": self.current_area
                    }, "high")
            
            # Update last log time
            self.last_state_log = current_time
        
        # Log state regularly
        if random.random() < 0.05:  # Reduce logging frequency for performance
            game_logger.log_player_state(self)
    
    def take_damage(self, amount, damage_type="normal"):
        """
        Handle player taking damage with elemental effects
        Returns dict with results of the damage including side effects
        """
        result = {"actual_damage": amount, "resistance_applied": 0, "effects": []}
        
        # Apply appropriate resistance based on damage type
        if damage_type == "water":
            # Water damage increases wetness
            old_wetness = self.wetness
            self.wetness = min(100, self.wetness + amount * 2)
            result["effects"].append(f"wetness_increased:{self.wetness - old_wetness}")
            
        elif damage_type == "fire":
            # Fire damage is reduced by fire resistance
            resistance = self.fire_resistance
            reduced_damage = max(1, amount * (1 - (resistance / 100)))
            result["resistance_applied"] = amount - reduced_damage
            result["actual_damage"] = reduced_damage
            
            # If player is wet, fire damage can create obsidian armor
            if self.wetness > 20 and not self.has_obsidian_armor:
                armor_gain = min(10, self.wetness / 10)
                self.obsidian_armor_level += armor_gain
                result["effects"].append(f"obsidian_forming:{armor_gain}")
                
                if self.obsidian_armor_level >= 50:
                    self.has_obsidian_armor = True
                    result["effects"].append("obsidian_armor_formed")
                
                # Fire reduces wetness
                wetness_loss = min(self.wetness, amount / 10)
                self.wetness -= wetness_loss
                result["effects"].append(f"wetness_decreased:{wetness_loss}")
                
        # Apply the actual damage but prevent health from going below 0
        self.health = max(0, self.health - result["actual_damage"])
        self.damage_taken += result["actual_damage"]
        
        # Log the damage event
        game_logger.debug("STATE_player_damage", {
            "damage_type": damage_type,
            "raw_damage": amount,
            "actual_damage": result["actual_damage"],
            "health_remaining": self.health,
            "wetness": self.wetness,
            "obsidian_armor": self.obsidian_armor_level,
            "effects": result["effects"]
        }, "high")
        
        return result
    
    def attack(self, enemy):
        """Attack an enemy and return the result"""
        base_damage = self.damage
        
        # Log attack initiation
        game_logger.debug("STATE_player_attack_initiate", {
            "target_enemy_id": id(enemy),
            "target_enemy_type": enemy.type,
            "base_damage": base_damage,
            "player_position": {"x": self.rect.x, "y": self.rect.y},
            "enemy_position": {"x": enemy.rect.x, "y": enemy.rect.y},
            "player_has_obsidian": self.has_obsidian_armor,
            "obsidian_level": self.obsidian_armor_level,
            "timestamp": time.time()
        }, "high")
        
        # In abyss, need obsidian armor to deal damage
        if enemy.area == "ABYSS" and not self.has_obsidian_armor:
            game_logger.debug("DEV_combat_ineffective", {
                "reason": "no_obsidian_armor",
                "target_type": enemy.type,
                "area": enemy.area,
                "attempted_damage": base_damage,
                "timestamp": time.time()
            }, "high")
            return {"damage": 0, "effects": ["attack_ineffective_no_obsidian"]}
        
        # Bonus damage with obsidian armor
        if self.has_obsidian_armor:
            obsidian_bonus = self.obsidian_armor_level / 5
            base_damage += obsidian_bonus
            
            game_logger.debug("DEV_obsidian_damage_bonus", {
                "obsidian_level": self.obsidian_armor_level,
                "damage_bonus": obsidian_bonus,
                "base_damage": self.damage,
                "total_damage": base_damage,
                "timestamp": time.time()
            }, "normal")
        
        # Execute the attack
        damage_dealt = enemy.take_damage(base_damage)
        self.damage_dealt += damage_dealt["actual_damage"]
        
        # Log attack result
        game_logger.debug("STATE_player_attack_result", {
            "target_enemy_id": id(enemy),
            "target_enemy_type": enemy.type, 
            "damage_attempted": base_damage,
            "damage_dealt": damage_dealt["actual_damage"],
            "enemy_health_remaining": enemy.health if hasattr(enemy, "health") else 0,
            "enemy_defeated": "enemy_defeated" in damage_dealt.get("effects", []),
            "effects": damage_dealt.get("effects", []),
            "timestamp": time.time()
        }, "high")
        
        return damage_dealt


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, area="BEACH"):
        super().__init__()
        self.area = area
        self.type = "generic"
        
        # Set properties based on area/type
        if area == "BEACH":
            self.setup_water_enemy()
        elif area == "VOLCANO":
            self.setup_lava_enemy()
        elif area == "ABYSS":
            self.setup_abyss_enemy()
            
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        # Movement variables
        self.speed = random.uniform(1.0, 3.0)
        self.direction = random.uniform(0, 2 * math.pi)
        self.direction_change_time = random.randint(30, 90)
        self.direction_timer = 0
        
        # Log enemy creation
        game_logger.log_enemy_spawned(self)
    
    def setup_water_enemy(self):
        self.type = "water_splasher"
        self.image = pygame.Surface((30, 30))
        self.image.fill((0, 200, 255))  # Light blue for water enemies
        self.health = 20
        self.max_health = 20
        self.damage = 1
        self.damage_type = "water"
        self.splash_amount = 10  # How much wetness to add when attacking
        
    def setup_lava_enemy(self):
        self.type = "lava_splasher"
        self.image = pygame.Surface((35, 35))
        self.image.fill((255, 100, 0))  # Orange for lava enemies
        self.health = 100
        self.max_health = 100
        self.damage = 1000
        self.damage_type = "fire"
    
    def setup_abyss_enemy(self):
        self.type = "abyss_horror"
        self.image = pygame.Surface((40, 40))
        self.image.fill((50, 0, 50))  # Dark purple for abyss enemies
        self.health = 500
        self.max_health = 500
        self.damage = 50
        self.damage_type = "void"
        
    def update(self, player):
        """Update enemy position and behavior"""
        # Log initial state for debugging
        pre_pos = {"x": self.rect.x, "y": self.rect.y}
        pre_direction = self.direction
        
        # Change direction occasionally
        self.direction_timer += 1
        direction_changed = False
        
        if self.direction_timer >= self.direction_change_time:
            old_direction = self.direction
            self.direction = random.uniform(0, 2 * math.pi)
            self.direction_timer = 0
            self.direction_change_time = random.randint(30, 90)
            direction_changed = True
            
            # Log direction change
            game_logger.debug("DEV_enemy_direction_change", {
                "enemy_id": id(self),
                "enemy_type": self.type,
                "old_direction": old_direction,
                "new_direction": self.direction,
                "next_change_time": self.direction_change_time,
                "reason": "timer_expired"
            }, "low")
        
        # Calculate distance to player
        dx_to_player = player.rect.x - self.rect.x
        dy_to_player = player.rect.y - self.rect.y
        distance_to_player = math.sqrt(dx_to_player**2 + dy_to_player**2)
        
        # Basic AI: move toward player with some randomness
        move_toward_player = False
        if random.random() < 0.7:  # 70% chance to move toward player
            old_direction = self.direction
            angle = math.atan2(dy_to_player, dx_to_player)
            self.direction = angle
            move_toward_player = True
            direction_changed = direction_changed or (old_direction != self.direction)
            
            # Log AI decision to move toward player
            if old_direction != self.direction:
                game_logger.debug("DEV_enemy_ai_decision", {
                    "enemy_id": id(self),
                    "enemy_type": self.type,
                    "decision": "move_toward_player",
                    "old_direction": old_direction,
                    "new_direction": self.direction,
                    "distance_to_player": distance_to_player,
                    "player_position": {"x": player.rect.x, "y": player.rect.y}
                }, "low")
            
        # Calculate movement
        dx = math.cos(self.direction) * self.speed
        dy = math.sin(self.direction) * self.speed
        
        # Move the enemy
        self.rect.x += dx
        self.rect.y += dy
        
        # Log movement details if position changed
        if pre_pos["x"] != self.rect.x or pre_pos["y"] != self.rect.y:
            game_logger.debug("DEV_enemy_movement", {
                "enemy_id": id(self),
                "enemy_type": self.type,
                "old_position": pre_pos,
                "new_position": {"x": self.rect.x, "y": self.rect.y},
                "delta": {"dx": dx, "dy": dy},
                "speed": self.speed,
                "direction": self.direction,
                "direction_changed": direction_changed,
                "moving_toward_player": move_toward_player
            }, "low")
        
        # Keep enemy on screen
        orig_x, orig_y = self.rect.x, self.rect.y
        screen_width, screen_height = pygame.display.get_surface().get_size()
        self.rect.x = max(0, min(self.rect.x, screen_width - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, screen_height - self.rect.height))
        
        # Log boundary correction if needed
        if orig_x != self.rect.x or orig_y != self.rect.y:
            game_logger.debug("DEV_enemy_boundary_correction", {
                "enemy_id": id(self),
                "enemy_type": self.type,
                "attempted_position": {"x": orig_x, "y": orig_y},
                "corrected_position": {"x": self.rect.x, "y": self.rect.y}
            }, "low")
        
        # Check for collision with player
        collision = self.rect.colliderect(player.rect)
        
        # Log collision detection
        if collision:
            game_logger.debug("DEV_enemy_player_collision", {
                "enemy_id": id(self),
                "enemy_type": self.type,
                "enemy_position": {"x": self.rect.x, "y": self.rect.y},
                "player_position": {"x": player.rect.x, "y": player.rect.y},
                "distance": distance_to_player,
                "collision_detected": True
            }, "normal")
            
            # Attack player if colliding
            self.attack(player)
    
    def take_damage(self, amount):
        """Handle enemy taking damage"""
        self.health -= amount
        
        result = {
            "actual_damage": amount,
            "effects": []
        }
        
        if self.health <= 0:
            result["effects"].append("enemy_defeated")
            self.kill()
            
        # Log damage
        game_logger.debug("DEV_enemy_damage", {
            "enemy_type": self.type,
            "enemy_id": id(self),
            "damage": amount,
            "health_remaining": self.health,
            "defeated": self.health <= 0
        }, "normal")
            
        return result
    
    def attack(self, player):
        """Attack the player"""
        # Log attack initiation
        game_logger.debug("DEV_enemy_attack_initiate", {
            "enemy_id": id(self),
            "enemy_type": self.type,
            "damage_type": self.damage_type,
            "base_damage": self.damage,
            "player_health": player.health,
            "player_wetness": player.wetness,
            "player_fire_resistance": player.fire_resistance,
            "player_obsidian": player.obsidian_armor_level,
            "timestamp": time.time()
        }, "high")
        
        # Add some randomness to attack success
        hit_chance = 0.8  # 80% chance to hit
        roll = random.random()
        hit_success = roll < hit_chance
        
        if hit_success:
            # Execute the attack
            result = player.take_damage(self.damage, self.damage_type)
            
            # Log combat event
            game_logger.log_combat_event(self, player, self.damage, self.damage_type, result)
            
            # Additional detailed logging
            game_logger.debug("DEV_enemy_attack_details", {
                "roll": roll,
                "hit_chance": hit_chance,
                "hit_success": hit_success,
                "raw_damage": self.damage,
                "actual_damage": result["actual_damage"],
                "resistance_applied": result.get("resistance_applied", 0),
                "player_health_remaining": player.health,
                "effects_triggered": result.get("effects", []),
                "timestamp": time.time()
            }, "high")
            
            return result
        else:
            # Attack missed
            game_logger.debug("DEV_attack_missed", {
                "attacker": self.type,
                "attacker_id": id(self),
                "target": "player",
                "roll": roll,
                "hit_chance": hit_chance,
                "timestamp": time.time()
            }, "normal")
            return {"actual_damage": 0, "effects": ["missed"]}


class AreaPortal(pygame.sprite.Sprite):
    def __init__(self, x, y, source_area, target_area):
        super().__init__()
        self.image = pygame.Surface((50, 50))
        self.image.fill((255, 255, 255))  # White portal
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.source_area = source_area
        self.target_area = target_area
        
        game_logger.debug("DEV_portal_created", {
            "source_area": source_area,
            "target_area": target_area,
            "position": {"x": x, "y": y}
        }, "normal")


# Specialized enemy classes for the tutorial
class WaterSplasher(Enemy):
    """Water enemy that increases player wetness when attacking"""
    def __init__(self, x, y):
        super().__init__(x, y, "BEACH")
        self.type = "water"
        # Ensure it's properly initialized as a water enemy
        self.setup_water_enemy()
        
        # Log specialized enemy creation
        game_logger.debug("DEV_water_splasher_created", {
            "x": x, 
            "y": y,
            "health": self.health,
            "damage": self.damage,
            "splash_effect": self.splash_amount
        }, "low")


class LavaSprite(Enemy):
    """Lava enemy that deals massive damage unless player has water resistance"""
    def __init__(self, x, y):
        super().__init__(x, y, "VOLCANO")
        self.type = "lava"
        # Ensure it's properly initialized as a lava enemy
        self.setup_lava_enemy()
        
        # Log specialized enemy creation
        game_logger.debug("DEV_lava_sprite_created", {
            "x": x, 
            "y": y,
            "health": self.health,
            "damage": self.damage
        }, "low")


class AbyssalEntity(Enemy):
    """Abyss enemy that can only be damaged by obsidian armor"""
    def __init__(self, x, y):
        super().__init__(x, y, "ABYSS")
        self.type = "abyss"
        # Ensure it's properly initialized as an abyss enemy
        self.setup_abyss_enemy()
        
        # Log specialized enemy creation
        game_logger.debug("DEV_abyssal_entity_created", {
            "x": x, 
            "y": y,
            "health": self.health,
            "damage": self.damage,
            "requires_obsidian": True
        }, "low")
