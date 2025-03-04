"""
Log Analysis and Visualization Tool for Elemental Game

This script provides utilities to analyze game logs and create visual representations
of game state changes over time using calculus concepts as an analogy.

Key Features:
1. Session Management:
   - List, browse, and select game sessions for analysis
   - Organize and categorize session data
   - Import legacy logs into the new session structure

2. Snapshot Analysis:
   - Extract game state data from periodic snapshots
   - Track changes in player attributes, enemy interactions, and environment
   - Create time-series visualizations of game states

3. Performance Metrics:
   - Calculate rates of change for any game variable
   - Identify patterns and correlations across gameplay
   - Generate derivative-based analysis for deeper insights

4. Data Visualization:
   - Create plots of game state changes
   - Compare multiple sessions or metrics
   - Visual representation of game balance and difficulty

Usage:
    python analyze_logs.py --list-sessions
    python analyze_logs.py --session [id] --metric player_health --derivative
    python analyze_logs.py --organize-legacy-logs
    python analyze_logs.py --list-snapshots --session [id]

Author: Codeium/Cascade Team
Date: March 2025
"""

import os
import sys
import argparse
import json
from datetime import datetime
from logger import game_logger
from visualization import GameStateVisualizer
import shutil

def main():
    parser = argparse.ArgumentParser(description="Analyze and visualize game logs")
    parser.add_argument('--session', '-s', help='Session ID to analyze (uses most recent if not specified)')
    parser.add_argument('--metric', '-m', default='player_health', 
                        help='Metric to analyze (player_health, enemy_count, player_x, etc.)')
    parser.add_argument('--derivative', '-d', action='store_true', 
                        help='Analyze rate of change of the metric')
    parser.add_argument('--window', '-w', type=int, default=3,
                        help='Window size for rate of change calculation')
    parser.add_argument('--analogy', '-a', action='store_true',
                        help='Show the calculus analogy visualization')
    parser.add_argument('--list-sessions', '-l', action='store_true',
                        help='List all available game sessions')
    parser.add_argument('--list-snapshots', action='store_true',
                        help='List all snapshots for a session')
    parser.add_argument('--list-duplets', action='store_true',
                        help='List all duplets for a session')
    parser.add_argument('--analyze-duplet', type=str,
                        help='Analyze a specific duplet by timestamp')
    parser.add_argument('--organize-legacy-logs', action='store_true',
                        help='Organize legacy logs into the new directory structure')
    parser.add_argument('--eat-logs', action='store_true',
                        help='Compress and analyze all logs into a pattern summary')
    parser.add_argument('--detect-patterns', action='store_true',
                        help='Detect patterns in player health and damage sources')
    
    args = parser.parse_args()
    
    # Create the logs directory if it doesn't exist
    os.makedirs('logs/exports', exist_ok=True)
    
    # Organize legacy logs
    if args.organize_legacy_logs:
        organize_legacy_logs()
        return
    
    # List sessions
    if args.list_sessions:
        sessions = list_all_sessions()
        if not sessions:
            print("No game sessions found.")
            return
            
    # Get session id
    session_id = args.session
    if not session_id:
        sessions = list_all_sessions()
        if not sessions:
            print("No game sessions found. Please run the game first.")
            return
        session_id = sessions[-1]  # Use most recent
        print(f"Using most recent session: {session_id}")
        
    # List snapshots
    if args.list_snapshots:
        list_session_snapshots(session_id)
        return
        
    # List duplets
    if args.list_duplets:
        list_session_duplets(session_id)
        return
        
    # Analyze a specific duplet
    if args.analyze_duplet:
        analyze_duplet(session_id, args.analyze_duplet)
        return
    
    # Show calculus analogy
    if args.analogy:
        print("Creating calculus analogy visualization...")
        filepath = game_logger.demonstrate_calculus_analogy()
        if filepath:
            print(f"Visualization saved to: {filepath}")
        else:
            print("Failed to create visualization. Check if matplotlib is installed.")
        return
    
    # Analyze rate of change
    if args.derivative:
        print(f"Analyzing rate of change for {args.metric}...")
        filepath = game_logger.visualize_rate_of_change(args.metric, session_id, args.window)
        if filepath:
            print(f"Analysis saved to: {filepath}")
        else:
            print("Failed to create visualization. Check if the metric exists in the logs.")
        return
        
    # Regular visualization
    print(f"Visualizing {args.metric} data...")
    filepath = game_logger.visualize_game_data(args.metric, session_id)
    if filepath:
        print(f"Visualization saved to: {filepath}")
    else:
        print("Failed to create visualization. Check if the metric exists in the logs.")

    # Eat logs command
    if args.eat_logs:
        print("Eating logs and detecting patterns...")
        generate_compressed_log_report()
        return
        
    # Detect patterns command
    if args.detect_patterns:
        detect_health_damage_patterns(args.session)
        return

def list_all_sessions():
    """List all available game sessions with metadata.
    
    This function lists all available game sessions, including both legacy sessions
    (without the 'session_' prefix) and new format sessions. It displays basic metadata
    about each session including start time and duration when available.
    
    Returns:
        list: List of session IDs
    """
    # Get the sessions directory
    sessions_dir = os.path.join(game_logger.log_directory, "sessions")
    
    if not os.path.exists(sessions_dir):
        print("No sessions directory found.")
        return []
        
    # List all session directories
    sessions = []
    for dirname in os.listdir(sessions_dir):
        session_dir = os.path.join(sessions_dir, dirname)
        if os.path.isdir(session_dir):
            sessions.append(dirname)
            
    if not sessions:
        print("No game sessions found.")
        return []
        
    # Sort sessions by timestamp embedded in the name
    sessions.sort()
    
    print(f"Found {len(sessions)} game sessions:")
    for i, session_id in enumerate(sessions):
        # Try to load manifest.json for metadata
        manifest_path = os.path.join(sessions_dir, session_id, "manifest.json")
        start_time = "Unknown"
        duration = "Unknowns"
        
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                    start_time = manifest.get('start_time', 'Unknown')
                    session_duration = manifest.get('duration', None)
                    if session_duration:
                        duration = f"{session_duration}s"
            except:
                pass
                
        print(f"{i+1}. {session_id} - Started: {start_time}, Duration: {duration}")
        
    return sessions

def list_session_snapshots(session_id):
    """List all snapshots for a specific session with timestamps and contents.
    
    This function retrieves and displays detailed information about all snapshots
    captured during a game session. Snapshots represent periodic game state records
    taken at 1-second intervals, containing categorized data about player state,
    enemy interactions, and environmental conditions.
    
    The output includes:
    1. Total number of snapshots for the session
    2. Timestamp for each snapshot
    3. Categories of data captured (player, enemy, environment, etc.)
    4. Number of data points per category
    5. Total data points across all categories
    
    Args:
        session_id (str): The unique identifier for the game session
        
    Returns:
        None: Results are printed to the console
    """
    # Extract the timestamp part from the session_id to match with snapshot filenames
    # For both formats: "session_20250303_182838_12372" or "20250303_182838_12372"
    if session_id.startswith("session_"):
        timestamp_part = session_id[8:].split('_')[0:2]  # Get the date and time parts
    else:
        timestamp_part = session_id.split('_')[0:2]  # Get the date and time parts
        
    timestamp_prefix = "_".join(timestamp_part)
    
    # First check session-specific snapshots directory
    sessions_dir = os.path.join(game_logger.log_directory, "sessions")
    session_dir = os.path.join(sessions_dir, session_id)
    snapshots_dir = os.path.join(session_dir, "snapshots")
    
    snapshot_files = []
    
    # Check session-specific directory first
    if os.path.exists(snapshots_dir):
        for filename in os.listdir(snapshots_dir):
            if filename.startswith("snapshot_") and filename.endswith(".json"):
                snapshot_files.append(os.path.join(snapshots_dir, filename))
    
    # Then check legacy location (top-level logs directory)
    legacy_snapshots = []
    for filename in os.listdir(game_logger.log_directory):
        # Match snapshots by timestamp prefix
        if (filename.startswith(f"snapshot_{timestamp_prefix}") and 
            filename.endswith(".json")):
            legacy_snapshots.append(os.path.join(game_logger.log_directory, filename))
    
    # Add legacy snapshots if we don't have session-specific ones
    if not snapshot_files and legacy_snapshots:
        print(f"Using legacy snapshots from main logs directory for session {session_id}")
        snapshot_files = legacy_snapshots
    
    if not snapshot_files:
        print(f"No snapshots found for session {session_id}")
        return
    
    # Sort by timestamp
    snapshot_files.sort()
    
    snapshots = []
    for snapshot_file in snapshot_files:
        try:
            with open(snapshot_file, 'r') as f:
                snapshot = json.load(f)
                snapshots.append(snapshot)
        except Exception as e:
            print(f"Error loading snapshot {snapshot_file}: {str(e)}")
    
    if not snapshots:
        print(f"No valid snapshots found for session {session_id}")
        return
        
    print(f"Found {len(snapshots)} snapshots for session {session_id}:")
    for i, snapshot in enumerate(snapshots):
        timestamp = snapshot.get('snapshot_time', 'Unknown')
        categories = list(snapshot.get('snapshot_data', {}).keys())
        if not categories and 'snapshot_data' in snapshot:
            # Handle legacy format
            print(f"{i+1}. Snapshot {timestamp} (Legacy format)")
            continue
            
        category_counts = {cat: len(snapshot['snapshot_data'][cat]) for cat in categories}
        
        print(f"{i+1}. Snapshot {timestamp}")
        print(f"   Categories: {', '.join(categories)}")
        print(f"   Data Points: {sum(category_counts.values())}")
        for cat, count in category_counts.items():
            print(f"      - {cat}: {count} entries")
        print()

def list_session_duplets(session_id):
    """List all duplets for a specific session with timestamps and contents."""
    duplets = game_logger.get_session_duplets(session_id)
    
    if not duplets:
        print(f"No duplets found for session {session_id}")
        return
        
    print(f"Found {len(duplets)} duplets for session {session_id}:")
    for i, duplet in enumerate(duplets):
        timestamp = duplet.get('snapshot_time', 'Unknown')
        categories = duplet.get('categories', [])
        
        print(f"{i+1}. Duplet {timestamp}")
        print(f"   Snapshot: {os.path.basename(duplet.get('snapshot_file', 'Unknown'))}")
        print(f"   Log Chunk: {os.path.basename(duplet.get('log_chunk', 'Unknown'))}")
        print(f"   Categories: {', '.join(categories)}")
        print()

def analyze_duplet(session_id, timestamp):
    """Analyze a specific duplet by timestamp."""
    duplets = game_logger.get_session_duplets(session_id)
    
    # Find the matching duplet
    target_duplet = None
    for duplet in duplets:
        if duplet.get('snapshot_time') == timestamp:
            target_duplet = duplet
            break
            
    if not target_duplet:
        print(f"No duplet found with timestamp {timestamp}")
        return
        
    print(f"Analyzing duplet from {timestamp}:")
    
    # Load snapshot data
    snapshot_file = target_duplet.get('snapshot_file')
    if os.path.exists(snapshot_file):
        with open(snapshot_file, 'r') as f:
            snapshot_data = json.load(f)
            print(f"Snapshot contains {len(snapshot_data.get('snapshot_data', {}))} categories")
            
            # Extract and display key metrics
            categories = snapshot_data.get('snapshot_data', {})
            if 'player' in categories and categories['player']:
                player_data = categories['player'][0]['data']
                print(f"\nPlayer State:")
                print(f"  Health: {player_data.get('health', 'N/A')}/{player_data.get('max_health', 'N/A')}")
                print(f"  Position: {player_data.get('position', {}).get('x', 'N/A')}, {player_data.get('position', {}).get('y', 'N/A')}")
                print(f"  Wetness: {player_data.get('wetness', 'N/A')}")
                print(f"  Fire Resistance: {player_data.get('fire_resistance', 'N/A')}")
                print(f"  Obsidian Armor: {player_data.get('has_obsidian_armor', 'N/A')}")
                print(f"  Current Area: {player_data.get('current_area', 'N/A')}")
            
            # Count enemies by type
            if 'enemy_spawn' in categories:
                enemy_types = {}
                for entry in categories['enemy_spawn']:
                    enemy_type = entry['data'].get('type', 'unknown')
                    if enemy_type not in enemy_types:
                        enemy_types[enemy_type] = 0
                    enemy_types[enemy_type] += 1
                    
                print(f"\nEnemy Distribution:")
                for enemy_type, count in enemy_types.items():
                    print(f"  {enemy_type}: {count}")
            
            # Combat statistics
            if 'combat' in categories:
                combat_events = categories['combat']
                damage_dealt = sum(event['data'].get('actual_damage', 0) for event in combat_events 
                                  if event['data'].get('attacker') == 'player')
                damage_taken = sum(event['data'].get('actual_damage', 0) for event in combat_events 
                                  if event['data'].get('defender') == 'player')
                                  
                print(f"\nCombat Statistics:")
                print(f"  Total combat events: {len(combat_events)}")
                print(f"  Player damage dealt: {damage_dealt}")
                print(f"  Player damage taken: {damage_taken}")
    else:
        print(f"Snapshot file not found: {snapshot_file}")

def organize_legacy_logs():
    """Organize legacy logs into the new directory structure."""
    print("Organizing legacy logs into the new directory structure...")
    
    # Get the logs directory
    logs_dir = game_logger.log_directory
    
    # Find legacy log files
    log_files = [f for f in os.listdir(logs_dir) if f.endswith('.log') and os.path.isfile(os.path.join(logs_dir, f))]
    snapshot_files = [f for f in os.listdir(logs_dir) if f.startswith('snapshot_') and f.endswith('.json') and os.path.isfile(os.path.join(logs_dir, f))]
    
    # Group files by session
    session_files = {}
    
    # Group log files
    for log_file in log_files:
        # Extract session ID from filename
        if log_file.startswith('game_session_'):
            # New format
            session_id = log_file.replace('game_session_', '').replace('.log', '')
        elif log_file.startswith('game_'):
            # Old format
            session_id = log_file.replace('game_', '').replace('.log', '')
        else:
            continue
            
        if session_id not in session_files:
            session_files[session_id] = {'logs': [], 'snapshots': []}
        session_files[session_id]['logs'].append(log_file)
    
    # Group snapshot files
    for snapshot_file in snapshot_files:
        # Extract timestamp from filename
        timestamp = snapshot_file.replace('snapshot_', '').replace('.json', '')
        
        # Find matching session by timestamp prefix
        for session_id in session_files:
            if timestamp.startswith(session_id.split('_')[0]):
                session_files[session_id]['snapshots'].append(snapshot_file)
                break
    
    # Create new directory structure and move files
    for session_id, files in session_files.items():
        # Create session directory
        session_dir = os.path.join(logs_dir, 'sessions', session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        # Create subdirectories
        snapshots_dir = os.path.join(session_dir, 'snapshots')
        os.makedirs(snapshots_dir, exist_ok=True)
        
        # Move log files
        for log_file in files['logs']:
            src = os.path.join(logs_dir, log_file)
            dst = os.path.join(session_dir, 'game_log.log')
            try:
                shutil.copy2(src, dst)
                print(f"Copied {log_file} to {dst}")
            except Exception as e:
                print(f"Error copying {log_file}: {str(e)}")
        
        # Move snapshot files
        for snapshot_file in files['snapshots']:
            src = os.path.join(logs_dir, snapshot_file)
            dst = os.path.join(snapshots_dir, snapshot_file)
            try:
                shutil.copy2(src, dst)
                print(f"Copied {snapshot_file} to {dst}")
            except Exception as e:
                print(f"Error copying {snapshot_file}: {str(e)}")
                
        # Create manifest file
        manifest = {
            "session_id": session_id,
            "organized_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "log_files": files['logs'],
            "snapshot_files": files['snapshots'],
            "log_file": os.path.join(session_dir, 'game_log.log'),
            "directories": {
                "session": session_dir,
                "snapshots": snapshots_dir
            }
        }
        
        # Save manifest
        manifest_path = os.path.join(session_dir, 'manifest.json')
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
            
    print(f"Organized {len(session_files)} sessions into the new directory structure.")

def detect_health_damage_patterns(session_id=None):
    """
    Detects patterns in player health changes, focusing on damage sources.
    
    This MVP implementation analyzes log data to confirm whether water enemies
    are consistently causing health reduction, and quantifies this relationship.
    
    Args:
        session_id (str): Session ID to analyze (uses most recent if None)
        
    Returns:
        dict: Detected patterns with supporting statistics
    """
    print("Analyzing health damage patterns...")
    
    # Get session ID if not provided
    if not session_id:
        sessions = list_all_sessions()
        if not sessions:
            print("No game sessions found.")
            return None
        session_id = sessions[-1]  # Use most recent
    
    # Get session directory
    sessions_dir = os.path.join('logs', 'sessions')
    session_dir = os.path.join(sessions_dir, session_id)
    snapshots_dir = os.path.join(session_dir, 'snapshots')
    
    if not os.path.exists(snapshots_dir):
        print(f"No snapshots found for session {session_id}")
        return None
    
    # Get all snapshot files in chronological order
    snapshot_files = sorted([
        os.path.join(snapshots_dir, f)
        for f in os.listdir(snapshots_dir)
        if f.endswith('.json')
    ])
    
    if not snapshot_files:
        print("No snapshots found")
        return None
    
    # Initialize data structures
    player_health_timeline = []
    enemy_presence_timeline = []
    damage_events = []
    
    # Process each snapshot
    prev_health = None
    for snapshot_file in snapshot_files:
        try:
            with open(snapshot_file, 'r') as f:
                snapshot = json.load(f)
            
            # Extract timestamp
            timestamp = snapshot.get('timestamp', 0)
            
            # Extract player health if available
            if 'player' in snapshot and 'health' in snapshot['player']:
                current_health = snapshot['player']['health']
                
                # Record health point
                player_health_timeline.append({
                    'timestamp': timestamp,
                    'health': current_health
                })
                
                # Detect health reduction
                if prev_health is not None and current_health < prev_health:
                    # Check for enemy presence
                    water_enemies = 0
                    lava_enemies = 0
                    abyss_enemies = 0
                    
                    if 'active_enemies' in snapshot:
                        for enemy in snapshot['active_enemies']:
                            if 'type' in enemy:
                                if enemy['type'] == 'water':
                                    water_enemies += 1
                                elif enemy['type'] == 'lava':
                                    lava_enemies += 1
                                elif enemy['type'] == 'abyss':
                                    abyss_enemies += 1
                    
                    # Record damage event with context
                    damage_events.append({
                        'timestamp': timestamp,
                        'damage_amount': prev_health - current_health,
                        'from_health': prev_health,
                        'to_health': current_health,
                        'water_enemies': water_enemies,
                        'lava_enemies': lava_enemies,
                        'abyss_enemies': abyss_enemies,
                        'player_wetness': snapshot.get('player', {}).get('wetness', 0)
                    })
                
                prev_health = current_health
            
            # Record enemy presence
            enemy_presence = {
                'timestamp': timestamp,
                'water_enemies': 0,
                'lava_enemies': 0,
                'abyss_enemies': 0
            }
            
            if 'active_enemies' in snapshot:
                for enemy in snapshot['active_enemies']:
                    if 'type' in enemy:
                        if enemy['type'] == 'water':
                            enemy_presence['water_enemies'] += 1
                        elif enemy['type'] == 'lava':
                            enemy_presence['lava_enemies'] += 1
                        elif enemy['type'] == 'abyss':
                            enemy_presence['abyss_enemies'] += 1
            
            enemy_presence_timeline.append(enemy_presence)
            
        except Exception as e:
            print(f"Error processing snapshot {snapshot_file}: {e}")
    
    # Analyze damage correlation with enemy types
    damage_correlation = {
        'water': {'damage_events': 0, 'total_damage': 0, 'avg_damage': 0},
        'lava': {'damage_events': 0, 'total_damage': 0, 'avg_damage': 0},
        'abyss': {'damage_events': 0, 'total_damage': 0, 'avg_damage': 0},
        'unknown': {'damage_events': 0, 'total_damage': 0, 'avg_damage': 0}
    }
    
    # Analyze each damage event
    for event in damage_events:
        if event['water_enemies'] > 0 and event['lava_enemies'] == 0 and event['abyss_enemies'] == 0:
            # Only water enemies present
            damage_correlation['water']['damage_events'] += 1
            damage_correlation['water']['total_damage'] += event['damage_amount']
        elif event['lava_enemies'] > 0 and event['water_enemies'] == 0 and event['abyss_enemies'] == 0:
            # Only lava enemies present
            damage_correlation['lava']['damage_events'] += 1
            damage_correlation['lava']['total_damage'] += event['damage_amount']
        elif event['abyss_enemies'] > 0 and event['water_enemies'] == 0 and event['lava_enemies'] == 0:
            # Only abyss enemies present
            damage_correlation['abyss']['damage_events'] += 1
            damage_correlation['abyss']['total_damage'] += event['damage_amount']
        else:
            # Multiple enemy types or no enemies
            damage_correlation['unknown']['damage_events'] += 1
            damage_correlation['unknown']['total_damage'] += event['damage_amount']
    
    # Calculate averages
    for enemy_type in damage_correlation:
        if damage_correlation[enemy_type]['damage_events'] > 0:
            damage_correlation[enemy_type]['avg_damage'] = (
                damage_correlation[enemy_type]['total_damage'] / 
                damage_correlation[enemy_type]['damage_events']
            )
    
    # Build pattern detection results
    patterns = {
        'session_id': session_id,
        'player_health': {
            'initial': player_health_timeline[0]['health'] if player_health_timeline else None,
            'final': player_health_timeline[-1]['health'] if player_health_timeline else None,
            'lowest': min([p['health'] for p in player_health_timeline]) if player_health_timeline else None,
            'highest': max([p['health'] for p in player_health_timeline]) if player_health_timeline else None
        },
        'damage_events': len(damage_events),
        'damage_correlation': damage_correlation,
        'primary_damage_source': max(
            damage_correlation.items(),
            key=lambda x: x[1]['damage_events'] if x[1]['damage_events'] > 0 else -1
        )[0] if damage_events else None
    }
    
    # Calculate confidence in water splash pattern
    water_damage_events = damage_correlation['water']['damage_events']
    total_damage_events = sum(item['damage_events'] for item in damage_correlation.values())
    
    if total_damage_events > 0:
        patterns['water_damage_confidence'] = (water_damage_events / total_damage_events) * 100
    else:
        patterns['water_damage_confidence'] = 0
    
    # Output findings
    print("\nDamage Pattern Analysis Results:")
    print(f"Session ID: {session_id}")
    print(f"Total damage events detected: {len(damage_events)}")
    
    if patterns['primary_damage_source']:
        print(f"Primary damage source: {patterns['primary_damage_source']}")
        print(f"Confidence: {patterns['water_damage_confidence']:.1f}%")
        
        if patterns['primary_damage_source'] == 'water':
            print("\nPATTERN CONFIRMED: Water enemies consistently reduce player health")
            print(f"Average damage per water attack: {damage_correlation['water']['avg_damage']:.2f}")
        else:
            print(f"\nPrimary damage source is {patterns['primary_damage_source']}, not water")
    
    # Create a simple visualization of health over time
    try:
        import matplotlib.pyplot as plt
        
        if player_health_timeline:
            # Extract time and health values
            times = [(p['timestamp'] - player_health_timeline[0]['timestamp']) for p in player_health_timeline]
            health_values = [p['health'] for p in player_health_timeline]
            
            # Create the plot
            plt.figure(figsize=(12, 6))
            plt.plot(times, health_values, 'b-', linewidth=2)
            plt.title('Player Health Over Time')
            plt.xlabel('Time (seconds)')
            plt.ylabel('Health')
            plt.grid(True)
            
            # Mark damage events
            for event in damage_events:
                event_time = event['timestamp'] - player_health_timeline[0]['timestamp']
                plt.axvline(x=event_time, color='r', linestyle='--', alpha=0.5)
            
            # Save the plot
            output_dir = os.path.join('logs', 'exports')
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, f"{session_id}_health_pattern.png")
            plt.savefig(output_file)
            plt.close()
            
            print(f"Health pattern visualization saved to: {output_file}")
    except:
        print("Could not create visualization (matplotlib may not be installed)")
    
    # Save analysis results
    output_dir = os.path.join('logs', 'exports')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{session_id}_pattern_analysis.json")
    
    with open(output_file, 'w') as f:
        json.dump(patterns, f, indent=2)
    
    print(f"Analysis results saved to: {output_file}")
    
    return patterns

def generate_compressed_log_report(session_id=None):
    """
    Generates a comprehensive game analysis report from logs.
    
    This function analyzes game logs to extract key patterns and insights,
    including player performance, enemy interactions, and progression.
    
    Args:
        session_id (str): Session ID to analyze (uses most recent if None)
        
    Returns:
        str: Formatted report text with analysis findings
    """
    # Get session if not provided
    if not session_id:
        sessions = list_all_sessions()
        if not sessions:
            return "No game sessions found. Please play the game first."
        session_id = sessions[-1]  # Use most recent
    
    print(f"Analyzing session: {session_id}")
    
    # Get the session directory
    sessions_dir = os.path.join(game_logger.log_directory, "sessions")
    session_dir = os.path.join(sessions_dir, session_id)
    
    if not os.path.exists(session_dir):
        return f"Session directory not found: {session_dir}"
    
    # Load session data
    snapshots_dir = os.path.join(session_dir, "snapshots")
    events_dir = os.path.join(session_dir, "events")
    
    if not os.path.exists(snapshots_dir):
        return f"No snapshots found for session: {session_id}"
    
    # Collect all snapshot files
    snapshot_files = sorted([f for f in os.listdir(snapshots_dir) if f.endswith('.json')])
    
    if not snapshot_files:
        return f"No snapshot data found for session: {session_id}"
    
    # Collect event files if they exist
    event_files = []
    if os.path.exists(events_dir):
        event_files = sorted([f for f in os.listdir(events_dir) if f.endswith('.json')])
    
    # Load manifest for session metadata
    manifest_path = os.path.join(session_dir, "manifest.json")
    session_start_time = "Unknown"
    session_duration = "Unknown"
    
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
                session_start_time = manifest.get('start_time', 'Unknown')
                session_duration = manifest.get('duration', 'Unknown')
        except Exception as e:
            print(f"Error reading manifest: {e}")
    
    # Begin analysis
    player_data = {}
    enemy_data = {}
    environment_data = {}
    areas_visited = set()
    damage_sources = {}
    health_changes = []
    
    # Track player wetness and fire resistance
    wetness_values = []
    fire_resistance_values = []
    
    # Process snapshots
    for snapshot_file in snapshot_files:
        try:
            with open(os.path.join(snapshots_dir, snapshot_file), 'r') as f:
                snapshot = json.load(f)
                
                # Extract timestamp from filename (snapshot_TIMESTAMP.json)
                timestamp = snapshot_file.replace('snapshot_', '').replace('.json', '')
                
                # Process player data
                if 'player' in snapshot:
                    player = snapshot['player']
                    if 'health' in player:
                        health_changes.append((timestamp, player['health']))
                    
                    if 'wetness' in player:
                        wetness_values.append((timestamp, player['wetness']))
                    
                    if 'fire_resistance' in player:
                        fire_resistance_values.append((timestamp, player['fire_resistance']))
                
                # Process area data
                if 'environment' in snapshot and 'current_area' in snapshot['environment']:
                    area = snapshot['environment']['current_area']
                    areas_visited.add(area)
                
                # Process enemy data
                if 'enemies' in snapshot:
                    for enemy in snapshot['enemies']:
                        enemy_type = enemy.get('type', 'Unknown')
                        if enemy_type not in enemy_data:
                            enemy_data[enemy_type] = 0
                        enemy_data[enemy_type] += 1
        
        except Exception as e:
            print(f"Error processing snapshot {snapshot_file}: {e}")
    
    # Process events to find damage sources
    for event_file in event_files:
        try:
            with open(os.path.join(events_dir, event_file), 'r') as f:
                event = json.load(f)
                
                # Look for damage events
                if event.get('event_type') == 'PLAYER_DAMAGED':
                    damage_source = event.get('data', {}).get('source', 'Unknown')
                    damage_amount = event.get('data', {}).get('amount', 0)
                    
                    if damage_source not in damage_sources:
                        damage_sources[damage_source] = []
                    damage_sources[damage_source].append(damage_amount)
        
        except Exception as e:
            print(f"Error processing event {event_file}: {e}")
    
    # Analyze health trends
    health_trend = "stable"
    if len(health_changes) >= 2:
        first_health = health_changes[0][1]
        last_health = health_changes[-1][1]
        
        if last_health < first_health:
            health_trend = "declining"
        elif last_health > first_health:
            health_trend = "improving"
    
    # Analyze wetness and fire resistance correlation
    wetness_fire_correlation = "undetermined"
    if len(wetness_values) > 5 and len(fire_resistance_values) > 5:
        # Simple correlation check
        increasing_together = 0
        decreasing_together = 0
        
        for i in range(1, min(len(wetness_values), len(fire_resistance_values))):
            prev_wetness = wetness_values[i-1][1]
            curr_wetness = wetness_values[i][1]
            
            prev_resistance = fire_resistance_values[i-1][1]
            curr_resistance = fire_resistance_values[i][1]
            
            if (curr_wetness > prev_wetness and curr_resistance > prev_resistance) or \
               (curr_wetness < prev_wetness and curr_resistance < prev_resistance):
                increasing_together += 1
            else:
                decreasing_together += 1
        
        if increasing_together > decreasing_together * 2:
            wetness_fire_correlation = "strong positive"
        elif increasing_together > decreasing_together:
            wetness_fire_correlation = "positive"
        elif decreasing_together > increasing_together * 2:
            wetness_fire_correlation = "strong negative"
        elif decreasing_together > increasing_together:
            wetness_fire_correlation = "negative"
        else:
            wetness_fire_correlation = "neutral"
    
    # Calculate average damage by source
    damage_source_summary = {}
    for source, damages in damage_sources.items():
        if damages:
            avg_damage = sum(damages) / len(damages)
            damage_source_summary[source] = {
                'avg_damage': avg_damage,
                'frequency': len(damages),
                'total_damage': sum(damages)
            }
    
    # Format the report
    report = f"""
[SESSION OVERVIEW]
Session ID: {session_id}
Start Time: {session_start_time}
Duration: {session_duration}
Areas Visited: {', '.join(areas_visited)}
Snapshots Captured: {len(snapshot_files)}
Events Recorded: {len(event_files)}

[PLAYER ANALYSIS]
Health Trend: {health_trend}
Wetness-Fire Resistance Correlation: {wetness_fire_correlation}
"""

    if wetness_values:
        min_wetness = min([w[1] for w in wetness_values])
        max_wetness = max([w[1] for w in wetness_values])
        avg_wetness = sum([w[1] for w in wetness_values]) / len(wetness_values)
        report += f"Wetness Range: {min_wetness:.1f} to {max_wetness:.1f} (avg: {avg_wetness:.1f})\n"
    
    if fire_resistance_values:
        min_resist = min([r[1] for r in fire_resistance_values])
        max_resist = max([r[1] for r in fire_resistance_values])
        avg_resist = sum([r[1] for r in fire_resistance_values]) / len(fire_resistance_values)
        report += f"Fire Resistance Range: {min_resist:.1f}% to {max_resist:.1f}% (avg: {avg_resist:.1f}%)\n"

    report += """
[ENEMY ENCOUNTERS]
"""
    if enemy_data:
        for enemy_type, count in enemy_data.items():
            report += f"{enemy_type}: {count} instances\n"
    else:
        report += "No enemy data recorded.\n"

    report += """
[DAMAGE ANALYSIS]
"""
    if damage_source_summary:
        for source, stats in damage_source_summary.items():
            report += f"{source}: {stats['frequency']} hits, {stats['avg_damage']:.1f} avg damage, {stats['total_damage']:.1f} total\n"
    else:
        report += "No damage data recorded.\n"

    report += """
[INSIGHTS & PATTERNS]
"""
    # Add any detected patterns
    insights = []
    
    # Check for wetness impact on fire resistance
    if wetness_fire_correlation in ["positive", "strong positive"]:
        insights.append("Increased wetness appears to boost fire resistance")
    
    # Check for primary damage sources
    if damage_source_summary:
        top_damage_source = max(damage_source_summary.items(), key=lambda x: x[1]['total_damage'])[0]
        insights.append(f"Primary damage source: {top_damage_source}")
    
    # Check for area-specific patterns
    if 'VOLCANO' in areas_visited and 'BEACH' in areas_visited:
        insights.append("Player progressed from water to fire areas")
    
    if 'ABYSS' in areas_visited:
        insights.append("Player reached the final abyss area")
    
    # Add insights to report
    if insights:
        for insight in insights:
            report += f"- {insight}\n"
    else:
        report += "No significant patterns detected.\n"
    
    print("Analysis complete!")
    return report

if __name__ == "__main__":
    main()
