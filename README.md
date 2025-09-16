# Blender Animation Transfer

A Python script for transferring animations between Blender files with support for rig scaling. Transfer animations from one .blend file to another with automatic bone mapping and scaling adjustments for rigs of different sizes.

## Features

- **Animation Transfer**: Copy animations between different .blend files
- **Automatic Rig Scaling**: Scale animations for rigs that are 70% (or any percentage) of the original size
- **Simple Bone Mapping**: Maps bones with identical names between source and target rigs
- **Directory Processing**: Batch process multiple .blend files from a directory
- **Safety Monitoring**: Memory and timeout limits to prevent system issues
- **Flexible Input**: Accept single files or entire directories of .blend files
- **Organized Output**: Creates output files with descriptive names in source directory

## Requirements

- **Blender 4.0+** (command-line interface)
- **Python 3.8+** with virtual environment
- **psutil** (for safety monitoring)

## Installation

1. Clone this repository:

   ```bash
   git clone <repository-url>
   cd blender-transfer-animation
   ```

2. Set up Python environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Quick Start

### Basic Usage - Single File

Transfer animation from one .blend file to another:

```bash
.venv/bin/python transfer_animation.py source.blend target.blend
```

### Directory Processing

Process multiple .blend files in a directory:

```bash
.venv/bin/python transfer_animation.py source_directory/ target.blend
```

### Advanced Options

```bash
# Custom scale factor
.venv/bin/python transfer_animation.py source.blend target.blend --scale 0.5

# Custom safety limits
.venv/bin/python transfer_animation.py source.blend target.blend --timeout 300 --max-memory 2048

# Continue processing on errors (for directories)
.venv/bin/python transfer_animation.py source_dir/ target.blend --continue-on-error
```

### Output Files

Output files are created in the same directory as the source file(s) with the naming pattern:

- `source_name_to_target_name.blend`

## Command Line Options

- `source`: Source .blend file or directory containing .blend files
- `target`: Target .blend file (rig to receive animations)  
- `--scale, -s`: Scale factor (default: 0.7)
- `--timeout, -t`: Timeout in seconds (default: 600)
- `--max-memory`: Max memory in MB (default: 4096)
- `--max-frames`: Max frames to process (default: 10000)
- `--max-bones`: Max bones to process (default: 1000)
- `--blender, -b`: Blender executable path (default: "blender")
- `--continue-on-error`: Continue processing other files if one fails

## Project Structure

```text
blender-animation-transfer/
├── .github/
│   └── copilot-instructions.md  # Development guidelines
├── .venv/                       # Python virtual environment
├── transfer_animation.py        # Main animation transfer script
├── requirements.txt             # Python dependencies
├── pyproject.toml               # Project configuration
└── README.md                    # This file
```

## How It Works

The `transfer_animation.py` script works as a standalone Python program that controls Blender externally:

### 1. External Process Control

- The script runs outside of Blender in your system Python environment
- It generates temporary Blender Python scripts and executes them via command-line
- Safety monitoring tracks memory usage, timeouts, and process health

### 2. Data Loading and Preparation

- Blender loads the target .blend file containing the destination rig
- The script generates code to append armatures and actions from the source .blend file
- Uses Blender's `bpy.data.libraries.load()` to import data without linking

### 3. Simple Bone Mapping

- **Direct Name Matching**: Maps bones with identical names between source and target rigs
- No complex analysis - relies on consistent bone naming conventions
- Creates a dictionary mapping source bone names to target bone names

### 4. Frame-by-Frame Animation Transfer

- Processes each frame sequentially from the source animation's frame range
- For each frame, sets the scene frame and reads bone transformations
- Applies scaling to location properties, copies rotation and scale unchanged
- Uses direct keyframe insertion: `target_bone.keyframe_insert()`

### 5. Scaling and Safety

- **Location Properties**: Multiplied by scale factor (e.g., 0.7 for 70% scaling)
- **Rotation Properties**: Copied unchanged (preserves animation style)  
- **Scale Properties**: Copied unchanged (maintains proportions)
- **Safety Monitoring**: Prevents infinite loops, memory overruns, and timeouts

## Customization

### Scaling Factors

You can use any scale factor via the command line:

```bash
# 50% scale
.venv/bin/python transfer_animation.py source.blend target.blend --scale 0.5

# 120% scale (upscaling)
.venv/bin/python transfer_animation.py source.blend target.blend --scale 1.2

# 30% scale (very small rig)
.venv/bin/python transfer_animation.py source.blend target.blend --scale 0.3
```

### Safety Limits

Adjust safety monitoring limits:

```bash
# Longer timeout for complex animations
.venv/bin/python transfer_animation.py source.blend target.blend --timeout 1200

# Higher memory limit for large rigs
.venv/bin/python transfer_animation.py source.blend target.blend --max-memory 8192

# Limit processing scope for safety
.venv/bin/python transfer_animation.py source.blend target.blend --max-frames 5000 --max-bones 500
```

### Batch Processing Options

```bash
# Continue processing even if some files fail
.venv/bin/python transfer_animation.py source_directory/ target.blend --continue-on-error

# Use custom Blender executable
.venv/bin/python transfer_animation.py source.blend target.blend --blender /path/to/blender
```

## Troubleshooting

### Common Issues

1. **"No target armature found"**
   - Ensure your target .blend file contains an armature object
   - The script looks for objects with type 'ARMATURE' in the scene

2. **"No source armature found"**
   - Check that the source .blend file contains armatures
   - Verify the source file path is correct and accessible

3. **"No animation data found"**
   - The source armature must have animation data assigned
   - Check that the source file contains action objects with keyframes

4. **Memory or timeout errors**
   - Use `--max-memory` to increase memory limits
   - Use `--timeout` to allow longer processing time
   - Try `--max-frames` and `--max-bones` to limit scope

5. **"Process appears to be stuck"**
   - Large animations may take time - the script shows progress every 100 frames
   - Consider using smaller frame ranges or fewer bones for testing

### Getting Debug Information

The script provides detailed output including:

- Frame processing progress every 100 frames
- Memory usage monitoring
- Bone mapping counts
- Keyframe transfer statistics

Run with verbose output:

```bash
.venv/bin/python transfer_animation.py source.blend target.blend 2>&1 | tee transfer.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test in Blender
5. Submit a pull request

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Credits

Created for Blender animation workflow optimization. Uses Blender's Python API (bpy) for internal animation processing via external process control.

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Test with simple .blend files first
3. Open an issue on the project repository

---

**Note**: This script runs externally and controls Blender via command-line interface. It does not need to be run inside Blender.
