import os

src_dir = "src"

# src/pages/Unauthorized.jsx
with open(os.path.join(src_dir, "pages", "Unauthorized.jsx"), "w") as f:
    f.write("""import React from 'react';
import { Link } from 'react-router-dom';

const Unauthorized = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <h2 className="text-3xl font-extrabold text-red-600">Unauthorized</h2>
        <p className="mt-2 text-gray-600 mb-6">You do not have permission to view this page.</p>
        <Link to="/login" className="text-blue-600 hover:text-blue-500 font-medium">
          Return to Login
        </Link>
      </div>
    </div>
  );
};

export default Unauthorized;
""")

print("Created Unauthorized.jsx")
