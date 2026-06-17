import { useState, useEffect } from 'react'
import { useParams, Link, useSearchParams } from 'react-router-dom'
import { useScan } from '../hooks/useScans'
import { useFindings } from '../hooks/useFindings'
import FindingCard from './FindingCard'
import { reportApi } from '../api/client'

const PHASES = [
  { time: 0, label: 'Initialising scan...' },
  { time: 10, label: 'Running port discovery...' },
  { time: 30, label: 'Crawling web surface...' },
  { time: 60, label: 'Running vulnerability detection...' },
  { time: 120, label: 'AI is analysing findings...' },
]

export default function ScanDetail() {
  const { id } = useParams<{ id: string }>()
  const [searchParams] = useSearchParams()
  const isDemo = searchParams.get('demo') === 'true'
  const { scan, loading: scanLoading } = useScan(id)
  const { findings, loading: findingsLoading } = useFindings(id)
  const [elapsed, setElapsed] = useState(0)

  const currentStatus = scan?.status || 'pending'

  useEffect(() => {
    if (currentStatus === 'running' || currentStatus === 'pending') {
      const interval = setInterval(() => {
        setElapsed((prev) => prev + 3)
      }, 3000)
      return () => clearInterval(interval)
    }
  }, [currentStatus])

  const getCurrentPhase = () => {
    let phase = PHASES[0]
    for (const p of PHASES) {
      if (elapsed >= p.time) {
        phase = p
      }
    }
    return phase
  }

  if (scanLoading && !isDemo) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    )
  }

  if (!scan && !isDemo) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Scan not found</p>
        <Link to="/" className="text-indigo-600 hover:text-indigo-800 mt-4 inline-block">Back to Dashboard</Link>
      </div>
    )
  }

  const displayTarget = isDemo ? 'http://demo-target.vulnai.local' : (scan?.target || '')
  const displayScan = isDemo ? {
    id: 'demo-scan-00000000-0000-0000-0000-000000000001',
    target: 'http://demo-target.vulnai.local',
    scope: ['demo-target.vulnai.local'],
    status: 'completed' as const,
    scan_types: ['port', 'web', 'nuclei', 'headers', 'ssl'],
    summary: 'This security assessment identified 8 findings across the target system, including 3 critical vulnerabilities requiring immediate remediation.',
    total_findings: 8,
    critical_count: 3,
    high_count: 3,
    medium_count: 2,
    low_count: 0,
    info_count: 0,
    created_at: new Date().toISOString(),
  } : scan

  const pdfUrl = scan?.id ? reportApi.getPdfUrl(scan.id) : ''

  return (
    <div className="space-y-6">
      {/* Demo mode banner */}
      {isDemo && (
        <div className="bg-yellow-50 border-2 border-yellow-400 rounded-lg p-4">
          <div className="flex items-center">
            <span className="text-xl mr-2">⚠️</span>
            <p className="text-yellow-800 font-medium">
              DEMO MODE — This is simulated data for demonstration purposes
            </p>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link to="/" className="text-sm text-indigo-600 hover:text-indigo-800">&larr; Back</Link>
          <h1 className="text-2xl font-bold text-gray-900 mt-1">{displayTarget}</h1>
        </div>
        <div className="flex items-center space-x-3">
          {(currentStatus === 'running' || currentStatus === 'pending') && !isDemo && (
            <div className="flex items-center space-x-3 text-blue-600">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
              <span className="text-sm font-medium">{getCurrentPhase().label}</span>
            </div>
          )}
          {currentStatus === 'completed' && displayScan && (
            <a
              href={pdfUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-green-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-green-700"
            >
              Download PDF Report
            </a>
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
            <p className="text-sm font-medium mt-1">{displayScan?.scan_types?.join(', ') || ''}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase">Scope</p>
            <p className="text-sm font-medium mt-1">{displayScan?.scope?.join(', ') || ''}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase">Created</p>
            <p className="text-sm font-medium mt-1">{displayScan?.created_at ? new Date(displayScan.created_at).toLocaleString() : ''}</p>
          </div>
        </div>
      </div>

      {/* Summary (if available) */}
      {displayScan?.summary && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">Executive Summary</h2>
          <p className="text-sm text-gray-700">{displayScan.summary}</p>
        </div>
      )}

      {/* Severity Counts */}
      {displayScan && (
        <div className="grid grid-cols-5 gap-3">
          {[
            { label: 'Critical', value: (displayScan as any).critical_count, color: 'text-red-600', bg: 'bg-red-50' },
            { label: 'High', value: (displayScan as any).high_count, color: 'text-orange-600', bg: 'bg-orange-50' },
            { label: 'Medium', value: (displayScan as any).medium_count, color: 'text-yellow-600', bg: 'bg-yellow-50' },
            { label: 'Low', value: (displayScan as any).low_count, color: 'text-blue-600', bg: 'bg-blue-50' },
            { label: 'Info', value: (displayScan as any).info_count, color: 'text-gray-600', bg: 'bg-gray-50' },
          ].map((item) => (
            <div key={item.label} className={`${item.bg} rounded-lg p-3 text-center`}>
              <p className={`text-2xl font-bold ${item.color}`}>{item.value}</p>
              <p className="text-xs text-gray-500 mt-1">{item.label}</p>
            </div>
          ))}
        </div>
      )}

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
              <FindingCard key={finding.id} finding={finding as any} />
            ))
          )}
        </div>
      </div>
    </div>
  )
}