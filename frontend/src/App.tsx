import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AuthPage from './components/AuthPage';
import BooksDashboard from './components/BooksDashboard';
import UploadDashboard from './components/UploadDashboard';
import TranscriptUploadDashboard from './components/TranscriptUploadDashboard';
import BookStructure from './components/BookStructure';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<AuthPage />} />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <BooksDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/upload/:bookId"
          element={
            <ProtectedRoute>
              <UploadDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/upload-transcript/:bookId"
          element={
            <ProtectedRoute>
              <TranscriptUploadDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/books/:bookId/structure"
          element={
            <ProtectedRoute>
              <BookStructure />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
