import React from 'react';
import { Routes, Route, Link, Navigate } from 'react-router-dom';
import HomePage from './pages/HomePage';
import ScanPage from './pages/ScanPage';
import FindingsPage from './pages/FindingsPage';
import ReportPage from './pages/ReportPage';

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-indigo-900 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <Link to="/" className="text-xl font-bold tracking-tight">
                🔬 VulnAI Scanner
              </Link>
              <Link to="/" className="text-gray-300 hover:text-white px-3 py-2 text-sm">
                Dashboard
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/scans/:id" element={<ScanPage />} />
          <Route path="/findings" element={<FindingsPage />} />
          <Route path="/reports/:scanId" element={<ReportPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;