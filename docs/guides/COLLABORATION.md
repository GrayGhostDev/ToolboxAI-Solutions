# ToolBoxAI Real-Time Collaboration Guide

This guide explains how to set up real-time collaboration for the ToolBoxAI-Solutions project across multiple macOS devices.

## 🚀 Quick Start

### On the Primary Machine (First Setup)
```bash
# 1. Run the collaboration setup script
./scripts/collaboration/collab-setup.sh

# 2. Set up Tailscale VPN (optional but recommended)
./infrastructure/collaboration/tailscale-setup.sh

# 3. Start shared services
docker compose -f docker-compose.collab.yml up -d

# 4. Check collaboration status
./scripts/collaboration/collab-status.sh
```

### On Secondary Machines
```bash
# 1. Clone the repository
git clone https://github.com/GrayGhostDev/ToolboxAI-Solutions.git
cd ToolBoxAI-Solutions

# 2. Run collaboration setup
./scripts/collaboration/collab-setup.sh

# 3. Copy .env.local.template to .env.local and configure
cp .env.local.template .env.local
# Edit .env.local with your PRIMARY_HOST IP

# 4. Start collaborating!
code .  # or cursor .
```

## 📋 Prerequisites

- macOS (tested on macOS 14+)
- Git
- VS Code or Cursor IDE
- Docker Desktop (optional, for shared services)
- Node.js 18+ and Python 3.11+

## 🔧 Collaboration Methods

### 1. VS Code Live Share (Recommended for Real-Time)

**Features:**
- Real-time collaborative editing
- Shared terminals and debugging
- Voice calls and chat
- Port forwarding

**Setup:**
1. Install the Live Share extension (automatic with our setup)
2. Sign in with GitHub or Microsoft account
3. Start a session: `Cmd+Shift+P` → "Live Share: Start Collaboration Session"
4. Share the link with collaborators

**Joining:**
1. Click on the shared link
2. Opens in VS Code/Cursor automatically
3. Full access to project, terminals, and debugging

### 2. Syncthing (File Synchronization)

**Features:**
- Automatic file synchronization
- Works offline
- Peer-to-peer (no cloud required)
- Conflict resolution

**Setup:**
1. Install Syncthing: `brew install syncthing`
2. Start service: `syncthing serve`
3. Access UI: http://localhost:8384
4. Add remote devices using their Device IDs

### 3. Git with Auto-Sync

**Features:**
- Automatic push/pull on commits
- Branch protection
- Merge conflict prevention

**Workflow:**
```bash
# Changes are automatically synced
git commit -m "Your changes"
# Hook automatically pushes to remote

# Manual sync if needed
./scripts/collaboration/collab-sync.sh
```

### 4. Tailscale VPN (Network Access)

**Features:**
- Secure peer-to-peer VPN
- Access services on any machine
- Works behind NAT/firewalls
- MagicDNS for easy hostnames

**Setup:**
1. Run: `./infrastructure/collaboration/tailscale-setup.sh`
2. Log in when prompted
3. Share your Tailscale IP with team

**Accessing Services:**
```bash
# Connect to PostgreSQL on primary machine
psql postgresql://eduplatform:eduplatform2024@100.x.x.x:5432/educational_platform_dev

# Or use the helper script
./scripts/collaboration/tailscale-connect.sh postgres
```

## 📁 Project Structure for Collaboration

```
ToolBoxAI-Solutions/
├── .env.shared           # Shared environment variables
├── .env.local           # Machine-specific overrides (not committed)
├── .stignore            # Syncthing ignore patterns
├── .collaboration/      # Collaboration metadata
├── infrastructure/
│   └── collaboration/   # Collaboration configs
├── scripts/
│   └── collaboration/   # Helper scripts
└── docker-compose.collab.yml  # Shared services
```

## 🔄 Synchronization Workflow

### Real-Time Editing (VS Code Live Share)
1. Host starts Live Share session
2. Collaborators join via link
3. All edits are synchronized instantly
4. Changes saved to host's file system
5. Host commits changes to Git

### File Sync (Syncthing)
1. Files changed on any machine
2. Syncthing detects changes (1-3 seconds)
3. Syncs to all connected devices
4. Conflicts saved as `.sync-conflict` files

### Git Sync
1. Developer makes changes
2. Commits locally
3. Post-commit hook pushes to GitHub
4. Other machines pull automatically

## 🐳 Shared Services Configuration

### Starting Services on Primary Machine
```bash
# Start all collaboration services
docker compose -f docker-compose.collab.yml up -d

# Check status
docker compose -f docker-compose.collab.yml ps

# View logs
docker compose -f docker-compose.collab.yml logs -f
```

### Connecting from Secondary Machines

Update `.env.local`:
```env
PRIMARY_HOST=192.168.1.100  # Primary machine's IP
# Or use Tailscale IP
PRIMARY_HOST=100.64.0.1
```

Then services are automatically configured to connect to the primary host.

## 🛠️ Helper Scripts

### `collab-setup.sh`
Initial setup for collaboration environment:
- Installs VS Code extensions
- Configures Git for collaboration
- Sets up Syncthing (optional)
- Creates machine profile

### `collab-sync.sh`
Force synchronization of all changes:
- Git pull/push
- Dependency updates
- Cache clearing
- Syncthing rescan

Options:
- `--push`: Push local changes only
- `--pull`: Pull remote changes only

### `collab-status.sh`
Monitor collaboration environment:
- Service status
- Network connectivity
- Git sync status
- Active collaborators

Options:
- `--watch`: Continuous monitoring
- `--json`: JSON output
- `--notify`: Desktop notifications

## 🔒 Security Considerations

### Network Security
- **Tailscale**: End-to-end encrypted VPN
- **Local Network**: Use firewall rules
- **Public Network**: Always use VPN

### Access Control
- Git branch protection
- Database user permissions
- Service authentication (JWT)
- VS Code Live Share permissions

### Sensitive Data
- Never commit `.env.local`
- Use environment variables for secrets
- Rotate credentials regularly
- Use secret management tools

## 🚨 Troubleshooting

### VS Code Live Share Issues

**Can't start session:**
```bash
# Reinstall extension
code --uninstall-extension ms-vsliveshare.vsliveshare
code --install-extension ms-vsliveshare.vsliveshare

# Sign out and back in
Cmd+Shift+P → "Live Share: Sign Out"
Cmd+Shift+P → "Live Share: Sign In"
```

### Syncthing Not Syncing

**Check status:**
```bash
# View Syncthing logs
syncthing serve -verbose

# Force rescan
curl -X POST -H "X-API-Key: {{SYNCTHING_API_KEY}}" \
  http://localhost:8384/rest/db/scan?folder=toolboxai-dev

# Check ignore patterns
cat .stignore
```

### Git Conflicts

**Resolve conflicts:**
```bash
# See conflict status
git status

# Pull with rebase
git pull --rebase origin main

# If conflicts, resolve then:
git add .
git rebase --continue
```

### Port Already in Use

**Find and kill process:**
```bash
# Find process using port
lsof -i :8009

# Kill process
kill -9 <PID>

# Or use different port in .env.local
API_PORT=8010
```

### Docker Services Not Accessible

**Check network:**
```bash
# List Docker networks
docker network ls

# Inspect network
docker network inspect toolboxai-collab-network

# Recreate if needed
docker compose -f docker-compose.collab.yml down
docker compose -f docker-compose.collab.yml up -d
```

## 📊 Monitoring

### Service Health
```bash
# Check all services
./scripts/collaboration/collab-status.sh

# Continuous monitoring
./scripts/collaboration/collab-status.sh --watch

# JSON output for automation
./scripts/collaboration/collab-status.sh --json
```

### Grafana Dashboard
Access at: http://PRIMARY_HOST:3000
- Username: admin
- Password: {{GRAFANA_PASSWORD}}  # set via secrets manager or .env on PRIMARY_HOST

### Logs
```bash
# Backend logs
docker compose -f docker-compose.collab.yml logs backend

# All services
docker compose -f docker-compose.collab.yml logs -f

# Syncthing logs
syncthing serve -verbose
```

## 🎯 Best Practices

### Communication
1. Use Live Share chat for quick questions
2. Create Git issues for tasks
3. Use conventional commits
4. Document changes in PR descriptions

### Code Synchronization
1. Commit frequently (small commits)
2. Pull before starting work
3. Push immediately after commits
4. Use feature branches

### Conflict Prevention
1. Communicate before editing same files
2. Use different feature branches
3. Assign ownership of modules
4. Regular sync meetings

### Performance
1. Exclude large files from Syncthing
2. Use shallow clones for large repos
3. Limit Docker resource usage
4. Regular cleanup of caches

## 📝 Configuration Examples

### Multiple Development Environments

**Development (.env.local):**
```env
PRIMARY_HOST=100.64.0.1  # Dev server
ENVIRONMENT=development
DEBUG=true
```

**Staging (.env.local):**
```env
PRIMARY_HOST=100.64.0.2  # Staging server
ENVIRONMENT=staging
DEBUG=false
```

### Team Roles

**Backend Developer:**
```env
COLLABORATION_MODE=enabled
AUTO_SYNC_BACKEND=true
AUTO_SYNC_FRONTEND=false
```

**Frontend Developer:**
```env
COLLABORATION_MODE=enabled
AUTO_SYNC_BACKEND=false
AUTO_SYNC_FRONTEND=true
```

## 🔄 Migration from Solo to Collaboration

1. **Backup current work:**
   ```bash
   git stash
   git branch backup-$(date +%Y%m%d)
   ```

2. **Set up collaboration:**
   ```bash
   ./scripts/collaboration/collab-setup.sh
   ```

3. **Configure environment:**
   ```bash
   cp .env .env.backup
   cp .env.shared .env
   cat .env.local >> .env
   ```

4. **Test services:**
   ```bash
   ./scripts/collaboration/collab-status.sh
   ```

5. **Invite collaborators:**
   - Share Git repository access
   - Share Tailscale network
   - Share Live Share session

## 📚 Additional Resources

- [VS Code Live Share Docs](https://docs.microsoft.com/en-us/visualstudio/liveshare/)
- [Syncthing Documentation](https://docs.syncthing.net/)
- [Tailscale Documentation](https://tailscale.com/kb/)
- [Git Collaboration](https://www.atlassian.com/git/tutorials/syncing)

## 🤝 Support

For issues or questions:
1. Check `./scripts/collaboration/collab-status.sh`
2. Review logs in `.collaboration/logs/`
3. Run diagnostics: `./scripts/collaboration/collab-setup.sh --diagnose`
4. Open an issue in the GitHub repository

---

**Version:** 1.0.0
**Last Updated:** 2025-10-01
**Maintained By:** ToolBoxAI Development Team