import { describe, it, expect } from 'vitest';

describe('Basic Test', () => {
  it('should pass a simple test', () => {
    expect(1 + 1).toBe(2);
  });

  it('should have testing library available', () => {
    expect(typeof expect).toBe('function');
  });
});