--!strict
--[[
    Generation Wizard Component
    Multi-step wizard interface for content generation with real-time preview
]]

local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local HttpService = game:GetService("HttpService")
local Selection = game:GetService("Selection")

-- Types
type WizardStep = {
    id: string,
    title: string,
    description: string,
    fields: {Field},
    validator: (any) -> (boolean, string?),
    next: string?,
    previous: string?
}

type Field = {
    name: string,
    type: "text" | "number" | "dropdown" | "checkbox" | "slider" | "color" | "multiselect",
    label: string,
    placeholder: string?,
    required: boolean,
    options: {any}?,
    default: any?,
    min: number?,
    max: number?,
    step: number?
}

type GenerationRequest = {
    contentType: string,
    educationalLevel: string,
    subject: string,
    topic: string,
    learningObjectives: {string},
    difficulty: number,
    engagementStyle: string,
    modalityPreferences: {string},
    accessibility: {string},
    customParameters: {[string]: any}
}

-- Generation Wizard Class
local GenerationWizard = {}
GenerationWizard.__index = GenerationWizard

function GenerationWizard.new(parent: Frame, stateManager: any, eventEmitter: any)
    local self = setmetatable({}, GenerationWizard)

    self.parent = parent
    self.stateManager = stateManager
    self.eventEmitter = eventEmitter
    self.currentStep = "content_type"
    self.formData = {}
    self.validation = {}
    self.ui = {}

    -- Define wizard steps
    self.steps = self:defineSteps()

    -- Create UI
    self:createUI()

    -- Setup event handlers
    self:setupEventHandlers()

    return self
end

function GenerationWizard:defineSteps(): {[string]: WizardStep}
    return {
        content_type = {
            id = "content_type",
            title = "Content Type",
            description = "Select the type of educational content to generate",
            fields = {
                {
                    name = "contentType",
                    type = "dropdown",
                    label = "Content Type",
                    required = true,
                    options = {
                        "Interactive Lesson",
                        "Educational Game",
                        "Assessment Quiz",
                        "Simulation",
                        "Tutorial",
                        "Puzzle",
                        "Story-based Learning",
                        "Coding Challenge"
                    },
                    default = "Interactive Lesson"
                },
                {
                    name = "modalityPreferences",
                    type = "multiselect",
                    label = "Content Modalities",
                    required = true,
                    options = {
                        "Text",
                        "Visual",
                        "Audio",
                        "Interactive",
                        "3D Models",
                        "Animations"
                    },
                    default = {"Text", "Visual", "Interactive"}
                }
            },
            validator = function(data)
                if not data.contentType then
                    return false, "Please select a content type"
                end
                if not data.modalityPreferences or #data.modalityPreferences == 0 then
                    return false, "Please select at least one modality"
                end
                return true
            end,
            next = "educational_details"
        },

        educational_details = {
            id = "educational_details",
            title = "Educational Details",
            description = "Specify the educational context and objectives",
            fields = {
                {
                    name = "educationalLevel",
                    type = "dropdown",
                    label = "Education Level",
                    required = true,
                    options = {
                        "Elementary (K-5)",
                        "Middle School (6-8)",
                        "High School (9-12)",
                        "College",
                        "Professional",
                        "All Ages"
                    },
                    default = "Middle School (6-8)"
                },
                {
                    name = "subject",
                    type = "dropdown",
                    label = "Subject",
                    required = true,
                    options = {
                        "Mathematics",
                        "Science",
                        "Computer Science",
                        "Language Arts",
                        "History",
                        "Social Studies",
                        "Art & Design",
                        "Music",
                        "Physical Education",
                        "Life Skills"
                    },
                    default = "Computer Science"
                },
                {
                    name = "topic",
                    type = "text",
                    label = "Specific Topic",
                    placeholder = "e.g., Introduction to Variables",
                    required = true
                },
                {
                    name = "learningObjectives",
                    type = "text",
                    label = "Learning Objectives (one per line)",
                    placeholder = "Students will be able to...",
                    required = true
                }
            },
            validator = function(data)
                if not data.educationalLevel then
                    return false, "Please select an education level"
                end
                if not data.subject then
                    return false, "Please select a subject"
                end
                if not data.topic or data.topic == "" then
                    return false, "Please enter a topic"
                end
                if not data.learningObjectives or data.learningObjectives == "" then
                    return false, "Please enter at least one learning objective"
                end
                return true
            end,
            previous = "content_type",
            next = "difficulty_engagement"
        },

        difficulty_engagement = {
            id = "difficulty_engagement",
            title = "Difficulty & Engagement",
            description = "Configure difficulty and engagement settings",
            fields = {
                {
                    name = "difficulty",
                    type = "slider",
                    label = "Difficulty Level",
                    min = 1,
                    max = 10,
                    step = 1,
                    default = 5,
                    required = true
                },
                {
                    name = "engagementStyle",
                    type = "dropdown",
                    label = "Engagement Style",
                    required = true,
                    options = {
                        "Gamified",
                        "Story-driven",
                        "Challenge-based",
                        "Exploratory",
                        "Collaborative",
                        "Competitive",
                        "Creative",
                        "Problem-solving"
                    },
                    default = "Gamified"
                },
                {
                    name = "pacing",
                    type = "dropdown",
                    label = "Content Pacing",
                    required = true,
                    options = {
                        "Self-paced",
                        "Timed",
                        "Adaptive",
                        "Structured"
                    },
                    default = "Self-paced"
                },
                {
                    name = "feedbackStyle",
                    type = "dropdown",
                    label = "Feedback Style",
                    required = true,
                    options = {
                        "Immediate",
                        "Delayed",
                        "Hints-based",
                        "Solution-reveal"
                    },
                    default = "Immediate"
                }
            },
            validator = function(data)
                if not data.difficulty then
                    return false, "Please set a difficulty level"
                end
                if not data.engagementStyle then
                    return false, "Please select an engagement style"
                end
                return true
            end,
            previous = "educational_details",
            next = "accessibility"
        },

        accessibility = {
            id = "accessibility",
            title = "Accessibility",
            description = "Configure accessibility and inclusion options",
            fields = {
                {
                    name = "accessibility",
                    type = "multiselect",
                    label = "Accessibility Features",
                    required = false,
                    options = {
                        "High Contrast",
                        "Large Text",
                        "Screen Reader Support",
                        "Keyboard Navigation",
                        "Color Blind Mode",
                        "Subtitles/Captions",
                        "Simple Language",
                        "Visual Indicators"
                    },
                    default = {"Keyboard Navigation", "Visual Indicators"}
                },
                {
                    name = "languageSupport",
                    type = "multiselect",
                    label = "Language Support",
                    required = false,
                    options = {
                        "English",
                        "Spanish",
                        "French",
                        "German",
                        "Chinese",
                        "Japanese",
                        "Portuguese",
                        "Arabic"
                    },
                    default = {"English"}
                },
                {
                    name = "contentWarnings",
                    type = "text",
                    label = "Content Warnings (if any)",
                    placeholder = "e.g., Flashing lights, loud sounds",
                    required = false
                }
            },
            validator = function(data)
                return true -- Accessibility is optional
            end,
            previous = "difficulty_engagement",
            next = "review"
        },

        review = {
            id = "review",
            title = "Review & Generate",
            description = "Review your settings and generate content",
            fields = {}, -- No fields, just display summary
            validator = function(data)
                return true
            end,
            previous = "accessibility"
        }
    }
end

function GenerationWizard:createUI()
    -- Main container
    local container = Instance.new("Frame")
    container.Size = UDim2.new(1, -20, 1, -20)
    container.Position = UDim2.new(0, 10, 0, 10)
    container.BackgroundColor3 = Color3.fromRGB(40, 40, 40)
    container.BorderSizePixel = 0
    container.Parent = self.parent
    self.ui.container = container

    -- Header
    local header = Instance.new("Frame")
    header.Size = UDim2.new(1, 0, 0, 60)
    header.BackgroundColor3 = Color3.fromRGB(50, 50, 50)
    header.BorderSizePixel = 0
    header.Parent = container

    local headerTitle = Instance.new("TextLabel")
    headerTitle.Size = UDim2.new(1, -20, 0, 30)
    headerTitle.Position = UDim2.new(0, 10, 0, 5)
    headerTitle.BackgroundTransparency = 1
    headerTitle.Text = "AI Content Generation Wizard"
    headerTitle.TextColor3 = Color3.fromRGB(255, 255, 255)
    headerTitle.TextScaled = true
    headerTitle.Font = Enum.Font.SourceSansBold
    headerTitle.Parent = header
    self.ui.headerTitle = headerTitle

    local headerDescription = Instance.new("TextLabel")
    headerDescription.Size = UDim2.new(1, -20, 0, 20)
    headerDescription.Position = UDim2.new(0, 10, 0, 35)
    headerDescription.BackgroundTransparency = 1
    headerDescription.Text = "Step 1 of 5"
    headerDescription.TextColor3 = Color3.fromRGB(200, 200, 200)
    headerDescription.TextScaled = true
    headerDescription.Font = Enum.Font.SourceSans
    headerDescription.Parent = header
    self.ui.headerDescription = headerDescription

    -- Progress bar
    local progressBar = Instance.new("Frame")
    progressBar.Size = UDim2.new(1, 0, 0, 4)
    progressBar.Position = UDim2.new(0, 0, 0, 60)
    progressBar.BackgroundColor3 = Color3.fromRGB(30, 30, 30)
    progressBar.BorderSizePixel = 0
    progressBar.Parent = container

    local progressFill = Instance.new("Frame")
    progressFill.Size = UDim2.new(0.2, 0, 1, 0)
    progressFill.BackgroundColor3 = Color3.fromRGB(0, 162, 255)
    progressFill.BorderSizePixel = 0
    progressFill.Parent = progressBar
    self.ui.progressFill = progressFill

    -- Content area with scrolling
    local contentScroll = Instance.new("ScrollingFrame")
    contentScroll.Size = UDim2.new(1, -20, 1, -140)
    contentScroll.Position = UDim2.new(0, 10, 0, 70)
    contentScroll.BackgroundTransparency = 1
    contentScroll.ScrollBarThickness = 6
    contentScroll.ScrollBarImageColor3 = Color3.fromRGB(100, 100, 100)
    contentScroll.Parent = container
    self.ui.contentScroll = contentScroll

    -- Footer with navigation buttons
    local footer = Instance.new("Frame")
    footer.Size = UDim2.new(1, 0, 0, 60)
    footer.Position = UDim2.new(0, 0, 1, -60)
    footer.BackgroundColor3 = Color3.fromRGB(50, 50, 50)
    footer.BorderSizePixel = 0
    footer.Parent = container

    -- Previous button
    local prevButton = Instance.new("TextButton")
    prevButton.Size = UDim2.new(0, 100, 0, 40)
    prevButton.Position = UDim2.new(0, 10, 0, 10)
    prevButton.BackgroundColor3 = Color3.fromRGB(60, 60, 60)
    prevButton.Text = "Previous"
    prevButton.TextColor3 = Color3.fromRGB(255, 255, 255)
    prevButton.Font = Enum.Font.SourceSans
    prevButton.TextScaled = true
    prevButton.Parent = footer
    prevButton.Visible = false
    self.ui.prevButton = prevButton

    -- Next button
    local nextButton = Instance.new("TextButton")
    nextButton.Size = UDim2.new(0, 100, 0, 40)
    nextButton.Position = UDim2.new(1, -110, 0, 10)
    nextButton.BackgroundColor3 = Color3.fromRGB(0, 162, 255)
    nextButton.Text = "Next"
    nextButton.TextColor3 = Color3.fromRGB(255, 255, 255)
    nextButton.Font = Enum.Font.SourceSans
    nextButton.TextScaled = true
    nextButton.Parent = footer
    self.ui.nextButton = nextButton

    -- Cancel button
    local cancelButton = Instance.new("TextButton")
    cancelButton.Size = UDim2.new(0, 100, 0, 40)
    cancelButton.Position = UDim2.new(0.5, -50, 0, 10)
    cancelButton.BackgroundColor3 = Color3.fromRGB(60, 60, 60)
    cancelButton.Text = "Cancel"
    cancelButton.TextColor3 = Color3.fromRGB(255, 255, 255)
    cancelButton.Font = Enum.Font.SourceSans
    cancelButton.TextScaled = true
    cancelButton.Parent = footer
    self.ui.cancelButton = cancelButton

    -- Load first step
    self:loadStep(self.currentStep)
end

function GenerationWizard:loadStep(stepId: string)
    local step = self.steps[stepId]
    if not step then return end

    -- Clear content area
    for _, child in ipairs(self.ui.contentScroll:GetChildren()) do
        if child:IsA("GuiObject") then
            child:Destroy()
        end
    end

    -- Update header
    self.ui.headerDescription.Text = step.title .. " - " .. step.description

    -- Update progress
    local stepIndex = self:getStepIndex(stepId)
    local totalSteps = self:getTotalSteps()
    local progress = stepIndex / totalSteps

    local tween = TweenService:Create(
        self.ui.progressFill,
        TweenInfo.new(0.3, Enum.EasingStyle.Quad),
        {Size = UDim2.new(progress, 0, 1, 0)}
    )
    tween:Play()

    -- Create form fields or review
    if stepId == "review" then
        self:createReviewUI()
    else
        self:createFormFields(step.fields)
    end

    -- Update navigation buttons
    self.ui.prevButton.Visible = step.previous ~= nil
    if step.next then
        self.ui.nextButton.Text = "Next"
    elseif stepId == "review" then
        self.ui.nextButton.Text = "Generate"
    else
        self.ui.nextButton.Text = "Finish"
    end

    self.currentStep = stepId
end

function GenerationWizard:createFormFields(fields: {Field})
    local yOffset = 10

    for _, field in ipairs(fields) do
        local fieldFrame = Instance.new("Frame")
        fieldFrame.Size = UDim2.new(1, -20, 0, 80)
        fieldFrame.Position = UDim2.new(0, 10, 0, yOffset)
        fieldFrame.BackgroundTransparency = 1
        fieldFrame.Parent = self.ui.contentScroll

        -- Label
        local label = Instance.new("TextLabel")
        label.Size = UDim2.new(1, 0, 0, 20)
        label.BackgroundTransparency = 1
        label.Text = field.label .. (field.required and " *" or "")
        label.TextColor3 = Color3.fromRGB(255, 255, 255)
        label.TextXAlignment = Enum.TextXAlignment.Left
        label.Font = Enum.Font.SourceSans
        label.TextScaled = true
        label.Parent = fieldFrame

        -- Create input based on type
        if field.type == "text" then
            local textBox = Instance.new("TextBox")
            textBox.Size = UDim2.new(1, 0, 0, 40)
            textBox.Position = UDim2.new(0, 0, 0, 25)
            textBox.BackgroundColor3 = Color3.fromRGB(30, 30, 30)
            textBox.BorderSizePixel = 1
            textBox.BorderColor3 = Color3.fromRGB(60, 60, 60)
            textBox.Text = self.formData[field.name] or field.default or ""
            textBox.PlaceholderText = field.placeholder or ""
            textBox.TextColor3 = Color3.fromRGB(255, 255, 255)
            textBox.Font = Enum.Font.SourceSans
            textBox.TextScaled = true
            textBox.Parent = fieldFrame

            textBox:GetPropertyChangedSignal("Text"):Connect(function()
                self.formData[field.name] = textBox.Text
            end)

        elseif field.type == "dropdown" then
            local dropdown = Instance.new("TextButton")
            dropdown.Size = UDim2.new(1, 0, 0, 40)
            dropdown.Position = UDim2.new(0, 0, 0, 25)
            dropdown.BackgroundColor3 = Color3.fromRGB(30, 30, 30)
            dropdown.BorderSizePixel = 1
            dropdown.BorderColor3 = Color3.fromRGB(60, 60, 60)
            dropdown.Text = self.formData[field.name] or field.default or "Select..."
            dropdown.TextColor3 = Color3.fromRGB(255, 255, 255)
            dropdown.Font = Enum.Font.SourceSans
            dropdown.TextScaled = true
            dropdown.Parent = fieldFrame

            dropdown.MouseButton1Click:Connect(function()
                self:showDropdownOptions(dropdown, field)
            end)

        elseif field.type == "slider" then
            local sliderFrame = Instance.new("Frame")
            sliderFrame.Size = UDim2.new(1, 0, 0, 40)
            sliderFrame.Position = UDim2.new(0, 0, 0, 25)
            sliderFrame.BackgroundColor3 = Color3.fromRGB(30, 30, 30)
            sliderFrame.BorderSizePixel = 1
            sliderFrame.BorderColor3 = Color3.fromRGB(60, 60, 60)
            sliderFrame.Parent = fieldFrame

            local sliderBar = Instance.new("Frame")
            sliderBar.Size = UDim2.new(1, -20, 0, 4)
            sliderBar.Position = UDim2.new(0, 10, 0.5, -2)
            sliderBar.BackgroundColor3 = Color3.fromRGB(60, 60, 60)
            sliderBar.Parent = sliderFrame

            local sliderHandle = Instance.new("Frame")
            sliderHandle.Size = UDim2.new(0, 20, 0, 20)
            sliderHandle.Position = UDim2.new(0.5, -10, 0.5, -10)
            sliderHandle.BackgroundColor3 = Color3.fromRGB(0, 162, 255)
            sliderHandle.Parent = sliderFrame

            local valueLabel = Instance.new("TextLabel")
            valueLabel.Size = UDim2.new(0, 40, 1, 0)
            valueLabel.Position = UDim2.new(1, -45, 0, 0)
            valueLabel.BackgroundTransparency = 1
            valueLabel.Text = tostring(field.default or field.min or 0)
            valueLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
            valueLabel.Font = Enum.Font.SourceSans
            valueLabel.TextScaled = true
            valueLabel.Parent = sliderFrame

            -- Initialize value
            local currentValue = self.formData[field.name] or field.default or field.min or 0
            self.formData[field.name] = currentValue
            valueLabel.Text = tostring(currentValue)

            -- Position handle based on value
            local range = (field.max or 10) - (field.min or 0)
            local normalizedValue = (currentValue - (field.min or 0)) / range
            sliderHandle.Position = UDim2.new(normalizedValue, -10, 0.5, -10)

        elseif field.type == "multiselect" then
            local container = Instance.new("Frame")
            container.Size = UDim2.new(1, 0, 0, math.ceil(#field.options / 2) * 25)
            container.Position = UDim2.new(0, 0, 0, 25)
            container.BackgroundTransparency = 1
            container.Parent = fieldFrame

            fieldFrame.Size = UDim2.new(1, -20, 0, 50 + container.Size.Y.Offset)

            self.formData[field.name] = self.formData[field.name] or field.default or {}

            for i, option in ipairs(field.options or {}) do
                local checkbox = Instance.new("TextButton")
                checkbox.Size = UDim2.new(0.5, -5, 0, 20)
                checkbox.Position = UDim2.new(
                    (i - 1) % 2 * 0.5,
                    ((i - 1) % 2) * 5,
                    0,
                    math.floor((i - 1) / 2) * 25
                )
                checkbox.BackgroundColor3 = Color3.fromRGB(30, 30, 30)
                checkbox.BorderSizePixel = 1
                checkbox.BorderColor3 = Color3.fromRGB(60, 60, 60)
                checkbox.Text = "☐ " .. option
                checkbox.TextColor3 = Color3.fromRGB(255, 255, 255)
                checkbox.TextXAlignment = Enum.TextXAlignment.Left
                checkbox.Font = Enum.Font.SourceSans
                checkbox.TextScaled = true
                checkbox.Parent = container

                -- Check if selected
                local isSelected = false
                for _, selected in ipairs(self.formData[field.name]) do
                    if selected == option then
                        isSelected = true
                        checkbox.Text = "☑ " .. option
                        checkbox.BackgroundColor3 = Color3.fromRGB(0, 162, 255)
                        break
                    end
                end

                checkbox.MouseButton1Click:Connect(function()
                    self:toggleMultiselect(checkbox, field, option)
                end)
            end
        end

        yOffset = yOffset + fieldFrame.Size.Y.Offset + 10
    end

    -- Update scrolling frame canvas size
    self.ui.contentScroll.CanvasSize = UDim2.new(0, 0, 0, yOffset)
end

function GenerationWizard:createReviewUI()
    local yOffset = 10

    -- Title
    local reviewTitle = Instance.new("TextLabel")
    reviewTitle.Size = UDim2.new(1, -20, 0, 30)
    reviewTitle.Position = UDim2.new(0, 10, 0, yOffset)
    reviewTitle.BackgroundTransparency = 1
    reviewTitle.Text = "Review Your Configuration"
    reviewTitle.TextColor3 = Color3.fromRGB(255, 255, 255)
    reviewTitle.Font = Enum.Font.SourceSansBold
    reviewTitle.TextScaled = true
    reviewTitle.Parent = self.ui.contentScroll
    yOffset = yOffset + 40

    -- Display all form data
    for stepId, step in pairs(self.steps) do
        if stepId ~= "review" then
            local sectionFrame = Instance.new("Frame")
            sectionFrame.Size = UDim2.new(1, -20, 0, 100)
            sectionFrame.Position = UDim2.new(0, 10, 0, yOffset)
            sectionFrame.BackgroundColor3 = Color3.fromRGB(30, 30, 30)
            sectionFrame.BorderSizePixel = 0
            sectionFrame.Parent = self.ui.contentScroll

            local sectionTitle = Instance.new("TextLabel")
            sectionTitle.Size = UDim2.new(1, -10, 0, 25)
            sectionTitle.Position = UDim2.new(0, 5, 0, 5)
            sectionTitle.BackgroundTransparency = 1
            sectionTitle.Text = step.title
            sectionTitle.TextColor3 = Color3.fromRGB(0, 162, 255)
            sectionTitle.Font = Enum.Font.SourceSansBold
            sectionTitle.TextScaled = true
            sectionTitle.TextXAlignment = Enum.TextXAlignment.Left
            sectionTitle.Parent = sectionFrame

            local contentY = 30
            for _, field in ipairs(step.fields) do
                local value = self.formData[field.name]
                if value then
                    local valueLabel = Instance.new("TextLabel")
                    valueLabel.Size = UDim2.new(1, -10, 0, 20)
                    valueLabel.Position = UDim2.new(0, 5, 0, contentY)
                    valueLabel.BackgroundTransparency = 1

                    if type(value) == "table" then
                        valueLabel.Text = field.label .. ": " .. table.concat(value, ", ")
                    else
                        valueLabel.Text = field.label .. ": " .. tostring(value)
                    end

                    valueLabel.TextColor3 = Color3.fromRGB(200, 200, 200)
                    valueLabel.Font = Enum.Font.SourceSans
                    valueLabel.TextScaled = true
                    valueLabel.TextXAlignment = Enum.TextXAlignment.Left
                    valueLabel.Parent = sectionFrame
                    contentY = contentY + 20
                end
            end

            sectionFrame.Size = UDim2.new(1, -20, 0, contentY + 10)
            yOffset = yOffset + sectionFrame.Size.Y.Offset + 10
        end
    end

    self.ui.contentScroll.CanvasSize = UDim2.new(0, 0, 0, yOffset)
end

function GenerationWizard:showDropdownOptions(button: TextButton, field: Field)
    -- Implementation for dropdown menu
    -- This would create a dropdown list with options
end

function GenerationWizard:toggleMultiselect(checkbox: TextButton, field: Field, option: string)
    local selected = self.formData[field.name] or {}
    local found = false
    local newSelected = {}

    for _, item in ipairs(selected) do
        if item == option then
            found = true
        else
            table.insert(newSelected, item)
        end
    end

    if not found then
        table.insert(newSelected, option)
        checkbox.Text = "☑ " .. option
        checkbox.BackgroundColor3 = Color3.fromRGB(0, 162, 255)
    else
        checkbox.Text = "☐ " .. option
        checkbox.BackgroundColor3 = Color3.fromRGB(30, 30, 30)
    end

    self.formData[field.name] = newSelected
end

function GenerationWizard:setupEventHandlers()
    -- Next button
    self.ui.nextButton.MouseButton1Click:Connect(function()
        self:handleNext()
    end)

    -- Previous button
    self.ui.prevButton.MouseButton1Click:Connect(function()
        self:handlePrevious()
    end)

    -- Cancel button
    self.ui.cancelButton.MouseButton1Click:Connect(function()
        self:handleCancel()
    end)
end

function GenerationWizard:handleNext()
    local currentStep = self.steps[self.currentStep]

    -- Validate current step
    local isValid, errorMsg = currentStep.validator(self.formData)
    if not isValid then
        self:showError(errorMsg or "Please complete all required fields")
        return
    end

    if self.currentStep == "review" then
        -- Generate content
        self:generateContent()
    elseif currentStep.next then
        -- Go to next step
        self:loadStep(currentStep.next)
    end
end

function GenerationWizard:handlePrevious()
    local currentStep = self.steps[self.currentStep]
    if currentStep.previous then
        self:loadStep(currentStep.previous)
    end
end

function GenerationWizard:handleCancel()
    self.formData = {}
    self:loadStep("content_type")
    self.eventEmitter:emit("wizardCancelled")
end

function GenerationWizard:generateContent()
    -- Prepare request
    local request: GenerationRequest = {
        contentType = self.formData.contentType,
        educationalLevel = self.formData.educationalLevel,
        subject = self.formData.subject,
        topic = self.formData.topic,
        learningObjectives = string.split(self.formData.learningObjectives or "", "\n"),
        difficulty = self.formData.difficulty,
        engagementStyle = self.formData.engagementStyle,
        modalityPreferences = self.formData.modalityPreferences,
        accessibility = self.formData.accessibility or {},
        customParameters = {
            pacing = self.formData.pacing,
            feedbackStyle = self.formData.feedbackStyle,
            languageSupport = self.formData.languageSupport,
            contentWarnings = self.formData.contentWarnings
        }
    }

    -- Update UI to show generating
    self.ui.nextButton.Text = "Generating..."
    self.ui.nextButton.BackgroundColor3 = Color3.fromRGB(100, 100, 100)
    self.ui.prevButton.Visible = false
    self.ui.cancelButton.Visible = false

    -- Emit generation request
    self.eventEmitter:emit("contentGenerationRequested", request)

    -- Reset form after delay
    task.wait(2)
    self:reset()
end

function GenerationWizard:showError(message: string)
    -- Create error notification
    local errorFrame = Instance.new("Frame")
    errorFrame.Size = UDim2.new(0, 300, 0, 60)
    errorFrame.Position = UDim2.new(0.5, -150, 0, -70)
    errorFrame.BackgroundColor3 = Color3.fromRGB(255, 50, 50)
    errorFrame.BorderSizePixel = 0
    errorFrame.Parent = self.ui.container

    local errorText = Instance.new("TextLabel")
    errorText.Size = UDim2.new(1, -20, 1, 0)
    errorText.Position = UDim2.new(0, 10, 0, 0)
    errorText.BackgroundTransparency = 1
    errorText.Text = message
    errorText.TextColor3 = Color3.fromRGB(255, 255, 255)
    errorText.Font = Enum.Font.SourceSans
    errorText.TextScaled = true
    errorText.Parent = errorFrame

    -- Animate in
    errorFrame:TweenPosition(
        UDim2.new(0.5, -150, 0, 10),
        Enum.EasingDirection.Out,
        Enum.EasingStyle.Back,
        0.3,
        true
    )

    -- Remove after delay
    task.wait(3)
    errorFrame:Destroy()
end

function GenerationWizard:reset()
    self.formData = {}
    self:loadStep("content_type")

    self.ui.nextButton.Text = "Next"
    self.ui.nextButton.BackgroundColor3 = Color3.fromRGB(0, 162, 255)
    self.ui.cancelButton.Visible = true
end

function GenerationWizard:getStepIndex(stepId: string): number
    local index = 1
    local current = "content_type"

    while current do
        if current == stepId then
            return index
        end
        local step = self.steps[current]
        current = step and step.next
        index = index + 1
    end

    return 1
end

function GenerationWizard:getTotalSteps(): number
    local count = 0
    local current = "content_type"

    while current do
        count = count + 1
        local step = self.steps[current]
        current = step and step.next
    end

    return count
end

return GenerationWizard