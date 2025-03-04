"""
Snapshot Analyzer Module

This module provides tools for analyzing game session snapshots from the logging system,
flattening time-series data, and extracting patterns for use in development tutorials.

The analyzer can:
1. Load multiple sessions and their snapshots
2. Flatten snapshots into time-series data
3. Extract key state changes and events
4. Generate tutorial steps based on observed patterns
5. Visualize progression and state changes
"""

import os
import json
import glob
import time
import datetime
from collections import defaultdict
from typing import Dict, List, Any, Tuple, Optional, Set

# Import from parent directory
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import game_logger


class SnapshotAnalyzer:
    """Analyzes game session snapshots to extract patterns and generate development insights."""
    
    def __init__(self, sessions_dir: str = None):
        """Initialize the snapshot analyzer with a target sessions directory."""
        self.sessions_dir = sessions_dir or os.path.join('logs', 'sessions')
        self.sessions = {}  # session_id -> session data
        self.flattened_data = {}  # Flattened time series data
        self.entity_history = defaultdict(list)  # Entity ID -> state history
        self.event_timeline = []  # Chronological list of significant events
        self.observed_patterns = []  # Patterns detected across sessions
        
    def load_sessions(self, limit: int = None, most_recent: bool = True) -> int:
        """
        Load session data from disk.
        
        Args:
            limit: Maximum number of sessions to load
            most_recent: If True, load most recent sessions; otherwise, load oldest
            
        Returns:
            Number of sessions loaded
        """
        session_paths = glob.glob(os.path.join(self.sessions_dir, 'session_*'))
        
        # Sort by creation time (newest or oldest first)
        session_paths.sort(key=os.path.getctime, reverse=most_recent)
        
        # Limit the number of sessions if specified
        if limit:
            session_paths = session_paths[:limit]
        
        # Load each session
        for session_path in session_paths:
            session_id = os.path.basename(session_path)
            
            # Load metadata
            metadata_path = os.path.join(session_path, 'metadata.json')
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    
                    # Create session entry
                    self.sessions[session_id] = {
                        'id': session_id,
                        'path': session_path,
                        'metadata': metadata,
                        'snapshots': None,  # Lazy load snapshots
                        'log_entries': None  # Lazy load log entries
                    }
                except Exception as e:
                    print(f"Error loading session {session_id}: {e}")
        
        return len(self.sessions)
    
    def load_session_snapshots(self, session_id: str) -> int:
        """
        Load snapshots for a specific session.
        
        Args:
            session_id: ID of the session to load snapshots for
            
        Returns:
            Number of snapshots loaded
        """
        if session_id not in self.sessions:
            print(f"Session {session_id} not found")
            return 0
            
        session = self.sessions[session_id]
        snapshot_dir = os.path.join(session['path'], 'snapshots')
        
        if not os.path.exists(snapshot_dir):
            print(f"No snapshots directory found for session {session_id}")
            return 0
            
        # Load all snapshot files
        snapshot_files = glob.glob(os.path.join(snapshot_dir, '*.json'))
        snapshots = []
        
        for snapshot_file in snapshot_files:
            try:
                with open(snapshot_file, 'r') as f:
                    snapshot = json.load(f)
                snapshots.append(snapshot)
            except Exception as e:
                print(f"Error loading snapshot {snapshot_file}: {e}")
        
        # Sort snapshots by timestamp
        snapshots.sort(key=lambda x: x.get('timestamp', 0))
        
        # Store in session
        session['snapshots'] = snapshots
        
        return len(snapshots)
    
    def load_session_logs(self, session_id: str) -> int:
        """
        Load log entries for a specific session.
        
        Args:
            session_id: ID of the session to load logs for
            
        Returns:
            Number of log entries loaded
        """
        if session_id not in self.sessions:
            print(f"Session {session_id} not found")
            return 0
            
        session = self.sessions[session_id]
        log_file = os.path.join(session['path'], 'game_log.log')
        
        if not os.path.exists(log_file):
            print(f"No log file found for session {session_id}")
            return 0
            
        # Parse log file 
        log_entries = []
        
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    # Quick and simple parsing - could be enhanced
                    if "debug" in line.lower():
                        parts = line.split("|")
                        if len(parts) >= 4:
                            timestamp_str = parts[0].strip()
                            level = parts[1].strip()
                            message = parts[2].strip()
                            data = parts[3].strip()
                            
                            try:
                                # Parse timestamp
                                timestamp = datetime.datetime.strptime(
                                    timestamp_str, 
                                    "%Y-%m-%d %H:%M:%S.%f"
                                ).timestamp()
                                
                                # Try to parse data as JSON
                                try:
                                    data_json = json.loads(data)
                                except:
                                    data_json = {'raw': data}
                                
                                log_entries.append({
                                    'timestamp': timestamp,
                                    'level': level,
                                    'message': message,
                                    'data': data_json
                                })
                            except Exception as e:
                                print(f"Error parsing log entry: {e}")
        except Exception as e:
            print(f"Error loading log file {log_file}: {e}")
        
        # Sort log entries by timestamp
        log_entries.sort(key=lambda x: x.get('timestamp', 0))
        
        # Store in session
        session['log_entries'] = log_entries
        
        return len(log_entries)
    
    def flatten_snapshots(self, session_id: str = None) -> Dict[str, List[Dict]]:
        """
        Flatten snapshots into time-series data for each tracked entity/property.
        
        Args:
            session_id: Optional specific session to flatten
            
        Returns:
            Dict mapping entity types to time-series data
        """
        sessions_to_process = [session_id] if session_id else self.sessions.keys()
        flattened = defaultdict(list)
        
        for sid in sessions_to_process:
            if sid not in self.sessions:
                continue
                
            session = self.sessions[sid]
            
            # Ensure snapshots are loaded
            if not session.get('snapshots'):
                self.load_session_snapshots(sid)
                
            if not session.get('snapshots'):
                continue
                
            # Process each snapshot
            for snapshot in session['snapshots']:
                timestamp = snapshot.get('timestamp', 0)
                
                # Extract player data
                if 'player' in snapshot:
                    player_data = snapshot['player']
                    player_data['timestamp'] = timestamp
                    player_data['session_id'] = sid
                    flattened['player'].append(player_data)
                
                # Extract enemies data
                if 'enemies' in snapshot:
                    for enemy in snapshot['enemies']:
                        enemy_data = enemy.copy()
                        enemy_data['timestamp'] = timestamp
                        enemy_data['session_id'] = sid
                        flattened['enemies'].append(enemy_data)
                
                # Extract environment data
                if 'environment' in snapshot:
                    env_data = snapshot['environment'].copy()
                    env_data['timestamp'] = timestamp
                    env_data['session_id'] = sid
                    flattened['environment'].append(env_data)
                    
                # Add any other entity types here
        
        # Sort each entity type by timestamp
        for entity_type in flattened:
            flattened[entity_type].sort(key=lambda x: x.get('timestamp', 0))
            
        self.flattened_data = dict(flattened)
        return self.flattened_data
    
    def detect_state_changes(self, entity_type: str, property_name: str, threshold: float = 0) -> List[Dict]:
        """
        Detect significant changes in entity state over time.
        
        Args:
            entity_type: Type of entity to analyze (e.g., 'player', 'enemies')
            property_name: Property to track changes for
            threshold: Minimum change to consider significant
            
        Returns:
            List of significant state changes
        """
        if not self.flattened_data or entity_type not in self.flattened_data:
            self.flatten_snapshots()
            
        if entity_type not in self.flattened_data:
            return []
            
        entities = self.flattened_data[entity_type]
        changes = []
        
        # Group by entity ID if needed
        if entity_type == 'enemies':
            # Group by enemy ID
            by_id = defaultdict(list)
            for entry in entities:
                if 'id' in entry:
                    by_id[entry['id']].append(entry)
                    
            # Detect changes for each enemy
            for enemy_id, entries in by_id.items():
                entries.sort(key=lambda x: x.get('timestamp', 0))
                prev_value = None
                
                for entry in entries:
                    if property_name in entry:
                        current_value = entry[property_name]
                        
                        if prev_value is not None and abs(current_value - prev_value) > threshold:
                            changes.append({
                                'entity_type': entity_type,
                                'entity_id': enemy_id,
                                'property': property_name,
                                'timestamp': entry.get('timestamp', 0),
                                'previous_value': prev_value,
                                'new_value': current_value,
                                'session_id': entry.get('session_id')
                            })
                            
                        prev_value = current_value
        else:
            # For singleton entities like player or environment
            entities.sort(key=lambda x: x.get('timestamp', 0))
            prev_value = None
            
            for entry in entities:
                if property_name in entry:
                    current_value = entry[property_name]
                    
                    if prev_value is not None and abs(current_value - prev_value) > threshold:
                        changes.append({
                            'entity_type': entity_type,
                            'property': property_name,
                            'timestamp': entry.get('timestamp', 0),
                            'previous_value': prev_value,
                            'new_value': current_value,
                            'session_id': entry.get('session_id')
                        })
                        
                    prev_value = current_value
                    
        return changes
    
    def extract_tutorial_steps(self) -> List[Dict]:
        """
        Extract potential tutorial steps based on observed gameplay patterns.
        
        Returns:
            List of tutorial step definitions
        """
        tutorial_steps = []
        
        # Look for player movement
        movement_changes = self.detect_state_changes('player', 'position', threshold=10)
        if movement_changes:
            tutorial_steps.append({
                'id': 'movement',
                'message': 'Learn to move your character using WASD or arrow keys.',
                'highlight': 'PLAYER',
                'required_action': 'MOVE',
                'test_goal': 'Verify player movement mechanics'
            })
        
        # Look for wetness changes
        wetness_changes = self.detect_state_changes('player', 'wetness', threshold=5)
        if wetness_changes:
            tutorial_steps.append({
                'id': 'getting_wet',
                'message': 'Getting splashed by water increases your Wetness level.',
                'highlight': 'WATER_ENEMY',
                'required_action': 'GET_SPLASHED',
                'test_goal': 'Verify wetness attribute and enemy attack mechanics'
            })
        
        # Look for combat actions
        # (Would need to extract from log entries rather than snapshots)
        
        # Look for area transitions
        area_changes = self.detect_state_changes('player', 'current_area')
        if area_changes:
            tutorial_steps.append({
                'id': 'portal_intro',
                'message': 'Portals take you to new areas with different challenges.',
                'highlight': 'PORTAL',
                'required_action': 'SPACE',
                'test_goal': 'Verify portal transitions'
            })
        
        return tutorial_steps
    
    def generate_dev_tutorial(self, output_file: str = None) -> Dict:
        """
        Generate a comprehensive development tutorial based on analysis.
        
        Args:
            output_file: Optional file to write tutorial to
            
        Returns:
            Tutorial definition dict
        """
        # Ensure we have data to work with
        if not self.flattened_data:
            if not self.sessions:
                self.load_sessions(limit=3, most_recent=True)
            self.flatten_snapshots()
        
        # Extract steps from patterns
        steps = self.extract_tutorial_steps()
        
        # Add fixed steps for core mechanics
        dev_tutorial = {
            'id': 'dev_tutorial',
            'name': 'Development Tutorial',
            'description': 'Comprehensive tutorial covering all game mechanics',
            'steps': [
                {
                    'id': 'welcome',
                    'message': 'Welcome to the Development Tutorial. This tutorial validates all game mechanics.',
                    'highlight': None,
                    'required_action': 'SPACE',
                    'test_goal': 'Initialize tutorial environment'
                }
            ]
        }
        
        # Add data-derived steps
        dev_tutorial['steps'].extend(steps)
        
        # Add final summary step
        dev_tutorial['steps'].append({
            'id': 'summary',
            'message': 'Development tutorial complete. All mechanics validated.',
            'highlight': None,
            'required_action': 'SPACE',
            'test_goal': 'Verify tutorial completion handling'
        })
        
        # Write to file if requested
        if output_file:
            try:
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                with open(output_file, 'w') as f:
                    json.dump(dev_tutorial, f, indent=2)
            except Exception as e:
                print(f"Error writing tutorial to {output_file}: {e}")
        
        return dev_tutorial
    
    def find_optimal_progression(self) -> List[Dict]:
        """
        Analyze successful gameplay sessions to find optimal progression paths.
        
        Returns:
            List of key progression milestones
        """
        # Implementation would analyze successful playthroughs
        # and extract the common progression patterns
        pass


if __name__ == "__main__":
    # Example usage
    analyzer = SnapshotAnalyzer()
    print(f"Loading sessions...")
    num_sessions = analyzer.load_sessions(limit=5)
    print(f"Loaded {num_sessions} sessions.")
    
    # Process the first session if any were loaded
    if num_sessions > 0:
        first_session = list(analyzer.sessions.keys())[0]
        print(f"Processing session {first_session}...")
        
        num_snapshots = analyzer.load_session_snapshots(first_session)
        print(f"Loaded {num_snapshots} snapshots.")
        
        num_logs = analyzer.load_session_logs(first_session)
        print(f"Loaded {num_logs} log entries.")
        
        flattened = analyzer.flatten_snapshots(first_session)
        print(f"Flattened data for {len(flattened)} entity types.")
        
        # Generate tutorial
        tutorial = analyzer.generate_dev_tutorial("devtools/generated_tutorial.json")
        print(f"Generated tutorial with {len(tutorial['steps'])} steps.")
