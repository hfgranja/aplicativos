# Spec mínima: múltiplos provedores por meio (marketplace de adquirência)

Complemento produzido pelo Agente 11 em 2026-11-14 para a lacuna #6 do
[`STATUS.md`](../relatorios/STATUS.md) ("Marketplace de múltiplos
provedores de adquirência", Média, dono sugerido Henrique Granja).

Esta é uma especificação de leitura, não uma mudança de código: o Agente
11 não altera a base de `receivables-orchestrator` sem pedido explícito
do dono da squad. O objetivo é dar ao dono um ponto de partida concreto,
não decidir a arquitetura por ele.

## Evidência do estado atual

- `models.PaymentProvider` (`receivables-orchestrator/backend/app/models.py:79-91`)
  tem `method` como campo simples (`pix|credit_card|debit_card|boleto|
  payment_link`), sem relação N:N provedor↔meio.
- `_get_provider()` (`receivables-orchestrator/backend/app/services/
  execution.py:24-25`) faz `.filter(PaymentProvider.method == method).
  first()` — pega o **primeiro** registro daquele meio, sem critério de
  escolha. Mesmo que existisse mais de um provedor cadastrado para o
  mesmo meio hoje, apenas um seria efetivamente usado.
- O motor de scoring (seção 5 do `docs/DESIGN.md`) decide entre **meios**
  (Pix vs. cartão vs. boleto), não entre **provedores do mesmo meio** —
  essa dimensão simplesmente não existe no motor de decisão hoje.

## O que mudaria (mínimo viável)

1. **Seleção de provedor, não só de meio.** `_get_provider` passaria a
   retornar uma lista de provedores operacionais para o meio e aplicar
   um critério explícito de escolha (ex.: menor `base_cost_pct` ajustado
   por `error_rate`, ou round-robin simples para começar) em vez de
   `.first()`.
2. **Fallback entre provedores do mesmo meio**, reaproveitando o
   `fallback_engine` já existente (`engine/fallback.py`), hoje usado só
   para troca de meio — o mesmo mecanismo de retry/fallback poderia
   escalonar para "mesmo meio, outro provedor" antes de trocar de meio.
3. **Dado necessário que falta:** nenhum — o schema de `PaymentProvider`
   já suporta múltiplas linhas por `method`; o que falta é lógica de
   seleção e um seed de dados de demonstração com >1 provedor por meio.

## O que fica fora deste complemento

- Negociação/contratação de provedores reais (comercial, fora do escopo
  técnico).
- Mudança de UI/dashboard para exibir a escolha de provedor ao
  estabelecimento — avaliar se é necessário depois que a lógica de
  seleção existir.

## Critério de fechamento desta lacuna

Henrique Granja (ou quem ele designar) decide: (a) se este é o momento
certo para essa mudança dado o contexto de mercado já registrado em
[`2026-11-07.md`](../relatorios/2026-11-07.md) (Rede já lidera via
bundling, não via diversificação de provedor), e (b) se aceita este
desenho mínimo ou propõe outro. Até essa decisão, a lacuna permanece
aberta no `STATUS.md`.
