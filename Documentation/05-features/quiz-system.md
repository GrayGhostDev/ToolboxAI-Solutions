# Quiz System

The quiz system provides assessment capabilities within the learning platform, allowing students to test their knowledge and receive immediate feedback.

## Overview

The quiz system handles the creation, display, and evaluation of assessments throughout the learning experience. It includes:

- Multiple choice questions
- Timer functionality
- Feedback mechanisms
- Score tracking
- Integration with the broader learning and gamification systems

## Core Components

### QuizController

The `QuizController` manages quiz interaction, question progression, answer validation, and score calculation.

```lua
-- Main controller initialization
local controller = QuizController.new(gui)
```text
#### Key Methods

| Method                         | Description                                         |
| ------------------------------ | --------------------------------------------------- |
| `loadQuestion(questionNumber)` | Displays a specific question and its options        |
| `selectOption(optionNumber)`   | Handles user selection of an answer option          |
| `submitAnswer()`               | Validates the selected answer and provides feedback |
| `nextQuestion()`               | Advances to the next question or ends quiz          |
| `startTimer()`                 | Initializes and manages the countdown timer         |
| `endQuiz()`                    | Finalizes quiz, calculates score, and shows results |

### Quiz Data Model

Quizzes are structured as collections of question objects:

```lua
-- Sample quiz data structure
local QUIZ_DATA = {
    {
        question = "What is the main concept being taught in this lesson?",
        options = {
            "Game Development",
            "User Interface Design",
            "3D Modeling",
            "Animation"
        },
        correctAnswer = 2
    },
    -- Additional questions...
}
```text
## UI Components

### Question Display

The main area showing the current question:

- Question text
- Visual assets if applicable
- Clear typography and spacing for readability

### Answer Options

Container for selectable answer choices:

- Multiple choice options
- Visual feedback for selection
- Support for rich content in answers (images, code snippets)

```lua
function QuizController:selectOption(optionNumber)
    local optionsFrame = self.gui.MainFrame.OptionsFrame

    -- Reset all options
    for i = 1, 4 do
        local button = optionsFrame:FindFirstChild("Option" .. i)
        if button then
            button.BackgroundColor3 = Color3.fromRGB(45, 156, 219)
        end
    end

    -- Highlight selected option
    local selectedButton = optionsFrame:FindFirstChild("Option" .. optionNumber)
    if selectedButton then
        selectedButton.BackgroundColor3 = Color3.fromRGB(255, 170, 0)
        self.selectedOption = optionNumber
    end
end
```text
### Timer Display

Countdown timer showing remaining time:

- Visual and numerical representation
- Warning states when time is running low
- Auto-submission when time expires

```lua
function QuizController:startTimer()
    -- Clear existing timer
    if self.timer then
        self.timer:Disconnect()
    end

    local timerText = self.gui.MainFrame.TimerFrame.TimerText

    self.timer = game:GetService("RunService").Heartbeat:Connect(function()
        if self.timeLeft > 0 then
            self.timeLeft = self.timeLeft - 1
            local minutes = math.floor(self.timeLeft / 60)
            local seconds = self.timeLeft % 60
            timerText.Text = string.format("Time: %d:%02d", minutes, seconds)
        else
            self:endQuiz()
        end
        wait(1)
    end)
end
```text
### Progress Tracker

Visual indicator showing quiz progression:

- Current question number
- Total questions
- Completion percentage

### Feedback Display

Modal or inline component showing answer feedback:

- Correct/incorrect indicator
- Explanation of correct answer
- Points earned
- Continue button

```lua
function QuizController:submitAnswer()
    if not self.selectedOption then return end

    local questionData = QUIZ_DATA[self.currentQuestion]
    local isCorrect = self.selectedOption == questionData.correctAnswer

    -- Show feedback
    local feedbackFrame = self.gui.MainFrame.FeedbackFrame
    local feedbackTitle = feedbackFrame.Title
    local feedbackText = feedbackFrame.Text

    feedbackTitle.Text = isCorrect and "Correct!" or "Incorrect"
    feedbackTitle.BackgroundColor3 = isCorrect and
        Color3.fromRGB(46, 204, 113) or
        Color3.fromRGB(231, 76, 60)

    feedbackText.Text = isCorrect and
        "Great job! You've earned 10 points!" or
        "Don't worry, keep trying!"

    feedbackFrame.Visible = true

    if isCorrect then
        self.score = self.score + 10
    end
end
```text
### Results Summary

End-of-quiz screen showing overall performance:

- Final score
- Correct/incorrect breakdown
- Time taken
- Option to review questions or return to lesson

## Quiz Mechanics

### Scoring System

The default scoring mechanism:

- Base points per correct answer (typically 10 points)
- Optional time bonuses for quick answers
- No penalty for incorrect answers in standard quizzes
- Support for partial credit in some question types

### Time Management

Quiz timing options:

- Overall time limit for the entire quiz
- Optional per-question time limits
- Pause functionality for accessibility needs
- Auto-submission when time expires

```lua
-- End quiz
function QuizController:endQuiz()
    if self.timer then
        self.timer:Disconnect()
    end

    -- Show final score
    local feedbackFrame = self.gui.MainFrame.FeedbackFrame
    feedbackFrame.Title.Text = "Quiz Complete!"
    feedbackFrame.Title.BackgroundColor3 = Color3.fromRGB(46, 204, 113)
    feedbackFrame.Text.Text = string.format("Final Score: %d points", self.score)
    feedbackFrame.Visible = true

    -- Change continue button text
    local continueButton = feedbackFrame.ContinueButton
    continueButton.Text = "Return to Lesson"
end
```text
## Integration Points

### Lesson System Integration

Quizzes are typically launched from the lesson interface:

```lua
-- From LessonPageController
function LessonPageController:startQuiz()
    -- Store lesson state
    self:saveProgress()

    -- Launch quiz
    local quizController = QuizController.new(self.gui)
    quizController:loadQuizForLesson(self.currentLesson)
end
```text
### Gamification Integration

Quiz results feed into the gamification system:

```lua
function QuizController:completeQuiz()
    -- Calculate XP based on score
    local earnedXP = math.floor(self.score * 1.5)

    -- Update gamification elements
    self.gamificationController:rewardXP(earnedXP)
    self.gamificationController:updateChallengeProgress("quizzes", 1)

    -- Check for achievements
    if self.score >= self.maxPossibleScore * 0.9 then
        self.gamificationController:awardAchievement("quiz_master")
    end
end
```text
### Progress Tracking Integration

Quiz results are stored for progress tracking:

```lua
function QuizController:saveResults()
    -- Create results object
    local results = {
        lessonId = self.lessonId,
        quizId = self.quizId,
        score = self.score,
        maxScore = self.maxPossibleScore,
        timeSpent = self.initialTime - self.timeLeft,
        completedAt = os.time(),
        answers = self.userAnswers
    }

    -- Save to progress tracking system
    self.progressController:saveQuizResults(results)
}
```text
## Accessibility Features

The quiz system incorporates several accessibility enhancements:

- Keyboard navigation for all interactions
- Compatible with screen readers
- Text size adjustments
- Extended time options for accommodation needs
- Color contrast considerations for visual impairments

## Implementation Guidelines

### Creating New Quizzes

To add a new quiz to the system:

1. Create quiz data following the `QUIZ_DATA` structure
2. Associate with appropriate lesson content
3. Set difficulty parameters and time limits
4. Add any specific instructions or resources

### Question Design Best Practices

- Keep questions clear and concise
- Ensure only one correct answer per question
- Avoid ambiguous phrasing
- Use consistent formatting across questions
- Include varied difficulty levels throughout the quiz

### Performance Considerations

- Pre-load quiz data to prevent delays between questions
- Optimize image assets if used in questions
- Implement periodic progress saving for longer quizzes

## Future Enhancements

- Additional question types (fill-in-blank, matching, ordering)
- Media-rich questions with images and video
- Adaptive difficulty based on student performance
- Interactive code execution for programming assessments
- Collaborative quizzes for group learning
- Enhanced analytics for question effectiveness
- Spaced repetition for previously missed questions
