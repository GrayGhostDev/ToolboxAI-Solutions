# Build Issues Resolution Guide - 2025

## 🚨 **Current Build Issues and Solutions**

This document provides comprehensive solutions for all build issues encountered during the MUI to Mantine v8 migration and Pusher integration.

## 🔧 **Critical Build Errors**

### **1. Icon Import Errors**

#### **Issue**: Tabler Icon Names Incorrect
```bash
Error: "IconGamepad2" is not exported by "@tabler/icons-react"
Error: "IconTerrain" is not exported by "@tabler/icons-react"
Error: "IconCircleCheck" is not exported by "@tabler/icons-react"
```

#### **Root Cause**:
Tabler Icons v3.x changed many icon names. Old imports are using deprecated names.

#### **✅ Solution**: Update Icon Imports
```typescript
// ❌ Incorrect (Old Names)
import {
  IconGamepad2,
  IconTerrain,
  IconCircleCheck,
  Icon3dRotation,
  IconFocusCentered
} from '@tabler/icons-react';

// ✅ Correct (2025 Names)
import {
  IconDeviceGamepad2,    // Gaming controller
  IconMountain,          // Terrain/landscape
  IconCheck,             // Check mark
  IconRotate,            // 3D rotation
  IconFocus2             // Focus/center
} from '@tabler/icons-react';
```

#### **Complete Icon Mapping Table**
| Old Name | New Name | Usage |
|----------|----------|-------|
| `IconGamepad2` | `IconDeviceGamepad2` | Gaming controls |
| `IconTerrain` | `IconMountain` | Landscape/terrain |
| `IconCircleCheck` | `IconCheck` | Success states |
| `Icon3dRotation` | `IconRotate` | 3D controls |
| `IconFocusCentered` | `IconFocus2` | Focus controls |
| `IconMemory` | `IconCpu` | System resources |

### **2. JSX Syntax Errors**

#### **Issue**: Mismatched Opening/Closing Tags
```bash
Error: Unexpected closing "div" tag does not match opening "CardContent" tag
Error: Unexpected closing "Box" tag does not match opening "Group" tag
```

#### **Root Cause**:
Mixed MUI and Mantine components with inconsistent tag matching during conversion.

#### **✅ Solution**: Systematic Component Replacement
```typescript
// ❌ Mixed MUI/Mantine (Causes Errors)
<Card>           // MUI
  <CardContent>  // MUI
    <Box>        // Mantine
      <Group>    // Mantine
      </Group>
    </Box>
  </div>        // ❌ Wrong closing tag
</div>          // ❌ Wrong closing tag

// ✅ Pure Mantine (Correct)
<Card>                    // Mantine
  <Card.Section>          // Mantine
    <Box>                 // Mantine
      <Group>             // Mantine
      </Group>
    </Box>
  </Card.Section>
</Card>
```

### **3. Import Path Resolution Errors**

#### **Issue**: Missing Import Paths
```bash
Error: Could not resolve "../config/api" from "src/services/observability.ts"
```

#### **Root Cause**:
Import paths changed during restructuring but not updated in all files.

#### **✅ Solution**: Update Import Paths
```typescript
// ❌ Incorrect Path
import { API_BASE_URL } from '../config/api';

// ✅ Correct Path
import { API_BASE_URL } from '../config';
```

## 🛠 **Systematic Resolution Strategy**

### **Phase 1: Fix Critical Build Blockers**

#### **Step 1: Update All Icon Imports**
```bash
# Find all files with problematic icon imports
grep -r "IconGamepad2\|IconTerrain\|IconCircleCheck\|Icon3dRotation\|IconFocusCentered" apps/dashboard/src/

# Files identified:
- src/components/roblox/RobloxControlPanel.tsx ✅ FIXED
- src/components/roblox/RobloxAIAssistant.tsx ✅ FIXED
- src/components/roblox/RobloxEnvironmentPreview.tsx ✅ FIXED
- src/components/pages/Messages.tsx ✅ FIXED
- src/components/widgets/StudentProgressTracker.tsx ✅ FIXED
- src/components/widgets/RealTimeAnalytics.tsx ✅ FIXED
```

#### **Step 2: Fix JSX Syntax Errors**
```bash
# Strategy: Convert entire files to pure Mantine
# Completed conversions:
- src/components/roblox/RobloxEnvironmentPreview.tsx ✅ FIXED
- src/components/roblox/Simple3DIcon.tsx ✅ FIXED
```

#### **Step 3: Resolve Import Path Issues**
```bash
# Fixed import paths:
- src/services/observability.ts ✅ FIXED
```

### **Phase 2: Complete MUI Removal**

#### **High Priority Files (Blocking Build)**
```bash
# Critical components that need immediate conversion:
1. src/components/progress/StudentProgress.tsx
2. src/components/mcp/MCPAgentDashboard.tsx
3. src/components/admin/EnhancedAnalytics.tsx
4. src/components/admin/UserManagement.tsx
5. src/components/analytics/PerformanceIndicator.tsx
```

#### **Conversion Template**
```typescript
// Standard conversion pattern for each file:

// 1. Replace imports
import {
  Box,           // MUI → Mantine
  Card,          // MUI → Mantine
  Text,          // Typography → Text
  Title,         // Typography variant="h*" → Title
  Button,        // MUI → Mantine
  ActionIcon,    // IconButton → ActionIcon
  TextInput,     // TextField → TextInput
  Select,        // Select + MenuItem → Select
  Badge,         // Chip → Badge
  Progress,      // LinearProgress → Progress
  Loader,        // CircularProgress → Loader
  Alert,         // Alert → Alert
  Group,         // Stack direction="row" → Group
  Stack,         // Stack → Stack
  SimpleGrid,    // Grid → SimpleGrid
  Modal,         // Dialog → Modal
  Stepper,       // Stepper → Stepper
  Table,         // Table components → Table
} from '@mantine/core';

// 2. Replace component usage
<Typography variant="h4"> → <Title order={4}>
<Typography variant="body1"> → <Text>
<IconButton> → <ActionIcon>
<TextField> → <TextInput>
<LinearProgress> → <Progress>
<CircularProgress> → <Loader>

// 3. Update styling
sx={{ padding: 16 }} → style={{ padding: '1rem' }}
height={64} → h={64}
width="100%" → w="100%"

// 4. Update props
position="apart" → justify="space-between"
spacing="md" → gap="md"
icon={<Icon />} → leftSection={<Icon />}
```

## 🧪 **Testing and Validation**

### **Build Validation Process**
```bash
# 1. Check for MUI imports
grep -r "@mui/material" apps/dashboard/src/ && echo "❌ MUI imports found" || echo "✅ No MUI imports"

# 2. Check for sx props
grep -r "sx={{" apps/dashboard/src/ && echo "❌ sx props found" || echo "✅ No sx props"

# 3. Test build
cd apps/dashboard && npm run build

# 4. Test TypeScript
npm run typecheck

# 5. Test linting
npm run lint
```

### **Component Testing**
```typescript
// Test each converted component
import { render, screen } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import ConvertedComponent from './ConvertedComponent';

test('converted component renders correctly', () => {
  render(
    <MantineProvider>
      <ConvertedComponent />
    </MantineProvider>
  );

  expect(screen.getByRole('button')).toBeInTheDocument();
});
```

## 🔄 **Automated Fix Scripts**

### **Icon Import Fixer**
```bash
#!/bin/bash
# Fix all icon imports automatically

find apps/dashboard/src -name "*.tsx" -type f -exec sed -i '' \
  -e 's/IconGamepad2/IconDeviceGamepad2/g' \
  -e 's/IconTerrain/IconMountain/g' \
  -e 's/IconCircleCheck/IconCheck/g' \
  -e 's/Icon3dRotation/IconRotate/g' \
  -e 's/IconFocusCentered/IconFocus2/g' \
  {} \;

echo "✅ Icon imports updated"
```

### **MUI Import Replacer**
```bash
#!/bin/bash
# Replace common MUI imports with Mantine equivalents

find apps/dashboard/src -name "*.tsx" -type f -exec sed -i '' \
  -e 's/import.*from.*@mui\/material.*/\/\/ TODO: Convert to Mantine/g' \
  -e 's/Typography/Text/g' \
  -e 's/IconButton/ActionIcon/g' \
  -e 's/TextField/TextInput/g' \
  -e 's/LinearProgress/Progress/g' \
  -e 's/CircularProgress/Loader/g' \
  {} \;

echo "✅ Basic MUI replacements completed"
```

### **Styling Converter**
```bash
#!/bin/bash
# Convert sx props to style props

find apps/dashboard/src -name "*.tsx" -type f -exec sed -i '' \
  -e 's/sx={{/style={{/g' \
  -e 's/height={([0-9]+)}/h={\1}/g' \
  -e 's/width="100%"/w="100%"/g' \
  {} \;

echo "✅ Styling props updated"
```

## 📋 **Resolution Checklist**

### **For Each Component File**
- [ ] Remove all `@mui/material` imports
- [ ] Add required `@mantine/core` imports
- [ ] Update all component names (Typography → Text, etc.)
- [ ] Convert all props (sx → style, height → h, etc.)
- [ ] Update icon imports to correct Tabler names
- [ ] Fix JSX tag matching
- [ ] Test component renders without errors
- [ ] Verify functionality is preserved
- [ ] Check responsive behavior
- [ ] Validate accessibility

### **Build Validation**
- [ ] No MUI imports remain
- [ ] No sx props remain
- [ ] All icon imports are valid
- [ ] JSX syntax is correct
- [ ] TypeScript compiles without errors
- [ ] Vite build succeeds
- [ ] All tests pass

## 🚀 **Quick Fix Commands**

### **Immediate Build Fix**
```bash
# Navigate to project
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions

# Run automated fixes
./infrastructure/docker/scripts/fix-build-issues.sh

# Test build
cd apps/dashboard && npm run build

# If successful, deploy
cd ../../infrastructure/docker/compose
docker-compose --env-file ../config/environment.env up -d
```

### **Emergency Deployment (Skip UI Issues)**
```bash
# Deploy backend services only (working)
docker-compose up -d postgres redis backend mcp-server agent-coordinator

# Access backend directly
curl http://localhost:8009/health
```

## 📊 **Progress Tracking**

### **Issue Resolution Status**
- ✅ **Icon Import Fixes**: 6/6 identified files fixed
- ✅ **JSX Syntax Fixes**: 2/2 critical files fixed
- ✅ **Import Path Fixes**: 1/1 identified files fixed
- 🔄 **MUI Conversion**: 8/149 files completed
- 🔄 **Build Stabilization**: In progress

### **Next Milestone**
**Target**: Clean `npm run build` with no errors
**ETA**: 1-2 days with systematic conversion
**Blocker**: Remaining MUI dependencies in 141 files

---

**Status**: 🔄 **Active Resolution**
**Priority**: **Critical** (blocking production frontend)
**Approach**: **Systematic conversion** following established patterns
