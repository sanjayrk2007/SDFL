import { useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceDot, Label,
} from 'recharts'

export default function ValidationHub({ diceData, epsilonData, fetchJson }) {
  const [rollbackRid, setRollbackRid] = useState(null)
  const [rollbackMsg, setRollbackMsg] = useState('')

  const bestDice = diceData.length > 0
    ? diceData.reduce((a, b) => (a.val_dice > b.val_dice ? a : b))
    : null

  async function confirmRollback() {
    if (rollbackRid === null) return
    setRollbackMsg('')
    try {
      const res = await fetchJson(`/rollback?round_id=${rollbackRid}`, { method: 'POST' })
      setRollbackMsg(`✅ Rolled back to Round ${res.round}`)
    } catch (e) {
      setRollbackMsg(`❌ ${e.message}`)
    }
    setRollbackRid(null)
  }

  return (
    <div className="space-y-4">
      <div>
        <span className="text-xs text-zinc-500 block mb-1">Validation Dice per Round</span>
        {diceData.length === 0 ? (
          <p className="text-xs text-zinc-700 italic">No data yet</p>
        ) : (
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={diceData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
              <XAxis dataKey="round_id" stroke="#71717a" tick={{ fontSize: 10 }} />
              <YAxis domain={[0, 1]} stroke="#71717a" tick={{ fontSize: 10 }} />
              <Tooltip
                contentStyle={{ background: '#18181b', border: '1px solid #27272a', fontSize: 12 }}
              />
              <Line type="monotone" dataKey="val_dice" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} />
              {bestDice && (
                <ReferenceDot x={bestDice.round_id} y={bestDice.val_dice} r={6} fill="#22c55e" stroke="#000">
                  <Label value={`★ ${bestDice.val_dice.toFixed(3)}`} position="top" fill="#22c55e" fontSize={10} />
                </ReferenceDot>
              )}
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      <div>
        <span className="text-xs text-zinc-500 block mb-1">Epsilon per Round</span>
        {epsilonData.length === 0 ? (
          <p className="text-xs text-zinc-700 italic">No data yet</p>
        ) : (
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={epsilonData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
              <XAxis dataKey="round_id" stroke="#71717a" tick={{ fontSize: 10 }} />
              <YAxis stroke="#71717a" tick={{ fontSize: 10 }} />
              <Tooltip
                contentStyle={{ background: '#18181b', border: '1px solid #27272a', fontSize: 12 }}
              />
              <Line type="monotone" dataKey="epsilon" stroke="#f59e0b" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      <div>
        <span className="text-xs text-zinc-500 block mb-1">Rollback</span>
        {diceData.length === 0 ? (
          <p className="text-xs text-zinc-700 italic">No rounds to rollback</p>
        ) : (
          <div className="overflow-x-auto max-h-40 overflow-y-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-zinc-500 border-b border-zinc-800">
                  <th className="pb-1 pr-2 font-medium">Round</th>
                  <th className="pb-1 pr-2 font-medium">Dice</th>
                  <th className="pb-1 pr-2 font-medium">IoU</th>
                  <th className="pb-1 font-medium">Action</th>
                </tr>
              </thead>
              <tbody>
                {[...diceData].reverse().map((d) => (
                  <tr key={d.round_id} className="border-b border-zinc-800/30">
                    <td className="py-1 pr-2 font-mono">#{d.round_id}</td>
                    <td className="py-1 pr-2">{d.val_dice?.toFixed(4)}</td>
                    <td className="py-1 pr-2">{d.val_iou?.toFixed(4)}</td>
                    <td className="py-1">
                      <button
                        onClick={() => setRollbackRid(d.round_id)}
                        className="px-2 py-0.5 rounded bg-orange-700 hover:bg-orange-600 text-xs cursor-pointer"
                      >
                        Rollback
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {rollbackRid !== null && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-6 max-w-sm w-full mx-4 space-y-4">
            <p className="text-sm">
              Roll back to <strong>Round {rollbackRid}</strong>? This will overwrite the current global model.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setRollbackRid(null)}
                className="px-4 py-2 rounded bg-zinc-800 hover:bg-zinc-700 text-sm cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={confirmRollback}
                className="px-4 py-2 rounded bg-orange-700 hover:bg-orange-600 text-sm cursor-pointer"
              >
                Confirm Rollback
              </button>
            </div>
          </div>
        </div>
      )}

      {rollbackMsg && (
        <p className="text-xs">{rollbackMsg}</p>
      )}
    </div>
  )
}
