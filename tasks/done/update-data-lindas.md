# Atualizar todos os pontos com LINDAS + endereços oficiais da swisstopo

**Objetivo**: Substituir os dados de junho/2026 (760.625 entidades, geocodificadas pela Mapbox) pelo registro comercial atual (~795 mil), com cada ponto na **coordenada oficial da entrada do edifício**. Deve rodar de novo com um único comando.

**Arquivos**: `scripts/update_data.py` (novo), `data/*.json.gz`, `data/search_index.json.gz`, `README.md`
**Status**: Todo
**Prazo**: antes de 16/10/2026 (inscrição no Swiss Viz Awards, ver `submission/submission.md`)

---

## Fontes (verificadas em 12/10/2026)

### 1. Empresas: LINDAS / Zefix (SPARQL)

- Endpoint: `https://ld.admin.ch/query`, grafo `<https://lindas.admin.ch/foj/zefix>`
- Classe `https://schema.ld.admin.ch/ZefixOrganisation`: **795.106** entidades
- Campos por entidade: `schema:name`, `schema:legalName`, `schema:additionalType` (forma jurídica, código eCH-0097, ex.: `.../legalforms/0106` = AG), `schema:identifier` (UID `CHE…`), `schema:municipality` (nº BFS da comuna)
- Endereço (`schema:address`): `locn:thoroughfare` (rua), `locn:locatorDesignator` (número), `schema:postalCode`, `schema:addressLocality`, `schema:addressRegion` (cantão)
- **Não tem coordenadas.** A geolocalização vem da fonte 2.
- Algumas entidades aparecem com mais de um `schema:name` (nome em várias línguas, ex.: "Danstar Ferment SA" / "Danstar Ferment Ltd"). Agrupar por `?c` e ficar com um só nome (preferir `legalName`).

### 2. Coordenadas: Registro oficial de endereços de edifícios (swisstopo)

- Download: `https://data.geo.admin.ch/ch.swisstopo.amtliches-gebaeudeadressverzeichnis/amtliches-gebaeudeadressverzeichnis_ch/amtliches-gebaeudeadressverzeichnis_ch_2056.csv.zip` (137 MB zip → 447 MB CSV, separador `;`, começa com BOM)
- 3.304.018 endereços (3.252.763 `real`, 51.255 `planned`)
- Colunas usadas: `STN_LABEL` (rua), `ADR_NUMBER`, `ZIP_LABEL` ("4052 Basel"), `COM_FOSNR` (nº BFS da comuna), `COM_CANTON`, `ADR_STATUS`, `ADR_EASTING`/`ADR_NORTHING` (LV95, EPSG:2056)
- O ponto é a **entrada do edifício**, o mesmo que o geo.admin.ch usa. Teste: "Ueberlandstrasse 341, 8051" → 47.408592, 8.582133.
- Gratuito e sem limite. Os termos da Mapbox não permitem guardar resultados da geocodificação gratuita, então isso também resolve a parte de licença.

## Precisão medida (amostra de 5.000 entidades do LINDAS, 10 blocos espalhados)

| Nível | Entidades | % |
|---|---:|---:|
| **Edifício exato** (CEP + rua + número) | 4.643 | **92,9%** |
| Centroide da rua (CEP + rua) | 107 | 2,1% |
| Sem correspondência | 250 | 5,0% |
| … dos quais sem rua no registro | 17 | 0,3% |

Isso com uma normalização ingênua (minúsculas, `strasse`→`str`, sem pontuação). As falhas vistas têm causas corrigíveis:
- abreviações francesas/italianas: `Ch.` → `Chemin`, `Av.` → `Avenue`, `Rte` → `Route`, `Pl.` → `Place`;
- CEP de caixa postal ou CEP diferente do edifício (ex.: `Industriestrasse 9, 6301 Zug`, onde o edifício fica em 6300). Para esses, casar por **nº BFS da comuna + rua + número** em vez do CEP;
- nomes de lugar em vez de rua (`Kantonsschule Sargans`, `Les Vernets`) → centroide da localidade.

**Meta: ≥ 96% no edifício exato**, com cada ponto marcado com o nível de precisão.

## Atenção: precisão perdida no empacotamento

`scripts/repack.py` arredonda lat/lng para **4 casas** (~11 m de latitude, ~7,5 m de longitude na Suíça). Com coordenadas de edifício, isso desloca os pontos para o prédio vizinho em ruas densas. Usar **5 casas** (~1 m). Medir quanto cresce o `.json.gz` antes de decidir.

---

## Subtarefas

### T1 — Baixar o LINDAS
- [ ] Consulta SPARQL paginada (`ORDER BY ?c`, `LIMIT 50000`, `OFFSET` crescente) com retry e timeout. Salvar em `build/zefix.parquet`.
- [ ] Agrupar por `?c` e escolher um nome por entidade.
- [ ] Verificar se o grafo traz só entidades **ativas** ou também canceladas/em liquidação (procurar algum predicado de status/data de cancelamento). Se houver canceladas, filtrar.
- [ ] Conferir o total, que deve ficar perto de 795.106.

### T2 — Mapear a forma jurídica
- [ ] Tabela eCH-0097 (`0101`…`0151`, ...) → os códigos de uma letra de `T_MAP` em `scripts/repack.py` (`A`, `G`, `E`, `S`, `V`, ...).
- [ ] Listar códigos sem mapeamento e decidir onde ficam, sem perder entidades em silêncio.

### T3 — Geocodificar contra o registro de endereços
- [ ] Baixar e descompactar o CSV da swisstopo em `build/` (fora do git).
- [ ] Normalizar rua e número dos dois lados com a mesma função (abreviações, acentos, `strasse`/`str.`, números como `31.1`/`4a`).
- [ ] Cascata de correspondência: (1) CEP + rua + nº → (2) comuna BFS + rua + nº → (3) CEP + rua (centroide) → (4) localidade/CEP (centroide). Gravar `precision` = `building` / `street` / `locality`.
- [ ] Preferir `ADR_STATUS = real`, usando `planned` só como desempate.
- [ ] Converter LV95 → WGS84 (pyproj, ou as fórmulas aproximadas da swisstopo, ~1 m).
- [ ] Imprimir as porcentagens por nível e por cantão. Exportar uma amostra dos não encontrados para revisão.

### T4 — Gerar os arquivos do site
- [ ] `data/<CANTÃO>_0.json.gz` no formato colunar atual `{n, t, lat, lng}` (ver `data/ZH_0.json.gz`).
- [ ] `data/search_index.json.gz` no formato atual `{n, t, c, lat, lng}`.
- [ ] Decidir 4 ou 5 casas decimais (ver "Atenção" acima).
- [ ] Gzip nível 9, mesma ordem de chaves. O `index.html` não deve precisar mudar.

### T5 — Validar
- [ ] Contagem por cantão e por forma jurídica: novo × atual. Investigar variações acima de ±10%.
- [ ] Todos os pontos dentro do bounding box da Suíça e no cantão certo.
- [ ] Verificação no mapa (`bun run dev`): 10 empresas conhecidas devem cair no edifício certo. Usar a skill `terminal-browser`.
- [ ] Comparar posições antigas (Mapbox) × novas na mesma empresa: mediana e p95 da distância.
- [ ] Atualizar o service worker (`sw.js`) se o cache precisar ser invalidado.

### T6 — Documentar e automatizar
- [ ] `scripts/update_data.py` faz T1 a T4 com um único comando e registra a data dos dados. Mostrar "Data as of …" na legenda.
- [ ] Atualizar o README: diagrama do pipeline LINDAS → swisstopo → `data/`, e remover a Mapbox do fluxo.
- [ ] Opcional: um GitHub Action mensal que roda o script e abre um PR.
- [ ] Recalcular os números citados em `submission/submission.md` (total, ZG 52,3% AG, BS 6,0% Stiftung, JU 28,7% Einzel).
