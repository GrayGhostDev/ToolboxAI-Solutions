/**
 * Test Validation Utility
 *
 * Ensures all test files meet the >85% pass rate requirement
 */

import { type Suite, type Task, type File } from 'vitest';

export interface TestResults {
  filename: string;
  total: number;
  passed: number;
  failed: number;
  skipped: number;
  passRate: number;
  failingTests: string[];
  duration: number;
}

export interface TestReport {
  totalFiles: number;
  passedFiles: number;
  failedFiles: FileReport[];
  overallTests: number;
  overallPassed: number;
  overallFailed: number;
  overallPassRate: number;
  executionTime: number;
  timestamp: string;
}

export interface FileReport {
  filename: string;
  passRate: string;
  passed: number;
  total: number;
  failing: string[];
}

/**
 * TestValidator class for validating test pass rates
 */
export class TestValidator {
  private static readonly REQUIRED_PASS_RATE = 85;
  private static readonly MIN_TESTS_PER_FILE = 10;

  /**
   * Validate a single test file meets requirements
   */
  static validateTestFile(filename: string, results: TestResults): boolean {
    // Check minimum test count
    if (results.total < this.MIN_TESTS_PER_FILE) {
      console.warn(
        `⚠️ ${filename}: Only ${results.total} tests. Minimum required: ${this.MIN_TESTS_PER_FILE}`
      );
    }

    // Calculate pass rate
    const passRate = results.total > 0 ? (results.passed / results.total) * 100 : 0;
    results.passRate = passRate;

    // Validate pass rate
    if (passRate < this.REQUIRED_PASS_RATE) {
      console.error(
        `❌ ${filename} failed validation:\n` +
        `   Pass rate: ${passRate.toFixed(1)}% (${results.passed}/${results.total} passed)\n` +
        `   Required: >${this.REQUIRED_PASS_RATE}%\n` +
        `   Failing tests: ${results.failingTests.join(', ')}`
      );
      return false;
    }

    console.log(
      `✅ ${filename}: ${passRate.toFixed(1)}% pass rate (${results.passed}/${results.total} passed) - MEETS REQUIREMENT`
    );
    return true;
  }

  /**
   * Generate a comprehensive test report
   */
  static generateReport(allResults: Map<string, TestResults>): TestReport {
    const report: TestReport = {
      totalFiles: allResults.size,
      passedFiles: 0,
      failedFiles: [],
      overallTests: 0,
      overallPassed: 0,
      overallFailed: 0,
      overallPassRate: 0,
      executionTime: 0,
      timestamp: new Date().toISOString(),
    };

    // Process each file's results
    allResults.forEach((results, filename) => {
      const passRate = (results.passed / results.total) * 100;
      report.overallTests += results.total;
      report.overallPassed += results.passed;
      report.overallFailed += results.failed;
      report.executionTime += results.duration;

      if (passRate >= this.REQUIRED_PASS_RATE) {
        report.passedFiles++;
      } else {
        report.failedFiles.push({
          filename,
          passRate: passRate.toFixed(1),
          passed: results.passed,
          total: results.total,
          failing: results.failingTests,
        });
      }
    });

    // Calculate overall pass rate
    report.overallPassRate =
      report.overallTests > 0
        ? (report.overallPassed / report.overallTests) * 100
        : 0;

    return report;
  }

  /**
   * Print formatted test report
   */
  static printReport(report: TestReport): void {
    const passed = report.failedFiles.length === 0;
    const statusEmoji = passed ? '✅' : '❌';
    const statusText = passed ? 'ALL PASSED' : 'FAILED';

    console.log('\n' + '='.repeat(60));
    console.log('TEST EXECUTION REPORT');
    console.log('='.repeat(60));
    console.log(`Timestamp: ${report.timestamp}`);
    console.log(`Total Test Files: ${report.totalFiles}`);
    console.log(
      `Files Meeting >85% Requirement: ${report.passedFiles}/${report.totalFiles} ${statusEmoji}`
    );

    if (report.failedFiles.length > 0) {
      console.log('\nFailed Files:');
      console.log('-'.repeat(40));
      report.failedFiles.forEach(file => {
        console.log(`❌ ${file.filename}`);
        console.log(`   Pass rate: ${file.passRate}% (${file.passed}/${file.total})`);
        if (file.failing.length > 0) {
          console.log(`   Failing: ${file.failing.slice(0, 3).join(', ')}${file.failing.length > 3 ? '...' : ''}`);
        }
      });
    }

    console.log('\nOverall Statistics:');
    console.log('-'.repeat(40));
    console.log(`Total Tests: ${report.overallTests}`);
    console.log(`Passed Tests: ${report.overallPassed}`);
    console.log(`Failed Tests: ${report.overallFailed}`);
    console.log(
      `Overall Pass Rate: ${report.overallPassRate.toFixed(1)}% ${
        report.overallPassRate >= this.REQUIRED_PASS_RATE ? '✅' : '❌'
      }`
    );

    console.log('\nPerformance:');
    console.log('-'.repeat(40));
    console.log(`Total Execution Time: ${(report.executionTime / 1000).toFixed(2)}s`);
    console.log(
      `Average Time per File: ${(report.executionTime / report.totalFiles / 1000).toFixed(2)}s`
    );

    console.log('\nQuality Gates:');
    console.log('-'.repeat(40));
    const gates = [
      {
        name: 'All files >85% pass rate',
        passed: report.failedFiles.length === 0,
      },
      {
        name: 'Overall >85% pass rate',
        passed: report.overallPassRate >= this.REQUIRED_PASS_RATE,
      },
      {
        name: 'Execution time <60s',
        passed: report.executionTime < 60000,
      },
    ];

    gates.forEach(gate => {
      console.log(`${gate.passed ? '✅' : '❌'} ${gate.name}`);
    });

    const allGatesPassed = gates.every(g => g.passed);
    console.log(`\nFinal Status: ${allGatesPassed ? '✅ ALL PASSED' : '❌ FAILED'}`);
    console.log('='.repeat(60) + '\n');
  }

  /**
   * Create a markdown report for documentation
   */
  static generateMarkdownReport(report: TestReport): string {
    const passed = report.failedFiles.length === 0;
    const statusEmoji = passed ? '✅' : '❌';

    let markdown = `# Test Execution Report ${statusEmoji}\n\n`;
    markdown += `**Generated:** ${report.timestamp}\n\n`;
    markdown += `## Summary\n\n`;
    markdown += `- **Total Test Files:** ${report.totalFiles}\n`;
    markdown += `- **Files Meeting >85% Requirement:** ${report.passedFiles}/${report.totalFiles}\n`;
    markdown += `- **Overall Pass Rate:** ${report.overallPassRate.toFixed(1)}%\n`;
    markdown += `- **Execution Time:** ${(report.executionTime / 1000).toFixed(2)}s\n\n`;

    if (report.failedFiles.length > 0) {
      markdown += `## Failed Files\n\n`;
      markdown += `| File | Pass Rate | Tests Passed | Status |\n`;
      markdown += `|------|-----------|--------------|--------|\n`;
      report.failedFiles.forEach(file => {
        markdown += `| ${file.filename} | ${file.passRate}% | ${file.passed}/${file.total} | ❌ |\n`;
      });
      markdown += '\n';
    }

    markdown += `## Test Statistics\n\n`;
    markdown += `| Metric | Value |\n`;
    markdown += `|--------|-------|\n`;
    markdown += `| Total Tests | ${report.overallTests} |\n`;
    markdown += `| Passed Tests | ${report.overallPassed} |\n`;
    markdown += `| Failed Tests | ${report.overallFailed} |\n`;
    markdown += `| Overall Pass Rate | ${report.overallPassRate.toFixed(1)}% |\n\n`;

    markdown += `## Quality Gates\n\n`;
    markdown += `| Gate | Status |\n`;
    markdown += `|------|--------|\n`;
    markdown += `| All files >85% pass rate | ${report.failedFiles.length === 0 ? '✅ Passed' : '❌ Failed'} |\n`;
    markdown += `| Overall >85% pass rate | ${report.overallPassRate >= 85 ? '✅ Passed' : '❌ Failed'} |\n`;
    markdown += `| Execution time <60s | ${report.executionTime < 60000 ? '✅ Passed' : '❌ Failed'} |\n`;

    return markdown;
  }

  /**
   * Parse Vitest results and extract test information
   */
  static parseVitestResults(suite: Suite): Map<string, TestResults> {
    const resultsMap = new Map<string, TestResults>();

    function processSuite(s: Suite, filepath: string) {
      const results: TestResults = {
        filename: filepath,
        total: 0,
        passed: 0,
        failed: 0,
        skipped: 0,
        passRate: 0,
        failingTests: [],
        duration: 0,
      };

      // Process tasks in the suite
      s.tasks?.forEach((task: Task) => {
        if (task.type === 'test') {
          results.total++;
          results.duration += task.result?.duration || 0;

          switch (task.result?.state) {
            case 'pass':
              results.passed++;
              break;
            case 'fail':
              results.failed++;
              results.failingTests.push(task.name);
              break;
            case 'skip':
              results.skipped++;
              break;
          }
        } else if (task.type === 'suite' && 'tasks' in task) {
          // Recursively process nested suites
          const nestedSuite = task as Suite;
          const nestedResults = processSuite(nestedSuite, filepath);
          results.total += nestedResults.total;
          results.passed += nestedResults.passed;
          results.failed += nestedResults.failed;
          results.skipped += nestedResults.skipped;
          results.failingTests.push(...nestedResults.failingTests);
          results.duration += nestedResults.duration;
        }
      });

      return results;
    }

    // Process each file
    const files = (suite as any).files || [];
    files.forEach((file: File) => {
      const filepath = file.filepath || file.name || 'unknown';
      const results = processSuite(file, filepath);
      resultsMap.set(filepath, results);
    });

    return resultsMap;
  }

  /**
   * Assert that all tests meet requirements (for CI/CD)
   */
  static assertAllTestsPass(report: TestReport): void {
    if (report.failedFiles.length > 0) {
      const message =
        `Test validation failed!\n` +
        `${report.failedFiles.length} file(s) have <85% pass rate:\n` +
        report.failedFiles.map(f => `  - ${f.filename}: ${f.passRate}%`).join('\n');

      throw new Error(message);
    }

    if (report.overallPassRate < this.REQUIRED_PASS_RATE) {
      throw new Error(
        `Overall pass rate ${report.overallPassRate.toFixed(1)}% is below required ${this.REQUIRED_PASS_RATE}%`
      );
    }

    console.log('✅ All test validation requirements met!');
  }
}

/**
 * Helper function to validate tests during development
 */
export function validateTests(results: Map<string, TestResults>): boolean {
  let allPassed = true;

  results.forEach((result, filename) => {
    const passed = TestValidator.validateTestFile(filename, result);
    if (!passed) {
      allPassed = false;
    }
  });

  const report = TestValidator.generateReport(results);
  TestValidator.printReport(report);

  return allPassed;
}

/**
 * Mock test results for testing the validator itself
 */
export function createMockTestResults(
  filename: string,
  passed: number,
  failed: number,
  skipped: number = 0
): TestResults {
  const total = passed + failed + skipped;
  const failingTests = Array.from({ length: failed }, (_, i) => `Test ${i + 1}`);

  return {
    filename,
    total,
    passed,
    failed,
    skipped,
    passRate: (passed / total) * 100,
    failingTests,
    duration: Math.random() * 5000, // Random duration 0-5s
  };
}

/**
 * Export validator instance for direct use
 */
export default TestValidator;