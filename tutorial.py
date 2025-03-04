"""
Tutorial system for Elemental Game.
Provides a step-by-step introduction to gameplay mechanics.
"""
import pygame
import time
from logger import game_logger

class Tutorial:
    """Tutorial system to teach players game mechanics in a controlled environment."""
    
    def __init__(self, game):
        """Initialize tutorial with game reference."""
        self.game = game
        self.active = False
        self.completed = False
        self.current_step = 0
        self.step_start_time = 0
        self.has_attacked = False
        self.has_moved = False
        self.has_been_splashed = False
        self.has_visited_lava = False
        self.has_formed_obsidian = False
        
        # Zoom level and pulse effect for highlights
        self.current_zoom = 1.0
        self.target_zoom = 1.0
        self.pulse_alpha = 50
        self.pulse_direction = 1
        self.last_pulse_time = 0
        
        # Enemies for tutorial demonstrations
        self.water_enemy_for_tutorial = None
        self.lava_enemy_for_tutorial = None
        
        # Define tutorial steps with progression
        self.steps = [
            {
                "id": "welcome",
                "message": "Welcome to the Elemental Progression Game!\nPress SPACE to continue.",
                "zoom_level": 1.0,
                "highlight": None,
                "required_action": "SPACE",
                "duration": 0,  # Wait for player input
                "test_goal": "Introduce game and verify UI rendering"
            },
            {
                "id": "player_intro",
                "message": "This is YOU, the player.\nYou'll explore different elemental areas.\nPress SPACE to continue.",
                "zoom_level": 1.5,
                "highlight": "PLAYER",
                "required_action": "SPACE",
                "duration": 0,
                "test_goal": "Verify player character rendering"
            },
            {
                "id": "movement",
                "message": "Use WASD or arrow keys to move around.\nTry moving now to continue.",
                "zoom_level": 1.2,
                "highlight": "PLAYER",
                "required_action": "MOVE",
                "duration": 0,
                "test_goal": "Verify player movement mechanics"
            },
            {
                "id": "enemy_intro",
                "message": "This is a Water Splasher enemy.\nThey'll try to splash water on you.\nPress SPACE to continue.",
                "zoom_level": 1.2,
                "highlight": "WATER_ENEMY",
                "required_action": "SPACE",
                "duration": 0,
                "test_goal": "Verify enemy rendering and AI behavior"
            },
            {
                "id": "getting_wet",
                "message": "Getting splashed by water increases your Wetness.\nMove close to the water enemy and let it splash you.",
                "zoom_level": 1.0,
                "highlight": "WATER_ENEMY",
                "required_action": "GET_SPLASHED",
                "duration": 0,
                "test_goal": "Verify wetness attribute and enemy attack mechanics"
            },
            {
                "id": "combat",
                "message": "Press SPACE or click on enemies to attack them.\nTry attacking the Water Splasher now.",
                "zoom_level": 1.0,
                "highlight": "WATER_ENEMY",
                "required_action": "ATTACK",
                "duration": 0,
                "test_goal": "Verify player attack mechanics"
            },
            {
                "id": "elemental_progression",
                "message": "As you get wetter, you gain resistance to fire.\nLet's introduce you to lava enemies...",
                "zoom_level": 1.0,
                "highlight": None,
                "required_action": "SPACE",
                "duration": 6,
                "test_goal": "Verify elemental progression mechanics explanation"
            },
            {
                "id": "lava_intro",
                "message": "This is a Lava Sprite. They do massive damage unless you're wet.\nApproach the lava enemy to continue.",
                "zoom_level": 1.2,
                "highlight": "LAVA_ENEMY",
                "required_action": "APPROACH_LAVA",
                "duration": 0,
                "test_goal": "Verify lava enemy rendering and behavior"
            },
            {
                "id": "obsidian_formation",
                "message": "When lava hits a wet player, Obsidian Armor forms!\nThis armor is needed for the final area.\nPress SPACE to continue.",
                "zoom_level": 1.0,
                "highlight": "PLAYER",
                "required_action": "SPACE",
                "duration": 6,
                "test_goal": "Verify obsidian armor formation mechanics"
            },
            {
                "id": "portal_intro",
                "message": "See the portal at the right side of the screen?\nPortals take you to new areas with different challenges.\nPress SPACE to continue.",
                "zoom_level": 0.8,
                "highlight": "PORTAL",
                "required_action": "SPACE",
                "duration": 5,
                "test_goal": "Verify portal rendering"
            },
            {
                "id": "game_summary",
                "message": "Game Goal: Progress through all areas by gaining elemental resistances.\nYou're now ready to begin your adventure!\nPress SPACE to start.",
                "zoom_level": 1.0,
                "highlight": None,
                "required_action": "SPACE",
                "duration": 0,
                "test_goal": "Final verification of player understanding and UI mechanics"
            }
        ]
        
        # Tutorial success metrics
        self.mechanics_tested = {
            "movement": False,
            "enemy_rendering": False,
            "wetness": False,
            "player_attack": False,
            "elemental_progression": False,
            "portal": False
        }
        
        # Visual properties
        self.font_large = pygame.font.SysFont(None, 48)
        self.font_small = pygame.font.SysFont(None, 28)
        self.box_color = (0, 0, 0, 180)  # Semi-transparent black
        self.text_color = (255, 255, 255)  # White
        self.highlight_color = (255, 255, 0, 100)  # Semi-transparent yellow
        
        # Timing
        self.pulse_interval = 0.5  # Pulse highlight every 0.5 seconds
        
        # Camera/zoom effects
        self.base_zoom = 1.0
        
        # Progress tracking
        self.water_enemy_for_tutorial = None
        
        # Log tutorial initiation
        game_logger.debug("tutorial_initialized", {
            "total_steps": len(self.steps)
        }, "normal")
    
    def start(self):
        """Begin the tutorial sequence."""
        if self.completed:
            # Tutorial already completed
            return
            
        # Create a clean tutorial environment
        self.setup_tutorial_environment()
        
        # Activate tutorial
        self.active = True
        self.current_step = 0
        self.step_start_time = time.time()
        self.target_zoom = self.steps[0]["zoom_level"]
        
        # Log tutorial start
        game_logger.debug("tutorial_started", {
            "current_step": self.current_step,
            "message": self.steps[0]["message"]
        }, "normal")
    
    def setup_tutorial_environment(self):
        """Set up a controlled environment for the tutorial."""
        # Clear existing enemies and portals
        for sprite in self.game.enemies:
            sprite.kill()
        for sprite in self.game.portals:
            sprite.kill()
        
        # Reset player position to center
        self.game.player.rect.x = self.game.width // 2
        self.game.player.rect.y = self.game.height // 2
        
        # Reset player attributes to default
        self.game.player.wetness = 0
        self.game.player.obsidian_level = 0
        
        # Create a water enemy for the tutorial at right side
        water_enemy_x = self.game.width // 2 + 150
        water_enemy_y = self.game.height // 2
        self.water_enemy_for_tutorial = self.create_tutorial_enemy(water_enemy_x, water_enemy_y, "BEACH")
        
        # Create a lava enemy (initially off-screen) 
        lava_enemy_x = self.game.width + 100  # Off-screen to start
        lava_enemy_y = self.game.height // 2
        self.lava_enemy_for_tutorial = self.create_tutorial_enemy(lava_enemy_x, lava_enemy_y, "VOLCANO")
        
        # Add a portal for demonstration
        from entities import AreaPortal
        portal = AreaPortal(self.game.width - 100, self.game.height // 2, "BEACH", "VOLCANO")
        self.game.all_sprites.add(portal)
        self.game.portals.add(portal)
        
        # Set up a safe starting environment
        self.has_attacked = False
        self.has_moved = False
        self.has_been_splashed = False
        self.has_visited_lava = False
        
        game_logger.debug("tutorial_environment_setup", {
            "water_enemy_position": (water_enemy_x, water_enemy_y),
            "lava_enemy_position": (lava_enemy_x, lava_enemy_y),
            "player_position": (self.game.player.rect.x, self.game.player.rect.y)
        }, "high")
    
    def create_tutorial_enemy(self, x, y, area_type="BEACH"):
        """Create an enemy for tutorial purposes."""
        if area_type == "BEACH":
            from entities import WaterSplasher
            enemy = WaterSplasher(x, y)
            # Make the tutorial enemy move more slowly for better demonstration
            enemy.speed = 1.0
        elif area_type == "VOLCANO":
            from entities import LavaSprite
            enemy = LavaSprite(x, y)
            enemy.speed = 0.8
        else:
            from entities import AbyssalEntity  # For completeness
            enemy = AbyssalEntity(x, y)
            enemy.speed = 0.7
            
        self.game.all_sprites.add(enemy)
        self.game.enemies.add(enemy)
        return enemy
    
    def update(self, events, keys):
        """Update the tutorial state based on player actions."""
        if not self.active or self.current_step >= len(self.steps):
            return
            
        current_time = time.time()
        current_step = self.steps[self.current_step]
        step_duration = current_step["duration"]
        
        # Handle zoom transitions
        self.target_zoom = current_step["zoom_level"]
        self.current_zoom += (self.target_zoom - self.current_zoom) * 0.05  # Smooth transition
        
        # Update pulse effect for highlights
        if current_time - self.last_pulse_time > 0.05:  # Update pulse every 50ms
            self.pulse_alpha += self.pulse_direction * 5
            if self.pulse_alpha >= 100:
                self.pulse_alpha = 100
                self.pulse_direction = -1
            elif self.pulse_alpha <= 30:
                self.pulse_alpha = 30
                self.pulse_direction = 1
            self.last_pulse_time = current_time
        
        # Check if player has completed required actions
        required_action = current_step["required_action"]
        step_id = current_step["id"]
        
        if required_action == "SPACE":
            # Check for space key press
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.advance_to_next_step()
                    
                    # Record testing results for specific steps
                    if step_id == "welcome":
                        game_logger.debug("tutorial_test_passed", {
                            "test": "UI_rendering",
                            "status": "PASS"
                        }, "high")
                    elif step_id == "player_intro":
                        self.mechanics_tested["enemy_rendering"] = True
                        game_logger.debug("tutorial_test_passed", {
                            "test": "player_rendering",
                            "status": "PASS"
                        }, "high")
        
        elif required_action == "MOVE":
            # Check if player has moved
            if any(keys[k] for k in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, 
                                    pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d]):
                self.has_moved = True
                
            # If player has moved enough, advance
            if self.has_moved:
                player = self.game.player
                center_x, center_y = self.game.width // 2, self.game.height // 2
                distance_from_center = ((player.rect.x - center_x) ** 2 + (player.rect.y - center_y) ** 2) ** 0.5
                
                if distance_from_center > 50:  # Player has moved at least 50 pixels from center
                    self.mechanics_tested["movement"] = True
                    game_logger.debug("tutorial_test_passed", {
                        "test": "player_movement",
                        "status": "PASS",
                        "distance_moved": distance_from_center
                    }, "high")
                    self.advance_to_next_step()
        
        elif required_action == "ATTACK":
            # Check if player has attacked
            if not self.has_attacked:
                # Check for both space key and mouse click
                for event in events:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        # Only count as attack if near the enemy
                        dx = self.game.player.rect.x - self.water_enemy_for_tutorial.rect.x
                        dy = self.game.player.rect.y - self.water_enemy_for_tutorial.rect.y
                        distance = (dx ** 2 + dy ** 2) ** 0.5
                        
                        if distance <= 60:  # Attack range
                            self.has_attacked = True
                            self.mechanics_tested["player_attack"] = True
                            game_logger.debug("tutorial_test_passed", {
                                "test": "player_attack_mechanics",
                                "status": "PASS",
                                "attack_method": "keyboard"
                            }, "high")
                            self.advance_to_next_step()
                    
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        # Check if player clicked on enemy
                        mouse_pos = pygame.mouse.get_pos()
                        if self.water_enemy_for_tutorial.rect.collidepoint(mouse_pos):
                            # Only count if player is close enough
                            dx = self.game.player.rect.x - self.water_enemy_for_tutorial.rect.x
                            dy = self.game.player.rect.y - self.water_enemy_for_tutorial.rect.y
                            distance = (dx ** 2 + dy ** 2) ** 0.5
                            
                            if distance <= 60:  # Attack range
                                self.has_attacked = True
                                self.mechanics_tested["player_attack"] = True
                                game_logger.debug("tutorial_test_passed", {
                                    "test": "player_attack_mechanics", 
                                    "status": "PASS",
                                    "attack_method": "mouse"
                                }, "high")
                                self.advance_to_next_step()
        
        elif required_action == "GET_SPLASHED":
            # Check if player has been splashed by water enemy
            if self.game.player.wetness > 0 and not self.has_been_splashed:
                self.has_been_splashed = True
                self.mechanics_tested["wetness"] = True
                game_logger.debug("tutorial_test_passed", {
                    "test": "wetness_mechanics",
                    "status": "PASS",
                    "wetness_level": self.game.player.wetness
                }, "high")
                self.advance_to_next_step()
        
        elif required_action == "APPROACH_LAVA":
            # Check if player has approached the lava enemy
            if self.lava_enemy_for_tutorial:
                dx = self.game.player.rect.x - self.lava_enemy_for_tutorial.rect.x
                dy = self.game.player.rect.y - self.lava_enemy_for_tutorial.rect.y
                distance = (dx ** 2 + dy ** 2) ** 0.5
                
                if distance <= 80 and not self.has_visited_lava:
                    self.has_visited_lava = True
                    self.mechanics_tested["elemental_progression"] = True
                    game_logger.debug("tutorial_test_passed", {
                        "test": "lava_interaction",
                        "status": "PASS"
                    }, "high")
                    self.advance_to_next_step()
                    
                    # Simulate obsidian formation if player is wet
                    if self.game.player.wetness > 30:
                        self.game.player.obsidian_level += 10
                        self.has_formed_obsidian = True
                        self.game.add_splash_message("Obsidian armor forming!", 2.0)
        
        # Check if step duration has elapsed
        if step_duration > 0 and current_time - self.step_start_time > step_duration:
            self.advance_to_next_step()
    
    def advance_to_next_step(self):
        """Move to the next tutorial step."""
        self.current_step += 1
        self.step_start_time = time.time()
        
        # Check if we've completed all steps
        if self.current_step >= len(self.steps):
            self.complete_tutorial()
        else:
            # Log step change
            game_logger.debug("tutorial_step_changed", {
                "new_step": self.current_step,
                "message": self.steps[self.current_step]["message"]
            }, "normal")
    
    def complete_tutorial(self):
        """Mark the tutorial as completed and summarize tested mechanics."""
        self.active = False
        self.completed = True
        
        # Generate tutorial summary
        summary = ""
        all_mechanics_tested = all(self.mechanics_tested.values())
        
        if all_mechanics_tested:
            summary = "All game mechanics successfully verified!"
        else:
            # Count tested mechanics
            tested_count = sum(1 for tested in self.mechanics_tested.values() if tested)
            total_count = len(self.mechanics_tested)
            
            summary = f"{tested_count}/{total_count} game mechanics verified."
            
            # Report untested mechanics
            untested = [mech for mech, tested in self.mechanics_tested.items() if not tested]
            if untested:
                untested_str = ", ".join(untested)
                summary += f" Untested: {untested_str}"
        
        # Save tutorial completion status (could be saved to a file for persistence)
        self.game.add_splash_message("Tutorial completed! Begin your adventure!", 4.0)
        
        # Log tutorial completion with detailed results
        game_logger.debug("tutorial_completed", {
            "duration": time.time() - self.step_start_time,
            "mechanics_tested": self.mechanics_tested,
            "all_mechanics_verified": all_mechanics_tested,
            "summary": summary
        }, "high")
        
        # Log detailed test metrics for analysis
        game_logger.create_snapshot("tutorial_completion")
        
        # Move the lava enemy off-screen before enabling real enemies
        if self.lava_enemy_for_tutorial:
            self.lava_enemy_for_tutorial.rect.x = self.game.width + 200
    
    def draw(self, screen):
        """Draw tutorial elements to the screen."""
        if not self.active or self.current_step >= len(self.steps):
            return
            
        current_step = self.steps[self.current_step]
        
        # Get dimensions
        screen_width, screen_height = screen.get_size()
        
        # Draw semi-transparent overlay if this is an important step
        if current_step["required_action"] in ["SPACE", "MOVE", "ATTACK", "GET_SPLASHED", "APPROACH_LAVA"]:
            overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 80))  # Semi-transparent black
            screen.blit(overlay, (0, 0))
        
        # Draw highlight around target element
        highlight_target = current_step["highlight"]
        if highlight_target:
            target_rect = None
            
            if highlight_target == "PLAYER":
                target_rect = self.game.player.rect
            elif highlight_target == "WATER_ENEMY" and self.water_enemy_for_tutorial:
                target_rect = self.water_enemy_for_tutorial.rect
            elif highlight_target == "LAVA_ENEMY" and self.lava_enemy_for_tutorial:
                target_rect = self.lava_enemy_for_tutorial.rect
            elif highlight_target == "PORTAL" and len(self.game.portals) > 0:
                target_rect = list(self.game.portals)[0].rect
            
            if target_rect:
                # Draw pulsing highlight with expanded rect
                expanded_rect = target_rect.inflate(20, 20)
                highlight_surface = pygame.Surface((expanded_rect.width, expanded_rect.height), pygame.SRCALPHA)
                highlight_color = (255, 255, 0, self.pulse_alpha)  # Yellow with variable transparency
                pygame.draw.rect(highlight_surface, highlight_color, (0, 0, expanded_rect.width, expanded_rect.height), 3, border_radius=8)
                screen.blit(highlight_surface, expanded_rect.topleft)
        
        # Draw message box at the bottom of the screen
        message = current_step["message"]
        
        # Create message box
        box_width = screen_width * 0.8
        box_height = 100
        box_x = (screen_width - box_width) / 2
        box_y = screen_height - box_height - 20  # 20px from bottom
        
        # Draw semi-transparent box
        message_box = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        message_box.fill((0, 0, 0, 180))  # Semi-transparent black
        pygame.draw.rect(message_box, (255, 255, 255), (0, 0, box_width, box_height), 2, border_radius=10)  # White border
        screen.blit(message_box, (box_x, box_y))
        
        # Split message into lines and render
        lines = message.split('\n')
        line_height = 24
        for i, line in enumerate(lines):
            text_surface = self.font_small.render(line, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(box_x + box_width / 2, box_y + 30 + i * line_height))
            screen.blit(text_surface, text_rect)
        
        # Draw step indicator (e.g., "Step 3/11")
        step_text = f"Step {self.current_step + 1}/{len(self.steps)}"
        step_surface = self.font_small.render(step_text, True, (200, 200, 200))
        screen.blit(step_surface, (box_x + 10, box_y + 10))
        
        # Draw control hint if needed
        if current_step["required_action"] == "SPACE":
            hint = "Press SPACE to continue"
        elif current_step["required_action"] == "MOVE":
            hint = "Use WASD or arrow keys to move"
        elif current_step["required_action"] == "ATTACK":
            hint = "Press SPACE or click to attack"
        elif current_step["required_action"] == "GET_SPLASHED":
            hint = "Let the water enemy splash you"
        elif current_step["required_action"] == "APPROACH_LAVA":
            hint = "Approach the lava enemy"
        else:
            hint = ""
            
        if hint:
            hint_surface = self.font_small.render(hint, True, (255, 255, 0))
            hint_rect = hint_surface.get_rect(bottomright=(box_x + box_width - 10, box_y + box_height - 10))
            screen.blit(hint_surface, hint_rect)
        
        # Draw test goal indicator if debug mode is on
        if self.game.debug_mode:
            test_goal = current_step.get("test_goal", "")
            if test_goal:
                goal_text = f"Testing: {test_goal}"
                goal_surface = self.font_small.render(goal_text, True, (100, 255, 100))
                screen.blit(goal_surface, (20, 20))
    
    def apply_camera_effects(self, screen):
        """Apply zoom effects if needed."""
        if not self.active or abs(self.current_zoom - 1.0) < 0.01:
            return screen
        
        # For simplicity, we're simulating zoom by scaling the final rendered frame
        # A more sophisticated approach would adjust the camera position before rendering
        
        # Create a copy of the screen
        screen_copy = screen.copy()
        
        # Calculate new dimensions
        new_width = int(self.game.width * self.current_zoom)
        new_height = int(self.game.height * self.current_zoom)
        
        # Scale the surface
        scaled_screen = pygame.transform.scale(screen_copy, (new_width, new_height))
        
        # Calculate offset to keep center focused
        offset_x = (self.game.width - new_width) // 2
        offset_y = (self.game.height - new_height) // 2
        
        # Create a new surface for the final output
        final_screen = pygame.Surface((self.game.width, self.game.height))
        final_screen.fill((0, 0, 0))  # Fill with black background
        
        # Blit the scaled surface onto the final surface
        final_screen.blit(scaled_screen, (offset_x, offset_y))
        
        return final_screen
