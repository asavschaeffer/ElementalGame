"""
Recursive Log Comparison Framework for Elemental Game

This MVP module implements a recursive framework for comparing any two log entities,
whether they're snapshots, game sessions, or exports. The framework supports both:
1. Co-occurrence analysis - Ignores time, focuses on relationships between data points
2. Temporal analysis - Examines how relationships evolve over time

The "recursive ouroboros" approach allows any two logs to be compared, identifying
patterns regardless of their hierarchical level in the logging system.

Usage:
    from recursive_analyzer import RecursiveAnalyzer
    
    # Initialize
    analyzer = RecursiveAnalyzer()
    
    # Compare two snapshots
    patterns = analyzer.compare(snapshot1, snapshot2)
    
    # Compare two sessions
    session_patterns = analyzer.compare_sessions(session1_id, session2_id)
    
    # Search for patterns across log levels (snapshot ↔ session ↔ export)
    cross_level_patterns = analyzer.find_cross_level_patterns(snapshot_id, session_id)
"""

import os
import json
import time
from datetime import datetime
from collections import defaultdict, Counter
import numpy as np
from logger import game_logger


class RecursiveAnalyzer:
    """
    Core class implementing the recursive ouroboros framework for log analysis.
    
    This analyzer can compare any two log entities (snapshots, sessions, etc.),
    identifying both co-occurrence patterns and temporal relationships.
    """
    
    def __init__(self, temporal_mode=False):
        """
        Initialize the recursive analyzer.
        
        Args:
            temporal_mode (bool): If True, analyze temporal relationships;
                                  if False, focus on co-occurrence only
        """
        self.temporal_mode = temporal_mode
        self.pattern_cache = {}  # Cache for previously identified patterns
    
    def compare(self, entity1, entity2, level="snapshot"):
        """
        Compare any two log entities, finding patterns and relationships.
        
        This is the core recursive comparison function that can work with
        any level of log entity, from individual snapshots to entire sessions.
        
        Args:
            entity1 (dict): First log entity to compare
            entity2 (dict): Second log entity to compare
            level (str): Level of comparison (snapshot, session, export)
            
        Returns:
            dict: Dictionary of patterns found between the entities
        """
        if level == "snapshot":
            return self._compare_snapshots(entity1, entity2)
        elif level == "session":
            return self._compare_sessions(entity1, entity2)
        elif level == "export":
            return self._compare_exports(entity1, entity2)
        else:
            return self._generic_compare(entity1, entity2)
    
    def _compare_snapshots(self, snapshot1, snapshot2):
        """
        Compare two individual game state snapshots.
        
        Args:
            snapshot1 (dict): First snapshot
            snapshot2 (dict): Second snapshot
            
        Returns:
            dict: Patterns and changes detected between snapshots
        """
        # Extract all keys from both snapshots for comparison
        all_keys = set()
        self._extract_keys(snapshot1, all_keys)
        self._extract_keys(snapshot2, all_keys)
        
        # Find changed values
        changes = {}
        related_changes = defaultdict(list)
        
        for key in all_keys:
            value1 = self._get_nested_value(snapshot1, key)
            value2 = self._get_nested_value(snapshot2, key)
            
            if value1 != value2:
                changes[key] = (value1, value2)
        
        # Identify potentially related changes (co-occurring)
        change_keys = list(changes.keys())
        for i in range(len(change_keys)):
            for j in range(i+1, len(change_keys)):
                key_pair = (change_keys[i], change_keys[j])
                related_changes[key_pair].append({
                    'values1': changes[change_keys[i]],
                    'values2': changes[change_keys[j]]
                })
        
        # Calculate temporal distance if in temporal mode
        if self.temporal_mode and 'timestamp' in snapshot1 and 'timestamp' in snapshot2:
            try:
                ts1 = snapshot1['timestamp']
                ts2 = snapshot2['timestamp']
                
                # If timestamps are strings, try to get numerical difference
                if isinstance(ts1, str) and isinstance(ts2, str):
                    # Simple approach - just count the string difference length for MVP
                    time_diff = len(set(ts1).symmetric_difference(set(ts2)))
                else:
                    time_diff = abs(float(ts1) - float(ts2))
                    
                return {
                    'changes': changes,
                    'related_changes': dict(related_changes),
                    'time_difference': time_diff
                }
            except (ValueError, TypeError):
                # If conversion fails, just skip the time difference
                pass
        
        return {
            'changes': changes,
            'related_changes': dict(related_changes)
        }
    
    def _compare_sessions(self, session1_id, session2_id):
        """
        Compare two game sessions, finding patterns across multiple snapshots.
        
        Args:
            session1_id (str): ID of first session
            session2_id (str): ID of second session
            
        Returns:
            dict: Patterns detected between sessions
        """
        # Load session snapshots
        snapshots1 = self._load_session_snapshots(session1_id)
        snapshots2 = self._load_session_snapshots(session2_id)
        
        if not snapshots1 or not snapshots2:
            return {'error': 'Failed to load session snapshots'}
        
        # Binary search tree approach - compare from middle outward
        return self._binary_tree_compare(snapshots1, snapshots2)
    
    def _binary_tree_compare(self, snapshots1, snapshots2):
        """
        Compare two sets of snapshots using a binary search tree approach.
        
        This starts from the middle and works outward, which is more efficient
        for finding dominant patterns than linear comparison from the beginning.
        
        Args:
            snapshots1 (list): First list of snapshots
            snapshots2 (list): Second list of snapshots
            
        Returns:
            dict: Patterns detected between the snapshot sets
        """
        # Short-circuit if empty
        if not snapshots1 or not snapshots2:
            return {}
            
        # Find midpoints
        mid1 = len(snapshots1) // 2
        mid2 = len(snapshots2) // 2
        
        # Compare midpoints first
        mid_comparison = self._compare_snapshots(snapshots1[mid1], snapshots2[mid2])
        
        # Initialize results with midpoint comparison
        results = {
            'central_patterns': mid_comparison,
            'all_patterns': [mid_comparison],
            'pattern_counts': defaultdict(int)
        }
        
        # Count pattern occurrences
        for key_pair in mid_comparison.get('related_changes', {}):
            results['pattern_counts'][str(key_pair)] += 1
        
        # If we have more than one snapshot in each set, recursively compare halves
        if len(snapshots1) > 1 and len(snapshots2) > 1:
            # Compare left halves
            left_results = self._binary_tree_compare(snapshots1[:mid1], snapshots2[:mid2])
            
            # Compare right halves
            right_results = self._binary_tree_compare(snapshots1[mid1+1:], snapshots2[mid2+1:])
            
            # Merge results
            for result in [left_results, right_results]:
                # Add all patterns to the all_patterns list
                if 'all_patterns' in result:
                    results['all_patterns'].extend(result['all_patterns'])
                
                # Update pattern counts
                for key, count in result.get('pattern_counts', {}).items():
                    results['pattern_counts'][key] += count
        
        # Convert defaultdict to regular dict for serialization
        results['pattern_counts'] = dict(results['pattern_counts'])
        
        return results
    
    def _compare_exports(self, export1, export2):
        """Compare two analysis exports."""
        # Simplified implementation for MVP
        return self._generic_compare(export1, export2)
    
    def _generic_compare(self, data1, data2):
        """Generic comparison for any data structures."""
        # Simplified implementation for MVP
        if isinstance(data1, dict) and isinstance(data2, dict):
            return self._compare_dictionaries(data1, data2)
        elif isinstance(data1, list) and isinstance(data2, list):
            return self._compare_lists(data1, data2)
        else:
            return {'equal': data1 == data2, 'values': (data1, data2)}
    
    def _compare_dictionaries(self, dict1, dict2):
        """Compare two dictionaries recursively."""
        all_keys = set(dict1.keys()) | set(dict2.keys())
        results = {
            'common_keys': list(set(dict1.keys()) & set(dict2.keys())),
            'only_in_first': list(set(dict1.keys()) - set(dict2.keys())),
            'only_in_second': list(set(dict2.keys()) - set(dict1.keys())),
            'differences': {}
        }
        
        # Compare values for common keys
        for key in results['common_keys']:
            if dict1[key] != dict2[key]:
                # Recursively compare nested structures
                if isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                    results['differences'][key] = self._compare_dictionaries(dict1[key], dict2[key])
                elif isinstance(dict1[key], list) and isinstance(dict2[key], list):
                    results['differences'][key] = self._compare_lists(dict1[key], dict2[key])
                else:
                    results['differences'][key] = {'values': (dict1[key], dict2[key])}
        
        return results
    
    def _compare_lists(self, list1, list2):
        """Compare two lists recursively."""
        # Simplified implementation for MVP
        return {
            'length_diff': len(list1) - len(list2),
            'common_length': min(len(list1), len(list2)),
            'sample_differences': self._sample_list_differences(list1, list2)
        }
    
    def _sample_list_differences(self, list1, list2, sample_size=3):
        """Sample differences between lists to avoid excessive output."""
        common_length = min(len(list1), len(list2))
        sample_indices = []
        
        # Choose beginning, middle, and end if possible
        if common_length > 0:
            sample_indices.append(0)  # First element
        if common_length > 2:
            sample_indices.append(common_length // 2)  # Middle element
        if common_length > 1:
            sample_indices.append(common_length - 1)  # Last element
        
        # Collect sample differences
        samples = {}
        for idx in sample_indices:
            if list1[idx] != list2[idx]:
                if isinstance(list1[idx], dict) and isinstance(list2[idx], dict):
                    samples[idx] = self._compare_dictionaries(list1[idx], list2[idx])
                else:
                    samples[idx] = {'values': (list1[idx], list2[idx])}
        
        return samples
    
    def _extract_keys(self, obj, keys_set, prefix=''):
        """Extract all keys from a nested dictionary structure."""
        if not isinstance(obj, dict):
            return
            
        for key, value in obj.items():
            full_key = f"{prefix}.{key}" if prefix else key
            keys_set.add(full_key)
            
            if isinstance(value, dict):
                self._extract_keys(value, keys_set, full_key)
    
    def _get_nested_value(self, obj, key_path):
        """Get a value from a nested dictionary using a dot-separated path."""
        if not isinstance(obj, dict):
            return None
            
        parts = key_path.split('.')
        current = obj
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
                
        return current
    
    def _load_session_snapshots(self, session_id):
        """
        Load all snapshots for a given session.
        
        Args:
            session_id (str): ID of the session to load snapshots for
            
        Returns:
            list: List of snapshot dictionaries, or empty list if none found
        
        Raises:
            No exceptions raised, but error messages are logged
        """
        snapshots = []
        
        # Get the session directory
        sessions_dir = os.path.join(game_logger.log_directory, "sessions")
        session_dir = os.path.join(sessions_dir, session_id)
        
        if not os.path.exists(session_dir):
            print(f"Error: Session directory not found for '{session_id}'")
            return []
        
        # Load snapshots
        snapshots_dir = os.path.join(session_dir, "snapshots")
        if not os.path.exists(snapshots_dir):
            print(f"Error: No snapshots directory found for session '{session_id}'")
            return []
            
        snapshot_files = sorted([f for f in os.listdir(snapshots_dir) if f.endswith('.json')])
        
        if not snapshot_files:
            print(f"Error: No snapshot files found for session '{session_id}'")
            return []
            
        for snapshot_file in snapshot_files:
            try:
                with open(os.path.join(snapshots_dir, snapshot_file), 'r') as f:
                    snapshot = json.load(f)
                    # Add timestamp from filename
                    timestamp = snapshot_file.replace('snapshot_', '').replace('.json', '')
                    snapshot['timestamp'] = timestamp
                    snapshots.append(snapshot)
            except json.JSONDecodeError as e:
                print(f"Error parsing snapshot {snapshot_file}: {e}")
            except Exception as e:
                print(f"Error loading snapshot {snapshot_file}: {e}")
        
        if not snapshots:
            print(f"Error: Failed to load any valid snapshots for session '{session_id}'")
            
        return snapshots
    
    def find_cross_level_patterns(self, entity1_id, entity2_id, level1="snapshot", level2="session"):
        """
        Find patterns across different log levels.
        
        This method demonstrates the power of the recursive framework by comparing
        entities at different hierarchical levels within the logging system.
        
        Args:
            entity1_id (str): ID of first entity
            entity2_id (str): ID of second entity
            level1 (str): Level of first entity (snapshot, session, export)
            level2 (str): Level of second entity (snapshot, session, export)
            
        Returns:
            dict: Patterns detected across different levels
        """
        # Load first entity
        entity1 = self._load_entity(entity1_id, level1)
        
        # Load second entity
        entity2 = self._load_entity(entity2_id, level2)
        
        if not entity1 or not entity2:
            return {'error': f"Failed to load entities: {level1}={entity1_id}, {level2}={entity2_id}"}
        
        # Perform the cross-level comparison
        return self._generic_compare(entity1, entity2)
    
    def _load_entity(self, entity_id, level):
        """Load an entity of the specified level."""
        if level == "snapshot":
            # Simplified for MVP - assumes snapshot is in the most recent session
            sessions_dir = os.path.join(game_logger.log_directory, "sessions")
            if os.path.exists(sessions_dir):
                sessions = sorted([s for s in os.listdir(sessions_dir) 
                                  if os.path.isdir(os.path.join(sessions_dir, s))])
                if sessions:
                    session_id = sessions[-1]
                    snapshots_dir = os.path.join(sessions_dir, session_id, "snapshots")
                    if os.path.exists(snapshots_dir):
                        try:
                            with open(os.path.join(snapshots_dir, f"snapshot_{entity_id}.json"), 'r') as f:
                                return json.load(f)
                        except Exception as e:
                            print(f"Error loading snapshot: {e}")
        elif level == "session":
            return {'snapshots': self._load_session_snapshots(entity_id)}
        elif level == "export":
            exports_dir = os.path.join(game_logger.log_directory, "exports")
            if os.path.exists(exports_dir):
                try:
                    with open(os.path.join(exports_dir, entity_id), 'r') as f:
                        return json.load(f)
                except Exception as e:
                    print(f"Error loading export: {e}")
        
        return None


# Simple demonstration
if __name__ == "__main__":
    analyzer = RecursiveAnalyzer()
    print("Recursive Analyzer initialized. Ready for comparing game logs at any level.")
