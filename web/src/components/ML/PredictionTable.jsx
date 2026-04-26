export default function PredictionTable({ data }) {
  return (
    <table border="1" cellPadding="10" style={{ width: "100%" }}>
      <thead>
        <tr>
          <th>Symbol</th>
          <th>Predicted Price</th>
          <th>Current Price</th>
          <th>Action</th>
        </tr>
      </thead>

      <tbody>
        {data.map((stock) => (
          <tr key={stock.symbol}>
            <td>{stock.symbol}</td>
            <td>{stock.predicted_price?.toFixed(2)}</td>
            <td>{stock.last_price?.toFixed(2)}</td>
            <td>
              <span style={{
                color:
                  stock.action === "BUY"
                    ? "green"
                    : stock.action === "SELL"
                    ? "red"
                    : "gray"
              }}>
                {stock.action}
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}