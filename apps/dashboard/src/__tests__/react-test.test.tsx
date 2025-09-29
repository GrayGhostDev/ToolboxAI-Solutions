/**
 * Simple React Test to Debug Hooks Issue
 */

import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';

// Simple component to test React hooks
function TestComponent() {
  const [count, setCount] = React.useState(0);

  return (
    <div>
      <span data-testid="count">{count}</span>
      <button onClick={() => setCount(c => c + 1)}>Increment</button>
    </div>
  );
}

describe('React Hooks Test', () => {
  it('should render a component with useState hook', () => {
    render(<TestComponent />);

    expect(screen.getByTestId('count')).toBeInTheDocument();
    expect(screen.getByTestId('count')).toHaveTextContent('0');
  });
});