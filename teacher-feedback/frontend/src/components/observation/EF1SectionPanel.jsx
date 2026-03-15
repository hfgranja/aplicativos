import { C } from '../../colors'
import { CriteriaRow } from './RatingButton'

const EF1_DOMAIN_META = {
  dc: {
    title: 'Domínio de Conteúdo',
    subtitle: 'Pedro Demo: "Ser professor é qualidade"',
    criteria: [
      ['ef1_dc_c1', 'Professor demonstra conhecimento sólido e preciso do conteúdo ensinado'],
      ['ef1_dc_c2', 'Explicações são adequadas à faixa etária (linguagem, exemplos, nível de abstração)'],
      ['ef1_dc_c3', 'Estabelece relações entre o conteúdo e o cotidiano/vivência das crianças'],
    ],
  },
  es: {
    title: 'Engajamento dos Estudantes',
    subtitle: 'Pedro Demo: "Educar pela pesquisa"',
    criteria: [
      ['ef1_es_c1', 'Crianças demonstram interesse, curiosidade e participação ativa'],
      ['ef1_es_c2', 'Professor valoriza e aproveita as falas e produções das crianças'],
      ['ef1_es_c3', 'Há clima de ludicidade, descoberta e pertencimento'],
    ],
  },
  me: {
    title: 'Metodologias e Estratégias',
    subtitle: 'Pedro Demo: "Avaliação qualitativa"',
    criteria: [
      ['ef1_me_c1', 'Utiliza abordagens variadas e adequadas para EF I (jogos, contação de histórias, brincadeiras dirigidas)'],
      ['ef1_me_c2', 'Propõe atividades que estimulam o pensamento, a autonomia e a criatividade'],
      ['ef1_me_c3', 'Equilibra momentos coletivos, em duplas/grupos e individuais'],
    ],
  },
  md: {
    title: 'Material Didático',
    subtitle: null,
    criteria: [
      ['ef1_md_c1', 'Materiais concretos, manipuláveis ou visuais são utilizados intencionalmente'],
      ['ef1_md_c2', 'Os recursos são adequados à faixa etária e ao objetivo da aula'],
      ['ef1_md_c3', 'Utiliza de forma intencional os materiais oficiais (livro didático, cadernos SEDUC)'],
    ],
  },
  gs: {
    title: 'Gestão de Sala',
    subtitle: null,
    criteria: [
      ['ef1_gs_c1', 'Organização do espaço físico favorece a aprendizagem e a interação'],
      ['ef1_gs_c2', 'Rotinas e transições entre atividades são claras e bem gerenciadas'],
      ['ef1_gs_c3', 'Tempo da aula é aproveitado de forma produtiva, minimizando tempos ociosos'],
    ],
  },
  mc: {
    title: 'Manejo de Conflitos',
    subtitle: null,
    criteria: [
      ['ef1_mc_c1', 'Professor identifica e intervém em situações de conflito com calma e assertividade'],
      ['ef1_mc_c2', 'Utiliza estratégias restaurativas, dialógicas e não punitivas'],
      ['ef1_mc_c3', 'Mantém ambiente acolhedor e seguro mesmo diante de comportamentos desafiadores'],
    ],
  },
}

const EF1_COLORS = {
  dc: '#6C63FF',
  es: '#00D4AA',
  me: '#FFB020',
  md: '#45B7D1',
  gs: '#FF6B6B',
  mc: '#A78BFA',
}

export function EF1SectionPanel({ domain, state, setRating }) {
  const meta = EF1_DOMAIN_META[domain]
  const color = EF1_COLORS[domain]

  return (
    <div>
      {/* EF I badge */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
        <span style={{
          background: color + '22', color, border: `1px solid ${color}55`,
          borderRadius: 6, padding: '3px 10px', fontSize: 11, fontWeight: 700,
        }}>
          EF I
        </span>
        <h2 style={{ color, fontSize: 16, fontWeight: 700, margin: 0 }}>
          {meta.title}
        </h2>
      </div>

      {meta.subtitle && (
        <p style={{ color: C.textMuted, fontSize: 12, marginBottom: 20, fontStyle: 'italic' }}>
          {meta.subtitle}
        </p>
      )}

      {meta.criteria.map(([field, label]) => (
        <CriteriaRow key={field} label={label} field={field} value={state[field]} onChange={setRating} />
      ))}
    </div>
  )
}

export function EF1MultiSectionPanel({ domains, state, setRating }) {
  return (
    <div>
      {domains.map((domain, i) => (
        <div key={domain}>
          {i > 0 && <div style={{ borderTop: `1px solid rgba(255,255,255,0.06)`, margin: '28px 0' }} />}
          <EF1SectionPanel domain={domain} state={state} setRating={setRating} />
        </div>
      ))}
    </div>
  )
}

export { EF1_COLORS }
