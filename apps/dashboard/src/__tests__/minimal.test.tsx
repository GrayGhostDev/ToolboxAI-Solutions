/**
 * Minimal test to verify React rendering works
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';

// Simple component without MUI
function SimpleComponent() {
  return (
    <div>
      <h1>Test Component</h1>
      <button>Click me</button>
    </div>
  );
}

describe('Minimal Test', () => {
  it('should render simple component', () => {
    render(<SimpleComponent />);

    expect(screen.getByText('Test Component')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
  });
});