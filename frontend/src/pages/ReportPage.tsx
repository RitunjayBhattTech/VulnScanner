import { useParams } from 'react-router-dom'
import { reportApi } from '../api/client'

export default function ReportPage() {
  const { scanId } = useParams<{ scanId: string }>()

  if (!scanId) return (
    <div className="text-red-400 text-center py-16">No scan ID provided</div>
  )

  const pdfUrl = reportApi.getPdfUrl(scanId)

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">PDF Report</h1>
      <div className="bg-[#0f1629] border border-[#1e2a45] rounded-xl p-6 text-center space-y-4">
        <div className="text-slate-400 text-sm">Download the PDF security report for this scan.</div>
        <a
          href={pdfUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg transition-colors"
        >
          ↓ Download PDF Report
        </a>
      </div>
    </div>
  )
}