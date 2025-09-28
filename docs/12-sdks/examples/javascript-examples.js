/**
 * ToolBoxAI JavaScript SDK Examples
 * Complete examples demonstrating SDK usage patterns
 */

// ============================================
// SETUP AND AUTHENTICATION
// ============================================

import { ToolBoxAI } from '@toolboxai/sdk';

// Basic initialization
const client = new ToolBoxAI({
    apiKey: process.env.TOOLBOXAI_API_KEY,
    environment: 'production'
});

// OAuth2 authentication for user-facing apps
const oauthClient = new ToolBoxAI({
    clientId: process.env.CLIENT_ID,
    clientSecret: process.env.CLIENT_SECRET,
    redirectUri: 'https://yourapp.com/callback',
    authMethod: 'oauth2'
});

// ============================================
// LESSON MANAGEMENT EXAMPLES
// ============================================

async function lessonManagementExamples() {
    // List all available lessons with filtering
    const mathLessons = await client.lessons.list({
        subject: 'math',
        grade: 5,
        difficulty: 'medium',
        limit: 20,
        offset: 0
    });

    console.log(`Found ${mathLessons.total} math lessons`);
    mathLessons.items.forEach(lesson => {
        console.log(`- ${lesson.title} (${lesson.duration} mins)`);
    });

    // Get detailed lesson information
    const lesson = await client.lessons.get('lesson-123');
    console.log('Lesson details:', {
        title: lesson.title,
        objectives: lesson.objectives,
        materials: lesson.materials,
        assessments: lesson.assessments.length
    });

    // Create a new lesson
    const newLesson = await client.lessons.create({
        title: 'Introduction to Fractions',
        subject: 'math',
        grade: 4,
        duration: 45,
        objectives: [
            'Understand what fractions represent',
            'Identify numerator and denominator',
            'Compare simple fractions'
        ],
        content: {
            introduction: 'Today we will learn about fractions...',
            activities: [
                {
                    type: 'interactive',
                    title: 'Pizza Fractions',
                    description: 'Divide pizzas into equal parts'
                }
            ]
        },
        robloxEnvironment: {
            theme: 'pizza_restaurant',
            interactive: true
        }
    });

    // Update an existing lesson
    const updatedLesson = await client.lessons.update('lesson-123', {
        duration: 60,
        difficulty: 'advanced',
        tags: ['fractions', 'visual-learning', 'interactive']
    });

    // Deploy lesson to Roblox
    const deployment = await client.lessons.deployToRoblox('lesson-123', {
        serverId: 'roblox-server-id',
        instanceType: 'classroom',
        maxPlayers: 30
    });
    console.log('Deployment URL:', deployment.joinUrl);
}

// ============================================
// QUIZ AND ASSESSMENT EXAMPLES
// ============================================

async function quizExamples() {
    // Create a quiz
    const quiz = await client.quizzes.create({
        title: 'Fractions Assessment',
        lessonId: 'lesson-123',
        type: 'formative',
        timeLimit: 600, // 10 minutes
        questions: [
            {
                type: 'multiple_choice',
                question: 'What is 1/2 + 1/4?',
                options: ['3/4', '2/6', '3/6', '1/3'],
                correctAnswer: 0,
                points: 10
            },
            {
                type: 'true_false',
                question: '1/3 is greater than 1/2',
                correctAnswer: false,
                points: 5
            },
            {
                type: 'fill_blank',
                question: 'The top number in a fraction is called the ___',
                correctAnswer: 'numerator',
                points: 5
            }
        ],
        passingScore: 70,
        randomizeQuestions: true
    });

    // Start a quiz attempt
    const attempt = await client.quizzes.startAttempt(quiz.id, {
        userId: 'user-123',
        timestamp: new Date().toISOString()
    });

    // Submit quiz answers
    const submission = await client.quizzes.submitAttempt(attempt.id, {
        answers: [
            { questionId: 'q1', answer: 0 },    // Multiple choice
            { questionId: 'q2', answer: false }, // True/false
            { questionId: 'q3', answer: 'numerator' } // Fill in blank
        ],
        timeSpent: 485 // seconds
    });

    console.log('Quiz Results:', {
        score: submission.score,
        passed: submission.passed,
        correctAnswers: submission.correctAnswers,
        feedback: submission.feedback
    });

    // Get quiz analytics
    const analytics = await client.quizzes.getAnalytics(quiz.id);
    console.log('Quiz Analytics:', {
        attemptCount: analytics.totalAttempts,
        averageScore: analytics.averageScore,
        passRate: analytics.passRate,
        averageTime: analytics.averageTimeSpent
    });
}

// ============================================
// STUDENT PROGRESS TRACKING
// ============================================

async function progressTrackingExamples() {
    const studentId = 'student-123';

    // Track lesson progress
    await client.progress.update(studentId, 'lesson-123', {
        completed: false,
        percentComplete: 65,
        objectivesCompleted: ['obj-1', 'obj-2'],
        timeSpent: 1800, // 30 minutes
        lastAccessedSection: 'activities',
        checkpoint: {
            sectionId: 'section-3',
            timestamp: new Date().toISOString()
        }
    });

    // Get student progress for a specific lesson
    const lessonProgress = await client.progress.getForLesson(
        studentId,
        'lesson-123'
    );

    // Get overall student progress
    const overallProgress = await client.progress.getOverall(studentId);
    console.log('Student Progress:', {
        lessonsCompleted: overallProgress.completedLessons,
        totalTimeSpent: overallProgress.totalTimeSpent,
        averageScore: overallProgress.averageQuizScore,
        currentStreak: overallProgress.streakDays
    });

    // Generate progress report
    const report = await client.progress.generateReport(studentId, {
        startDate: '2024-01-01',
        endDate: '2024-03-31',
        includeQuizzes: true,
        includeActivities: true,
        format: 'pdf'
    });

    // Download the report
    const fs = require('fs');
    fs.writeFileSync('progress-report.pdf', report.data);
}

// ============================================
// GAMIFICATION EXAMPLES
// ============================================

async function gamificationExamples() {
    const userId = 'user-123';

    // Award XP points
    const xpResult = await client.gamification.awardXP(userId, {
        amount: 100,
        reason: 'quiz_completion',
        source: 'quiz-456'
    });

    if (xpResult.levelUp) {
        console.log(`Level up! New level: ${xpResult.newLevel}`);
        // Trigger celebration animation in UI
    }

    // Unlock achievement
    const achievement = await client.gamification.unlockAchievement(
        userId,
        'first_perfect_score'
    );
    console.log(`Achievement unlocked: ${achievement.title}`);

    // Get user's achievements
    const achievements = await client.gamification.getAchievements(userId);
    const unlockedCount = achievements.filter(a => a.unlocked).length;
    console.log(`Unlocked ${unlockedCount}/${achievements.length} achievements`);

    // Update leaderboard
    await client.gamification.updateLeaderboard('weekly_xp', {
        userId: userId,
        score: xpResult.totalXP
    });

    // Get leaderboard
    const leaderboard = await client.gamification.getLeaderboard('weekly_xp', {
        limit: 10,
        timeframe: 'week'
    });

    leaderboard.entries.forEach((entry, index) => {
        console.log(`${index + 1}. ${entry.username}: ${entry.score} XP`);
    });

    // Create a quest
    const quest = await client.gamification.createQuest({
        title: 'Math Master',
        description: 'Complete 5 math lessons this week',
        requirements: [
            { type: 'complete_lessons', subject: 'math', count: 5 }
        ],
        rewards: {
            xp: 500,
            badge: 'math_master',
            items: ['golden_calculator']
        },
        duration: 7 * 24 * 60 * 60 * 1000 // 7 days in ms
    });

    // Assign quest to user
    await client.gamification.assignQuest(userId, quest.id);
}

// ============================================
// REAL-TIME COLLABORATION
// ============================================

async function realtimeExamples() {
    // Connect to real-time updates
    const socket = await client.realtime.connect();

    // Join a classroom session
    const session = await client.realtime.joinSession('classroom-123', {
        userId: 'user-123',
        role: 'student'
    });

    // Listen for real-time events
    socket.on('lesson:started', (data) => {
        console.log('Lesson started:', data.lessonTitle);
        updateUI({ status: 'lesson_active' });
    });

    socket.on('quiz:question', (question) => {
        console.log('New question:', question.text);
        displayQuestion(question);
    });

    socket.on('student:joined', (student) => {
        console.log(`${student.name} joined the session`);
        updateParticipantsList();
    });

    socket.on('achievement:unlocked', (achievement) => {
        if (achievement.userId === currentUserId) {
            showAchievementNotification(achievement);
        }
    });

    // Send real-time updates
    socket.emit('answer:submit', {
        questionId: 'q1',
        answer: 'A',
        timestamp: Date.now()
    });

    // Teacher controls (if role is teacher)
    if (userRole === 'teacher') {
        // Start a quiz for all students
        socket.emit('quiz:start', {
            quizId: 'quiz-123',
            timeLimit: 600
        });

        // Send a message to all students
        socket.emit('message:broadcast', {
            text: 'Great job on the first section!',
            type: 'encouragement'
        });

        // Monitor student progress in real-time
        socket.on('progress:update', (progressData) => {
            updateProgressDashboard(progressData);
        });
    }

    // Disconnect when done
    socket.disconnect();
}

// ============================================
// BATCH OPERATIONS
// ============================================

async function batchOperationsExamples() {
    // Batch create users
    const users = await client.batch.createUsers([
        { name: 'Alice', email: 'alice@school.edu', grade: 5 },
        { name: 'Bob', email: 'bob@school.edu', grade: 5 },
        { name: 'Charlie', email: 'charlie@school.edu', grade: 6 }
    ]);

    // Batch enroll students in a course
    const enrollments = await client.batch.enrollStudents('course-123', 
        users.map(u => u.id)
    );

    // Batch update progress
    const progressUpdates = [
        { userId: 'user-1', lessonId: 'lesson-1', progress: 100 },
        { userId: 'user-2', lessonId: 'lesson-1', progress: 75 },
        { userId: 'user-3', lessonId: 'lesson-1', progress: 50 }
    ];

    await client.batch.updateProgress(progressUpdates);

    // Batch grade assignments
    const grades = await client.batch.gradeAssignments([
        { assignmentId: 'asn-1', userId: 'user-1', score: 95 },
        { assignmentId: 'asn-1', userId: 'user-2', score: 87 },
        { assignmentId: 'asn-1', userId: 'user-3', score: 92 }
    ]);
}

// ============================================
// LMS INTEGRATION EXAMPLES
// ============================================

async function lmsIntegrationExamples() {
    // Canvas integration
    const canvasIntegration = await client.integrations.canvas.setup({
        domain: 'school.instructure.com',
        accessToken: process.env.CANVAS_TOKEN
    });

    // Sync courses from Canvas
    const courses = await client.integrations.canvas.syncCourses();
    console.log(`Synced ${courses.length} courses from Canvas`);

    // Export grades to Canvas
    await client.integrations.canvas.exportGrades('course-123', {
        assignmentId: 'canvas-assignment-id',
        grades: [
            { studentId: 'student-1', score: 95 },
            { studentId: 'student-2', score: 87 }
        ]
    });

    // Google Classroom integration
    const googleClassroom = await client.integrations.googleClassroom.setup({
        clientId: process.env.GOOGLE_CLIENT_ID,
        clientSecret: process.env.GOOGLE_CLIENT_SECRET
    });

    // Create assignment in Google Classroom
    await client.integrations.googleClassroom.createAssignment({
        courseId: 'google-course-id',
        title: 'Fractions Practice',
        description: 'Complete the fractions lesson and quiz',
        lessonId: 'lesson-123',
        dueDate: '2024-12-20T23:59:59Z'
    });

    // Schoology integration
    const schoology = await client.integrations.schoology.setup({
        consumerKey: process.env.SCHOOLOGY_KEY,
        consumerSecret: process.env.SCHOOLOGY_SECRET
    });

    // Import roster from Schoology
    const roster = await client.integrations.schoology.importRoster('section-id');
    console.log(`Imported ${roster.students.length} students`);
}

// ============================================
// ANALYTICS AND REPORTING
// ============================================

async function analyticsExamples() {
    // Get classroom analytics
    const classAnalytics = await client.analytics.getClassroom('class-123', {
        startDate: '2024-01-01',
        endDate: '2024-03-31',
        metrics: ['engagement', 'performance', 'progress']
    });

    console.log('Class Analytics:', {
        averageEngagement: classAnalytics.engagement.average,
        topPerformers: classAnalytics.performance.top5,
        completionRate: classAnalytics.progress.completionRate
    });

    // Get detailed learning analytics
    const learningAnalytics = await client.analytics.getLearningPatterns('user-123');
    console.log('Learning Patterns:', {
        preferredTime: learningAnalytics.preferredStudyTime,
        averageSessionLength: learningAnalytics.avgSessionDuration,
        strongSubjects: learningAnalytics.subjectStrengths,
        improvementAreas: learningAnalytics.areasForImprovement
    });

    // Generate custom report
    const customReport = await client.analytics.generateReport({
        type: 'performance_summary',
        entityType: 'school',
        entityId: 'school-123',
        dateRange: {
            start: '2024-01-01',
            end: '2024-12-31'
        },
        includeCharts: true,
        format: 'html'
    });

    // Track custom events
    await client.analytics.trackEvent('lesson_interaction', {
        userId: 'user-123',
        lessonId: 'lesson-456',
        action: 'clicked_help_button',
        timestamp: new Date().toISOString(),
        metadata: {
            section: 'quiz',
            questionNumber: 3
        }
    });
}

// ============================================
// ERROR HANDLING
// ============================================

async function errorHandlingExamples() {
    try {
        const lesson = await client.lessons.get('invalid-id');
    } catch (error) {
        if (error.code === 'NOT_FOUND') {
            console.error('Lesson not found');
            // Show user-friendly error message
        } else if (error.code === 'UNAUTHORIZED') {
            console.error('Authentication failed');
            // Redirect to login
        } else if (error.code === 'RATE_LIMIT') {
            console.error(`Rate limited. Retry after ${error.retryAfter} seconds`);
            // Implement retry logic
            setTimeout(() => retryRequest(), error.retryAfter * 1000);
        } else {
            console.error('Unexpected error:', error.message);
            // Log to error tracking service
        }
    }

    // Using error handler middleware
    client.setErrorHandler((error) => {
        // Global error handling
        console.error('API Error:', error);
        
        // Send to error tracking service
        errorTracker.log(error);
        
        // Show user notification
        showErrorNotification(error.userMessage || 'An error occurred');
    });
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

// Helper function to display question
function displayQuestion(question) {
    console.log('Displaying question:', question);
    // Update UI with question
}

// Helper function to update UI
function updateUI(state) {
    console.log('Updating UI:', state);
    // Update UI components
}

// Helper function to show notifications
function showAchievementNotification(achievement) {
    console.log('Achievement unlocked:', achievement.title);
    // Display achievement popup
}

// Helper function to update participants list
function updateParticipantsList() {
    console.log('Updating participants list');
    // Refresh participants UI
}

// Helper function to update progress dashboard
function updateProgressDashboard(data) {
    console.log('Updating progress dashboard:', data);
    // Update dashboard UI
}

// Helper function to show error notification
function showErrorNotification(message) {
    console.error('Error:', message);
    // Display error to user
}

// ============================================
// MAIN EXECUTION
// ============================================

async function main() {
    try {
        console.log('Starting ToolBoxAI SDK Examples...\n');
        
        // Run examples
        await lessonManagementExamples();
        await quizExamples();
        await progressTrackingExamples();
        await gamificationExamples();
        await batchOperationsExamples();
        await analyticsExamples();
        
        console.log('\nAll examples completed successfully!');
    } catch (error) {
        console.error('Error running examples:', error);
    }
}

// Run if executed directly
if (require.main === module) {
    main();
}

// Export for use in other modules
module.exports = {
    lessonManagementExamples,
    quizExamples,
    progressTrackingExamples,
    gamificationExamples,
    realtimeExamples,
    batchOperationsExamples,
    lmsIntegrationExamples,
    analyticsExamples,
    errorHandlingExamples
};