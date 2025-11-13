export type MockDataModule = typeof import('./mock-data');

let mockModulePromise: Promise<MockDataModule> | null = null;

export function loadMockDataModule(): Promise<MockDataModule> {
  if (!mockModulePromise) {
    mockModulePromise = import('./mock-data');
  }

  return mockModulePromise;
}

export function resetMockDataModuleCache(): void {
  mockModulePromise = null;
}
