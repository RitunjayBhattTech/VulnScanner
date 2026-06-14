import React from 'react';
import { Link } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useScans } from '../hooks/useScans';
import SeverityBadge from './SeverityBadge';

export default function Dashboard() {
  const { data: scansData, isLoading } = useScans({ page: 1 });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  const scans = scansData?.items || [];
  const totals = scans.reduce(
    (acc, s) => ({
      total: acc.total + s.total_findings,
      critical: acc.critical + s.critical_count,
      high: acc.high + s.high_count,
      medium: acc.medium + s.medium_count,
      low: acc.low + s.low_count,
    }),
    { total: 0, critical: 0, high: 0, medium: 0, low: 0 },
  );

  const chartData = [
    { name: 'Critical', count: totals.critical, fill: '#dc2626' },
    { name: 'High', count: totals.high, fill: '#ea580c' },
    { name: 'Medium', count: totals.medium, fill: '#ca8a04' },
    { name: 'Low', count: totals.low, fill: '#2563eb' },
  ];

  const recentScans = scans.slice(0, 5);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Total Scans</p>
          <p className="text-2xl font-bold text-gray-900">{scans.length}</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Total Findings</p>
          <p className="text-2xl font-bold text-gray-900">{totals.total}</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Critical</p>
          <p className="text-2xl font-bold text-red-600">{totals.critical}</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500">High</p>
          <p className="text-2xl font-bold text-orange-600">{totals.high}</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Medium</p>
          <p className="text-2xl font-bold text-yellow-600">{totals.medium}</p>
        </div>
      </div>

      {/* Chart */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Findings by Severity</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="count" name="Count" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Recent Scans */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-4 py-3 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Recent Scans</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {recentScans.map((scan) => (
            <Link
              key={scan.id}
              to={`/scans/${scan.id}`}
              className="block px-4 py-3 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-indigo-600 truncate">{scan.target}</p>
                  <p className="text-xs text-gray-500">
                    {new Date(scan.created_at).toLocaleString()} | {scan.status.toUpperCase()}
                  </p>
                </div>
                <div className="flex items-center space-x-2 ml-4">
                  <span className="text-xs text-gray-500">{scan.total_findings} findings</span>
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                    scan.status === 'completed' ? 'bg-green-100 text-green-700' :
                    scan.status === 'running' ? 'bg-blue-100 text-blue-700' :
                    scan.status === 'failed' ? 'bg-red-100 text-red-700' :
                    'bg-gray-100 text-gray-700'
                  }`}>
                    {scan.status}
                  </span>
                </div>
              </div>
            </Link>
          ))}
          {recentScans.length === 0 && (
            <div className="px-4 py-8 text-center text-gray-500">
              No scans yet. Create one to get started.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}