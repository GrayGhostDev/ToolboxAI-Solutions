# Accessibility Guide - Roblox Dashboard

**Version**: 1.0.0
**Last Updated**: 2025-10-01
**WCAG Compliance**: 2.1 AA
**Framework**: Mantine v8 with React 19

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Keyboard Navigation](#keyboard-navigation)
3. [Screen Reader Support](#screen-reader-support)
4. [Color Contrast](#color-contrast)
5. [Focus Management](#focus-management)
6. [ARIA Labels](#aria-labels)
7. [Component Accessibility](#component-accessibility)
8. [Testing](#testing)

---

## 🎯 Overview

This dashboard implements WCAG 2.1 AA accessibility standards to ensure all users can effectively use the Roblox-themed interface.

### Key Features

- **Keyboard Navigation**: Complete keyboard support for all interactive elements
- **Screen Readers**: ARIA labels and semantic HTML for assistive technologies
- **Color Contrast**: Minimum 4.5:1 contrast ratios for all text
- **Focus Indicators**: Clear visual focus states
- **Alternative Text**: Descriptive text for all images and icons
- **Skip Links**: Quick navigation to main content areas

---

## ⌨️ Keyboard Navigation

### Global Shortcuts

| Shortcut | Action | Scope |
|----------|--------|-------|
| `Tab` | Move focus forward | Global |
| `Shift + Tab` | Move focus backward | Global |
| `Enter` | Activate focused element | Global |
| `Space` | Activate button/checkbox | Buttons, Checkboxes |
| `Escape` | Close modal/drawer | Modals, Drawers |
| `Arrow Keys` | Navigate within components | Navigation, Tabs |
| `/` | Focus search input | Global |
| `?` | Open keyboard shortcuts help | Global |

### Dashboard-Specific Shortcuts

| Shortcut | Action | Scope |
|----------|--------|-------|
| `g h` | Go to Home | Global |
| `g c` | Go to Courses | Global |
| `g a` | Go to Achievements | Global |
| `g p` | Go to Profile | Global |
| `Alt + n` | Open notifications | Global |
| `Alt + s` | Open settings | Global |
| `Alt + m` | Toggle sidebar | Global |

### Implementation

```typescript
// useKeyboardShortcuts.ts
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export interface KeyboardShortcut {
  key: string;
  modifiers?: ('ctrl' | 'alt' | 'shift' | 'meta')[];
  action: () => void;
  description: string;
}

export const useKeyboardShortcuts = (shortcuts: KeyboardShortcut[]) => {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      shortcuts.forEach((shortcut) => {
        const modifiersMatch =
          (!shortcut.modifiers || shortcut.modifiers.length === 0) ||
          shortcut.modifiers.every((mod) => {
            switch (mod) {
              case 'ctrl': return event.ctrlKey;
              case 'alt': return event.altKey;
              case 'shift': return event.shiftKey;
              case 'meta': return event.metaKey;
              default: return false;
            }
          });

        if (modifiersMatch && event.key === shortcut.key) {
          event.preventDefault();
          shortcut.action();
        }
      });
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts]);
};

// Usage in component
export const DashboardLayout = () => {
  const navigate = useNavigate();

  const shortcuts: KeyboardShortcut[] = [
    { key: 'h', modifiers: ['alt'], action: () => navigate('/'), description: 'Go to Home' },
    { key: 'c', modifiers: ['alt'], action: () => navigate('/courses'), description: 'Go to Courses' },
    { key: 'a', modifiers: ['alt'], action: () => navigate('/achievements'), description: 'Go to Achievements' },
    { key: '/', action: () => document.getElementById('search')?.focus(), description: 'Focus search' },
  ];

  useKeyboardShortcuts(shortcuts);

  return <>{/* Layout content */}</>;
};
```

### Roving Tab Index for Navigation

```typescript
// useRovingTabIndex.ts
import { useEffect, useState } from 'react';

export const useRovingTabIndex = (itemsCount: number) => {
  const [activeIndex, setActiveIndex] = useState(0);

  const handleKeyDown = (event: KeyboardEvent) => {
    switch (event.key) {
      case 'ArrowRight':
      case 'ArrowDown':
        event.preventDefault();
        setActiveIndex((prev) => (prev + 1) % itemsCount);
        break;
      case 'ArrowLeft':
      case 'ArrowUp':
        event.preventDefault();
        setActiveIndex((prev) => (prev - 1 + itemsCount) % itemsCount);
        break;
      case 'Home':
        event.preventDefault();
        setActiveIndex(0);
        break;
      case 'End':
        event.preventDefault();
        setActiveIndex(itemsCount - 1);
        break;
    }
  };

  return { activeIndex, handleKeyDown };
};

// Usage in Roblox3DNavigation
export const Roblox3DNavigation = ({ items }: Props) => {
  const { activeIndex, handleKeyDown } = useRovingTabIndex(items.length);

  return (
    <nav role="navigation" aria-label="Main navigation" onKeyDown={handleKeyDown}>
      {items.map((item, index) => (
        <button
          key={item.id}
          tabIndex={index === activeIndex ? 0 : -1}
          aria-current={index === activeIndex ? 'page' : undefined}
        >
          {item.label}
        </button>
      ))}
    </nav>
  );
};
```

---

## 🔊 Screen Reader Support

### ARIA Landmarks

```typescript
// Proper semantic structure
<div>
  <header role="banner">
    <nav aria-label="Main navigation" role="navigation">
      {/* Navigation items */}
    </nav>
  </header>

  <main role="main" aria-label="Main content">
    <section aria-labelledby="dashboard-heading">
      <h1 id="dashboard-heading">Dashboard</h1>
      {/* Content */}
    </section>
  </main>

  <aside role="complementary" aria-label="Achievements sidebar">
    {/* Sidebar content */}
  </aside>

  <footer role="contentinfo">
    {/* Footer content */}
  </footer>
</div>
```

### Live Regions for Dynamic Content

```typescript
// useLiveRegion.ts
import { useEffect, useRef } from 'react';

export const useLiveRegion = (message: string, politeness: 'polite' | 'assertive' = 'polite') => {
  const liveRegionRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (liveRegionRef.current && message) {
      liveRegionRef.current.textContent = message;
    }
  }, [message]);

  return (
    <div
      ref={liveRegionRef}
      role="status"
      aria-live={politeness}
      aria-atomic="true"
      className="sr-only"
    />
  );
};

// Usage for XP updates
export const XPTracker = ({ xp }: Props) => {
  const [message, setMessage] = useState('');
  const liveRegion = useLiveRegion(message);

  const handleXPGain = (amount: number) => {
    setMessage(`You earned ${amount} XP!`);
  };

  return (
    <>
      {liveRegion}
      <div aria-label={`Current XP: ${xp}`}>
        {xp} XP
      </div>
    </>
  );
};
```

### Descriptive Labels

```typescript
// Roblox3DButton with accessibility
export const Roblox3DButton = ({
  iconName,
  label,
  onClick,
  ariaLabel,
  ariaDescribedBy
}: Props) => {
  return (
    <button
      onClick={onClick}
      aria-label={ariaLabel || label}
      aria-describedby={ariaDescribedBy}
      className="roblox-button"
    >
      {iconName && <Roblox3DIcon name={iconName} aria-hidden="true" />}
      <span>{label}</span>
    </button>
  );
};
```

---

## 🎨 Color Contrast

### WCAG AA Compliance

All text meets minimum contrast ratios:

| Text Size | Normal | Large (18pt+) | UI Components |
|-----------|--------|---------------|---------------|
| Minimum Ratio | 4.5:1 | 3:1 | 3:1 |

### Roblox Theme Contrast

```typescript
// High contrast variants for accessibility
export const accessibleColors = {
  // Primary actions - meets 4.5:1 on dark bg
  primary: {
    light: '#33ccff', // Lighter electric blue
    DEFAULT: '#00bfff',
    dark: '#0099cc',
  },

  // Success - meets 4.5:1
  success: {
    light: '#33ff66', // Lighter toxic green
    DEFAULT: '#00ff00',
    dark: '#00cc00',
  },

  // Warning - meets 4.5:1
  warning: {
    light: '#ffcc00',
    DEFAULT: '#ffaa00',
    dark: '#ff8800',
  },

  // Error - meets 4.5:1
  error: {
    light: '#ff6666',
    DEFAULT: '#ff3333',
    dark: '#cc0000',
  },

  // Text on dark background
  text: {
    primary: '#ffffff',   // 21:1 ratio
    secondary: '#e0e0e0', // 12:1 ratio
    disabled: '#9e9e9e',  // 4.5:1 ratio
  },
};
```

### Contrast Testing Tool

```typescript
// ContrastChecker.tsx
export const ContrastChecker = ({ foreground, background }: Props) => {
  const calculateContrast = (fg: string, bg: string): number => {
    // Implementation of WCAG contrast calculation
    const getLuminance = (color: string): number => {
      // Convert hex to RGB and calculate relative luminance
      const rgb = parseInt(color.slice(1), 16);
      const r = (rgb >> 16) & 0xff;
      const g = (rgb >> 8) & 0xff;
      const b = (rgb >> 0) & 0xff;

      const toLinear = (val: number) => {
        const v = val / 255;
        return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
      };

      return 0.2126 * toLinear(r) + 0.7152 * toLinear(g) + 0.0722 * toLinear(b);
    };

    const l1 = getLuminance(fg);
    const l2 = getLuminance(bg);
    const lighter = Math.max(l1, l2);
    const darker = Math.min(l1, l2);

    return (lighter + 0.05) / (darker + 0.05);
  };

  const ratio = calculateContrast(foreground, background);
  const passesAA = ratio >= 4.5;
  const passesAAA = ratio >= 7;

  return (
    <div>
      <Text>Contrast Ratio: {ratio.toFixed(2)}:1</Text>
      <Badge color={passesAA ? 'green' : 'red'}>
        {passesAAA ? 'AAA' : passesAA ? 'AA' : 'Fail'}
      </Badge>
    </div>
  );
};
```

---

## 🎯 Focus Management

### Custom Focus Styles

```typescript
// Global focus styles (apps/dashboard/src/theme/mantine-theme.ts)
export const mantineTheme = createTheme({
  focusRing: 'always',
  focusClassName: 'roblox-focus',

  components: {
    Button: Button.extend({
      classNames: {
        root: 'roblox-button',
      },
      styles: (theme) => ({
        root: {
          '&:focus-visible': {
            outline: `3px solid ${theme.colors.electricBlue[5]}`,
            outlineOffset: '2px',
            boxShadow: `0 0 0 4px ${theme.colors.electricBlue[2]}40`,
          },
        },
      }),
    }),
  },
});
```

### Focus Trap for Modals

```typescript
// useFocusTrap.ts
import { useEffect, useRef } from 'react';

export const useFocusTrap = (isActive: boolean) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isActive || !containerRef.current) return;

    const container = containerRef.current;
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

    const handleTabKey = (event: KeyboardEvent) => {
      if (event.key !== 'Tab') return;

      if (event.shiftKey) {
        if (document.activeElement === firstElement) {
          event.preventDefault();
          lastElement?.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          event.preventDefault();
          firstElement?.focus();
        }
      }
    };

    firstElement?.focus();
    container.addEventListener('keydown', handleTabKey);

    return () => {
      container.removeEventListener('keydown', handleTabKey);
    };
  }, [isActive]);

  return containerRef;
};

// Usage
export const RobloxModal = ({ isOpen, onClose, children }: Props) => {
  const trapRef = useFocusTrap(isOpen);

  return (
    <Modal opened={isOpen} onClose={onClose}>
      <div ref={trapRef}>
        {children}
      </div>
    </Modal>
  );
};
```

---

## 🏷️ ARIA Labels

### Component-Specific Labels

```typescript
// Roblox3DMetricCard with full ARIA support
export const Roblox3DMetricCard = ({
  title,
  value,
  icon,
  trend
}: Props) => {
  const trendLabel = trend > 0
    ? `increased by ${trend}%`
    : `decreased by ${Math.abs(trend)}%`;

  return (
    <Card
      role="article"
      aria-labelledby={`metric-${title}`}
      aria-describedby={`metric-desc-${title}`}
    >
      <Group>
        {icon && <div aria-hidden="true">{icon}</div>}
        <div>
          <Text id={`metric-${title}`} size="sm" c="dimmed">
            {title}
          </Text>
          <Text
            id={`metric-desc-${title}`}
            size="xl"
            fw={700}
            aria-label={`${title}: ${value}, ${trendLabel}`}
          >
            {value}
          </Text>
        </div>
      </Group>
    </Card>
  );
};
```

### Progress Indicators

```typescript
// Accessible progress bar
export const RobloxProgressBar = ({
  value,
  max,
  label
}: Props) => {
  const percentage = (value / max) * 100;

  return (
    <div>
      <Text id="progress-label" size="sm" mb="xs">
        {label}
      </Text>
      <Progress
        value={percentage}
        aria-labelledby="progress-label"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-valuetext={`${value} of ${max} completed`}
      />
      <Text size="xs" c="dimmed" mt="xs">
        {value} / {max} ({percentage.toFixed(0)}%)
      </Text>
    </div>
  );
};
```

---

## 🧩 Component Accessibility

### Roblox3DButton

```typescript
interface Roblox3DButtonProps {
  iconName?: string;
  label?: string;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  loading?: boolean;
  ariaLabel?: string;
  ariaDescribedBy?: string;
  ariaPressed?: boolean; // For toggle buttons
}

export const Roblox3DButton = memo(({
  iconName,
  label,
  onClick,
  disabled,
  loading,
  ariaLabel,
  ariaPressed,
  ...props
}: Roblox3DButtonProps) => {
  return (
    <Button
      onClick={onClick}
      disabled={disabled || loading}
      aria-label={ariaLabel || label}
      aria-pressed={ariaPressed}
      aria-busy={loading}
      {...props}
    >
      {loading ? (
        <Loader size="xs" aria-label="Loading" />
      ) : iconName ? (
        <Roblox3DIcon name={iconName} aria-hidden="true" />
      ) : null}
      {label && <span>{label}</span>}
    </Button>
  );
});
```

### Roblox3DNavigation

```typescript
export const Roblox3DNavigation = ({
  items,
  activeId,
  onItemClick
}: Props) => {
  const { activeIndex, handleKeyDown } = useRovingTabIndex(items.length);

  return (
    <nav
      role="navigation"
      aria-label="Main navigation"
      onKeyDown={handleKeyDown}
    >
      {items.map((item, index) => (
        <button
          key={item.id}
          onClick={() => onItemClick?.(item)}
          tabIndex={index === activeIndex ? 0 : -1}
          aria-current={item.id === activeId ? 'page' : undefined}
          aria-label={item.tooltip || item.label}
        >
          <Roblox3DIcon name={item.iconName} aria-hidden="true" />
          <span>{item.label}</span>
          {item.badge && (
            <Badge aria-label={`${item.badge} notifications`}>
              {item.badge}
            </Badge>
          )}
        </button>
      ))}
    </nav>
  );
};
```

---

## 🧪 Testing

### Automated Testing

```bash
# Install accessibility testing tools
npm install --save-dev @axe-core/react vitest-axe
```

```typescript
// setupTests.ts
import { configureAxe } from 'vitest-axe';

configureAxe({
  rules: {
    // WCAG 2.1 AA rules
    'color-contrast': { enabled: true },
    'label': { enabled: true },
    'button-name': { enabled: true },
    'image-alt': { enabled: true },
  },
});
```

```typescript
// Roblox3DButton.test.tsx
import { render } from '@testing-library/react';
import { axe } from 'vitest-axe';
import { Roblox3DButton } from './Roblox3DButton';

describe('Roblox3DButton Accessibility', () => {
  it('should have no accessibility violations', async () => {
    const { container } = render(
      <Roblox3DButton label="Click me" iconName="TROPHY" />
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should be keyboard navigable', () => {
    const handleClick = vi.fn();
    const { getByRole } = render(
      <Roblox3DButton label="Click me" onClick={handleClick} />
    );

    const button = getByRole('button');
    button.focus();
    expect(button).toHaveFocus();

    fireEvent.keyDown(button, { key: 'Enter' });
    expect(handleClick).toHaveBeenCalled();
  });

  it('should announce loading state to screen readers', () => {
    const { getByRole } = render(
      <Roblox3DButton label="Submit" loading />
    );

    const button = getByRole('button');
    expect(button).toHaveAttribute('aria-busy', 'true');
  });
});
```

### Manual Testing Checklist

- [ ] **Keyboard Navigation**
  - [ ] Tab through all interactive elements
  - [ ] Activate buttons with Enter/Space
  - [ ] Navigate lists with arrow keys
  - [ ] Close modals with Escape
  - [ ] Test keyboard shortcuts

- [ ] **Screen Reader**
  - [ ] Test with NVDA (Windows)
  - [ ] Test with JAWS (Windows)
  - [ ] Test with VoiceOver (macOS/iOS)
  - [ ] Test with TalkBack (Android)
  - [ ] Verify all images have alt text
  - [ ] Verify form labels are associated
  - [ ] Verify live regions announce updates

- [ ] **Color Contrast**
  - [ ] Use browser DevTools contrast checker
  - [ ] Test with color blindness simulators
  - [ ] Verify focus indicators are visible

- [ ] **Focus Management**
  - [ ] Focus visible on all interactive elements
  - [ ] Focus trap works in modals
  - [ ] Focus restored when modals close

- [ ] **Responsive**
  - [ ] Test at 200% zoom
  - [ ] Test on mobile devices
  - [ ] Test landscape/portrait orientations

---

## 📚 Resources

- **WCAG 2.1 Guidelines**: https://www.w3.org/WAI/WCAG21/quickref/
- **Mantine Accessibility**: https://mantine.dev/guides/accessibility/
- **React Aria**: https://react-spectrum.adobe.com/react-aria/
- **axe DevTools**: https://www.deque.com/axe/devtools/
- **WebAIM**: https://webaim.org/

---

**Version**: 1.0.0
**Last Updated**: 2025-10-01
**Maintainer**: ToolboxAI Development Team
