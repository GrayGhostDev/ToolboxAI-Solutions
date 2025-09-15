/**
 * Roblox-themed Dashboard Routes
 * 
 * Routes for the futuristic Roblox-themed dashboard
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import RobloxThemedDashboard from '../components/pages/RobloxThemedDashboard';

export const RobloxRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<RobloxThemedDashboard />} />
      <Route path="/dashboard" element={<RobloxThemedDashboard />} />
      <Route path="/space-station" element={<RobloxThemedDashboard />} />
    </Routes>
  );
};

export default RobloxRoutes;
