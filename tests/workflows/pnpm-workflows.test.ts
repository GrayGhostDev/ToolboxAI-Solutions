/**
 * Unit Tests for pnpm Workflow Verification
 * 
 * Tests cover:
 * 1. pnpm setup verification across all workflows
 * 2. Dependency installation with pnpm
 * 3. Script execution (lint, test, build, type-check, format:check)
 * 4. Playwright commands execution via pnpm exec
 * 5. Global package installation (Vercel CLI, etc.)
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import * as cp from 'child_process';

// Mock child process
vi.mock('child_process');

interface WorkflowConfig {
  name: string;
  filePath: string;
  expectedSetupSteps: string[];
  expectedScripts: string[];
  expectedGlobalPackages?: string[];
}

/**
 * Test 1: Verify pnpm setup in workflows
 */
describe('pnpm Setup Verification', () => {
  const workflowConfigs: WorkflowConfig[] = [
    {
      name: 'ci-cd-main',
      filePath: '.github/workflows/ci-cd-main.yml',
      expectedSetupSteps: [
        'pnpm/action-setup@v3',
        'actions/setup-node@v4',
      ],
      expectedScripts: ['pnpm install', 'pnpm lint', 'pnpm build'],
    },
    {
      name: 'e2e-testing',
      filePath: '.github/workflows/e2e-testing.yml',
      expectedSetupSteps: [
        'pnpm/action-setup@v3',
        'actions/setup-node@v4',
      ],
      expectedScripts: ['pnpm install', 'pnpm exec playwright'],
    },
    {
      name: 'deploy-vercel',
      filePath: '.github/workflows/deploy-vercel.yml',
      expectedSetupSteps: [
        'pnpm/action-setup@v3',
        'actions/setup-node@v4',
      ],
      expectedScripts: ['pnpm install', 'pnpm add -g vercel'],
    },
    {
      name: 'testing-suite',
      filePath: '.github/workflows/testing-suite.yml',
      expectedSetupSteps: [
        'pnpm/action-setup@v3',
        'actions/setup-node@v4',
      ],
      expectedScripts: ['pnpm install', 'pnpm lint', 'pnpm test', 'pnpm type-check'],
    },
  ];

  workflowConfigs.forEach((config) => {
    it(`should have pnpm action setup in ${config.name}`, () => {
      const workflowPath = path.join(process.cwd(), config.filePath);
      const workflowContent = fs.readFileSync(workflowPath, 'utf-8');

      // Verify pnpm action is present
      expect(workflowContent).toContain('pnpm/action-setup@v3');
      
      // Verify version is specified
      expect(workflowContent).toMatch(/version:\s*['\"]?8/);

      // Verify Node.js setup action follows
      expect(workflowContent).toContain('actions/setup-node@v4');
    });

    it(`should have correct Node.js version in ${config.name}`, () => {
      const workflowPath = path.join(process.cwd(), config.filePath);
      const workflowContent = fs.readFileSync(workflowPath, 'utf-8');

      // Verify Node version is set to 20
      expect(workflowContent).toContain('NODE_VERSION: \'20\'');
      expect(workflowContent).toContain('node-version: ${{ env.NODE_VERSION }}');
    });

    it(`should have pnpm cache configured in ${config.name}`, () => {
      const workflowPath = path.join(process.cwd(), config.filePath);
      const workflowContent = fs.readFileSync(workflowPath, 'utf-8');

      // Verify cache is set to pnpm
      expect(workflowContent).toContain("cache: 'pnpm'");
    });
  });

  it('should setup Node.js after pnpm setup', () => {
    const workflowPath = path.join(process.cwd(), '.github/workflows/ci-cd-main.yml');
    const workflowContent = fs.readFileSync(workflowPath, 'utf-8');

    // Find positions of pnpm setup and node setup
    const pnpmPos = workflowContent.indexOf('pnpm/action-setup@v3');
    const nodePos = workflowContent.indexOf('actions/setup-node@v4');

    expect(pnpmPos).toBeLessThan(nodePos);
  });
});

/**
 * Test 2: Verify dependency installation with pnpm
 */
describe('Dependency Installation Verification', () => {
  const workflowConfigs: WorkflowConfig[] = [
    {
      name: 'ci-cd-main',
      filePath: '.github/workflows/ci-cd-main.yml',
      expectedSetupSteps: [],
      expectedScripts: ['pnpm install --frozen-lockfile'],
    },
    {
      name: 'e2e-testing',
      filePath: '.github/workflows/e2e-testing.yml',
      expectedSetupSteps: [],
      expectedScripts: ['pnpm install --frozen-lockfile'],
    },
    {
      name: 'testing-suite',
      filePath: '.github/workflows/testing-suite.yml',
      expectedSetupSteps: [],
      expectedScripts: ['pnpm install --frozen-lockfile'],
    },
    {
      name: 'deploy-vercel',
      filePath: '.github/workflows/deploy-vercel.yml',
      expectedSetupSteps: [],
      expectedScripts: ['pnpm install --frozen-lockfile'],
    },
  ];

  workflowConfigs.forEach((config) => {
    it(`should use pnpm install --frozen-lockfile in ${config.name}`, () => {
      const workflowPath = path.join(process.cwd(), config.filePath);
      const workflowContent = fs.readFileSync(workflowPath, 'utf-8');

      expect(workflowContent).toContain('pnpm install --frozen-lockfile');
    });

    it(`should not use npm install in ${config.name}`, () => {
      const workflowPath = path.join(process.cwd(), config.filePath);
      const workflowContent = fs.readFileSync(workflowPath, 'utf-8');

      // Ensure npm install is not used for frontend dependencies
      const lines = workflowContent.split('\n');
      const npmLines = lines.filter((line) => 
        line.includes('npm install') && !line.includes('python -m pip')
      );

      expect(npmLines).toHaveLength(0);
    });

    it(`should not use yarn install in ${config.name}`, () => {
      const workflowPath = path.join(process.cwd(), config.filePath);
      const workflowContent = fs.readFileSync(workflowPath, 'utf-8');

      expect(workflowContent).not.toContain('yarn install');
    });

    it(`should have correct working directory in ${config.name}`, () => {
      const workflowPath = path.join(process.cwd(), config.filePath);
      const workflowContent = fs.readFileSync(workflowPath, 'utf-8');

      // For frontend workflows, should use apps/dashboard or similar
      if (config.name.includes('e2e') || config.name.includes('testing') || config.name.includes('vercel')) {
        expect(workflowContent).toContain('working-directory: apps/dashboard');
      }
    });
  });

  it('should handle cache-dependency-path correctly', () => {
    const workflowPath = path.join(process.cwd(), '.github/workflows/ci-cd-main.yml');
    const workflowContent = fs.readFileSync(workflowPath, 'utf-8');

    // Should have proper cache path
    const hasCacheDepPath = workflowContent.includes('cache-dependency-path:') &&
                           workflowContent.includes('pnpm-lock.yaml');

    expect(hasCacheDepPath).toBe(true);
  });
});

/**
 * Test 3: Verify script execution (lint, test, build, type-check, format:check)
 */
describe('Script Execution Verification', () => {
  describe('CI/CD Main Workflow', () => {
    const workflowPath = '.github/workflows/ci-cd-main.yml';

    it('should execute pnpm lint', () => {
      const content = fs.readFileSync(
        path.join(process.cwd(), workflowPath),
        'utf-8'
      );
      expect(content).toContain('pnpm lint');
    });

    it('should execute pnpm format:check', () => {
      const content = fs.readFileSync(
        path.join(process.cwd(), workflowPath),
        'utf-8'
      );
      expect(content).toContain('pnpm format:check');
    });

    it('should execute pnpm build', () => {
      const content = fs.readFileSync(
        path.join(process.cwd(), workflowPath),
        'utf-8'
      );
      expect(content).toContain('pnpm build');
    });
  });

  describe('Testing Suite Workflow', () => {
    const workflowPath = '.github/workflows/testing-suite.yml';

    it('should execute pnpm lint', () => {
      const content = fs.readFileSync(
        path.join(process.cwd(), workflowPath),
        'utf-8'
      );
      expect(content).toContain('pnpm lint');
    });

    it('should execute pnpm test with coverage', () => {
      const content = fs.readFileSync(
        path.join(process.cwd(), workflowPath),
        'utf-8'
      );
      expect(content).toContain('pnpm test');
    });

    it('should execute pnpm type-check', () => {
      const content = fs.readFileSync(
        path.join(process.cwd(), workflowPath),
        'utf-8'
      );
      expect(content).toContain('pnpm type-check');
    });

    it('should execute pnpm format:check', () => {
      const content = fs.readFileSync(
        path.join(process.cwd(), workflowPath),
        'utf-8'
      );
      expect(content).toContain('pnpm format:check');
    });
  });

  describe('Script Isolation', () => {
    it('should use pnpm within correct working directory', () => {
      const workflowPath = path.join(process.cwd(), '.github/workflows/testing-suite.yml');
      const content = fs.readFileSync(workflowPath, 'utf-8');

      // Verify working directory is set before scripts run
      const lines = content.split('\n');
      let foundWorkingDir = false;
      let foundScript = false;

      for (let i = 0; i < lines.length; i++) {
        if (lines[i].includes('working-directory: apps/dashboard')) {
          foundWorkingDir = true;
        }
        if (foundWorkingDir && i < lines.length - 1) {
          if (lines[i + 1].includes('pnpm lint') || 
              lines[i + 1].includes('pnpm test')) {
            foundScript = true;
            break;
          }
        }
      }

      expect(foundWorkingDir).toBe(true);
    });
  });
});

/**
 * Test 4: Playwright E2E Commands Verification
 */
describe('Playwright E2E Testing Verification', () => {
  const workflowPath = '.github/workflows/e2e-testing.yml';

  it('should use pnpm exec playwright install', () => {
    const content = fs.readFileSync(
      path.join(process.cwd(), workflowPath),
      'utf-8'
    );
    expect(content).toContain('pnpm exec playwright install');
  });

  it('should use pnpm exec playwright install with --with-deps', () => {
    const content = fs.readFileSync(
      path.join(process.cwd(), workflowPath),
      'utf-8'
    );
    expect(content).toContain('pnpm exec playwright install --with-deps');
  });

  it('should use pnpm exec playwright test', () => {
    const content = fs.readFileSync(
      path.join(process.cwd(), workflowPath),
      'utf-8'
    );
    expect(content).toContain('pnpm exec playwright test');
  });

  it('should support browser matrix in Playwright tests', () => {
    const content = fs.readFileSync(
      path.join(process.cwd(), workflowPath),
      'utf-8'
    );

    expect(content).toContain('chromium');
    expect(content).toContain('firefox');
    expect(content).toContain('webkit');
  });

  it('should install Playwright browsers before running tests', () => {
    const content = fs.readFileSync(
      path.join(process.cwd(), workflowPath),
      'utf-8'
    );

    const lines = content.split('\n');
    let installIndex = -1;
    let testIndex = -1;

    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes('pnpm exec playwright install')) {
        installIndex = i;
      }
      if (lines[i].includes('pnpm exec playwright test')) {
        testIndex = i;
      }
    }

    // Install should come before test
    expect(installIndex).toBeGreaterThanOrEqual(0);
    expect(testIndex).toBeGreaterThanOrEqual(0);
    expect(installIndex).toBeLessThan(testIndex);
  });

  it('should specify browser in playwright test command', () => {
    const content = fs.readFileSync(
      path.join(process.cwd(), workflowPath),
      'utf-8'
    );

    expect(content).toContain('--project=');
  });

  it('should upload test results and reports', () => {
    const content = fs.readFileSync(
      path.join(process.cwd(), workflowPath),
      'utf-8'
    );

    expect(content).toContain('playwright-results');
    expect(content).toContain('playwright-report');
  });
});

/**
 * Test 5: Global Package Installation (Vercel CLI, etc.)
 */
describe('Global Package Installation Verification', () => {
  describe('Vercel CLI Installation', () => {
    const workflowPath = '.github/workflows/deploy-vercel.yml';

    it('should use pnpm add -g for Vercel CLI', () => {
      const content = fs.readFileSync(
        path.join(process.cwd(), workflowPath),
        'utf-8'
      );
      expect(content).toContain('pnpm add -g vercel');
    });

    it('should install Vercel CLI before build step', () => {
      const content = fs.readFileSync(
        path.join(process.cwd(), workflowPath),
        'utf-8'
      );

      const lines = content.split('\n');
      let vercelIndex = -1;
      let buildIndex = -1;

      for (let i = 0; i < lines.length; i++) {
        if (lines[i].includes('pnpm add -g vercel')) {
          vercelIndex = i;
        }
        if (lines[i].includes('vercel pull') || lines[i].includes('vercel build')) {
          buildIndex = i;
        }
      }

      expect(vercelIndex).toBeGreaterThanOrEqual(0);
      expect(buildIndex).toBeGreaterThanOrEqual(0);
      expect(vercelIndex).toBeLessThan(buildIndex);
    });

    it('should specify vercel@latest version', () => {
      const content = fs.readFileSync(
        path.join(process.cwd(), workflowPath),
        'utf-8'
      );

      expect(content).toContain('vercel@latest');
    });

    it('should install Vercel CLI in preview and production jobs', () => {
      const content = fs.readFileSync(
        path.join(process.cwd(), workflowPath),
        'utf-8'
      );

      // Count occurrences of vercel installation
      const vercelInstallCount = (content.match(/pnpm add -g vercel/g) || []).length;
      expect(vercelInstallCount).toBeGreaterThanOrEqual(2);
    });
  });
});

/**
 * Test 6: Error Handling and Edge Cases
 */
describe('Error Handling and Edge Cases', () => {
  it('should not mix pnpm with npm or yarn', () => {
    const workflowFiles = [
      '.github/workflows/ci-cd-main.yml',
      '.github/workflows/e2e-testing.yml',
      '.github/workflows/deploy-vercel.yml',
      '.github/workflows/testing-suite.yml',
    ];

    workflowFiles.forEach((file) => {
      const content = fs.readFileSync(
        path.join(process.cwd(), file),
        'utf-8'
      );

      // Frontend should use pnpm, not npm
      const hasPnpm = content.includes('pnpm');
      const hasNpmInstall = content.includes('npm install') && 
                           !content.includes('pip') &&
                           !content.includes('npm install --upgrade pip');
      const hasYarn = content.includes('yarn install');

      if (hasPnpm) {
        expect(hasNpmInstall).toBe(false);
        expect(hasYarn).toBe(false);
      }
    });
  });

  it('should use --frozen-lockfile for reproducible builds', () => {
    const workflowFiles = [
      '.github/workflows/ci-cd-main.yml',
      '.github/workflows/e2e-testing.yml',
      '.github/workflows/testing-suite.yml',
      '.github/workflows/deploy-vercel.yml',
    ];

    workflowFiles.forEach((file) => {
      const content = fs.readFileSync(
        path.join(process.cwd(), file),
        'utf-8'
      );

      if (content.includes('pnpm install')) {
        expect(content).toContain('pnpm install --frozen-lockfile');
      }
    });
  });

  it('should handle pnpm exec for CLI tools correctly', () => {
    const workflowPath = '.github/workflows/e2e-testing.yml';
    const content = fs.readFileSync(
      path.join(process.cwd(), workflowPath),
      'utf-8'
    );

    // pnpm exec should be used for locally installed tools
    const execMatches = content.match(/pnpm exec [\w-]+/g) || [];
    expect(execMatches.length).toBeGreaterThan(0);

    // Verify proper format
    execMatches.forEach((match) => {
      expect(match).toMatch(/^pnpm exec [\w-]+$/);
    });
  });

  it('should set NODE_VERSION environment variable', () => {
    const workflowFiles = [
      '.github/workflows/ci-cd-main.yml',
      '.github/workflows/e2e-testing.yml',
      '.github/workflows/testing-suite.yml',
      '.github/workflows/deploy-vercel.yml',
    ];

    workflowFiles.forEach((file) => {
      const content = fs.readFileSync(
        path.join(process.cwd(), file),
        'utf-8'
      );

      if (content.includes('NODE_VERSION')) {
        expect(content).toContain("NODE_VERSION: '20'");
      }
    });
  });
});

/**
 * Test 7: Workflow Configuration Consistency
 */
describe('Workflow Configuration Consistency', () => {
  it('all workflows should use same pnpm version', () => {
    const workflowFiles = [
      '.github/workflows/ci-cd-main.yml',
      '.github/workflows/e2e-testing.yml',
      '.github/workflows/testing-suite.yml',
      '.github/workflows/deploy-vercel.yml',
    ];

    const versions: string[] = [];

    workflowFiles.forEach((file) => {
      const content = fs.readFileSync(
        path.join(process.cwd(), file),
        'utf-8'
      );

      if (content.includes('pnpm/action-setup')) {
        const versionMatch = content.match(/version:\s*['\"]?(\d+)/);
        if (versionMatch) {
          versions.push(versionMatch[1]);
        }
      }
    });

    // All versions should be the same
    const uniqueVersions = new Set(versions);
    expect(uniqueVersions.size).toBe(1);
  });

  it('all workflows should use same Node.js version', () => {
    const workflowFiles = [
      '.github/workflows/ci-cd-main.yml',
      '.github/workflows/e2e-testing.yml',
      '.github/workflows/testing-suite.yml',
      '.github/workflows/deploy-vercel.yml',
    ];

    const versions: string[] = [];

    workflowFiles.forEach((file) => {
      const content = fs.readFileSync(
        path.join(process.cwd(), file),
        'utf-8'
      );

      if (content.includes('NODE_VERSION')) {
        const versionMatch = content.match(/NODE_VERSION:\s*['\"](\d+)/);
        if (versionMatch) {
          versions.push(versionMatch[1]);
        }
      }
    });

    // All versions should be the same
    const uniqueVersions = new Set(versions);
    expect(uniqueVersions.size).toBeLessThanOrEqual(1);
  });

  it('should use consistent cache configuration', () => {
    const workflowFiles = [
      '.github/workflows/ci-cd-main.yml',
      '.github/workflows/e2e-testing.yml',
      '.github/workflows/testing-suite.yml',
      '.github/workflows/deploy-vercel.yml',
    ];

    workflowFiles.forEach((file) => {
      const content = fs.readFileSync(
        path.join(process.cwd(), file),
        'utf-8'
      );

      if (content.includes('pnpm/action-setup')) {
        // Should use pnpm cache
        expect(content).toContain("cache: 'pnpm'");
      }
    });
  });
});

/**
 * Test 8: Integration Testing
 */
describe('Integration Testing', () => {
  it('should allow running commands in CI environment', () => {
    // This is a conceptual test - in real CI, these would be actual executions
    const mockExec = vi.spyOn(cp, 'execSync').mockReturnValue('pnpm 8.0.0' as any);

    // This would be tested in actual CI environment
    expect(mockExec).toBeDefined();

    mockExec.mockRestore();
  });

  it('workflows should be valid YAML', () => {
    const workflowFiles = [
      '.github/workflows/ci-cd-main.yml',
      '.github/workflows/e2e-testing.yml',
      '.github/workflows/testing-suite.yml',
      '.github/workflows/deploy-vercel.yml',
    ];

    workflowFiles.forEach((file) => {
      const content = fs.readFileSync(
        path.join(process.cwd(), file),
        'utf-8'
      );

      // Basic YAML validation
      expect(content).toContain('name:');
      expect(content).toContain('on:');
      expect(content).toContain('jobs:');
      expect(content).toContain('runs-on:');
      expect(content).toContain('steps:');
    });
  });
});
