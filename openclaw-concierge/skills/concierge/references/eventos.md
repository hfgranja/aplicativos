# Shows, teatro, cinema e outras atividades

## Pesquisar

1. Defina período (padrão: próximos 14 dias, ou o fim de semana pedido) e
   cidade do perfil.
2. `web_search` combinando tipo + cidade + mês, e consulte as fontes de
   ingressos/agenda: Sympla, Ticketmaster, Eventim, Ingresse, Uhuu,
   Bilheteria Digital, sites das casas de show e teatros, agenda cultural
   de jornais/Time Out, Ingresso.com para cinema, sites de museus.
3. Para artistas favoritos do perfil, procure "<artista> turnê <ano> <cidade>"
   proativamente.
4. `web_fetch` na página do evento para confirmar data, horário, local,
   faixa de preço e status (à venda / esgotado / em breve).

## Apresentar

```
🎤 **Evento** — Local, bairro
📅 sáb 22/11 · 21h · 💰 R$ 80–220 · 🎟️ à venda (fonte)
Por que: liga com gostos do perfil.
🔗 link de ingresso
```
Verifique a agenda do usuário e marque ⚠️ se houver conflito.

## Depois da escolha

- Envie o link oficial de compra (não use revendedores não oficiais sem avisar).
- Ofereça: criar evento na agenda com local e link, lembrete 1 dia antes
  (ver `agenda.md`) e sugerir restaurante perto do local antes do show
  (ver `restaurantes.md`).
- Para shows ainda sem venda aberta, ofereça uma automação para avisar quando
  abrir (verificação diária via `web_fetch` da página do evento).
