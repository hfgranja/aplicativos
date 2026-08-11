export function formatCurrency(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(value);
}

export function formatNumber(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("pt-BR", { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(value);
}

export function formatDate(value) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" }).format(new Date(value));
}
