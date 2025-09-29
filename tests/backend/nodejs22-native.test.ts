jest.setTimeout(10000);

// Example using Node.js 22 native test runner
import { describe, it, before, after } from 'node:test';
import assert from 'node:assert/strict';

describe('Node.js 22 Native Test Example', () => {
  let testData: any;

  before(async () => {
    // Setup before tests
    testData = { value: 42 };
  });

  after(async () => {
    // Cleanup after tests
    testData = null;
  });

  it('should use native test runner', () => {
    assert.equal(typeof test, 'function');
  });

  it('should support async tests', async () => {
    const result = await Promise.resolve(testData.value);
    assert.equal(result, 42);
  });

  it('should have native assertions', () => {
    assert.deepEqual([1, 2, 3], [1, 2, 3]);
    assert.throws(() => {
      throw new Error('Test error');
    }, /Test error/);
  });

  describe('nested suite', () => {
    it('should support nested tests', () => {
      assert.ok(true);
    });
  });
});
