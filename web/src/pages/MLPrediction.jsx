import { useEffect, useState } from "react";
import { getMLPredictions } from "../services/mlService";
import PredictionTable from "../components/ML/PredictionTable";
import tradingService from "@/services/tradingService";

export default function MLPrediction() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  const indexAliasToYahoo = {
    'NIFTY 50': '^NSEI',
    'NIFTY BANK': '^NSEBANK',
    'S&P BSE SENSEX': '^BSESN',
    'SENSEX': '^BSESN',
    'INDIA VIX': '^INDIAVIX',
    'NIFTY 100': '^CNX100',
    'NIFTY 500': '^CRSLDX',
    'NIFTY IT': '^CNXIT',
    'NIFTY PHARMA': '^CNXPHARMA',
    'NIFTY AUTO': '^CNXAUTO',
    'NIFTY FMCG': '^CNXFMCG',
    'NIFTY METAL': '^CNXMETAL',
    'NIFTY REALTY': '^CNXREALTY',
    'NIFTY ENERGY': '^CNXENERGY',
    'NIFTY INFRA': '^CNXINFRA',
    'NIFTY PSU BANK': '^CNXPSUBANK',
    'NIFTY MIDCAP 50': '^NSEMDCP50',
    'NIFTY NEXT 50': '^NSMIDCP',
    'NIFTY SMLCAP 100': '^CNXSC',
    'NIFTY SMALLCAP 100': '^CNXSC',
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const [predRes, indicesRes] = await Promise.all([
        getMLPredictions(),
        tradingService.getMarketIndices(),
      ]);

      const predictions = Array.isArray(predRes) ? predRes : [];
      const indices = Array.isArray(indicesRes?.data) ? indicesRes.data : [];

      const indexKeys = new Set(
        indices
          .map((idx) => String(idx?.symbol || idx?.name || '').trim())
          .filter(Boolean)
          .map((s) => s.toUpperCase())
      );

      const bySymbol = new Map(
        predictions
          .filter((x) => x?.symbol)
          .map((x) => [String(x.symbol).toUpperCase(), x])
      );

      // Merge indices: if ML returned prediction under Yahoo index symbol (e.g. ^NSEI)
      // attach it to the market display symbol row (e.g. NIFTY 50).
      for (const idx of indices) {
        const sym = String(idx?.symbol || idx?.name || '').trim();
        if (!sym) continue;
        const key = sym.toUpperCase();

        const yahooKey = String(indexAliasToYahoo[key] || '').toUpperCase();
        const predicted = (yahooKey && bySymbol.has(yahooKey)) ? bySymbol.get(yahooKey) : null;

        if (predicted && !bySymbol.has(key)) {
          bySymbol.set(key, {
            ...predicted,
            symbol: sym,
            last_price: Number(idx?.current_value || predicted?.last_price || 0),
          });
          continue;
        }

        if (bySymbol.has(key)) {
          const existing = bySymbol.get(key);
          bySymbol.set(key, {
            ...existing,
            symbol: sym,
            last_price: Number(idx?.current_value || existing?.last_price || 0),
          });
          continue;
        }

        bySymbol.set(key, {
          symbol: sym,
          predicted_price: null,
          last_price: Number(idx?.current_value || 0),
          action: 'HOLD',
          _source: 'index',
        });
      }

      setData(Array.from(bySymbol.values()));
    } catch (_) {
      setData([]);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div style={{ padding: "20px" }}>
      <h2>🤖 AI Stock Predictions</h2>

      <button onClick={fetchData} style={{ marginBottom: 10 }}>
        Refresh
      </button>

      {loading ? (
        <p>Loading predictions...</p>
      ) : (
        <PredictionTable data={data} />
      )}
    </div>
  );
}