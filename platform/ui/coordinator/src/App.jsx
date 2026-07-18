import { useState, useEffect, useCallback, useRef } from 'react'
import SiteDirectory from './components/SiteDirectory'
import Scheduler from './components/Scheduler'
import ValidationHub from './components/ValidationHub'
import AuditTrail from './components/AuditTrail'

const API_BASE = import.meta.env.VITE_API_URL || 'http://coordinator:8000'
const API_KEY = import.meta.env.VITE_API_KEY || ''

const headers = { 'X-API-Key': API_KEY, 'Content-Type': 'application/json' }

function fetchJson(url, opts = {}) {
  return fetch(`${API_BASE}${url}`, {
    ...opts,
    headers: { ...headers, ...opts.headers },
  }).then((r) => {
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
    return r.json()
  })
}

export default function App() {
  const [clients, setClients] = useState([])
  const [rounds, setRounds] = useState([])
  const [auditPage, setAuditPage] = useState(1)
  const [auditData, setAuditData] = useState(null)
  const [auditFilters, setAuditFilters] = useState({})
  const [diceData, setDiceData] = useState([])
  const [epsilonData, setEpsilonData] = useState([])
  const [liveStatus, setLiveStatus] = useState({})
  const [wsConnected, setWsConnected] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)
  const wsRef = useRef(null)

  const poll = useCallback(() => {
    fetchJson('/clients').then(setClients).catch(() => {})
    fetchJson('/rounds').then(setRounds).catch(() => {})
    fetchJson(`/audit-log?page=${auditPage}&limit=50${auditFilters.event_type ? `&event_type=${auditFilters.event_type}` : ''}${auditFilters.round_id ? `&round_id=${auditFilters.round_id}` : ''}`)
      .then(setAuditData).catch(() => {})
    fetchJson('/metrics/dice').then(setDiceData).catch(() => {})
    fetchJson('/metrics/epsilon').then(setEpsilonData).catch(() => {})
  }, [auditPage, auditFilters])

  useEffect(() => {
    poll()
    const iv = setInterval(poll, 10000)
    return () => clearInterval(iv)
  }, [poll, refreshKey])

  useEffect(() => {
    const wsUrl = API_BASE.replace(/^http/, 'ws') + '/ws/live'
    let ws
    function connect() {
      ws = new WebSocket(wsUrl)
      ws.onopen = () => setWsConnected(true)
      ws.onmessage = (e) => {
        try { setLiveStatus(JSON.parse(e.data)) } catch {}
      }
      ws.onclose = () => {
        setWsConnected(false)
        setTimeout(connect, 3000)
      }
      ws.onerror = () => ws.close()
    }
    connect()
    wsRef.current = { close: () => ws?.close() }
    return () => ws?.close()
  }, [])

  const latestRound = rounds.length > 0 ? rounds.reduce((a, b) => a.round_id > b.round_id ? a : b) : null

  return (
    <div className="min-h-screen p-4 space-y-4">
      <header className="flex items-center justify-between border-b border-zinc-800 pb-3">
        <h1 className="text-xl font-bold tracking-tight">
          SDFL Central Coordinator
          <span className="ml-2 text-sm font-normal text-zinc-500">
            | Rounds: {latestRound?.round_id || 0}
          </span>
        </h1>
        <div className="flex items-center gap-2 text-sm">
          <span
            className={`inline-block w-3 h-3 rounded-full ${wsConnected ? 'bg-green-500 shadow-[0_0_8px_#22c55e]' : 'bg-red-500'}`}
          />
          <span className="text-zinc-400">
            {wsConnected ? 'Live' : 'Disconnected'}
          </span>
          <button
            onClick={() => setRefreshKey((k) => k + 1)}
            className="ml-4 px-3 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-xs cursor-pointer"
          >
            Refresh
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <div className="border border-zinc-800 rounded-lg bg-zinc-900/50 p-4">
          <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
            Site Directory
          </h2>
          <SiteDirectory clients={clients} liveStatus={liveStatus} />
        </div>

        <div className="border border-zinc-800 rounded-lg bg-zinc-900/50 p-4">
          <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
            Scheduler
          </h2>
          <Scheduler rounds={rounds} latestRound={latestRound} fetchJson={fetchJson} />
        </div>

        <div className="border border-zinc-800 rounded-lg bg-zinc-900/50 p-4">
          <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
            Validation Hub
          </h2>
          <ValidationHub diceData={diceData} epsilonData={epsilonData} fetchJson={fetchJson} />
        </div>

        <div className="border border-zinc-800 rounded-lg bg-zinc-900/50 p-4">
          <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
            Audit Trail
          </h2>
          <AuditTrail
            auditData={auditData}
            page={auditPage}
            onPageChange={setAuditPage}
            filters={auditFilters}
            onFilterChange={setAuditFilters}
          />
        </div>
      </div>
    </div>
  )
}
