# Form Patterns Specification

## Overview
Form patterns define consistent approaches to data collection and user input across the ToolBoxAI educational platform. These patterns ensure accessibility, usability, and educational context appropriateness.

## Core Principles

### 1. **Progressive Disclosure**
Complex forms should be broken into logical steps that match educational workflows.

### 2. **Immediate Feedback**
Validation and guidance should be provided in real-time to help users succeed.

### 3. **Error Prevention**
Forms should guide users toward valid inputs and prevent common mistakes.

### 4. **Educational Context**
Form design should reflect the educational nature of the data being collected.

## Form Types

### 1. Assignment Creation
**Context**: Teachers creating assignments for students
**Complexity**: High - Multiple steps, rich content, settings
**Pattern**: Multi-step wizard with preview

```
Step 1: Basic Information (Title, Subject, Grade Level)
Step 2: Instructions and Content (Rich text editor, attachments)
Step 3: Settings (Due date, grading criteria, submission types)
Step 4: Preview and Publish
```

### 2. Student Registration
**Context**: Adding new students to classes
**Complexity**: Medium - Personal info, class assignment
**Pattern**: Single page with grouped sections

```
Section 1: Student Information
Section 2: Parent/Guardian Contact
Section 3: Class Assignment
Section 4: Learning Preferences (optional)
```

### 3. Grade Entry
**Context**: Teachers entering grades for assignments
**Complexity**: Low - Simple data entry with validation
**Pattern**: Inline editing with batch operations

### 4. Class Settings
**Context**: Configuring class parameters and preferences
**Complexity**: Medium - Multiple categories of settings
**Pattern**: Tabbed interface with grouped controls

## Field Types and Validation

### Text Fields

#### Standard Text Input
```typescript
interface TextFieldProps {
  label: string;
  required?: boolean;
  helperText?: string;
  error?: boolean;
  errorText?: string;
  placeholder?: string;
  maxLength?: number;
  validation?: 'email' | 'url' | 'text' | 'number';
}
```

**Educational Examples**:
- Assignment titles (required, 1-100 characters)
- Student names (required, proper name validation)
- Email addresses (email format validation)

#### Rich Text Editor
**Use cases**: Assignment instructions, lesson content, feedback
**Features**:
- Basic formatting (bold, italic, lists)
- Link insertion with safety checks
- Image upload with size limits
- Mathematical formula support
- Accessibility-friendly markup generation

### Selection Fields

#### Dropdown Select
**Use cases**: Grade levels, subjects, assignment types
```typescript
interface SelectFieldProps {
  label: string;
  options: Array<{value: string; label: string; disabled?: boolean}>;
  required?: boolean;
  multiple?: boolean;
  searchable?: boolean;
}
```

#### Checkbox Groups
**Use cases**: Learning objectives, student permissions, notification preferences
```typescript
interface CheckboxGroupProps {
  label: string;
  options: Array<{value: string; label: string; description?: string}>;
  required?: boolean;
  minSelections?: number;
  maxSelections?: number;
}
```

#### Radio Button Groups
**Use cases**: Grading scales, assignment submission types, privacy settings
```typescript
interface RadioGroupProps {
  label: string;
  options: Array<{value: string; label: string; description?: string}>;
  required?: boolean;
  layout?: 'vertical' | 'horizontal';
}
```

### Date and Time Fields

#### Date Picker
**Use cases**: Assignment due dates, class schedules, event planning
```typescript
interface DateFieldProps {
  label: string;
  required?: boolean;
  minDate?: Date;
  maxDate?: Date;
  excludeDates?: Date[];
  helperText?: string;
}
```

#### Time Picker
**Use cases**: Class periods, meeting times, deadline times
```typescript
interface TimeFieldProps {
  label: string;
  required?: boolean;
  format?: '12h' | '24h';
  minuteStep?: number;
}
```

### File Upload

#### Single File Upload
**Use cases**: Assignment attachments, profile pictures, documents
```typescript
interface FileUploadProps {
  label: string;
  accept?: string; // MIME types or file extensions
  maxSize?: number; // in bytes
  required?: boolean;
  preview?: boolean;
  onUpload?: (file: File) => Promise<void>;
}
```

#### Multiple File Upload
**Use cases**: Assignment resources, portfolio submissions
```typescript
interface MultiFileUploadProps {
  label: string;
  accept?: string;
  maxSize?: number;
  maxFiles?: number;
  required?: boolean;
  onUpload?: (files: File[]) => Promise<void>;
}
```

## Validation Patterns

### Real-time Validation
- Validate on blur for individual fields
- Show success states for valid fields
- Provide immediate feedback for format errors
- Use debounced validation for expensive checks (uniqueness, availability)

### Error Handling
```typescript
interface FieldError {
  type: 'required' | 'format' | 'length' | 'custom';
  message: string;
  field: string;
}

interface FormErrors {
  [fieldName: string]: FieldError[];
}
```

### Success States
- Visual confirmation for successfully validated fields
- Progress indicators for multi-step forms
- Clear completion messaging

## Educational Context Patterns

### Grade-Appropriate Language
- Elementary: Simple, clear language with visual cues
- Middle School: More detailed explanations with examples
- High School: Professional terminology with comprehensive help
- Adult/Teacher: Technical accuracy with educational best practices

### Role-Based Forms
```typescript
interface FormContext {
  userRole: 'student' | 'teacher' | 'admin' | 'parent';
  gradeLevel?: 'elementary' | 'middle' | 'high' | 'college';
  subject?: string;
}
```

### Assignment-Specific Patterns

#### Multiple Choice Creation
```
Question Text: [Rich text editor]
Options: [Dynamic list with add/remove]
  Option A: [Text input] [Correct checkbox]
  Option B: [Text input] [Correct checkbox]
  [Add Option Button]
Explanation: [Rich text editor - optional]
Points: [Number input with validation]
```

#### Essay Assignment Setup
```
Prompt: [Rich text editor with character limit]
Word Count: [Range selector: Min/Max]
Rubric: [Rubric builder component]
  Criteria 1: [Text] Points: [Number]
  Criteria 2: [Text] Points: [Number]
  [Add Criteria Button]
Submission Format: [Radio: Text only/File upload/Both]
```

### Grading Forms

#### Quick Grade Entry
```
Student: [Auto-complete dropdown]
Assignment: [Dropdown with recent assignments]
Grade: [Number input with scale validation]
Feedback: [Text area - optional]
[Save] [Save and Next Student]
```

#### Rubric-Based Grading
```
For each criteria:
  Criteria Name: [Display only]
  Performance Level: [Radio buttons with point values]
  Comments: [Text area for specific feedback]
Overall Comments: [Rich text editor]
Final Grade: [Auto-calculated, manual override option]
```

## Accessibility Requirements

### Keyboard Navigation
- Logical tab order through all form elements
- Enter key submits forms appropriately
- Escape key cancels/closes modal forms
- Arrow keys navigate within grouped controls

### Screen Reader Support
- Proper labeling for all form controls
- Error messages associated with specific fields
- Progress announcements for multi-step forms
- Clear instructions and help text

### Visual Design
- 4.5:1 minimum contrast ratio for all text
- Clear visual hierarchy with proper heading structure
- Error states that don't rely solely on color
- Sufficient spacing between interactive elements

## Form Layout Patterns

### Single Column (Recommended)
- Easier scanning and completion
- Better for mobile devices
- Clearer visual hierarchy
- Reduced cognitive load

### Two Column (Limited Use)
- Only for clearly related fields (First Name | Last Name)
- Maintain single column on mobile
- Ensure proper tab order

### Multi-Step Forms
```
Step Indicator:
[1. Basic Info] → [2. Content] → [3. Settings] → [4. Review]

Navigation:
[Back] [Save Draft] [Continue]

Progress:
Progress bar showing completion percentage
```

## Error Prevention Strategies

### Input Constraints
- Date fields only accept valid dates
- Number fields reject non-numeric input
- Email fields provide format guidance
- File uploads check type and size before upload

### Smart Defaults
- Current date for assignment creation
- User's subject area pre-selected
- Grade level based on class context
- Reasonable time limits and point values

### Confirmation Patterns
- Preview step for complex forms
- Confirmation dialogs for destructive actions
- Summary of changes before submission
- Option to save drafts and return later

## Testing Requirements

### Functional Testing
- All validation rules work correctly
- Form submission handles success and error states
- Draft saving and restoration works properly
- File uploads complete successfully

### Accessibility Testing
- Screen reader navigation is logical
- Keyboard-only operation is possible
- Error states are properly announced
- Form instructions are clear and complete

### Usability Testing
- Forms complete successfully by target users
- Error messages help users recover
- Multi-step flows are intuitive
- Mobile experience is optimized

This specification ensures that all forms in the ToolBoxAI platform provide excellent user experience while maintaining educational context and accessibility standards.