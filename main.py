import pygame
import sys
import random
import time
import os
from logger import game_logger
from entities import Player, Enemy, AreaPortal
from tutorial import Tutorial

# Check for development tutorial mode
try:
    # Import the development tutorial if in dev mode
    if os.environ.get("ELEMENTAL_GAME_MODE") == "dev":
        from devtools.dev_tutorial import create_tutorial
        TUTORIAL_MODE = "dev"
        print("Starting in DEVELOPMENT TUTORIAL mode")
    else:
        TUTORIAL_MODE = "standard"
        print("Starting in STANDARD mode")
except ImportError:
    # Fall back to standard tutorial if import fails
    TUTORIAL_MODE = "standard"
    print("Development tools not found, using standard tutorial")

class Game:
    def __init__(self):
        # Initialize pygame
        pygame.init()
        
        # Set up the display
        self.width, self.height = 800, 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Elemental Progression Game")
        
        # Set up clock
        self.clock = pygame.time.Clock()
        self.fps = 60
        
        # Game state
        self.running = True
        self.current_area = "BEACH"
        self.areas = ["BEACH", "VOLCANO", "ABYSS"]
        self.area_colors = {
            "BEACH": (135, 206, 235),  # Sky blue
            "VOLCANO": (153, 76, 0),   # Brown
            "ABYSS": (0, 0, 0)         # Black
        }
        
        # Game over state
        self.game_over = False
        self.game_over_time = 0
        self.game_over_display_duration = 5  # Show game over screen for 5 seconds
        
        # Notification system
        self.notification_message = None
        self.notification_time = 0
        self.notification_duration = 3  # Default duration in seconds
        
        # Debug mode - useful for tutorial development and testing
        self.debug_mode = False  # Set to True to show test goals and mechanics validation
        
        # Sprites and groups
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.portals = pygame.sprite.Group()
        
        # Create player
        self.player = Player(self.width // 2, self.height // 2)
        self.all_sprites.add(self.player)
        
        # Tutorial system - Initialize before spawning enemies
        if TUTORIAL_MODE == "dev":
            self.tutorial = create_tutorial(self)
        else:
            self.tutorial = Tutorial(self)
        self.show_tutorial = True  # Set to False to skip tutorial
        self.tutorial_started = False
        self.tutorial_completed = False
        
        # Initial setup (moved after tutorial initialization)
        # Only setup portals initially, not enemies
        if self.show_tutorial:
            self.setup_area_safe()  # New method that doesn't spawn enemies yet
        else:
            self.setup_area(self.current_area)  # Full setup with enemies if tutorial is skipped
        
        # Splash text
        self.splash_font = pygame.font.SysFont(None, 36)
        self.splash_messages = []
        
        # Game time tracking for debug
        self.start_time = time.time()
        self.last_log_time = self.start_time
        
        # Analysis display flags and data
        self.showing_analysis = False
        self.analysis_results = None
        self.analysis_scroll_position = 0
        self.analysis_scroll_speed = 20
        
        game_logger.debug("game_initialized", {
            "screen_size": (self.width, self.height),
            "starting_area": self.current_area,
            "fps": self.fps,
            "tutorial_enabled": self.show_tutorial
        }, "high")
    
    def setup_area(self, area):
        """Set up a new area with appropriate enemies and portals"""
        # Clear existing enemies and portals
        for sprite in self.enemies:
            sprite.kill()
        for sprite in self.portals:
            sprite.kill()
            
        # Create new enemies based on area
        if area == "BEACH":
            self.spawn_enemies(15, "BEACH")
            # Add portal to next area
            portal = AreaPortal(self.width - 100, self.height // 2, "BEACH", "VOLCANO")
            self.all_sprites.add(portal)
            self.portals.add(portal)
            
        elif area == "VOLCANO":
            self.spawn_enemies(8, "VOLCANO")
            # Add portal to next area
            portal = AreaPortal(self.width - 100, self.height // 2, "VOLCANO", "ABYSS")
            self.all_sprites.add(portal)
            self.portals.add(portal)
            
        elif area == "ABYSS":
            self.spawn_enemies(12, "ABYSS")
            
        # Update player's current area
        old_area = self.player.current_area
        self.player.current_area = area
        
        game_logger.log_area_transition(self.player, old_area, area)
        
        # Add splash message for area
        self.add_splash_message(f"Entered {area}")
    
    def setup_area_safe(self):
        """Set up a new area without spawning enemies"""
        # Clear existing enemies and portals
        for sprite in self.enemies:
            sprite.kill()
        for sprite in self.portals:
            sprite.kill()
            
        # Add portal to next area
        portal = AreaPortal(self.width - 100, self.height // 2, "BEACH", "VOLCANO")
        self.all_sprites.add(portal)
        self.portals.add(portal)
        
        # Update player's current area
        old_area = self.player.current_area
        self.player.current_area = "BEACH"
        
        game_logger.log_area_transition(self.player, old_area, "BEACH")
        
        # Add splash message for area
        self.add_splash_message(f"Entered {self.current_area}")
    
    def spawn_enemies(self, count, area):
        """Spawn a given number of enemies for the specified area"""
        for _ in range(count):
            x = random.randint(50, self.width - 100)
            y = random.randint(50, self.height - 100)
            enemy = Enemy(x, y, area)
            self.all_sprites.add(enemy)
            self.enemies.add(enemy)
            
        game_logger.debug("enemies_spawned", {
            "count": count,
            "area": area,
            "types": [e.type for e in self.enemies]
        }, "normal")
    
    def add_splash_message(self, text, duration=3.0):
        """Add a splash message to the screen"""
        if not hasattr(self, 'splash_messages'):
            self.splash_messages = []
        self.splash_messages.append({
            "text": text,
            "duration": duration,
            "start_time": time.time()
        })
        
        game_logger.debug("splash_message", {
            "message": text,
            "duration": duration
        }, "low")
    
    def handle_events(self):
        """Handle pygame events"""
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            
            # Handle ESC key for exit, especially during game over
            if event.type == pygame.KEYDOWN:
                # General keyboard input logging for all keys
                key_name = pygame.key.name(event.key)
                game_logger.debug("KEY_INPUT", {
                    "key": key_name,
                    "key_code": event.key,
                    "game_state": "game_over" if self.game_over else "playing",
                    "timestamp": time.time()
                }, "normal")
                
                if event.key == pygame.K_ESCAPE:
                    # If showing analysis, close it
                    if self.showing_analysis:
                        self.showing_analysis = False
                    # If we're in game over state, quit immediately
                    elif self.game_over:
                        self.running = False
                    # Otherwise it could be used for menu/pause in the future
                elif event.key == pygame.K_SPACE and not self.tutorial.active and not self.showing_analysis:
                    # Attack nearby enemies (only if not in tutorial)
                    self.player_attack()
                
                # Handle scrolling in analysis view
                elif self.showing_analysis:
                    if event.key == pygame.K_UP:
                        self.analysis_scroll_position = max(0, self.analysis_scroll_position - self.analysis_scroll_speed)
                    elif event.key == pygame.K_DOWN:
                        self.analysis_scroll_position += self.analysis_scroll_speed
                    
                # Handle analysis options during game over screen
                elif self.game_over:
                    if event.key == pygame.K_e:  # E for Eat Logs
                        # Log the key press event with priority "critical" to ensure it appears
                        game_logger.debug("INPUT_KEY_PRESSED", {
                            "key": "E",
                            "action": "eat_logs",
                            "screen": "game_over",
                            "timestamp": time.time()
                        }, "critical")
                        
                        game_logger.debug("GAME_OVER_EAT_LOGS_SELECTED", {
                            "action": "eat_logs",
                            "player_state": self.player.__dict__,
                            "session_data": game_logger.get_current_session_id()
                        }, "critical")  # Changed priority to critical
                        
                        # Add a more visible notification
                        self.show_notification("ANALYZING LOGS - PROCESSING DATA...", 5)
                        
                        # Run the unified analysis in a way that displays results in game
                        self.analyze_logs_in_game()
            
            # Handle mouse clicks
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    if self.showing_analysis:
                        # Check if clicked on the close button
                        close_button_rect = pygame.Rect(self.width//2 - 60, self.height - 60, 120, 40)
                        if close_button_rect.collidepoint(event.pos):
                            self.showing_analysis = False
                    elif not self.tutorial.active:
                        # Attack with mouse
                        self.handle_mouse_attack(event.pos)
                
                # Mouse wheel for scrolling in analysis view
                elif event.button == 4 and self.showing_analysis:  # Scroll up
                    self.analysis_scroll_position = max(0, self.analysis_scroll_position - self.analysis_scroll_speed)
                elif event.button == 5 and self.showing_analysis:  # Scroll down
                    self.analysis_scroll_position += self.analysis_scroll_speed
        
        # Pass events to tutorial if active
        if self.tutorial.active and not self.showing_analysis:
            # Apply any camera effects from tutorial (zoom, etc)
            screen_with_effects = self.tutorial.apply_camera_effects(self.screen.copy())
            self.screen.blit(screen_with_effects, (0, 0))
            
            # Draw tutorial UI elements on top
            self.tutorial.draw(self.screen)
            
            # Make sure to update the tutorial with the events
            self.tutorial.update(events, pygame.key.get_pressed())
        
        return events
    
    def handle_mouse_attack(self, mouse_pos):
        """Handle mouse click attacks on enemies"""
        # Find enemies that were clicked on
        for enemy in self.enemies:
            if enemy.rect.collidepoint(mouse_pos):
                # Calculate distance to enemy
                dx = enemy.rect.x - self.player.rect.x
                dy = enemy.rect.y - self.player.rect.y
                distance = (dx ** 2 + dy ** 2) ** 0.5
                
                # Only attack if player is close enough
                if distance <= 60:  # Attack range
                    result = self.player.attack(enemy)
                    
                    # Add splash message for special effects
                    if "attack_ineffective_no_obsidian" in result.get("effects", []):
                        self.add_splash_message("Need obsidian armor for Abyss enemies!")
                    elif "formed_obsidian" in result.get("effects", []):
                        self.add_splash_message("Obsidian armor forming!")
    
    def player_attack(self):
        """Handle player attacking nearby enemies"""
        attack_range = 60  # Attack radius
        attack_count = 0
        
        for enemy in self.enemies:
            # Calculate distance to enemy
            dx = enemy.rect.x - self.player.rect.x
            dy = enemy.rect.y - self.player.rect.y
            distance = (dx ** 2 + dy ** 2) ** 0.5
            
            if distance <= attack_range:
                result = self.player.attack(enemy)
                attack_count += 1
                
                # Add splash message for special effects
                if "attack_ineffective_no_obsidian" in result.get("effects", []):
                    self.add_splash_message("Need obsidian armor to damage abyss enemies!", 2.0)
                
                if "enemy_defeated" in result.get("effects", []):
                    # Chance to spawn new enemy
                    if random.random() < 0.3:
                        self.spawn_enemies(1, self.current_area)
        
        if attack_count == 0:
            self.add_splash_message("No enemies in range", 1.0)
        else:
            game_logger.debug("player_attack", {
                "enemies_hit": attack_count,
                "area": self.current_area
            }, "normal")
    
    def update(self):
        """Update game state"""
        # Check if player is dead
        if self.player.health <= 0 and not self.game_over:
            # Determine cause of death based on player state
            cause_of_death = "Unknown"
            
            # Check if player had high wetness but no obsidian armor in volcano area
            if self.current_area == "VOLCANO" and self.player.wetness < 50:
                cause_of_death = "Insufficient Wetness in Volcano Area"
            # Check if player was in abyss without obsidian armor
            elif self.current_area == "ABYSS" and not self.player.has_obsidian_armor:
                cause_of_death = "Entered Abyss Without Obsidian Armor"
            # Default case - water damage in beach area
            elif self.current_area == "BEACH":
                cause_of_death = "Defeated by Water Creatures"
            else:
                cause_of_death = "Elemental Damage"

            # Log the initiation of the game over sequence with detailed cause
            game_logger.debug("GAME_OVER_SEQUENCE_INITIATING", {
                "player_health": self.player.health,
                "cause_of_death": cause_of_death,
                "current_area": self.current_area,
                "wetness": self.player.wetness,
                "fire_resistance": self.player.fire_resistance,
                "obsidian_armor": self.player.obsidian_armor_level,
                "has_obsidian_armor": self.player.has_obsidian_armor,
                "timestamp": time.time()
            }, "critical")
            
            self.game_over = True
            self.game_over_time = time.time()
            
            # Create a copy of the progression dictionary to avoid modifying the original
            progression_copy = {}
            for key, value in self.player.progression.items():
                # Convert sets to lists for JSON serialization
                if isinstance(value, set):
                    progression_copy[key] = list(value)
                elif isinstance(value, dict):
                    # Handle nested dictionaries that might contain sets
                    progression_copy[key] = {}
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, set):
                            progression_copy[key][sub_key] = list(sub_value)
                        else:
                            progression_copy[key][sub_key] = sub_value
                else:
                    progression_copy[key] = value
                    
            game_logger.debug("GAME_OVER", {
                "final_health": self.player.health,
                "death_area": self.current_area,
                "wetness": self.player.wetness,
                "obsidian_armor": self.player.obsidian_armor_level,
                "time_survived": time.time() - self.start_time,
                "progression": progression_copy,
                "cause_of_death": cause_of_death
            }, "critical")
            
            # Log game over sequence completion
            game_logger.debug("GAME_OVER_SEQUENCE_INITIATED", {
                "display_duration": self.game_over_display_duration,
                "cause_of_death": cause_of_death,
                "auto_exit_at": time.time() + self.game_over_display_duration
            }, "critical")
            
            return  # Stop updating game if player is dead
            
        # Process input
        keys = pygame.key.get_pressed()
        
        # Only update player if not in tutorial or tutorial is inactive
        if not self.tutorial.active:
            self.player.update(keys)
            
            # Check collisions with portals
            self.check_portal_collisions()
        
        # Update enemies (they will move towards player)
        for enemy in self.enemies:
            enemy.update(self.player)
            
            # Check collision with player (enemy attacking player)
            if not self.tutorial.active and pygame.sprite.collide_rect(enemy, self.player):
                enemy.attack(self.player)
        
        # Remove splash messages that have expired
        current_time = time.time()
        self.splash_messages = [msg for msg in self.splash_messages 
                              if current_time - msg["start_time"] < msg["duration"]]
        
        # Start tutorial if enabled and not started yet
        if self.show_tutorial and not self.tutorial_started:
            self.tutorial.start()
            self.tutorial_started = True
        
        # If tutorial just completed and enemies haven't been spawned yet, spawn them now
        if self.show_tutorial and self.tutorial.completed and not self.tutorial_completed:
            self.tutorial_completed = True
            self.setup_area(self.current_area)  # Now spawn real enemies
            self.add_splash_message("Get ready! Your journey begins!", 3.0)
            
        # Periodically log game state
        if current_time - self.last_log_time >= 1.0:
            game_logger.log_environment_state(
                self.current_area,
                list(self.enemies),
                []  # No environmental hazards implemented yet
            )
            
            # Create a snapshot of game state every second
            game_logger.create_snapshot()
            
            self.last_log_time = current_time
    
    def check_portal_collisions(self):
        """Check if player has collided with any portals and handle area transitions"""
        for portal in self.portals:
            if pygame.sprite.collide_rect(self.player, portal):
                if self.player.current_area != portal.target_area:
                    # Log area transition initiation
                    game_logger.debug("area_transition_initiate", {
                        "from_area": self.current_area,
                        "to_area": portal.target_area,
                        "player_health": self.player.health,
                        "player_wetness": self.player.wetness,
                        "player_obsidian": self.player.obsidian_armor_level,
                        "timestamp": time.time()
                    }, "high")
                    
                    self.current_area = portal.target_area
                    self.setup_area(self.current_area)
                    
                    # Reset player position
                    game_logger.debug("resetting player position")
                    self.player.rect.x = 100
                    game_logger.debug("reset player position to" + str(self.player.rect.x))
                    self.player.rect.y = self.height // 2
                    game_logger.debug("reset player position to" + str(self.player.rect.y))
                    
                    # Add splash message for transition
                    game_logger.debug("adding splash message")
                    self.add_splash_message(f"Entered {portal.target_area}", 3.0)
                    game_logger.debug("added splash message at" +portal.target_area)
    
    def draw(self, screen=None):
        """Draw everything to the screen"""
        # Set screen to self.screen if not provided
        if screen is None:
            screen = self.screen
        
        # Fill the background with area color
        screen.fill(self.area_colors.get(self.current_area, (0, 0, 0)))
        
        # Draw all sprites
        self.all_sprites.draw(screen)
        
        # Draw splash messages
        current_time = time.time()
        y_offset = 50
        for message in self.splash_messages:
            # Calculate opacity based on time remaining
            elapsed = current_time - message["start_time"]
            opacity = max(0, min(255, 255 * (1 - elapsed / message["duration"])))
            
            text = self.splash_font.render(message["text"], True, (255, 255, 255))
            text.set_alpha(int(opacity))
            
            text_rect = text.get_rect(center=(self.width // 2, y_offset))
            screen.blit(text, text_rect)
            y_offset += 40
        
        # Draw tutorial elements if active
        if self.tutorial.active:
            # Apply any camera effects from tutorial (zoom, etc)
            screen_with_effects = self.tutorial.apply_camera_effects(screen.copy())
            screen.blit(screen_with_effects, (0, 0))
            
            # Draw tutorial UI elements on top
            self.tutorial.draw(screen)
        
        # Draw HUD
        self.draw_hud(screen)
        
        # Draw notification if active
        self.draw_notification(screen)
        
        # Draw debug info if debug mode is enabled
        if self.debug_mode:
            self.draw_debug_info(screen)
            
    def draw_notification(self, screen=None):
        """Draw any active notification on the screen"""
        # Set screen to self.screen if not provided
        if screen is None:
            screen = self.screen
        
        if self.notification_message and time.time() - self.notification_time < self.notification_duration:
            # Create a semi-transparent background
            notification_bg = pygame.Surface((self.width, 40), pygame.SRCALPHA)
            notification_bg.fill((0, 0, 0, 180))  # Black with 70% opacity
            screen.blit(notification_bg, (0, self.height - 40))
            
            # Draw the message
            font = pygame.font.Font(None, 28)
            text = font.render(self.notification_message, True, (200, 255, 200))
            screen.blit(text, (self.width // 2 - text.get_width() // 2, self.height - 30))
            
            # Calculate and show remaining time
            remaining = max(0, self.notification_duration - (time.time() - self.notification_time))
            # Only log once every second to avoid spam
            if int(remaining) != int(remaining + 0.2):
                game_logger.debug("NOTIFICATION_DISPLAY", {
                    "message": self.notification_message,
                    "remaining_time": round(remaining, 1)
                }, "low")
    
    def draw_hud(self, screen=None):
        """Draw HUD elements like health bar, status effects, etc."""
        # Set screen to self.screen if not provided
        if screen is None:
            screen = self.screen
            
        # Draw health bar
        pygame.draw.rect(screen, (255, 0, 0), (20, 20, 150, 20))  # Red background
        if self.player.health > 0:
            health_width = max(0, min(150, 150 * (self.player.health / self.player.max_health)))
            pygame.draw.rect(screen, (0, 255, 0), (20, 20, health_width, 20))  # Green health
        
        # Draw health text
        health_text = f"Health: {max(0, int(self.player.health))}/{self.player.max_health}"
        health_surface = self.splash_font.render(health_text, True, (255, 255, 255))
        screen.blit(health_surface, (180, 20))
        
        # Draw wetness meter if player has any wetness
        if self.player.wetness > 0:
            # Background
            pygame.draw.rect(screen, (100, 100, 255), (20, 50, 150, 15))
            # Filled amount
            wetness_width = 150 * (self.player.wetness / 100)
            pygame.draw.rect(screen, (0, 0, 255), (20, 50, wetness_width, 15))
            # Text
            wetness_text = f"Wetness: {int(self.player.wetness)}%"
            wetness_surface = self.splash_font.render(wetness_text, True, (255, 255, 255))
            screen.blit(wetness_surface, (180, 45))
            
        # Draw fire resistance if player has any
        if self.player.fire_resistance > 0:
            resist_text = f"Fire Resist: {int(self.player.fire_resistance)}%"
            resist_surface = self.splash_font.render(resist_text, True, (255, 200, 0))
            screen.blit(resist_surface, (20, 75))
            
        # Draw obsidian armor if player has any
        if self.player.obsidian_armor_level > 0:
            armor_text = f"Obsidian: {int(self.player.obsidian_armor_level)}%"
            armor_color = (100, 100, 100) if not self.player.has_obsidian_armor else (200, 200, 200)
            armor_surface = self.splash_font.render(armor_text, True, armor_color)
            screen.blit(armor_surface, (20, 100))
            
        # Draw current area
        area_text = f"Area: {self.current_area}"
        area_surface = self.splash_font.render(area_text, True, (255, 255, 255))
        screen.blit(area_surface, (self.width - area_surface.get_width() - 20, 20))
    
    def draw_debug_info(self, screen=None):
        """Draw debug information on screen when debug mode is enabled"""
        # Set screen to self.screen if not provided
        if screen is None:
            screen = self.screen
        
        debug_font = pygame.font.SysFont(None, 20)
        y_offset = 10
        x_offset = 10
        
        # Player stats
        debug_texts = [
            f"FPS: {int(self.clock.get_fps())}",
            f"Player Health: {self.player.health}",
            f"Player Position: ({self.player.rect.x}, {self.player.rect.y})",
            f"Wetness: {self.player.wetness}",
            f"Fire Resistance: {self.player.fire_resistance}%",
            f"Area: {self.current_area}",
            f"Obsidian Armor: {'Yes' if self.player.has_obsidian_armor else 'No'} (Level: {self.player.obsidian_armor_level})"
        ]
        
        # Enemy counts by type
        water_enemies = len([e for e in self.enemies if hasattr(e, 'type') and e.type == 'WATER'])
        lava_enemies = len([e for e in self.enemies if hasattr(e, 'type') and e.type == 'LAVA'])
        abyss_enemies = len([e for e in self.enemies if hasattr(e, 'type') and e.type == 'ABYSS'])
        
        debug_texts.extend([
            f"Water Enemies: {water_enemies}",
            f"Lava Enemies: {lava_enemies}",
            f"Abyss Enemies: {abyss_enemies}",
            f"Game Over: {self.game_over}"
        ])
        
        # Create a semi-transparent background for debug text
        debug_bg = pygame.Surface((250, 14 * len(debug_texts) + 10), pygame.SRCALPHA)
        debug_bg.fill((0, 0, 0, 128))  # Black with 50% opacity
        screen.blit(debug_bg, (x_offset - 5, y_offset - 5))
        
        # Render debug texts
        for text in debug_texts:
            debug_surface = debug_font.render(text, True, (255, 255, 255))
            screen.blit(debug_surface, (x_offset, y_offset))
            y_offset += 14  # Line spacing
        
        # Log that we rendered debug info
        game_logger.debug("DEBUG_INFO_DISPLAYED", {
            "debug_mode": self.debug_mode,
            "player_stats": {
                "health": self.player.health,
                "wetness": self.player.wetness,
                "fire_resistance": self.player.fire_resistance,
                "obsidian_armor": self.player.has_obsidian_armor
            }
        }, "low")
    
    def draw_game_over(self, screen=None):
        """Draw game over screen with detailed information"""
        # Set screen to self.screen if not provided
        if screen is None:
            screen = self.screen
        
        # Determine cause of death based on player state
        cause_of_death = "Unknown"
        
        # Check if player had high wetness but no obsidian armor in volcano area
        if self.current_area == "VOLCANO" and self.player.wetness < 50:
            cause_of_death = "Insufficient Wetness in Volcano Area"
            cause_color = (255, 100, 50)  # Orange-red for volcano death
        # Check if player was in abyss without obsidian armor
        elif self.current_area == "ABYSS" and not self.player.has_obsidian_armor:
            cause_of_death = "Entered Abyss Without Obsidian Armor"
            cause_color = (128, 0, 128)  # Purple for abyss death
        # Default case - water damage in beach area
        elif self.current_area == "BEACH":
            cause_of_death = "Defeated by Water Creatures"
            cause_color = (64, 64, 255)  # Blue for water death
        else:
            cause_of_death = "Elemental Damage"
            cause_color = (255, 0, 0)  # Red for general death

        game_logger.debug("DRAWING_GAME_OVER_SCREEN", {
            "cause_of_death": cause_of_death,
            "current_area": self.current_area,
            "time_elapsed": time.time() - self.game_over_time,
            "remaining_time": max(0, (self.game_over_time + self.game_over_display_duration) - time.time())
        }, "info")
        
        # Semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Black with 70% opacity
        screen.blit(overlay, (0, 0))
        
        # Game over text
        title_font = pygame.font.Font(None, 72)
        info_font = pygame.font.Font(None, 36)
        stats_font = pygame.font.Font(None, 28)
        
        # Main title
        game_over_text = title_font.render("GAME OVER", True, (255, 0, 0))
        screen.blit(game_over_text, (self.width // 2 - game_over_text.get_width() // 2, 100))
        
        # Cause of death with dynamic color
        death_text = info_font.render(f"Cause of Death: {cause_of_death}", True, cause_color)
        screen.blit(death_text, (self.width // 2 - death_text.get_width() // 2, 180))
        
        # Game stats
        y_offset = 250
        stats = [
            f"Area: {self.current_area}",
            f"Wetness Level: {self.player.wetness}",
            f"Fire Resistance: {self.player.fire_resistance}%",
            f"Obsidian Armor: {'Yes' if self.player.has_obsidian_armor else 'No'} (Level: {self.player.obsidian_armor_level})",
            f"Areas Visited: {', '.join(list(self.player.progression.get('areas_visited', [])))[:30]}..." if len(', '.join(list(self.player.progression.get('areas_visited', [])))) > 30 else ', '.join(list(self.player.progression.get('areas_visited', [])))
        ]
        
        for stat in stats:
            stat_text = stats_font.render(stat, True, (200, 200, 200))
            screen.blit(stat_text, (self.width // 2 - stat_text.get_width() // 2, y_offset))
            y_offset += 30
        
        # Add EAT LOGS button
        y_offset += 30
        eat_logs_text = info_font.render("Press E - EAT LOGS", True, (150, 250, 150))
        eat_logs_bg = pygame.Surface((eat_logs_text.get_width() + 20, eat_logs_text.get_height() + 10), pygame.SRCALPHA)
        eat_logs_bg.fill((0, 100, 0, 128))  # Dark green with transparency
        
        # Position the button
        button_x = self.width // 2 - eat_logs_bg.get_width() // 2
        button_y = y_offset
        
        # Draw button background and text
        screen.blit(eat_logs_bg, (button_x, button_y))
        screen.blit(eat_logs_text, (self.width // 2 - eat_logs_text.get_width() // 2, button_y + 5))
        
        # Add description
        y_offset += 60
        description_text = stats_font.render("Analyze all gameplay data for patterns and insights", True, (180, 180, 180))
        screen.blit(description_text, (self.width // 2 - description_text.get_width() // 2, y_offset))
        
        # Exit instructions
        exit_text = info_font.render("Press ESC to exit, or wait for auto-exit", True, (150, 150, 150))
        screen.blit(exit_text, (self.width // 2 - exit_text.get_width() // 2, self.height - 100))
        
        # Add a countdown timer
        remaining_time = max(0, int(self.game_over_display_duration - (time.time() - self.game_over_time)))
        timer_text = stats_font.render(f"Auto-exit in: {remaining_time} seconds", True, (150, 150, 150))
        screen.blit(timer_text, (self.width // 2 - timer_text.get_width() // 2, self.height - 60))
        
        game_logger.debug("GAME_OVER_SCREEN_RENDERED", {
            "cause_of_death": cause_of_death,
            "remaining_time": remaining_time,
            "stats_displayed": stats
        }, "info")
    
    def draw_analysis_results(self, screen=None):
        """Draw the analysis results overlay"""
        # Set screen to self.screen if not provided
        if screen is None:
            screen = self.screen
        
        # Create a semi-transparent overlay for the background
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 30, 230))  # Dark blue with high opacity
        screen.blit(overlay, (0, 0))
        
        # Title and instructions
        title_font = pygame.font.Font(None, 48)
        info_font = pygame.font.Font(None, 28)
        content_font = pygame.font.Font(None, 24)
        
        # Title
        title_text = title_font.render("LOG ANALYSIS RESULTS", True, (150, 220, 255))
        screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, 20))
        
        # Instructions
        instructions = [
            "↑/↓: Scroll",
            "ESC: Return to Game"
        ]
        instruction_x = self.width - 200
        instruction_y = 25
        
        for instruction in instructions:
            instruction_text = info_font.render(instruction, True, (180, 180, 255))
            screen.blit(instruction_text, (instruction_x, instruction_y))
            instruction_y += 30
        
        # Draw a bordered container for the results
        container_rect = pygame.Rect(50, 80, self.width - 100, self.height - 160)
        pygame.draw.rect(screen, (30, 30, 80), container_rect)
        pygame.draw.rect(screen, (80, 80, 180), container_rect, 2)  # Border
        
        # Render the content with scroll position
        if self.analysis_results:
            # Prepare the content
            result_sections = self.analysis_results.split('\n\n')
            y_offset = 90 - self.analysis_scroll_position
            
            # Draw each section
            for section in result_sections:
                section_lines = section.split('\n')
                
                # Draw the section header if present (first line)
                if section_lines and section_lines[0].strip():
                    header_line = section_lines[0].strip()
                    if len(header_line) > 3 and header_line[0] == '[' and header_line[-1] == ']':
                        # This is a section header
                        header_text = info_font.render(header_line, True, (255, 255, 150))
                        if 80 <= y_offset <= self.height - 100:
                            screen.blit(header_text, (60, y_offset))
                        y_offset += 30
                        section_lines = section_lines[1:]  # Skip the header for the content rendering
                
                # Draw the content
                for line in section_lines:
                    line_text = content_font.render(line, True, (200, 200, 220))
                    # Only draw lines that are visible in the container
                    if 80 <= y_offset <= self.height - 100:
                        screen.blit(line_text, (60, y_offset))
                    y_offset += 25
                
                # Add space between sections
                y_offset += 15
            
            # Draw scroll indicators if needed
            if self.analysis_scroll_position > 0:
                # Draw up arrow
                pygame.draw.polygon(screen, (255, 255, 255), 
                    [(self.width//2 - 10, 75), (self.width//2 + 10, 75), (self.width//2, 65)])
                
            if y_offset > self.height - 80:
                # Draw down arrow
                pygame.draw.polygon(screen, (255, 255, 255), 
                    [(self.width//2 - 10, self.height - 85), (self.width//2 + 10, self.height - 85), (self.width//2, self.height - 75)])
        else:
            # No results yet, show loading message
            loading_text = info_font.render("Processing logs, please wait...", True, (200, 200, 220))
            screen.blit(loading_text, (self.width//2 - loading_text.get_width()//2, self.height//2))
        
        # Draw a "Close" button at the bottom
        close_button_rect = pygame.Rect(self.width//2 - 60, self.height - 60, 120, 40)
        pygame.draw.rect(screen, (60, 60, 120), close_button_rect)
        pygame.draw.rect(screen, (100, 100, 200), close_button_rect, 2)  # Border
        
        close_text = info_font.render("Close", True, (220, 220, 255))
        screen.blit(close_text, (self.width//2 - close_text.get_width()//2, self.height - 55))
    
    def analyze_logs_in_game(self):
        """Run log analysis and display results directly in the game UI"""
        # First show a "processing" notification
        self.show_notification("Crunching logs... analyzing patterns...", 3)
        
        # Log the start of analysis with detailed information
        game_logger.debug("LOG_ANALYSIS_STARTED_IN_GAME", {
            "session_id": game_logger.get_current_session_id(),
            "player_state": {
                "health": self.player.health,
                "wetness": self.player.wetness,
                "obsidian_armor": self.player.obsidian_armor_level,
                "position": {"x": self.player.rect.x, "y": self.player.rect.y}
            },
            "timestamp": time.time(),
            "triggered_by": "e_key_press"
        }, "critical")
        
        # Use subprocess to run the analysis in the background
        import subprocess
        import threading
        from analyze_logs import generate_compressed_log_report
        
        current_session = game_logger.get_current_session_id()
        
        def process_logs():
            try:
                # Generate the report
                results = generate_compressed_log_report(current_session)
                
                if results:
                    # We have results! Show them in-game
                    self.display_analysis_results(results)
                else:
                    self.show_notification("No patterns found in logs", 5)
            except Exception as e:
                self.show_notification(f"Error analyzing logs: {str(e)}", 5)
                game_logger.debug("LOG_ANALYSIS_ERROR", {
                    "error": str(e)
                }, "error")
        
        # Run in a separate thread to avoid blocking the game
        analysis_thread = threading.Thread(target=process_logs)
        analysis_thread.daemon = True
        analysis_thread.start()
    
    def display_analysis_results(self, results):
        """Display the analysis results in a game overlay"""
        # We'll implement a modal dialog that shows the results
        # and pauses the game until the user dismisses it
        
        # Flag to show we're in analysis mode
        self.showing_analysis = True
        self.analysis_results = results
        self.analysis_scroll_position = 0
        self.analysis_start_time = time.time()
        
        game_logger.debug("DISPLAYING_ANALYSIS_RESULTS", {
            "results_size": len(str(results)),
            "time": time.time()
        })
    
    def run_analysis_command(self, command_option):
        """Run a log analysis command with the specified option"""
        import subprocess
        import threading
        
        current_session = game_logger.get_current_session_id()
        
        def run_command():
            try:
                # Create a visible command prompt window showing the analysis
                cmd = f'start cmd /k python analyze_logs.py {command_option} --session {current_session}'
                subprocess.call(cmd, shell=True)
                
                game_logger.debug("LOG_ANALYSIS_STARTED", {
                    "command": f"analyze_logs.py {command_option}",
                    "session": current_session,
                    "non_blocking": True
                })
            except Exception as e:
                game_logger.debug("LOG_ANALYSIS_ERROR", {
                    "error": str(e),
                    "command": command_option
                }, "error")
        
        # Run in a separate thread to avoid blocking the game
        analysis_thread = threading.Thread(target=run_command)
        analysis_thread.daemon = True
        analysis_thread.start()
        
        # Show a small notification on screen
        self.show_notification(f"Starting log analysis: {command_option}")
    
    def show_notification(self, message, duration=3):
        """Show a temporary notification message at the bottom of the screen"""
        # We'll just set a message and timestamp to be displayed in the main loop
        self.notification_message = message
        self.notification_time = time.time()
        self.notification_duration = duration
        
        game_logger.debug("NOTIFICATION_DISPLAYED", {
            "message": message,
            "duration": duration
        })
    
    def log_game_state(self, current_fps):
        """Log the current game state with detailed information"""
        game_logger.debug("GAME_STATE", {
            "player": {
                "health": self.player.health,
                "wetness": self.player.wetness,
                "fire_resistance": self.player.fire_resistance,
                "obsidian_armor": self.player.obsidian_armor_level,
                "has_obsidian_armor": self.player.has_obsidian_armor,
                "position": {"x": self.player.rect.x, "y": self.player.rect.y},
                "damage_dealt": self.player.damage_dealt,
                "damage_taken": self.player.damage_taken
            },
            "environment": {
                "current_area": self.current_area,
                "enemies_count": len(self.enemies),
                "active_sprites": len(self.all_sprites)
            },
            "performance": {
                "fps": current_fps,
                "game_time": time.time() - self.start_time,
                "memory_usage": sys.getsizeof(self)
            },
            "tutorial": {
                "active": self.tutorial.active,
                "current_step": self.tutorial.current_step if hasattr(self.tutorial, "current_step") else 0
            },
            "game_over": self.game_over
        }, "info")
    
    def save_player_progression(self):
        """Save player progression data to a file"""
        try:
            # Create a copy of the progression dictionary to avoid modifying the original
            progression_copy = {}
            for key, value in self.player.progression.items():
                # Convert sets to lists for JSON serialization
                if isinstance(value, set):
                    progression_copy[key] = list(value)
                elif isinstance(value, dict):
                    # Handle nested dictionaries that might contain sets
                    progression_copy[key] = {}
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, set):
                            progression_copy[key][sub_key] = list(sub_value)
                        else:
                            progression_copy[key][sub_key] = sub_value
                else:
                    progression_copy[key] = value
                    
            # Log progress save
            game_logger.debug("PROGRESS_SAVE", {
                "player_health": self.player.health,
                "current_area": self.current_area,
                "wetness": self.player.wetness,
                "areas_visited": progression_copy.get("areas_visited", []),
                "timestamp": time.time()
            }, "low")
            
        except Exception as e:
            game_logger.debug("PROGRESS_SAVE_ERROR", {
                "error": str(e),
                "error_type": type(e).__name__
            }, "high")
    
    def cleanup(self):
        """Clean up resources and perform final logging before shutdown"""
        # Log final state before exiting
        game_logger.debug("GAME_SHUTDOWN", {
            "total_playtime": time.time() - self.start_time,
            "final_player_state": {
                "health": self.player.health,
                "wetness": self.player.wetness,
                "obsidian_armor": self.player.obsidian_armor_level,
                "has_obsidian_armor": self.player.has_obsidian_armor,
                "damage_dealt": self.player.damage_dealt,
                "damage_taken": self.player.damage_taken,
                "final_area": self.current_area
            },
            "game_over": self.game_over,
            "cause_of_exit": "Game Over" if self.game_over else "User Quit"
        }, "critical")
        
        # Create final snapshot before exit
        game_logger.create_snapshot()
        
        # Quit pygame
        pygame.quit()
    
    def run(self):
        """Initialize and run the main game loop"""
        self.main_loop()
        
        # Clean up and exit
        self.cleanup()
    
    def main_loop(self):
        """Main game loop"""
        # Game loop
        while self.running:
            # Handle events
            self.handle_events()
            
            # Set the background
            self.screen.fill((0, 0, 0))
            
            # Only update game state if not in game over or analysis mode
            if not self.game_over and not self.showing_analysis:
                self.update()
                # Draw the game
                self.draw(self.screen)
                
                # Draw any active notifications
                self.draw_notification(self.screen)
                
                # Draw debug info if debug mode is on
                if self.debug_mode:
                    self.draw_debug_info(self.screen)
            # Draw game over screen if game is over
            elif self.game_over:
                self.draw_game_over(self.screen)
                
                # Check if it's time to auto-exit from game over
                if time.time() - self.game_over_time > self.game_over_display_duration:
                    game_logger.debug("AUTO_EXITING_GAME_OVER", {
                        "game_over_time": self.game_over_time,
                        "display_duration": self.game_over_display_duration,
                        "actual_duration": time.time() - self.game_over_time
                    }, "info")
                    self.running = False
            
            # Draw analysis results if in analysis mode
            elif self.showing_analysis:
                self.draw_analysis_results(self.screen)
            
            # Update the display
            pygame.display.flip()
            
            # Cap the frame rate
            self.clock.tick(60)
    
if __name__ == "__main__":
    game = Game()
    game.run()
