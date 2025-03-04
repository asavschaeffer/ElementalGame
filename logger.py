"""
Advanced Game Logging System for Elemental Game

This module implements a comprehensive, high-performance logging system specifically designed
for game state analysis and debugging. It provides:

1. Hierarchical organization of logs by game session
2. High-volume debug logging with buffering for performance
3. Time-based snapshots for state analysis (once per second)
4. Log-snapshot duplets that associate logs with their state snapshots
5. Compressed storage for efficient disk usage
6. Visualization and analysis tools for game state metrics
7. Backward compatibility with legacy log formats

The logging system is designed to capture an intense level of detail about the game state,
enabling deep analysis of patterns across gameplay sessions. This supports both debugging
and game balance analytics.

Usage:
    from logger import game_logger
    
    # Log different categories of information
    game_logger.debug("player", {"health": 100, "position": {"x": 50, "y": 30}}, "normal")
    game_logger.debug("enemy", {"type": "lava", "health": 30}, "high")
    
    # Use specialized logging methods
    game_logger.log_player_state(player)
    game_logger.log_combat_event(attacker, defender, damage, damage_type, result)
    
    # Analyze logs
    game_logger.visualize_game_data("player_health", session_id)
    game_logger.visualize_rate_of_change("enemy_count", session_id)

Author: Codeium/Cascade Team
Date: March 2025
"""

import time
import json
import os
import gzip
import base64
import pickle
import atexit
import shutil
from datetime import datetime
from loguru import logger
import threading

class GameLogger:
    def __init__(self, log_directory="logs"):
        """Initialize the game logger with comprehensive debug logging.
        
        This constructor sets up the entire logging infrastructure including directory
        structure, session management, and logging configurations. It establishes a 
        hierarchical organization of logs for better analysis capabilities.
        
        Args:
            log_directory (str): Base directory for all logs, defaults to "logs"
            
        The logger creates the following structure:
            logs/
            ├── sessions/
            │   └── session_YYYYMMDD_HHMMSS_PID/
            │       ├── manifest.json      # Session metadata
            │       ├── metadata.json      # Session results (created at end)
            │       ├── game_log.log       # Main log file
            │       ├── snapshots/         # State snapshots taken every second
            │       ├── duplets/           # Paired snapshots and log chunks
            │       └── cache/             # Compressed log chunks
            └── exports/                   # Analysis results and visualizations
        """
        self.snapshots = []
        self.log_directory = log_directory
        self.last_snapshot_time = 0
        self.snapshot_interval = 1.0  # 1 second between snapshots
        self.log_lock = threading.Lock()
        self.log_buffer = []  # Buffer for high-volume logs
        self.buffer_flush_time = 0
        self.buffer_flush_interval = 0.2  # Flush buffer every 200ms
        
        # Session identification
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"
        self.session_start_time = time.time()
        
        # In-memory cache of all logs for this session
        self.log_cache = []
        self.cache_size_limit = 10000  # Maximum number of entries before compressing to disk
        
        # Create logs directory if it doesn't exist
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)
            
        # Create organized logs directory structure
        self._setup_log_directories()
        
        # Set up loguru logger
        log_file = os.path.join(self.session_directory, f"game_log.log")
        self.log_file_path = log_file
        
        logger.remove()  # Remove default handler
        logger.add(log_file, rotation="100 MB", level="DEBUG", 
                  format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}")
        logger.add(lambda msg: print(msg), level="INFO", 
                  format="{time:HH:mm:ss} | {level} | {message}")
        
        # Register cleanup handler
        atexit.register(self.finalize_cache)
        
        # Create a session manifest file
        self._create_session_manifest()
        
        logger.info(f"Game Logger initialized for session: {self.session_id}")

    def _setup_log_directories(self):
        """Set up organized directory structure for logs.
        
        Creates a hierarchical directory structure for organizing all log data:
        
        - sessions/: Container for all game sessions
          - session_YYYYMMDD_HHMMSS_PID/: Unique session directory
            - snapshots/: Game state snapshots taken every second
            - cache/: Compressed log chunks for efficient storage
            - duplets/: Paired snapshots and log chunks for analysis
        - exports/: Analysis results and visualizations
        
        Each session gets its own isolated directory for clear separation of data
        and easier analysis capabilities.
        """
        # Create main directories
        self.sessions_directory = os.path.join(self.log_directory, "sessions")
        os.makedirs(self.sessions_directory, exist_ok=True)
        
        # Ensure session_id always has the "session_" prefix for consistency
        if not self.session_id.startswith("session_"):
            self.session_id = f"session_{self.session_id}"
        
        # Create session-specific directory
        self.session_directory = os.path.join(self.sessions_directory, self.session_id)
        os.makedirs(self.session_directory, exist_ok=True)
        
        # Create directories for different types of data
        self.snapshots_directory = os.path.join(self.session_directory, "snapshots")
        os.makedirs(self.snapshots_directory, exist_ok=True)
        
        self.cache_directory = os.path.join(self.session_directory, "cache")
        os.makedirs(self.cache_directory, exist_ok=True)
        
        self.duplets_directory = os.path.join(self.session_directory, "duplets")
        os.makedirs(self.duplets_directory, exist_ok=True)
        
        self.exports_directory = os.path.join(self.log_directory, "exports")
        os.makedirs(self.exports_directory, exist_ok=True)

    def _create_session_manifest(self):
        """Create a manifest file for the current session with metadata."""
        manifest = {
            "session_id": self.session_id,
            "start_time": self.session_start_time,
            "start_time_readable": datetime.fromtimestamp(self.session_start_time).strftime('%Y-%m-%d %H:%M:%S'),
            "log_file": self.log_file_path,
            "directories": {
                "session": self.session_directory,
                "snapshots": self.snapshots_directory,
                "cache": self.cache_directory,
                "duplets": self.duplets_directory
            }
        }
        
        # Save manifest to the session directory
        manifest_path = os.path.join(self.session_directory, "manifest.json")
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)

    def debug(self, category, data, priority="normal"):
        """
        Log debug information with categorization and priority.
        
        This is the primary logging method for game state information. It categorizes
        log entries and assigns a priority level, making it easy to filter and analyze
        the logs later.
        
        Args:
            category (str): The category of the log entry (e.g., "player", "enemy", "combat")
            data (dict): The data to log, should be serializable to JSON
            priority (str): Priority level ("low", "normal", "high", "critical")
        """
        timestamp = time.time()
        
        # Create structured log entry
        log_entry = {
            "timestamp": timestamp,
            "category": category,
            "data": data,
            "priority": priority,
            "session_id": self.session_id
        }
        
        # Add to in-memory cache
        with self.log_lock:
            self.log_buffer.append(log_entry)
            
            # Flush buffer if interval elapsed or high priority
            current_time = time.time()
            if (current_time - self.buffer_flush_time >= self.buffer_flush_interval or 
                priority in ["high", "critical"]):
                self._flush_log_buffer()
                
        # Also send to loguru for console output and file rotation
        if priority == "high" or priority == "critical":
            logger.warning(f"{category}: {json.dumps(data)}")
        else:
            logger.debug(f"{category}: {json.dumps(data)}")
            
        # Take a snapshot if it's time
        if timestamp - self.last_snapshot_time >= self.snapshot_interval:
            self.create_snapshot()
            
    def get_current_session_id(self):
        """Get the current session ID.
        
        Returns:
            str: The ID of the current logging session
        """
        return self.session_id
    
    def compress_cache_chunk(self):
        """Compress and store a chunk of the log cache to disk in a lightweight format."""
        if not self.log_cache:
            return
            
        # Create a unique filename for this chunk
        chunk_id = int(time.time() * 1000)
        chunk_file = os.path.join(self.cache_directory, f"chunk_{chunk_id}.gz")
        
        # Compress the log cache using gzip + pickle (very efficient for Python objects)
        try:
            with gzip.open(chunk_file, 'wb', compresslevel=9) as f:
                pickle.dump(self.log_cache, f, protocol=pickle.HIGHEST_PROTOCOL)
                
            # Clear the cache after successful compression
            logger.debug(f"Compressed {len(self.log_cache)} log entries to {chunk_file}")
            self.log_cache = []
        except Exception as e:
            logger.error(f"Error compressing log cache: {str(e)}")
    
    def finalize_cache(self):
        """Finalize the log cache when the game terminates."""
        # Compress any remaining logs in the cache
        if self.log_cache:
            self.compress_cache_chunk()
            
        # Create a metadata file for this session
        session_metadata = {
            "session_id": self.session_id,
            "start_time": self.session_start_time,
            "end_time": time.time(),
            "duration": time.time() - self.session_start_time,
            "log_file": self.log_file_path,
            "snapshot_count": self._count_snapshots(),
            "duplet_count": self._count_duplets()
        }
        
        metadata_file = os.path.join(self.session_directory, "metadata.json")
        try:
            with open(metadata_file, 'w') as f:
                json.dump(session_metadata, f, indent=2)
                
            # Create a symlink in the main cache directory for backward compatibility
            compat_metadata_file = os.path.join(self.log_directory, "cache", f"{self.session_id}_metadata.json")
            with open(compat_metadata_file, 'w') as f:
                json.dump(session_metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Error writing session metadata: {str(e)}")
            
        logger.debug(f"Session {self.session_id} cache finalized")
        
    def _count_snapshots(self):
        """Count the number of snapshot files for this session."""
        try:
            return len([f for f in os.listdir(self.snapshots_directory) if f.endswith('.json')])
        except:
            return 0
            
    def _count_duplets(self):
        """Count the number of duplet files for this session."""
        try:
            return len([f for f in os.listdir(self.duplets_directory) if f.endswith('.json')])
        except:
            return 0
        
    def get_cached_sessions(self):
        """Get a list of all cached sessions."""
        sessions = []
        
        # Look for session directories
        if os.path.exists(self.sessions_directory):
            for session_dir in os.listdir(self.sessions_directory):
                session_path = os.path.join(self.sessions_directory, session_dir)
                if os.path.isdir(session_path):
                    metadata_path = os.path.join(session_path, "metadata.json")
                    manifest_path = os.path.join(session_path, "manifest.json")
                    
                    # Try to load metadata, or manifest if metadata doesn't exist
                    try:
                        if os.path.exists(metadata_path):
                            with open(metadata_path, 'r') as f:
                                metadata = json.load(f)
                                sessions.append(metadata)
                        elif os.path.exists(manifest_path):
                            with open(manifest_path, 'r') as f:
                                manifest = json.load(f)
                                sessions.append(manifest)
                    except:
                        pass
        
        # For backward compatibility, also check the cache directory
        if os.path.exists(os.path.join(self.log_directory, "cache")):
            for filename in os.listdir(os.path.join(self.log_directory, "cache")):
                if filename.endswith("_metadata.json"):
                    session_id = filename.replace("_metadata.json", "")
                    
                    # Skip if we already found this session
                    if any(s.get("session_id") == session_id for s in sessions):
                        continue
                        
                    try:
                        with open(os.path.join(self.log_directory, "cache", filename), 'r') as f:
                            metadata = json.load(f)
                            sessions.append(metadata)
                    except:
                        pass
        
        # Sort by start time
        sessions.sort(key=lambda x: x.get("start_time", 0))
        return sessions
    
    def load_session_logs(self, session_id):
        """Load all logs for a given session."""
        logs = []
        
        # First try to load from new directory structure
        session_dir = os.path.join(self.sessions_directory, session_id)
        cache_dir = os.path.join(session_dir, "cache")
        
        if os.path.exists(cache_dir):
            # Find all chunk files for this session in the new location
            for filename in sorted(os.listdir(cache_dir)):
                if filename.startswith("chunk_") and filename.endswith(".gz"):
                    try:
                        with gzip.open(os.path.join(cache_dir, filename), 'rb') as f:
                            chunk_logs = pickle.load(f)
                            logs.extend(chunk_logs)
                    except Exception as e:
                        logger.error(f"Error loading log chunk {filename}: {str(e)}")
        
        # For backward compatibility, also check the old location
        if not logs and os.path.exists(os.path.join(self.log_directory, "cache")):
            for filename in sorted(os.listdir(os.path.join(self.log_directory, "cache"))):
                if filename.startswith(f"{session_id}_chunk_") and filename.endswith(".gz"):
                    try:
                        with gzip.open(os.path.join(self.log_directory, "cache", filename), 'rb') as f:
                            chunk_logs = pickle.load(f)
                            logs.extend(chunk_logs)
                    except Exception as e:
                        logger.error(f"Error loading log chunk {filename}: {str(e)}")
                        
        # Sort logs by timestamp
        logs.sort(key=lambda x: x.get("timestamp", 0))
        return logs
        
    def get_session_snapshots(self, session_id):
        """Get all snapshots for a specific session."""
        snapshots = []
        
        # Look in the session's snapshot directory
        session_dir = os.path.join(self.sessions_directory, session_id)
        snapshots_dir = os.path.join(session_dir, "snapshots")
        
        if os.path.exists(snapshots_dir):
            for filename in sorted(os.listdir(snapshots_dir)):
                if filename.startswith("snapshot_") and filename.endswith(".json"):
                    try:
                        with open(os.path.join(snapshots_dir, filename), 'r') as f:
                            snapshot = json.load(f)
                            snapshots.append(snapshot)
                    except Exception as e:
                        logger.error(f"Error loading snapshot {filename}: {str(e)}")
        
        return snapshots
        
    def get_session_duplets(self, session_id):
        """Get all duplets for a specific session."""
        duplets = []
        
        # Look in the session's duplet directory
        session_dir = os.path.join(self.sessions_directory, session_id)
        duplets_dir = os.path.join(session_dir, "duplets")
        
        if os.path.exists(duplets_dir):
            for filename in sorted(os.listdir(duplets_dir)):
                if filename.startswith("duplet_") and filename.endswith(".json"):
                    try:
                        with open(os.path.join(duplets_dir, filename), 'r') as f:
                            duplet = json.load(f)
                            duplets.append(duplet)
                    except Exception as e:
                        logger.error(f"Error loading duplet {filename}: {str(e)}")
        
        return duplets

    def create_snapshot(self):
        """Create a snapshot of the current game state for time-series analysis.
        
        This method captures the accumulated game state data (collected at 1-second intervals)
        and creates a structured JSON snapshot. These snapshots serve as the foundation for
        pattern analysis across time by providing:
        
        1. Categorized data organization (player, enemy, environment, etc.)
        2. Precise timestamping for temporal analysis
        3. Session correlation for gameplay pattern identification
        4. Duplet creation that links logs with corresponding game states
        
        Snapshots are stored in two locations:
        - session_id/snapshots/ - Primary location for the current session
        - logs/ - Legacy location for backward compatibility
        
        Each snapshot generates a corresponding duplet that pairs it with relevant logs
        for comprehensive context during analysis.
        
        Returns:
            None
        """
        if not self.snapshots:
            return
            
        snapshot_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_file = os.path.join(self.snapshots_directory, f"snapshot_{snapshot_time}.json")
        
        # Group logs by category for better analysis
        categorized_data = {}
        for entry in self.snapshots:
            category = entry["category"]
            if category not in categorized_data:
                categorized_data[category] = []
            categorized_data[category].append(entry)
        
        # Save snapshot to file with detailed metadata
        snapshot_data = {
            "timestamp": time.time(),
            "snapshot_time": snapshot_time,
            "session_id": self.session_id,
            "snapshot_data": categorized_data
        }
        
        # Save snapshot to file
        with open(snapshot_file, "w") as f:
            json.dump(snapshot_data, f, indent=2)
            
        # For backward compatibility, also create a copy in the original location
        compat_snapshot_file = os.path.join(self.log_directory, f"snapshot_{snapshot_time}.json")
        with open(compat_snapshot_file, "w") as f:
            json.dump(snapshot_data, f, indent=2)
        
        # Create a duplet by pairing this snapshot with recent logs
        self._create_snapshot_log_duplet(snapshot_data, snapshot_time)
            
        # Clear snapshots after saving
        self.snapshots = []
        logger.debug(f"Created game state snapshot: {snapshot_file}")
    
    def _create_snapshot_log_duplet(self, snapshot_data, snapshot_time):
        """Create a duplet by pairing this snapshot with recently cached logs."""
        # Get the most recent log chunk
        cache_files = [f for f in os.listdir(self.cache_directory) if f.endswith(".gz")]
        if not cache_files:
            return
            
        # Sort by time and get the most recent
        cache_files.sort(reverse=True)
        if not cache_files:
            return
            
        recent_chunk = cache_files[0]
        
        # Create a duplet file
        duplet_file = os.path.join(self.duplets_directory, f"duplet_{snapshot_time}.json")
        
        # Create duplet metadata
        duplet_data = {
            "snapshot_file": os.path.join(self.snapshots_directory, f"snapshot_{snapshot_time}.json"),
            "log_chunk": os.path.join(self.cache_directory, recent_chunk),
            "timestamp": time.time(),
            "snapshot_time": snapshot_time,
            "session_id": self.session_id,
            "categories": list(snapshot_data["snapshot_data"].keys())
        }
        
        # Save duplet
        with open(duplet_file, "w") as f:
            json.dump(duplet_data, f, indent=2)
            
        logger.debug(f"Created snapshot-log duplet: {duplet_file}")

    def log_player_state(self, player):
        """Log comprehensive player state information."""
        self.debug("player", {
            "health": player.health,
            "max_health": player.max_health,
            "position": {"x": player.rect.x, "y": player.rect.y},
            "wetness": player.wetness,
            "fire_resistance": player.fire_resistance,
            "has_obsidian_armor": player.has_obsidian_armor,
            "obsidian_armor_level": player.obsidian_armor_level,
            "current_area": player.current_area,
            "damage_dealt": player.damage_dealt,
            "damage_taken": player.damage_taken
        }, "normal")
    
    def log_enemy_spawned(self, enemy):
        """Log when an enemy is spawned with detailed information."""
        self.debug("enemy_spawn", {
            "type": enemy.type,
            "id": id(enemy),
            "health": enemy.health,
            "damage": enemy.damage,
            "position": {"x": enemy.rect.x, "y": enemy.rect.y},
            "area": enemy.area
        }, "normal")
    
    def log_combat_event(self, attacker, defender, damage, damage_type, result):
        """Log detailed combat interaction."""
        self.debug("combat", {
            "attacker": attacker.type if hasattr(attacker, "type") else "player",
            "attacker_id": id(attacker),
            "defender": defender.type if hasattr(defender, "type") else "player",
            "defender_id": id(defender),
            "damage_attempted": damage,
            "damage_type": damage_type,
            "actual_damage": result.get("actual_damage", 0),
            "resistance_applied": result.get("resistance_applied", 0),
            "effects": result.get("effects", [])
        }, "high")
    
    def log_area_transition(self, player, old_area, new_area):
        """Log when player transitions between game areas."""
        self.debug("area_transition", {
            "player_id": id(player),
            "old_area": old_area,
            "new_area": new_area,
            "player_health": player.health,
            "wetness": player.wetness,
            "has_obsidian_armor": player.has_obsidian_armor
        }, "high")
    
    def log_environment_state(self, area, active_enemies, environmental_hazards):
        """Log the state of the game environment."""
        self.debug("environment", {
            "area": area,
            "enemy_count": len(active_enemies),
            "enemy_types": [e.type for e in active_enemies],
            "hazards": [h.type for h in environmental_hazards] if environmental_hazards else []
        }, "normal")

    def visualize_game_data(self, metric_name="player_health", session_id=None):
        """
        Create and display a visualization of game data using the calculus analogy.
        
        Args:
            metric_name (str): The metric to visualize (e.g., "player_health", "enemy_count")
            session_id (str): The session ID to analyze (uses most recent if None)
        
        Returns:
            str: Path to the saved visualization, or None if visualization failed
        """
        try:
            # Lazy import to avoid circular imports
            from visualization import GameStateVisualizer
            
            # Create visualizer with this logger instance
            visualizer = GameStateVisualizer(self)
            
            # Create exports directory if it doesn't exist
            export_dir = os.path.join(self.log_directory, "exports")
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
            
            # Create visualization
            if session_id is None:
                sessions = self.get_cached_sessions()
                if sessions:
                    session_id = sessions[-1]['session_id']  # Use most recent
                else:
                    logger.warning("No game sessions found to visualize")
                    return None
            
            # Generate the visualization
            save_path = os.path.join(export_dir, f"{session_id}_{metric_name}.png")
            visualizer.visualize_session_data(session_id, metric_name, save_path)
            
            logger.info(f"Visualization of {metric_name} saved to: {save_path}")
            return save_path
            
        except ImportError as e:
            logger.error(f"Visualization failed: {str(e)}. Make sure matplotlib, numpy, and scipy are installed.")
            return None
        except Exception as e:
            logger.error(f"Visualization error: {str(e)}")
            return None
    
    def visualize_rate_of_change(self, metric_name="player_health", session_id=None, window_size=3):
        """
        Create and display a visualization of the rate of change for a game metric.
        
        Args:
            metric_name (str): The metric to analyze (e.g., "player_health", "enemy_count")
            session_id (str): The session ID to analyze (uses most recent if None)
            window_size (int): Size of window for calculating derivatives
        
        Returns:
            str: Path to the saved visualization, or None if visualization failed
        """
        try:
            # Lazy import to avoid circular imports
            from visualization import GameStateVisualizer
            
            # Create visualizer with this logger instance
            visualizer = GameStateVisualizer(self)
            
            # Create exports directory if it doesn't exist
            export_dir = os.path.join(self.log_directory, "exports")
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
            
            # Use most recent session if none specified
            if session_id is None:
                sessions = self.get_cached_sessions()
                if sessions:
                    session_id = sessions[-1]['session_id']
                else:
                    logger.warning("No game sessions found to visualize")
                    return None
            
            # Generate the visualization
            save_path = os.path.join(export_dir, f"{session_id}_{metric_name}_derivative.png")
            visualizer.analyze_derivative(session_id, metric_name, window_size, save_path)
            
            logger.info(f"Rate of change analysis for {metric_name} saved to: {save_path}")
            return save_path
            
        except ImportError as e:
            logger.error(f"Visualization failed: {str(e)}. Make sure matplotlib, numpy, and scipy are installed.")
            return None
        except Exception as e:
            logger.error(f"Visualization error: {str(e)}")
            return None
    
    def demonstrate_calculus_analogy(self):
        """
        Create and save the calculus analogy visualization.
        
        Returns:
            str: Path to the saved visualization
        """
        try:
            # Lazy import to avoid circular imports
            from visualization import GameStateVisualizer
            
            # Create visualizer with this logger instance
            visualizer = GameStateVisualizer(self)
            
            # Create exports directory if it doesn't exist
            export_dir = os.path.join(self.log_directory, "exports")
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
            
            # Generate the visualization
            save_path = os.path.join(export_dir, "calculus_analogy.png")
            visualizer.visualize_calculus_analogy(save_path)
            
            logger.info(f"Calculus analogy visualization saved to: {save_path}")
            return save_path
            
        except ImportError as e:
            logger.error(f"Visualization failed: {str(e)}. Make sure matplotlib, numpy, and scipy are installed.")
            return None
        except Exception as e:
            logger.error(f"Visualization error: {str(e)}")
            return None

    def _flush_log_buffer(self):
        """Flush the log buffer to disk in bulk."""
        if not self.log_buffer:
            return
            
        # Group by category for more efficient logging
        by_category = {}
        for entry in self.log_buffer:
            category = entry["category"]
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(entry)
        
        # Log each category in bulk
        for category, entries in by_category.items():
            if len(entries) == 1:
                # Single entry - log normally
                entry = entries[0]
                message = f"[{category}] {json.dumps(entry['data'])}"
                logger.debug(message)
            else:
                # Multiple entries - log count and first/last
                message = f"[{category}] Bulk log: {len(entries)} entries from {entries[0]['timestamp']} to {entries[-1]['timestamp']}"
                logger.debug(message)
                
                # Log first and last entry in detail
                logger.debug(f"[{category}] First: {json.dumps(entries[0]['data'])}")
                logger.debug(f"[{category}] Last: {json.dumps(entries[-1]['data'])}")
        
        # Clear buffer
        self.log_buffer = []
    
    def export_session_data(self, session_id, output_format="json"):
        """Export session data to a file in the specified format."""
        logs = self.load_session_logs(session_id)
        if not logs:
            return None
            
        # Create exports directory if it doesn't exist
        exports_dir = os.path.join(self.log_directory, "exports")
        if not os.path.exists(exports_dir):
            os.makedirs(exports_dir)
            
        output_file = os.path.join(exports_dir, f"{session_id}_export.{output_format}")
        
        if output_format == "json":
            with open(output_file, 'w') as f:
                json.dump(logs, f)
        elif output_format == "csv":
            import csv
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                # Write header
                if logs:
                    sample = logs[0]
                    header = ["timestamp", "category", "priority"]
                    if "data" in sample and isinstance(sample["data"], dict):
                        for key in sample["data"].keys():
                            header.append(f"data.{key}")
                    writer.writerow(header)
                    
                    # Write data rows
                    for log in logs:
                        row = [log.get("timestamp", ""), log.get("category", ""), log.get("priority", "")]
                        if "data" in log and isinstance(log["data"], dict):
                            for key in sample["data"].keys():
                                row.append(str(log["data"].get(key, "")))
                        writer.writerow(row)
        
        return output_file

# Global instance for easy access
game_logger = GameLogger()
