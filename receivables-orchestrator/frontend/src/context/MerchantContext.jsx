import { createContext, useContext, useEffect, useState } from "react";
import api from "../api/client.js";

const MerchantContext = createContext(null);

export function MerchantProvider({ children }) {
  const [merchants, setMerchants] = useState([]);
  const [merchantId, setMerchantId] = useState(localStorage.getItem("ro_merchant_id") || "");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    api
      .listMerchants()
      .then((list) => {
        setMerchants(list);
        if (!merchantId && list.length) {
          setMerchantId(list[0].id);
        }
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (merchantId) localStorage.setItem("ro_merchant_id", merchantId);
  }, [merchantId]);

  const merchant = merchants.find((m) => m.id === merchantId) || null;

  const value = {
    merchants,
    merchant,
    merchantId,
    apiKey: merchant?.api_key,
    setMerchantId,
    loading,
    error,
  };

  return <MerchantContext.Provider value={value}>{children}</MerchantContext.Provider>;
}

export function useMerchant() {
  const ctx = useContext(MerchantContext);
  if (!ctx) throw new Error("useMerchant deve ser usado dentro de MerchantProvider");
  return ctx;
}
