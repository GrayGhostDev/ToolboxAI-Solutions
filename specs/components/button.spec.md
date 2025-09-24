# Button Component Specification

## Overview
The Button component is a fundamental interactive element used throughout the ToolBoxAI platform for triggering actions, navigation, and form submissions.

## Design Principles
- **Clear Action Intent**: Button text should clearly indicate what will happen when clicked
- **Educational Context**: Button styling should reflect the educational nature of actions
- **Accessibility First**: All buttons must be keyboard navigable and screen reader friendly
- **Consistent Interaction**: Similar actions should use similar button styles across the platform

## Variants

### Primary
- **Use case**: Main actions, form submissions, primary navigation
- **Styling**: Filled with primary color (#1976d2)
- **Examples**: "Submit Assignment", "Create Class", "Save Lesson"

### Secondary
- **Use case**: Secondary actions, alternative options
- **Styling**: Outlined with primary color
- **Examples**: "Cancel", "Preview", "Skip"

### Success
- **Use case**: Positive actions, completion states
- **Styling**: Filled with success color (#2e7d32)
- **Examples**: "Publish Lesson", "Mark Complete", "Approve"

### Warning
- **Use case**: Important actions that require attention
- **Styling**: Filled with warning color (#f57c00)
- **Examples**: "Archive Class", "Reset Progress", "Unpublish"

### Danger
- **Use case**: Destructive actions, deletions
- **Styling**: Filled with error color (#d32f2f)
- **Examples**: "Delete Assignment", "Remove Student", "Permanently Delete"

## Sizes

### Small
- **Height**: 32px
- **Padding**: 8px 16px
- **Font Size**: 14px
- **Use case**: Compact interfaces, table actions, secondary controls

### Medium (Default)
- **Height**: 40px
- **Padding**: 10px 20px
- **Font Size**: 16px
- **Use case**: Standard forms, primary actions, general interface

### Large
- **Height**: 48px
- **Padding**: 12px 24px
- **Font Size**: 18px
- **Use case**: Landing pages, prominent calls-to-action, mobile interfaces

## States

### Default
- Standard appearance with full opacity and no additional styling

### Hover
- Slight darkening of background color (darken by 8%)
- Subtle elevation increase for filled buttons
- Smooth transition (300ms)

### Active/Pressed
- Further darkening of background color (darken by 12%)
- Slightly reduced elevation
- Immediate visual feedback

### Focus
- Clear focus ring using primary color
- 2px solid outline with 2px offset
- Visible on keyboard navigation

### Disabled
- 50% opacity reduction
- Cursor changes to 'not-allowed'
- No hover or active states
- Clear visual indication that action is unavailable

### Loading
- Spinner icon replaces text or appears alongside text
- Button remains same size to prevent layout shift
- Disabled state while loading
- Clear indication that action is in progress

## Content Guidelines

### Text
- Use action verbs: "Create", "Save", "Delete", "Submit"
- Be specific about the action: "Save Draft" vs "Save"
- Keep text concise: 1-3 words when possible
- Use sentence case: "Create assignment" not "Create Assignment"

### Icons
- Support both leading and trailing icons
- Icons should reinforce the action (save icon for save actions)
- Maintain 16px icon size for medium buttons
- 4px spacing between icon and text

## Accessibility Requirements

### Keyboard Navigation
- Tab focus order follows logical reading order
- Enter and Space keys trigger button action
- Focus indicators are clearly visible
- No keyboard traps

### Screen Readers
- Button text clearly describes the action
- Loading states announced to screen readers
- Disabled states communicated appropriately
- Context provided when button purpose isn't clear from text alone

### Visual
- Minimum 44px touch target size on mobile
- 4.5:1 color contrast ratio minimum
- Focus indicators visible for keyboard users
- Button purpose clear without relying on color alone

## Educational Context Usage

### Assignment Management
```typescript
// Primary action for assignment creation
<Button variant="primary" size="medium">
  Create Assignment
</Button>

// Secondary action for drafts
<Button variant="secondary" size="medium">
  Save as Draft
</Button>
```

### Grading Actions
```typescript
// Success state for approval
<Button variant="success" size="small" icon="check">
  Approve Grade
</Button>

// Warning for grade changes
<Button variant="warning" size="small">
  Modify Grade
</Button>
```

### Class Management
```typescript
// Danger state for destructive actions
<Button variant="danger" size="medium" icon="trash">
  Archive Class
</Button>
```

## Technical Implementation

### Props Interface
```typescript
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'leading' | 'trailing';
  fullWidth?: boolean;
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  type?: 'button' | 'submit' | 'reset';
  'aria-label'?: string;
  'aria-describedby'?: string;
  children: React.ReactNode;
}
```

### Material-UI Integration
- Extend MUI Button component
- Override theme colors with educational palette
- Maintain MUI accessibility features
- Add educational-specific variants

## Testing Requirements

### Unit Tests
- All variant and size combinations render correctly
- Click handlers execute properly
- Disabled state prevents interactions
- Loading state displays spinner and disables interaction

### Accessibility Tests
- Focus management works correctly
- Screen reader announcements are appropriate
- Keyboard navigation functions properly
- Color contrast meets requirements

### Visual Regression Tests
- Component appears consistently across browsers
- State changes render correctly
- Icon and text alignment is maintained
- Responsive behavior works properly

## Examples

### Form Submission
```tsx
<Stack direction="row" spacing={2}>
  <Button variant="primary" type="submit" loading={isSubmitting}>
    {isSubmitting ? 'Creating...' : 'Create Assignment'}
  </Button>
  <Button variant="secondary" onClick={onCancel}>
    Cancel
  </Button>
</Stack>
```

### Destructive Action with Confirmation
```tsx
<Button
  variant="danger"
  onClick={handleDelete}
  aria-describedby="delete-warning"
>
  Delete Class
</Button>
```

### Icon Button for Quick Actions
```tsx
<Button
  variant="secondary"
  size="small"
  icon={<EditIcon />}
  aria-label="Edit assignment"
>
  Edit
</Button>
```

This specification ensures consistent, accessible, and educationally-appropriate button usage throughout the ToolBoxAI platform.