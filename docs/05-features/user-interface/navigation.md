# Navigation System

The navigation system provides the core user interface framework for moving between different sections of the educational platform.

## Overview

The navigation system offers a consistent and intuitive way for users to access different features of the platform, with responsive design considerations for various screen sizes and device types.

## Core Components

### NavigationMenuController

The `NavigationMenuController` manages the navigation panel, including display states, interactions, and transitions between sections.

```lua
-- Main controller initialization
local controller = NavigationMenuController.new(gui)
```text
#### Key Methods

| Method                       | Description                                             |
| ---------------------------- | ------------------------------------------------------- |
| `toggleMenu()`               | Expands or collapses the navigation panel               |
| `selectSection(sectionName)` | Highlights the selected section and triggers navigation |
| `updateLayout()`             | Adjusts layout based on screen size                     |
| `handleSearch(searchText)`   | Filters navigation items based on search query          |

### MainController

The `MainController` coordinates between navigation and content areas, ensuring proper content loading and state management.

```lua
function MainController:switchSection(sectionName)
    -- Update header title
    local headerTitle = self.gui.MainContainer.ContentFrame.HeaderFrame.Title
    headerTitle.Text = sectionName

    -- Hide current section
    local contentContainer = self.gui.MainContainer.ContentFrame.ContentContainer
    contentContainer[self.currentSection .. "Section"].Visible = false

    -- Show new section
    contentContainer[sectionName .. "Section"].Visible = true

    -- Update navigation highlight
    self:updateNavigationHighlight(sectionName)

    self.currentSection = sectionName
end
```text
## UI Components

### Navigation Panel

The main navigation sidebar that contains:

- Profile section
- Search functionality
- Navigation items for different sections
- Expandable/collapsible design for responsive layouts

```lua
-- Navigation items configuration
local NAV_ITEMS = {
    {name = "Dashboard", icon = "🏠"},
    {name = "Lessons", icon = "📚"},
    {name = "Quizzes", icon = "📝"},
    {name = "Progress", icon = "📊"},
    {name = "Rewards", icon = "🏆"},
    {name = "Messages", icon = "✉️"},
    {name = "Settings", icon = "⚙️"}
}
```text
### Responsive Elements

Components designed to adapt to different screen sizes:

- Collapsible sidebar that shows only icons on smaller screens
- Mobile-friendly toggle button
- Adaptive content layout

```lua
function NavigationMenuController:checkScreenSize()
    local viewportSize = workspace.CurrentCamera.ViewportSize
    local isMobile = viewportSize.X < 768

    if isMobile ~= self.isMobile then
        self.isMobile = isMobile
        self:updateLayout()
    end
end

function NavigationMenuController:updateLayout()
    if self.isMobile then
        if self.isExpanded then
            self:toggleMenu() -- Collapse menu on mobile by default
        end
        self.navFrame.ToggleButton.Visible = true
    else
        self.navFrame.ToggleButton.Visible = false
        if not self.isExpanded then
            self:toggleMenu() -- Expand menu on desktop
        end
    end
end
```text
### Visual Feedback Elements

Components that provide interactive feedback:

- Hover effects
- Selection indicators
- Transition animations

```lua
function NavigationMenuController:showHoverEffect(hoverEffect)
    local hoverTween = TweenService:Create(
        hoverEffect,
        HOVER_TWEEN_INFO,
        {BackgroundTransparency = 0.9}
    )
    hoverTween:Play()
end
```text
## Animation System

The navigation incorporates smooth transitions for a polished user experience:

```lua
-- Animation settings
local TWEEN_INFO = TweenInfo.new(
    0.3,    -- Time
    Enum.EasingStyle.Quad,
    Enum.EasingDirection.Out
)

local HOVER_TWEEN_INFO = TweenInfo.new(
    0.15,   -- Time
    Enum.EasingStyle.Quad,
    Enum.EasingDirection.Out
)

-- Toggle menu expansion with animation
function NavigationMenuController:toggleMenu()
    self.isExpanded = not self.isExpanded

    local targetSize = self.isExpanded and
        UDim2.new(0.25, 0, 1, 0) or
        UDim2.new(0.08, 0, 1, 0)

    local sizeTween = TweenService:Create(
        self.navFrame,
        TWEEN_INFO,
        {Size = targetSize}
    )
    sizeTween:Play()

    -- Update visibility of text labels
    for _, item in ipairs(self.navFrame.NavContainer:GetChildren()) do
        if item:IsA("Frame") and item.Name:match("Item$") then
            local label = item.Label
            label.Visible = self.isExpanded
        end
    end
end
```text
## Search Functionality

The navigation includes a search mechanism to quickly find platform features:

```lua
function NavigationMenuController:handleSearch(searchText)
    searchText = searchText:lower()

    for _, item in ipairs(self.navFrame.NavContainer:GetChildren()) do
        if item:IsA("Frame") and item.Name:match("Item$") then
            local label = item.Label
            local matches = label.Text:lower():find(searchText, 1, true)

            -- Show/hide based on search
            item.Visible = searchText == "" or matches
        end
    end
end
```text
## User Profile Integration

The navigation system includes user profile display:

- User avatar
- Username/display name
- Quick access to profile settings

## Role-Based Navigation

The system supports different navigation options based on user roles:

### Student Navigation

Focused on learning activities:

- Dashboard
- Lessons
- Quizzes
- Progress
- Rewards

### Educator Navigation

Includes teaching and management tools:

- Courses
- Student Progress
- Grading
- Analytics
- Content Creation

## Keyboard Navigation

Support for keyboard-based navigation to improve accessibility:

```lua
function NavigationMenuController:setupKeyboardNavigation()
    UserInputService.InputBegan:Connect(function(input)
        if not self.settings.keyboardNavigation then return end

        if input.KeyCode == Enum.KeyCode.Tab then
            -- Move focus
            local currentIndex = table.find(self.focusableElements, self.currentFocus) or 0
            local nextIndex = (currentIndex % #self.focusableElements) + 1

            self:setFocus(self.focusableElements[nextIndex])
        elseif input.KeyCode == Enum.KeyCode.Return and self.currentFocus then
            -- Activate focused element
            self:activateFocusedElement()
        end
    end)
end
```text
## Implementation Guidelines

### Adding New Navigation Items

To add a new section to the navigation:

1. Add entry to the `NAV_ITEMS` table
2. Create corresponding content section
3. Update the `switchSection` method to handle the new section
4. Add any role-based restrictions if necessary

### Customization Options

The navigation system supports several customization options:

- Dark/light mode toggle
- Color scheme adjustments for accessibility
- Icon and text size adjustments
- Expanded/collapsed state persistence

### Best Practices

- Keep navigation hierarchy shallow (max 2 levels)
- Use consistent iconography for intuitive recognition
- Provide clear visual feedback for the current section
- Ensure all functions are accessible via keyboard
- Maintain responsive design for all screen sizes

## Future Enhancements

- Multi-level navigation for more complex hierarchies
- Customizable navigation order
- Favorites/pinned sections
- Context-sensitive navigation options
- Navigation history and breadcrumbs
- Enhanced transition animations
