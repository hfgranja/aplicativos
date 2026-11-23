# Status consolidado das lacunas — Agente 11

Atualizado em 2026-11-23. Este arquivo consolida o estado de todas as
lacunas mapeadas até agora nos relatórios diários (`AAAA-MM-DD.md`), para
que o grupo não precise ler 8 relatórios para saber o que está aberto.
Ele é mantido pelo Agente 11 e deve ser atualizado a cada rodada que
mudar o status de algo — não substitui os relatórios diários, que
guardam a evidência e o raciocínio completo de cada achado.

| # | Lacuna | Severidade | Dono sugerido | Aberta desde | Rodadas sem confirmação | 1º relatório |
|---|---|---|---|---|---|---|
| 1 | Split Payment tributário (Pix/QR Code) — **fontes oficiais confirmadas em 2026-11-23** (Receita/CGIBS): fase de testes desde 15/10/2026, **janela de registro de PSPs aberta desde 16/11/2026** (ativa agora), operação plena em 2027. Reframe de 2026-11-17 mantido: provável dono fora do roster (área de Rodrigo Bizzotto) | **Crítica** — urgência elevada por prazo real de registro, não só lead time arquitetural | Fabiana Fernandes + Márcio Abdulatiff — **confirmar com urgência** se o Itaú já está registrado (fase de testes ou janela de 16/11) antes de qualquer outra ação | 2026-11-06 | 18 | [2026-11-06](2026-11-06.md) |
| 2 | Consentimento expresso por entidade parceira (Resolução Conjunta BCB/CMN nº 21/2026) | Alta | **Ambíguo** — não presumido | 2026-11-10 | 14 | [2026-11-10](2026-11-10.md) |
| 3 | Gap de mapeamento do próprio grupo — Angelo Russomanno (recebimentos/adquirência Itaú Empresas, visto em 2026-11-11 e novamente em 2026-11-22 falando sobre Itaú Pay/e-commerce Rede) e Rodrigo Bizzotto (Produtos de Adquirência, 2026-11-17) fora do roster | Alta | **Ambíguo** — validar com o grupo | 2026-11-11 | 13 | [2026-11-11](2026-11-11.md) |
| 4 | Documentação do grupo atrás de lançamentos reais de produto (recorrente) — 3ª ocorrência em 2026-11-22 (Itaú Pay, e-commerce/checkout) | Média | Dayane Ribeiro | 2026-11-11 (consolidada; 1ª ocorrência em 2026-11-09) | 13 | [2026-11-09](2026-11-09.md) |
| 5 | Antecipação de recebíveis como produto de crédito | Baixa (rebaixada em 2026-11-19 — já existe como produto formal do Itaú Empresas) | Fabiana Fernandes | 2026-11-06 | 18 | [2026-11-06](2026-11-06.md) |
| 6 | Marketplace de múltiplos provedores de adquirência — **spec entregue em 2026-11-14** ([ver](../complementos/marketplace-provedores-spec.md)), aguardando decisão de Henrique Granja | Média (prioridade reduzida em 2026-11-07 — Rede já lidera via bundling conta+maquininha) | Henrique Granja | 2026-11-06 | 18 | [2026-11-06](2026-11-06.md) |
| 7 | Antifraude/risco de adquirência | Baixa (rebaixada de Alta em 2026-11-09 — capacidade já robusta no banco) | Henrique Granja | 2026-11-06 | 18 | [2026-11-06](2026-11-06.md) |
| 8 | Comunicação multicanal inteligente na cobrança — infra de WhatsApp+IA generativa já existe no banco (ver [2026-11-15](2026-11-15.md)), esforço de fechamento reduzido | Baixa | Priscila Rocha | 2026-11-06 | 18 | [2026-11-06](2026-11-06.md) |

## Notas de pesquisa (não são lacunas)

- "Pulse" (área de Priscila Rocha) não tem rastro público localizável via
  WebSearch até 2026-11-12 — limitação de pesquisa, não lacuna.
- Mercado de adquirência: Rede lidera volume (18%, UBS BB jan/2026) via
  bundling conta PJ + maquininha — contexto favorável, não lacuna.

## Como fechar uma lacuna deste quadro

Uma linha só sai desta tabela quando o grupo confirma, fora deste agente,
que (a) há um dono formal e (b) existe um critério objetivo de conclusão
atingido ou em andamento com prazo. O Agente 11 nunca fecha uma lacuna
unilateralmente — ver seção "Missão" em
[`../.claude/agents/agente-11.md`](../.claude/agents/agente-11.md).
