import React from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useFindings } from '../hooks/useFindings';
import FindingCard from '../components/FindingCard';

export default function FindingsPage() {
  const [searchParams] = useSearchParams();
  const scanId = searchParams.get('scan_id') || '';

  const { data: findings, isLoading } = useFindings(scanId || undefined);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Findings</h1>
        {scanId && (
          <Link
            to={`/scans/${scanId}`}
            className="text-sm text-indigo-600 hover:text-indigo-800"
          >
            View Scan &rarr;
          </Link>
        )}
      </div>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600"></div>
        </div>
      ) : findings && findings.length > 0 ? (
        <div className="space-y-2">
          {findings.map((finding) => (
            <FindingCard key={finding.id} finding={finding} />
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center text-gray-500">
          {scanId ? 'No findings for this scan.' : 'Select a scan to view findings.'}
        </div>
      )}
    </div>
  );
}