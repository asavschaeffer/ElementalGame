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
from recursive_analyzer import RecursiveAnalyzer

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
    parser.add_argument('--narrative', action='store_true',
                        help='Generate a narrative description of gameplay experience')
    parser.add_argument('--multi-session-narrative', action='store_true',
                        help='Generate a narrative across all gameplay sessions')
    parser.add_argument('--cross-session-patterns', action='store_true',
                        help='Analyze patterns and progression across multiple sessions')
    parser.add_argument('--compare-recursive', action='store_true',
                        help='Compare logs recursively using the ouroboros framework')
    parser.add_argument('--compare-mode', choices=['cooccurrence', 'temporal'], default='cooccurrence',
                        help='Mode for recursive comparison (ignoring time vs. focusing on temporal evolution)')
    parser.add_argument('--entity1', help='First entity ID to compare (snapshot, session, or export)')
    parser.add_argument('--entity2', help='Second entity ID to compare (snapshot, session, or export)')
    parser.add_argument('--entity1-level', choices=['snapshot', 'session', 'export'], default='session',
                        help='Level of first entity')
    parser.add_argument('--entity2-level', choices=['snapshot', 'session', 'export'], default='session',
                        help='Level of second entity')
    
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

    # Generate narrative
    if args.narrative:
        print("Generating gameplay narrative...")
        narrative = generate_gameplay_narrative(session_id)
        print(narrative)
        return
        
    # Generate multi-session narrative
    if args.multi_session_narrative:
        print("Generating multi-session gameplay narrative...")
        narrative = generate_gameplay_narrative(session_id=None, multi_session=True)
        print(narrative)
        return

    # Eat logs command
    if args.eat_logs:
        print("Eating logs and detecting patterns...")
        # Updated to process all sessions instead of just one
        sessions = list_all_sessions()
        if not sessions:
            print("No game sessions found. Please play the game first.")
            return
            
        print(f"Processing {len(sessions)} sessions...")
        combined_report = "# MULTI-SESSION ANALYSIS REPORT\n\n"
        
        for idx, session in enumerate(sessions):
            print(f"Analyzing session {idx+1}/{len(sessions)}: {session}")
            report = generate_compressed_log_report(session)
            combined_report += f"## Session {idx+1}: {session}\n\n"
            combined_report += report + "\n\n"
            
        # Save combined report to file
        exports_dir = os.path.join('logs', 'exports')
        os.makedirs(exports_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(exports_dir, f"multi_session_report_{timestamp}.md")
        
        with open(report_file, 'w') as f:
            f.write(combined_report)
            
        print(f"Multi-session analysis complete! Report saved to: {report_file}")
        print(combined_report)
        return

    # Cross-session pattern analysis
    if args.cross_session_patterns:
        print("Analyzing patterns across multiple sessions...")
        analyze_cross_session_patterns()
        return
        
    # Recursive comparison (new feature)
    if args.compare_recursive:
        print("Performing recursive log comparison...")
        temporal_mode = args.compare_mode == 'temporal'
        
        # Initialize the recursive analyzer
        analyzer = RecursiveAnalyzer(temporal_mode=temporal_mode)
        
        if not args.entity1 or not args.entity2:
            # If no specific entities provided, compare the two most recent sessions
            sessions = list_all_sessions()
            if len(sessions) < 2:
                print("Need at least two sessions for comparison.")
                return
            entity1 = sessions[-1]  # Most recent
            entity2 = sessions[-2]  # Second most recent
            level1 = level2 = 'session'
            print(f"Comparing two most recent sessions: {entity1} and {entity2}")
        else:
            entity1 = args.entity1
            entity2 = args.entity2
            level1 = args.entity1_level
            level2 = args.entity2_level
        
        # Perform the comparison
        print(f"Comparing {level1}:{entity1} with {level2}:{entity2}...")
        if level1 == level2 == 'session':
            results = analyzer.compare(entity1, entity2, level='session')
        else:
            results = analyzer.find_cross_level_patterns(entity1, entity2, level1, level2)
        
        # Generate and save report
        report = generate_recursive_comparison_report(results, entity1, entity2, level1, level2, temporal_mode)
        
        # Save to file
        exports_dir = os.path.join('logs', 'exports')
        os.makedirs(exports_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(exports_dir, f"recursive_comparison_{timestamp}.md")
        
        with open(report_file, 'w') as f:
            f.write(report)
            
        print(f"Recursive comparison complete! Report saved to: {report_file}")
        print(report)
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
    
    # Collect event files if they exist
    event_files = []
    events_dir = os.path.join(session_dir, "events")
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
    
    # Add deeper pattern analysis
    # Track elemental progression timeline
    elemental_timeline = []
    if 'BEACH' in areas_visited:
        elemental_timeline.append("Gained water resistance")
    if 'VOLCANO' in areas_visited and len(fire_resistance_values) > 0 and any(r[1] > 50 for r in fire_resistance_values):
        elemental_timeline.append("Developed significant fire resistance")
    if 'ABYSS' in areas_visited and len(fire_resistance_values) > 0 and len(wetness_values) > 0:
        if any(r[1] > 70 for r in fire_resistance_values) and any(w[1] > 70 for w in wetness_values):
            elemental_timeline.append("Achieved obsidian armor formation")
    
    # Detect player adaptation patterns
    adaptation_insights = []
    # Check for wetness increases after fire damage
    if damage_sources.get("LAVA", []) and wetness_values:
        wet_timestamps = [float(w[0]) for w in wetness_values]
        lava_damage_events = []
        for event_file in event_files:
            try:
                with open(os.path.join(events_dir, event_file), 'r') as f:
                    event = json.load(f)
                    if event.get('event_type') == 'PLAYER_DAMAGED' and event.get('data', {}).get('source') == 'LAVA':
                        lava_damage_events.append(float(event.get('timestamp', 0)))
            except Exception:
                pass
        
        # Look for wetness increases after lava damage
        adaptation_count = 0
        for damage_time in lava_damage_events:
            for i, wet_time in enumerate(wet_timestamps[:-1]):
                if wet_time > damage_time and wet_timestamps[i+1] > wet_time:
                    # Check if wetness increased
                    if wetness_values[i+1][1] > wetness_values[i][1]:
                        adaptation_count += 1
                        break
        
        if adaptation_count > 2:
            adaptation_insights.append("Player learned to increase wetness after taking fire damage")
    
    # Add narrative-driven summary
    narrative = []
    
    if elemental_timeline:
        narrative.append("Elemental Journey: " + " → ".join(elemental_timeline))
    
    if adaptation_insights:
        narrative.append("Player Adaptation: " + " | ".join(adaptation_insights))
    
    # Check for combat style
    if damage_source_summary:
        total_hits = sum(stats['frequency'] for stats in damage_source_summary.values())
        if total_hits > 20:
            narrative.append("Combat Style: Experienced many combat encounters")
        elif total_hits < 5:
            narrative.append("Combat Style: Avoided most combat encounters")
    
    # Add insights to report
    if insights:
        report += "Key Observations:\n"
        for insight in insights:
            report += f"- {insight}\n"
    
    if narrative:
        report += "\nYour Gameplay Story:\n"
        for story_element in narrative:
            report += f"- {story_element}\n"
    
    if not insights and not narrative:
        report += "No significant patterns detected.\n"
    
    print("Analysis complete!")
    return report

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
    sessions_dir = os.path.join('logs', 'sessions')
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
    
    # Add deeper pattern analysis
    # Track elemental progression timeline
    elemental_timeline = []
    if 'BEACH' in areas_visited:
        elemental_timeline.append("Gained water resistance")
    if 'VOLCANO' in areas_visited and len(fire_resistance_values) > 0 and any(r[1] > 50 for r in fire_resistance_values):
        elemental_timeline.append("Developed significant fire resistance")
    if 'ABYSS' in areas_visited and len(fire_resistance_values) > 0 and len(wetness_values) > 0:
        if any(r[1] > 70 for r in fire_resistance_values) and any(w[1] > 70 for w in wetness_values):
            elemental_timeline.append("Achieved obsidian armor formation")
    
    # Detect player adaptation patterns
    adaptation_insights = []
    # Check for wetness increases after fire damage
    if damage_sources.get("LAVA", []) and wetness_values:
        wet_timestamps = [float(w[0]) for w in wetness_values]
        lava_damage_events = []
        for event_file in event_files:
            try:
                with open(os.path.join(events_dir, event_file), 'r') as f:
                    event = json.load(f)
                    if event.get('event_type') == 'PLAYER_DAMAGED' and event.get('data', {}).get('source') == 'LAVA':
                        lava_damage_events.append(float(event.get('timestamp', 0)))
            except Exception:
                pass
        
        # Look for wetness increases after lava damage
        adaptation_count = 0
        for damage_time in lava_damage_events:
            for i, wet_time in enumerate(wet_timestamps[:-1]):
                if wet_time > damage_time and wet_timestamps[i+1] > wet_time:
                    # Check if wetness increased
                    if wetness_values[i+1][1] > wetness_values[i][1]:
                        adaptation_count += 1
                        break
        
        if adaptation_count > 2:
            adaptation_insights.append("Player learned to increase wetness after taking fire damage")
    
    # Add narrative-driven summary
    narrative = []
    
    if elemental_timeline:
        narrative.append("Elemental Journey: " + " → ".join(elemental_timeline))
    
    if adaptation_insights:
        narrative.append("Player Adaptation: " + " | ".join(adaptation_insights))
    
    # Check for combat style
    if damage_source_summary:
        total_hits = sum(stats['frequency'] for stats in damage_source_summary.values())
        if total_hits > 20:
            narrative.append("Combat Style: Experienced many combat encounters")
        elif total_hits < 5:
            narrative.append("Combat Style: Avoided most combat encounters")
    
    # Add insights to report
    if insights:
        report += "Key Observations:\n"
        for insight in insights:
            report += f"- {insight}\n"
    
    if narrative:
        report += "\nYour Gameplay Story:\n"
        for story_element in narrative:
            report += f"- {story_element}\n"
    
    if not insights and not narrative:
        report += "No significant patterns detected.\n"
    
    print("Analysis complete!")
    return report

def generate_gameplay_narrative(session_id=None, multi_session=False):
    """
    Generate a narrative description of the player's gameplay experience.
    
    This function uses the advanced analytics module to create a story-driven
    interpretation of the player's journey through the game world.
    
    Args:
        session_id (str): Session ID to analyze (uses most recent if None)
        multi_session (bool): Whether to analyze multiple sessions
        
    Returns:
        str: Narrative text describing the gameplay experience
    """
    try:
        from advanced_analytics import TemporalPatternAnalyzer
        
        if multi_session:
            # Get all sessions
            sessions = list_all_sessions()
            if not sessions:
                return "No gameplay data available for analysis."
                
            print(f"Generating narrative across {len(sessions)} sessions...")
            combined_narrative = "# Your Complete Elemental Journey\n\n"
            combined_narrative += "## Across Multiple Game Sessions\n\n"
            
            # Track progression across sessions
            areas_visited_all = set()
            progression_stages = []
            
            # Process each session
            for idx, session in enumerate(sessions):
                print(f"Analyzing session {idx+1}/{len(sessions)}: {session}")
                
                # Initialize the analyzer
                analyzer = TemporalPatternAnalyzer(session)
                
                # Generate narrative for this session
                session_narrative = analyzer.generate_gameplay_narrative()
                
                # Extract areas visited
                areas_in_session = set()
                for snapshot in analyzer.snapshots:
                    if 'environment' in snapshot and 'current_area' in snapshot['environment']:
                        area = snapshot['environment']['current_area']
                        areas_in_session.add(area)
                        areas_visited_all.add(area)
                
                # Track progression milestones
                if 'BEACH' in areas_in_session and 'BEACH' not in [stage[0] for stage in progression_stages]:
                    progression_stages.append(('BEACH', idx))
                if 'VOLCANO' in areas_in_session and 'VOLCANO' not in [stage[0] for stage in progression_stages]:
                    progression_stages.append(('VOLCANO', idx))
                if 'ABYSS' in areas_in_session and 'ABYSS' not in [stage[0] for stage in progression_stages]:
                    progression_stages.append(('ABYSS', idx))
                
                # Add session narrative
                combined_narrative += f"### Session {idx+1}\n\n"
                combined_narrative += session_narrative + "\n\n"
            
            # Add cross-session analysis
            combined_narrative += "## Your Overall Journey\n\n"
            
            # Describe progression path
            if progression_stages:
                progression_stages.sort(key=lambda x: x[1])  # Sort by session index
                progression_path = " → ".join([stage[0] for stage in progression_stages])
                combined_narrative += f"Your path through the elemental world: **{progression_path}**\n\n"
            
            if 'ABYSS' in areas_visited_all:
                combined_narrative += "You reached the final challenge in the Abyss, completing your elemental journey!\n\n"
            elif 'VOLCANO' in areas_visited_all:
                combined_narrative += "You've ventured through fire, but have yet to master the final challenge.\n\n"
            elif 'BEACH' in areas_visited_all:
                combined_narrative += "You've begun your elemental journey, taking your first steps into the world of water.\n\n"
            
            # Save narrative to file
            exports_dir = os.path.join('logs', 'exports')
            os.makedirs(exports_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            narrative_file = os.path.join(exports_dir, f"multi_session_narrative_{timestamp}.md")
            
            with open(narrative_file, 'w') as f:
                f.write(combined_narrative)
            
            print(f"Multi-session narrative saved to: {narrative_file}")
            
            return combined_narrative
        else:
            # Original single-session analysis
            analyzer = TemporalPatternAnalyzer(session_id)
            narrative = analyzer.generate_gameplay_narrative()
            
            # Save narrative to file
            if narrative:
                exports_dir = os.path.join('logs', 'exports')
                os.makedirs(exports_dir, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                narrative_file = os.path.join(exports_dir, f"narrative_{timestamp}.md")
                
                with open(narrative_file, 'w') as f:
                    f.write(narrative)
                
                print(f"Narrative saved to: {narrative_file}")
            
            return narrative
            
    except ImportError as e:
        print(f"Error: Could not import advanced analytics module: {e}")
        return "Advanced analytics module not available. Please ensure the advanced_analytics.py file exists."

def analyze_cross_session_patterns():
    """
    Analyze patterns and player progression across multiple game sessions.
    
    This function identifies trends and patterns that emerge across gameplay sessions,
    such as how player performance improves over time, how strategies evolve,
    and the overall progression through the game's elemental mechanics.
    
    Returns:
        str: Cross-session analysis report
    """
    # Get all sessions
    sessions = list_all_sessions()
    if not sessions:
        print("No gameplay data available for analysis.")
        return
    
    print(f"Analyzing patterns across {len(sessions)} sessions...")
    
    # Track key metrics per session
    session_metrics = []
    areas_per_session = {}
    damage_per_session = {}
    wetness_per_session = {}
    
    # Analyze each session
    for session_id in sessions:
        # Get the session directory
        sessions_dir = os.path.join('logs', 'sessions')
        session_dir = os.path.join(sessions_dir, session_id)
        
        if not os.path.exists(session_dir):
            continue
        
        # Get snapshots and events
        snapshots_dir = os.path.join(session_dir, "snapshots")
        events_dir = os.path.join(session_dir, "events")
        
        if not os.path.exists(snapshots_dir):
            continue
            
        # Collect snapshot files
        snapshot_files = sorted([f for f in os.listdir(snapshots_dir) if f.endswith('.json')])
        if not snapshot_files:
            continue
            
        # Collect event files
        event_files = []
        if os.path.exists(events_dir):
            event_files = sorted([f for f in os.listdir(events_dir) if f.endswith('.json')])
            
        # Load manifest for session metadata
        manifest_path = os.path.join(session_dir, "manifest.json")
        session_start_time = "Unknown"
        
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                    session_start_time = manifest.get('start_time', 0)
            except Exception:
                pass
                
        # Extract session data
        session_data = {
            'id': session_id,
            'timestamp': float(session_start_time) if isinstance(session_start_time, (int, float, str)) else 0,
            'areas': set(),
            'max_health': 0,
            'max_wetness': 0,
            'max_fire_resistance': 0,
            'damage_taken': 0,
            'enemies_encountered': 0,
            'snapshot_count': len(snapshot_files),
            'event_count': len(event_files)
        }
        
        # Process snapshots for this session
        for snapshot_file in snapshot_files:
            try:
                with open(os.path.join(snapshots_dir, snapshot_file), 'r') as f:
                    snapshot = json.load(f)
                    
                    # Track areas visited
                    if 'environment' in snapshot and 'current_area' in snapshot['environment']:
                        area = snapshot['environment']['current_area']
                        session_data['areas'].add(area)
                        
                    # Track player stats
                    if 'player' in snapshot:
                        player = snapshot['player']
                        if 'health' in player and player['health'] > session_data['max_health']:
                            session_data['max_health'] = player['health']
                            
                        if 'wetness' in player and player['wetness'] > session_data['max_wetness']:
                            session_data['max_wetness'] = player['wetness']
                            
                        if 'fire_resistance' in player and player['fire_resistance'] > session_data['max_fire_resistance']:
                            session_data['max_fire_resistance'] = player['fire_resistance']
                            
                    # Count enemies
                    if 'enemies' in snapshot:
                        session_data['enemies_encountered'] += len(snapshot['enemies'])
            except Exception:
                continue
                
        # Process events for this session
        if os.path.exists(events_dir):
            for event_file in event_files:
                try:
                    with open(os.path.join(events_dir, event_file), 'r') as f:
                        event = json.load(f)
                        
                        # Track damage taken
                        if event.get('event_type') == 'PLAYER_DAMAGED':
                            damage = event.get('data', {}).get('amount', 0)
                            session_data['damage_taken'] += damage
                except Exception:
                    continue
                    
        # Add to tracking collections
        session_metrics.append(session_data)
        areas_per_session[session_id] = session_data['areas']
        damage_per_session[session_id] = session_data['damage_taken']
        wetness_per_session[session_id] = session_data['max_wetness']
        
    # Sort sessions by timestamp
    session_metrics.sort(key=lambda x: x['timestamp'])
    
    # Generate visualization
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        from datetime import datetime
        
        # Create figure
        plt.figure(figsize=(12, 10))
        
        # Plot 1: Areas visited progression
        plt.subplot(2, 2, 1)
        areas_known = set()
        for session in session_metrics:
            areas_known.update(session['areas'])
        
        area_order = ['BEACH', 'FOREST', 'VOLCANO', 'ABYSS']
        area_order = [a for a in area_order if a in areas_known] + [a for a in areas_known if a not in area_order]
        
        area_matrix = np.zeros((len(session_metrics), len(area_order)))
        for i, session in enumerate(session_metrics):
            for j, area in enumerate(area_order):
                if area in session['areas']:
                    area_matrix[i, j] = 1
        
        plt.imshow(area_matrix, aspect='auto', cmap='viridis')
        plt.yticks(range(len(session_metrics)), [f"S{i+1}" for i in range(len(session_metrics))])
        plt.xticks(range(len(area_order)), area_order)
        plt.title('Area Progression')
        plt.xlabel('Game Areas')
        plt.ylabel('Session Number')
        
        # Plot 2: Max wetness/fire resistance over sessions
        plt.subplot(2, 2, 2)
        wetness_values = [s['max_wetness'] for s in session_metrics]
        fire_res_values = [s['max_fire_resistance'] for s in session_metrics]
        x = range(len(session_metrics))
        
        plt.plot(x, wetness_values, 'b-', label='Max Wetness')
        plt.plot(x, fire_res_values, 'r-', label='Max Fire Resistance')
        plt.xticks(x, [f"S{i+1}" for i in range(len(session_metrics))])
        plt.title('Elemental Resistance Progression')
        plt.xlabel('Session Number')
        plt.ylabel('Maximum Value')
        plt.legend()
        plt.grid(True)
        
        # Plot 3: Damage taken per session
        plt.subplot(2, 2, 3)
        damage_values = [s['damage_taken'] for s in session_metrics]
        plt.bar(x, damage_values)
        plt.xticks(x, [f"S{i+1}" for i in range(len(session_metrics))])
        plt.title('Damage Taken Per Session')
        plt.xlabel('Session Number')
        plt.ylabel('Damage Amount')
        plt.grid(True)
        
        # Plot 4: Enemies encountered per session
        plt.subplot(2, 2, 4)
        enemy_values = [s['enemies_encountered'] for s in session_metrics]
        plt.bar(x, enemy_values)
        plt.xticks(x, [f"S{i+1}" for i in range(len(session_metrics))])
        plt.title('Enemies Encountered Per Session')
        plt.xlabel('Session Number')
        plt.ylabel('Enemy Count')
        plt.grid(True)
        
        # Adjust layout and save
        plt.tight_layout()
        
        # Save visualization
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        exports_dir = os.path.join('logs', 'exports')
        os.makedirs(exports_dir, exist_ok=True)
        output_file = os.path.join(exports_dir, f"cross_session_analysis_{timestamp}.png")
        plt.savefig(output_file)
        plt.close()
        
        print(f"Cross-session visualization saved to: {output_file}")
        
    except ImportError:
        print("Could not create visualization - matplotlib may not be installed")
        
    # Generate report
    report = "# Cross-Session Analysis Report\n\n"
    
    # Identify game progression
    max_areas_reached = {}
    for session in session_metrics:
        for area in session['areas']:
            if area not in max_areas_reached or session['timestamp'] > max_areas_reached[area]['timestamp']:
                max_areas_reached[area] = {
                    'session': session['id'],
                    'timestamp': session['timestamp']
                }
    
    # Organize progression milestones
    progression_points = []
    area_order = ['BEACH', 'FOREST', 'VOLCANO', 'ABYSS']
    
    for area in area_order:
        if area in max_areas_reached:
            progression_points.append((area, max_areas_reached[area]['session']))
    
    # Add progression summary
    if progression_points:
        report += "## Progression Milestones\n\n"
        for area, session in progression_points:
            report += f"- **{area}** first reached in session {session}\n"
        report += "\n"
    
    # Analyze session-to-session improvements
    if len(session_metrics) > 1:
        report += "## Player Development\n\n"
        
        # Check for wetness/fire resistance improvement
        first_wetness = session_metrics[0]['max_wetness']
        last_wetness = session_metrics[-1]['max_wetness']
        
        first_fire = session_metrics[0]['max_fire_resistance']
        last_fire = session_metrics[-1]['max_fire_resistance']
        
        wetness_change = last_wetness - first_wetness
        fire_change = last_fire - first_fire
        
        if wetness_change > 10:
            report += f"- Wetness mastery improved by {wetness_change:.1f} points across sessions\n"
        
        if fire_change > 10:
            report += f"- Fire resistance improved by {fire_change:.1f}% across sessions\n"
        
        # Check for reaching end game
        if 'ABYSS' in max_areas_reached:
            report += "- Player successfully reached the final area (ABYSS)\n"
            
            # Check if they had obsidian armor
            final_session = max_areas_reached['ABYSS']['session']
            for session in session_metrics:
                if session['id'] == final_session:
                    if session['max_wetness'] > 70 and session['max_fire_resistance'] > 70:
                        report += "- Successfully formed obsidian armor (high wetness + fire resistance)\n"
                    break
        
        report += "\n"
    
    # Identify learning patterns
    if len(session_metrics) > 2:
        report += "## Player Learning Patterns\n\n"
        
        # Analyze damage taken over time
        damages = [s['damage_taken'] for s in session_metrics if s['damage_taken'] > 0]
        if len(damages) >= 3:
            first_half = damages[:len(damages)//2]
            second_half = damages[len(damages)//2:]
            
            if sum(first_half) > 0 and sum(second_half) > 0:
                avg_damage_early = sum(first_half) / len(first_half)
                avg_damage_late = sum(second_half) / len(second_half)
                
                if avg_damage_late < avg_damage_early * 0.75:
                    report += "- Player is learning to avoid damage (damage taken decreased over time)\n"
                elif avg_damage_late > avg_damage_early * 1.25:
                    report += "- Player is facing more challenging content (damage taken increased over time)\n"
        
        # Check for exploration patterns
        areas_by_session = [len(s['areas']) for s in session_metrics]
        if max(areas_by_session) > 1:
            report += f"- Maximum areas explored in a single session: {max(areas_by_session)}\n"
            
        report += "\n"
    
    # Save report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = os.path.join(exports_dir, f"cross_session_report_{timestamp}.md")
    
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"Cross-session analysis report saved to: {report_file}")
    print(report)
    
    return report

def generate_recursive_comparison_report(results, entity1, entity2, level1, level2, temporal_mode):
    """
    Generate a report from recursive comparison results.
    
    Args:
        results (dict): Comparison results
        entity1 (str): First entity ID
        entity2 (str): Second entity ID
        level1 (str): Level of first entity
        level2 (str): Level of second entity
        temporal_mode (bool): Whether temporal analysis was used
        
    Returns:
        str: Formatted report
    """
    report = ["# Recursive Ouroboros Analysis Report\n"]
    
    # Add comparison summary
    report.append("## Comparison Summary")
    report.append(f"- Entity 1: {entity1} ({level1})")
    report.append(f"- Entity 2: {entity2} ({level2})")
    report.append(f"- Analysis Mode: {'Temporal Evolution' if temporal_mode else 'Co-occurrence'}\n")
    
    # Check for errors
    if 'error' in results:
        report.append(f"**Error:** {results['error']}")
        report.append("\nTroubleshooting suggestions:")
        report.append("1. Check that both entities exist and are accessible")
        report.append("2. Verify that snapshots are available for both sessions")
        report.append("3. Try using different comparison entities or modes")
        report.append("\nFor more information, run: `python analyze_logs.py --list-sessions` to see available sessions.")
        return "\n".join(report)
    
    # Central comparison patterns (for binary tree comparison)
    if 'central_patterns' in results:
        report.append("## Central Comparison")
        central = results['central_patterns']
        if 'changes' in central:
            num_changes = len(central['changes'])
            report.append(f"- Found {num_changes} changed values between central snapshots")
            
            if num_changes > 0:
                report.append("\n### Top Changes")
                # Show a few important changes
                changes_shown = 0
                for key, (old_val, new_val) in central['changes'].items():
                    if changes_shown < 5:  # Limit to 5 examples
                        report.append(f"- `{key}`: {old_val} → {new_val}")
                        changes_shown += 1
    
    # Pattern counts aggregated across all comparisons
    if 'pattern_counts' in results and results['pattern_counts']:
        report.append("\n## Detected Patterns")
        pattern_counts = results['pattern_counts']
        
        # Convert string keys back to tuples for readability
        readable_patterns = {}
        for key_str, count in pattern_counts.items():
            try:
                # The key is stored as a string but represents a tuple of keys
                # Example: "('player.health', 'environment.area')"
                clean_key = key_str.strip("()' ").replace("'", "")
                parts = clean_key.split(',')
                if len(parts) == 2:
                    readable_key = f"{parts[0].strip()} ↔ {parts[1].strip()}"
                    readable_patterns[readable_key] = count
            except:
                readable_patterns[key_str] = count
                
        # Sort by frequency
        sorted_patterns = sorted(readable_patterns.items(), key=lambda x: x[1], reverse=True)
        
        report.append(f"- Found {len(sorted_patterns)} recurring patterns")
        
        if sorted_patterns:
            report.append("\n### Most Frequent Patterns")
            for pattern, count in sorted_patterns[:10]:  # Show top 10
                report.append(f"- **{pattern}**: {count} occurrences")
    
    # Temporal information
    if temporal_mode and 'all_patterns' in results:
        report.append("\n## Temporal Analysis")
        time_diffs = []
        
        for pattern in results.get('all_patterns', []):
            if 'time_difference' in pattern:
                time_diffs.append(pattern['time_difference'])
        
        if time_diffs:
            avg_time_diff = sum(time_diffs) / len(time_diffs)
            report.append(f"- Average time between related changes: {avg_time_diff:.2f}")
            report.append(f"- Total temporal relationships found: {len(time_diffs)}")
    
    # Add visualization suggestions
    report.append("\n## Suggested Visualizations")
    report.append("Based on this analysis, consider generating these visualizations:")
    
    if level1 == level2 == 'session':
        report.append("1. Changes over time for both sessions")
        report.append("2. Pattern frequency comparison")
    else:
        report.append("1. Cross-level relationship diagram")
        report.append("2. Hierarchical pattern map")
    
    # Add a note about the recursive framework
    report.append("\n## About Recursive Ouroboros Framework")
    report.append("This analysis uses a recursive comparison framework that can identify patterns")
    report.append("across different levels of game data. The 'ouroboros' approach allows")
    report.append("patterns to feed back into themselves, revealing cyclic relationships.")
    
    if temporal_mode:
        report.append("\nTemporal mode analyzes how relationships evolve over time,")
        report.append("focusing on the sequence and timing of changes.")
    else:
        report.append("\nCo-occurrence mode focuses on relationships between data points,")
        report.append("ignoring time to identify associations regardless of when they occur.")
    
    return "\n".join(report)

if __name__ == "__main__":
    main()
