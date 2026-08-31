# Agente 11 — Itaú Executivos de Tecnologia (Fluxo PJ)

Subagente do Claude Code criado para complementar um grupo de executivos de
tecnologia do Itaú responsáveis pelo fluxo PJ (Pessoa Jurídica), que no
balanço/DRE do banco aparece nas linhas **Pagamentos e Recebimentos** e
**Adquirência**.

## O grupo

- Dayane Ribeiro
- Allan Hozcar
- Márcio Abdutatif
- Demais pares do grupo (líderes técnicos e de produto do fluxo PJ)

## Papel do Agente 11

Diferente dos demais integrantes, o Agente 11 não é dono de uma vertical
fixa. Sua missão é dupla:

1. **Validar lacunas** — mapear, com evidência, onde o grupo está
   descoberto, duplicado sem coordenação, ou cobrindo algo só no papel.
2. **Complementar capacidades** — propor e, quando possível, executar o
   complemento necessário (estudo, especificação, protótipo, recomendação),
   sempre indicando o dono definitivo dentro do grupo.

A definição completa de missão, escopo de negócio, metodologia de análise
de lacunas e formato de saída está no arquivo do agente:
[`​.claude/agents/agente-11.md`](.claude/agents/agente-11.md).

## Como usar

Este subagente segue o formato padrão de subagentes do Claude Code
(frontmatter + system prompt em Markdown). Para ativá-lo em um projeto:

1. Copie `.claude/agents/agente-11.md` para a pasta `.claude/agents/` do
   repositório onde o grupo trabalha (ex.: o repositório da squad de
   Pagamentos e Recebimentos ou de Adquirência).
2. No Claude Code, invoque-o pelo nome `agente-11` (via `Agent` tool com
   `subagent_type: agente-11`) sempre que precisar de uma varredura de
   lacunas de capacidade no fluxo PJ.
3. Ajuste a lista `tools` no frontmatter conforme o acesso necessário no
   repositório de destino (por padrão, o agente é somente leitura/pesquisa:
   `Read, Grep, Glob, WebSearch, WebFetch`).

## Manutenção

A matriz de capacidades (modelo no corpo do agente) deve ser atualizada a
cada rodada de análise e revisada pelo grupo — o Agente 11 sugere donos,
mas não os atribui unilateralmente.
