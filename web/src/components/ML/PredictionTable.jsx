import { formatPrice } from '@/utils/formatters';

export default function PredictionTable({ data = [] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="text-xs text-[var(--text-tertiary)] border-b border-[var(--border-primary)]">
            <th className="px-3 py-2 text-left">Stock</th>
            <th className="px-3 py-2 text-right">Predicted</th>
            <th className="px-3 py-2 text-right">LTP</th>
            <th className="px-3 py-2 text-right">Action</th>
          </tr>
        </thead>

        <tbody>
          {data.map((stock) => {
            const action = (stock.action || 'HOLD').toUpperCase();
            const actionClass =
              action === 'BUY'
                ? 'bg-[var(--profit-bg)] text-[var(--profit)]'
                : action === 'SELL'
                ? 'bg-[var(--loss-bg)] text-[var(--loss)]'
                : 'bg-[var(--bg-tertiary)] text-[var(--text-secondary)]';

            return (
              <tr
                key={stock.symbol}
                className="border-b border-[var(--border-primary)] hover:bg-[var(--bg-card-hover)] transition-colors cursor-pointer"
              >
                <td className="px-2 py-2">
                  <div className="flex items-center gap-1">
                    <div className="w-6 h-6 rounded-lg bg-[var(--accent-primary)]/10 flex items-center justify-center text-xs font-bold text-[var(--accent-primary)]">
                      {stock.symbol?.[0] || '?'}
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-[var(--text-primary)]">{stock.symbol}</p>
                      <p className="text-xs text-[var(--text-tertiary)] truncate max-w-[100px]">{stock._source === 'index' ? 'Market Index' : (stock.name || '')}</p>
                    </div>
                  </div>
                </td>

                <td className="px-2 py-2 text-right font-mono text-sm text-[var(--text-primary)]">
                  {stock.predicted_price != null ? formatPrice(stock.predicted_price) : '—'}
                </td>

                <td className="px-2 py-2 text-right font-mono text-sm text-[var(--text-primary)]">
                  {stock.last_price != null ? formatPrice(stock.last_price) : '—'}
                </td>

                <td className="px-2 py-2 text-right">
                  <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${actionClass}`}>
                    {action}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}