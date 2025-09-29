# Fix Python Extension Notification Issue

## Problem
Cursor keeps asking to install the recommended 'Python' extension from Anysphere even though it's already installed.

## Solution Applied

### 1. Updated Extensions Configuration
- Changed from `ms-python.python` to `anysphere.python`
- Changed from `ms-python.vscode-pylance` to `anysphere.pylance`
- Added `unwantedRecommendations` to block Microsoft extensions

### 2. Updated VS Code Settings
- Set `python.languageServer` to "Pylance"
- Added extension management settings
- Updated Python interpreter path

## Manual Steps to Complete

### Step 1: Reload Window
1. Press `Cmd+Shift+P`
2. Type "Developer: Reload Window"
3. Press Enter

### Step 2: Check Installed Extensions
1. Press `Cmd+Shift+X` (Extensions view)
2. Search for "Python"
3. Verify you have:
   - ✅ **Python** by Anysphere (anysphere.python)
   - ✅ **Pylance** by Anysphere (anysphere.pylance)
   - ❌ **Python** by Microsoft (ms-python.python) - should be disabled/uninstalled

### Step 3: Disable Conflicting Extensions
If you see Microsoft Python extensions:
1. Click the gear icon next to "Python" by Microsoft
2. Select "Disable" or "Uninstall"
3. Do the same for "Pylance" by Microsoft

### Step 4: Verify Python Interpreter
1. Press `Cmd+Shift+P`
2. Type "Python: Select Interpreter"
3. Select: `/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/ToolboxAI-Roblox-Environment/venv_clean/bin/python`

## Expected Result
- No more notification about installing Python extension
- Python language features work correctly
- Type checking and IntelliSense work properly

## Troubleshooting

If the notification still appears:

1. **Clear Extension Cache**:
   - Close Cursor completely
   - Delete `~/.cursor/extensions` folder
   - Restart Cursor

2. **Reset Workspace Settings**:
   - Delete `.vscode/settings.json`
   - Restart Cursor
   - Reapply the settings

3. **Check Extension Conflicts**:
   - Look for multiple Python extensions
   - Disable all except Anysphere's Python extension

## Files Modified
- `.vscode/extensions.json` - Extension recommendations
- `.vscode/settings.json` - Python configuration
- `pyproject.toml` - Pyright configuration
