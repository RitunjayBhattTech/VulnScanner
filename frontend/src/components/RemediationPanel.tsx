import React from 'react';
import ReactMarkdown from 'react-markdown';

interface Props {
  remediation: string;
}

export default function RemediationPanel({ remediation }: Props) {
  const [expanded, setExpanded] = React.useState(false);

  if (!remediation) return null;

  return (
    <div className="border border-green-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-2 bg-green-50 hover:bg-green-100 transition-colors"
      >
        <span className="text-sm font-medium text-green-800">AI-Generated Remediation</span>
        <svg className={`w-4 h-4 text-green-600 transform transition-transform ${expanded ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {expanded && (
        <div className="p-4 bg-white">
          <ReactMarkdown className="prose prose-sm max-w-none text-gray-700">
            {remediation}
          </ReactMarkdown>
        </div>
      )}
    </div>
  );
}