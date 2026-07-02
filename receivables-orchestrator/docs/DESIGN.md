# Receivables Orchestrator — Motor Inteligente de Recebimentos

> Documento de design executivo, produto, arquitetura e negócio.
> Squad: CPO Pagamentos · Distinguished Engineer · Data/AI Lead · Risk Officer · CFO/Business Strategist · UX Lead

---

## 1. Visão executiva

### Problema atual

Hoje o estabelecimento comercial (merchant) decide manualmente, por reflexo ou hábito, qual meio de pagamento oferecer a cada cliente: "boleto para B2B", "Pix para reduzir custo", "cartão parcelado para ticket alto". Essa decisão é:

- **Estática** — não muda por cliente, horário, valor ou momento de caixa do estabelecimento.
- **Não instrumentada** — não há malha de feedback ligando meio escolhido → conversão → custo real → inadimplência.
- **Subótima em escala** — um estabelecimento com 50 mil cobranças/mês perde pontos de conversão e margem que uma decisão orientada a dados capturaria.
- **Cega a risco** — a mesma política é aplicada a um cliente adimplente histórico e a um cliente novo de alto risco.
- **Fragmentada entre provedores** — multiadquirência, Pix via PSP, boleto via banco e link via gateway operam como silos, cada um com seu próprio painel e SLA.

O resultado mensurável: taxas de conversão de cobrança 8–20 p.p. abaixo do potencial, custo transacional 15–40% acima do ótimo (uso de cartão onde Pix serviria), inadimplência não segmentada e times financeiros gastando horas em conciliação manual entre meios.

### Oportunidade de negócio

O mercado brasileiro de recebíveis é regido por três forças simultâneas: (1) fragmentação de meios de pagamento (Pix ultrapassou cartão em volume de transações desde 2023), (2) multiadquirência como padrão de mercado (Resolução BCB 4.649/2020 obriga portabilidade de recebíveis), e (3) pressão de margem em adquirência (MDR em queda estrutural). Isso cria espaço para uma camada de orquestração e inteligência **acima** dos meios de pagamento e das adquirentes — não competindo com Pix, cartão ou boleto, mas decidindo *entre* eles.

### Proposta de valor

> "O estabelecimento diz **o que** quer receber e **quando**. O motor decide **como**."

Substituímos a escolha manual de meio de pagamento por uma camada de decisão orientada a objetivo (conversão, custo, risco, liquidez ou experiência), que aprende com cada transação.

### Diferencial competitivo

| Alternativa de mercado | Limitação | Nosso diferencial |
|---|---|---|
| Gateway de checkout (ex.: Pagar.me, Cielo LIO) | Executa o meio escolhido pelo merchant; não decide | Decide/recomenda com base em objetivo declarado |
| Split de pagamento tradicional | Resolve divisão de valores, não escolha de meio | Split é uma dimensão do motor, não o produto inteiro |
| Cobrança recorrente (assinatura) | Foco em retry de cartão apenas | Multi-meio, multi-objetivo, com fallback cross-rail |
| ERP financeiro | Registra, não decide nem executa | Decide, executa e retroalimenta o ERP |
| Adquirente única | Interesse em empurrar seu próprio meio (cartão) | Agnóstico de meio — otimiza para o merchant, não para si mesmo |

### Por que agora

1. **Pix atingiu maturidade de infraestrutura** (Pix Automático, Pix Garantido/Parcelado em rollout do BACEN) — cria mais "caminhos" para orquestrar.
2. **Open Finance** disponibiliza dados de conta e histórico de pagamento do cliente pagador, com consentimento — alimenta o scoring.
3. **Custo de IA caiu** o suficiente para rodar modelos de decisão em tempo real por transação com custo marginal desprezível.
4. **Regulação empurra multiadquirência e portabilidade** — o mercado já assume que meios e adquirentes são intercambiáveis; falta a camada de decisão.
5. **Pressão de margem** em varejo e serviços torna 1–3 p.p. de economia em custo transacional um argumento comercial imediato, não hipotético.

### Benefícios por ator

| Ator | Benefício |
|---|---|
| Estabelecimento | +conversão, -custo de recebimento, previsibilidade de caixa, menos operação manual, explicação auditável da decisão |
| Cliente pagador | Recebe a opção de pagamento mais conveniente para o seu perfil, menos fricção, menos cobrança repetida indevida |
| Adquirente/instituição financeira parceira | Aumento de volume roteado (se participar do roteamento), dados de performance por segmento, redução de estorno/chargeback por melhor triagem |

### Tese de impacto financeiro

Para um estabelecimento de médio porte com R$ 10 milhões/mês em recebíveis:

- **+3 a +7 p.p. de conversão de cobrança** via escolha do meio certo por perfil de cliente.
- **-15% a -30% de custo transacional médio** por deslocar volume de cartão para Pix/boleto quando o objetivo é custo e o risco permite.
- **-10% a -20% de chargeback/estorno** por triagem de risco antes do roteamento.
- **Redução de 30–50% do esforço operacional** de conciliação manual entre meios.

Esses números são o *range* observado em produtos análogos de orquestração de pagamento (roteamento inteligente de gateway, otimização de checkout); serão validados e recalibrados durante o piloto (seção 12).

---

## 2. Definição do produto (PRD)

### Nome da solução
**Receivables Orchestrator** (nome interno: "Motor Inteligente de Recebimentos" / codinome de projeto: **Órbita**).

### Persona principal
**Gestor financeiro / dono de operação de cobrança do estabelecimento** (CFO de PME, analista de contas a receber de empresa média, head de growth/checkout de e-commerce). Dor central: precisa maximizar entrada de caixa sem aumentar custo nem inadimplência, e não tem tempo/expertise para configurar regras finas por meio de pagamento.

### Personas secundárias

- **Cliente pagador** (consumidor final ou empresa cliente do estabelecimento) — recebe a cobrança pelo canal e meio mais convenientes.
- **Time de atendimento/cobrança** — precisa entender por que um cliente recebeu boleto e não Pix, para responder dúvidas.
- **Risk/Compliance officer do estabelecimento maior** — precisa auditar decisões e limites de exposição.
- **Desenvolvedor integrador** (ERP, e-commerce, software de gestão) — consome a API do Orchestrator.
- **Executivo/board** — quer o dashboard de impacto financeiro, não o detalhe operacional.

### Jobs to be Done

1. "Quando preciso cobrar um cliente, quero declarar o resultado que busco (receber rápido, barato, com baixo risco) sem escolher manualmente o meio."
2. "Quando um pagamento falha, quero que o sistema tente automaticamente uma alternativa antes de eu precisar intervir."
3. "Quando o mês fecha, quero entender quanto economizei e por quê, para justificar a ferramenta ao meu board."
4. "Quando um auditor pergunta por que cobramos assim um cliente específico, quero uma explicação clara e rastreável."
5. "Quando preciso de caixa antecipado, quero que o sistema já saiba disso e priorize meios de liquidação rápida."

### Casos de uso

- Cobrança avulsa B2C (e-commerce, serviços) — decisão em tempo real no checkout.
- Cobrança B2B recorrente (mensalidades, contratos) — decisão + retry + fallback ao longo de um ciclo de dias.
- Cobrança de dívida/atraso (régua de cobrança) — decisão de canal e meio para recuperação.
- Marketplace com split — decisão de meio + divisão automática entre vendedor e plataforma.
- Antecipação de recebíveis — recomendação de quando antecipar com base em necessidade de caixa declarada.

### Dores atuais (hoje, sem o produto)

- Escolha de meio hardcoded no checkout ou na régua de cobrança.
- Fallback manual: humano liga ou reenvia cobrança quando o Pix expira.
- Conciliação feita em planilha cruzando extratos de 3–5 adquirentes/PSPs.
- Nenhuma malha de aprendizado: o mesmo erro de roteamento se repete todo mês.
- Explicação de decisão inexistente — "sempre fizemos assim".

### Funcionalidades essenciais (core)

1. Criação de intenção de recebimento (`ReceivableIntent`) via API/painel.
2. Motor de regras + scoring que ranqueia meios disponíveis.
3. Execução ou recomendação da estratégia (conforme modo de operação).
4. Fallback determinístico entre meios quando o primeiro falha/expira.
5. Retry controlado (cartão negado, Pix expirado).
6. Registro de tentativas, confirmação de pagamento, conciliação básica.
7. Explicação de decisão (por que este meio, não outro).
8. Dashboard de performance (conversão, custo, tempo até pagamento).

### Funcionalidades avançadas (pós-MVP)

- Split de pagamento multi-parte com regras de comissão.
- Recomendação de antecipação de recebíveis integrada a fluxo de caixa.
- Modelo de melhor canal e horário de comunicação (WhatsApp, SMS, e-mail, push).
- Scoring de propensão e risco por cliente pagador com aprendizado contínuo.
- Modo autopilot com limites de exposição financeira.
- Marketplace de provedores (múltiplos PSPs de Pix, múltiplas adquirentes de cartão) com roteamento por SLA e custo em tempo real.
- API de simulação ("what-if eu priorizasse custo em vez de conversão?").

### O que fica fora do MVP

- Execução 100% autônoma sem revisão humana.
- Split de pagamento complexo (N partes com regras condicionais).
- Modelo de risco de fraude proprietário (usar provedor terceiro no MVP).
- Antecipação de recebíveis como produto financeiro (apenas recomendação, sem execução de crédito).
- Múltiplos provedores por meio (marketplace) — MVP usa um provedor por meio.
- Comunicação multicanal inteligente — MVP usa canal único pré-configurado.

### Critérios de sucesso

- Piloto com 5–8 estabelecimentos ativos por 90 dias sem incidente de duplicidade de cobrança ou falha de liquidação.
- Ganho de conversão mensurável ≥ 3 p.p. vs. baseline do estabelecimento.
- NPS do estabelecimento piloto ≥ 40.
- 100% das decisões com explicação disponível e auditável.

### Métricas norte (North Star)

**Valor líquido recebido a tempo, por real de intenção declarada** — isto é: de cada R$ 1 que o estabelecimento pediu para receber até a data-alvo, quantos centavos chegaram, líquidos de custo transacional, dentro do prazo.

### Métricas operacionais

- Taxa de conversão por meio e por intenção.
- Tempo médio até confirmação de pagamento.
- Taxa de fallback acionado.
- Taxa de sucesso de retry.
- Taxa de erro por provedor.
- % de decisões automáticas vs. recomendadas vs. sobrescritas por humano.

### Métricas de risco

- Taxa de chargeback por meio/segmento.
- Taxa de fraude confirmada.
- Exposição financeira em autopilot (valor sob decisão autônoma).
- % de decisões de baixa confiança escaladas para humano.

### Métricas de experiência

- Tempo até o cliente pagador visualizar a opção de pagamento.
- Taxa de reclamação/dúvida sobre cobrança.
- Taxa de abandono por meio oferecido.
- Preferência declarada vs. meio oferecido (aderência).

---

## 3. Jornada ponta a ponta

| # | Etapa | Entrada | Processamento | Saída | Riscos | Controles | Métricas |
|---|---|---|---|---|---|---|---|
| 1 | Estabelecimento cria intenção | `merchant_id`, valor, prazo, objetivo, restrições | Validação de schema, política do merchant, limites | `ReceivableIntent` criado (status `created`) | Intenção duplicada; dados incompletos | Idempotency-key obrigatória; validação síncrona | Taxa de intenções válidas na 1ª tentativa |
| 2 | Motor recebe contexto da transação | Intenção + metadados (canal de origem, produto/serviço) | Enriquecimento de contexto (segmento, geografia, canal) | Contexto consolidado anexado à intenção | Contexto ausente leva a decisão pobre | Valores default por segmento; alerta se contexto < 60% completo | % de intenções com contexto completo |
| 3 | Consulta dados de cliente/risco/custo/liquidez | `customer_id`, histórico | Chamadas paralelas a: perfil do cliente, antifraude, tabela de custo por provedor, posição de caixa do merchant | Feature vector consolidado | Timeout de provedor externo; dado desatualizado | Timeout curto (< 800 ms) com fallback a cache; circuit breaker | Latência p95 de enriquecimento; taxa de cache hit |
| 4 | Motor calcula opções possíveis | Feature vector + meios habilitados/proibidos | Motor de regras filtra opções elegíveis (compliance, limites, meios permitidos) | Lista de `PaymentOption` elegíveis | Meio inelegível passar pelo filtro | Regras determinísticas versionadas; teste de regressão de regras | Nº médio de opções elegíveis por intenção |
| 5 | IA ranqueia os melhores caminhos | Opções elegíveis + pesos da política do merchant | Modelo de scoring (seção 5) calcula `DecisionScore` por opção | Ranking ordenado com score e confiança | Score enviesado por dado ruim; baixa confiança não tratada | Threshold de confiança mínima; fallback a regra determinística se confiança baixa | Confiança média da decisão; % de decisões abaixo do threshold |
| 6 | Sistema recomenda ou executa | Ranking + modo de operação | Se modo recomendação: aguarda aprovação; se automático: executa dentro de limites | `PaymentRoute` definida | Execução fora do limite aprovado | Guardrails de valor máximo por modo; aprovação humana obrigatória acima de limite | % de recomendações aceitas sem alteração |
| 7 | Cliente recebe a opção | `PaymentRoute` + dados de contato | Geração de cobrança no meio escolhido (QR Pix, link de cartão, boleto) + envio pelo canal definido | Cobrança entregue ao cliente pagador | Canal errado; cobrança não entregue | Confirmação de entrega (webhook do canal); reenvio automático se não visualizado em X horas | Taxa de entrega; taxa de visualização |
| 8 | Falha → retry/fallback | Evento de falha/expiração | `RetryPolicy` decide novo timing; se esgotado, `FallbackPlan` escolhe meio alternativo | Nova tentativa ou novo meio acionado | Retry excessivo gera fadiga/spam | Limite de tentativas; backoff exponencial; interstício mínimo entre tentativas | Taxa de sucesso por tentativa; nº médio de tentativas até sucesso |
| 9 | Pagamento confirmado | Webhook do provedor/adquirente | Validação de assinatura, idempotência, valor exato | `PaymentAttempt` = `confirmed` | Confirmação falsa/replay | Verificação de assinatura HMAC; idempotency-key; reconciliação cruzada com extrato | Tempo entre criação e confirmação |
| 10 | Liquidação e conciliação | Extrato do provedor + `PaymentAttempt` | Casamento automático (matching) por valor/data/id; split se aplicável | `Settlement` + `Reconciliation` registrados | Diferença de valor não identificada | Alertas de divergência > tolerância; fila de exceção manual | Taxa de conciliação automática |
| 11 | Retroalimentação do modelo | Resultado real (sucesso, tempo, custo, chargeback) | Pipeline de feature/label engineering grava outcome | Dataset atualizado para retreino | Label incorreta contaminando o modelo | Validação de outcome antes de uso em treino; janela de maturação (ex.: aguardar 30 dias por chargeback) | Lag entre evento e disponibilidade para treino |
| 12 | Dashboard explica e mostra performance | Todos os dados acima | Agregação e explicação por decisão | Visualização executiva/operacional | Métrica enganosa sem contexto | Definição única de métrica (data dictionary); revisão de dashboard por Data Lead | Ver seção 2 (métricas) |

---

## 4. Modos de operação

| Modo | Quando usar | Benefícios | Riscos | Guardrails | Critério de evolução |
|---|---|---|---|---|---|
| **Recomendação** | Início de relacionamento, merchants sem histórico de dados suficiente, decisões de alto valor | Zero risco de execução errada; constrói confiança | Lento, depende de humano disponível | Nenhuma execução sem clique de aprovação | ≥ 500 decisões aprovadas com < 5% de alteração pelo humano |
| **Assistido** | Merchant já validou o motor; quer velocidade mas com trilhos | IA executa, mas só dentro de regras pré-aprovadas (ex.: "Pix sempre para valores < R$ 500") | Regras mal calibradas geram execução indesejada dentro do trilho | Regras auditáveis e versionadas; revisão mensal obrigatória | Regras estáveis por 60 dias sem exceção manual > 2% |
| **Automático** | Merchant maduro, volume alto, necessidade de velocidade | Decide e executa com limites de valor/risco (autopilot com teto) | Erro sistemático em escala antes de detecção | Limite de exposição financeira por dia/hora; circuit breaker que pausa autopilot se taxa de erro > threshold | 90 dias em modo assistido sem incidente + auditoria aprovada |
| **Conservador** | Segmentos regulados, valores muito altos, clientes novos de alto risco | Só atua com alta confiança do modelo (ex. > 0.9); caso contrário, escala para humano | Muitas escalações reduzem o ganho de automação | Threshold de confiança configurável por merchant/segmento; escalação com SLA definido | Modo permanente para segmentos de risco — não "evolui", é uma política deliberada |

Regra geral de maturidade: a transição entre modos é **gated por dados**, nunca por tempo decorrido isoladamente. Cada merchant tem um "nível de confiança operacional" calculado a partir de volume de decisões, taxa de acerto e ausência de incidentes.

---

## 5. Motor de decisão

### Dimensões consideradas

Conversão esperada, custo total, risco de fraude, risco de chargeback, prazo de liquidação, necessidade de caixa, preferência do cliente, preferência do estabelecimento, valor da transação, segmento de mercado, histórico de sucesso, canal disponível, status operacional dos provedores, regras regulatórias, limites de exposição.

### Fórmula conceitual de scoring

Para cada opção de pagamento `o` (ex.: Pix, cartão à vista, cartão parcelado 3x, boleto), calculamos:

```
Score(o) = w_conv  · Conversao_esperada(o)
         - w_custo · Custo_total_normalizado(o)
         - w_risco · Risco_estimado(o)
         + w_liq   · Liquidez(o)
         + w_exp   · Experiencia_esperada(o)
         + w_pref  · Aderencia_preferencia_cliente(o)

sujeito a:
  Score(o) = -infinito  se o viola regra dura (compliance, meio proibido,
                          limite de exposição, provedor indisponível)

Confianca(o) = f(qualidade_dos_dados, cobertura_historica, variancia_do_modelo)
```

Onde cada termo é normalizado em [0,1] antes da ponderação. `Custo_total_normalizado` inclui MDR/tarifa fixa, custo de antecipação se aplicável, e custo operacional de fallback esperado (custo esperado de precisar de uma 2ª tentativa). `Liquidez(o)` é inversamente proporcional ao prazo de liquidação (D+0 Pix > D+1 débito > D+2 crédito à vista > D+30 boleto).

A opção com maior `Score` e `Confiança` acima do threshold do modo de operação vence. As demais opções e seus scores ficam registrados em `DecisionScore` para explicabilidade (seção 19).

### Pesos por política do estabelecimento

| Política | w_conv | w_custo | w_risco | w_liq | w_exp | w_pref | Efeito prático |
|---|---|---|---|---|---|---|---|
| Maximizar conversão | 0.40 | 0.10 | 0.15 | 0.10 | 0.15 | 0.10 | Favorece Pix/boleto com menor fricção; parcelamento quando ajuda a fechar venda |
| Minimizar custo | 0.15 | 0.45 | 0.15 | 0.10 | 0.05 | 0.10 | Favorece Pix e boleto sobre cartão; evita antecipação |
| Minimizar risco | 0.15 | 0.10 | 0.45 | 0.10 | 0.10 | 0.10 | Favorece meios com antifraude mais forte (cartão com 3DS, Pix com score alto); pode recusar boleto para cliente novo |
| Maximizar liquidez | 0.15 | 0.10 | 0.15 | 0.45 | 0.05 | 0.10 | Favorece Pix (D+0) sobre boleto/crédito parcelado |
| Maximizar experiência | 0.15 | 0.10 | 0.10 | 0.10 | 0.45 | 0.10 | Favorece o meio historicamente preferido pelo cliente, menor nº de passos |
| Balanceada (default) | 0.22 | 0.22 | 0.22 | 0.14 | 0.12 | 0.08 | Distribuição equilibrada; ponto de partida recomendado no MVP |

Os pesos são configuráveis por `MerchantPolicy` e podem ser sobrepostos por intenção específica (`objective` no payload da API). O motor nunca deixa `w_risco` cair abaixo de um piso mínimo absoluto (`w_risco_floor`), mesmo em política "maximizar conversão" — isso é um guardrail duro, não uma preferência.

---

## 6. Arquitetura técnica

### Visão lógica (componentes)

```
[Canais de entrada: API, Painel Web, ERP/CRM, E-commerce plugin]
        │
        ▼
[API Gateway] — autenticação, rate limiting, roteamento
        │
        ▼
[Serviço de Intenção de Recebimento] → publica evento IntentCreated
        │
        ▼
[Event Bus] ──────────────────────────────────────────────┐
        │                                                   │
        ▼                                                   ▼
[Motor de Regras] → filtra opções elegíveis      [Serviço de Auditoria] (consome tudo)
        │
        ▼
[Serviço de Scoring / Motor de Decisão IA] → consulta [Feature Store]
        │
        ▼
[Serviço de Roteamento de Pagamento] → aciona provedor via [Camada de Integração]
        │                                   │
        │                        ┌──────────┼──────────┬─────────────┐
        │                        ▼          ▼          ▼             ▼
        │                    [Pix PSP] [Adquirente] [Boleto/Banco] [Antifraude]
        ▼
[Serviço de Comunicação] → envia cobrança (WhatsApp/SMS/e-mail/link)
        │
        ▼
[Serviço de Retry] ←→ [Serviço de Fallback]  (orientados por evento de falha)
        │
        ▼
[Serviço de Conciliação] ←→ [Serviço de Liquidação]
        │
        ▼
[Data Lake] → [Feature Store] → [Model Registry] → [MLOps pipeline] (retreino)
        │
        ▼
[Dashboard Operacional] / [Dashboard Executivo]
```

Transversais a todos os serviços: **Serviço de Observabilidade** (logs, métricas, traces) e **Serviço de Auditoria** (log imutável de toda decisão e mutação de estado).

### Visão física (deploy)

- Arquitetura **celular/modular**: cada célula atende um subconjunto de merchants (sharding por `merchant_id`), isolando blast radius de incidentes.
- Serviços stateless em containers (Kubernetes), auto-scaling horizontal por fila de eventos.
- Banco de dados transacional (PostgreSQL) por domínio (intent, payment, settlement) com **outbox pattern** para publicar eventos de forma consistente com a escrita transacional.
- Event bus (Kafka ou equivalente gerenciado) com partições por `merchant_id` para ordenação garantida por merchant.
- Multi-AZ dentro da região primária; **disaster recovery** com réplica em região secundária e RTO/RPO definidos por criticidade do serviço (ver seção 17).

### Visão de integração

- **Pix**: integração via PSP autorizado pelo BACEN (API Pix — DICT, criação de cobrança imediata `cob`, webhook de liquidação).
- **Cartão**: integração via adquirente/subadquirente (tokenização, 3DS2, captura, cancelamento) — camada de abstração multiadquirente para permitir troca de provedor sem refatorar o core.
- **Boleto**: integração via banco emissor ou agregador de boleto (registro CIP, baixa automática).
- **Antifraude**: provedor terceiro (ex.: score de dispositivo, geolocalização, velocity checks) consumido de forma síncrona com timeout curto.
- **ERP/CRM**: webhooks de saída (status da intenção, confirmação de pagamento) + API de consulta para sincronizar contas a receber.
- **Link de pagamento / carteira digital**: via camada de checkout hospedado, reaproveitando tokenização de cartão e QR Pix.

### Visão de dados

- **Data Lake** (bronze/silver/gold) recebe todos os eventos brutos (intents, tentativas, confirmações, falhas).
- **Feature Store** materializa features de cliente, merchant e transação com baixa latência (online store) para servir o motor de decisão em tempo real, e histórico (offline store) para treino.
- **Model Registry** versiona modelos, com metadata de dataset de treino, métricas e aprovação de governança antes de promoção a produção.

### Visão de segurança

Detalhada na seção 18 — autenticação mTLS/OAuth2 entre serviços, tokenização de dados de cartão (nunca armazenar PAN), criptografia em repouso e trânsito, segregação de dados sensíveis (PII) do dado transacional.

### Visão de resiliência

- **Idempotência**: toda operação de criação/execução exige `Idempotency-Key`; reprocessamento de evento não duplica efeito.
- **Retry controlado**: backoff exponencial com jitter; máximo de tentativas configurável por tipo de falha.
- **Circuit breaker**: por provedor — se taxa de erro do provedor > threshold em janela deslizante, o roteamento para de enviar tráfego a ele automaticamente e aciona fallback.
- **Timeout**: todo call síncrono a serviço externo tem timeout curto (< 1s) com fallback a cache ou valor default seguro.
- **SAGA**: fluxo de pagamento com split é modelado como SAGA (criação de cobrança → confirmação → distribuição de split → compensação se etapa falhar).
- **Outbox pattern**: garante que evento de domínio só é publicado se a transação de banco correspondente foi commitada.
- **Auditoria imutável**: `AuditLog` em armazenamento append-only (write-once), com hash encadeado para detectar adulteração.
- **Observabilidade ponta a ponta**: trace id único por intenção, propagado por todos os serviços e provedores externos (quando suportado).
- **Alta disponibilidade**: SLO de disponibilidade do core de decisão ≥ 99.9%; degradação graciosa (se o motor de IA cair, cai para motor de regras determinístico, nunca para "sem decisão").

---

## 7. APIs principais

### Criar intenção de recebimento

```
POST /receivables/intents
Idempotency-Key: 8f14e45f-...
```
```json
{
  "merchant_id": "mch_9182",
  "customer_id": "cus_4471",
  "amount": 12500.00,
  "currency": "BRL",
  "due_date": "2026-08-15",
  "objective": "maximize_conversion",
  "allowed_payment_methods": ["pix", "credit_card", "boleto"],
  "forbidden_payment_methods": ["debit_card"],
  "max_cost": {"type": "percentage", "value": 3.5},
  "max_risk": "medium",
  "liquidity_need": "standard",
  "customer_context": {
    "segment": "b2b_recurring",
    "preferred_channel": "whatsapp",
    "historical_payment_method": "boleto"
  },
  "merchant_policy": {
    "policy_id": "pol_balanced_default"
  },
  "metadata": {
    "order_id": "ord_778812",
    "source": "erp_totvs"
  }
}
```
Resposta `201`:
```json
{
  "intent_id": "int_5f3a9c",
  "status": "created",
  "created_at": "2026-07-02T14:30:00Z"
}
```

### Consultar recomendação

```
GET /receivables/intents/int_5f3a9c/recommendation
```
```json
{
  "intent_id": "int_5f3a9c",
  "recommended_route": {
    "payment_method": "pix",
    "score": 0.87,
    "confidence": 0.93,
    "expected_conversion": 0.91,
    "expected_cost_pct": 0.99,
    "expected_settlement": "D+0"
  },
  "alternatives": [
    {"payment_method": "boleto", "score": 0.71, "confidence": 0.90},
    {"payment_method": "credit_card_1x", "score": 0.64, "confidence": 0.88}
  ],
  "model_version": "decision-engine-v2.3.1"
}
```

### Executar estratégia

```
POST /receivables/intents/int_5f3a9c/execute
Idempotency-Key: 3b2c11a0-...
```
```json
{ "approved_route": "pix", "approved_by": "user_2291" }
```
Resposta:
```json
{
  "route_id": "rte_00291",
  "status": "executing",
  "payment_link": "https://pay.orchestrator.com/qr/rte_00291"
}
```

### Consultar status

```
GET /receivables/intents/int_5f3a9c/status
```
```json
{
  "intent_id": "int_5f3a9c",
  "status": "awaiting_payment",
  "current_attempt": {"attempt_id": "att_881", "method": "pix", "expires_at": "2026-07-02T15:30:00Z"}
}
```

### Registrar pagamento (webhook de entrada do provedor)

```
POST /receivables/webhooks/pix
X-Signature: hmac-sha256=...
```
```json
{
  "provider_event_id": "evt_pix_00981",
  "route_id": "rte_00291",
  "status": "confirmed",
  "amount": 12500.00,
  "paid_at": "2026-07-02T14:52:11Z",
  "e2e_id": "E12345678202607021452abc"
}
```

### Reprocessar tentativa

```
POST /receivables/intents/int_5f3a9c/retry
Idempotency-Key: 9a11f2ee-...
```
```json
{ "reason": "pix_expired" }
```

### Aplicar fallback

```
POST /receivables/intents/int_5f3a9c/fallback
```
```json
{ "from_method": "pix", "to_method": "boleto", "trigger": "expired_no_action" }
```

### Consultar explicação da decisão

```
GET /receivables/intents/int_5f3a9c/explanation
```
```json
{
  "chosen_method": "pix",
  "reason_summary": "Pix maximiza conversão esperada (91%) e liquidação D+0, dentro do limite de custo de 3.5% definido pela política.",
  "discarded_options": [
    {"method": "credit_card_3x", "reason": "custo estimado 8.2% excede max_cost declarado"},
    {"method": "boleto", "reason": "score inferior por menor conversão esperada (78%) para este segmento"}
  ],
  "weights_applied": {"conversion": 0.40, "cost": 0.10, "risk": 0.15, "liquidity": 0.10, "experience": 0.15, "preference": 0.10}
}
```

### Consultar conciliação

```
GET /receivables/settlements?merchant_id=mch_9182&date=2026-07-02
```
```json
{
  "settlements": [
    {"route_id": "rte_00291", "gross_amount": 12500.00, "fee": 123.75, "net_amount": 12376.25, "settled_at": "2026-07-02T18:00:00Z", "reconciled": true}
  ]
}
```

### Consultar métricas

```
GET /receivables/metrics?merchant_id=mch_9182&period=2026-07
```
```json
{
  "conversion_rate": 0.89,
  "avg_cost_pct": 1.6,
  "avg_time_to_payment_hours": 4.2,
  "fallback_rate": 0.07,
  "chargeback_rate": 0.003
}
```

---

## 8. Modelo de dados

| Entidade | Campos principais | Chaves | Relacionamentos | Dados sensíveis | Retenção | LGPD |
|---|---|---|---|---|---|---|
| **Merchant** | nome, documento (CNPJ), segmento, política padrão | `merchant_id` (PK) | 1:N com Intent, MerchantPolicy | CNPJ, dados bancários | Vida do contrato + 5 anos (obrigação fiscal) | Base legal: execução de contrato |
| **Customer** | nome, documento, contato, segmento | `customer_id` (PK) | 1:N com Intent; 1:1 com CustomerPreference | CPF/CNPJ, telefone, e-mail | Vida do relacionamento + prazo legal de cobrança | Consentimento + legítimo interesse para cobrança |
| **ReceivableIntent** | amount, due_date, objective, status | `intent_id` (PK), FK `merchant_id`, `customer_id` | 1:N com PaymentOption, PaymentAttempt | Valor financeiro | 5 anos (fiscal/contábil) | Minimização: não replicar PII além do necessário |
| **PaymentOption** | method, estimated_cost, estimated_conversion | `option_id` (PK), FK `intent_id` | N:1 com Intent; 1:1 com DecisionScore | — | Igual ao Intent | — |
| **PaymentAttempt** | method, status, expires_at, provider_ref | `attempt_id` (PK), FK `intent_id` | N:1 com Intent | Dados de pagamento tokenizados | 5 anos | Token, não dado bruto de cartão |
| **PaymentRoute** | chosen_method, executed_at, mode | `route_id` (PK), FK `intent_id` | 1:N com PaymentAttempt | — | 5 anos | — |
| **PaymentProvider** | nome, tipo (Pix/cartão/boleto), status operacional, SLA | `provider_id` (PK) | N:M com PaymentRoute | Credenciais (em vault, não na tabela) | Enquanto ativo | — |
| **RiskAssessment** | fraud_score, chargeback_score, model_version | `assessment_id` (PK), FK `intent_id` ou `customer_id` | 1:1 com Intent | Score de risco (dado sensível de decisão automatizada) | 5 anos (auditoria) | Direito à explicação (art. 20 LGPD) |
| **DecisionScore** | score, confidence, weights_applied, discarded_options | `score_id` (PK), FK `option_id` | 1:1 com PaymentOption | — | 5 anos (auditoria) | Base da explicabilidade obrigatória |
| **FallbackPlan** | trigger_condition, from_method, to_method, max_attempts | `plan_id` (PK), FK `merchant_id` | 1:N aplicado a Intent | — | Enquanto ativo | — |
| **RetryPolicy** | max_retries, backoff_strategy, interval | `policy_id` (PK), FK `merchant_id` | 1:N aplicado a Attempt | — | Enquanto ativo | — |
| **CommunicationEvent** | channel, sent_at, opened_at, status | `event_id` (PK), FK `intent_id` | N:1 com Intent | Telefone/e-mail do cliente | 2 anos | Consentimento de canal (opt-in) |
| **Settlement** | gross_amount, fee, net_amount, settled_at | `settlement_id` (PK), FK `route_id` | 1:1 com PaymentRoute | Valor financeiro | 5 anos (fiscal) | — |
| **Reconciliation** | matched, discrepancy_amount, reconciled_at | `reconciliation_id` (PK), FK `settlement_id` | 1:1 com Settlement | — | 5 anos | — |
| **AuditLog** | actor, action, before/after, timestamp, hash_prev | `log_id` (PK) | N:1 com qualquer entidade auditada | Pode conter PII referenciada | 5–10 anos conforme exigência regulatória | Log é a prova de conformidade; acesso restrito por least privilege |
| **ModelDecision** | model_version, input_features_hash, output, latency | `decision_id` (PK), FK `intent_id` | 1:1 com DecisionScore | Hash de features (não valor bruto) | 2 anos (MLOps) + amostragem 5 anos (auditoria) | Explicabilidade e não-discriminação |
| **MerchantPolicy** | weights, max_exposure, allowed_methods | `policy_id` (PK), FK `merchant_id` | 1:N aplicado a Intent | — | Enquanto ativo + histórico versionado | — |
| **CustomerPreference** | preferred_method, preferred_channel, opt_outs | `preference_id` (PK), FK `customer_id` | 1:1 com Customer | Preferência é dado comportamental | Enquanto cliente ativo | Direito de portabilidade e exclusão (art. 18 LGPD) |

Princípios transversais de LGPD: **minimização** (o motor de decisão recebe *features* derivadas, não PII bruta sempre que possível), **finalidade** (dado de risco não é reaproveitado para marketing sem nova base legal), **direito à explicação** (toda decisão automatizada relevante tem `DecisionScore` consultável pelo titular ou pelo estabelecimento em seu nome), **retenção proporcional** (dado fiscal 5 anos; dado comportamental de preferência apagável a pedido, exceto o necessário para obrigação legal).

---

## 9. IA e modelos analíticos

| Modelo | Objetivo | Input features (exemplos) | Output | Métrica de qualidade | Retreino | Explicabilidade | Fallback determinístico |
|---|---|---|---|---|---|---|---|
| **Propensão ao pagamento** | Prever probabilidade de pagamento dentro do prazo | histórico do cliente, valor, prazo, segmento | probabilidade [0,1] | AUC-ROC, Brier score | Semanal | SHAP por feature | Média histórica do segmento |
| **Melhor meio de pagamento** | Ranquear meios por score composto | ver seção 5 | ranking + score | NDCG@3, taxa de acerto do top-1 | Semanal | Pesos + contribuição por dimensão | Regra fixa por segmento (ex.: "B2B > boleto") |
| **Risco de fraude** | Detectar transação fraudulenta antes da execução | device fingerprint, velocity, geolocalização | score de fraude [0,1] | Precision@threshold, recall | Diário (dados antifraude mudam rápido) | Top features contribuintes | Regras de velocity check determinísticas |
| **Risco de chargeback** | Prever probabilidade de contestação pós-pagamento | histórico de disputas, ticket médio, canal | probabilidade [0,1] | AUC-ROC, calibração | Mensal | SHAP | Limite fixo por valor/segmento |
| **Probabilidade de atraso/inadimplência** | Prever atraso de pagamento em recorrência/boleto | histórico de pagamento, dias de atraso médio | dias esperados de atraso | MAE, calibração | Mensal | Feature importance | Média móvel do cliente |
| **Melhor canal de comunicação** | Escolher canal com maior taxa de abertura/ação | histórico de engajamento por canal | canal recomendado | taxa de conversão por canal (teste A/B) | Mensal | Ranking simples explicável | Canal padrão configurado pelo merchant |
| **Melhor horário de cobrança** | Escolher janela de envio com maior taxa de resposta | histórico de horário de pagamento do cliente | janela recomendada | taxa de resposta por janela | Mensal | Distribuição histórica | Horário comercial padrão |
| **Retry inteligente** | Otimizar timing e número de tentativas | motivo da falha, histórico de retry do cliente | política de retry (intervalo, tentativas) | taxa de sucesso do retry, taxa de fadiga (opt-out) | Mensal | Regra + ajuste aprendido | Backoff exponencial fixo |
| **Fallback** | Escolher o melhor meio alternativo dado falha do 1º | meio que falhou, motivo, contexto | meio alternativo ranqueado | taxa de sucesso do fallback | Mensal | Reaproveita explicação do scoring principal | Ordem de fallback pré-configurada por política |
| **Otimização de custo** | Minimizar custo total mantendo conversão mínima | tabela de custo por provedor, elasticidade de conversão por meio | alocação ótima | custo médio realizado vs. teórico ótimo | Mensal | Decomposição de custo por componente | Meio de menor tarifa nominal |
| **Previsão de liquidação** | Estimar data/hora real de liquidação | meio, provedor, histórico de SLA do provedor | data/hora estimada | MAE em horas | Mensal | SLA declarado do provedor | SLA contratual do provedor |
| **Recomendação de antecipação** | Sugerir quando antecipar recebíveis | posição de caixa declarada, custo de antecipação, prazo do recebível | recomendar/não recomendar + economia estimada | acurácia da recomendação vs. decisão do CFO | Mensal | Comparação custo de capital vs. custo de antecipação | Regra: antecipar se custo de antecipação < custo de capital declarado |
| **Detecção de anomalia operacional** | Detectar padrão fora do normal (queda de conversão, pico de erro de provedor) | séries temporais de métricas operacionais | alerta + score de anomalia | falsos positivos por semana | Contínuo (streaming) | Desvio vs. baseline explicado | Threshold estático por métrica |

**Riscos de viés (transversal):** modelos treinados em dados históricos podem penalizar segmentos com menos histórico de dados (pequenos estabelecimentos, clientes novos) — mitigação via *fairness testing* por segmento (ver seção 21) e piso de exploração (não deixar o modelo "condenar" um cliente novo a sempre boleto por falta de dado; usar bandit/exploração controlada).

**Monitoramento e drift (transversal):** todo modelo em produção tem dashboard de PSI (Population Stability Index) para drift de input e monitoramento de métrica de qualidade em produção vs. baseline de treino; alerta automático se PSI > 0.2 ou métrica cair > 10% relativo.

**Guardrails (transversal):** nenhum modelo decide sozinho fora dos limites de `MerchantPolicy`; toda saída de modelo passa pelo motor de regras antes de virar ação.

---

## 10. Agentes de IA

| Agente | Responsabilidade | Ferramentas | Dados acessados | Decisões permitidas | Decisões proibidas | Logs obrigatórios | Escalação humana |
|---|---|---|---|---|---|---|---|
| **Orquestrador de Recebimento** | Coordenar o fluxo entre os demais agentes e decidir a ação final | Chama os demais agentes; motor de regras | Intent, contexto consolidado | Selecionar rota dentro do modo de operação vigente | Executar acima do limite de exposição do modo | Toda decisão final com trace completo | Se confiança < threshold do modo |
| **Agente de Risco** | Avaliar fraude e chargeback antes do roteamento | API antifraude, RiskAssessment | Histórico de risco do cliente/merchant | Recomendar bloqueio/permissão de meio | Aprovar transação acima do limite de exposição sem revisão | Score e motivo de cada avaliação | Score em zona cinzenta (nem claramente aprovado nem bloqueado) |
| **Agente de Custo** | Calcular custo total por opção | Tabela de custo por provedor, MerchantPolicy | Tarifário, histórico de custo realizado | Recomendar meio de menor custo dentro dos demais limites | Ignorar `max_cost` declarado pelo merchant | Cálculo de custo por opção | Divergência > 20% entre custo estimado e realizado |
| **Agente de Liquidez** | Avaliar necessidade de caixa e prazo de liquidação | Posição de caixa declarada, SLA de provedores | `liquidity_need`, histórico de settlement | Priorizar meios de liquidação mais rápida | Recomendar antecipação sem sinalizar custo ao merchant | Toda recomendação de liquidez/antecipação | Necessidade de caixa crítica declarada (ação urgente) |
| **Agente de Experiência do Cliente** | Maximizar conveniência para o cliente pagador | CustomerPreference, histórico de canal | Preferência declarada e comportamental | Priorizar meio/canal preferido dentro dos limites de risco/custo | Contatar cliente fora da janela/canal consentido | Toda escolha de canal e meio orientada a experiência | Cliente sinaliza reclamação/opt-out |
| **Agente de Comunicação** | Disparar e monitorar envio da cobrança | Provedores de canal (WhatsApp, SMS, e-mail) | Dados de contato, CommunicationEvent | Enviar, reenviar dentro da política de frequência | Enviar mais que o limite de frequência anti-spam | Todo envio, entrega, abertura | Falha de entrega recorrente (3x) |
| **Agente de Conciliação** | Casar pagamentos confirmados com liquidações | Extrato de provedores, Settlement | Dados financeiros da transação | Marcar como conciliado automaticamente dentro da tolerância | Ajustar valor divergente sem revisão humana | Toda conciliação automática e exceção | Divergência acima da tolerância configurada |
| **Agente de Auditoria** | Garantir rastreabilidade e imutabilidade | AuditLog, hash chain | Todos os eventos de decisão e mutação | Registrar; nunca decide sobre o negócio | Alterar ou remover registro histórico | Auto-registro de sua própria operação | Tentativa de adulteração detectada |
| **Agente de Explicabilidade** | Gerar explicação de cada decisão para diferentes públicos | DecisionScore, ModelDecision | Pesos, alternativas descartadas | Gerar texto explicativo por persona (seção 19) | Omitir informação relevante para o titular do dado | Toda explicação gerada e para quem foi servida | Pedido formal de explicação (LGPD art. 20) sem resposta satisfatória automatizada |
| **Agente de Monitoramento Operacional** | Detectar anomalia de provedor/modelo/negócio | Métricas de observabilidade, PSI de drift | Métricas agregadas, não PII | Acionar circuit breaker de provedor | Pausar operação de merchant inteiro sem alçada | Todo alerta e ação de circuit breaker | Anomalia sustentada > 15 min ou impacto financeiro estimado > limite |

Guardrail transversal a todos os agentes: nenhum agente tem acesso de escrita direto a `Settlement` ou a credenciais de provedor — toda ação financeira passa pelo Serviço de Roteamento de Pagamento, que aplica os limites de `MerchantPolicy` como última linha de defesa, independente do que os agentes recomendem.

---

## 11. Guardrails, risco e compliance

| Risco | Causa | Impacto | Prob. | Severidade | Controle preventivo | Controle detectivo | Controle corretivo | Dono | Métrica de monitoramento |
|---|---|---|---|---|---|---|---|---|---|
| Violação de LGPD (uso indevido de dado) | Feature engineering usa PII além do necessário | Multa ANPD, dano reputacional | Média | Alta | Minimização por design; revisão de DPIA antes de novo modelo | Auditoria trimestral de features em uso | Retreino sem a feature; notificação ao titular se aplicável | Risk Officer / DPO | % de features classificadas e revisadas |
| Falta de consentimento de canal | Comunicação enviada sem opt-in válido | Reclamação, multa, bloqueio de canal (WhatsApp Business) | Média | Média | Opt-in obrigatório no cadastro do cliente | Auditoria de CommunicationEvent vs. consentimento registrado | Suspensão do canal para o cliente + pedido de novo consentimento | Risk Officer | Taxa de envio sem consentimento registrado (deve ser 0) |
| Vazamento de dados sensíveis | Falha de segregação/criptografia | Vazamento de dado financeiro/pessoal | Baixa | Crítica | Criptografia em repouso/trânsito; tokenização de cartão | Monitoramento de acesso anômalo (DLP) | Plano de resposta a incidente; notificação ANPD em 72h se aplicável | Distinguished Engineer / CISO | Nº de acessos fora de padrão por período |
| Fraude no roteamento | Cliente/ator malicioso explora meio de menor triagem | Perda financeira direta | Média | Alta | Agente de Risco com piso mínimo de triagem por meio | Monitoramento de taxa de fraude por meio/segmento | Bloqueio automático de meio/segmento + revisão manual | Risk Officer | Taxa de fraude confirmada por meio |
| Chargeback elevado | Roteamento para cartão em segmento de alto risco sem triagem adequada | Custo direto + possível suspensão pela adquirente | Média | Alta | `max_risk` na política + Agente de Risco | Dashboard de chargeback por segmento | Ajuste de política + reforço de antifraude | Risk Officer / CPO | Taxa de chargeback por segmento vs. benchmark |
| Cobrança abusiva (excesso de retry/spam) | RetryPolicy mal configurada ou modelo de retry agressivo | Dano à experiência, reclamação, dano reputacional do merchant | Média | Média | Limite duro de frequência de contato (anti-spam) | Monitoramento de taxa de reclamação por merchant | Pausa automática de régua + revisão de política | UX Lead / Risk Officer | Nº de reclamações por 1.000 cobranças |
| Discriminação algorítmica | Modelo aprende correlação espúria com proxy de classe social/geografia | Dano reputacional, risco regulatório, decisão injusta | Baixa | Alta | Fairness testing por segmento antes de promoção a produção | Auditoria periódica de outcome por segmento demográfico proxy | Reversão para regra determinística + retreino sem feature enviesada | Data/AI Lead / Risk Officer | Disparidade de taxa de aprovação/roteamento entre segmentos |
| Decisão opaca (sem explicação) | Falha do Agente de Explicabilidade ou modelo não instrumentado | Não conformidade LGPD, perda de confiança do merchant | Baixa | Alta | Toda decisão gera `DecisionScore` obrigatoriamente (bloqueante) | Auditoria de decisões sem explicação disponível | Reprocessamento com geração forçada de explicação | Data/AI Lead | % de decisões com explicação disponível (meta 100%) |
| Erro de roteamento | Bug no motor de regras/scoring | Cobrança pelo meio errado, custo ou risco indevido | Média | Média | Teste de regressão de regras + canário em produção | Alerta de desvio estatístico do padrão de roteamento | Rollback de versão do motor + reprocessamento | Distinguished Engineer | Taxa de decisões revertidas manualmente |
| Falha de provedor (Pix/cartão/boleto indisponível) | Instabilidade externa | Cobrança não realizada, atraso de recebimento | Média | Média | Circuit breaker + fallback automático | Health check contínuo por provedor | Ativação de fallback + comunicação proativa ao merchant | Distinguished Engineer | Uptime por provedor, taxa de fallback acionado |
| Duplicidade de cobrança | Reprocessamento sem idempotência | Cliente cobrado 2x, dano reputacional grave | Baixa | Crítica | Idempotency-key obrigatória em toda API mutável | Reconciliação cruzada por `order_id`/`intent_id` | Estorno automático + notificação | Distinguished Engineer | Nº de cobranças duplicadas detectadas (meta 0) |
| Falha de liquidação | Erro no provedor ou no matching de settlement | Merchant não recebe valor esperado no prazo | Baixa | Alta | SLA contratual monitorado + alerta de atraso | Dashboard de settlement pendente > SLA | Escalação ao provedor + comunicação ao merchant | CPO / Distinguished Engineer | % de settlements dentro do SLA |
| Erro de conciliação | Falha de matching automático | Diferença não identificada, retrabalho manual | Média | Baixa | Tolerância configurável + regra de matching robusta | Fila de exceções de conciliação monitorada | Conciliação manual assistida + ajuste de regra | CFO / Distinguished Engineer | Taxa de conciliação automática |
| Dano reputacional | Qualquer um dos riscos acima materializado publicamente | Perda de clientes, dano de marca | Baixa | Alta | Todos os controles acima + comunicação transparente | Monitoramento de menções/reclamações | Plano de comunicação de crise | CPO / CEO | NPS, taxa de churn de merchant |
| Falha de auditoria | Log incompleto ou adulterável | Impossibilidade de provar conformidade | Baixa | Alta | Log append-only com hash encadeado desde o dia 1 | Verificação periódica de integridade da cadeia de hash | Reconstrução a partir de backup + relato de incidente | Risk Officer | % de eventos auditáveis registrados |
| Não conformidade regulatória (BACEN, arranjos de pagamento) | Motor atua como iniciador/roteador sem enquadramento correto | Sanção regulatória, obrigação de licenciamento | Baixa | Crítica | Parecer jurídico prévio sobre enquadramento regulatório do modelo de operação | Revisão jurídica periódica de mudanças normativas | Ajuste de modelo de negócio/licenciamento | CFO / Risk Officer | Revisão jurídica registrada por trimestre |
| Dependência excessiva de terceiros | Concentração em poucos provedores/PSPs | Risco de continuidade se provedor sair do ar ou encerrar parceria | Média | Média | Multiadquirência/multi-PSP desde o design | Monitoramento de concentração de volume por provedor | Ativação de provedor alternativo pré-homologado | Distinguished Engineer / CFO | % de volume no maior provedor único |
| Ruptura de continuidade de negócio | Incidente de infraestrutura maior (região inteira) | Indisponibilidade total do motor | Baixa | Crítica | DR multi-região, runbook testado | Simulação de disaster recovery trimestral | Failover para região secundária | Distinguished Engineer | RTO/RPO medido em simulação |

Nota jurídica relevante (premissa explícita): o enquadramento regulatório do Orchestrator perante o BACEN depende de **como** ele participa do fluxo financeiro. Se apenas orienta/roteia sem tocar recursos (não é instituição de pagamento, não detém saldo), o enquadramento tende a ser mais leve (prestador de serviço tecnológico). Se passar a deter saldo, fazer split de valores diretamente ou atuar como iniciador de pagamento, entra no perímetro de arranjos de pagamento e Open Finance, exigindo autorização/registro no BACEN. **Esta é uma premissa que precisa de validação jurídica formal antes do MVP tocar dinheiro diretamente** — recomendação: MVP opera via provedores já licenciados (PSP, adquirente, banco), sem o Orchestrator deter saldo.

---

## 12. Estratégia de MVP (90 dias)

### Escopo do MVP
- Criação de intenção via API + painel simples.
- Recomendação (não execução autônoma) entre **Pix, cartão à vista e boleto**.
- Ranking baseado em custo, conversão esperada e prazo — score determinístico + modelo estatístico simples (não deep learning).
- Fallback simples pré-configurado (ex.: Pix expirado → boleto).
- Explicação textual da decisão (template + variáveis, não geração livre).
- Dashboard de performance (conversão, custo, tempo até pagamento).
- Auditoria básica (log append-only das decisões).
- **Modo recomendação obrigatório** — toda execução exige aprovação humana.

### Fora do MVP
Débito, carteira digital, recorrência, split, retry inteligente com IA, modo automático/autopilot, múltiplos provedores por meio, antecipação, modelo de propensão com ML avançado, canais múltiplos de comunicação.

### Hipóteses a validar
1. Estabelecimentos aceitam declarar "objetivo" em vez de escolher meio manualmente.
2. O ranking baseado nas 3 dimensões (custo/conversão/prazo) já gera ganho perceptível sem IA sofisticada.
3. Explicação simples é suficiente para gerar confiança no piloto.
4. A integração com Pix/cartão/boleto via provedores existentes é operacionalmente viável em 90 dias.

### Funcionalidades obrigatórias vs. opcionais

| Obrigatório | Opcional (nice-to-have no MVP) |
|---|---|
| API de intenção, recomendação, execução, status | Painel white-label |
| Pix + cartão + boleto | Link de pagamento como 4º meio |
| Fallback simples (1 nível) | Fallback com 2+ níveis |
| Dashboard de conversão/custo/tempo | Dashboard de chargeback (pode ser manual no MVP) |
| Auditoria básica | Explicação por múltiplas personas (seção 19 completa) |

### Integrações mínimas
1 PSP de Pix, 1 adquirente de cartão, 1 emissor/agregador de boleto, 1 provedor de antifraude básico (mesmo que via regras simples do próprio adquirente).

### Dados mínimos
Histórico de transações do merchant piloto (mínimo 3–6 meses, se existir) para calibrar baseline de comparação; caso não exista, iniciar com regra determinística pura e coletar dados durante o piloto.

### Métricas de sucesso do MVP
- ≥ 3 p.p. de ganho de conversão vs. baseline em pelo menos 4 dos 5–8 merchants piloto.
- 0 incidentes de duplicidade de cobrança ou falha de liquidação.
- 100% das decisões com explicação disponível.
- Tempo de resposta da recomendação < 2s p95.

### Critérios de go/no-go (para seguir a fase 2)
- **Go** se: ganho de conversão validado, 0 incidentes críticos, NPS piloto ≥ 40, ao menos 2 merchants dispostos a expandir volume.
- **No-go/pivot** se: ganho não se sustenta sem intervenção manual constante, ou risco operacional (duplicidade, falha de liquidação) ocorreu.

### Riscos do MVP
Integração de provedor atrasar prazo; dado histórico do merchant insuficiente para calibrar baseline; resistência do time financeiro do merchant em "confiar" na recomendação.

### Plano de piloto
5–8 estabelecimentos, prazo 90 dias, acompanhamento semanal com o time financeiro de cada merchant, ajuste de política de forma colaborativa (não silenciosa).

### Perfil ideal de clientes piloto
- Faturamento recorrente mensal (facilita comparação de baseline).
- Já usa 2+ meios de pagamento hoje (tem "o que orquestrar").
- Time financeiro disponível para validar recomendações semanalmente.
- Volume médio (não tão pequeno que o ganho seja imperceptível, não tão grande que o risco de erro seja inaceitável no início).

### Critérios para expansão
Sair de 5–8 para 30–50 merchants somente após: modo assistido validado com pelo menos 3 merchants piloto por 60 dias consecutivos sem incidente, e processo de onboarding de provedor replicável (não artesanal).

---

## 13. Roadmap

| Fase | Prazo | Entregas | Capacidade técnica | Capacidade de IA | Integrações | Métricas-chave | Riscos | Dependências | Critério de maturidade |
|---|---|---|---|---|---|---|---|---|---|
| **MVP** | 0–90 dias | Recomendação Pix/cartão/boleto, dashboard básico, auditoria | Core API, motor de regras, fallback simples | Score determinístico + estatístico simples | 1 PSP Pix, 1 adquirente, 1 boleto | Conversão +3p.p., 0 incidentes | Atraso de integração | Parecer jurídico de enquadramento regulatório | Ver seção 12 |
| **Piloto expandido** | 3–6 meses | Modo assistido, split simples, retry com regra aprendida | Circuit breaker, observabilidade completa, feature store inicial | Modelo de propensão v1, retreino mensal | 2º provedor por meio (início multiadquirência) | Conversão +5p.p., custo -10% | Regras assistidas mal calibradas | MVP validado (go) | 3 merchants em modo assistido 60 dias sem incidente |
| **Automação assistida** | 6–12 meses | Modo automático com limites, explicabilidade multi-persona, antecipação (recomendação) | Model registry, MLOps completo, agentes especializados (seção 10) | Modelos de risco/chargeback/canal em produção | Antifraude dedicado, ERP/CRM bidirecional | Chargeback -15%, esforço operacional -30% | Autopilot exceder limite por falha de guardrail | Piloto expandido validado | 90 dias em modo assistido sem exceção > 2% |
| **Autopilot controlado** | 12–18 meses | Modo automático como padrão para merchants maduros, retry/fallback totalmente orientados a IA | Arquitetura celular madura, DR multi-região testado | Modelo de retry/fallback adaptativo, detecção de anomalia em produção | Marketplace embrionário (3+ provedores por meio) | Disponibilidade 99.9%, decisões automáticas > 60% do volume | Concentração de erro sistêmico em escala | Auditoria externa aprovada | Auditoria de compliance formal concluída |
| **Marketplace e otimização avançada** | 18–24 meses | Marketplace de provedores com roteamento por SLA/custo em tempo real, otimização de portfólio de recebíveis | Roteamento dinâmico multiprovedor, negociação de custo automatizada | Otimização multi-objetivo avançada (portfolio-level, não só por transação) | N provedores por meio, Open Finance para dados de conta do pagador | Custo transacional otimizado -25% vs. baseline original | Complexidade de governança de múltiplos parceiros | Modelo de monetização de marketplace definido (seção 15) | Receita de revenue-share com provedores > 0 |

---

## 14. Business case

### Premissas base (por estabelecimento médio)

- Volume mensal de recebíveis: **R$ 10.000.000**
- Conversão de cobrança atual: **82%**
- Custo transacional médio atual: **2,3%** (mix atual de meios)
- Chargeback atual: **0,35%** do volume em cartão
- Esforço operacional de conciliação: **40 horas/mês** de analista (custo-hora R$ 60)

### Fórmulas

```
Receita_incremental_por_conversao = Volume × (Δ conversão em p.p. / 100)
Economia_custo_transacional       = Volume × (custo_atual% − custo_novo%)
Economia_chargeback                = Volume_cartão × (Δ chargeback%)
Economia_operacional               = Δ horas/mês × custo-hora × 12
Ganho_antecipacao                  = Volume_antecipado × (custo_capital_evitado − custo_antecipacao)
Receita_total_incremental_anual    = 12 × (Receita_incremental_por_conversao + Economia_custo_transacional
                                      + Economia_chargeback + Economia_operacional) + Ganho_antecipacao
ROI                                 = (Receita_total_incremental_anual − Custo_total_anual) / Custo_total_anual
Payback_meses                       = Custo_implantação / (Receita_total_incremental_anual / 12)
```

### Cenários (por estabelecimento médio, ano 1)

| Cenário | Δ conversão | Δ custo transacional | Δ chargeback | Δ esforço operacional | Receita incremental anual | Custo implantação + operação (ano 1) | ROI ano 1 | Payback |
|---|---|---|---|---|---|---|---|---|
| **Conservador** | +2 p.p. | -0,3 p.p. | -0,05 p.p. | -20% | R$ 2,4M + R$ 0,36M + R$ 0,02M + R$ 0,07M ≈ **R$ 2,85M** | R$ 0,9M | ~217% | ~4 meses |
| **Base** | +4 p.p. | -0,6 p.p. | -0,10 p.p. | -35% | R$ 4,8M + R$ 0,72M + R$ 0,04M + R$ 0,12M ≈ **R$ 5,68M** | R$ 1,1M | ~416% | ~2,3 meses |
| **Arrojado** | +7 p.p. | -1,0 p.p. | -0,18 p.p. | -50% | R$ 8,4M + R$ 1,2M + R$ 0,08M + R$ 0,17M ≈ **R$ 9,85M** | R$ 1,3M | ~658% | ~1,6 meses |

> Nota de premissa: os números acima são **por estabelecimento-tipo de R$ 10M/mês**, para ilustrar a mecânica do modelo. Para o business case da empresa dona do produto (nós), a receita real vem da **monetização sobre esse valor** (seção 15), não do valor incremental capturado pelo merchant — ou seja, o merchant captura a economia acima, e nós capturamos uma fração dela via fee. Isso deve ser recalibrado com dados reais do piloto antes de qualquer projeção ser levada ao board como compromisso.

### Custo de implantação (visão do produto, não do merchant) — ordem de grandeza

- Squad multidisciplinar (7 squads da seção 20) por 12 meses: maior componente de custo, dimensionar em plano de headcount à parte.
- Infraestrutura cloud + provedores (Pix/cartão/boleto/antifraude): custo variável por transação, negociar volume mínimo.
- Certificações/compliance (auditoria PCI se tocar dado de cartão, parecer jurídico regulatório): custo fixo relevante no ano 1.

---

## 15. Monetização

| Modelo | Vantagens | Desvantagens | Melhor público | Risco comercial | Complexidade operacional |
|---|---|---|---|---|---|
| **Fee por transação orquestrada** | Previsível, escala com uso, fácil de explicar | Pode ser visto como custo adicional sobre o MDR já pago | Todos os merchants | Sensibilidade a preço em segmentos de margem apertada | Baixa |
| **% sobre economia gerada** (success fee) | Alinha incentivo — só ganhamos se o merchant ganha | Exige medição confiável de baseline/contrafactual, contestável | Merchants médios/grandes com dado histórico robusto | Disputa sobre "quanto foi economizado de fato" | Alta (precisa de baseline auditável) |
| **SaaS mensal por estabelecimento** | Receita recorrente previsível, simples de vender | Não escala com valor entregue em merchants grandes | PMEs, merchants com volume baixo/médio | Churn se valor percebido cair | Baixa |
| **Plano por volume (tiers)** | Captura mais valor de merchants grandes sem success fee complexo | Pode desincentivar crescimento de uso perto do limite do tier | Merchants em crescimento | Necessidade de renegociação frequente de tier | Média |
| **Revenue share com provedores** (Pix PSP, adquirente, boleto) | Monetiza o lado do provedor também (2 lados do marketplace) | Conflito de interesse percebido (favorecer provedor que paga mais) | Fase de marketplace (18–24 meses) | Reputacional se roteamento parecer viesado por comissão | Alta — exige guardrail duro de que comissão não entra no score de decisão |
| **Fee por recuperação de pagamento** (sucesso de retry/fallback em inadimplência) | Alinhado a resultado, fácil de justificar | Só se aplica a uma fração do volume (cobrança em atraso) | Merchants com régua de cobrança relevante | Pode incentivar cobrança agressiva se mal desenhado | Média |
| **Premium analytics** (benchmarking de mercado, insights avançados) | Alta margem, diferenciação | Requer massa crítica de dados agregados para ser valioso | Merchants grandes, decisão de CFO | Baixo, mas depende de volume de dados agregados | Baixa |
| **Autopilot pago** (fee adicional para modo automático) | Monetiza a maturidade — cobra mais por menos operação manual do cliente | Pode frear adoção de autopilot se percebido como upsell forçado | Merchants maduros (fase 3–4 do roadmap) | Médio | Média |
| **Módulo antifraude premium** | Alta disposição a pagar (risco é dor cara) | Exige parceria/licenciamento de motor antifraude robusto | Merchants de alto ticket/alto risco | Dependência de parceiro terceiro | Média-alta |
| **Módulo forecast/caixa premium** | Complementa a proposta de liquidez, alta relevância para CFO | Concorre com ferramentas de gestão financeira já estabelecidas | Merchants médios/grandes com necessidade de gestão de caixa ativa | Médio | Média |

**Recomendação de sequenciamento**: iniciar com **SaaS mensal + fee por transação** (previsível, fácil de vender no piloto), evoluir para **% sobre economia gerada** quando houver baseline auditável robusto (pós fase 2), introduzir **revenue share** apenas na fase de marketplace com guardrail contratual e técnico de que comissão de provedor nunca entra como termo no `Score(o)`.

---

## 16. Experiência do usuário

| Tela | Objetivo | Usuário | Campos principais | Ações | Métricas exibidas | Estados de erro | Decisão importante |
|---|---|---|---|---|---|---|---|
| **Criar intenção de recebimento** | Declarar o que precisa ser cobrado | Financeiro do merchant | Cliente, valor, prazo, objetivo, meios permitidos/proibidos | Salvar, salvar como recorrente | — | Cliente não encontrado, valor inválido, prazo no passado | Objetivo (conversão/custo/risco/liquidez/experiência) |
| **Configurar política do estabelecimento** | Definir pesos e limites padrão | Gestor financeiro/CFO | Pesos por dimensão, `max_exposure`, meios habilitados globalmente | Salvar política, criar política por segmento de cliente | Simulação "como isso teria afetado os últimos 30 dias" | Pesos não somam critério válido, limite de exposição abaixo do necessário | Política default vs. política por segmento |
| **Ver recomendação** | Apresentar o ranking e a opção sugerida | Financeiro/atendimento | Meio recomendado, score, alternativas, custo/conversão/prazo esperados | Aprovar, escolher alternativa, rejeitar com motivo | Score, confiança | Nenhuma opção elegível (todas bloqueadas por regra) | Aceitar ou sobrescrever recomendação |
| **Ver explicação da decisão** | Justificar o porquê | Financeiro/auditoria | Texto explicativo, pesos aplicados, opções descartadas e motivo | Exportar para auditoria | — | Explicação indisponível (bloqueante — não deveria ocorrer) | — |
| **Acompanhar tentativas** | Rastrear tentativas de cobrança de uma intenção | Financeiro/atendimento | Linha do tempo de tentativas, status, canal usado | Forçar retry manual, cancelar intenção | Tempo decorrido, nº de tentativas | Provedor indisponível | Intervir manualmente ou aguardar automação |
| **Configurar fallback** | Definir ordem de meios alternativos | Financeiro/operação | Sequência de meios, condição de gatilho (expiração, recusa) | Reordenar, ativar/desativar fallback automático | Taxa histórica de sucesso por fallback | Sequência circular/inválida | Nível de automação do fallback |
| **Configurar limites de risco** | Definir exposição máxima e apetite de risco | Risk officer do merchant | `max_risk`, limite de valor por modo, segmentos bloqueados | Salvar, aprovar exceção pontual | Exposição atual vs. limite | Limite conflita com política de conversão | Apetite de risco por segmento |
| **Dashboard de performance** | Visão geral de conversão/tempo/fallback | Gestor financeiro/board | Filtros por período, meio, segmento | Exportar relatório | Conversão, tempo até pagamento, taxa de fallback | Dado incompleto no período | — |
| **Dashboard de custo** | Visão de custo transacional | CFO | Custo por meio, custo evitado (economia) | Comparar cenários de política | Custo médio %, economia acumulada | — | Ajustar `max_cost` global |
| **Dashboard de liquidação** | Visão de prazo e valor liquidado | Financeiro/tesouraria | Valores a liquidar, liquidados, atrasados | Filtrar por provedor | % dentro do SLA, valor pendente | Settlement atrasado além do SLA | Escalar ao provedor |
| **Dashboard de conciliação** | Visão de matching automático vs. exceção | Financeiro/contabilidade | Lista de exceções, motivo da divergência | Resolver manualmente, marcar como investigado | Taxa de conciliação automática | Divergência não resolvida > X dias | Aprovar ajuste manual |
| **Alertas operacionais** | Notificar anomalia/incidente em tempo real | Operação/Distinguished Engineer on-call | Tipo de alerta, severidade, provedor/merchant afetado | Reconhecer, escalar, ver runbook | Tempo até reconhecimento, tempo até resolução | Alerta não reconhecido dentro do SLA | Acionar war room |

---

## 17. Observabilidade e operação

### SLIs / SLOs / SLAs

| Serviço | SLI | SLO interno | SLA contratual (merchant) |
|---|---|---|---|
| Core de decisão (recomendação) | Latência p95 | < 2s | < 3s |
| Execução de rota | Disponibilidade | 99.9% | 99.5% |
| Webhook de confirmação | Latência de processamento | < 5s | < 30s |
| Conciliação | Taxa de conciliação automática | > 90% | Reporte D+1 |

### Logs, métricas, traces
- **Logs estruturados** (JSON) com `intent_id`/`trace_id` correlacionável em todos os serviços.
- **Métricas**: contadores e histogramas por serviço, exportados para sistema de séries temporais.
- **Traces distribuídos**: um trace por intenção, atravessando motor de regras, scoring, roteamento, provedor externo.

### Alertas e runbooks
Cada alerta crítico (circuit breaker acionado, taxa de erro de provedor > threshold, drift de modelo > threshold, fila de conciliação crescendo) tem um runbook associado com passos de diagnóstico e ação imediata, versionado junto ao código.

### Monitoramento específico
- **Provedores**: health check ativo + passivo (taxa de erro real de tráfego), painel de status por provedor.
- **Modelo**: PSI de drift, métrica de qualidade em produção, % de decisões de baixa confiança.
- **Fraude**: taxa de fraude confirmada por meio/segmento em janela móvel.
- **Conciliação**: idade da fila de exceções, valor total em disputa.

### Gestão de incidentes
- Severidade 1 (impacto financeiro direto ou indisponibilidade total): war room imediato, comunicação a merchants afetados em até 30 min.
- Severidade 2/3: tratamento assíncrono via fila de incidentes, SLA de resposta por severidade.

### Plano de rollback e contingência
- Toda versão do motor de regras/scoring é deployada com **canário** (5% do tráfego) antes de 100%; rollback automático se métrica de erro subir acima do baseline.
- Contingência de indisponibilidade de provedor: fallback automático + modo "somente registro" (aceita a intenção, mas não executa) se todos os provedores de um meio estiverem fora.

### Métricas exemplo (painel operacional)
Taxa de conversão por meio · custo médio por recebimento · tempo médio até pagamento · taxa de fallback · taxa de retry bem-sucedido · taxa de erro por provedor · taxa de chargeback · taxa de fraude · taxa de conciliação automática · latência da API (p50/p95/p99) · disponibilidade · % decisões com baixa confiança · PSI de drift por modelo.

### Pós-incidente
Todo incidente de severidade 1/2 gera post-mortem sem culpa (blameless), com ação corretiva rastreada até fechamento.

---

## 18. Segurança

- **Autenticação**: OAuth2/mTLS entre serviços internos; API keys + assinatura de request para integradores externos.
- **Autorização**: RBAC por papel (financeiro, risco, auditoria, admin) e por `merchant_id` (isolamento multi-tenant).
- **Criptografia em trânsito**: TLS 1.2+ obrigatório em todas as chamadas.
- **Criptografia em repouso**: AES-256 para dados sensíveis (PII, valores financeiros) em banco e data lake.
- **Gestão de segredos**: vault dedicado (nunca segredo em código/config versionado).
- **Tokenização**: dado de cartão nunca armazenado em claro — tokenização via adquirente/gateway certificado PCI.
- **PCI-DSS**: aplicável ao componente que toca dado de cartão; arquitetura desenhada para reduzir escopo PCI ao mínimo (usar campo hospedado/tokenização do adquirente, evitar que o Orchestrator veja PAN).
- **Proteção contra replay**: `Idempotency-Key` + timestamp + nonce em webhooks recebidos.
- **Idempotência**: end-to-end em toda operação mutável, conforme seção 6.
- **Assinatura de webhook**: HMAC-SHA256 validado antes de qualquer processamento de webhook de entrada.
- **Rate limiting**: por `merchant_id` e por IP, com backoff para clientes que excedem limite.
- **Proteção contra abuso**: detecção de padrão anômalo de criação de intenções (possível teste de cartão/fraude).
- **Segregação de dados**: isolamento lógico (e, quando exigido por contrato, físico) entre merchants.
- **Auditoria**: log imutável de toda ação sensível (seção 6/11).
- **Least privilege**: cada serviço/agente com o mínimo de escopo de dado e ação necessário (seção 10).
- **Gestão de chaves**: rotação periódica, HSM/KMS gerenciado para chaves críticas.
- **Zero trust**: nenhuma chamada interna confiável por rede/localização — sempre autenticada e autorizada explicitamente.

---

## 19. Explicabilidade

Toda decisão responde: por que este meio foi escolhido, quais opções foram descartadas e por quê, custo/conversão/risco/prazo esperados, quais regras da política do merchant foram aplicadas, o que mudaria com outro objetivo, e o que o sistema aprendeu com o resultado real (retroalimentação).

**Exemplo para o CFO:**
> "Em julho, 89% dos recebimentos foram via Pix, reduzindo o custo transacional médio de 2,3% para 1,6% — uma economia de R$ 70 mil no mês, sem queda de conversão."

**Exemplo para o time financeiro:**
> "Este cliente (Cliente 4471) recebeu recomendação de Pix porque tem histórico de pagamento em até 2h via Pix nas últimas 6 cobranças, e o boleto teria adicionado 2 dias ao prazo de recebimento sem ganho de conversão esperado."

**Exemplo para o time de atendimento:**
> "O cliente recebeu boleto, não Pix, porque essa é a primeira cobrança dele e a política da empresa exige meio com prazo de contestação maior para clientes novos, dentro do limite de risco configurado."

**Exemplo para o estabelecimento comercial (visão resumida):**
> "Recomendamos Pix para esta cobrança: maior chance de receber rápido e custo mais baixo, dentro do seu limite de custo máximo de 3,5%."

**Exemplo para auditoria (visão técnica completa):**
> "Decisão `int_5f3a9c`, modelo `decision-engine-v2.3.1`, score Pix = 0.87 (confiança 0.93), score boleto = 0.71, score cartão 3x = 0.64 (descartado — custo estimado 8.2% excede `max_cost` 3.5%). Pesos aplicados: conversão 0.40, custo 0.10, risco 0.15, liquidez 0.10, experiência 0.15, preferência 0.10. Nenhuma regra dura violada. Log completo em `AuditLog#...`."

**Exemplo para o cliente final (quando aplicável, linguagem simples):**
> "Preparamos uma opção de pagamento via Pix para você — rápida e sem taxa adicional. Se preferir, você também pode pagar por boleto."

**"O que aconteceria com outro objetivo" (contrafactual):** o painel de política (seção 16) permite simular "se a política fosse 'minimizar custo' em vez de 'maximizar conversão', qual teria sido a decisão nos últimos 30 dias e qual o efeito estimado" — isso responde diretamente à pergunta de auditabilidade e também serve como ferramenta de venda/consultoria ao merchant.

---

## 20. Plano de implementação

### Squads e papéis

| Squad | Papéis | Foco |
|---|---|---|
| **Core Orchestration** | Eng. backend sênior (2-3), Distinguished Engineer (tech lead) | Serviço de intenção, motor de regras, roteamento, saga/outbox |
| **Payment Integrations** | Eng. backend (2), especialista em integração de pagamentos | Pix, cartão, boleto, antifraude, webhooks |
| **Data & AI** | Data/AI Lead, ML engineer (1-2), data engineer (1) | Feature store, modelos de scoring/risco, MLOps |
| **Risk & Compliance** | Risk officer, DPO/jurídico (part-time), analista de fraude | Guardrails, LGPD, auditoria, matriz de risco |
| **Merchant Experience** | UX Lead, product designer, frontend (2) | Painel, dashboards, onboarding |
| **Reconciliation & Settlement** | Eng. backend (1-2), analista financeiro | Conciliação, liquidação, integração ERP |
| **Platform & Observability** | SRE/DevOps (1-2) | Infra, observabilidade, segurança, CI/CD |

### Backlog inicial (épicos → features → histórias, exemplo)

**Épico 1 — Intenção de recebimento**
- Feature: criar/consultar intenção via API.
  - História: como financeiro do merchant, quero criar uma intenção com objetivo declarado para não escolher o meio manualmente.
  - História: como desenvolvedor integrador, quero idempotência garantida para não duplicar cobrança em retry de rede.

**Épico 2 — Motor de decisão**
- Feature: motor de regras determinístico (MVP) com filtro de elegibilidade.
- Feature: scoring com pesos configuráveis por política.
  - História: como CFO, quero configurar pesos por objetivo para refletir a prioridade do meu negócio.

**Épico 3 — Execução e fallback**
- Feature: execução de rota aprovada.
- Feature: fallback simples (1 nível).

**Épico 4 — Explicabilidade e auditoria**
- Feature: geração de explicação por decisão.
- Feature: log imutável append-only.

**Épico 5 — Dashboard**
- Feature: dashboard de conversão/custo/tempo.

### Dependências e sequenciamento
Integrações de pagamento (Épico 3 técnico) e motor de decisão (Épico 2) podem correr em paralelo após o Épico 1 (contrato de dados) estar fechado; explicabilidade (Épico 4) depende do `DecisionScore` do Épico 2; dashboard depende de dado real fluindo (após Épico 3).

### Estimativa de esforço (ordem de grandeza, MVP)
Épico 1: 2 semanas · Épico 2 (regras): 3 semanas · Épico 3 (integrações + fallback): 5-6 semanas (maior risco de prazo — depende de homologação de provedor externo) · Épico 4: 2 semanas (paralelo) · Épico 5: 2 semanas (paralelo, no fim). Total realista para 90 dias considerando paralelismo entre squads.

### Riscos de entrega
Homologação de provedor externo (Pix/cartão/boleto) é historicamente o maior risco de atraso — depende de terceiro, não apenas do squad interno; mitigar iniciando homologação na semana 1, não esperando o motor estar pronto.

### Critérios de aceite
Cada história tem critério de aceite testável (ex.: "dado um `max_cost` de 3.5%, quando uma opção excede esse custo, então ela não aparece no ranking e o motivo consta na explicação").

### Estratégia de testes
Ver seção 21.

### Estratégia de rollout
Canário por merchant (não por % de tráfego global no MVP, dado o baixo número de merchants piloto) — ativar 1 merchant, validar 1 semana, expandir.

### Change management
Onboarding assistido (não self-service) no MVP — squad de Merchant Experience acompanha os primeiros 30 dias de cada merchant piloto lado a lado, coletando feedback qualitativo além das métricas.

---

## 21. Testes

| Tipo | Escopo |
|---|---|
| **Unitários** | Lógica de scoring, motor de regras, cálculo de custo/liquidez isoladamente |
| **Contrato** | Schema de API entre serviços internos e com provedores externos (contract testing tipo Pact) |
| **Integração** | Fluxo completo intenção → decisão → execução → confirmação em ambiente de sandbox dos provedores |
| **Carga** | Pico de criação de intenções (ex.: campanha de cobrança em massa no dia 5 do mês) |
| **Resiliência** | Provedor lento/indisponível → validar timeout, circuit breaker, fallback |
| **Caos** | Injeção de falha em produção controlada (kill de instância, latência artificial) em ambiente não crítico primeiro |
| **Idempotência** | Reenvio do mesmo request/webhook não deve duplicar efeito |
| **Duplicidade** | Simular corrida de eventos (mesma confirmação chegando 2x) |
| **Segurança** | Pentest de API, teste de assinatura de webhook forjada, teste de rate limiting |
| **Fraude** | Simulação de padrão de fraude conhecido para validar triagem do Agente de Risco |
| **Modelo** | Backtesting em dados históricos, teste de fairness por segmento, teste de calibração |
| **Regressão** | Suite completa rodando a cada deploy do motor de decisão |
| **A/B** | Comparação de política/modelo novo vs. atual em fração controlada de merchants/tráfego |
| **Dados sintéticos** | Geração de intenções sintéticas cobrindo casos-limite (valor zero, prazo passado, cliente sem histórico) |
| **Conciliação** | Casos de matching perfeito, matching parcial, divergência de valor, duplicidade de extrato |
| **Liquidação** | Simulação de atraso de provedor além do SLA, validação de alerta |
| **Fallback** | Cada transição possível do `FallbackPlan` testada explicitamente, incluindo esgotamento de todas as opções |

---

## 22. Tabela de decisões críticas

| Decisão | Opções | Recomendação | Racional | Risco | Tradeoff | Impacto no prazo | Impacto financeiro |
|---|---|---|---|---|---|---|---|
| Modo de operação inicial | Recomendação / Assistido / Automático | **Recomendação** | Constrói confiança e dataset antes de autonomia | Automação prematura gera incidente reputacional grave | Velocidade de ganho vs. segurança | Neutro | Baixo risco de perda financeira direta |
| O Orchestrator deve deter saldo? | Sim (vira instituição de pagamento) / Não (via provedores licenciados) | **Não, no MVP** | Evita licenciamento regulatório complexo no curto prazo | Regulatório: enquadramento incorreto | Menos controle direto vs. menor barreira regulatória | Reduz prazo de MVP significativamente | Evita custo de licenciamento/capital regulatório |
| Modelo de IA no MVP | Deep learning desde o início / Regra + estatística simples | **Regra + estatística simples** | Explicabilidade mais fácil, menos dado necessário para calibrar | Menor sofisticação inicial pode limitar ganho | Velocidade de entrega vs. sofisticação | Reduz prazo de MVP | Menor custo de MLOps inicial |
| Monetização inicial | Success fee (% economia) / SaaS + fee transação | **SaaS + fee transação** | Não depende de baseline auditável complexo desde o dia 1 | Captura menos valor percebido no curto prazo | Simplicidade de cobrança vs. alinhamento de incentivo | Neutro | Receita mais previsível, porém menor upside inicial |
| Segmento piloto | Enterprise grande / PME-média com dado recorrente | **PME-média com recorrência** | Baseline mensurável, ciclo de decisão mais rápido que enterprise | Ganho absoluto menor por merchant | Velocidade de aprendizado vs. tamanho do logo | Reduz prazo de validação | ROI relativo mais fácil de provar |
| Estratégia de multiadquirência | 1 provedor por meio no MVP / Marketplace desde o início | **1 provedor por meio no MVP** | Reduz complexidade de integração e de scoring de provedor | Menor resiliência a falha de provedor único no início | Simplicidade vs. resiliência | Reduz prazo de MVP | Custo de integração menor inicialmente |
| Como tratar comissão de provedor no score | Incluir no `Score(o)` / Nunca incluir | **Nunca incluir no score de decisão** | Evita conflito de interesse e viés de roteamento | Pressão comercial futura para "otimizar receita própria" | Pureza da decisão vs. margem potencial de curto prazo | Neutro | Protege confiança do merchant (ativo de longo prazo) |

---

## 23. Narrativa para pitch (5 minutos)

**Abertura forte:**
"Toda empresa que cobra um cliente hoje toma uma decisão manual — Pix, boleto ou cartão — sem dado, sem aprendizado e sem explicação. Isso custa pontos de conversão e margem todos os meses, silenciosamente."

**Problema:**
"O estabelecimento escolhe o meio de pagamento por hábito, não por evidência. Não existe uma camada que decida, entre Pix, cartão, boleto, link e split, qual caminho maximiza o que o negócio realmente quer — conversão, custo, risco, liquidez ou experiência — para cada cliente, em cada momento."

**Tamanho da oportunidade:**
"O Brasil processa hoje um volume massivo de recebíveis fragmentado entre Pix, cartão e boleto, com multiadquirência virando padrão regulatório. Cada ponto percentual de conversão ou de custo transacional recuperado em escala representa dezenas de milhões de reais por ano só entre nossos merchants-alvo."

**Solução:**
"O Receivables Orchestrator recebe uma intenção — 'quero receber R$ 12.500 até dia 15, priorizando conversão' — e decide ou recomenda o melhor caminho, com fallback automático se falhar, e explica cada decisão de forma auditável."

**Como funciona:**
"Um motor de regras garante os limites duros — compliance, risco, exposição financeira. Sobre ele, um motor de scoring pondera conversão, custo, risco, liquidez e experiência conforme a política de cada estabelecimento, aprendendo com cada transação."

**Por que somos capazes de fazer:**
"Combinamos arquitetura de pagamentos resiliente e auditável, um motor de decisão explicável desde o primeiro dia, e uma governança de risco que nunca deixa o modelo decidir fora dos limites aprovados pelo negócio."

**MVP:**
"Em 90 dias, entregamos recomendação entre Pix, cartão e boleto para 5 a 8 estabelecimentos piloto, em modo recomendação — sem autonomia total — com explicação de cada decisão e dashboard de resultado."

**Riscos e controles:**
"Os riscos são reais: duplicidade de cobrança, decisão opaca, viés algorítmico, dependência de provedor. Cada um tem controle preventivo, detectivo e corretivo definido, e nenhuma decisão financeira sai do motor sem log imutável e auditável."

**Impacto financeiro:**
"No cenário base, projetamos +4 pontos percentuais de conversão e -0,6 ponto percentual de custo transacional por estabelecimento — payback em cerca de 2 a 3 meses no volume operado por eles, com upside de monetização proporcional para nós."

**Pedido de decisão:**
"Peço aprovação para financiar o MVP de 90 dias com o squad inicial definido, validação jurídica do enquadramento regulatório em paralelo, e autorização para operar o piloto com 5 a 8 estabelecimentos em modo recomendação."

---

## 24. Entregáveis finais

1. **Resumo executivo de 1 página** — seção 1 deste documento.
2. **PRD do produto** — seção 2.
3. **Arquitetura textual completa** — seção 6.
4. **Modelo de dados conceitual** — seção 8.
5. **APIs principais com exemplos** — seção 7.
6. **Roadmap** — seção 13.
7. **Matriz de riscos** — seção 11.
8. **Business case** — seção 14.
9. **Plano de MVP** — seção 12.
10. **Pitch executivo de 5 minutos** — seção 23.
11. **Backlog inicial com épicos e features** — seção 20.
12. **Lista de perguntas em aberto** — ver abaixo.
13. **Recomendação final** — ver abaixo.

### Perguntas em aberto

1. Qual o enquadramento regulatório definitivo perante o BACEN se, no futuro, o Orchestrator quiser deter saldo ou fazer split diretamente (vs. sempre operar via provedores licenciados)?
2. Quais provedores (PSP Pix, adquirente, agregador de boleto, antifraude) serão homologados primeiro, e em que prazo real de integração eles se comprometem?
3. Qual o apetite do board para o modelo de monetização "% sobre economia gerada" — vale o investimento em baseline auditável desde já ou só na fase 2?
4. Os merchants piloto têm dado histórico suficiente (3–6 meses) para calibrar baseline de comparação, ou o piloto começa "a frio"?
5. Quem é o Data Protection Officer (DPO) responsável por aprovar a DPIA antes do primeiro modelo entrar em produção?
6. Qual o limite de exposição financeira que o board aceita para o modo automático/autopilot, e a partir de qual volume validado ele pode subir?
7. Faz sentido, no MVP, o motor rodar dentro da infraestrutura de um parceiro (ex.: white-label de PSP) para acelerar prazo, versus construir a camada de integração própria desde o início?

### Recomendação final

**Pilotar.** Não construir a visão completa de uma vez, não descartar a tese. A tese é sólida (fragmentação de meios + multiadquirência + maturidade de dados criam espaço real para uma camada de decisão), mas o produto tem superfícies de risco financeiro e regulatório reais demais para pular direto a autonomia total. Recomenda-se: (1) validar juridicamente o enquadramento regulatório em paralelo ao MVP, (2) construir o MVP de 90 dias em modo recomendação com 3 meios (Pix/cartão/boleto) e 5–8 merchants piloto com dado recorrente, (3) só avançar para modo assistido/automático com base em critérios de maturidade orientados a dados (seção 4 e 12), nunca por calendário. Se os critérios de go/no-go da seção 12 forem atingidos, o roadmap de 24 meses (seção 13) está pronto para execução sequencial.
