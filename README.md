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
