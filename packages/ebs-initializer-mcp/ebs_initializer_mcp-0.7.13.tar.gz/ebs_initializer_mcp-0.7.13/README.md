# EBS Initialization MCP Server

A Model Context Protocol (MCP) server for automating AWS EBS volume initialization. This server provides tools to initialize EBS volumes attached to EC2 instances using AWS Systems Manager.

## Features

- 🔍 **Volume Discovery**: Automatically discover all EBS volumes attached to an EC2 instance
- 🚀 **Automated Initialization**: Initialize volumes using `fio` (recommended) or `dd`
- 🏢 **Multi-Instance Support**: Initialize volumes across multiple instances in parallel with single SSM command
- ⏱️ **Smart Time Estimation**: Predict completion time based on volume size and throughput with parallel processing simulation
- 📊 **Real-time Progress Tracking**: Visual progress bars with accurate percentage and remaining time per instance
- ❌ **Cancellation Support**: Cancel ongoing initialization with complete process cleanup
- 🤖 **AI Agent Optimized**: Text-based responses optimized for AI agent compatibility
- 🌐 **Multi-Region Support**: Works across all AWS regions
- 🔒 **Secure Execution**: Uses AWS Systems Manager for secure remote execution
- 🏗️ **Modular Architecture**: Clean, maintainable codebase with separated concerns

## Installation

### Using uvx (Recommended)

```bash
# Run directly without installation (latest version)
uvx ebs-initializer-mcp@latest

# Or run specific version
uvx ebs-initializer-mcp==0.7.10

# Install globally
uv tool install ebs-initializer-mcp

# Upgrade to latest version
uvx --upgrade ebs-initializer-mcp
```

### From GitHub

```bash
uvx --from git+https://github.com/username/ebs-init-mcp.git ebs-mcp-server
```

## Usage

### As MCP Server

Add to your MCP configuration (`mcp_config.json`):

```json
{
  "mcpServers": {
    "ebs-initializer": {
      "command": "uvx",
      "args": ["ebs-initializer-mcp@latest"],
      "env": {
        "AWS_REGION": "us-west-2"
      }
    }
  }
}
```

### Available Tools

1. **get_instance_volumes**: Get all EBS volumes attached to an instance
2. **initialize_all_volumes**: Initialize all volumes on one or multiple instances (supports comma-separated instance IDs with single SSM command execution)
3. **initialize_volume_by_id**: Initialize a specific volume by its volume ID
4. **check_initialization_status**: Monitor initialization progress and view detailed logs with per-instance estimation data
5. **cancel_initialization**: Cancel ongoing initialization with complete process cleanup

### Example Usage with Claude Code

```
# Single instance
"Initialize all EBS volumes for instance i-1234567890abcdef0 using fio"

# Multiple instances (comma-separated)
"Initialize all EBS volumes for instances i-1234567890abcdef0,i-0987654321fedcba0 using fio"

# Specific volume
"Initialize volume vol-1234567890abcdef0 using fio"

# Check status
"Check the status of the initialization command 12345678-1234-1234-1234-123456789012"

# Cancel operation
"Cancel the initialization command 12345678-1234-1234-1234-123456789012"
```

The MCP server will:
1. Discover all attached EBS volumes and calculate estimated completion time per instance
2. Install fio on the target instance(s)
3. Execute single SSM command across multiple instances with IMDS-based volume filtering
4. Run initialization commands in parallel with real-time throughput optimization
5. Provide **real-time progress tracking** with visual progress bars and per-instance estimations
6. Return **AI agent-optimized flat JSON structure** with instance-specific data
7. Allow cancellation with complete process cleanup if needed

## Progress Tracking

Enhanced progress tracking optimized for AI agents with multi-instance support:

### Visual Progress Display
- **Real-time progress bars**: `[██████████░░░░░░░░░░] 50.0%`
- **Per-instance tracking**: Individual progress for each instance
- **Accurate percentages**: Based on initial time estimation and elapsed time
- **Remaining time calculation**: Precise estimates of completion time

### Multi-Instance Support
- **Instance-specific estimations**: Each instance gets its own time prediction
- **Parallel execution time**: Shows maximum time across all instances (not sum)
- **IMDS volume filtering**: Each instance only processes its own volumes
- **Parameter Store integration**: Stores estimation data for multi-instance commands

### AI Agent Optimization
- **Flat JSON structure**: Progress information at top-level fields for easy access
- **Priority field ordering**: Most important progress data comes first
- **Instance breakdown**: Detailed per-instance estimation data

### Single Instance Response Structure
```json
{
  "command_id": "...",
  "status": "InProgress",
  "execution_start_time": "2025-09-10 01:18:21.418000+00:00",
  "progress_percentage": 50.0,
  "progress_bar": "[██████████░░░░░░░░░░] 50.0%",
  "estimated_remaining_minutes": 5.2,
  "message": "🔄 50.0% Complete..."
}
```

### Multi-Instance Response Structure
```json
{
  "status": "initialization_started",
  "command_id": "4044d07e-c10c-4caf-b5b7-eee8435ac1c7",
  "target_instances": ["i-0fe60964746c77041", "i-0a824284f8c887f4a"],
  "total_instances": 2,
  "instance_estimations": {
    "i-0fe60964746c77041": {
      "estimated_minutes": 1.09,
      "volume_count": 1,
      "total_gb": 8,
      "instance_type": "t3.xlarge"
    },
    "i-0a824284f8c887f4a": {
      "estimated_minutes": 6.89,
      "volume_count": 3,
      "total_gb": 208,
      "instance_type": "m5.4xlarge"
    }
  },
  "total_estimated_minutes": 6.89
}
```

## Prerequisites

- AWS CLI configured with appropriate permissions
- EC2 instances must have Systems Manager agent installed
- **Supported Operating Systems:**
  - Amazon Linux 2
  - Amazon Linux 2023
  - Red Hat Enterprise Linux (RHEL)
  - Ubuntu (18.04, 20.04, 22.04, 24.04)
  - SUSE Linux Enterprise Server (SLES)
- Required IAM permissions:
  - `ec2:DescribeVolumes`
  - `ec2:DescribeInstances`
  - `ssm:SendCommand`
  - `ssm:GetCommandInvocation`
  - `ssm:PutParameter`
  - `ssm:GetParameter`
  - `ssm:DeleteParameter`

## AWS IAM Permissions

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeVolumes",
                "ec2:DescribeInstances",
                "ssm:SendCommand",
                "ssm:GetCommandInvocation",
                "ssm:PutParameter",
                "ssm:GetParameter",
                "ssm:DeleteParameter"
            ],
            "Resource": "*"
        }
    ]
}
```

## Configuration

### Environment Variables

The server automatically detects AWS region from environment variables:

```bash
# Option 1: AWS_DEFAULT_REGION (preferred)
export AWS_DEFAULT_REGION=ap-northeast-2

# Option 2: AWS_REGION (also supported)  
export AWS_REGION=ap-northeast-2
```

**Priority order:**
1. `AWS_DEFAULT_REGION` environment variable
2. `AWS_REGION` environment variable  
3. Fallback to `us-east-1`

### MCP Configuration

```json
{
  "mcpServers": {
    "ebs-initializer": {
      "command": "uvx",
      "args": ["ebs-initializer-mcp@latest"],
      "env": {
        "AWS_DEFAULT_REGION": "ap-northeast-2"
      }
    }
  }
}
```

## Architecture

### Modular Design

The codebase is organized into focused modules for maintainability and reusability:

```
src/ebs_init_mcp/
├── server.py           # MCP server and tool definitions (430 lines)
├── aws_clients.py      # AWS client caching and management
├── throughput.py       # EBS throughput calculation
├── estimation.py       # Time estimation algorithms
├── initialization.py   # Command generation for volume initialization
├── status.py          # Status checking and progress calculation
└── utils.py           # Utility functions and device mapping scripts
```

### Time Estimation Logic

#### 1. `initialize_all_volumes` (Parallel Initialization)

**Algorithm**: Simulates parallel processing with throughput sharing

```python
# Step 1: Get instance EBS throughput
instance_throughput = get_instance_ebs_throughput(instance_type)

# Step 2: Collect volume data
volumes = [{'size_gb': size, 'max_throughput_mbps': vol_throughput}...]

# Step 3: AWS EBS throughput allocation algorithm
while volumes_remaining:
    total_demand = sum(vol_throughput for each volume)
    
    if total_demand <= instance_throughput:
        # Each volume gets its maximum throughput
        allocated_throughputs = [vol_max_throughput for each volume]
    else:
        # AWS EBS allocation: smaller volumes get priority
        fair_share = instance_throughput / len(volumes_remaining)
        
        # First pass: allocate full throughput to volumes <= fair_share
        for volume in volumes_remaining:
            if volume.max_throughput <= fair_share:
                volume.allocated = volume.max_throughput
                remaining_throughput -= volume.max_throughput
        
        # Second pass: distribute remaining among larger volumes
        remaining_large_volumes = volumes with throughput > fair_share
        throughput_per_large = remaining_throughput / len(remaining_large_volumes)
        for volume in remaining_large_volumes:
            volume.allocated = throughput_per_large
    
    # Calculate completion times and process next step
    completion_times = [(size * 1024) / allocated_throughput / 60 for each volume]
```

**Example**: t3.large (500MB/s) with 3 volumes:
- Volume 1: 100GB/125MB/s, Volume 2: 100GB/1000MB/s, Volume 3: 100GB/1000MB/s  
- Total demand: 2125MB/s > 500MB/s (exceeds instance limit)
- Allocation: Vol1=125MB/s, Vol2=187.5MB/s, Vol3=187.5MB/s
- Result: Vol2&3 finish at 9.1min, Vol1 continues alone → 13.7min total

#### 2. `initialize_volume_by_id` (Single Volume)

**Algorithm**: Simple throughput-limited calculation

```python
# Step 1: Get throughput constraints
instance_throughput = get_instance_ebs_throughput(instance_type)
volume_throughput = volume.get('Throughput', 1000)

# Step 2: Calculate effective throughput (bottleneck)
effective_throughput = min(volume_throughput, instance_throughput)

# Step 3: Linear time calculation
estimated_minutes = (size_gb * 1024 MB) / effective_throughput / 60
```

**Example**: 100GB volume, t3.large (500MB/s), gp3 (1000MB/s)
- Effective: min(1000, 500) = 500MB/s
- Time: (100 × 1024) / 500 / 60 = **3.4 minutes**


## Development

```bash
git clone <repository>
cd ebs-init-mcp

# Install dependencies
uv sync

# Run development server
AWS_REGION=ap-northeast-2 uv run mcp dev src/ebs_init_mcp/server.py

# Run tests
uv run pytest

# Format code
uv run ruff format src/
uv run ruff check src/
```

## License

MIT License
