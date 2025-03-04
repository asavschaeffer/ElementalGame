"""
Elemental Game Launcher

This module provides a graphical launcher for the Elemental Progression Game,
allowing users to choose between standard gameplay or development testing mode.

Usage:
    python launcher.py
"""

import os
import sys
import pygame
import subprocess
import time
from typing import Dict, List, Any, Tuple

# Initialize pygame
pygame.init()
pygame.font.init()

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
TITLE = "Elemental Progression Launcher"
BG_COLOR = (25, 25, 35)  # Dark blue-gray
ACCENT_COLOR = (70, 130, 180)  # Steel blue
TEXT_COLOR = (255, 255, 255)  # White
HIGHLIGHT_COLOR = (255, 215, 0)  # Gold

# Button definitions
BUTTON_WIDTH, BUTTON_HEIGHT = 300, 60
BUTTON_MARGIN = 20


class Button:
    """Interactive button for the launcher UI."""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str, action: callable):
        """Initialize button with position, size, text, and action."""
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.hovered = False
        self.font = pygame.font.SysFont(None, 32)
    
    def draw(self, screen: pygame.Surface):
        """Draw the button to the screen."""
        # Determine colors based on hover state
        bg_color = HIGHLIGHT_COLOR if self.hovered else ACCENT_COLOR
        
        # Draw button background
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=8)
        pygame.draw.rect(screen, TEXT_COLOR, self.rect, 2, border_radius=8)
        
        # Render text
        text_surf = self.font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
    
    def update(self, mouse_pos: Tuple[int, int]) -> bool:
        """Update hover state based on mouse position."""
        self.hovered = self.rect.collidepoint(mouse_pos)
        return self.hovered
    
    def handle_click(self) -> bool:
        """Handle a click on this button."""
        if self.hovered:
            self.action()
            return True
        return False


class Launcher:
    """Main launcher interface for the Elemental Progression Game."""
    
    def __init__(self):
        """Initialize the launcher window and components."""
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Create fonts
        self.title_font = pygame.font.SysFont(None, 64)
        self.subtitle_font = pygame.font.SysFont(None, 32)
        self.info_font = pygame.font.SysFont(None, 24)
        
        # Create buttons
        button_x = (SCREEN_WIDTH - BUTTON_WIDTH) // 2
        
        self.buttons = [
            Button(
                button_x,
                220,
                BUTTON_WIDTH,
                BUTTON_HEIGHT,
                "Standard Game",
                self.start_standard_game
            ),
            Button(
                button_x,
                220 + BUTTON_HEIGHT + BUTTON_MARGIN,
                BUTTON_WIDTH,
                BUTTON_HEIGHT,
                "Development Tutorial",
                self.start_dev_tutorial
            ),
            Button(
                button_x,
                220 + (BUTTON_HEIGHT + BUTTON_MARGIN) * 2,
                BUTTON_WIDTH,
                BUTTON_HEIGHT,
                "Analyze Logs",
                self.analyze_logs
            ),
            Button(
                button_x,
                220 + (BUTTON_HEIGHT + BUTTON_MARGIN) * 3,
                BUTTON_WIDTH,
                BUTTON_HEIGHT,
                "Exit",
                self.exit_launcher
            )
        ]
        
        # Status message
        self.status_message = ""
        self.status_color = TEXT_COLOR
        self.status_time = 0
    
    def run(self):
        """Run the launcher main loop."""
        while self.running:
            mouse_pos = pygame.mouse.get_pos()
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    for button in self.buttons:
                        if button.handle_click():
                            break
            
            # Update buttons
            for button in self.buttons:
                button.update(mouse_pos)
            
            # Draw everything
            self.draw()
            
            # Update display
            pygame.display.flip()
            self.clock.tick(60)
    
    def draw(self):
        """Draw the launcher interface."""
        # Clear screen
        self.screen.fill(BG_COLOR)
        
        # Draw title
        title_text = self.title_font.render("Elemental Progression", True, TEXT_COLOR)
        title_rect = title_text.get_rect(centerx=SCREEN_WIDTH // 2, y=50)
        self.screen.blit(title_text, title_rect)
        
        # Draw subtitle
        subtitle_text = self.subtitle_font.render("Launcher", True, TEXT_COLOR)
        subtitle_rect = subtitle_text.get_rect(centerx=SCREEN_WIDTH // 2, y=120)
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Draw buttons
        for button in self.buttons:
            button.draw(self.screen)
        
        # Draw status message if active
        if self.status_message and time.time() - self.status_time < 5:
            status_text = self.info_font.render(self.status_message, True, self.status_color)
            status_rect = status_text.get_rect(centerx=SCREEN_WIDTH // 2, y=SCREEN_HEIGHT - 50)
            self.screen.blit(status_text, status_rect)
    
    def set_status(self, message: str, color: Tuple[int, int, int] = TEXT_COLOR):
        """Set a status message to display."""
        self.status_message = message
        self.status_color = color
        self.status_time = time.time()
    
    def start_standard_game(self):
        """Launch the standard game mode."""
        self.set_status("Starting standard game...", (100, 255, 100))
        
        try:
            # Create and set environment variable for standard mode
            env = os.environ.copy()
            env["ELEMENTAL_GAME_MODE"] = "standard"
            
            # Launch the game in a separate process
            subprocess.Popen([sys.executable, "main.py"], env=env)
            
            # Exit the launcher
            self.running = False
        except Exception as e:
            self.set_status(f"Error starting game: {e}", (255, 100, 100))
    
    def start_dev_tutorial(self):
        """Launch the game in development tutorial mode."""
        self.set_status("Starting development tutorial...", (100, 255, 100))
        
        try:
            # Create and set environment variable for dev mode
            env = os.environ.copy()
            env["ELEMENTAL_GAME_MODE"] = "dev"
            
            # Launch the game in a separate process
            subprocess.Popen([sys.executable, "main.py"], env=env)
            
            # Exit the launcher
            self.running = False
        except Exception as e:
            self.set_status(f"Error starting dev tutorial: {e}", (255, 100, 100))
    
    def analyze_logs(self):
        """Launch the log analyzer."""
        self.set_status("Opening log analyzer...", (100, 255, 100))
        
        try:
            # Launch the analyzer in a separate process
            subprocess.Popen([sys.executable, "analyze_logs.py"])
        except Exception as e:
            self.set_status(f"Error opening analyzer: {e}", (255, 100, 100))
    
    def exit_launcher(self):
        """Exit the launcher."""
        self.running = False


if __name__ == "__main__":
    launcher = Launcher()
    launcher.run()
    
    # Quit pygame
    pygame.quit()
    sys.exit()
