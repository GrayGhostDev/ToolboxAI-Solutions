# Roblox-Inspired Design System

A comprehensive theme system for the ToolBoxAI educational platform, featuring official Roblox brand colors, gamification elements, and accessibility-focused design.

## Overview

This design system provides:
- **Roblox Brand Colors**: Official red (#E2231A) and gray (#393B3D)
- **Gamification Elements**: XP bars, achievement badges, level indicators
- **Dark/Light Mode**: Automatic system detection with manual override
- **Accessibility**: WCAG AA compliant colors and focus states
- **Smooth Animations**: Performance-optimized transitions
- **Design Tokens**: Consistent spacing, typography, and styling

## Quick Start

### 1. Wrap Your App

```tsx
import { ThemeWrapper } from './theme';

function App() {
  return (
    <ThemeWrapper>
      <YourApp />
    </ThemeWrapper>
  );
}
```

### 2. Use Theme Context

```tsx
import { useThemeContext } from './theme';

function MyComponent() {
  const { mode, toggleTheme, isDark } = useThemeContext();
  
  return (
    <div>
      <p>Current mode: {mode}</p>
      <button onClick={toggleTheme}>
        Switch to {isDark ? 'light' : 'dark'} mode
      </button>
    </div>
  );
}
```

### 3. Use Styled Components

```tsx
import { RobloxCard, RobloxButton, RobloxChip } from './theme';

function GameCard() {
  return (
    <RobloxCard>
      <h3>Achievement Unlocked!</h3>
      <p>You completed your first lesson!</p>
      <RobloxChip rarity="legendary" label="Master Student" />
      <RobloxButton variant="contained">
        Continue Learning
      </RobloxButton>
    </RobloxCard>
  );
}
```

### 4. Add Theme Switcher

```tsx
import { ThemeSwitcher } from './theme';

function Header() {
  return (
    <header>
      <h1>ToolBoxAI</h1>
      <ThemeSwitcher variant="menu" showLabel />
    </header>
  );
}
```

## Design Tokens

### Colors

```tsx
// Primary Roblox Colors
const robloxRed = '#E2231A';
const robloxGray = '#393B3D';
const robloxWhite = '#FFFFFF';

// Gamification Colors
const colors = {
  xp: '#8B5CF6',        // Purple for XP
  level: '#F59E0B',     // Gold for levels
  badge: '#10B981',     // Emerald for badges
  achievement: '#F97316', // Orange for achievements
  streak: '#EF4444',    // Red for streaks
  coin: '#FCD34D',      // Yellow for coins
  gem: '#A855F7',       // Violet for gems
  star: '#FBBF24'       // Amber for stars
};
```

### Typography

```tsx
// Font Families
fontFamily: {
  sans: ['Inter', 'system-ui', 'sans-serif'],
  display: ['Fredoka One', 'Inter', 'sans-serif'], // Fun headings
  mono: ['JetBrains Mono', 'monospace']
}

// Font Sizes (with line heights)
fontSize: {
  xs: ['0.75rem', { lineHeight: '1rem' }],
  sm: ['0.875rem', { lineHeight: '1.25rem' }],
  base: ['1rem', { lineHeight: '1.5rem' }],
  lg: ['1.125rem', { lineHeight: '1.75rem' }],
  xl: ['1.25rem', { lineHeight: '1.75rem' }],
  '2xl': ['1.5rem', { lineHeight: '2rem' }],
  // ... up to 9xl
}
```

### Spacing

```tsx
// 4px base scale
spacing: {
  1: '0.25rem',    // 4px
  2: '0.5rem',     // 8px
  3: '0.75rem',    // 12px
  4: '1rem',       // 16px
  6: '1.5rem',     // 24px
  8: '2rem',       // 32px
  12: '3rem',      // 48px
  16: '4rem',      // 64px
  // ... up to 96
}
```

### Border Radius

```tsx
borderRadius: {
  sm: '0.125rem',   // 2px
  base: '0.25rem',  // 4px
  md: '0.375rem',   // 6px
  lg: '0.5rem',     // 8px
  xl: '0.75rem',    // 12px
  '2xl': '1rem',    // 16px
  '3xl': '1.5rem',  // 24px
  full: '9999px'
}
```

## Components

### RobloxCard
Enhanced card with Roblox red accent border and smooth animations.

```tsx
<RobloxCard>
  <CardContent>
    Your content here
  </CardContent>
</RobloxCard>
```

### RobloxButton
Gaming-style button with gradient background and hover effects.

```tsx
<RobloxButton variant="contained" size="large">
  Start Learning
</RobloxButton>

<RobloxButton variant="outlined">
  View Progress
</RobloxButton>
```

### RobloxChip
Gamification chip with rarity-based colors.

```tsx
<RobloxChip rarity="common" label="Beginner" />
<RobloxChip rarity="rare" label="Advanced" />
<RobloxChip rarity="epic" label="Expert" />
<RobloxChip rarity="legendary" label="Master" />
```

### XPProgressBar
Animated progress bar with level-based gradients.

```tsx
<XPProgressBar value={75} level={15} />
```

### RobloxAvatar
Gaming avatar with level badge and online indicator.

```tsx
<RobloxAvatar level={25} isOnline>
  <Avatar src="/path/to/avatar.jpg" />
</RobloxAvatar>
```

### AchievementBadge
Badge component for achievements with different tiers.

```tsx
<AchievementBadge achievement="gold" badgeContent="!">
  <RobloxAvatar level={100}>
    <Avatar>👑</Avatar>
  </RobloxAvatar>
</AchievementBadge>
```

### RobloxFAB
Floating action button with game-like hover effects.

```tsx
<RobloxFAB>
  <AddIcon />
</RobloxFAB>
```

### GameContainer
Special container with animated background effects.

```tsx
<GameContainer>
  <Typography variant="h4">Welcome to the Arena!</Typography>
  <Typography>Your gaming content here</Typography>
</GameContainer>
```

### RobloxSkeleton
Loading skeleton with Roblox-themed shimmer effect.

```tsx
<RobloxSkeleton width="60%" height={32} />
<RobloxSkeleton width="100%" height={120} />
```

### RobloxNotificationCard
Notification card with severity-based styling.

```tsx
<RobloxNotificationCard severity="success">
  <Typography>Achievement unlocked!</Typography>
</RobloxNotificationCard>
```

## Animation Classes

Add these CSS classes for animations:

```tsx
// Pulse animation
<div className="roblox-pulse">Pulsing element</div>

// Floating animation
<div className="roblox-float">Floating element</div>

// Glow effect
<div className="roblox-glow">Glowing element</div>

// Shimmer effect
<div className="roblox-shimmer">Shimmering element</div>

// Scale on hover
<div className="roblox-scale">Hoverable element</div>
```

## Theme Modes

### Light Mode
- Clean white backgrounds
- Roblox red accents
- High contrast for readability
- Professional appearance for educators

### Dark Mode
- Dark gray backgrounds
- Reduced eye strain
- Enhanced focus on content
- Gaming-inspired aesthetics

### System Mode
- Automatically follows user's OS preference
- Switches between light/dark based on system settings
- Default mode for new users

## Accessibility

### Color Contrast
- All text meets WCAG AA standards (4.5:1 ratio)
- Interactive elements have sufficient contrast
- Focus indicators are clearly visible

### Focus Management
- Custom focus rings with Roblox red
- Logical tab order
- Skip navigation links
- Screen reader friendly

### Motion
- Respects `prefers-reduced-motion`
- Smooth transitions (300ms default)
- Optional animation disable
- Performance optimized

### Responsive Design
- Mobile-first approach
- Touch-friendly hit areas (44px minimum)
- Fluid typography scaling
- Flexible grid layouts

## Gamification Features

### XP System
```tsx
// Show XP progress
<XPProgressBar value={xpProgress} level={userLevel} />

// Award XP with animation
<RobloxChip 
  label={`+${xpEarned} XP`} 
  rarity="epic" 
  className="roblox-pulse"
/>
```

### Achievement System
```tsx
// Achievement notification
<RobloxNotificationCard severity="success">
  <AchievementBadge achievement="gold">
    <EmojiEventsIcon />
  </AchievementBadge>
  <Typography>First Lesson Complete!</Typography>
</RobloxNotificationCard>
```

### Leaderboards
```tsx
// User ranking display
<RobloxCard>
  <RobloxAvatar level={user.level} isOnline={user.isOnline}>
    <Avatar src={user.avatar} />
  </RobloxAvatar>
  <Typography>{user.name}</Typography>
  <RobloxChip rarity={user.tier} label={`Rank #${user.rank}`} />
</RobloxCard>
```

## Best Practices

### Performance
- Use CSS-in-JS for dynamic theming
- Leverage Material-UI's built-in optimizations
- Minimize animation complexity
- Use transform properties for smooth animations

### Consistency
- Always use design tokens instead of hardcoded values
- Follow the established component API patterns
- Maintain consistent spacing and typography
- Use semantic color names

### Accessibility
- Test with screen readers
- Ensure keyboard navigation works
- Verify color contrast ratios
- Provide alternative text for visual elements

### Customization
- Extend existing components rather than creating new ones
- Use theme overrides for global changes
- Follow the established naming conventions
- Document any custom components

## Migration Guide

### From Old Theme System

1. **Update imports:**
   ```tsx
   // Old
   import { theme } from './theme/index';
   
   // New
   import { RobloxThemeProvider, useThemeContext } from './theme';
   ```

2. **Replace ThemeProvider:**
   ```tsx
   // Old
   <ThemeProvider theme={theme}>
   
   // New
   <RobloxThemeProvider>
   ```

3. **Update styled components:**
   ```tsx
   // Old
   const StyledCard = styled(Card)(...);
   
   // New
   import { RobloxCard } from './theme';
   ```

4. **Update color references:**
   ```tsx
   // Old
   color: theme.palette.primary.main
   
   // New
   color: '#E2231A' // or use theme tokens
   ```

### Breaking Changes
- Theme structure has been reorganized
- Some color values have changed to match Roblox branding
- Animation timing functions updated
- Component prop APIs may have changed

## Contributing

When adding new components or modifying existing ones:

1. Follow the established patterns in `RobloxStyledComponents.tsx`
2. Use design tokens from `designTokens.ts`
3. Include proper TypeScript types
4. Add accessibility features (focus states, ARIA labels)
5. Test in both light and dark modes
6. Document any new props or usage patterns
7. Update this guide with new components

## Troubleshooting

### Theme Not Loading
- Ensure `ThemeWrapper` is at the root of your app
- Check for JavaScript errors in console
- Verify all theme files are properly imported

### Colors Not Updating
- Check if you're using theme tokens vs hardcoded values
- Ensure the theme context is properly configured
- Verify theme mode is being set correctly

### Performance Issues
- Reduce animation complexity
- Use CSS transforms instead of changing layout properties
- Check for unnecessary re-renders
- Consider using `React.memo` for expensive components

### Accessibility Problems
- Test with keyboard navigation
- Use a screen reader to test announcements
- Verify color contrast with accessibility tools
- Check focus indicator visibility

---

**Built with ❤️ for the ToolBoxAI educational platform**

For more information, see the individual component documentation in the `src/theme/` directory.
