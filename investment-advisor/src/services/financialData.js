/**
 * Financial data service — connects to public APIs:
 *  - Banco Central do Brasil (BCB/SGS) — SELIC, IPCA, CDI, USD/BRL
 *
 * All endpoints are CORS-friendly and require no API key.
 * Falls back to historical averages if any fetch fails.
 */

const BCB = "https://api.bcb.gov.br/dados/serie/bcdata.sgs";

async function bcbFetch(seriesCode, periods = 1) {
  try {
    const res = await fetch(
      `${BCB}.${seriesCode}/dados/ultimos/${periods}?formato=json`,
      { signal: AbortSignal.timeout(6000) }
    );
    if (!res.ok) throw new Error(`BCB ${seriesCode} error`);
    return await res.json();
  } catch {
    return null;
  }
}

/**
 * Returns live macro indicators from BCB.
 * Falls back to conservative historical averages on failure.
 */
export async function fetchMarketIndicators() {
  const [selicData, ipcaData, cdiData, usdData] = await Promise.all([
    bcbFetch(432, 1),   // Meta SELIC (% a.a.)
    bcbFetch(433, 12),  // IPCA mensal (% a.m.) — últimos 12 meses
    bcbFetch(4391, 1),  // Taxa CDI Over (% a.a.)
    bcbFetch(10813, 1), // USD/BRL (compra)
  ]);

  // SELIC meta anualizada
  const selic = selicData
    ? parseFloat(selicData[0].valor.replace(",", "."))
    : 13.75; // fallback

  // IPCA: anualize compound of last 12 monthly readings
  let ipcaAnual = 5.5; // fallback
  if (ipcaData && ipcaData.length > 0) {
    const compound = ipcaData.reduce(
      (acc, d) => acc * (1 + parseFloat(d.valor.replace(",", ".")) / 100),
      1
    );
    ipcaAnual = (compound - 1) * 100;
  }

  const cdi = cdiData
    ? parseFloat(cdiData[0].valor.replace(",", "."))
    : selic * 0.99;

  const usd = usdData
    ? parseFloat(usdData[0].valor.replace(",", "."))
    : 5.1;

  return {
    selic: +selic.toFixed(2),
    ipcaAnual: +ipcaAnual.toFixed(2),
    cdi: +cdi.toFixed(2),
    usd: +usd.toFixed(4),
    source: selicData ? "Banco Central do Brasil (tempo real)" : "Médias históricas (offline)",
    fetchedAt: new Date().toLocaleString("pt-BR"),
  };
}

/**
 * Human-readable descriptions for each data point shown in the market bar.
 */
export const INDICATOR_META = {
  selic: { label: "SELIC", unit: "% a.a.", desc: "Taxa básica de juros — BCB" },
  ipcaAnual: { label: "IPCA", unit: "% a.a.", desc: "Inflação 12 meses — BCB" },
  cdi: { label: "CDI", unit: "% a.a.", desc: "Taxa DI overnight — BCB" },
  usd: { label: "USD/BRL", unit: "R$", desc: "Câmbio dólar — BCB" },
};
