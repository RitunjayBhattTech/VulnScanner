import React from 'react';
import ScanForm from '../components/ScanForm';
import Dashboard from '../components/Dashboard';
import ScanList from '../components/ScanList';

export default function HomePage() {
  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <ScanForm />
        <Dashboard />
      </div>
      <ScanList />
    </div>
  );
}