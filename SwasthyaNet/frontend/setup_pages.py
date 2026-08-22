import os

src_dir = "src"

# Dashboards
roles = {
    "SuperAdminDashboard": "Super Admin",
    "DistrictAdminDashboard": "District Admin",
    "PhcDashboard": "PHC Staff",
    "ChcDashboard": "CHC Staff"
}

for component, title in roles.items():
    with open(os.path.join(src_dir, "pages", f"{component}.jsx"), "w") as f:
        f.write(f"""import React, {{ useContext }} from 'react';
import {{ AuthContext }} from '../context/AuthContext';
import {{ useNavigate }} from 'react-router-dom';

const {component} = () => {{
  const {{ user, logoutUser }} = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogout = () => {{
    logoutUser();
    navigate('/login');
  }};

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto bg-white rounded-xl shadow-md overflow-hidden p-6 border border-gray-200">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-gray-800">{title} Dashboard</h1>
          <button 
            onClick={{handleLogout}}
            className="px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
          >
            Logout
          </button>
        </div>
        <p className="text-gray-600 mb-4">Welcome back, {{user?.email}}!</p>
        <div className="bg-blue-50 p-4 rounded border border-blue-200">
          <h2 className="font-semibold text-blue-800">Your Role: {{user?.role}}</h2>
          <p className="text-sm text-blue-600 mt-1">
            This is a placeholder for the Phase 4 actual dashboard implementation.
          </p>
        </div>
      </div>
    </div>
  );
}};

export default {component};
""")

print("Created pages.")
