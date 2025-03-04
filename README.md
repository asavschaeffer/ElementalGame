# Elemental Game

A combat game with elemental progression mechanics:

1. Water enemies splash you for small damage, increasing your water resistance
2. Lava enemies do massive damage, but water resistance helps you survive them
3. Obsidian armor forms when lava interacts with your wet character
4. The final abyss area requires obsidian armor to damage enemies

## Setup

```
pip install -r requirements.txt
python main.py
```

## Game Mechanics

- **Health**: Player starts with limited health
- **Wetness**: Increases when hit by water enemies, provides fire resistance
- **Obsidian Armor**: Forms when lava hits a wet player, required for the abyss
- **Areas**: Beach → Volcano → Abyss

## Performance Optimization

For improved game performance, you can enable logging optimization:

```
# Windows
set OPTIMIZE_LOGGING=true
python main.py

# Linux/Mac
OPTIMIZE_LOGGING=true python main.py
```

This will reduce logging overhead while maintaining critical event tracking.

## Log Analysis Framework

The game includes a powerful log analysis system that can identify gameplay patterns and optimize performance:

```
# Basic usage - analyze most recent session
python analyze_logs.py

# Detect gameplay patterns
python analyze_logs.py --detect-patterns

# Optimize logs to reduce lag
python analyze_logs.py --optimize

# Analyze patterns across multiple sessions
python analyze_logs.py --cross-session

# List all available sessions
python analyze_logs.py --list-sessions
```

### Analysis Features

- **Pattern Detection**: Identifies common death locations, enemy behavior patterns, and player strategies
- **Log Optimization**: Reduces file system overhead and compresses old logs to improve performance
- **Cross-Session Analysis**: Aggregates data across multiple play sessions to identify trends
- **Visualization**: Creates graphs of player stats, enemy interactions, and game performance

### Advanced Options

```
# Analyze specific session
python analyze_logs.py --session SESSION_ID --detect-patterns

# Analyze specific metric
python analyze_logs.py --metric player_wetness

# Analyze rate of change of a metric
python analyze_logs.py --metric enemy_count --derivative

# Set maximum number of log files when optimizing
python analyze_logs.py --optimize --max-files 30

# Specify number of sessions for cross-session analysis
python analyze_logs.py --cross-session --session-limit 5
```

## Advanced Analytics System

The game now includes a sophisticated analytics system that provides deep insights into gameplay patterns:

```
# Generate a narrative description of your gameplay experience
python analyze_logs.py --narrative

# Analyze logs and detect patterns
python analyze_logs.py --eat-logs
```

### Analytics Features

- **Temporal Pattern Detection**: Identifies relationships between game events across time
- **Elemental Interaction Analysis**: Quantifies how wetness affects fire resistance and damage reduction
- **Game State Visualization**: Creates visual representations of player progression
- **Storyline Generation**: Converts raw gameplay data into a narrative experience

### Recursive Ouroboros Framework

The analytics system now includes a powerful recursive comparison framework:

```
# Compare two sessions recursively
python analyze_logs.py --compare-recursive

# Compare specific entities with temporal analysis
python analyze_logs.py --compare-recursive --entity1 SESSION_ID1 --entity2 SESSION_ID2 --compare-mode temporal

# Compare entities across different levels
python analyze_logs.py --compare-recursive --entity1 SNAPSHOT_ID --entity2 SESSION_ID --entity1-level snapshot --entity2-level session
```

#### Key Features of the Recursive Framework

The recursive framework enables deep pattern analysis across multiple log levels:

1. **Hierarchical Comparison**
   - Analyze relationships between any log entities (snapshots, sessions, exports)
   - Compare across hierarchy levels (e.g., a snapshot vs. an entire session)
   - Identify patterns that might be invisible when comparing at a single level

2. **Analysis Modes**
   - **Co-occurrence Mode** (default): Discovers relationships between data points regardless of when they occur
   - **Temporal Mode**: Examines how relationships evolve over time, tracking the sequence and timing of changes

3. **Pattern Detection Algorithms**
   - **Binary Tree Comparison**: Starts from the center and works outward for efficient pattern detection
   - **Related Change Detection**: Identifies data points that consistently change together
   - **Cross-Level Pattern Identification**: Finds recurring structures across different log hierarchies

#### Example Use Cases

- **Identify Game Balance Issues**: "Is water resistance consistently reducing lava damage as expected?"
- **Track Player Progression**: "How do player strategies evolve across multiple game sessions?"
- **Optimize Game Mechanics**: "Which environmental factors most influence player behavior?"
- **Debug Complex Interactions**: "What sequence of events leads to obsidian armor formation failures?"

#### Understanding Analysis Reports

The recursive analysis generates comprehensive reports with:

- Comparison summary detailing which entities were compared
- Visualization of top changes detected between entities
- Pattern frequency charts showing recurring relationships
- Temporal analysis of how patterns evolve over time

#### Advanced Configuration

For power users, the framework offers fine-grained control:

```
# Compare specific snapshots instead of sessions
python analyze_logs.py --compare-recursive --entity1 SNAPSHOT_ID1 --entity2 SNAPSHOT_ID2 --entity1-level snapshot --entity2-level snapshot

# Export comparison results for further analysis
python analyze_logs.py --compare-recursive --export-results

# Set depth limit for recursion (default: unlimited)
python analyze_logs.py --compare-recursive --max-depth 3
```

### Visualization

The analytics system can generate various visualizations to help understand gameplay patterns:

- Player attribute progression over time
- Elemental interaction matrices
- Damage source correlation networks
- Area transition flow diagrams

Run the visualizer directly:

```
python -m devtools.visualizer
```

## Logging System

The game features a comprehensive logging system that captures detailed information about gameplay:

- **Game State**: Regular snapshots of player stats, enemy positions, and game environment
- **Events**: Combat interactions, area transitions, and special events
- **Performance**: FPS tracking and memory usage monitoring
- **Death Statistics**: Detailed analysis of player deaths with cause identification

Log files are stored in the `logs/` directory with the following structure:

```
logs/
├── sessions/
│   └── session_YYYYMMDD_HHMMSS_PID/
│       ├── manifest.json      # Session metadata
│       ├── metadata.json      # Session results
│       ├── game_log.log       # Main log file
│       ├── snapshots/         # State snapshots
│       ├── duplets/           # Paired logs and snapshots
│       └── cache/             # Compressed log chunks
└── exports/                   # Analysis results
```

## Troubleshooting

If you experience lag during gameplay:

1. Run the log optimizer: `python analyze_logs.py --optimize`
2. Enable low-overhead logging: `set OPTIMIZE_LOGGING=true`
3. Close other applications that might be consuming system resources
4. Check the analysis reports for performance bottlenecks
