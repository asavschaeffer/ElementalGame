"""
Advanced Analytics Module for Elemental Game

This module implements sophisticated pattern recognition and temporal analysis
for game logs, inspired by the concept of the "recursive ouroboros" - finding
patterns that feed back into themselves across multiple snapshots of game state.

Key features:
1. Temporal Difference Analysis - Compare snapshots across time to detect changes
2. Relationship Pattern Recognition - Find correlations between game state variables
3. Memory-Efficient Processing - Discard "dust" (unchanging data) while maintaining references
4. Narrative Interpretation - Transform raw data patterns into player-readable insights

Usage:
    from advanced_analytics import TemporalPatternAnalyzer
    
    # Initialize the analyzer with session data
    analyzer = TemporalPatternAnalyzer(session_id)
    
    # Find related data pairs across snapshots
    relationships = analyzer.find_related_duples()
    
    # Get narrative interpretation
    story = analyzer.generate_gameplay_narrative()
"""

import os
import json
import time
from datetime import datetime
from collections import defaultdict, Counter
import numpy as np
from logger import game_logger

class TemporalPatternAnalyzer:
    """Analyzes temporal patterns across game snapshots."""
    
    def __init__(self, session_id=None):
        """
        Initialize the analyzer with session data.
        
        Args:
            session_id (str): Session ID to analyze (uses most recent if None)
        """
        self.session_id = session_id
        self.snapshots = []
        self.events = []
        self.duples = {}  # Connected data pairs
        self.pattern_counts = Counter()  # Count pattern occurrences
        
        # Load session data
        self._load_session_data()
    
    def _load_session_data(self):
        """Load snapshot and event data for the specified session."""
        # Get session if not provided
        if not self.session_id:
            sessions_dir = os.path.join(game_logger.log_directory, "sessions")
            if os.path.exists(sessions_dir):
                sessions = sorted([s for s in os.listdir(sessions_dir) if os.path.isdir(os.path.join(sessions_dir, s))])
                if sessions:
                    self.session_id = sessions[-1]  # Use most recent
        
        if not self.session_id:
            print("No game sessions found.")
            return
        
        # Get the session directory
        sessions_dir = os.path.join(game_logger.log_directory, "sessions")
        session_dir = os.path.join(sessions_dir, self.session_id)
        
        if not os.path.exists(session_dir):
            print(f"Session directory not found: {session_dir}")
            return
        
        # Load snapshots
        snapshots_dir = os.path.join(session_dir, "snapshots")
        if os.path.exists(snapshots_dir):
            snapshot_files = sorted([f for f in os.listdir(snapshots_dir) if f.endswith('.json')])
            for snapshot_file in snapshot_files:
                try:
                    with open(os.path.join(snapshots_dir, snapshot_file), 'r') as f:
                        snapshot = json.load(f)
                        # Add timestamp from filename
                        timestamp = snapshot_file.replace('snapshot_', '').replace('.json', '')
                        snapshot['_timestamp'] = timestamp
                        self.snapshots.append(snapshot)
                except Exception as e:
                    print(f"Error loading snapshot {snapshot_file}: {e}")
        
        # Load events
        events_dir = os.path.join(session_dir, "events")
        if os.path.exists(events_dir):
            event_files = sorted([f for f in os.listdir(events_dir) if f.endswith('.json')])
            for event_file in event_files:
                try:
                    with open(os.path.join(events_dir, event_file), 'r') as f:
                        event = json.load(f)
                        self.events.append(event)
                except Exception as e:
                    print(f"Error loading event {event_file}: {e}")
    
    def find_related_duples(self, min_occurrences=2):
        """
        Find related data pairs (duples) across snapshots.
        
        This method identifies pairs of data points that change together
        across multiple snapshots, ignoring "dust" (unchanging data).
        
        Args:
            min_occurrences (int): Minimum number of occurrences to consider a pattern
            
        Returns:
            dict: Dictionary of related data pairs and their occurrence counts
        """
        if not self.snapshots:
            print("No snapshots available for analysis.")
            return {}
        
        # Track value changes across snapshots
        value_changes = defaultdict(list)
        
        # Process snapshots in sequence, tracking changes
        for i in range(1, len(self.snapshots)):
            prev = self.snapshots[i-1]
            curr = self.snapshots[i]
            
            changes = self._extract_changes(prev, curr)
            
            # Record all pairs of changing values
            change_keys = list(changes.keys())
            for j in range(len(change_keys)):
                for k in range(j+1, len(change_keys)):
                    key1 = change_keys[j]
                    key2 = change_keys[k]
                    
                    # Create a duple identifier
                    duple_id = f"{key1}:{key2}"
                    
                    # Record the timestamp and values
                    value_changes[duple_id].append({
                        'timestamp': curr.get('_timestamp', i),
                        key1: changes[key1],
                        key2: changes[key2]
                    })
        
        # Filter to duples that occur multiple times
        self.duples = {k: v for k, v in value_changes.items() if len(v) >= min_occurrences}
        
        # Count pattern occurrences
        for duple_id, occurrences in self.duples.items():
            self.pattern_counts[duple_id] = len(occurrences)
        
        return self.duples
    
    def _extract_changes(self, prev_snapshot, curr_snapshot, prefix=''):
        """
        Extract changes between two snapshots, recursively traversing nested structures.
        
        Args:
            prev_snapshot (dict): Previous snapshot
            curr_snapshot (dict): Current snapshot
            prefix (str): Path prefix for nested keys
            
        Returns:
            dict: Dictionary of changed values
        """
        changes = {}
        
        # Handle the case where snapshots might be different types
        if not isinstance(prev_snapshot, dict) or not isinstance(curr_snapshot, dict):
            if prev_snapshot != curr_snapshot:
                return {prefix.rstrip('.'): (prev_snapshot, curr_snapshot)}
            return {}
        
        # Compare all keys in current snapshot
        for key, curr_value in curr_snapshot.items():
            # Skip metadata keys
            if key.startswith('_'):
                continue
                
            path = f"{prefix}{key}"
            
            if key not in prev_snapshot:
                # New key
                changes[path] = (None, curr_value)
            elif isinstance(curr_value, dict) and isinstance(prev_snapshot[key], dict):
                # Recursively check nested dictionaries
                nested_changes = self._extract_changes(
                    prev_snapshot[key], curr_value, f"{path}."
                )
                changes.update(nested_changes)
            elif isinstance(curr_value, list) and isinstance(prev_snapshot[key], list):
                # For lists, just check if they're different
                if curr_value != prev_snapshot[key]:
                    changes[path] = (prev_snapshot[key], curr_value)
            elif curr_value != prev_snapshot[key]:
                # Simple value change
                changes[path] = (prev_snapshot[key], curr_value)
        
        return changes
    
    def find_significant_patterns(self, top_n=5):
        """
        Find the most significant patterns in the game data.
        
        Args:
            top_n (int): Number of top patterns to return
            
        Returns:
            list: List of (pattern, count) tuples
        """
        if not self.pattern_counts:
            self.find_related_duples()
        
        # Get the top N patterns by occurrence count
        return self.pattern_counts.most_common(top_n)
    
    def analyze_elemental_interactions(self):
        """
        Analyze elemental interactions specific to the game mechanics.
        
        This method specifically looks for patterns related to:
        - Wetness levels affecting fire resistance
        - Lava damage reduction based on wetness
        - Obsidian armor formation conditions
        
        Returns:
            dict: Analysis results
        """
        results = {
            'wetness_fire_resistance': {},
            'lava_damage_reduction': {},
            'obsidian_formation': {},
        }
        
        # Extract relevant data from snapshots
        wetness_values = []
        fire_resistance_values = []
        health_values = []
        timestamps = []
        
        for snapshot in self.snapshots:
            if 'player' in snapshot:
                player = snapshot['player']
                timestamp = snapshot.get('_timestamp', 0)
                
                if 'wetness' in player and 'fire_resistance' in player:
                    wetness_values.append(player['wetness'])
                    fire_resistance_values.append(player['fire_resistance'])
                    if 'health' in player:
                        health_values.append(player['health'])
                    timestamps.append(timestamp)
        
        # Analyze wetness to fire resistance relationship
        if len(wetness_values) > 5 and len(fire_resistance_values) > 5:
            # Calculate correlation
            correlation = np.corrcoef(wetness_values, fire_resistance_values)[0, 1]
            results['wetness_fire_resistance']['correlation'] = float(correlation)
            
            # Determine if there's a clear relationship
            if correlation > 0.7:
                results['wetness_fire_resistance']['relationship'] = 'strong_positive'
            elif correlation > 0.4:
                results['wetness_fire_resistance']['relationship'] = 'positive'
            elif correlation < -0.7:
                results['wetness_fire_resistance']['relationship'] = 'strong_negative'
            elif correlation < -0.4:
                results['wetness_fire_resistance']['relationship'] = 'negative'
            else:
                results['wetness_fire_resistance']['relationship'] = 'weak'
        
        # Extract lava damage events
        lava_damage_events = []
        for event in self.events:
            if event.get('event_type') == 'PLAYER_DAMAGED':
                data = event.get('data', {})
                if data.get('source') == 'LAVA':
                    lava_damage_events.append({
                        'timestamp': event.get('timestamp', 0),
                        'damage': data.get('amount', 0)
                    })
        
        # Match lava damage to player wetness at the time
        if lava_damage_events and wetness_values:
            damage_wetness_pairs = []
            
            for damage_event in lava_damage_events:
                event_time = float(damage_event['timestamp'])
                
                # Find the closest snapshot
                closest_idx = 0
                for i, time_str in enumerate(timestamps):
                    if float(time_str) <= event_time:
                        closest_idx = i
                
                if closest_idx < len(wetness_values):
                    damage_wetness_pairs.append((
                        damage_event['damage'],
                        wetness_values[closest_idx]
                    ))
            
            # Analyze relationship between wetness and damage
            if damage_wetness_pairs:
                damages = [p[0] for p in damage_wetness_pairs]
                wetnesses = [p[1] for p in damage_wetness_pairs]
                
                if len(damages) > 1:
                    # Calculate correlation
                    correlation = np.corrcoef(wetnesses, damages)[0, 1]
                    results['lava_damage_reduction']['correlation'] = float(correlation)
                    
                    # Check for damage reduction with higher wetness
                    results['lava_damage_reduction']['average_damage'] = sum(damages) / len(damages)
                    
                    # Categorize wetness into low/high and check damage difference
                    median_wetness = np.median(wetnesses)
                    high_wetness_damage = [d for w, d in damage_wetness_pairs if w > median_wetness]
                    low_wetness_damage = [d for w, d in damage_wetness_pairs if w <= median_wetness]
                    
                    if high_wetness_damage and low_wetness_damage:
                        high_avg = sum(high_wetness_damage) / len(high_wetness_damage)
                        low_avg = sum(low_wetness_damage) / len(low_wetness_damage)
                        
                        results['lava_damage_reduction']['high_wetness_damage_avg'] = high_avg
                        results['lava_damage_reduction']['low_wetness_damage_avg'] = low_avg
                        results['lava_damage_reduction']['damage_reduction_pct'] = (
                            (low_avg - high_avg) / low_avg * 100 if low_avg > 0 else 0
                        )
        
        return results
    
    def generate_gameplay_narrative(self):
        """
        Generate a narrative description of the player's gameplay experience.
        
        Returns:
            str: Narrative text describing the gameplay experience
        """
        if not self.snapshots:
            return "No gameplay data available for analysis."
        
        # Analyze elemental interactions
        elemental_analysis = self.analyze_elemental_interactions()
        
        # Extract key gameplay events
        areas_visited = set()
        for snapshot in self.snapshots:
            if 'environment' in snapshot and 'current_area' in snapshot['environment']:
                areas_visited.add(snapshot['environment']['current_area'])
        
        # Build the narrative
        narrative = [
            "# Your Elemental Journey",
            "",
            "## The Path You've Taken"
        ]
        
        # Describe areas visited
        area_descriptions = {
            'BEACH': "You began your journey on the Beach, where water enemies tested your resilience.",
            'FOREST': "The Forest provided a brief respite from elemental challenges.",
            'VOLCANO': "In the Volcano, you faced the searing heat of lava creatures.",
            'ABYSS': "You ventured into the Abyss, the ultimate challenge requiring obsidian armor."
        }
        
        for area in ['BEACH', 'FOREST', 'VOLCANO', 'ABYSS']:
            if area in areas_visited:
                narrative.append(f"- {area_descriptions.get(area, f'You visited the {area}.')}")
        
        narrative.append("")
        narrative.append("## Elemental Mastery")
        
        # Describe wetness and fire resistance relationship
        wetness_fire = elemental_analysis.get('wetness_fire_resistance', {})
        relationship = wetness_fire.get('relationship', '')
        
        if relationship == 'strong_positive':
            narrative.append(
                "- You've mastered the relationship between water and fire: your wetness "
                "significantly increased your fire resistance."
            )
        elif relationship == 'positive':
            narrative.append(
                "- You've begun to understand how water affects fire: increasing your wetness "
                "provided some protection against fire damage."
            )
        elif relationship in ['negative', 'strong_negative']:
            narrative.append(
                "- You seem to have struggled with balancing water and fire elements: "
                "your fire resistance didn't improve with wetness as expected."
            )
        
        # Describe lava damage reduction
        lava_reduction = elemental_analysis.get('lava_damage_reduction', {})
        if 'damage_reduction_pct' in lava_reduction:
            reduction = lava_reduction['damage_reduction_pct']
            if reduction > 70:
                narrative.append(
                    f"- You expertly used water to counter fire: when wet, you reduced lava damage by {reduction:.1f}%!"
                )
            elif reduction > 30:
                narrative.append(
                    f"- You discovered that water provides protection: wetness reduced lava damage by {reduction:.1f}%."
                )
            elif reduction > 0:
                narrative.append(
                    f"- You began to see how water affects fire: wetness reduced lava damage by {reduction:.1f}%."
                )
        
        # Look for obsidian armor formation
        if 'VOLCANO' in areas_visited and 'ABYSS' in areas_visited:
            narrative.append(
                "- Your journey through fire while properly protected by water allowed the "
                "formation of obsidian armor, enabling you to face the Abyss."
            )
        
        # Add pattern insights
        narrative.append("")
        narrative.append("## Gameplay Patterns")
        
        top_patterns = self.find_significant_patterns(3)
        if top_patterns:
            for pattern, count in top_patterns:
                parts = pattern.split(':')
                if len(parts) >= 2:
                    key1, key2 = parts[0], parts[1]
                    narrative.append(f"- You frequently connected {key1.split('.')[-1]} with {key2.split('.')[-1]} ({count} times)")
        else:
            narrative.append("- No significant recurring patterns detected in your gameplay.")
        
        return "\n".join(narrative)


# Example usage
if __name__ == "__main__":
    analyzer = TemporalPatternAnalyzer()
    print(analyzer.generate_gameplay_narrative())
