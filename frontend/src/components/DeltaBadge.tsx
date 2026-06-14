import React from 'react';

interface Props {
  deltaStatus: string | null | undefined;
}

const deltaConfig: Record<string, { label: string; classes: string }> = {
  new: { label: 'NEW', classes: 'bg-red-100 text-red-700 border-red-300' },
  fixed: { label: 'FIXED', classes: 'bg-green-100 text-green-700 border-green-300' },
  regressed: { label: 'REGRESSED', classes: 'bg-orange-100 text-orange-700 border-orange-300' },
  existing: { label: 'EXISTING', classes: 'bg-gray-100 text-gray-600 border-gray-200' },
};

export default function DeltaBadge({ deltaStatus }: Props) {
  if (!deltaStatus) return null;

  const config = deltaConfig[deltaStatus.toLowerCase()];
  if (!config) return null;

  return (
    <span className={`inline-flex items-center px-2 py-0.5 text-xs font-medium rounded border ${config.classes}`}>
      {config.label}
    </span>
  );
}