"""
Status Checking and Progress Calculation Module

This module handles checking the status of EBS initialization commands,
calculating progress, and formatting status responses.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from aws_clients import get_ssm_client, DEFAULT_REGION

logger = logging.getLogger(__name__)


def parse_estimation_from_comment(comment: str) -> Dict[str, Any]:
    """
    Parse estimation data from SSM command comment.
    
    Args:
        comment: SSM command comment string
        
    Returns:
        Dictionary with parsed estimation data
    """
    estimation_data = {}
    
    if not comment:
        return estimation_data
    
    # Parse new multi-instance format with base64 encoded JSON: "EBS Init Multi: <base64>"
    logger.info(f"DEBUG: Trying to parse comment: '{comment}'")
    multi_b64_match = re.search(r'EBS Init Multi: ([A-Za-z0-9+/=]+)', comment)
    if multi_b64_match:
        try:
            import base64
            import json as json_module
            
            b64_data = multi_b64_match.group(1)
            logger.info(f"DEBUG: Extracted base64 data: '{b64_data}' (length: {len(b64_data)})")
            
            json_str = base64.b64decode(b64_data).decode()
            logger.info(f"DEBUG: Decoded JSON string: '{json_str}' (length: {len(json_str)})")
            
            compact_data = json_module.loads(json_str)
            logger.info(f"DEBUG: Parsed compact data: {compact_data}")
            
            # Convert compact format back to full format
            estimation_data = {
                "instances": compact_data.get("i", 0),
                "volumes": compact_data.get("v", 0), 
                "total_gb": compact_data.get("g", 0),
                "method": compact_data.get("m", ""),
                "is_multi_instance": True,
                "estimations": {}
            }
            
            # Convert compact estimations back to full format
            compact_estimations = compact_data.get("e", {})
            logger.info(f"DEBUG: Processing {len(compact_estimations)} compact estimations")
            
            for inst_id, compact_est in compact_estimations.items():
                estimation_data["estimations"][inst_id] = {
                    "estimated_minutes": compact_est.get("est", 0),
                    "volume_count": compact_est.get("vol", 0),
                    "total_gb": compact_est.get("gb", 0),
                    "instance_type": compact_est.get("type", "Unknown")
                }
                logger.info(f"DEBUG: Converted estimation for {inst_id}: {estimation_data['estimations'][inst_id]}")
            
            logger.info(f"DEBUG: Final parsed multi-instance base64 estimation data: {estimation_data}")
            return estimation_data
        except Exception as e:
            logger.error(f"DEBUG: Failed to parse base64 estimation data: {e}")
            logger.error(f"DEBUG: Base64 data was: '{b64_data if 'b64_data' in locals() else 'N/A'}'")
            # Fall through to try other parsing methods
    else:
        logger.info("DEBUG: No base64 multi-instance format match found")
        
    # Parse legacy comment format: "EBS Init: 2inst 3vol 208GB fio"  
    multi_match = re.search(r'(\d+)inst (\d+)vol (\d+)GB (\w+)', comment)
    if multi_match:
        estimation_data = {
            "instances_count": int(multi_match.group(1)),
            "volumes_count": int(multi_match.group(2)),
            "total_gb": int(multi_match.group(3)),
            "method": multi_match.group(4),
            "is_multi_instance": True
        }
        logger.info(f"Debug - Parsed legacy multi-instance estimation data: {estimation_data}")
        return estimation_data
        
    # Parse single instance format: "EBS Init: 3vol 208GB est:14.0m fio"
    single_match = re.search(r'(\d+)vol (\d+)GB est:(\d+(?:\.\d+)?)m (\w+)', comment)
    if single_match:
        estimation_data = {
            "volumes_count": int(single_match.group(1)),
            "total_gb": int(single_match.group(2)),
            "estimated_minutes": float(single_match.group(3)),
            "method": single_match.group(4),
            "is_multi_instance": False
        }
        logger.info(f"Debug - Parsed single instance estimation data: {estimation_data}")
    else:
        logger.warning(f"Debug - Comment regex did not match: '{comment}'")
    
    return estimation_data


def parse_start_time(start_time) -> datetime:
    """
    Parse start time with proper timezone handling.
    
    Args:
        start_time: Start time from AWS API (string or datetime)
        
    Returns:
        Timezone-aware datetime object in UTC
    """
    if isinstance(start_time, str):
        # Handle various timezone formats
        if start_time.endswith('Z'):
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        elif '+' in start_time or '-' in start_time[-6:]:  # Check for timezone offset like +09:00
            start_dt = datetime.fromisoformat(start_time)
        elif start_time.endswith('UTC'):
            start_dt = datetime.fromisoformat(start_time.replace('UTC', '')).replace(tzinfo=timezone.utc)
        else:
            # Assume UTC if no timezone info
            start_dt = datetime.fromisoformat(start_time).replace(tzinfo=timezone.utc)
    else:
        # If it's already a datetime object, ensure it has timezone info
        if start_time.tzinfo is None:
            start_dt = start_time.replace(tzinfo=timezone.utc)
        else:
            start_dt = start_time
    
    # Convert to UTC for consistent calculation
    if start_dt.tzinfo is not None:
        start_dt_utc = start_dt.astimezone(timezone.utc)
    else:
        start_dt_utc = start_dt.replace(tzinfo=timezone.utc)
    
    return start_dt_utc


def calculate_elapsed_time(start_time) -> float:
    """
    Calculate elapsed time from start time to now in minutes.
    
    Args:
        start_time: Start time from AWS API
        
    Returns:
        Elapsed time in minutes
    """
    # Get reliable current UTC time
    import time
    current_utc_timestamp = time.time()
    current_time = datetime.fromtimestamp(current_utc_timestamp, tz=timezone.utc)
    
    start_dt_utc = parse_start_time(start_time)
    elapsed_minutes = (current_time - start_dt_utc).total_seconds() / 60
    
    logger.info(f"Debug - Times: start_utc='{start_dt_utc}', current_utc='{current_time}', elapsed={elapsed_minutes:.1f}min")
    
    return elapsed_minutes


def calculate_progress_info(elapsed_minutes: float, estimation_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate progress information based on elapsed time and estimation data.
    
    Args:
        elapsed_minutes: Elapsed time in minutes
        estimation_data: Parsed estimation data from comment
        
    Returns:
        Dictionary with progress information
    """
    if not estimation_data or estimation_data.get('estimated_minutes', 0) <= 0:
        return {}
    
    estimated_total_minutes = estimation_data['estimated_minutes']
    progress_percentage = min(95, max(0, (elapsed_minutes / estimated_total_minutes) * 100))
    
    # Create progress bar (20 characters) - ensure non-negative
    progress_chars = max(0, min(20, int(progress_percentage / 5)))  # 5% per character, clamp between 0-20
    progress_bar = '█' * progress_chars + '░' * (20 - progress_chars)
    
    return {
        "elapsed_minutes": round(elapsed_minutes, 1),
        "estimated_total_minutes": estimated_total_minutes,
        "estimated_remaining_minutes": round(max(0, estimated_total_minutes - elapsed_minutes), 1),
        "progress_percentage": round(progress_percentage, 1),
        "progress_bar": f"[{progress_bar}] {progress_percentage:.1f}%",
        "volumes_count": estimation_data.get('volumes_count', 0),
        "total_gb": estimation_data.get('total_gb', 0),
        "method": estimation_data.get('method', 'Unknown')
    }


def get_command_status(command_id: str, region: str = DEFAULT_REGION) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Get command status and details from SSM for all instances.
    
    Args:
        command_id: SSM command ID
        region: AWS region
        
    Returns:
        Tuple of (command_response, error_message)
    """
    try:
        ssm = get_ssm_client(region)
        
        # Get command details for all instances
        command_invocations = ssm.list_command_invocations(
            CommandId=command_id,
            Details=True
        )
        
        if not command_invocations['CommandInvocations']:
            return {}, f"❌ No command invocations found for command {command_id}"
        
        # Get detailed response for all invocations
        invocations_data = []
        for invocation in command_invocations['CommandInvocations']:
            instance_id = invocation['InstanceId']
            
            response = ssm.get_command_invocation(
                CommandId=command_id,
                InstanceId=instance_id
            )
            
            invocations_data.append({
                'response': response,
                'invocation': invocation,
                'instance_id': instance_id
            })
        
        return {
            'invocations': invocations_data,
            'command_id': command_id
        }, None
        
    except Exception as e:
        return {}, f"❌ Failed to get command status for {command_id}: {str(e)}"


def format_status_message(status: str, progress_info: Optional[Dict[str, Any]] = None) -> str:
    """
    Format status message with appropriate emoji and context.
    
    Args:
        status: Command status from AWS
        progress_info: Optional progress information
        
    Returns:
        Formatted status message
    """
    if status == 'Success':
        return '✅ Volume initialization completed successfully'
    elif status == 'InProgress':
        if progress_info and 'progress_percentage' in progress_info:
            progress_pct = progress_info.get('progress_percentage', 0)
            return f'🔄 {progress_pct}% Complete... (Actual initialization time may vary depending on environment. This is for reference only.)'
        else:
            return '🔄 Volume initialization is still in progress (Actual initialization time may vary depending on environment. This is for reference only.)'
    elif status == 'Failed':
        return '❌ Volume initialization failed'
    elif status == 'Cancelled':
        return '⚠️  Volume initialization was cancelled'
    elif status == 'TimedOut':
        return '⏰ Volume initialization timed out'
    else:
        return f'ℹ️  Volume initialization status: {status}'


def format_text_response(status: str, progress_info: Optional[Dict[str, Any]], 
                        instance_id: str, execution_start_time: str, 
                        execution_end_time: Optional[str] = None) -> str:
    """
    Format text-based response for AI agent compatibility.
    
    Args:
        status: Command status
        progress_info: Progress information
        instance_id: EC2 instance ID  
        execution_start_time: Command start time
        execution_end_time: Command end time (for completed commands)
        
    Returns:
        Formatted text response
    """
    if status == 'InProgress' and progress_info:
        elapsed = progress_info.get('elapsed_minutes', 0)
        remaining = progress_info.get('estimated_remaining_minutes', 0)
        volumes = progress_info.get('volumes_count', 0)
        total_gb = progress_info.get('total_gb', 0)
        method = progress_info.get('method', 'Unknown')
        progress_bar = progress_info.get('progress_bar', '[░░░░░░░░░░░░░░░░░░░░] 0.0%')
        
        return f"""Status: {status}
Progress: {progress_bar}
Elapsed: {elapsed} minutes
Estimated remaining: {remaining} minutes
Volumes: {volumes} 
Size: {total_gb}GB
Method: {method}
Instance: {instance_id}
Started: {execution_start_time}

Note: Actual initialization time may vary depending on environment. This is for reference only."""
    
    elif status == 'Success':
        if execution_end_time:
            # Calculate total elapsed time
            try:
                start_dt = datetime.fromisoformat(execution_start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(execution_end_time.replace('Z', '+00:00'))
                total_elapsed = end_dt - start_dt
                
                # Format elapsed time nicely
                total_minutes = int(total_elapsed.total_seconds() / 60)
                hours = total_minutes // 60
                minutes = total_minutes % 60
                
                if hours > 0:
                    elapsed_str = f"{hours}h {minutes}m"
                else:
                    elapsed_str = f"{minutes}m"
                
                return f"""Status: Completed Successfully ✅
Instance ID: {instance_id}
Start Time: {execution_start_time}
End Time: {execution_end_time}
Total Elapsed: {elapsed_str}"""
            except Exception as e:
                logger.warning(f"Error calculating elapsed time: {e}")
                return f"""Status: Completed Successfully ✅
Instance ID: {instance_id}
Start Time: {execution_start_time}
End Time: {execution_end_time}"""
        else:
            return f"""Status: Completed Successfully ✅
Instance ID: {instance_id}
Start Time: {execution_start_time}"""
    
    else:
        return f"""Status: {status}
Instance ID: {instance_id}"""