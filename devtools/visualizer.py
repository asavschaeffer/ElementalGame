"""
Log Visualizer Tool

This module provides visualization capabilities for game logs and metrics,
helping developers understand patterns and performance issues. It converts
snapshots and log data into interactive charts and graphs.

Features:
1. FPS over time visualization
2. Entity count tracking
3. Player state progression visualization
4. Area transition flow diagrams
5. Performance hotspot identification
"""

import os
import sys
import json
import datetime
import time
from typing import Dict, List, Any, Tuple, Optional

# Optional matplotlib import for visualizations
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not found. Visualization features will be limited.")

# Import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import game_logger

# Import from the same package
from .snapshot_analyzer import SnapshotAnalyzer


class LogVisualizer:
    """Provides visualization tools for game log data."""
    
    def __init__(self, analyzer: SnapshotAnalyzer = None):
        """
        Initialize the visualizer.
        
        Args:
            analyzer: Optional SnapshotAnalyzer instance
        """
        self.analyzer = analyzer or SnapshotAnalyzer()
        self.data = {}
        self.output_dir = os.path.join('devtools', 'visualizations')
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
    
    def load_data(self, sessions_limit: int = 3):
        """Load data for visualization."""
        # Load sessions
        self.analyzer.load_sessions(limit=sessions_limit)
        
        # Process the first session
        if self.analyzer.sessions:
            first_session = list(self.analyzer.sessions.keys())[0]
            self.analyzer.load_session_snapshots(first_session)
            self.analyzer.load_session_logs(first_session)
            
            # Flatten data
            self.data = self.analyzer.flatten_snapshots()
    
    def visualize_fps(self, session_id: str = None, output_file: str = None):
        """
        Visualize FPS data over time.
        
        Args:
            session_id: Optional specific session to visualize
            output_file: Optional output file path
        """
        if not HAS_MATPLOTLIB:
            print("Error: matplotlib is required for this feature.")
            return
        
        # Load session logs if needed
        if not self.analyzer.sessions:
            self.load_data()
        
        # Get the session to use
        if session_id and session_id in self.analyzer.sessions:
            session = self.analyzer.sessions[session_id]
        elif self.analyzer.sessions:
            session = list(self.analyzer.sessions.values())[0]
        else:
            print("No sessions available.")
            return
        
        # Ensure log entries are loaded
        if not session.get('log_entries'):
            session_id = session['id']
            self.analyzer.load_session_logs(session_id)
            
        # Extract FPS data from logs
        timestamps = []
        fps_values = []
        
        for entry in session.get('log_entries', []):
            if 'dev_tutorial_performance' in entry.get('message', ''):
                data = entry.get('data', {})
                if isinstance(data, dict) and 'avg_fps' in data:
                    fps = data['avg_fps']
                    timestamp = datetime.datetime.fromtimestamp(entry.get('timestamp', 0))
                    
                    timestamps.append(timestamp)
                    fps_values.append(fps)
        
        if not fps_values:
            print("No FPS data available.")
            return
        
        # Create plot
        plt.figure(figsize=(12, 6))
        plt.plot(timestamps, fps_values, 'b-', label='Average FPS')
        
        # Add target FPS line
        plt.axhline(y=60, color='g', linestyle='--', label='Target (60 FPS)')
        plt.axhline(y=30, color='r', linestyle='--', label='Minimum (30 FPS)')
        
        # Format the plot
        plt.title('Game Performance Over Time')
        plt.xlabel('Time')
        plt.ylabel('Frames Per Second')
        plt.legend()
        plt.grid(True)
        
        # Format x-axis to show readable times
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        
        # Auto-rotate date labels
        plt.gcf().autofmt_xdate()
        
        # Save or show
        if output_file:
            output_path = os.path.join(self.output_dir, output_file)
            plt.savefig(output_path)
            print(f"FPS visualization saved to {output_path}")
        else:
            plt.show()
    
    def visualize_player_progression(self, output_file: str = None):
        """
        Visualize player attribute progression over time.
        
        Args:
            output_file: Optional output file path
        """
        if not HAS_MATPLOTLIB:
            print("Error: matplotlib is required for this feature.")
            return
        
        # Load data if needed
        if not self.data:
            self.load_data()
        
        # Check for player data
        if 'player' not in self.data or not self.data['player']:
            print("No player data available.")
            return
        
        # Extract player attributes over time
        timestamps = []
        health_values = []
        wetness_values = []
        obsidian_values = []
        
        for entry in self.data['player']:
            timestamp = entry.get('timestamp', 0)
            health = entry.get('health', 0)
            wetness = entry.get('wetness', 0)
            obsidian = entry.get('obsidian_level', 0)
            
            timestamps.append(datetime.datetime.fromtimestamp(timestamp))
            health_values.append(health)
            wetness_values.append(wetness)
            obsidian_values.append(obsidian)
        
        if not timestamps:
            print("No player progression data available.")
            return
        
        # Create multi-panel plot
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
        
        # Plot health
        ax1.plot(timestamps, health_values, 'r-')
        ax1.set_ylabel('Health')
        ax1.set_title('Player Health Over Time')
        ax1.grid(True)
        
        # Plot wetness
        ax2.plot(timestamps, wetness_values, 'b-')
        ax2.set_ylabel('Wetness')
        ax2.set_title('Player Wetness Over Time')
        ax2.grid(True)
        
        # Plot obsidian
        ax3.plot(timestamps, obsidian_values, 'k-')
        ax3.set_ylabel('Obsidian')
        ax3.set_title('Player Obsidian Level Over Time')
        ax3.grid(True)
        ax3.set_xlabel('Time')
        
        # Format x-axis to show readable times
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        
        # Adjust layout
        plt.tight_layout()
        
        # Auto-rotate date labels
        fig.autofmt_xdate()
        
        # Save or show
        if output_file:
            output_path = os.path.join(self.output_dir, output_file)
            plt.savefig(output_path)
            print(f"Player progression visualization saved to {output_path}")
        else:
            plt.show()
    
    def visualize_enemy_count(self, output_file: str = None):
        """
        Visualize enemy count over time.
        
        Args:
            output_file: Optional output file path
        """
        if not HAS_MATPLOTLIB:
            print("Error: matplotlib is required for this feature.")
            return
        
        # Load data if needed
        if not self.data:
            self.load_data()
        
        # Check for environment data
        if 'environment' not in self.data or not self.data['environment']:
            print("No environment data available.")
            return
        
        # Extract enemy counts over time
        timestamps = []
        enemy_counts = []
        
        for entry in self.data['environment']:
            timestamp = entry.get('timestamp', 0)
            enemies = entry.get('enemies', [])
            
            # Count enemies
            count = len(enemies) if isinstance(enemies, list) else 0
            
            timestamps.append(datetime.datetime.fromtimestamp(timestamp))
            enemy_counts.append(count)
        
        if not timestamps:
            print("No enemy count data available.")
            return
        
        # Create plot
        plt.figure(figsize=(12, 6))
        plt.plot(timestamps, enemy_counts, 'g-')
        
        # Format the plot
        plt.title('Enemy Count Over Time')
        plt.xlabel('Time')
        plt.ylabel('Number of Enemies')
        plt.grid(True)
        
        # Format x-axis to show readable times
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        
        # Auto-rotate date labels
        plt.gcf().autofmt_xdate()
        
        # Save or show
        if output_file:
            output_path = os.path.join(self.output_dir, output_file)
            plt.savefig(output_path)
            print(f"Enemy count visualization saved to {output_path}")
        else:
            plt.show()
    
    def generate_report(self, output_file: str = "performance_report.html"):
        """
        Generate an HTML report with visualizations.
        
        Args:
            output_file: Output HTML file path
        """
        # Generate visualizations
        fps_img = "fps_chart.png"
        self.visualize_fps(output_file=fps_img)
        
        player_img = "player_progression.png"
        self.visualize_player_progression(output_file=player_img)
        
        enemy_img = "enemy_count.png"
        self.visualize_enemy_count(output_file=enemy_img)
        
        # Create HTML report
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Elemental Game Performance Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1, h2, h3 {{ color: #2c3e50; }}
        .chart-container {{ margin: 30px 0; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }}
        .chart {{ width: 100%; }}
        .summary {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Elemental Game Performance Report</h1>
        <p>Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary">
            <h2>Summary</h2>
            <p>This report provides visualizations of game performance and player progression based on log data.</p>
        </div>
        
        <div class="chart-container">
            <h2>FPS Performance</h2>
            <img class="chart" src="{fps_img}" alt="FPS Chart">
        </div>
        
        <div class="chart-container">
            <h2>Player Progression</h2>
            <img class="chart" src="{player_img}" alt="Player Progression">
        </div>
        
        <div class="chart-container">
            <h2>Enemy Count</h2>
            <img class="chart" src="{enemy_img}" alt="Enemy Count">
        </div>
    </div>
</body>
</html>
"""
        
        # Write HTML file
        output_path = os.path.join(self.output_dir, output_file)
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        print(f"Performance report generated at {output_path}")
        return output_path


if __name__ == "__main__":
    # Example usage
    visualizer = LogVisualizer()
    visualizer.load_data()
    
    # Generate report
    report_path = visualizer.generate_report()
    
    # Open the report in default browser
    import webbrowser
    webbrowser.open('file://' + os.path.abspath(report_path))
