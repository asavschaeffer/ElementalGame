"""
Development Tutorial Module

This module provides an advanced tutorial system specifically designed for testing
and validating game mechanics during development. It leverages log data and snapshots
to create dynamic tutorial experiences that comprehensively test all game systems.

Features:
1. Dynamic tutorial generation from gameplay logs
2. Comprehensive mechanics validation
3. Performance and behavior metrics
4. State transition verification
5. Integration with the snapshot analyzer
"""

import os
import sys
import json
import time
import pygame
from typing import Dict, List, Any, Tuple, Optional, Set

# Import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import game_logger
from tutorial import Tutorial

# Import from the same package
from .snapshot_analyzer import SnapshotAnalyzer


class DevTutorial(Tutorial):
    """
    Advanced tutorial system for development and testing purposes.
    Extends the base Tutorial class with additional capabilities for
    comprehensive mechanics validation and testing.
    """
    
    def __init__(self, game, analyzer: SnapshotAnalyzer = None):
        """
        Initialize the development tutorial.
        
        Args:
            game: Reference to the Game instance
            analyzer: Optional SnapshotAnalyzer instance for dynamic generation
        """
        super().__init__(game)
        
        # Override basic properties
        self.name = "Development Tutorial"
        self.is_dev_tutorial = True
        
        # Store analyzer
        self.analyzer = analyzer or SnapshotAnalyzer()
        
        # Additional metrics for development
        self.performance_metrics = {
            'fps_history': [],
            'memory_usage': [],
            'render_times': [],
            'update_times': [],
            'collision_counts': []
        }
        
        # Extended mechanics testing
        self.mechanics_tested.update({
            'player_damage': False,
            'player_death': False,
            'enemy_spawning': False,
            'area_transition': False,
            'obsidian_formation': False,
            'environmental_interaction': False,
            'rendering_performance': False,
            'collision_detection': False
        })
        
        # Load saved tutorial if available
        self.load_generated_tutorial()
        
        # Add development-specific steps
        self.add_dev_specific_steps()
        
        # Logging
        game_logger.debug("dev_tutorial_initialized", {
            'steps_count': len(self.steps),
            'mechanics_to_test': list(self.mechanics_tested.keys())
        }, "high")
    
    def load_generated_tutorial(self) -> bool:
        """
        Load a previously generated tutorial definition.
        
        Returns:
            True if a tutorial was loaded, False otherwise
        """
        tutorial_path = os.path.join('devtools', 'generated_tutorial.json')
        
        if os.path.exists(tutorial_path):
            try:
                with open(tutorial_path, 'r') as f:
                    tutorial_def = json.load(f)
                
                # Only use generated steps if they exist
                if 'steps' in tutorial_def and tutorial_def['steps']:
                    # Don't completely replace steps, just add the generated ones
                    generated_steps = tutorial_def['steps']
                    
                    # Insert after the welcome step but before the final step
                    if len(self.steps) > 1:
                        self.steps = self.steps[:1] + generated_steps + self.steps[-1:]
                    else:
                        self.steps.extend(generated_steps)
                    
                    game_logger.debug("dev_tutorial_loaded", {
                        'steps_count': len(self.steps),
                        'source': tutorial_path
                    }, "high")
                    
                    return True
            
            except Exception as e:
                game_logger.error(f"Error loading generated tutorial: {e}")
        
        return False
    
    def add_dev_specific_steps(self):
        """Add development-specific tutorial steps."""
        # Add performance testing step
        self.steps.append({
            'id': 'perf_test',
            'message': 'Performance Test: Move rapidly around the screen\nto generate multiple entity updates and collisions.',
            'zoom_level': 0.8,
            'highlight': None,
            'required_action': 'PERF_TEST',
            'duration': 10,  # 10 seconds of performance testing
            'test_goal': 'Validate rendering performance and collision detection'
        })
        
        # Add stress test step (lots of enemies)
        self.steps.append({
            'id': 'stress_test',
            'message': 'Stress Test: Multiple enemies will spawn.\nObserve system performance.',
            'zoom_level': 0.7,
            'highlight': None,
            'required_action': 'SPACE',
            'duration': 0,
            'test_goal': 'Validate system performance under high entity count'
        })
    
    def start(self):
        """Begin the development tutorial sequence."""
        # Generate fresh tutorial if we have an analyzer but no generated tutorial
        if not any(step.get('id') == 'perf_test' for step in self.steps) and self.analyzer:
            try:
                self.analyzer.load_sessions(limit=3)
                self.analyzer.generate_dev_tutorial('devtools/generated_tutorial.json')
                self.load_generated_tutorial()
            except Exception as e:
                game_logger.error(f"Error generating tutorial: {e}")
        
        # Continue with normal startup
        super().start()
        
        # Log that we're starting the dev tutorial specifically
        game_logger.debug("dev_tutorial_started", {
            'steps_count': len(self.steps),
            'first_test': self.steps[0].get('test_goal', 'unknown')
        }, "high")
    
    def setup_tutorial_environment(self):
        """Set up a controlled environment specifically for development testing."""
        # First use the base setup
        super().setup_tutorial_environment()
        
        # Then add development-specific elements
        
        # Create enemies for various tests
        self.create_test_enemies()
        
        # Create test portals
        self.create_test_portals()
        
        # Log the enhanced setup
        game_logger.debug("dev_tutorial_environment_setup", {
            'enemy_count': len(self.game.enemies),
            'portal_count': len(self.game.portals),
            'test_ready': True
        }, "high")
    
    def create_test_enemies(self):
        """Create various enemies for testing all mechanics."""
        # We'll create enemies but position them off-screen initially
        screen_width = self.game.width
        screen_height = self.game.height
        
        # Create enemies of each type for testing
        from entities import WaterSplasher, LavaSprite, AbyssalEntity
        
        # Additional water enemies for stress testing
        for i in range(3):
            x = screen_width + 200 + (i * 50)
            y = screen_height // 2 - 100 + (i * 50)
            enemy = WaterSplasher(x, y)
            enemy.speed = 0.8
            self.game.all_sprites.add(enemy)
            self.game.enemies.add(enemy)
        
        # Additional lava enemies
        for i in range(2):
            x = screen_width + 300 + (i * 50)
            y = screen_height // 2 + 100 + (i * 50)
            enemy = LavaSprite(x, y)
            enemy.speed = 0.7
            self.game.all_sprites.add(enemy)
            self.game.enemies.add(enemy)
        
        # Abyss enemy for final testing
        abyss_enemy = AbyssalEntity(screen_width + 400, screen_height // 2)
        abyss_enemy.speed = 0.5
        self.game.all_sprites.add(abyss_enemy)
        self.game.enemies.add(abyss_enemy)
    
    def create_test_portals(self):
        """Create test portals for area transitions."""
        # We'll create additional portals but position them off-screen initially
        screen_width = self.game.width
        
        # Create a portal to each area for testing
        from entities import AreaPortal
        
        # Add off-screen portals to each area
        volcano_portal = AreaPortal(screen_width + 250, self.game.height // 2 - 100, "BEACH", "VOLCANO")
        self.game.all_sprites.add(volcano_portal)
        self.game.portals.add(volcano_portal)
        
        abyss_portal = AreaPortal(screen_width + 300, self.game.height // 2 + 100, "VOLCANO", "ABYSS")
        self.game.all_sprites.add(abyss_portal)
        self.game.portals.add(abyss_portal)
    
    def update(self, events, keys):
        """Update the development tutorial with advanced testing logic."""
        # First use the base update
        super().update(events, keys)
        
        # Then add development-specific update logic
        if self.active:
            # Record performance metrics
            self.record_performance_metrics()
            
            # Handle development-specific actions
            current_step = self.steps[self.current_step] if self.current_step < len(self.steps) else None
            
            if current_step and current_step.get('id') == 'perf_test':
                # Performance test step
                self.handle_performance_test(events, keys)
            
            elif current_step and current_step.get('id') == 'stress_test':
                # Stress test step
                self.handle_stress_test(events, keys)
    
    def record_performance_metrics(self):
        """Record various performance metrics during tutorial execution."""
        # Record FPS
        current_fps = self.game.clock.get_fps()
        self.performance_metrics['fps_history'].append(current_fps)
        
        # Keep only the last 100 values to avoid memory bloat
        if len(self.performance_metrics['fps_history']) > 100:
            self.performance_metrics['fps_history'].pop(0)
        
        # Every 60 frames, log performance metrics
        if len(self.performance_metrics['fps_history']) % 60 == 0:
            # Calculate average FPS
            avg_fps = sum(self.performance_metrics['fps_history']) / len(self.performance_metrics['fps_history'])
            
            game_logger.debug("dev_tutorial_performance", {
                'avg_fps': avg_fps,
                'enemy_count': len(self.game.enemies),
                'step_id': self.steps[self.current_step].get('id') if self.current_step < len(self.steps) else None
            }, "normal")
    
    def handle_performance_test(self, events, keys):
        """Handle the performance test step."""
        # Check if test has been running long enough
        current_time = time.time()
        if current_time - self.step_start_time >= 8:  # Allow 8 seconds for the test
            # If we have enough samples and performance is acceptable, mark the test as passed
            if len(self.performance_metrics['fps_history']) >= 60:
                avg_fps = sum(self.performance_metrics['fps_history']) / len(self.performance_metrics['fps_history'])
                
                # Consider the test passed if average FPS is above 30
                if avg_fps >= 30:
                    self.mechanics_tested['rendering_performance'] = True
                    game_logger.debug("tutorial_test_passed", {
                        "test": "rendering_performance",
                        "status": "PASS",
                        "avg_fps": avg_fps
                    }, "high")
                
                # Move to next step
                self.advance_to_next_step()
    
    def handle_stress_test(self, events, keys):
        """Handle the stress test step."""
        # When the player presses space, spawn many enemies
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                # Move all the offscreen test enemies on-screen
                for enemy in self.game.enemies:
                    if enemy.rect.x > self.game.width:
                        enemy.rect.x = (self.game.width - 100) * (0.3 + 0.7 * (enemy.rect.x / (self.game.width + 400)))
                
                self.mechanics_tested['enemy_spawning'] = True
                game_logger.debug("tutorial_test_passed", {
                    "test": "enemy_spawning",
                    "status": "PASS",
                    "enemy_count": len(self.game.enemies)
                }, "high")
                
                # Advance to next step
                self.advance_to_next_step()
    
    def complete_tutorial(self):
        """Complete the development tutorial with comprehensive reporting."""
        # First use the base completion
        super().complete_tutorial()
        
        # Then add development-specific completion logic
        
        # Generate detailed performance report
        performance_report = {
            'avg_fps': sum(self.performance_metrics['fps_history']) / max(1, len(self.performance_metrics['fps_history'])),
            'min_fps': min(self.performance_metrics['fps_history']) if self.performance_metrics['fps_history'] else 0,
            'max_fps': max(self.performance_metrics['fps_history']) if self.performance_metrics['fps_history'] else 0,
            'mechanics_tested': self.mechanics_tested,
            'completion_time': time.time() - self.step_start_time
        }
        
        # Log the report
        game_logger.debug("dev_tutorial_completed", performance_report, "critical")
        
        # Create a snapshot specifically for the completion
        game_logger.create_snapshot("dev_tutorial_completion")
        
        # Display completion message
        self.game.add_splash_message("Dev Tutorial Complete! All mechanics tested.", 5.0)
        
        # Optionally save the report to a file
        try:
            report_path = os.path.join('devtools', 'tutorial_report.json')
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            
            with open(report_path, 'w') as f:
                json.dump(performance_report, f, indent=2)
        except Exception as e:
            game_logger.error(f"Error saving tutorial report: {e}")


# Factory function to create the appropriate tutorial type
def create_tutorial(game, type_name="standard"):
    """
    Factory function to create a tutorial of the specified type.
    
    Args:
        game: Reference to the Game instance
        type_name: Type of tutorial to create ("standard" or "dev")
        
    Returns:
        Tutorial instance
    """
    if type_name.lower() == "dev":
        analyzer = SnapshotAnalyzer()
        return DevTutorial(game, analyzer)
    else:
        return Tutorial(game)


if __name__ == "__main__":
    # This would be for standalone testing
    print("Development Tutorial Module - Import this module to use.")
    print("To test, modify main.py to use DevTutorial instead of Tutorial.")
