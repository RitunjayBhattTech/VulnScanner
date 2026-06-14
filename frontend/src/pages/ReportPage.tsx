import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { downloadReport } from '../api/client';

export default function ReportPage() {
  const { scanId } = useParams<{ scanId: string }>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!scanId) return;

    const fetchReport = async () => {
      try {
        setLoading(true);
        const blob = await downloadReport(scanId);
        const url = window.URL.createObjectURL(blob);
        window.open(url, '_blank');
        window.URL.revokeObjectURL(url);
      } catch (err: any) {
        setError(err.message || 'Failed to download report');
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [scanId]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        <p className="ml-3 text-gray-500">Generating PDF report...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-4">{error}</p>
        <Link to={`/scans/${scanId}`} className="text-indigo-600 hover:text-indigo-800">
          Back to Scan
        </Link>
      </div>
    );
  }

  return (
    <div className="text-center py-12">
      <p className="text-gray-500">Report should have opened in a new tab.</p>
      <Link to={`/scans/${scanId}`} className="text-indigo-600 hover:text-indigo-800 mt-4 inline-block">
        Back to Scan
      </Link>
    </div>
  );
}