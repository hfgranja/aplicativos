# Motor Inteligente de Recebimentos (Receivables Orchestrator)

Documento de design executivo e técnico completo, produzido por um squad
multidisciplinar simulado (CPO de meios de pagamento, Distinguished Engineer,
Data/AI Lead, Risk Officer, CFO/Business Strategist e UX Lead).

A tese: o estabelecimento comercial declara **intenção financeira**
("receber R$ 12.500 até 15/08, priorizando conversão") e o motor decide ou
recomenda o melhor caminho entre Pix, cartão, boleto, link, split, retry e
fallback — considerando custo, risco, liquidez, experiência e preferências
do cliente pagador.

## Onde está o quê

O documento completo está em [`docs/DESIGN.md`](docs/DESIGN.md), estruturado
nas 24 seções solicitadas: visão executiva, PRD, jornada, motor de decisão,
arquitetura, APIs, modelo de dados, IA, agentes, riscos/compliance, MVP,
roadmap, business case, monetização, UX, observabilidade, segurança,
explicabilidade, plano de implementação, testes, decisões críticas, pitch e
entregáveis finais.

## Recomendação final (resumo)

**Pilotar em 90 dias** com 5-8 estabelecimentos em modo *recomendação*
(Pix + cartão + boleto, sem execução autônoma), antes de investir em
automação total. Detalhes na seção 24 do documento principal.
