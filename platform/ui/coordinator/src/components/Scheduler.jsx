import { useState, useEffect } from 'react'
import { formatTimestamp } from '../lib/utils'

export default function Scheduler({ rounds, latestRound, fetchJson }) {
  const [windowSec, setWindowSec] = useState(300)
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState('')
  const [countdown, setCountdown] = useState(null)

  const isOpen = latestRound?.status === 'OPEN'

  useEffect(() => {
    if (!isOpen || !latestRound?.expiry_timestamp) {
      setCountdown(null)
      return
    }
    const tick = () => {
      const rem = Math.max(0, Math.floor((new Date(latestRound.expiry_timestamp).getTime() - Date.now()) / 1000))
      setCountdown(rem)
      if (rem <= 0) return
    }
    tick()
    const iv = setInterval(tick, 1000)
    return () => clearInterval(iv)
  }, [isOpen, latestRound?.expiry_timestamp])

  async function startRound() {
    setStarting(true)
    setError('')
    try {
      await fetchJson('/rounds/start', {
        method: 'POST',
        body: JSON.stringify({ window_seconds: windowSec, num_rounds: 1 }),
      })
    } catch (e) {
      setError(e.message)
    }
    setStarting(false)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between p-3 rounded bg-zinc-800/50">
        <div>
          <span className="text-xs text-zinc-500">Current Round</span>
          <p className="text-lg font-semibold">
            {latestRound ? `#${latestRound.round_id}` : 'None'}
          </p>
        </div>
        <div className="text-right">
          <span className="text-xs text-zinc-500">Status</span>
          <p>
            {isOpen ? (
              <span className="inline-flex items-center gap-1 text-green-500">
                <span className="w-2 h-2 rounded-full bg-green-500" /> OPEN
              </span>
            ) : latestRound ? (
              <span className="text-zinc-400">{latestRound.status}</span>
            ) : (
              <span className="text-zinc-600">—</span>
            )}
          </p>
        </div>
      </div>

      {countdown !== null && (
        <div className="text-center">
          <span className="text-xs text-zinc-500">Expires in</span>
          <p className="text-2xl font-mono font-bold text-yellow-500">
            {Math.floor(countdown / 60)}:{String(countdown % 60).padStart(2, '0')}
          </p>
        </div>
      )}

      <div className="flex items-end gap-3">
        <div className="flex-1">
          <label className="block text-xs text-zinc-500 mb-1">Window (seconds)</label>
          <input
            type="number"
            min={60}
            max={7200}
            value={windowSec}
            onChange={(e) => setWindowSec(Number(e.target.value))}
            disabled={isOpen}
            className="w-full px-3 py-2 rounded bg-zinc-800 border border-zinc-700 text-sm disabled:opacity-50"
          />
        </div>
        <button
          onClick={startRound}
          disabled={isOpen || starting}
          className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium cursor-pointer"
        >
          {starting ? 'Starting…' : isOpen ? 'Round in Progress' : 'Start Round'}
        </button>
      </div>

      {error && <p className="text-xs text-red-400">{error}</p>}

      <div>
        <span className="text-xs text-zinc-500 block mb-1">Round History</span>
        {rounds.length === 0 ? (
          <p className="text-xs text-zinc-700 italic">No rounds yet</p>
        ) : (
          <div className="overflow-x-auto max-h-48 overflow-y-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-zinc-500 border-b border-zinc-800">
                  <th className="pb-1 pr-2 font-medium">Round</th>
                  <th className="pb-1 pr-2 font-medium">Status</th>
                  <th className="pb-1 pr-2 font-medium">Window</th>
                  <th className="pb-1 font-medium">Created</th>
                </tr>
              </thead>
              <tbody>
                {[...rounds].reverse().map((r) => (
                  <tr key={r.round_id} className="border-b border-zinc-800/30">
                    <td className="py-1 pr-2 font-mono">#{r.round_id}</td>
                    <td className="py-1 pr-2">{r.status}</td>
                    <td className="py-1 pr-2 text-zinc-400">{r.window_seconds}s</td>
                    <td className="py-1 text-zinc-400">{formatTimestamp(r.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
