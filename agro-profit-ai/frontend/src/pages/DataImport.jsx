import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";
import { useFarmFieldIds } from "../hooks/useFarmFieldIds.js";

const IMPORT_TABS = ["Talhões (GeoJSON)", "Produtividade", "Solo (laboratório)", "Operações"];

export default function DataImport() {
  const { auth } = useAuth();
  const [tab, setTab] = useState(IMPORT_TABS[0]);
  const [farmId, setFarmId] = useState(null);

  const farmsQuery = useQuery({ queryKey: ["farms"], queryFn: () => api.listFarms(auth.token) });
  useEffect(() => {
    if (!farmId && farmsQuery.data?.length) setFarmId(farmsQuery.data[0].id);
  }, [farmsQuery.data, farmId]);

  const fieldsQuery = useFarmFieldIds(farmId);

  return (
    <div>
      <h1>Dados da fazenda</h1>
      <p className="page-subtitle">
        Farm Data Hub (spec seção 5): dados do produtor são o ativo mais difícil de copiar — solo, produtividade e manejo
        alimentam diretamente a previsão e as recomendações.
      </p>

      {farmsQuery.data?.length > 1 && (
        <div className="tag-row">
          {farmsQuery.data.map((f) => (
            <button key={f.id} className={`tab-button${f.id === farmId ? " active" : ""}`} onClick={() => setFarmId(f.id)}>
              {f.name}
            </button>
          ))}
        </div>
      )}

      <div className="tag-row">
        {IMPORT_TABS.map((t) => (
          <button key={t} className={`tab-button${tab === t ? " active" : ""}`} onClick={() => setTab(t)}>
            {t}
          </button>
        ))}
      </div>

      <div className="card">
        {tab === "Talhões (GeoJSON)" && <ImportFields farmId={farmId} />}
        {tab === "Produtividade" && <ImportYield fields={fieldsQuery.data} />}
        {tab === "Solo (laboratório)" && <ImportSoil fields={fieldsQuery.data} />}
        {tab === "Operações" && <ImportOperation fields={fieldsQuery.data} />}
      </div>
    </div>
  );
}

function useFormStatus() {
  const [status, setStatus] = useState(null);
  return {
    status,
    async run(fn) {
      setStatus(null);
      try {
        await fn();
        setStatus({ ok: true, message: "Importado com sucesso." });
      } catch (err) {
        setStatus({ ok: false, message: err.message });
      }
    },
  };
}

function StatusMessage({ status }) {
  if (!status) return null;
  return <p className={status.ok ? "muted" : "login-error"} style={{ marginTop: 10 }}>{status.message}</p>;
}

function ImportFields({ farmId }) {
  const { auth } = useAuth();
  const [text, setText] = useState("");
  const [defaultCrop, setDefaultCrop] = useState("soja");
  const [defaultSeason, setDefaultSeason] = useState("2025/2026");
  const { status, run } = useFormStatus();

  return (
    <div>
      <h2>Importar limites de talhões (GeoJSON)</h2>
      <p className="muted" style={{ fontSize: 12 }}>
        Cole um FeatureCollection GeoJSON. Conversão de KML/Shapefile acontece client-side antes do envio.
      </p>
      <textarea rows={8} style={{ width: "100%" }} value={text} onChange={(e) => setText(e.target.value)} placeholder='{"type":"FeatureCollection","features":[...]}' />
      <div className="form-grid">
        <label>
          Cultura padrão
          <input value={defaultCrop} onChange={(e) => setDefaultCrop(e.target.value)} />
        </label>
        <label>
          Safra padrão
          <input value={defaultSeason} onChange={(e) => setDefaultSeason(e.target.value)} />
        </label>
      </div>
      <button
        className="btn-primary"
        onClick={() =>
          run(async () => {
            const geojson = JSON.parse(text);
            await api.importFields(auth.token, { farm_id: farmId, geojson, default_crop: defaultCrop, default_season: defaultSeason });
          })
        }
      >
        Importar talhões
      </button>
      <StatusMessage status={status} />
    </div>
  );
}

function FieldSelect({ fields, value, onChange }) {
  return (
    <label>
      Talhão
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">Selecione…</option>
        {fields?.map((f) => (
          <option key={f.id} value={f.id}>
            {f.name}
          </option>
        ))}
      </select>
    </label>
  );
}

function ImportYield({ fields }) {
  const { auth } = useAuth();
  const [fieldId, setFieldId] = useState("");
  const [season, setSeason] = useState("2024/2025");
  const [crop, setCrop] = useState("soja");
  const [yieldKgHa, setYieldKgHa] = useState("");
  const { status, run } = useFormStatus();

  return (
    <div>
      <h2>Importar produtividade histórica</h2>
      <div className="form-grid">
        <FieldSelect fields={fields} value={fieldId} onChange={setFieldId} />
        <label>
          Safra
          <input value={season} onChange={(e) => setSeason(e.target.value)} />
        </label>
        <label>
          Cultura
          <input value={crop} onChange={(e) => setCrop(e.target.value)} />
        </label>
        <label>
          Produtividade (kg/ha)
          <input type="number" value={yieldKgHa} onChange={(e) => setYieldKgHa(e.target.value)} />
        </label>
      </div>
      <button
        className="btn-primary"
        disabled={!fieldId}
        onClick={() =>
          run(() => api.importYieldRecord(auth.token, { field_id: fieldId, season, crop, yield_kg_ha: Number(yieldKgHa) }))
        }
      >
        Importar produtividade
      </button>
      <StatusMessage status={status} />
    </div>
  );
}

function ImportSoil({ fields }) {
  const { auth } = useAuth();
  const [fieldId, setFieldId] = useState("");
  const [form, setForm] = useState({ sample_id: "", depth_cm: "0-20", ph: "", organic_matter: "", clay: "", cec: "" });
  const { status, run } = useFormStatus();

  function set(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  return (
    <div>
      <h2>Importar amostra de solo (laboratório)</h2>
      <div className="form-grid">
        <FieldSelect fields={fields} value={fieldId} onChange={setFieldId} />
        <label>
          ID da amostra
          <input value={form.sample_id} onChange={(e) => set("sample_id", e.target.value)} />
        </label>
        <label>
          Profundidade (cm)
          <input value={form.depth_cm} onChange={(e) => set("depth_cm", e.target.value)} />
        </label>
        <label>
          pH
          <input type="number" step="0.1" value={form.ph} onChange={(e) => set("ph", e.target.value)} />
        </label>
        <label>
          Matéria orgânica (g/kg)
          <input type="number" value={form.organic_matter} onChange={(e) => set("organic_matter", e.target.value)} />
        </label>
        <label>
          Argila (%)
          <input type="number" value={form.clay} onChange={(e) => set("clay", e.target.value)} />
        </label>
        <label>
          CTC
          <input type="number" value={form.cec} onChange={(e) => set("cec", e.target.value)} />
        </label>
      </div>
      <button
        className="btn-primary"
        disabled={!fieldId}
        onClick={() =>
          run(() =>
            api.importSoilSample(auth.token, {
              field_id: fieldId,
              sample_id: form.sample_id,
              depth_cm: form.depth_cm,
              ph: form.ph ? Number(form.ph) : null,
              organic_matter: form.organic_matter ? Number(form.organic_matter) : null,
              clay: form.clay ? Number(form.clay) : null,
              cec: form.cec ? Number(form.cec) : null,
            }),
          )
        }
      >
        Importar amostra
      </button>
      <StatusMessage status={status} />
    </div>
  );
}

function ImportOperation({ fields }) {
  const { auth } = useAuth();
  const [fieldId, setFieldId] = useState("");
  const [form, setForm] = useState({ operation_type: "fertilization", product: "", cost_per_ha: "" });
  const { status, run } = useFormStatus();

  function set(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  return (
    <div>
      <h2>Importar operação (plantio, adubação, defensivo, irrigação)</h2>
      <div className="form-grid">
        <FieldSelect fields={fields} value={fieldId} onChange={setFieldId} />
        <label>
          Tipo
          <select value={form.operation_type} onChange={(e) => set("operation_type", e.target.value)}>
            <option value="planting">Plantio</option>
            <option value="fertilization">Adubação</option>
            <option value="defensive">Defensivo</option>
            <option value="irrigation">Irrigação</option>
            <option value="machine">Máquina</option>
            <option value="harvest">Colheita</option>
          </select>
        </label>
        <label>
          Produto
          <input value={form.product} onChange={(e) => set("product", e.target.value)} />
        </label>
        <label>
          Custo (R$/ha)
          <input type="number" value={form.cost_per_ha} onChange={(e) => set("cost_per_ha", e.target.value)} />
        </label>
      </div>
      <button
        className="btn-primary"
        disabled={!fieldId}
        onClick={() =>
          run(() =>
            api.importOperation(auth.token, {
              field_id: fieldId,
              operation_type: form.operation_type,
              product: form.product,
              cost_per_ha: form.cost_per_ha ? Number(form.cost_per_ha) : 0,
            }),
          )
        }
      >
        Importar operação
      </button>
      <StatusMessage status={status} />
    </div>
  );
}
