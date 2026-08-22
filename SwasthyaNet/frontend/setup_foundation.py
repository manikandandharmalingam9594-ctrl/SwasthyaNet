import os

src_dir = "src"
os.makedirs(os.path.join(src_dir, "pages"), exist_ok=True)
os.makedirs(os.path.join(src_dir, "components"), exist_ok=True)
os.makedirs(os.path.join(src_dir, "services"), exist_ok=True)
os.makedirs(os.path.join(src_dir, "context"), exist_ok=True)

# src/services/api.js
with open(os.path.join(src_dir, "services", "api.js"), "w") as f:
    f.write("""import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
""")

# src/services/authService.js
with open(os.path.join(src_dir, "services", "authService.js"), "w") as f:
    f.write("""import api from './api';

export const login = async (username, password) => {
  const params = new URLSearchParams();
  params.append('username', username);
  params.append('password', password);
  
  const response = await api.post('/auth/login', params, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  });
  return response.data;
};
""")

# src/context/AuthContext.jsx
with open(os.path.join(src_dir, "context", "AuthContext.jsx"), "w") as f:
    f.write("""import React, { createContext, useState, useEffect } from 'react';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');
    
    if (token && storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  const loginUser = (token, userData) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
  };

  const logoutUser = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loginUser, logoutUser, loading }}>
      {children}
    </AuthContext.Provider>
  );
};
""")

# src/components/ProtectedRoute.jsx
with open(os.path.join(src_dir, "components", "ProtectedRoute.jsx"), "w") as f:
    f.write("""import { useContext } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

const ProtectedRoute = ({ allowedRoles }) => {
  const { user, loading } = useContext(AuthContext);

  if (loading) return <div>Loading...</div>;

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <Outlet />;
};

export default ProtectedRoute;
""")

print("Created foundational files.")
