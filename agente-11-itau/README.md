# Agente 11 — Itaú Executivos de Tecnologia (Fluxo PJ)

Subagente do Claude Code criado para complementar um grupo de executivos de
tecnologia do Itaú responsáveis pelo fluxo PJ (Pessoa Jurídica), que no
balanço/DRE do banco aparece nas linhas **Pagamentos e Recebimentos** e
**Adquirência**.

## O grupo

| Nome | Área/capacidade principal |
|---|---|
| Dayane Ribeiro | Operação de todos os produtos |
| Fábio Margarito | Itaú Empresas |
| Priscila Rocha | Canais de atendimento, pricing e Pulse |
| Rodolfo Marques | Cartão PJ |
| Allan Hozcar | Laranjinha |
| Márcio Abdulatiff | E-commerce Rede |
| Henrique Granja | Core Adquirência |
| Fabiana Fernandes | Cash Management |

## Liderança de referência

- **Milton Maluhy Filho** — CEO do Itaú Unibanco
- **Ricardo Guerra** — CIO do Itaú Unibanco
- **Adriano Tchen** — Diretor de Tecnologia, Itaú Unibanco

Usada como bússola de prioridade/cultura e como topo da cadeia de
escalação para lacunas críticas (ver detalhe no arquivo do agente).

## Papel do Agente 11

Diferente dos demais integrantes, o Agente 11 não é dono de uma vertical
fixa. Sua missão é dupla:

1. **Validar lacunas** — mapear, com evidência, onde o grupo está
   descoberto, duplicado sem coordenação, ou cobrindo algo só no papel,
   classificando cada uma por severidade (crítica/alta/média/baixa).
2. **Complementar capacidades** — propor e, quando possível, executar o
   complemento necessário (estudo, especificação, protótipo, recomendação),
   sempre indicando o dono definitivo dentro do grupo — e escalando à
   liderança de referência quando a lacuna for crítica.

A análise também considera dimensões de regulatório/compliance,
ecossistema/parcerias externas e dados/IA, e usa pesquisa pública
(LinkedIn e mídia executiva) para embasar a sugestão de dono de cada
lacuna — sempre limitada a expertise profissional, nunca a dados internos
do banco (guardrail de confidencialidade obrigatório no agente).

A definição completa de missão, escopo de negócio, metodologia de análise
de lacunas, severidade, escalação e formato de saída está no arquivo do
agente: [`.claude/agents/agente-11.md`](.claude/agents/agente-11.md).

## Rodada semanal automática

Uma Routine semanal aciona o Agente 11 automaticamente, gerando um novo
relatório em [`relatorios/`](relatorios) a cada execução (arquivo
`AAAA-MM-DD.md`) e commitando o resultado no repositório.

## Como usar manualmente

Este subagente segue o formato padrão de subagentes do Claude Code
(frontmatter + system prompt em Markdown). Para ativá-lo em um projeto:

1. Copie `.claude/agents/agente-11.md` para a pasta `.claude/agents/` do
   repositório onde o grupo trabalha (ex.: o repositório da squad de
   Pagamentos e Recebimentos ou de Adquirência).
2. No Claude Code, invoque-o pelo nome `agente-11` (via `Agent` tool com
   `subagent_type: agente-11`) sempre que precisar de uma varredura de
   lacunas de capacidade no fluxo PJ.
3. Ajuste a lista `tools` no frontmatter conforme o acesso necessário no
   repositório de destino (por padrão: `Read, Grep, Glob, WebSearch,
   WebFetch, Write, Edit, Bash` — pesquisa e produção de specs/protótipos,
   sem restrição de execução além dos limites descritos no próprio agente).

## Manutenção

O roster e a matriz de capacidades devem ser revisados pelo grupo sempre
que a composição do time mudar — o Agente 11 sugere donos e escalações,
mas não os atribui unilateralmente.
