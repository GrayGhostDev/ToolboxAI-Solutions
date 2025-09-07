# Lesson System

The lesson system forms the core educational framework within the learning platform, providing structured content delivery and progress tracking.

## Overview

The lesson system allows students to access educational content in a structured, sequential manner. It includes:
- Interactive lesson content
- Progress tracking
- Navigation between lesson sections
- Integration with quiz system for assessment

## Core Components

### LessonPageController

The `LessonPageController` manages user interaction within lessons, including navigation, content display, and transition to assessments.

```lua
-- Main controller initialization
local controller = LessonPageController.new(gui)
```

#### Key Methods

| Method | Description |
|--------|-------------|
| `switchLesson(lessonNumber)` | Navigates to a specific lesson and updates content |
| `loadQuestion(questionNumber)` | For embedded quiz elements, loads a specific question |
| `updateProgressBar()` | Updates visual progress indicators |
| `startQuiz()` | Transitions to the quiz interface for lesson assessment |

### Lesson Content Structure

Lessons are organized into a hierarchical structure:

```
Course
  └── Lesson 1
       ├── Introduction
       ├── Content Section 1
       ├── Content Section 2
       ├── Practice
       └── Assessment
  └── Lesson 2
      ...
```

Each lesson typically contains:
- Title and overview
- Educational content (text, images, interactive elements)
- Progress indicators
- Navigation elements

### Lesson Data Model

```lua
-- Sample lesson data structure
local LESSON_TITLES = {
    "Lesson 1: Introduction",
    "Lesson 2: Basic Concepts",
    "Lesson 3: Advanced Topics",
    "Lesson 4: Practice Exercises",
    "Lesson 5: Final Project"
}

local LESSON_DESCRIPTIONS = {
    "Welcome to the course! In this lesson, you'll learn the fundamental concepts...",
    "Building on the basics, we'll explore key principles and techniques...",
    "Time to dive deeper into advanced topics and real-world applications...",
    "Put your knowledge to the test with hands-on practice exercises...",
    "Apply everything you've learned in this comprehensive final project..."
}
```

## UI Components

### Content Display Area

The main region where lesson content is presented:
- Displays text, images, and interactive elements
- Support for multimedia content
- Adaptive layout for different screen sizes

### Navigation Controls

Controls for moving between lesson sections:
- Previous/Next buttons
- Lesson outline/table of contents
- Quick navigation to specific sections

```lua
function LessonPageController:setupButtonCallbacks()
    local sidePanel = self.gui.MainFrame.SidePanel

    -- Setup lesson button callbacks
    for i = 1, 5 do
        local button = sidePanel:FindFirstChild("LessonButton" .. i)
        if button then
            button.MouseButton1Click:Connect(function()
                self:switchLesson(i)
            end)
        end
    end

    -- Setup quiz button callback
    local quizButton = self.gui.MainFrame.ContentArea.QuizButton
    if quizButton then
        quizButton.MouseButton1Click:Connect(function()
            self:startQuiz()
        end)
    end
end
```

### Progress Tracking

Visual indicators showing student progress:
- Overall course completion percentage
- Current position within a lesson
- Completed vs. remaining sections

```lua
function LessonPageController:updateProgressBar()
    local progressFill = self.gui.MainFrame.ProgressBarContainer.ProgressBar.ProgressFill
    local progressText = self.gui.MainFrame.ProgressBarContainer.ProgressBar.ProgressText
    local progress = self.currentLesson / self.totalLessons

    local progressTween = TweenService:Create(
        progressFill,
        TWEEN_INFO,
        {Size = UDim2.new(progress, 0, 1, 0)}
    )
    progressTween:Play()

    progressText.Text = string.format("Progress: %d%%", math.floor(progress * 100))
end
```

## Integration Points

### Quiz System Integration

When a student completes a lesson and begins assessment:

```lua
function LessonPageController:startQuiz()
    -- Store current lesson state
    self:saveProgress()

    -- Initialize quiz for current lesson
    local quizController = QuizController.new(self.gui)
    quizController:loadQuizForLesson(self.currentLesson)

    -- Update UI state
    self.gui.MainFrame.ContentArea.Visible = false
    self.gui.MainFrame.QuizArea.Visible = true
end
```

### Gamification Integration

Lessons integrate with the gamification system:

```lua
function LessonPageController:completeLesson()
    -- Calculate XP based on lesson difficulty and completion time
    local earnedXP = self:calculateXP()

    -- Update gamification components
    self.gamificationController:rewardXP(earnedXP)
    self.gamificationController:updateChallengeProgress("lessons", 1)
    self.gamificationController:checkAchievements("lesson", self.currentLesson)

    -- Show completion feedback
    self:showCompletionDialog(earnedXP)
end
```

## Accessibility Features

The lesson system incorporates several accessibility enhancements:

- Text size adjustment
- High contrast mode option
- Keyboard navigation support
- Voice assistance compatibility

```lua
function LessonPageController:setupAccessibility()
    -- Text size adjustments
    self.accessibilitySettings = self.accessibilityController:getSettings()
    self:applyTextSizeAdjustments(self.accessibilitySettings.textSize)

    -- Setup keyboard navigation if enabled
    if self.accessibilitySettings.keyboardNavigation then
        self:setupKeyboardControls()
    end
end
```

## Implementation Guidelines

### Adding New Lessons

To add a new lesson to the system:

1. Create lesson content in the appropriate format
2. Add lesson metadata to the lessons data table
3. Create necessary media assets
4. Update course progression metrics

### Content Design Best Practices

- Break content into digestible sections
- Include interactive elements every 2-3 screens
- Provide clear learning objectives at the start
- Include summary points at the end
- Ensure each lesson builds upon previous knowledge

### Performance Considerations

- Lazy-load lesson content to reduce initial loading time
- Pre-load the next lesson to reduce transition delay
- Cache completed lesson results to avoid redundant calculations

## Future Enhancements

- Support for branching content paths based on student performance
- Adaptive difficulty adjustments
- Enhanced multimedia support including video and interactive simulations
- Collaborative learning features
- Offline mode with content synchronization
