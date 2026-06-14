import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreateScan } from '../hooks/useScans';

const SCAN_TYPE_OPTIONS = [
  { value: 'port', label: 'Port Scan (nmap)' },
  { value: 'web', label: 'Web Crawl + Nuclei' },
  { value: 'header', label: 'Header Analysis' },
  { value: 'ssl', label: 'SSL Check' },
  { value: 'semgrep', label: 'Semgrep (SAST - local dirs only)' },
];

export default function ScanForm() {
  const navigate = useNavigate();
  const createScan = useCreateScan();

  const [target, setTarget] = useState('');
  const [scopeInput, setScopeInput] = useState('');
  const [scanTypes, setScanTypes] = useState<string[]>(['port', 'web', 'nuclei', 'header', 'ssl']);
  const [authorisationConfirmed, setAuthorisationConfirmed] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!authorisationConfirmed) {
      setError('You must confirm authorisation before running a scan.');
      return;
    }

    const scope = scopeInput.split('\n').filter(s => s.trim()).map(s => s.trim());

    if (scope.length === 0) {
      setError('Scope must not be empty. Add at least one host, CIDR, or domain.');
      return;
    }

    try {
      const result = await createScan.mutateAsync({
        target,
        scope,
        scan_types: scanTypes,
        authorisation_confirmed: true,
      });
      navigate(`/scans/${result.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to create scan');
    }
  };

  const toggleScanType = (value: string) => {
    setScanTypes(prev =>
      prev.includes(value) ? prev.filter(v => v !== value) : [...prev, value]
    );
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 space-y-6">
      <h2 className="text-lg font-semibold text-gray-900">New Security Scan</h2>

      {/* Target */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Target URL/IP
        </label>
        <input
          type="text"
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          placeholder="https://example.com or 10.0.0.1"
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-sm"
          required
        />
      </div>

      {/* Scope */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Scope (one per line - hosts, CIDRs, or domains)
        </label>
        <textarea
          value={scopeInput}
          onChange={(e) => setScopeInput(e.target.value)}
          placeholder="example.com&#10;10.0.0.0/8&#10;192.168.1.0/24"
          rows={4}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-sm"
          required
        />
      </div>

      {/* Scan Types */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Scan Types
        </label>
        <div className="space-y-2">
          {SCAN_TYPE_OPTIONS.map(option => (
            <label key={option.value} className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={scanTypes.includes(option.value)}
                onChange={() => toggleScanType(option.value)}
                className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              <span className="text-sm text-gray-700">{option.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Authorisation Confirmation */}
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <label className="flex items-start space-x-3">
          <input
            type="checkbox"
            checked={authorisationConfirmed}
            onChange={(e) => setAuthorisationConfirmed(e.target.checked)}
            className="mt-1 rounded border-red-300 text-red-600 focus:ring-red-500"
          />
          <span className="text-sm text-red-800">
            <strong>Legal Acknowledgement:</strong> I confirm I have written authorisation from the system owner to perform
            security testing on the specified target. I understand that unauthorised scanning may be illegal.
          </span>
        </label>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-100 border border-red-300 text-red-700 px-4 py-3 rounded text-sm">
          {error}
        </div>
      )}

      {/* Submit */}
      <button
        type="submit"
        disabled={!authorisationConfirmed || createScan.isPending}
        className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm font-medium transition-colors"
      >
        {createScan.isPending ? 'Creating Scan...' : 'Start Scan'}
      </button>
    </form>
  );
}