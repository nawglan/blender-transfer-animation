#!/usr/bin/env python3
"""
Standalone Blender Animation Transfer Tool

This script runs Blender in background mode to transfer animations between .blend files
with proper rig scaling and safety monitoring.
"""

import subprocess
import tempfile
import os
import sys
import argparse
from pathlib import Path
import json
import time
import psutil
from threading import Timer
import shutil
import glob


def create_blender_script(source_blend: str, scale_factor: float = 0.7, 
                         max_frames: int = 10000, max_bones: int = 1000, 
                         max_memory_mb: int = 4096) -> str:
    """Create the Blender Python script content."""
    
    script_content = f'''
import bpy
import bmesh
import mathutils
from mathutils import Vector, Matrix, Euler
import os
import sys
import time
import gc

# Safety configuration
MAX_FRAME_RANGE = {max_frames}
MAX_BONES = {max_bones}
MAX_MEMORY_MB = {max_memory_mb}
PROGRESS_INTERVAL = 100

class SafetyMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.last_progress = time.time()
        self.frame_count = 0
        self.bone_count = 0
    
    def check_timeout(self, max_seconds=300):
        elapsed = time.time() - self.start_time
        if elapsed > max_seconds:
            raise RuntimeError(f"Operation timed out after {{elapsed:.1f}} seconds")
    
    def check_memory(self, max_mb=MAX_MEMORY_MB):
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            if memory_mb > max_mb:
                raise RuntimeError(f"Memory usage exceeded {{max_mb}}MB (current: {{memory_mb:.1f}}MB)")
        except ImportError:
            pass
    
    def check_progress(self, current_frame=None):
        now = time.time()
        if now - self.last_progress > 30:
            raise RuntimeError("Operation appears to be stuck (no progress for 30 seconds)")
        
        if current_frame is not None:
            self.frame_count += 1
            if self.frame_count % PROGRESS_INTERVAL == 0:
                print(f"Processed frame {{current_frame}} ({{self.frame_count}} total frames)")
                self.last_progress = now
                gc.collect()
    
    def update_progress(self):
        self.last_progress = time.time()

def main():
    print("=== Blender Animation Transfer Started ===")
    
    monitor = SafetyMonitor()
    source_file = r"{source_blend}"
    scale_factor = {scale_factor}
    
    print(f"Source file: {{source_file}}")
    print(f"Scale factor: {{scale_factor}}")
    
    try:
        # Find target armature
        monitor.check_timeout()
        monitor.check_memory()
        
        target_armature = None
        for obj in bpy.context.scene.objects:
            if obj.type == 'ARMATURE':
                target_armature = obj
                break
        
        if not target_armature:
            print("ERROR: No target armature found!")
            return False
        
        print(f"Target armature: {{target_armature.name}}")
        monitor.update_progress()
        
        # Append source data
        print("Appending source armature and animations...")
        monitor.check_timeout()
        
        with bpy.data.libraries.load(source_file, link=False) as (data_from, data_to):
            data_to.objects = data_from.objects
            data_to.actions = data_from.actions
            data_to.armatures = data_from.armatures
        
        monitor.update_progress()
        
        # Find source armature
        source_armature = None
        imported_objects = []
        
        for obj in bpy.data.objects:
            monitor.check_timeout()
            if obj.name not in bpy.context.scene.objects:
                bpy.context.scene.collection.objects.link(obj)
                imported_objects.append(obj)
                
                if obj.type == 'ARMATURE' and obj != target_armature:
                    source_armature = obj
                    print(f"Found source armature: {{obj.name}}")
        
        if not source_armature:
            print("ERROR: No source armature found!")
            return False
        
        monitor.update_progress()
        
        # Get animation data
        if not source_armature.animation_data or not source_armature.animation_data.action:
            print("ERROR: No animation data found!")
            available_actions = [action for action in bpy.data.actions]
            print(f"Available actions: {{[a.name for a in available_actions]}}")
            
            if available_actions:
                if not source_armature.animation_data:
                    source_armature.animation_data_create()
                source_armature.animation_data.action = available_actions[0]
                print(f"Assigned action: {{available_actions[0].name}}")
            else:
                return False
        
        source_action = source_armature.animation_data.action
        print(f"Source action: {{source_action.name}}")
        
        # Show source action frame range info
        if source_action.frame_range:
            src_start, src_end = source_action.frame_range
            print(f"Source action frame range: {{int(src_start)}} to {{int(src_end)}} ({{int(src_end - src_start + 1)}} frames)")
        else:
            print("Source action has no explicit frame range, using scene range")
        
        monitor.update_progress()
        
        # Create target action
        target_action_name = f"{{source_action.name}}_scaled"
        target_action = bpy.data.actions.new(target_action_name)
        
        if not target_armature.animation_data:
            target_armature.animation_data_create()
        
        target_armature.animation_data.action = target_action
        print(f"Created target action: {{target_action_name}}")
        monitor.update_progress()
        
        # Set pose mode
        bpy.context.view_layer.objects.active = target_armature
        bpy.ops.object.mode_set(mode='POSE')
        monitor.update_progress()
        
        # Create bone mapping
        print("Creating bone mapping...")
        monitor.check_timeout()
        monitor.check_memory()
        
        bone_mapping = {{}}
        source_bone_names = [bone.name for bone in source_armature.pose.bones]
        target_bone_names = [bone.name for bone in target_armature.pose.bones]
        
        if len(source_bone_names) > MAX_BONES or len(target_bone_names) > MAX_BONES:
            print(f"WARNING: Large number of bones (Source: {{len(source_bone_names)}}, Target: {{len(target_bone_names)}})")
            if len(source_bone_names) > MAX_BONES * 2 or len(target_bone_names) > MAX_BONES * 2:
                print("ERROR: Too many bones for safe processing")
                return False
        
        for source_bone_name in source_bone_names:
            monitor.check_timeout()
            if source_bone_name in target_bone_names:
                bone_mapping[source_bone_name] = source_bone_name
        
        print(f"Bone mapping created: {{len(bone_mapping)}} bones mapped")
        
        # Copy keyframes with scaling
        print("Copying and scaling keyframes...")
        monitor.check_timeout()
        monitor.check_memory()
        
        if source_action.frame_range:
            start_frame = int(source_action.frame_range[0])
            end_frame = int(source_action.frame_range[1])
        else:
            start_frame = bpy.context.scene.frame_start
            end_frame = bpy.context.scene.frame_end
        
        frame_count = end_frame - start_frame + 1
        if frame_count > MAX_FRAME_RANGE:
            print(f"WARNING: Large frame range: {{frame_count}} frames")
            if frame_count > MAX_FRAME_RANGE * 2:
                print("ERROR: Frame range too large")
                return False
        
        print(f"Processing frames {{start_frame}} to {{end_frame}} ({{frame_count}} frames)")
        
        # IMPORTANT: Extend target scene frame range to match source animation
        original_start = bpy.context.scene.frame_start
        original_end = bpy.context.scene.frame_end
        
        print(f"Original scene range: {{original_start}} to {{original_end}}")
        
        # Set scene frame range to accommodate the full animation
        bpy.context.scene.frame_start = start_frame
        bpy.context.scene.frame_end = end_frame
        
        print(f"Extended scene range to: {{start_frame}} to {{end_frame}}")
        
        keyframes_copied = 0
        bones_per_frame = len(bone_mapping)
        total_operations = frame_count * bones_per_frame
        
        print(f"Total operations: {{total_operations:,}}")
        
        for frame_idx, frame in enumerate(range(start_frame, end_frame + 1)):
            monitor.check_timeout(max_seconds=600)
            monitor.check_progress(frame)
            
            if frame_idx % 100 == 0:
                monitor.check_memory()
                progress_pct = (frame_idx / frame_count) * 100
                print(f"Progress: {{progress_pct:.1f}}% (Frame {{frame}}/{{end_frame}})")
            
            bpy.context.scene.frame_set(frame)
            
            for bone_idx, (source_bone_name, target_bone_name) in enumerate(bone_mapping.items()):
                if bone_idx % 50 == 0:
                    monitor.check_timeout(max_seconds=600)
                
                if (target_bone_name in target_armature.pose.bones and 
                    source_bone_name in source_armature.pose.bones):
                    
                    source_bone = source_armature.pose.bones[source_bone_name]
                    target_bone = target_armature.pose.bones[target_bone_name]
                    
                    # Scale location
                    scaled_location = source_bone.location.copy()
                    scaled_location *= scale_factor
                    target_bone.location = scaled_location
                    target_bone.keyframe_insert(data_path="location", frame=frame)
                    
                    # Copy rotation
                    target_bone.rotation_quaternion = source_bone.rotation_quaternion.copy()
                    target_bone.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                    
                    # Copy scale
                    target_bone.scale = source_bone.scale.copy()
                    target_bone.keyframe_insert(data_path="scale", frame=frame)
                    
                    keyframes_copied += 1
            
            if frame_idx % 500 == 0:
                gc.collect()
        
        print(f"✓ Copied and scaled {{keyframes_copied:,}} keyframes")
        
        # Update target action frame range to match what we just created
        target_action.frame_range = (start_frame, end_frame)
        print(f"Set target action frame range: {{start_frame}} to {{end_frame}}")
        
        # Cleanup
        print("Cleaning up...")
        monitor.check_timeout()
        
        bpy.ops.object.mode_set(mode='OBJECT')
        
        for obj in imported_objects:
            monitor.check_timeout()
            bpy.data.objects.remove(obj, do_unlink=True)
        
        print("=== Animation Transfer Completed Successfully ===")
        print(f"New action created: {{target_action_name}}")
        print(f"Total processing time: {{time.time() - monitor.start_time:.1f}} seconds")
        print("RESULT: SUCCESS")
        return True
    
    except RuntimeError as e:
        print(f"SAFETY ERROR: {{e}}")
        print("RESULT: FAILED")
        return False
    except MemoryError:
        print("ERROR: Out of memory")
        print("RESULT: FAILED")
        return False
    except Exception as e:
        print(f"UNEXPECTED ERROR: {{e}}")
        import traceback
        traceback.print_exc()
        print("RESULT: FAILED")
        return False
    finally:
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            pass

if __name__ == "__main__":
    success = main()
    if success:
        bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
        sys.exit(0)
    else:
        sys.exit(1)
'''
    
    return script_content


def create_output_filename(source_path: str, target_path: str) -> str:
    """
    Create output filename based on source file, placed in source directory.
    
    Args:
        source_path: Path to source .blend file
        target_path: Path to target .blend file
        
    Returns:
        Path for the output file
    """
    source_dir = os.path.dirname(source_path)
    source_name = os.path.splitext(os.path.basename(source_path))[0]
    target_name = os.path.splitext(os.path.basename(target_path))[0]
    
    # Create output filename: source_name + "_to_" + target_name + ".blend"
    output_name = f"{source_name}_to_{target_name}.blend"
    output_path = os.path.join(source_dir, output_name)
    
    return output_path


def copy_target_file(target_path: str, output_path: str) -> bool:
    """
    Copy target file to output location.
    
    Args:
        target_path: Original target file
        output_path: Where to copy it
        
    Returns:
        True if successful
    """
    try:
        print(f"Creating copy: {output_path}")
        shutil.copy2(target_path, output_path)
        return True
    except Exception as e:
        print(f"ERROR: Failed to copy target file: {e}")
        return False


def find_blend_files(path: str) -> list:
    """
    Find .blend files in a path (file or directory).
    
    Args:
        path: File path or directory path
        
    Returns:
        List of .blend file paths
    """
    if os.path.isfile(path):
        if path.lower().endswith('.blend'):
            return [path]
        else:
            print(f"ERROR: {path} is not a .blend file")
            return []
    elif os.path.isdir(path):
        # Find all .blend files in directory
        blend_files = []
        for pattern in ['*.blend', '*.BLEND']:
            blend_files.extend(glob.glob(os.path.join(path, pattern)))
        
        # Sort for consistent ordering
        blend_files.sort()
        print(f"Found {len(blend_files)} .blend files in {path}")
        for f in blend_files:
            print(f"  - {os.path.basename(f)}")
        
        return blend_files
    else:
        print(f"ERROR: {path} does not exist")
        return []


def process_single_transfer(source_file: str, target_file: str, args) -> bool:
    """
    Process a single animation transfer.
    
    Args:
        source_file: Source .blend file
        target_file: Target .blend file  
        args: Command line arguments
        
    Returns:
        True if successful
    """
    print(f"\n{'='*60}")
    print(f"Processing: {os.path.basename(source_file)}")
    print(f"{'='*60}")
    
    # Create output filename and copy target
    output_file = create_output_filename(source_file, target_file)
    
    if not copy_target_file(target_file, output_file):
        return False
    
    # Create temp script
    script_content = create_blender_script(
        source_file, args.scale, args.max_frames, args.max_bones, args.max_memory
    )
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script_content)
        temp_script = f.name
    
    try:
        # Run Blender on the output file
        cmd = [args.blender, output_file, "--background", "--python", temp_script]
        print(f"Running: {' '.join([args.blender, os.path.basename(output_file), '--background', '--python', 'temp_script.py'])}")
        
        start_time = time.time()
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Monitor process
        while process.poll() is None:
            elapsed = time.time() - start_time
            if elapsed > args.timeout:
                print(f"ERROR: Timeout after {elapsed:.1f} seconds")
                process.terminate()
                process.wait(timeout=5)
                if process.poll() is None:
                    process.kill()
                return False
            
            # Check memory
            try:
                proc_info = psutil.Process(process.pid)
                memory_mb = proc_info.memory_info().rss / 1024 / 1024
                
                if memory_mb > args.max_memory:
                    print(f"ERROR: Memory exceeded {args.max_memory}MB ({memory_mb:.1f}MB)")
                    process.terminate()
                    process.wait(timeout=5)
                    if process.poll() is None:
                        process.kill()
                    return False
                
                if int(elapsed) % 30 == 0 and elapsed > 0:
                    print(f"Progress: {elapsed:.0f}s, {memory_mb:.1f}MB")
            
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            
            time.sleep(0.1)
        
        stdout, stderr = process.communicate()
        
        print("=== Blender Output ===")
        print(stdout)
        if stderr:
            print("=== Blender Errors ===")
            print(stderr)
        
        if process.returncode == 0 and "RESULT: SUCCESS" in stdout:
            elapsed = time.time() - start_time
            print(f"✓ Success in {elapsed:.1f} seconds!")
            print(f"Output file: {output_file}")
            return True
        else:
            print("✗ Failed!")
            # Clean up failed output file
            if os.path.exists(output_file):
                os.remove(output_file)
            return False
    
    finally:
        if os.path.exists(temp_script):
            os.unlink(temp_script)


def main():
    """Enhanced command line interface with file and directory support."""
    parser = argparse.ArgumentParser(
        description="Transfer animations between Blender files with rig scaling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single file transfer
  python transfer_animation.py source.blend target.blend --scale 0.7
  
  # Directory of source files to single target
  python transfer_animation.py source_dir/ target.blend --scale 0.7
  
  # Custom safety limits
  python transfer_animation.py source.blend target.blend --scale 0.7 --timeout 600 --max-memory 4096

Output files are created in the same directory as the source file(s) with names like:
  source_name_to_target_name.blend
        """
    )
    
    parser.add_argument("source", help="Source .blend file or directory containing .blend files")
    parser.add_argument("target", help="Target .blend file (rig to receive animations)")
    parser.add_argument("--scale", "-s", type=float, default=0.7, help="Scale factor (default: 0.7)")
    parser.add_argument("--timeout", "-t", type=int, default=600, help="Timeout in seconds")
    parser.add_argument("--max-memory", type=int, default=4096, help="Max memory in MB")
    parser.add_argument("--max-frames", type=int, default=10000, help="Max frames to process")
    parser.add_argument("--max-bones", type=int, default=1000, help="Max bones to process")
    parser.add_argument("--blender", "-b", default="blender", help="Blender executable path")
    parser.add_argument("--continue-on-error", action="store_true", 
                       help="Continue processing other files if one fails")
    
    args = parser.parse_args()
    
    print("Blender Animation Transfer Tool")
    print("=" * 50)
    print(f"Source: {args.source}")
    print(f"Target: {args.target}")
    print(f"Scale: {args.scale}")
    print(f"Safety limits: {args.timeout}s timeout, {args.max_memory}MB memory")
    
    # Validate target file
    if not os.path.exists(args.target):
        print(f"ERROR: Target file not found: {args.target}")
        sys.exit(1)
    
    if not args.target.lower().endswith('.blend'):
        print(f"ERROR: Target file must be a .blend file: {args.target}")
        sys.exit(1)
    
    # Find source files
    source_files = find_blend_files(args.source)
    if not source_files:
        print("ERROR: No valid .blend source files found")
        sys.exit(1)
    
    print(f"\nProcessing {len(source_files)} source file(s)...")
    
    # Process each source file
    results = {}
    successful = 0
    
    for source_file in source_files:
        try:
            success = process_single_transfer(source_file, args.target, args)
            results[source_file] = success
            
            if success:
                successful += 1
            elif not args.continue_on_error:
                print(f"\nStopping due to failure. Use --continue-on-error to process remaining files.")
                break
                
        except KeyboardInterrupt:
            print(f"\n\nInterrupted by user")
            break
        except Exception as e:
            print(f"ERROR processing {source_file}: {e}")
            results[source_file] = False
            if not args.continue_on_error:
                break
    
    # Print summary
    print(f"\n{'='*60}")
    print("TRANSFER SUMMARY")
    print(f"{'='*60}")
    print(f"Successful: {successful}/{len(source_files)}")
    
    if results:
        print("\nResults:")
        for source_file, success in results.items():
            status = "✓" if success else "✗"
            print(f"{status} {os.path.basename(source_file)}")
            
            if success:
                output_file = create_output_filename(source_file, args.target)
                print(f"   → {output_file}")
    
    sys.exit(0 if successful == len(results) else 1)


if __name__ == "__main__":
    main()