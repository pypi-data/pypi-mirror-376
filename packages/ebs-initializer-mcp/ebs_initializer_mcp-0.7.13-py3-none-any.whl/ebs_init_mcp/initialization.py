"""
EBS Volume Initialization Command Generation Module

This module handles the generation of shell commands for initializing EBS volumes
using different methods (fio or dd) and managing parallel execution.
"""

import logging
from typing import List, Dict, Any
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from utils import DEVICE_MAPPING_SCRIPT, get_install_command

logger = logging.getLogger(__name__)


def create_fio_command(volume_id: str, device: str, size_gb: int) -> str:
    """
    Create a fio command for volume initialization.
    
    Args:
        volume_id: EBS volume ID
        device: AWS device path
        size_gb: Volume size in GB
        
    Returns:
        Shell command string for fio initialization
    """
    return f"""(
ACTUAL_DEVICE=$(map_device_name "{device}" "{volume_id}")
echo "=== Volume {volume_id}: AWS device {device} mapped to actual device $ACTUAL_DEVICE ===" && \\
echo "=== Starting initialization of {volume_id} ($ACTUAL_DEVICE, {size_gb}GB) ===" && \\
sudo fio --filename="$ACTUAL_DEVICE" --rw=read --bs=1M --iodepth=32 \\
--ioengine=libaio --direct=1 --name=init-{volume_id} \\
--group_reporting && \\
echo "=== Completed {volume_id} ==="
) &"""


def create_dd_command(volume_id: str, device: str, size_gb: int) -> str:
    """
    Create a dd command for volume initialization.
    
    Args:
        volume_id: EBS volume ID
        device: AWS device path
        size_gb: Volume size in GB
        
    Returns:
        Shell command string for dd initialization
    """
    return f"""(
ACTUAL_DEVICE=$(map_device_name "{device}" "{volume_id}")
echo "=== Volume {volume_id}: AWS device {device} mapped to actual device $ACTUAL_DEVICE ===" && \\
echo "=== Starting initialization of {volume_id} ($ACTUAL_DEVICE, {size_gb}GB) ===" && \\
sudo dd if="$ACTUAL_DEVICE" of=/dev/null bs=1M status=progress && \\
echo "=== Completed {volume_id} ==="
) &"""


def create_filtered_fio_command(volume_id: str, device: str, size_gb: int) -> str:
    """
    Create a filtered fio command that only runs if the volume belongs to current instance.
    
    Args:
        volume_id: EBS volume ID
        device: AWS device path
        size_gb: Volume size in GB
        
    Returns:
        Shell command string for filtered fio initialization
    """
    return f"""# Check if {volume_id} belongs to current instance
if [[ "${{INSTANCE_VOLUMES["{volume_id}"]}}" == "$CURRENT_INSTANCE_ID" ]]; then
(
    ACTUAL_DEVICE=$(map_device_name "{device}" "{volume_id}")
    echo "=== Initializing {volume_id} (AWS: {device} -> Actual: $ACTUAL_DEVICE, {size_gb}GB) ===" && \\
    sudo fio --filename="$ACTUAL_DEVICE" --rw=read --bs=1M --iodepth=32 \\
        --ioengine=libaio --direct=1 --name=init-{volume_id} --group_reporting && \\
    echo "=== Completed {volume_id} ==="
) &
fi"""


def create_filtered_dd_command(volume_id: str, device: str, size_gb: int) -> str:
    """
    Create a filtered dd command that only runs if the volume belongs to current instance.
    
    Args:
        volume_id: EBS volume ID
        device: AWS device path
        size_gb: Volume size in GB
        
    Returns:
        Shell command string for filtered dd initialization
    """
    return f"""# Check if {volume_id} belongs to current instance
if [[ "${{INSTANCE_VOLUMES["{volume_id}"]}}" == "$CURRENT_INSTANCE_ID" ]]; then
(
    ACTUAL_DEVICE=$(map_device_name "{device}" "{volume_id}")
    echo "=== Initializing {volume_id} (AWS: {device} -> Actual: $ACTUAL_DEVICE, {size_gb}GB) ===" && \\
    sudo dd if="$ACTUAL_DEVICE" of=/dev/null bs=1M status=progress && \\
    echo "=== Completed {volume_id} ==="
) &
fi"""


def create_single_volume_command(volume_id: str, device: str, size_gb: int, method: str) -> str:
    """
    Create initialization command for a single volume (non-parallel).
    
    Args:
        volume_id: EBS volume ID
        device: AWS device path
        size_gb: Volume size in GB
        method: Initialization method ('fio' or 'dd')
        
    Returns:
        Shell command string for single volume initialization
    """
    if method == 'fio':
        return f"""ACTUAL_DEVICE=$(map_device_name "{device}" "{volume_id}")
echo "=== Volume {volume_id}: AWS device {device} mapped to actual device $ACTUAL_DEVICE ===" && \\
echo "=== Starting initialization of {volume_id} ($ACTUAL_DEVICE, {size_gb}GB) ===" && \\
sudo fio --filename="$ACTUAL_DEVICE" --rw=read --bs=1M --iodepth=32 \\
--ioengine=libaio --direct=1 --name=init-{volume_id} \\
--group_reporting && \\
echo "=== Completed {volume_id} ====" """
    else:  # dd method
        return f"""ACTUAL_DEVICE=$(map_device_name "{device}" "{volume_id}")
echo "=== Volume {volume_id}: AWS device {device} mapped to actual device $ACTUAL_DEVICE ===" && \\
echo "=== Starting initialization of {volume_id} ($ACTUAL_DEVICE, {size_gb}GB) ===" && \\
sudo dd if="$ACTUAL_DEVICE" of=/dev/null bs=1M status=progress && \\
echo "=== Completed {volume_id} ====" """


def build_initialization_commands(volume_list: List[Dict[str, Any]], method: str, 
                                parallel: bool = True) -> List[str]:
    """
    Build complete initialization command list for volumes.
    
    Args:
        volume_list: List of volume information dictionaries
        method: Initialization method ('fio' or 'dd')
        parallel: Whether to run volumes in parallel
        
    Returns:
        List of shell command strings
    """
    commands = []
    
    # Add shebang
    commands.append("#!/bin/bash")
    
    # Add package installation if needed
    install_cmd = get_install_command(method)
    if install_cmd:
        commands.append(install_cmd)
    
    # Add device mapping script
    commands.append(DEVICE_MAPPING_SCRIPT)
    commands.append('echo "Device mapping function ready"')
    
    if parallel and len(volume_list) > 1:
        # Group volumes by instance for multi-instance support
        instance_volumes = {}
        for volume in volume_list:
            instance_id = volume.get('instance_id')
            if instance_id not in instance_volumes:
                instance_volumes[instance_id] = []
            instance_volumes[instance_id].append(volume)
        
        # If multiple instances detected, use filtered commands with IMDS
        if len(instance_volumes) > 1:
            # Add IMDS support for multi-instance scenarios
            imds_script = """
# ==============================================================================
# Get current instance ID using IMDS (supports both v1 and v2)
# ==============================================================================
echo "=== Getting current instance ID from IMDS ==="

# Try IMDSv2 first (token-based)
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" -s --connect-timeout 2 --max-time 5 2>/dev/null)

if [[ -n "$TOKEN" ]]; then
    echo "Using IMDSv2 (token-based)"
    CURRENT_INSTANCE_ID=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s --connect-timeout 2 --max-time 5 "http://169.254.169.254/latest/meta-data/instance-id" 2>/dev/null)
else
    echo "IMDSv2 failed, trying IMDSv1 (direct access)"
    CURRENT_INSTANCE_ID=$(curl -s --connect-timeout 2 --max-time 5 "http://169.254.169.254/latest/meta-data/instance-id" 2>/dev/null)
fi

if [[ -z "$CURRENT_INSTANCE_ID" ]]; then
    echo "❌ Failed to get instance ID from IMDS"
    exit 1
fi

echo "Current instance ID: $CURRENT_INSTANCE_ID"
"""
            commands.append(imds_script)
            
            # Add filter script header
            commands.append("""# ==============================================================================
# Filter volumes to process only those belonging to current instance
# ==============================================================================
echo "=== Filtering volumes for current instance ==="

declare -A INSTANCE_VOLUMES""")
            
            # Add volume mappings for each instance with debug output
            for inst_id, vols in instance_volumes.items():
                for vol in vols:
                    commands.append(f'INSTANCE_VOLUMES["{vol["volume_id"]}"]="{inst_id}"')
                    commands.append(f'echo "Debug: Volume {vol["volume_id"]} belongs to instance {inst_id}"')
            
            # Add filter logic
            commands.append("""echo "Debug: Current instance ID: $CURRENT_INSTANCE_ID"
echo "Debug: All volume mappings:"
for vol_id in "${!INSTANCE_VOLUMES[@]}"; do
    echo "  $vol_id -> ${INSTANCE_VOLUMES[$vol_id]}"
done

# Get list of volumes for current instance
MY_VOLUMES=()
for vol_id in "${!INSTANCE_VOLUMES[@]}"; do
    echo "Debug: Checking $vol_id (belongs to ${INSTANCE_VOLUMES[$vol_id]})"
    if [[ "${INSTANCE_VOLUMES[$vol_id]}" == "$CURRENT_INSTANCE_ID" ]]; then
        MY_VOLUMES+=("$vol_id")
        echo "Debug: Added $vol_id to MY_VOLUMES"
    fi
done

echo "Volumes to process on this instance: ${MY_VOLUMES[*]}"
if [[ ${#MY_VOLUMES[@]} -eq 0 ]]; then
    echo "No volumes to process on this instance"
    exit 0
fi""")
        
            # Create parallel commands with instance filtering (for multi-instance)
            parallel_commands = []
            for volume in volume_list:
                if method == 'fio':
                    cmd = create_filtered_fio_command(volume['volume_id'], volume['device'], volume['size_gb'])
                else:
                    cmd = create_filtered_dd_command(volume['volume_id'], volume['device'], volume['size_gb'])
                parallel_commands.append(cmd)
            
            # Create final parallel script with filtering
            parallel_script = f"""
# ==============================================================================
# Start volume initializations in parallel (filtered by instance)
# ==============================================================================
echo "=== Starting initialization of volumes for current instance ==="

{chr(10).join(parallel_commands)}

# Wait for all background jobs to complete
echo "=== Waiting for all volume initializations to complete ==="
wait

echo "=== All volume initializations completed ==="
"""
            commands.append(parallel_script)
        
        else:
            # Single instance case - use direct commands without IMDS filtering
            parallel_commands = []
            for volume in volume_list:
                if method == 'fio':
                    cmd = create_fio_command(volume['volume_id'], volume['device'], volume['size_gb'])
                else:
                    cmd = create_dd_command(volume['volume_id'], volume['device'], volume['size_gb'])
                parallel_commands.append(cmd)
            
            # Create final parallel script without filtering
            parallel_script = f"""
# ==============================================================================
# Start volume initializations in parallel (single instance)
# ==============================================================================
echo "=== Starting initialization of {len(parallel_commands)} volumes ==="

{chr(10).join(parallel_commands)}

# Wait for all background jobs to complete
echo "=== Waiting for all volume initializations to complete ==="
wait

echo "=== All volume initializations completed ==="
"""
            commands.append(parallel_script)
    
    else:
        # Create sequential commands for single volume or when parallel is disabled
        for volume in volume_list:
            cmd = create_single_volume_command(volume['volume_id'], volume['device'], 
                                             volume['size_gb'], method)
            commands.append(cmd)
    
    return commands


def create_process_cleanup_commands() -> List[str]:
    """
    Create commands to clean up initialization processes.
    
    Returns:
        List of cleanup command strings
    """
    return [
        "#!/bin/bash",
        "echo '=== Killing fio processes ==='",
        "kill -9 `ps -ef | grep 'fio --filename' | grep -v grep | awk '{print $2}'` 2>/dev/null || echo 'No fio processes found'",
        "echo '=== Killing dd processes ==='", 
        "kill -9 `ps -ef | grep 'dd if=' | grep -v grep | awk '{print $2}'` 2>/dev/null || echo 'No dd processes found'",
        "echo '=== Process cleanup completed ==='"
    ]