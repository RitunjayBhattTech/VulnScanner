import React from 'react';

interface Props {
  severity: string;
  size?: 'sm' | 'md' | 'lg';
}

const severityColors: Record<string, string> = {
  critical: 'bg-red-100 text-red-800 border-red-300',
  high: 'bg-orange-100 text-orange-800 border-orange-300',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  low: 'bg-blue-100 text-blue-800 border-blue-300',
  informational: 'bg-gray-100 text-gray-800 border-gray-300',
};

export default function SeverityBadge({ severity, size = 'md' }: Props) {
  const sizeClasses = {
    sm: 'px-1.5 py-0.5 text-xs',
    md: 'px-2 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base',
  };

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full border ${severityColors[severity.toLowerCase()] || severityColors.informational} ${sizeClasses[size]}`}
    >
      {severity.toUpperCase()}
    </span>
  );
}