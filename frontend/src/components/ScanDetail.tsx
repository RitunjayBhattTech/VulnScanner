import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useScan, useScanStatus, useDownloadReport } from '../hooks/useScans';
import { useFindings } from '../hooks/useFindings';
import FindingCard from './FindingCard';

export default function ScanDetail() {
  const { id } = useParams<{ id: string }>();
  const { data: scan, isLoading: scanLoading } = useScan(id);
  const { data: status } = useScanStatus(id, scan?.status === 'running' || scan?.status === 'pending');
  const { data: findings, isLoading: findingsLoading } = useFindings(id);
  const downloadReport = useDownloadReport();

  const currentStatus = status?.status || scan?.status || 'pending';

  if (scanLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (!scan) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Scan not found</p>
        <Link to="/" className="text-indigo-600 hover:text-indigo-800 mt-4 inline-block">Back to Dashboard</Link>
      </div>
    );
  }

  const handleDownloadReport = async () => {
    try {
      const blob = await downloadReport.mutateAsync(scan.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `vulnai_report_${scan.id.slice(0, 8)}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Failed to download report:', err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link to="/" className="text-sm text-indigo-600 hover:text-indigo-800">&larr; Back</Link>
          <h1 className="text-2xl font-bold text-gray-900 mt-1">{scan.target}</h1>
        </div>
        <div className="flex items-center space-x-3">
          {(currentStatus === 'running' || currentStatus === 'pending') && (
            <div className="flex items-center space-x-2 text-blue-600">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
              <span className="text-sm font-medium">{currentStatus.toUpperCase()}</span>
            </div>
          )}
          {currentStatus === 'completed' && (
            <button
              onClick={handleDownloadReport}
              disabled={downloadReport.isPending}
              className="bg-green-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-green-700 disabled:bg-gray-400"
            >
              {downloadReport.isPending ? 'Generating...' : 'Download PDF Report'}
            </button>
          )}
        </div>
      </div>

      {/* Scan Info */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-xs text-gray-500 uppercase">Status</p>
            <p className={`text-sm font-medium mt-1 ${
              currentStatus === 'completed' ? 'text-green-600' :
              currentStatus === 'running' ? 'text-blue-600' :
              currentStatus === 'failed' ? 'text-red-600' :
              'text-gray-600'
            }`}>{currentStatus}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase">Scan Types</p>
            <p className="text-sm font-medium mt-1">{scan.scan_types?.join(', ')}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase">Scope</p>
            <p className="text-sm font-medium mt-1">{scan.scope?.join(', ')}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase">Created</p>
            <p className="text-sm font-medium mt-1">{new Date(scan.created_at).toLocaleString()}</p>
          </div>
        </div>
      </div>

      {/* Summary (if available) */}
      {scan.summary && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">Executive Summary</h2>
          <p className="text-sm text-gray-700">{scan.summary}</p>
        </div>
      )}

      {/* Severity Counts */}
      <div className="grid grid-cols-5 gap-3">
        {[
          { label: 'Critical', value: scan.critical_count, color: 'text-red-600', bg: 'bg-red-50' },
          { label: 'High', value: scan.high_count, color: 'text-orange-600', bg: 'bg-orange-50' },
          { label: 'Medium', value: scan.medium_count, color: 'text-yellow-600', bg: 'bg-yellow-50' },
          { label: 'Low', value: scan.low_count, color: 'text-blue-600', bg: 'bg-blue-50' },
          { label: 'Info', value: scan.info_count, color: 'text-gray-600', bg: 'bg-gray-50' },
        ].map((item) => (
          <div key={item.label} className={`${item.bg} rounded-lg p-3 text-center`}>
            <p className={`text-2xl font-bold ${item.color}`}>{item.value}</p>
            <p className="text-xs text-gray-500 mt-1">{item.label}</p>
          </div>
        ))}
      </div>

      {/* Findings */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Findings ({findings?.length || 0})
        </h2>
        <div className="space-y-2">
          {findingsLoading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600"></div>
            </div>
          ) : findings?.length === 0 ? (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center text-gray-500">
              No findings yet. The scan is still in progress.
            </div>
          ) : (
            findings?.map((finding) => (
              <FindingCard key={finding.id} finding={finding} />
            ))
          )}
        </div>
      </div>
    </div>
  );
}