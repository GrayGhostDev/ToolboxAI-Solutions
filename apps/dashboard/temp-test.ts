// WebSocket/HMR Test File
// Updated: 2025-10-05T11:38:00.000Z
// This file tests that Hot Module Replacement is working correctly

export function testHMRFunctionality() {
  console.log('HMR test function called - WebSocket working!');
  return {
    timestamp: new Date().toISOString(),
    message: 'Hot Module Replacement is functional',
    testCount: 2
  };
}

export { StudentManagement } from './src/components/StudentManagement/StudentManagement.tsx';
