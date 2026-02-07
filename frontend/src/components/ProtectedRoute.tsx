import React from 'react';
import { Navigate } from 'react-router-dom';

// ============================================
// ProtectedRoute - JWT Authentication Guard
// ============================================

interface ProtectedRouteProps {
    children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
    const token = localStorage.getItem('access_token');

    if (!token) {
        // Redirect to login if no token found
        return <Navigate to="/login" replace />;
    }

    return <>{children}</>;
};

export default ProtectedRoute;
