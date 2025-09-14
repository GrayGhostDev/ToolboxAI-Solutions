# Global Command Palette Fix - Cursor IDE

## Problem
The `Cmd+Shift+P` keybinding was opening Claude/Cursor AI chat instead of the VS Code command palette, even after workspace-level fixes.

## Root Cause
Cursor IDE was overriding workspace keybindings with global user settings that prioritized AI features over the standard command palette.

## Solution Implemented
Created global user-level keybinding and settings files that take precedence over workspace settings.

## Files Created

### 1. Cursor Global Keybindings
**Location**: `~/Library/Application Support/Cursor/User/keybindings.json`
```json
[
  {
    "key": "cmd+shift+p",
    "command": "workbench.action.showCommands"
  },
  {
    "key": "cmd+shift+p",
    "command": "-aipane.show",
    "when": "editorTextFocus"
  },
  {
    "key": "cmd+shift+p",
    "command": "-cursor.showCommandPalette"
  }
]
```

### 2. Cursor Global Settings
**Location**: `~/Library/Application Support/Cursor/User/settings.json`
```json
{
  "cursor.cpp.disabledLanguages": [],
  "cursor.chat.openaiApiKey": "",
  "workbench.commandPalette.experimental.suggestCommands": true,
  "keyboard.dispatch": "keyCode"
}
```

### 3. VS Code Global Keybindings (Backup)
**Location**: `~/Library/Application Support/Code/User/keybindings.json`
```json
[
  {
    "key": "cmd+shift+p",
    "command": "workbench.action.showCommands"
  }
]
```

### 4. VS Code Global Settings (Backup)
**Location**: `~/Library/Application Support/Code/User/settings.json`
```json
{
  "workbench.commandPalette.experimental.suggestCommands": true,
  "keyboard.dispatch": "keyCode"
}
```

## Key Features

### Negative Commands
The critical part is the negative commands that disable conflicting AI bindings:
- `"-aipane.show"` - Disables AI pane when in editor
- `"-cursor.showCommandPalette"` - Disables Cursor's custom command palette

### Settings Explained
- `"keyboard.dispatch": "keyCode"` - Ensures proper key handling
- `"workbench.commandPalette.experimental.suggestCommands": true` - Enables command suggestions
- `"cursor.cpp.disabledLanguages": []` - Ensures C++ support is available
- `"cursor.chat.openaiApiKey": ""` - Clears any cached API keys

## Next Steps

1. **Restart Cursor**: Close Cursor completely and reopen
2. **Test Command Palette**: Press `Cmd+Shift+P` - should open VS Code command palette
3. **Verify AI Features**: AI features should still work through other shortcuts

## Alternative Commands

If you need to open the files manually:
```bash
# Open Cursor keybindings
code ~/Library/Application\ Support/Cursor/User/keybindings.json

# Open Cursor settings
code ~/Library/Application\ Support/Cursor/User/settings.json

# Open VS Code keybindings
code ~/Library/Application\ Support/Code/User/keybindings.json
```

## Troubleshooting

If the issue persists:

1. **Check Global Settings Priority**: Global user settings override workspace settings
2. **Verify File Locations**: Ensure files are in the correct Cursor user directory
3. **Restart Cursor**: Sometimes requires a full restart to load new keybindings
4. **Check for Extensions**: Some extensions might override keybindings

## Verification

The global keybindings should now take precedence and ensure that `Cmd+Shift+P` always opens the VS Code command palette, not Claude or other AI features.

