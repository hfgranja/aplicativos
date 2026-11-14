# Restaurantes, bares e cafés

## Entender o pedido (pergunte só o que faltar, máx. 2 perguntas)

Ocasião (date, família, negócios, amigos, sozinho) · data/hora · nº de pessoas ·
região · tipo de cozinha · faixa de preço. Use o perfil para preencher o resto.

## Pesquisar

1. Se a skill `goplaces` estiver disponível (e `GOOGLE_PLACES_API_KEY`):
   `goplaces search "<cozinha> restaurante <bairro>" --min-rating 4.3 --limit 8 --json`
   e `goplaces details <place_id> --reviews` para os finalistas
   (horário, telefone, faixa de preço, avaliações recentes).
2. Complemente com `web_search`: guias e críticas locais (ex.: Guia Michelin,
   Veja Comer & Beber, Prazeres da Mesa, Time Out, Folha/Estadão Guia,
   TripAdvisor, Instagram do restaurante) e "<nome> reserva".
3. Use `web_fetch` na página do restaurante para confirmar horário de
   funcionamento no dia pedido, cardápio/faixa de preço e se aceita reserva.
4. Filtre: fechado no dia/horário → descarte. Já visitado e mal avaliado no
   histórico → descarte. Já visitado e bem avaliado → pode sugerir como "aposta segura".

## Apresentar

3–5 opções variadas (uma segura, uma novidade, uma com melhor custo-benefício),
no formato padrão do SKILL.md. Mencione se tem carta de vinhos boa ou rolha.

## Reservar

- Encontre o canal de reserva oficial (link do site, plataformas de reserva
  como OpenTable/TheFork/Get In/Tagme, ou WhatsApp/telefone).
- O agente **não** conclui reserva sozinho em sites que exigem login/pagamento:
  envie o link direto e ofereça colocar na agenda após o usuário confirmar.
- Se houver ferramenta de navegador e o usuário pedir explicitamente, pode
  preencher o formulário, mas pare antes de enviar e peça confirmação.
- Após confirmação: crie o evento (ver `agenda.md`) e registre no histórico.
