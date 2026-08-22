import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

import Login from './pages/Login';
import SuperAdminDashboard from './pages/SuperAdminDashboard';
import DistrictAdminDashboard from './pages/DistrictAdminDashboard';
import PhcDashboard from './pages/PhcDashboard';
import ChcDashboard from './pages/ChcDashboard';
import Unauthorized from './pages/Unauthorized';
import CentreDetails from './pages/CentreDetails';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/unauthorized" element={<Unauthorized />} />
          
          <Route element={<ProtectedRoute allowedRoles={['SUPER_ADMIN']} />}>
            <Route path="/super-admin" element={<SuperAdminDashboard />} />
          </Route>
          
          <Route element={<ProtectedRoute allowedRoles={['DISTRICT_ADMIN']} />}>
            <Route path="/district-admin" element={<DistrictAdminDashboard />} />
          </Route>
          
          <Route element={<ProtectedRoute allowedRoles={['PHC_STAFF']} />}>
            <Route path="/phc" element={<PhcDashboard />} />
          </Route>
          
          <Route element={<ProtectedRoute allowedRoles={['CHC_STAFF']} />}>
            <Route path="/chc" element={<ChcDashboard />} />
          </Route>

          <Route element={<ProtectedRoute allowedRoles={['SUPER_ADMIN', 'DISTRICT_ADMIN', 'PHC_STAFF', 'CHC_STAFF']} />}>
            <Route path="/centres/:centreId" element={<CentreDetails />} />
          </Route>

          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
