"""
Input Tracking System for Elemental Game

This module implements a sophisticated input tracking system that logs all keyboard and mouse
interactions with high precision while optimizing log volume by only reporting changes.

Features:
1. Tracks all keyboard key states (pressed/released)
2. Monitors mouse position and button states
3. Uses differential logging - only reports changes between frames
4. Provides detailed timestamps for precise interaction analysis
5. Integrates seamlessly with the game's existing logging framework

Usage:
    from input_tracker import InputTracker
    
    # Initialize in game class
    self.input_tracker = InputTracker(game_logger)
    
    # Update every frame in main loop
    self.input_tracker.update()
"""

import pygame
import time
from logger import game_logger

class InputTracker:
    """
    Tracks and logs all keyboard and mouse inputs with change detection.
    
    This class samples the input state each frame and logs only the changes,
    ensuring comprehensive input tracking without excessive log volume.
    """
    
    def __init__(self, logger):
        """Initialize the input tracker with its own logger instance."""
        self.logger = logger
        
        # Initialize previous input states
        self.prev_keys = {}
        self.prev_mouse_pos = (0, 0)
        self.prev_mouse_buttons = [False, False, False]  # Left, Middle, Right
        
        # For keyboard tracking, we'll initialize with all keys as released
        for key_constant in range(pygame.K_FIRST, pygame.K_LAST + 1):
            self.prev_keys[key_constant] = False
            
        # Track when we last logged a complete input state snapshot
        self.last_full_snapshot_time = 0
        self.full_snapshot_interval = 5.0  # Log full state every 5 seconds
        
        # Log creation
        self.logger.debug("INPUT_TRACKER_INITIALIZED", {
            "timestamp": time.time(),
            "tracked_keys": len(self.prev_keys),
            "mouse_tracking": True
        }, "normal")
    
    def update(self):
        """
        Update input tracking, detecting and logging changes.
        
        Call this method once per game frame to maintain accurate input tracking.
        """
        current_time = time.time()
        
        # Get current input states
        current_keys = pygame.key.get_pressed()
        current_mouse_pos = pygame.mouse.get_pos()
        current_mouse_buttons = pygame.mouse.get_pressed()
        
        # Check for changes in keyboard state
        key_changes = {}
        for key_constant in range(pygame.K_FIRST, pygame.K_LAST + 1):
            # Skip keys that don't exist or are out of range
            if key_constant >= len(current_keys):
                continue
                
            current_state = bool(current_keys[key_constant])
            if current_state != self.prev_keys.get(key_constant, False):
                # State changed, record it
                key_changes[key_constant] = current_state
                self.prev_keys[key_constant] = current_state
        
        # Check for mouse position changes
        mouse_pos_changed = current_mouse_pos != self.prev_mouse_pos
        if mouse_pos_changed:
            self.prev_mouse_pos = current_mouse_pos
        
        # Check for mouse button changes
        button_changes = {}
        for i, (current, previous) in enumerate(zip(current_mouse_buttons, self.prev_mouse_buttons)):
            if current != previous:
                button_names = ["LEFT", "MIDDLE", "RIGHT"]
                button_changes[button_names[i]] = current
                self.prev_mouse_buttons[i] = current
        
        # Log changes if any occurred
        changes_detected = key_changes or mouse_pos_changed or button_changes
        
        if changes_detected:
            log_data = {
                "timestamp": current_time,
                "frame_delta": current_time - self.last_full_snapshot_time if self.last_full_snapshot_time > 0 else 0
            }
            
            # Add key changes if any
            if key_changes:
                key_names = {key: pygame.key.name(key) for key in key_changes.keys()}
                log_data["key_changes"] = [{
                    "key_code": k, 
                    "key_name": key_names.get(k, f"Unknown-{k}"),
                    "pressed": v
                } for k, v in key_changes.items()]
            
            # Add mouse position if changed
            if mouse_pos_changed:
                log_data["mouse_position"] = {
                    "x": current_mouse_pos[0],
                    "y": current_mouse_pos[1],
                    "previous_x": self.prev_mouse_pos[0],
                    "previous_y": self.prev_mouse_pos[1],
                    "delta_x": current_mouse_pos[0] - self.prev_mouse_pos[0],
                    "delta_y": current_mouse_pos[1] - self.prev_mouse_pos[1]
                }
            
            # Add button changes if any
            if button_changes:
                log_data["mouse_button_changes"] = [
                    {"button": k, "pressed": v} for k, v in button_changes.items()
                ]
            
            # Log the changes
            self.logger.debug("INPUT_STATE_CHANGES", log_data, "low")
        
        # Periodically log the full input state for reference
        if current_time - self.last_full_snapshot_time >= self.full_snapshot_interval:
            self._log_full_snapshot(current_time, current_keys, current_mouse_pos, current_mouse_buttons)
            self.last_full_snapshot_time = current_time
    
    def _log_full_snapshot(self, current_time, current_keys, current_mouse_pos, current_mouse_buttons):
        """Log the complete input state periodically as a reference snapshot."""
        # Get all pressed keys for the snapshot
        pressed_keys = []
        for key_constant in range(pygame.K_FIRST, pygame.K_LAST + 1):
            if key_constant < len(current_keys) and current_keys[key_constant]:
                key_name = pygame.key.name(key_constant)
                if key_name:  # Only include valid keys
                    pressed_keys.append({
                        "key_code": key_constant,
                        "key_name": key_name
                    })
        
        # Create snapshot with current mouse and keyboard state
        snapshot_data = {
            "timestamp": current_time,
            "pressed_keys_count": len(pressed_keys),
            "pressed_keys": pressed_keys,
            "mouse_position": {
                "x": current_mouse_pos[0],
                "y": current_mouse_pos[1]
            },
            "mouse_buttons": {
                "left": current_mouse_buttons[0],
                "middle": current_mouse_buttons[1],
                "right": current_mouse_buttons[2]
            }
        }
        
        # Log the full snapshot
        self.logger.debug("INPUT_FULL_SNAPSHOT", snapshot_data, "low")
        
    def force_full_snapshot(self):
        """Force an immediate full snapshot of all input states."""
        current_keys = pygame.key.get_pressed()
        current_mouse_pos = pygame.mouse.get_pos()
        current_mouse_buttons = pygame.mouse.get_pressed()
        self._log_full_snapshot(time.time(), current_keys, current_mouse_pos, current_mouse_buttons)
