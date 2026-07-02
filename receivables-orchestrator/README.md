# Motor Inteligente de Recebimentos (Receivables Orchestrator)

Documento de design executivo/técnico completo **e** uma implementação
funcional do MVP descrito na seção 12 do design: o estabelecimento declara
uma intenção financeira ("receber R$ 12.500 até 15/08, priorizando
conversão") e o motor decide/recomenda o melhor caminho entre **Pix, cartão
de crédito e boleto**, com scoring explicável, fallback, retry, liquidação,
conciliação e auditoria imutável.

## Onde está o quê

- [`docs/DESIGN.md`](docs/DESIGN.md) — documento de design completo (24
  seções): visão executiva, PRD, jornada, motor de decisão, arquitetura,
  APIs, modelo de dados, IA, agentes, riscos/compliance, MVP, roadmap,
  business case, monetização, UX, observabilidade, segurança,
  explicabilidade, plano de implementação, testes, decisões críticas, pitch
  e entregáveis finais.
- [`backend/`](backend) — API (FastAPI + SQLAlchemy + SQLite) que implementa
  o motor de decisão, os agentes descritos na seção 10, provedores
  simulados de Pix/cartão/boleto, fallback/retry, liquidação/conciliação e
  auditoria com cadeia de hash.
- [`frontend/`](frontend) — painel (React + Vite) com as telas da seção 16:
  nova intenção, recomendação, explicação da decisão, acompanhamento de
  tentativas, política do estabelecimento e os dashboards de performance,
  custo, liquidação, conciliação, alertas e auditoria.

## Rodando localmente

### Com Docker

```bash
cd receivables-orchestrator
docker compose up
```

- Frontend: http://localhost:5173
- Backend/API: http://localhost:8000 (docs interativos em `/docs`)

### Sem Docker

```bash
# backend
cd receivables-orchestrator/backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000

# frontend (em outro terminal)
cd receivables-orchestrator/frontend
npm install
cp .env.example .env
npm run dev
```

Ao subir, o backend semeia automaticamente 2 estabelecimentos de
demonstração — **Nimbus Comércio Digital** (e-commerce B2C, modo
recomendação) e **Vetor Consultoria Empresarial** (B2B recorrente, modo
assistido) — cada um com clientes, provedores, política, fallback e retry
já configurados. O seletor de estabelecimento no topo do menu lateral troca
entre eles.

## O que está implementado vs. simulado vs. fora de escopo

Esta é uma implementação de **MVP demonstrável**, não um sistema de produção
tocando dinheiro real — coerente com a recomendação da seção 24 do design
doc de pilotar antes de automatizar totalmente. Especificamente:

| Implementado de verdade | Simulado (comportamento realista, sem infra real) | Fora de escopo desta implementação |
|---|---|---|
| Motor de regras (elegibilidade, limites, compliance) | Provedores de Pix/cartão/boleto (`app/providers/simulator.py`) — criação de cobrança, expiração, confirmação probabilística | Integração real com PSP/adquirente/banco (exigiria credenciais e homologação — seção 6/11 do design) |
| Motor de scoring com pesos configuráveis (seção 5) | Antifraude (heurística determinística em vez de modelo treinado — seção 9) | Modelos de ML treinados (propensão, risco, canal, etc. — seção 9) |
| Fallback e retry com backoff | Resolução assíncrona de tentativas (thread com delay simulado, análoga a um webhook chegando depois) | Event bus real (Kafka), arquitetura celular, multi-região (seção 6) |
| Explicabilidade multi-persona (CFO, financeiro, atendimento, auditoria, cliente final) | Liquidação e conciliação (fee/prazo calculados a partir dos parâmetros do provedor simulado) | Split de pagamento, antecipação de recebíveis, marketplace de provedores (roadmap 12-24 meses) |
| Auditoria imutável com cadeia de hash (verificável via `/receivables/audit-log/verify`) | | Autenticação OAuth2/mTLS completa, PCI-DSS (aqui: API key por merchant — ver nota em `app/security.py`) |
| 4 modos de operação (recomendação/assistido/automático/conservador) com guardrails de exposição e risco | | |

## Recomendação final do design (resumo)

**Pilotar em 90 dias** com 5-8 estabelecimentos em modo *recomendação*
(Pix + cartão + boleto, sem execução autônoma), antes de investir em
automação total. Detalhes na seção 24 de [`docs/DESIGN.md`](docs/DESIGN.md).
