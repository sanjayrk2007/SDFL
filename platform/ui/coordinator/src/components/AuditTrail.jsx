import { formatTimestamp } from '../lib/utils'

const EVENT_COLORS = {
  round_open: 'text-blue-400',
  round_close: 'text-zinc-400',
  key_destroyed: 'text-red-400',
  model_rollback: 'text-orange-400',
}

const EVENT_LABELS = {
  round_open: 'Round Open',
  round_close: 'Round Close',
  key_destroyed: 'Key Destroyed',
  model_rollback: 'Model Rollback',
}

export default function AuditTrail({ auditData, page, onPageChange, filters, onFilterChange }) {
  const entries = auditData?.entries || []
  const total = auditData?.total || 0
  const limit = auditData?.limit || 50
  const totalPages = Math.max(1, Math.ceil(total / limit))

  function exportCsv() {
    if (entries.length === 0) return
    const header = 'id,event_type,round_id,timestamp,details\n'
    const rows = entries
      .map((e) =>
        [
          e.id,
          e.event_type,
          e.round_id ?? '',
          e.timestamp || '',
          (e.details ? JSON.stringify(e.details).replace(/"/g, '""') : ''),
        ].join(',')
      )
      .join('\n')
    const blob = new Blob([header + rows], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `audit_log_page${page}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-3">
        <select
          value={filters.event_type || ''}
          onChange={(e) => onFilterChange({ ...filters, event_type: e.target.value || undefined, page: 1 })}
          className="px-2 py-1.5 rounded bg-zinc-800 border border-zinc-700 text-xs"
        >
          <option value="">All Events</option>
          {Object.entries(EVENT_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>

        <input
          type="number"
          placeholder="Round ID"
          value={filters.round_id ?? ''}
          onChange={(e) => onFilterChange({ ...filters, round_id: e.target.value ? Number(e.target.value) : undefined })}
          className="w-20 px-2 py-1.5 rounded bg-zinc-800 border border-zinc-700 text-xs"
        />

        <button
          onClick={exportCsv}
          disabled={entries.length === 0}
          className="px-3 py-1.5 rounded bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 text-xs cursor-pointer"
        >
          Export CSV
        </button>
      </div>

      {entries.length === 0 ? (
        <p className="text-xs text-zinc-700 italic">No audit events</p>
      ) : (
        <div className="overflow-x-auto max-h-64 overflow-y-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-zinc-500 border-b border-zinc-800">
                <th className="pb-1 pr-2 font-medium">ID</th>
                <th className="pb-1 pr-2 font-medium">Event</th>
                <th className="pb-1 pr-2 font-medium">Round</th>
                <th className="pb-1 font-medium">Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => (
                <tr key={e.id} className="border-b border-zinc-800/30">
                  <td className="py-1 pr-2 text-zinc-500">{e.id}</td>
                  <td className={`py-1 pr-2 font-medium ${EVENT_COLORS[e.event_type] || 'text-zinc-300'}`}>
                    {EVENT_LABELS[e.event_type] || e.event_type}
                  </td>
                  <td className="py-1 pr-2 text-zinc-400">{e.round_id ?? '—'}</td>
                  <td className="py-1 text-zinc-400">{formatTimestamp(e.timestamp)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-between text-xs text-zinc-500">
          <span>{total} total entries</span>
          <div className="flex items-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => onPageChange(page - 1)}
              className="px-2 py-1 rounded bg-zinc-800 hover:bg-zinc-700 disabled:opacity-30 cursor-pointer"
            >
              Prev
            </button>
            <span>
              {page} / {totalPages}
            </span>
            <button
              disabled={page >= totalPages}
              onClick={() => onPageChange(page + 1)}
              className="px-2 py-1 rounded bg-zinc-800 hover:bg-zinc-700 disabled:opacity-30 cursor-pointer"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
