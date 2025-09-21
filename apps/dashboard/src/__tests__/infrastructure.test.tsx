/**
 * Infrastructure Validation Test
 * Tests the basic test infrastructure setup for 2025 standards
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@test/utils/render';
import React from 'react';

// Simple test component
const TestComponent: React.FC<{ message?: string }> = ({ message = 'Hello Test' }) => {
  return (
    <div data-testid="test-component">
      <h1>{message}</h1>
      <button onClick={() => console.log('clicked')}>Test Button</button>
    </div>
  );
};

describe('Test Infrastructure Validation', () => {
  it('should support basic component rendering', () => {
    render(<TestComponent />);

    expect(screen.getByTestId('test-component')).toBeInTheDocument();
    expect(screen.getByText('Hello Test')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Test Button' })).toBeInTheDocument();
  });

  it('should support custom props', () => {
    render(<TestComponent message="Custom Message" />);

    expect(screen.getByText('Custom Message')).toBeInTheDocument();
  });

  it('should support Vitest mocking', () => {
    const mockFunction = vi.fn();
    mockFunction('test');

    expect(mockFunction).toHaveBeenCalledWith('test');
    expect(mockFunction).toHaveBeenCalledTimes(1);
  });

  it('should support async operations', async () => {
    const asyncOperation = () => Promise.resolve('async result');

    const result = await asyncOperation();
    expect(result).toBe('async result');
  });

  it('should support DOM queries', () => {
    render(<TestComponent />);

    // Test different query methods
    expect(screen.getByTestId('test-component')).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('should support custom render options', () => {
    render(<TestComponent />, {
      routerProps: {
        initialEntries: ['/test-path'],
      }
    });

    expect(screen.getByTestId('test-component')).toBeInTheDocument();
  });

  it('should validate environment globals', () => {
    expect(globalThis.__TEST__).toBe(true);
    expect(globalThis.__DEV__).toBe(false);
    expect(process.env.NODE_ENV).toBe('test');
  });
});