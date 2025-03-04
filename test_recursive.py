"""
Test script for the Recursive Ouroboros Framework
"""

import os
import json
import shutil
from datetime import datetime
from recursive_analyzer import RecursiveAnalyzer
from logger import game_logger

def create_test_snapshot(session_dir, name, data):
    """Create a test snapshot file in the specified session directory"""
    snapshots_dir = os.path.join(session_dir, "snapshots")
    os.makedirs(snapshots_dir, exist_ok=True)
    
    snapshot_path = os.path.join(snapshots_dir, f"snapshot_{name}.json")
    with open(snapshot_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    return snapshot_path

def create_test_session(session_id, snapshots):
    """Create a test session with the specified snapshots"""
    sessions_dir = os.path.join(game_logger.log_directory, "sessions")
    os.makedirs(sessions_dir, exist_ok=True)
    
    session_dir = os.path.join(sessions_dir, session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    # Create manifest.json
    manifest = {
        "start_time": datetime.now().timestamp(),
        "session_id": session_id
    }
    
    with open(os.path.join(session_dir, "manifest.json"), 'w') as f:
        json.dump(manifest, f, indent=2)
    
    # Create snapshots
    for snapshot_name, snapshot_data in snapshots.items():
        create_test_snapshot(session_dir, snapshot_name, snapshot_data)
    
    return session_dir

def setup_test_environment():
    """Set up test environment with sample sessions and snapshots"""
    print("\n===== SETTING UP TEST ENVIRONMENT =====\n")
    
    # Create test exports directory
    exports_dir = os.path.join('logs', 'exports')
    os.makedirs(exports_dir, exist_ok=True)
    
    # Create test session 1: Beach area
    beach_session_id = "test_beach_session"
    
    beach_snapshots = {
        "beach_t1": {
            "snapshot_time": "20250304_021500",
            "timestamp": "20250304_021500",
            "snapshot_data": {
                "player": {
                    "health": 100,
                    "wetness": 50,
                    "position": {"x": 300, "y": 200},
                    "inventory": ["health_potion", "map"]
                },
                "environment": {
                    "current_area": "BEACH",
                    "water_present": True,
                    "lava_present": False,
                    "enemies": 3
                },
                "enemies": {
                    "water_splasher_1": {"health": 30, "position": {"x": 350, "y": 250}},
                    "water_splasher_2": {"health": 50, "position": {"x": 400, "y": 300}}
                }
            }
        },
        "beach_t2": {
            "snapshot_time": "20250304_021501",
            "timestamp": "20250304_021501",
            "snapshot_data": {
                "player": {
                    "health": 95,
                    "wetness": 70,
                    "position": {"x": 310, "y": 210},
                    "inventory": ["health_potion", "map"]
                },
                "environment": {
                    "current_area": "BEACH",
                    "water_present": True,
                    "lava_present": False,
                    "enemies": 2
                },
                "enemies": {
                    "water_splasher_1": {"health": 0, "position": {"x": 350, "y": 250}},
                    "water_splasher_2": {"health": 50, "position": {"x": 400, "y": 300}}
                }
            }
        }
    }
    
    # Create test session 2: Volcano area
    volcano_session_id = "test_volcano_session"
    
    volcano_snapshots = {
        "volcano_t1": {
            "snapshot_time": "20250304_021600",
            "timestamp": "20250304_021600",
            "snapshot_data": {
                "player": {
                    "health": 90,
                    "wetness": 80,
                    "position": {"x": 500, "y": 300},
                    "inventory": ["health_potion", "map", "water_flask"]
                },
                "environment": {
                    "current_area": "VOLCANO",
                    "water_present": False,
                    "lava_present": True,
                    "enemies": 2
                },
                "enemies": {
                    "lava_sprite_1": {"health": 100, "position": {"x": 550, "y": 350}},
                    "lava_sprite_2": {"health": 120, "position": {"x": 600, "y": 400}}
                }
            }
        },
        "volcano_t2": {
            "snapshot_time": "20250304_021601",
            "timestamp": "20250304_021601",
            "snapshot_data": {
                "player": {
                    "health": 50,
                    "wetness": 30,
                    "position": {"x": 520, "y": 310},
                    "armor": "obsidian",
                    "inventory": ["health_potion", "map", "water_flask"]
                },
                "environment": {
                    "current_area": "VOLCANO",
                    "water_present": False,
                    "lava_present": True,
                    "enemies": 1
                },
                "enemies": {
                    "lava_sprite_1": {"health": 0, "position": {"x": 550, "y": 350}},
                    "lava_sprite_2": {"health": 120, "position": {"x": 600, "y": 400}}
                }
            }
        }
    }
    
    # Create the test sessions
    create_test_session(beach_session_id, beach_snapshots)
    create_test_session(volcano_session_id, volcano_snapshots)
    
    print(f"Created test session: {beach_session_id}")
    print(f"Created test session: {volcano_session_id}")
    
    return beach_session_id, volcano_session_id

def cleanup_test_environment(session_ids):
    """Clean up test sessions after testing"""
    print("\n===== CLEANING UP TEST ENVIRONMENT =====\n")
    
    sessions_dir = os.path.join(game_logger.log_directory, "sessions")
    
    for session_id in session_ids:
        session_dir = os.path.join(sessions_dir, session_id)
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir)
            print(f"Removed test session: {session_id}")

def run_demonstrations():
    """Run the recursive framework demonstrations"""
    # Set up the test environment
    beach_session_id, volcano_session_id = setup_test_environment()
    
    try:
        print("\n===== RECURSIVE OUROBOROS FRAMEWORK DEMO =====\n")
        
        # Initialize analyzers for different modes
        analyzer_cooccurrence = RecursiveAnalyzer(temporal_mode=False)
        analyzer_temporal = RecursiveAnalyzer(temporal_mode=True)
        
        # 1. Comparing individual snapshots
        print("1. COMPARING INDIVIDUAL SNAPSHOTS")
        print("----------------------------------")
        
        # Load snapshots from the beach session
        sessions_dir = os.path.join(game_logger.log_directory, "sessions")
        beach_session_dir = os.path.join(sessions_dir, beach_session_id)
        snapshots_dir = os.path.join(beach_session_dir, "snapshots")
        
        with open(os.path.join(snapshots_dir, "snapshot_beach_t1.json"), 'r') as f:
            beach_t1 = json.load(f)
        
        with open(os.path.join(snapshots_dir, "snapshot_beach_t2.json"), 'r') as f:
            beach_t2 = json.load(f)
        
        # Compare beach snapshots
        beach_comparison = analyzer_cooccurrence.compare(beach_t1, beach_t2)
        
        print("Beach Snapshot Comparison (Co-occurrence):")
        print(f"- Found {len(beach_comparison['changes'])} changed values")
        print(f"- Found {len(beach_comparison['related_changes'])} related change pairs")
        
        print("\nExample changes:")
        for key, (old_val, new_val) in list(beach_comparison['changes'].items())[:3]:
            print(f"  {key}: {old_val} -> {new_val}")
        
        # 2. Comparing beach vs volcano snapshots
        print("\n2. COMPARING BEACH VS VOLCANO SNAPSHOTS")
        print("---------------------------------------")
        
        # Load a snapshot from the volcano session
        volcano_session_dir = os.path.join(sessions_dir, volcano_session_id)
        volcano_snapshots_dir = os.path.join(volcano_session_dir, "snapshots")
        
        with open(os.path.join(volcano_snapshots_dir, "snapshot_volcano_t1.json"), 'r') as f:
            volcano_t1 = json.load(f)
        
        # Compare beach and volcano snapshots
        area_comparison = analyzer_cooccurrence.compare(beach_t1, volcano_t1)
        
        print("Beach vs Volcano Comparison:")
        print(f"- Found {len(area_comparison['changes'])} changed values")
        print(f"- Found {len(area_comparison['related_changes'])} related change pairs")
        
        print("\nTop changes:")
        for key, (old_val, new_val) in list(area_comparison['changes'].items())[:2]:
            if 'current_area' in key or 'lava_present' in key:
                print(f"  {key}: {old_val} -> {new_val}")
        
        # 3. Binary tree session comparison
        print("\n3. BINARY TREE SESSION COMPARISON")
        print("---------------------------------")
        
        session_comparison = analyzer_cooccurrence.compare(beach_session_id, volcano_session_id, level='session')
        
        print("Beach Session vs Volcano Session (Binary Tree):")
        if 'central_patterns' in session_comparison and 'changes' in session_comparison['central_patterns']:
            change_count = len(session_comparison['central_patterns']['changes'])
            print(f"- Central comparison has {change_count} changes")
        
        if 'pattern_counts' in session_comparison:
            pattern_count = len(session_comparison['pattern_counts'])
            print(f"- Total patterns found: {pattern_count}")
            
            print("\nTop recurring patterns:")
            sorted_patterns = sorted(
                session_comparison['pattern_counts'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]
            
            for pattern, count in sorted_patterns:
                # Clean up pattern string for display
                clean_pattern = pattern.strip("'()[]{}").replace("'", "")
                print(f"  {clean_pattern}: {count} occurrences")
        
        # 4. Temporal vs co-occurrence analysis
        print("\n4. TEMPORAL VS CO-OCCURRENCE ANALYSIS")
        print("------------------------------------")
        
        # Compare the same snapshots but with temporal analysis
        temporal_comparison = analyzer_temporal.compare(beach_t1, beach_t2)
        
        print("Temporal Analysis Additional Insights:")
        if 'time_difference' in temporal_comparison:
            print(f"- Time between snapshots: {temporal_comparison['time_difference']}")
        
        print("\n===== DEMO COMPLETE =====")
        print("This demonstrates how the recursive framework can compare any game logs")
        print("at different levels, using both co-occurrence and temporal analysis approaches.")
    
    finally:
        # Clean up test environment
        cleanup_test_environment([beach_session_id, volcano_session_id])

if __name__ == "__main__":
    run_demonstrations()
