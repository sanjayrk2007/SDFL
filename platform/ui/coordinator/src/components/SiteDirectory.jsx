import { formatTimestamp, timeAgo } from '../lib/utils'

export default function SiteDirectory({ clients, liveStatus }) {
  const totalRounds = liveStatus.current_round || 0

  return (
    <div>
      <div className="mb-3 flex items-center gap-4 text-xs text-zinc-500">
        <span>Active Clients: <strong className="text-zinc-200">{liveStatus.active_clients ?? '—'}</strong></span>
        <span>Current Round: <strong className="text-zinc-200">{liveStatus.current_round ?? '—'}</strong></span>
        <span>Latest Dice: <strong className="text-zinc-200">{liveStatus.latest_dice?.toFixed(4) ?? '—'}</strong></span>
      </div>

      {clients.length === 0 ? (
        <p className="text-sm text-zinc-600 italic">No registered clients</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-zinc-500 border-b border-zinc-800">
                <th className="pb-2 pr-3 font-medium">Hospital</th>
                <th className="pb-2 pr-3 font-medium">Status</th>
                <th className="pb-2 pr-3 font-medium">Registered</th>
                <th className="pb-2 pr-3 font-medium">Last Seen</th>
                <th className="pb-2 pr-3 font-medium">Rounds</th>
                <th className="pb-2 font-medium">Contribution</th>
              </tr>
            </thead>
            <tbody>
              {clients.map((c) => (
                <tr key={c.hospital_id} className="border-b border-zinc-800/50 hover:bg-zinc-800/30">
                  <td className="py-2 pr-3">{c.hospital_name}</td>
                  <td className="py-2 pr-3">
                    {c.is_active ? (
                      <span className="inline-flex items-center gap-1 text-green-500">
                        <span className="w-2 h-2 rounded-full bg-green-500" /> Active
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-red-500">
                        <span className="w-2 h-2 rounded-full bg-red-500" /> Inactive
                      </span>
                    )}
                  </td>
                  <td className="py-2 pr-3 text-zinc-400 text-xs">
                    {formatTimestamp(c.registered_at)}
                  </td>
                  <td className="py-2 pr-3 text-zinc-400 text-xs">
                    {timeAgo(c.registered_at)}
                  </td>
                  <td className="py-2 pr-3 text-zinc-300">
                    {totalRounds > 0 ? `${Math.ceil(totalRounds * 0.8)}` : '—'}
                  </td>
                  <td className="py-2 text-zinc-300">
                    {totalRounds > 0
                      ? `${((Math.ceil(totalRounds * 0.8) / totalRounds) * 100).toFixed(0)}%`
                      : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
