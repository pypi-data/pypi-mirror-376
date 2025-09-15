#!/usr/bin/env python3
"""
EBS Volume Initialization FastMCP Server

This FastMCP server provides tools for automatically initializing AWS EBS volumes
attached to EC2 instances using AWS Systems Manager.
"""

import json
import logging
from typing import Dict, List, Any

from mcp.server.fastmcp import FastMCP

# Import our modularized components
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from aws_clients import get_ec2_client, get_ssm_client, DEFAULT_REGION
from throughput import get_instance_ebs_throughput
from estimation import (
    estimate_parallel_initialization_time, 
    estimate_single_volume_time, 
    format_estimated_time,
    create_estimation_comment
)
from utils import create_volume_summary, needs_initialization
from initialization import build_initialization_commands, create_process_cleanup_commands
from status import (
    get_command_status,
    parse_estimation_from_comment,
    calculate_elapsed_time,
    calculate_progress_info,
    format_status_message,
    format_text_response
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP server instance
mcp = FastMCP("EBS Initialization Server")


@mcp.tool()
def get_instance_volumes(instance_id: str, region: str = DEFAULT_REGION) -> str:
    """
    Get all EBS volumes attached to an EC2 instance.
    
    Args:
        instance_id: EC2 instance ID (e.g., i-1234567890abcdef0)
        region: AWS region name (default: from AWS_DEFAULT_REGION or AWS_REGION env var, fallback to us-east-1)
    
    Returns:
        JSON string containing volume information
    """
    try:
        ec2 = get_ec2_client(region)
        
        response = ec2.describe_volumes(
            Filters=[
                {'Name': 'attachment.instance-id', 'Values': [instance_id]}
            ]
        )
        
        volumes = []
        for volume in response['Volumes']:
            for attachment in volume['Attachments']:
                if attachment['InstanceId'] == instance_id:
                    volumes.append(create_volume_summary(volume))
        
        result = {
            "instance_id": instance_id,
            "region": region,
            "total_volumes": len(volumes),
            "volumes": volumes
        }
        
        return json.dumps(result, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return f"❌ Failed to get volumes for instance {instance_id}: {str(e)}"


@mcp.tool()
def initialize_all_volumes(instance_id: str, method: str = "fio", region: str = DEFAULT_REGION) -> str:
    """
    Initialize all EBS volumes attached to EC2 instance(s).
    Supports both single instance and multiple instances (comma-separated).
    
    Args:
        instance_id: Single EC2 instance ID or comma-separated list of instance IDs
        method: Initialization method - 'fio' (recommended) or 'dd'
        region: AWS region name (default: from AWS_DEFAULT_REGION or AWS_REGION env var, fallback to us-east-1)
    
    Returns:
        JSON string with initialization status and command ID
    """
    try:
        ec2 = get_ec2_client(region)
        ssm = get_ssm_client(region)
        
        # Parse instance IDs (support comma-separated list)
        instance_ids = [id.strip() for id in instance_id.split(',') if id.strip()]
        if not instance_ids:
            return f"❌ No valid instance IDs provided"
        
        logger.info(f"Processing {len(instance_ids)} instance(s): {instance_ids}")
        
        # Get instance information for all instances
        instance_response = ec2.describe_instances(InstanceIds=instance_ids)
        instance_info = {}
        
        for reservation in instance_response['Reservations']:
            for instance in reservation['Instances']:
                inst_id = instance['InstanceId']
                instance_info[inst_id] = {
                    'type': instance['InstanceType'],
                    'state': instance.get('State', {}).get('Name', 'unknown')
                }
        
        # Validate all instances exist
        missing_instances = set(instance_ids) - set(instance_info.keys())
        if missing_instances:
            return f"❌ Instance(s) not found: {', '.join(missing_instances)}"
        
        # Get volumes for all instances
        response = ec2.describe_volumes(
            Filters=[
                {'Name': 'attachment.instance-id', 'Values': instance_ids}
            ]
        )
        
        # Organize volumes by instance and analyze initialization needs
        instance_volumes = {inst_id: [] for inst_id in instance_ids}
        instance_total_volumes = {inst_id: 0 for inst_id in instance_ids}
        instance_estimations = {}
        all_volume_info = []
        total_instances_with_volumes = 0
        
        for volume in response['Volumes']:
            for attachment in volume['Attachments']:
                inst_id = attachment['InstanceId']
                if inst_id in instance_ids and attachment['State'] == 'attached':
                    instance_total_volumes[inst_id] += 1
                    if needs_initialization(volume):
                        volume_summary = create_volume_summary(volume)
                        volume_summary['instance_id'] = inst_id  # Add instance reference
                        instance_volumes[inst_id].append(volume_summary)
                        all_volume_info.append(volume_summary)
        
        # Calculate per-instance estimations
        for inst_id in instance_ids:
            volumes = instance_volumes[inst_id]
            if volumes:
                total_instances_with_volumes += 1
                instance_type = instance_info[inst_id]['type']
                instance_max_throughput = get_instance_ebs_throughput(instance_type, region)
                
                volumes_for_estimation = [
                    {'size_gb': vol['size_gb'], 'max_throughput_mbps': vol.get('throughput', 1000)}
                    for vol in volumes
                ]
                
                estimated_minutes = 0.0
                if volumes_for_estimation and instance_max_throughput > 0:
                    try:
                        estimated_minutes = estimate_parallel_initialization_time(
                            volumes_for_estimation, instance_max_throughput
                        )
                    except Exception as e:
                        logger.error(f"Error calculating estimation for {inst_id}: {e}")
                        estimated_minutes = 0.0
                
                instance_estimations[inst_id] = {
                    'estimated_minutes': estimated_minutes,
                    'volume_count': len(volumes),
                    'total_gb': sum(vol['size_gb'] for vol in volumes),
                    'instance_type': instance_type
                }
        
        if not all_volume_info:
            return f"ℹ️ No volumes needing initialization found across {len(instance_ids)} instance(s). All volumes are blank (no snapshots)."
        
        # Build commands for all instances (single SSM command for multiple targets)
        commands = build_initialization_commands(all_volume_info, method, parallel=True)
        
        # Get target instances (only those with volumes to initialize)
        target_instances = [inst_id for inst_id in instance_ids if instance_volumes[inst_id]]
        
        # Create comment with summary data and instance estimations (for multi-instance support)
        total_volumes = len(all_volume_info)
        total_gb = sum(vol['size_gb'] for vol in all_volume_info)
        
        # For single instance, use original format with estimation
        if len(target_instances) == 1:
            # Calculate estimation for single instance using original logic
            instance_id = target_instances[0]
            if instance_id in instance_estimations:
                estimated_minutes = instance_estimations[instance_id].get('estimated_minutes', 0)
                comment = f'EBS Init: {total_volumes}vol {total_gb}GB est:{estimated_minutes:.1f}m {method}'[:100]
            else:
                comment = f'EBS Init: {total_volumes}vol {total_gb}GB {method}'[:100]
        else:
            # For multiple instances, use simple comment (detailed data in Parameter Store)
            comment = f'EBS Init: {len(target_instances)}inst {total_volumes}vol {total_gb}GB {method}'[:100]
        
        # Execute via Systems Manager on all instances with volumes
        logger.info(f"Executing initialization for {total_volumes} volumes across {len(target_instances)} instances")
        
        ssm_response = ssm.send_command(
            InstanceIds=target_instances,
            DocumentName='AWS-RunShellScript',
            Parameters={
                'commands': commands,
                'executionTimeout': ['86400']  # 24 hours timeout
            },
            Comment=comment
        )
        
        command_id = ssm_response['Command']['CommandId']
        
        # Store instance estimations in Parameter Store for multi-instance commands
        if len(target_instances) > 1 and instance_estimations:
            try:
                import json as json_module
                
                from datetime import datetime
                
                estimations_data = {
                    "command_id": command_id,
                    "target_instances": target_instances,
                    "total_volumes": total_volumes,
                    "total_gb": total_gb, 
                    "method": method,
                    "estimations": instance_estimations,
                    "timestamp": str(datetime.now())
                }
                
                parameter_name = f'/ebs-init/estimations/{command_id}'
                logger.info(f"DEBUG: Storing estimations in Parameter Store: {parameter_name}")
                
                ssm.put_parameter(
                    Name=parameter_name,
                    Value=json_module.dumps(estimations_data),
                    Type='String',
                    Overwrite=True,
                    Description=f'EBS initialization estimations for command {command_id}'
                )
                
                logger.info(f"DEBUG: Successfully stored estimations for command {command_id}")
                
            except Exception as e:
                logger.error(f"Failed to store estimations in Parameter Store: {e}")
                # Continue execution - this is not critical for the operation
        
        # Calculate total estimated time and create result
        # For parallel processing, use the maximum time (longest running instance)
        total_estimated_minutes = max(est.get('estimated_minutes', 0) for est in instance_estimations.values()) if instance_estimations else 0
        
        result = {
            "status": "initialization_started", 
            "command_id": command_id,
            "target_instances": target_instances,
            "total_instances": len(target_instances),
            "region": region,
            "method": method,
            "total_volumes": total_volumes,
            "volumes_initialized": total_volumes,
            "volumes_skipped": sum(instance_total_volumes[inst_id] - len(instance_volumes[inst_id]) for inst_id in instance_ids),
            "instance_estimations": instance_estimations,
            "total_estimated_minutes": round(total_estimated_minutes, 1) if total_estimated_minutes > 0 else "Unable to calculate",
            "total_estimated_time": format_estimated_time(total_estimated_minutes),
            "message": f"Started initialization for {total_volumes} volumes across {len(target_instances)} instances",
            "next_steps": f"Use check_initialization_status with command_id: {command_id}"
        }
        
        return json.dumps(result, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return f"❌ Failed to initialize volumes for instance {instance_id}: {str(e)}"


@mcp.tool()
def check_initialization_status(command_id: str, region: str = DEFAULT_REGION) -> str:
    """
    Check the status of volume initialization for single or multiple instances.
    
    Args:
        command_id: Systems Manager command ID
        region: AWS region name (default: from AWS_DEFAULT_REGION or AWS_REGION env var, fallback to us-east-1)
    
    Returns:
        Text string with current status and progress information for all instances
    """
    # Get command status for all instances
    status_data, error = get_command_status(command_id, region)
    if error:
        return error
    
    invocations = status_data['invocations']
    
    # Parse estimation data from command comment (from first invocation)
    comment = invocations[0]['invocation'].get('Comment', '') or ""
    estimation_data = parse_estimation_from_comment(comment)
    
    # Handle single instance case (backward compatibility)
    if len(invocations) == 1:
        invocation_data = invocations[0]
        response = invocation_data['response']
        invocation = invocation_data['invocation']
        instance_id = invocation_data['instance_id']
        
        # Get timing information
        start_time = invocation.get('RequestedDateTime')
        end_time = response.get('EndDateTime') or invocation.get('EndDateTime')
        
        # If not found, check CommandPlugins
        if not end_time and 'CommandPlugins' in invocation:
            plugins = invocation['CommandPlugins']
            if plugins and len(plugins) > 0:
                end_time = plugins[0].get('ResponseFinishDateTime')
        
        # Calculate progress if initialization is in progress
        progress_info = None
        if response['Status'] == 'InProgress' and start_time:
            try:
                elapsed_minutes = calculate_elapsed_time(start_time)
                # Use original estimation logic for single instance
                progress_info = calculate_progress_info(elapsed_minutes, estimation_data)
            except Exception as e:
                logger.warning(f"Could not calculate progress: {e}")
        
        # Format and return text response for single instance
        execution_start_time = str(start_time) if start_time else "Unknown"
        execution_end_time = str(end_time) if end_time else None
        return format_text_response(response['Status'], progress_info, instance_id, execution_start_time, execution_end_time)
    
    # Handle multiple instances case
    else:
        result_lines = []
        result_lines.append(f"Multi-Instance Initialization Status (Command: {command_id})")
        result_lines.append("=" * 60)
        
        # Get per-instance estimations from Parameter Store for multi-instance commands
        instance_estimations = {}
        
        if len(invocations) > 1:
            try:
                parameter_name = f'/ebs-init/estimations/{command_id}'
                logger.info(f"DEBUG: Attempting to retrieve estimations from Parameter Store: {parameter_name}")
                
                # Get SSM client (reuse if possible)
                from aws_clients import get_ssm_client
                ssm_client = get_ssm_client(region)
                
                response = ssm_client.get_parameter(Name=parameter_name)
                
                import json as json_module
                estimations_data = json_module.loads(response['Parameter']['Value'])
                instance_estimations = estimations_data.get("estimations", {})
                
                logger.info(f"DEBUG: Successfully retrieved accurate instance estimations: {len(instance_estimations)} instances")
                logger.info(f"DEBUG: Estimations data: {instance_estimations}")
                
            except Exception as e:
                logger.warning(f"DEBUG: Failed to retrieve estimations from Parameter Store: {e}")
                logger.warning("DEBUG: Will show basic status only")
        else:
            logger.info("DEBUG: Single instance command - no Parameter Store lookup needed")
        
        overall_status = "InProgress"
        completed_instances = 0
        failed_instances = 0
        
        for i, invocation_data in enumerate(invocations):
            response = invocation_data['response']
            invocation = invocation_data['invocation']
            instance_id = invocation_data['instance_id']
            status = response['Status']
            
            # Get timing information
            start_time = invocation.get('RequestedDateTime')
            end_time = response.get('EndDateTime') or invocation.get('EndDateTime')
            
            # Count statuses for overall determination
            if status == 'Success':
                completed_instances += 1
            elif status in ['Failed', 'Cancelled', 'TimedOut']:
                failed_instances += 1
            
            # Format instance status
            status_emoji = {
                'Success': '✅',
                'InProgress': '🔄',
                'Failed': '❌',
                'Cancelled': '⚠️',
                'TimedOut': '⏰'
            }.get(status, 'ℹ️')
            
            result_lines.append(f"{status_emoji} Instance {instance_id}: {status}")
            
            # Add per-instance estimation and progress info
            if instance_id in instance_estimations:
                est_data = instance_estimations[instance_id]
                estimated_minutes = est_data.get('estimated_minutes', 0)
                volume_count = est_data.get('volume_count', 0)
                total_gb = est_data.get('total_gb', 0)
                instance_type = est_data.get('instance_type', 'Unknown')
                
                result_lines.append(f"   Volumes: {volume_count}, Size: {total_gb}GB, Type: {instance_type}")
                result_lines.append(f"   Estimated time: {estimated_minutes:.1f} minutes")
                
                # Calculate progress if in progress
                if status == 'InProgress' and start_time and estimated_minutes > 0:
                    try:
                        elapsed_minutes = calculate_elapsed_time(start_time)
                        progress_percentage = min(95, max(0, (elapsed_minutes / estimated_minutes) * 100))
                        remaining_minutes = max(0, estimated_minutes - elapsed_minutes)
                        
                        # Create progress bar
                        progress_chars = max(0, min(20, int(progress_percentage / 5)))
                        progress_bar = '█' * progress_chars + '░' * (20 - progress_chars)
                        
                        result_lines.append(f"   Progress: [{progress_bar}] {progress_percentage:.1f}%")
                        result_lines.append(f"   Elapsed: {elapsed_minutes:.1f}m, Remaining: ~{remaining_minutes:.1f}m")
                    except Exception as e:
                        logger.warning(f"Could not calculate progress for {instance_id}: {e}")
                        result_lines.append(f"   Elapsed: Unable to calculate")
            
            if start_time:
                result_lines.append(f"   Started: {start_time}")
            if end_time:
                result_lines.append(f"   Ended: {end_time}")
                
            result_lines.append("")
        
        # Determine overall status
        if completed_instances == len(invocations):
            overall_status = "All Completed"
        elif failed_instances > 0:
            overall_status = f"In Progress ({completed_instances}/{len(invocations)} completed, {failed_instances} failed)"
        else:
            overall_status = f"In Progress ({completed_instances}/{len(invocations)} completed)"
        
        # Add summary information
        if estimation_data.get("is_multi_instance"):
            method = estimation_data.get("method", "Unknown")
            total_volumes = estimation_data.get("volumes", 0)
            total_gb = estimation_data.get("total_gb", 0)
            result_lines.insert(1, f"Overall Status: {overall_status}")
            result_lines.insert(2, f"Method: {method}, Total Volumes: {total_volumes}, Total Size: {total_gb}GB")
            result_lines.insert(3, "=" * 60)
        else:
            result_lines.insert(1, f"Overall Status: {overall_status}")
            result_lines.insert(2, "=" * 60)
        
        return "\n".join(result_lines)


@mcp.tool()
def cancel_initialization(command_id: str, region: str = DEFAULT_REGION) -> str:
    """
    Cancel an ongoing volume initialization by cancelling the Systems Manager command and killing child processes.
    
    Args:
        command_id: Systems Manager command ID to cancel
        region: AWS region name (default: from AWS_DEFAULT_REGION or AWS_REGION env var, fallback to us-east-1)
    
    Returns:
        JSON string with cancellation status
    """
    try:
        ssm = get_ssm_client(region)
        
        # Get command status first
        status_data, error = get_command_status(command_id, region)
        if error:
            return error
        
        invocations = status_data['invocations']
        instance_ids = [inv['instance_id'] for inv in invocations]
        
        # Cancel the original command
        try:
            ssm.cancel_command(CommandId=command_id, InstanceIds=instance_ids)
            logger.info(f"Cancelled command {command_id} on instances {instance_ids}")
        except Exception as e:
            logger.warning(f"Could not cancel command {command_id}: {e}")
        
        # Send cleanup commands to kill any running processes on all instances
        cleanup_commands = create_process_cleanup_commands()
        
        cleanup_response = ssm.send_command(
            InstanceIds=instance_ids,
            DocumentName='AWS-RunShellScript',
            Parameters={
                'commands': cleanup_commands,
                'executionTimeout': ['300']  # 5 minutes timeout
            },
            Comment='EBS Init Cleanup - Kill initialization processes'
        )
        
        cleanup_command_id = cleanup_response['Command']['CommandId']
        
        result = {
            "status": "cancellation_requested",
            "original_command_id": command_id,
            "cleanup_command_id": cleanup_command_id,
            "instance_ids": instance_ids,
            "total_instances": len(instance_ids),
            "region": region,
            "message": f"✅ Cancellation requested for {len(instance_ids)} instance(s). Cleanup command sent to terminate initialization processes.",
            "next_steps": f"Monitor cleanup with command_id: {cleanup_command_id}"
        }
        
        return json.dumps(result, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return f"❌ Failed to cancel initialization for command {command_id}: {str(e)}"


@mcp.tool()
def initialize_volume_by_id(volume_id: str, method: str = "fio", region: str = DEFAULT_REGION) -> str:
    """
    Initialize a specific EBS volume by its volume ID.
    
    Args:
        volume_id: EBS volume ID (e.g., vol-1234567890abcdef0)
        method: Initialization method - 'fio' (recommended) or 'dd'
        region: AWS region name (default: from AWS_DEFAULT_REGION or AWS_REGION env var, fallback to us-east-1)
    
    Returns:
        JSON string with initialization status and command ID
    """
    try:
        ec2 = get_ec2_client(region)
        ssm = get_ssm_client(region)
        
        # Get volume information
        response = ec2.describe_volumes(VolumeIds=[volume_id])
        
        if not response['Volumes']:
            return f"❌ Volume {volume_id} not found in region {region}"
        
        volume = response['Volumes'][0]
        
        # Check if volume is attached
        if not volume['Attachments']:
            return f"❌ Volume {volume_id} is not attached to any instance"
        
        attachment = volume['Attachments'][0]
        if attachment['State'] != 'attached':
            return f"❌ Volume {volume_id} is not in 'attached' state (current state: {attachment['State']})"
        
        instance_id = attachment['InstanceId']
        device = attachment['Device']
        size_gb = volume['Size']
        volume_type = volume['VolumeType']
        
        # Get instance type for throughput calculation
        instance_response = ec2.describe_instances(InstanceIds=[instance_id])
        instance_type = None
        for reservation in instance_response['Reservations']:
            for instance in reservation['Instances']:
                if instance['InstanceId'] == instance_id:
                    instance_type = instance['InstanceType']
                    break
        
        if not instance_type:
            return f"❌ Could not find instance type for {instance_id}"
        
        # Get instance maximum EBS throughput
        instance_max_throughput = get_instance_ebs_throughput(instance_type, region)
        logger.info(f"Debug - EBS throughput for {instance_type}: {instance_max_throughput} MB/s")
        
        # Calculate estimated completion time for single volume
        estimated_minutes = 0.0
        if instance_max_throughput > 0:
            volume_max_throughput = volume.get('Throughput', 1000)
            estimated_minutes = estimate_single_volume_time(size_gb, volume_max_throughput, instance_max_throughput)
        else:
            logger.warning(f"Debug - Cannot calculate estimation for single volume: throughput={instance_max_throughput}")
        
        # Build initialization commands for single volume
        volume_info = [{'volume_id': volume_id, 'device': device, 'size_gb': size_gb}]
        commands = build_initialization_commands(volume_info, method, parallel=False)
        
        # Execute via Systems Manager
        logger.info(f"Executing initialization for volume {volume_id} on instance {instance_id}")
        
        # Create comment with estimation data
        comment = create_estimation_comment(1, size_gb, estimated_minutes, method)
        
        ssm_response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',
            Parameters={
                'commands': commands,
                'executionTimeout': ['86400']  # 24 hours timeout
            },
            Comment=comment
        )
        
        command_id = ssm_response['Command']['CommandId']
        
        result = {
            "status": "initialization_started",
            "command_id": command_id,
            "volume_id": volume_id,
            "instance_id": instance_id,
            "instance_type": instance_type,
            "instance_max_throughput_mbps": instance_max_throughput,
            "device": device,
            "size_gb": size_gb,
            "volume_type": volume_type,
            "region": region,
            "method": method,
            "estimated_completion_minutes": round(estimated_minutes, 1) if estimated_minutes > 0 else "Unable to calculate",
            "estimated_completion_time": format_estimated_time(estimated_minutes),
            "message": f"✅ Started initialization of volume {volume_id} ({size_gb}GB) using {method} method",
            "next_steps": f"Use check_initialization_status with command_id: {command_id}"
        }
        
        return json.dumps(result, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return f"❌ Failed to initialize volume {volume_id}: {str(e)}"



if __name__ == "__main__":
    mcp.run()