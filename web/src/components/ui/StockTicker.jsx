import React, { useEffect, useMemo, useState } from 'react';
import { cn } from '@/utils/cn';
import { formatPrice, formatPercent, getPnLColor } from '@/utils/formatters';
import { TrendingUp, TrendingDown } from 'lucide-react';

import tradingService from '@/services/tradingService';
import useMarketStore from '@/store/marketStore';
import useMarketSubscription from '@/hooks/useMarketSubscription';

const DEFAULT_SYMBOLS = [
  'RELIANCE',
  'TCS',
  'HDFCBANK',
  'INFY',
  'ICICIBANK',
  'ITC',
  'TATAMOTORS',
  'BHARTIARTL',
  'SBIN',
  'WIPRO',
  'SUNPHARMA',
  'LT',
];

const toNum = (v) => {
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
};

const normalizeKey = (v) => String(v || '').toUpperCase().trim();

const TickerItem = ({ data }) => {
  const isPositive = data.change >= 0;

  return (
    <div className="flex items-center gap-2 px-4 py-1 whitespace-nowrap">
      <span className="text-xs font-semibold text-[var(--text-primary)]">
        {data.symbol}
      </span>
      <span className="text-xs font-mono text-[var(--text-primary)]">
        {formatPrice(data.price)}
      </span>
      <span className={cn(
        'flex items-center gap-0.5 text-xs font-mono',
        isPositive ? 'text-[var(--profit)]' : 'text-[var(--loss)]'
      )}>
        {isPositive ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
        {formatPercent(data.changePercent)}
      </span>
      <span className="text-[var(--border-secondary)] mx-1">│</span>
    </div>
  );
};

const StockTicker = ({ symbols = DEFAULT_SYMBOLS, className }) => {
  const prices = useMarketStore((s) => s.prices);
  const [indices, setIndices] = useState([]);
  const [snapshots, setSnapshots] = useState({});

  useEffect(() => {
    let mounted = true;

    const load = async () => {
      try {
        const indicesRes = await tradingService.getMarketIndices();
        const raw = indicesRes?.data || [];

        if (mounted) {
          setIndices(raw.map((idx) => idx.name || idx.symbol).filter(Boolean));
        }

        const nextSnapshots = {};

        for (const idx of raw) {
          const label = idx.name || idx.symbol;
          if (!label) continue;
          nextSnapshots[normalizeKey(label)] = {
            symbol: label,
            price: toNum(idx.current_value),
            change: toNum(idx.change),
            changePercent: toNum(idx.change_percent),
          };
        }

        const quoteResults = await Promise.all(
          (Array.isArray(symbols) ? symbols : [])
            .filter(Boolean)
            .map(async (sym) => {
              try {
                const res = await tradingService.getStockQuote(sym);
                const q = res?.data || {};
                return {
                  symbol: sym,
                  price: toNum(q.price ?? q.current_price ?? q.last_price),
                  change: toNum(q.change),
                  changePercent: toNum(q.changePercent ?? q.change_percent),
                };
              } catch (_) {
                return null;
              }
            })
        );

        for (const q of quoteResults) {
          if (!q?.symbol) continue;
          nextSnapshots[normalizeKey(q.symbol)] = q;
        }

        if (mounted) {
          setSnapshots(nextSnapshots);
        }
      } catch (_) {
        if (mounted) {
          setIndices([]);
          setSnapshots({});
        }
      }
    };

    load();

    return () => {
      mounted = false;
    };
  }, [symbols]);

  useMarketSubscription({
    symbols: Array.isArray(symbols) ? symbols : [],
    indices,
    enabled: true,
  });

  const liveData = useMemo(() => {
    const base = [];

    for (const idx of indices) {
      const key = normalizeKey(idx);
      const live = prices?.[idx] || prices?.[key] || null;
      const snap = snapshots?.[key] || null;

      base.push({
        symbol: idx,
        price: toNum(live?.price ?? snap?.price),
        change: toNum(live?.change ?? snap?.change),
        changePercent: toNum(live?.changePercent ?? snap?.changePercent),
      });
    }

    for (const sym of (Array.isArray(symbols) ? symbols : [])) {
      const key = normalizeKey(sym);
      const live = prices?.[sym] || prices?.[key] || null;
      const snap = snapshots?.[key] || null;

      base.push({
        symbol: sym,
        price: toNum(live?.price ?? snap?.price),
        change: toNum(live?.change ?? snap?.change),
        changePercent: toNum(live?.changePercent ?? snap?.changePercent),
      });
    }

    return base.filter((x) => x.symbol);
  }, [indices, prices, snapshots, symbols]);

  // Double the data for seamless loop
  const tickerData = [...liveData, ...liveData];

  return (
    <div className={cn(
      'w-full overflow-hidden',
      'bg-[var(--bg-secondary)] border-b border-[var(--border-primary)]',
      className
    )}>
      <div className="ticker-tape py-1">
        <div className="ticker-tape-content">
          {tickerData.map((item, index) => (
            <TickerItem key={`${item.symbol}-${index}`} data={item} />
          ))}
        </div>
      </div>
    </div>
  );
};

export default StockTicker;