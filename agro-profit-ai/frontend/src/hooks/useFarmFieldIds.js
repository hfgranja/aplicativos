import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";

export function useFarmFieldIds(farmId) {
  const { auth } = useAuth();
  return useQuery({
    queryKey: ["farm-fields", farmId],
    queryFn: () => api.listFarmFields(auth.token, farmId),
    enabled: Boolean(farmId),
  });
}
