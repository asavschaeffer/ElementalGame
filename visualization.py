import matplotlib.pyplot as plt
import numpy as np
import json
import os
from matplotlib.patches import Polygon
from scipy.interpolate import make_interp_spline
from logger import GameLogger

class GameStateVisualizer:
    """
    Visualizes game state data using calculus concepts as an analogy.
    This class creates visual representations of how snapshot logging relates to
    the continuous nature of player experience.
    """
    
    def __init__(self, logger=None):
        """Initialize with an optional GameLogger instance"""
        self.logger = logger or GameLogger()
        self.fig_size = (14, 8)
        self.dpi = 100
        self.colors = {
            'curve': '#1f77b4',      # Blue - true player state
            'intervals': '#2ca02c',   # Green - time intervals
            'complexity': '#9467bd',  # Purple - state complexity 
            'trapezoids': '#1f77b4',  # Blue (transparent) - approximation areas
            'slope': '#d62728',       # Red - instantaneous change
            'snapshots': '#ff7f0e'    # Yellow/Orange - JSON snapshots
        }
    
    def visualize_calculus_analogy(self, save_path=None):
        """
        Create a visual representation of how game state logging relates to calculus concepts.
        """
        # Create figure
        fig, ax = plt.subplots(figsize=self.fig_size, dpi=self.dpi)
        
        # Generate a smooth curve representing "true" player state
        x = np.linspace(0, 10, 1000)
        true_curve = 2 + np.sin(x) + 0.5*np.sin(2*x) + 0.2*np.sin(5*x) + x*0.1
        
        # Plot the true curve
        ax.plot(x, true_curve, color=self.colors['curve'], linewidth=2.5, label="True Player State")
        
        # Create sample snapshots (discrete points)
        # We'll use irregular intervals to show the concept better
        snapshot_x = np.array([0, 1.5, 3, 4, 5.5, 7, 8.2, 10])
        snapshot_y = 2 + np.sin(snapshot_x) + 0.5*np.sin(2*snapshot_x) + 0.2*np.sin(5*snapshot_x) + snapshot_x*0.1
        
        # Draw the trapezoids
        for i in range(len(snapshot_x)-1):
            # Create trapezoid
            x_points = [snapshot_x[i], snapshot_x[i], snapshot_x[i+1], snapshot_x[i+1]]
            y_points = [0, snapshot_y[i], snapshot_y[i+1], 0]
            trapezoid = Polygon(np.column_stack([x_points, y_points]), 
                               facecolor=self.colors['trapezoids'], alpha=0.3)
            ax.add_patch(trapezoid)
            
            # Add time interval arrows (x-axis)
            interval = snapshot_x[i+1] - snapshot_x[i]
            mid_x = (snapshot_x[i] + snapshot_x[i+1]) / 2
            ax.arrow(snapshot_x[i], -0.3, interval * 0.9, 0, head_width=0.1, 
                    head_length=interval * 0.1, fc=self.colors['intervals'], ec=self.colors['intervals'])
            ax.text(mid_x, -0.5, f"Δt = {interval:.1f}s", ha='center', color=self.colors['intervals'])
            
            # Add complexity arrows (y-axis)
            complexity = snapshot_y[i]
            ax.arrow(snapshot_x[i] - 0.2, 0, 0, complexity * 0.9, head_width=0.1, 
                    head_length=complexity * 0.1, fc=self.colors['complexity'], ec=self.colors['complexity'])
            ax.text(snapshot_x[i] - 0.4, complexity/2, f"Complexity\n{int(complexity*10)} props", 
                   va='center', ha='right', color=self.colors['complexity'])
        
        # Add snapshot rectangles
        for i, (xs, ys) in enumerate(zip(snapshot_x, snapshot_y)):
            rect_width, rect_height = 0.3, 0.4
            rect = plt.Rectangle((xs - rect_width/2, ys + 0.2), rect_width, rect_height, 
                                 facecolor=self.colors['snapshots'], alpha=0.9, edgecolor='black')
            ax.add_patch(rect)
            ax.text(xs, ys + 0.4, f"JSON\n{i+1}", ha='center', va='center', color='black', fontsize=8)
        
        # Plot the discrete points
        ax.scatter(snapshot_x, snapshot_y, color=self.colors['snapshots'], s=80, zorder=5, label="Snapshots")
        
        # Add a tangent line (derivative) at a specific point
        tangent_x = 4
        tangent_idx = np.abs(x - tangent_x).argmin()
        # Approximate derivative
        h = 0.01
        derivative = (true_curve[tangent_idx + 1] - true_curve[tangent_idx - 1]) / (x[tangent_idx + 1] - x[tangent_idx - 1])
        
        # Plot tangent line
        tangent_line_x = np.array([tangent_x - 1, tangent_x + 1])
        tangent_line_y = true_curve[tangent_idx] + derivative * (tangent_line_x - tangent_x)
        ax.plot(tangent_line_x, tangent_line_y, color=self.colors['slope'], linestyle='--', linewidth=2,
               label="Instantaneous Change")
        
        # Add labels and title
        ax.set_xlabel('Time (seconds)', fontsize=12)
        ax.set_ylabel('Game State Complexity', fontsize=12)
        ax.set_title('Game State Logging as Calculus: The Trapezoid Method', fontsize=16)
        
        # Add explanatory text
        explanation = """
        This visualization shows how game state logging is similar to calculus concepts:
        
        • Blue Line: True continuous player state (like a function in calculus)
        • Yellow Points: Discrete snapshots we capture (like sampling points)
        • Blue Areas: Trapezoids that approximate the true player experience
        • Green Arrows: Time intervals between snapshots (Δt)
        • Purple Arrows: Data complexity of each snapshot
        • Red Line: Instantaneous rate of change (like a derivative)
        
        Just as the trapezoid method approximates the area under a curve,
        our snapshots approximate the player's true game experience.
        """
        plt.figtext(0.5, 0.01, explanation, ha="center", fontsize=10, 
                  bbox={"facecolor":"white", "alpha":0.8, "pad":5})
        
        # Add grid and legend
        ax.grid(linestyle='--', alpha=0.7)
        ax.legend(loc='upper left')
        
        # Set y-axis to start at 0
        ax.set_ylim(bottom=-0.6)
        
        # Save or show
        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            return save_path
        else:
            plt.tight_layout()
            plt.show()
        
        return fig
    
    def visualize_session_data(self, session_id=None, metric_name="player_health", save_path=None):
        """
        Create a visualization of actual game data using the calculus analogy.
        
        Args:
            session_id: The session ID to analyze (loads most recent if None)
            metric_name: The metric to analyze (e.g., "player_health", "enemy_count")
            save_path: Where to save the figure (displays if None)
        """
        # Get session data
        if session_id is None:
            # Get most recent session
            sessions = self.logger.get_cached_sessions()
            if not sessions:
                return None
            session_id = sessions[-1]['session_id']
            
        # Load session logs
        logs = self.logger.load_session_logs(session_id)
        if not logs:
            return None
        
        # Extract timestamps and the specified metric
        timestamps = []
        values = []
        
        for log in logs:
            # Check if this is a snapshot log with game state data
            if 'snapshot' in log and 'timestamp' in log:
                # For simplicity, we'll handle a few common metrics
                if metric_name == "player_health" and 'player' in log['snapshot']:
                    if 'health' in log['snapshot']['player']:
                        timestamps.append(log['timestamp'])
                        values.append(log['snapshot']['player']['health'])
                        
                elif metric_name == "enemy_count" and 'enemies' in log['snapshot']:
                    timestamps.append(log['timestamp'])
                    values.append(len(log['snapshot']['enemies']))
                    
                elif metric_name == "player_x" and 'player' in log['snapshot']:
                    if 'x' in log['snapshot']['player']:
                        timestamps.append(log['timestamp'])
                        values.append(log['snapshot']['player']['x'])
                        
                # Add more metrics as needed
        
        if not timestamps or not values:
            print(f"No data found for metric: {metric_name}")
            return None
            
        # Convert to relative timestamps (starting from 0)
        start_time = min(timestamps)
        rel_timestamps = [t - start_time for t in timestamps]
        
        # Create figure
        fig, ax = plt.subplots(figsize=self.fig_size, dpi=self.dpi)
        
        # Plot the discrete points
        ax.scatter(rel_timestamps, values, color=self.colors['snapshots'], s=80, zorder=5, label="Snapshots")
        
        # Create a smooth curve approximation using spline interpolation (if we have enough points)
        if len(rel_timestamps) > 3:
            # Sort data by timestamps to ensure proper interpolation
            sorted_indices = np.argsort(rel_timestamps)
            sorted_times = np.array(rel_timestamps)[sorted_indices]
            sorted_values = np.array(values)[sorted_indices]
            
            # Create spline model for smoother curve
            x_smooth = np.linspace(min(sorted_times), max(sorted_times), 500)
            try:
                spline = make_interp_spline(sorted_times, sorted_values, k=min(3, len(sorted_times)-1))
                y_smooth = spline(x_smooth)
                ax.plot(x_smooth, y_smooth, color=self.colors['curve'], linewidth=2.5, label="Estimated True State")
                
                # Draw trapezoids
                for i in range(len(sorted_times)-1):
                    x_points = [sorted_times[i], sorted_times[i], sorted_times[i+1], sorted_times[i+1]]
                    y_points = [0, sorted_values[i], sorted_values[i+1], 0]
                    trapezoid = Polygon(np.column_stack([x_points, y_points]), 
                                      facecolor=self.colors['trapezoids'], alpha=0.3)
                    ax.add_patch(trapezoid)
            except:
                # Fall back to simple line if spline fails
                ax.plot(sorted_times, sorted_values, color=self.colors['curve'], linewidth=2.5, label="Estimated True State")
        else:
            # Just connect the dots with straight lines if too few points
            ax.plot(rel_timestamps, values, color=self.colors['curve'], linewidth=2.5, label="Estimated True State")
        
        # Add labels and title
        ax.set_xlabel('Time (seconds)', fontsize=12)
        ax.set_ylabel(f'{metric_name.replace("_", " ").title()}', fontsize=12)
        ax.set_title(f'Game State Analysis: {metric_name.replace("_", " ").title()} Over Time', fontsize=16)
        
        # Add grid and legend
        ax.grid(linestyle='--', alpha=0.7)
        ax.legend(loc='best')
        
        # Set y-axis to start at 0 if all values are positive
        if min(values) >= 0:
            ax.set_ylim(bottom=0)
        
        # Save or show
        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            return save_path
        else:
            plt.tight_layout()
            plt.show()
        
        return fig
    
    def analyze_derivative(self, session_id=None, metric_name="player_health", window_size=3, save_path=None):
        """
        Analyze the rate of change (derivative) of a specific metric over time.
        
        Args:
            session_id: The session ID to analyze (loads most recent if None)
            metric_name: The metric to analyze
            window_size: Size of the window for calculating finite differences
            save_path: Where to save the figure (displays if None)
        """
        # Get session data
        if session_id is None:
            # Get most recent session
            sessions = self.logger.get_cached_sessions()
            if not sessions:
                return None
            session_id = sessions[-1]['session_id']
            
        # Load session logs
        logs = self.logger.load_session_logs(session_id)
        if not logs:
            return None
        
        # Extract timestamps and the specified metric
        timestamps = []
        values = []
        
        for log in logs:
            # Similar extraction as visualize_session_data
            if 'snapshot' in log and 'timestamp' in log:
                if metric_name == "player_health" and 'player' in log['snapshot']:
                    if 'health' in log['snapshot']['player']:
                        timestamps.append(log['timestamp'])
                        values.append(log['snapshot']['player']['health'])
                # Add more metrics as needed
        
        if not timestamps or not values:
            print(f"No data found for metric: {metric_name}")
            return None
            
        # Convert to relative timestamps (starting from 0)
        start_time = min(timestamps)
        rel_timestamps = [t - start_time for t in timestamps]
        
        # Sort data by timestamps
        sorted_indices = np.argsort(rel_timestamps)
        sorted_times = np.array(rel_timestamps)[sorted_indices]
        sorted_values = np.array(values)[sorted_indices]
        
        # Calculate finite differences (derivatives)
        derivatives = []
        derivative_times = []
        
        for i in range(window_size, len(sorted_times)):
            # Calculate derivative using finite difference over the window
            dx = sorted_times[i] - sorted_times[i-window_size]
            dy = sorted_values[i] - sorted_values[i-window_size]
            if dx != 0:  # Avoid division by zero
                derivative = dy / dx
                derivatives.append(derivative)
                derivative_times.append(sorted_times[i-window_size//2])  # Use middle of window
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.fig_size, dpi=self.dpi, sharex=True)
        
        # Plot the original values
        ax1.scatter(sorted_times, sorted_values, color=self.colors['snapshots'], s=60, alpha=0.7, label="Snapshots")
        ax1.plot(sorted_times, sorted_values, color=self.colors['curve'], linewidth=2, label="Value")
        ax1.set_ylabel(f'{metric_name.replace("_", " ").title()}', fontsize=12)
        ax1.set_title(f'Game State Analysis: {metric_name.replace("_", " ").title()} and Rate of Change', fontsize=16)
        ax1.grid(linestyle='--', alpha=0.7)
        ax1.legend(loc='best')
        
        # Plot the derivatives
        ax2.scatter(derivative_times, derivatives, color=self.colors['slope'], s=60, alpha=0.7)
        ax2.plot(derivative_times, derivatives, color=self.colors['slope'], linewidth=2, label="Rate of Change")
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax2.set_xlabel('Time (seconds)', fontsize=12)
        ax2.set_ylabel(f'Change in {metric_name.replace("_", " ")} / second', fontsize=12)
        ax2.grid(linestyle='--', alpha=0.7)
        ax2.legend(loc='best')
        
        # Add explanatory text
        explanation = """
        The top graph shows the actual values recorded in snapshots.
        The bottom graph shows the rate of change (derivative) - how quickly the value is changing.
        Positive values mean increasing, negative values mean decreasing, and zero means stable.
        """
        plt.figtext(0.5, 0.01, explanation, ha="center", fontsize=10, 
                  bbox={"facecolor":"white", "alpha":0.8, "pad":5})
        
        # Save or show
        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            return save_path
        else:
            plt.tight_layout()
            plt.show()
        
        return fig


def demonstrate_analogy():
    """Create and save the calculus analogy visualization."""
    visualizer = GameStateVisualizer()
    save_path = os.path.join('logs', 'exports', 'calculus_analogy.png')
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    visualizer.visualize_calculus_analogy(save_path)
    print(f"Calculus analogy visualization saved to: {save_path}")
    return save_path


if __name__ == "__main__":
    demonstrate_analogy()
