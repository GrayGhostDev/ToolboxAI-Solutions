# 🧹 ToolBoxAI Intelligent Cleanup System

## Overview
Comprehensive cleanup and optimization system for the ToolBoxAI Educational Platform, based on the CLEANUP_INTEGRATED.md orchestrator design.

## 🚀 Quick Start

### Run Standard Cleanup
```bash
# Preview what will be cleaned (dry run)
python scripts/terminal_sync/intelligent_cleanup.py --dry-run

# Run standard cleanup
python scripts/terminal_sync/intelligent_cleanup.py

# Run aggressive cleanup
python scripts/terminal_sync/intelligent_cleanup.py --aggressive
```

### Emergency Cleanup
```bash
# Run emergency cleanup (for critical disk space)
./scripts/terminal_sync/emergency_cleanup.sh

# Force cleanup even if disk usage is healthy
./scripts/terminal_sync/emergency_cleanup.sh --force
```

### Monitor System Health
```bash
# Generate cleanup monitoring report
python scripts/terminal_sync/cleanup_monitor.py
```

### Setup Automatic Scheduling
```bash
# Setup cron jobs for automatic cleanup
./scripts/terminal_sync/setup_automatic_cleanup.sh
```

## 📁 Components

### 1. **intelligent_cleanup.py**
Main cleanup orchestrator with modular cleaners:
- **PythonCleaner**: Removes __pycache__, *.pyc, .pytest_cache, etc.
- **NodeCleaner**: Cleans node_modules and npm/yarn caches
- **LogCleaner**: Archives and rotates log files
- **GitCleaner**: Runs git garbage collection

### 2. **emergency_cleanup.sh**
Aggressive cleanup for critical disk space situations:
- Triggers at 95% disk usage threshold
- Removes all temporary files
- Clears all caches aggressively
- Suitable for emergency recovery

### 3. **cleanup_monitor.py**
Monitoring and reporting system:
- Tracks disk usage and project size
- Counts cleanable artifacts
- Generates health reports
- Provides recommendations

### 4. **setup_automatic_cleanup.sh**
Configures cron jobs for scheduled cleanup:
- Daily cleanup at 3 AM (Python, Node, logs)
- Weekly deep cleanup on Sunday at 2 AM
- Emergency check every 6 hours

## 📊 Cleanup Statistics

### Initial Cleanup Results
- **Before**: 2.2 GB project size
- **After**: 1.5 GB project size
- **Space Freed**: ~700 MB
- **Items Removed**: 23,562 files

### What Gets Cleaned

#### Python Artifacts
- `__pycache__` directories
- `*.pyc` and `*.pyo` files
- `.pytest_cache` directories
- `.coverage` files
- `htmlcov` directories
- `dist` and `build` directories
- `*.egg-info` directories
- Virtual environments (if unused > 7 days)

#### Node.js Artifacts
- `node_modules` directories
- `.next` and `.nuxt` directories
- `coverage` directories
- `.nyc_output` directories
- Package manager caches

#### Other
- Log files (archived if > 7 days, deleted if > 30 days)
- Git repository optimization
- Temporary files

## 🎯 Usage Scenarios

### Daily Maintenance
```bash
python scripts/terminal_sync/intelligent_cleanup.py --type python node logs
```

### Before Deployment
```bash
python scripts/terminal_sync/intelligent_cleanup.py --aggressive
```

### Space Recovery
```bash
./scripts/terminal_sync/emergency_cleanup.sh
```

### Health Check
```bash
python scripts/terminal_sync/cleanup_monitor.py
```

## ⚙️ Configuration

### Cleanup Thresholds
- **Archive logs**: After 7 days
- **Delete logs**: After 30 days
- **Clean venv**: If unused for 7 days
- **Emergency trigger**: At 95% disk usage

### Cron Schedule
```cron
# Daily cleanup at 3 AM
0 3 * * * /usr/bin/python3 /path/to/intelligent_cleanup.py --type python node logs

# Weekly deep cleanup on Sunday at 2 AM
0 2 * * 0 /usr/bin/python3 /path/to/intelligent_cleanup.py --aggressive

# Emergency check every 6 hours
0 */6 * * * /path/to/emergency_cleanup.sh
```

## 📈 Monitoring

### View Cleanup History
```bash
ls -la logs/cleanup/cleanup_*.json
```

### Check Current Status
```bash
df -h /Volumes/G-DRIVE\ ArmorATD
du -sh /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions
```

### Generate Report
```bash
python scripts/terminal_sync/cleanup_monitor.py
```

## 🛡️ Safety Features

1. **Dry Run Mode**: Preview changes before execution
2. **Selective Cleaning**: Choose specific cleanup types
3. **Protected Directories**: Skips production and backup directories
4. **Usage Checks**: Virtual environments checked for recent activity
5. **Logging**: All operations logged with timestamps

## 🔧 Troubleshooting

### Cleanup Taking Too Long
Use specific cleanup types instead of all:
```bash
python scripts/terminal_sync/intelligent_cleanup.py --type python
python scripts/terminal_sync/intelligent_cleanup.py --type node
```

### Permission Errors
Run with appropriate permissions:
```bash
sudo python scripts/terminal_sync/intelligent_cleanup.py
```

### Cron Jobs Not Running
Check cron service:
```bash
# List current jobs
crontab -l

# Check cron logs
grep CRON /var/log/syslog
```

## 📝 Best Practices

1. **Run dry-run first** to preview what will be deleted
2. **Regular monitoring** with cleanup_monitor.py
3. **Backup important data** before aggressive cleanup
4. **Use selective cleaning** for faster execution
5. **Check disk usage** after major operations

## 🚨 Emergency Procedures

If disk space becomes critical:

1. **Immediate Action**:
   ```bash
   ./scripts/terminal_sync/emergency_cleanup.sh
   ```

2. **Manual Cleanup**:
   ```bash
   # Remove all Python artifacts
   find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
   find . -type f -name "*.pyc" -delete
   
   # Remove all node_modules
   find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null
   
   # Clear all caches
   npm cache clean --force
   pip cache purge
   ```

3. **Check Results**:
   ```bash
   df -h /Volumes/G-DRIVE\ ArmorATD
   ```

## 📊 Success Metrics

- ✅ Disk usage maintained below 80%
- ✅ Zero duplicate dependencies
- ✅ All test artifacts archived
- ✅ Log files rotated properly
- ✅ Git repository optimized
- ✅ Automatic cleanup running daily

## 🔄 Integration with Terminal Orchestrator

The cleanup system integrates with the terminal orchestrator design from CLEANUP_INTEGRATED.md:

- **Redis Integration**: Ready for message queue implementation
- **Cross-Terminal Communication**: Supports notifications to other terminals
- **Database Cleanup**: Prepared for PostgreSQL optimization
- **Docker Support**: Ready for container cleanup integration

---

*Intelligent Cleanup System v1.0.0*
*Based on CLEANUP_INTEGRATED.md orchestrator design*