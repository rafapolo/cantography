# Linha do tempo: empresas abrindo e fechando (SHAB, 2018–2026)

**Objetivo**: Animar no mapa cada abertura e cada encerramento de empresa publicado no Diário Oficial do Comércio (SHAB) desde 2018, cada evento no edifício exato. É a peça central para inscrever o Cantography na categoria **Avant-Garde**: o país "respirando".
**Arquivos**: `scripts/fetch_shab.py` (novo), `scripts/update_data.py` (reaproveita a geocodificação), `data/timeline/*.bin|json.gz` (novo), `index.html`
**Status**: Todo
**Prazo**: 16/10/2026 (ver `submission/submission.md`)
**Depende de**: T3 de `tasks/update-data-lindas.md` (geocodificação pela swisstopo)

---

## Fonte (verificada em 12/10/2026)

API aberta do amtsblattportal.ch, sem cadastro nem token.

- Lista: `GET https://amtsblattportal.ch/api/v1/publications?subRubrics=HR01&publicationStates=PUBLISHED&publicationDate.start=AAAA-MM-DD&publicationDate.end=AAAA-MM-DD&pageRequest.size=1000&pageRequest.page=N`
  - `HR01` = Neueintragung (abertura) · `HR03` = Löschung (encerramento)
  - `pageRequest.size` até 3000 testado (3000 itens = 4 MB, 1,5 s)
  - a lista traz `meta` (id, data, título "Neueintragung NOME, SEDE", cantões), **mas `content` = null**
- Detalhe: `GET https://amtsblattportal.ch/api/v1/publications/{id}/xml`
  - HR01 → `<commonsNew><company>`: `name`, `uid` (CHE-…), `seat`, `legalForm` (eCH-0097, ex.: `0106` = AG), `address` (`street`, `houseNumber`, `swissZipCode`, `town`), além de `capital`
  - HR03 → `<commonsActual><company>`: mesmos campos. **96/100 encerramentos testados trazem rua.**
  - `journalDate` (data da inscrição no registro) e `publicationDate` (data no SHAB, poucos dias depois). Usar `journalDate` como data do evento.
- Taxa medida: **~70 req/s com 8 threads, 160/160 respostas 200**, sem limitação aparente. Mesmo assim, usar backoff e retry.

### Volume

| Ano | HR01 aberturas | HR03 encerramentos |
|---|---:|---:|
| 2017 | 0 | 0 |
| 2018 (início do portal, meio do ano) | 14.310 | 9.943 |
| 2019 | 44.616 | 31.273 |
| 2025 | 55.654 | 33.971 |
| 2026 (até 12/10) | — | — |

Total estimado 2018–2026: ~400 mil aberturas + ~260 mil encerramentos ≈ **660 mil XML ≈ 2,5–3 h** a 70 req/s.

---

## Subtarefas

### S1 — Coletar (`scripts/fetch_shab.py`) ✅ 13/10/2026
- [x] Paginar a lista (HR01 e HR03) e guardar os ids em `build/shab_ids.parquet`. Os meses vão em paralelo, cada um numa página de 3000; uma janela com mais que isso se divide em duas (a API recusa offset perto de 10 mil e não tem ordem fixa).
- [x] Baixar os XML com 16 threads (~75–90 req/s), timeout de 30 s, retry com backoff. O cache é `build/shab_events.jsonl` (uma linha por id), e uma nova execução pula o que já foi baixado. Atenção: o cache da API às vezes devolve gzip sem avisar; o script descompacta.
- [x] Extrair `id, kind (open/close), date (journalDate), pub, uid, name, legalForm, street, houseNumber, zip, town, seat, cantons`.
- [x] `subRubrics=HR01,HR03` funciona numa chamada só.
- [x] Conferido: 661.461 ids = 661.461 XML, 0 falhas, de 03/09/2018 (início do portal) a 12/10/2026. O total da API bate, descontadas as publicações do dia seguinte.

**Atualizar com as publicações novas:**
```bash
cd ~/Projetos/swissviz-timeline
python3 scripts/fetch_shab.py --refresh-list   # refaz a lista (~1 min) e baixa só os XML novos
python3 scripts/build_timeline.py              # regera data/timeline/events.bin.gz
```
Depois, aumentar `TL_VERSION` no `index.html`, porque o service worker guarda os arquivos de dados para sempre. Sem `--refresh-list`, o script reaproveita a lista antiga e não vê nada novo.

### S2 — Geolocalizar
- [ ] Reaproveitar a cascata de `tasks/update-data-lindas.md` T3 (CEP + rua + nº → comuna + rua + nº → rua → localidade).
- [ ] Fallback para quem não tem rua: cruzar o UID com outro evento da mesma empresa (abertura ↔ encerramento) ou com o LINDAS. Se nada casar, centro da `seat`.
- [ ] Gravar o nível de precisão por evento. Meta: ≥ 90% no edifício exato.
- [ ] Atenção: o endereço do encerramento é o **último** endereço da empresa, que pode ter mudado desde a abertura. Isso está certo para a animação, porque ela apaga o ponto onde a empresa estava.

### S3 — Preparar os dados para o navegador
- [ ] Formato compacto para cerca de 660 mil eventos: arrays colunares `day` (dias desde 2018-01-01, uint16), `lat`/`lng` (int32 × 1e5), `kind` (0/1), `t` (forma jurídica, 1 char). Como `.bin` gzip ou JSON colunar gzip.
- [ ] Medir o tamanho. Se passar de ~8 MB, dividir por ano e carregar sob demanda.
- [ ] Opcional: nomes num arquivo separado, carregado só quando o usuário clica num evento.

### S4 — Animar (`index.html`)
- [ ] Controle de tempo: play/pause, velocidade (1 ano ≈ 7 s → 2018–2026 em ~60 s) e arrastar a data.
- [ ] Abertura: o ponto acende (flash claro, raio maior) e assenta na cor da forma jurídica.
- [ ] Encerramento: o ponto pisca em vermelho/âmbar e se apaga em ~1 s.
- [ ] Implementar com deck.gl `ScatterplotLayer` + filtro de tempo na GPU (`DataFilterExtension` com `filterRange` pelo dia) ou atributo de idade calculado no shader, para não recriar a camada a cada quadro.
- [ ] Contadores ao vivo: data atual, aberturas e encerramentos acumulados e saldo líquido.
- [ ] Mini-histograma semanal sob o controle (aberturas para cima, encerramentos para baixo). Mostra sazonalidade e Covid.
- [ ] Funciona no modo noturno, que é o padrão do vídeo.

### S5 — Achados para o texto da inscrição
- [ ] Sazonalidade: pico de aberturas no início do ano?
- [ ] 2020 (Covid): queda de aberturas e onda de encerramentos depois?
- [ ] Cantões e comunas com maior saldo líquido; endereços com muitas aberturas e encerramentos (rotatividade de empresas de fachada).
- [ ] Conferir cada afirmação contra os dados antes de escrever.

### S6 — Inscrição Avant-Garde
- [ ] Vídeo `cantography_demo.mp4`: a animação 2018–2026 em ~45 s, modo noturno, visão nacional com um zoom em Zurique ou Zug no meio.
- [ ] Hero: um quadro da animação com as aberturas acendendo.
- [ ] Reescrever Title, Purpose, Impact e Audience para Avant-Garde, mantendo os limites de palavras.
- [ ] PDF de documentação: fontes (SHAB, LINDAS, swisstopo), método, precisão e limitações (histórico só desde 2018; a data é a da inscrição no registro, não a do início real da atividade).

## Plano B (se o prazo apertar)
- Usar só os títulos da lista ("Neueintragung NOME, SEDE"), sem baixar os XML. Cruzar as aberturas pelo nome com o LINDAS (coordenada exata das que ainda existem) e pôr os encerramentos no centro da comuna (`seat`).
- Se a animação não ficar boa até 15/10: inscrever na **Public Lens** com a visão nacional e deixar a linha do tempo para depois.
