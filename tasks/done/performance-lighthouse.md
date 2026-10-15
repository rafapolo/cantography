# Desempenho e Lighthouse em 100

**Objetivo**: Levar o Lighthouse a 100 no desktop e o mais perto possível de 100 no celular. Pelo caminho, aplicar no swissviz o que funcionou no tocador. Hoje acessibilidade, boas práticas e SEO já estão em 100, então o trabalho é todo em **Performance**.

**Arquivos**: `index.html`, `sw.js`, `scripts/build.js`, `.github/workflows/deploy.yml`
**Status**: Feito (2026-10-15). T2 e T3 portados para o main por rebase (`bf63cb1`, `3b5470a`), sem push. T7 já estava no main (`aria-label="DE · Deutsch"`); T5 fica como está (decisão). Lighthouse no celular, `dist/`, 3 rodadas alternadas: Perf 73 → 98, TBT ~1.400 ms → ~100 ms. Em aberto: o LCP subiu de ~0,85 s para ~2,0 s (Render Delay do `h1.wordmark`), ainda abaixo de 2,5 s; e o CLS de 0,017 do `#dock`.
**Relacionado**: `tasks/worker-duplicated-parse-logic.md` (lógica duplicada do worker de parse e worker que trava sem rejeitar; não está repetido aqui)

---

## Resultado em 2026-10-15 (T2 + T3)

**Condições.** Lighthouse 12, Chromium da Playwright, `--headless=new`, só a categoria performance. Celular no padrão (CPU 4×, 4G lento simulado), desktop com `--preset=desktop`. A = `dist/` do `main` em `d9be156`, congelado e servido na porta 3031. B = `dist/` do ramo, servido na porta 3012. As rodadas alternam A e B: 5 no celular e 3 no desktop, por rodada. Havia outras sessões usando a CPU; por isso os números são medianas, com a faixa entre parênteses. Script: `lh.sh`/`lhsum.py` no scratchpad da sessão.

| | Perf | TBT | Speed Index | LCP | CLS |
|---|---|---|---|---|---|
| celular A (`d9be156`) | 75 (70–76) | 1.210 ms (1.090–2.209) | 3,3 s | 0,8 s | 0–0,017 |
| celular, só T2 (outra rodada; o A dela deu 72 e 1.223 ms) | 77 (70–80) | 1.112 ms (771–3.402) | 2,7 s | 0,9 s | 0,017 |
| **celular, T2 + T3** | **99 (98–99)** | **92 ms (70–127)** | **2,5 s** | 0,8 s | 0,017 |
| desktop A | 100 (93–100) | 56 ms | 1,1 s | 0,2 s | 0,018 |
| **desktop, T2 + T3** | **100 (100–100)** | **0 ms** | 0,7 s | 0,4 s | 0,018 |

**O que mudou o resultado.** O perfil de CPU (4×) mostrou que o gargalo não era o deck.gl. Era `_parseWorker.onmessage`, que levava **1,26 s** desserializando ~450 mil objetos de ponto com `companies[]`. O deck.gl inteiro custava 0,5–0,9 s.
- **T2:** o JS do deck caiu para ~250 ms de execução e a nota subiu ~2–5 pontos. Isso confirma a estimativa feita antes de começar.
- **T3 (colunas transferíveis):** o handler foi de 1,26 s para 15 ms. A CPU ocupada no boot caiu de 3,0 s para 1,4 s, e as tarefas longas, de 19 para 5. A maior que sobrou é do maplibre (91 ms).

**T2, o que foi feito.**
- `scripts/deck-entry.js` reúne `ScatterplotLayer`, `DataFilterExtension` e `MapLibreOverlay` de `@deck.gl/*@9.4.0`, com versão fixada e como devDependencies no `bun.lock`.
- `Bun.build` gera `vendor/deck.mjs` (gitignored), que `build.js` copia para `dist/`.
- Tamanho: **789 KB crus / 223 KB gzip**, contra 2,07 MB / 575 KB do UMD do unpkg. O critério de 250 KB vale para o gzip, que é o que trafega.
- O esbuild dá o mesmo tamanho, por isso não entrou como dependência.
- Quem serve a pasta-fonte precisa rodar `bun run build` uma vez.

**T3, o que foi feito (a "opção 4", ajustada).**
- O worker devolve cada cantão em colunas, enviadas como *transferables*:
  - `pos` (Float64Array);
  - `mask`;
  - `off` (faixa de empresas de cada endereço);
  - `lab`;
  - `year`.
- Os nomes vão como **uma string só**. Assim o hover e o clique continuam síncronos, sem pedir nada ao worker.
- O layer usa atributos binários: posições, filtro e cores. O objeto de posições é o mesmo entre rebuilds, então não há reenvio.
- O cartão e a busca montam o ponto sob demanda (`pointView`).

**Checagens (A contra B, iguais em todos os itens).**
- Contagens dos 26 cantões e da legenda.
- Desligar uma forma jurídica, desligar e religar ZH.
- Hover e cartão fixado.
- 4 buscas no índice global e as mesmas na busca local de fallback, com o índice derrubado à força: resultados, marcadores e cartão.
- Cor da moldura no modo dia, com e sem GmbH.
- Brilho e cor média das capturas em z7.5 e z12.5, no modo noite e no modo dia.
- Erro do worker sem cache (chunk com falha de rede e gz corrompido): a promessa rejeita, o cantão desliga e a contagem fica "(–)", sem travar.

**Interações, tarefas longas na thread principal com CPU 4× (`PerformanceObserver`, máximo/soma em ms):**

| ação | A | B |
|---|---|---|
| Desmarcar todos | 105 / 177 | 0 / 0 |
| Selecionar todos | 153 / 221 | 76 / 76 |
| BE desligar / ligar | 69 / 89 | 0 / 0 |
| modo noite desligar / ligar | 262 / 88 | 74 / 53 |
| GmbH desligar / ligar | 89 / 109 | 65 / 0 |

O B não tem nenhuma tarefa com mais de 76 ms. As que ainda passam de 50 ms vêm de recalcular o filtro e as cores, com ~450 mil pontos, em `layerData()`. O critério do T3 era "nada acima de 50 ms vindo do carregamento de dados", e ele é cumprido: o carregamento já não aparece. Para essas interações passarem de 76 para menos de 50 ms, o filtro e as cores teriam de ir para o worker ou para a GPU.

**Outras checagens.**
- **Toque:** com `(hover: none)` ativo, no viewport de 390 px, a folha inferior abre com o mesmo conteúdo em A e B.
- **Build do CI:** reproduzido num clone limpo com Bun 1.4.2 e `--frozen-lockfile`. O `vendor/deck.mjs` saiu byte a byte igual ao local.
- **Recuperação:** depois de uma falha, o botão "Retry" do alerta carrega o cantão de novo.

**Em aberto.**
- O CLS de 0,017 vem do `#dock` no celular. Aparece também em A, de forma intermitente, então não é regressão deste trabalho, mas vale investigar.
- Sobra o T7.
- O T5 fica como está (decisão).

## Linha de base (medida em 2026-10-15)

### Como medir (use sempre o mesmo comando, antes e depois de cada tarefa)

```bash
bun run build && npx serve dist -l 3012 &
export CHROME_PATH="$(ls -d ~/Library/Caches/ms-playwright/chromium-*/chrome-mac-arm64/*.app/Contents/MacOS/Google* | tail -1)"
for i in 1 2 3; do
  npx -y lighthouse@12 http://localhost:3012/ --quiet --chrome-flags="--headless=new" \
    --output=json --output-path=/tmp/lh-mobile-$i.json            # celular (padrão: 4× CPU, 4G lento)
  npx -y lighthouse@12 http://localhost:3012/ --preset=desktop --quiet --chrome-flags="--headless=new" \
    --output=json --output-path=/tmp/lh-desktop-$i.json
done
```

Registre a **mediana de 3 execuções**: o TBT do celular varia entre 280 e 450 ms de uma rodada para outra. Meça sempre a pasta `dist/` minificada. O `index.html` cru aparece com avisos falsos de "unminified CSS/JS".

### Resultado de `dist/` (ramo `feat/night-light`, commit `9376b04`)

| perfil | Perf | A11y/BP/SEO | FCP | LCP | TBT | Speed Index | CLS |
|---|---|---|---|---|---|---|---|
| celular (mediana) | **69** | 100/100/100 | 1,7 s | **6,3 s** | 280 ms | 4,3 s | 0 |
| desktop (mediana) | **88** | 100/100/100 | 0,5 s | **2,2 s** | 10 ms | 1,3 s | 0,005 |

### Item 0: o site publicado está atrasado (decisão sua, não é tarefa de código)

`rafapolo.github.io/swissviz` ainda serve o `main` de 17/09, com **Perf 29 no celular** (maplibre 5.24 e deck.gl 9.3 bloqueando a renderização, LCP de 9,3 s) e 91 no desktop. Todo o trabalho desde então está no ramo `feat/night-light`, que nunca chegou ao `main`. Fazer o merge sozinho já leva o celular de 29 para cerca de 69.

---

## O que vem do tocador

| Técnica no tocador | No swissviz | Situação |
|---|---|---|
| Formato colunar (v2) no catálogo | `{n,t,lat,lng}` por cantão | ✅ já feito |
| Descompactação nativa (`DecompressionStream`) | `gunzipJson` | ✅ já feito, mas na thread principal (T3) |
| Trabalho pesado fora da thread principal | worker de parse e worker de busca | ⚠️ parcial: fetch, gunzip, `JSON.parse` e `foldText` ainda rodam na thread principal (T3) |
| Normalizar o texto da busca uma vez só, na carga | `indexCanton` faz `foldText` em toda empresa | ⚠️ no tocador, `buildAlbums` foi o maior bloqueio na abertura; aqui é igual (T3) |
| HTML pré-renderizado antes do JS (páginas de álbum) | lista de cantões e textos montados por JS | ❌ é a causa do LCP (T1) |
| Fontes com `display=optional` | `display=swap` | ❌ (T5) |
| Nome do cache do service worker reescrito com o SHA do commit a cada deploy | `V = 'swissviz-v5'` fixo | ❌ quem volta ao site nunca recebe dados novos (T6) |
| Bun fixado no Dockerfile/CI (uma atualização do Bun quebrou o S3Client em 2026-08-20) | `bun-version: latest` | ❌ (T8) |
| Minificação no deploy | `scripts/build.js` (html-minifier-terser) | ✅ já feito |
| Grade virtual (~30 nós no DOM) | o mapa é WebGL e não tem lista grande | — não se aplica |

---

## Tarefas, por impacto

### T1. Pintar o LCP sem esperar o maplibre (celular: LCP 6,3 s; desktop: 2,2 s)

**Evidência.** O elemento de LCP é texto montado por JS: o placeholder da busca (`div#placeholder`) no celular e `.canton-name` no desktop. **Render Delay = 93%** do LCP. As tarefas longas são todas do `maplibre-gl.mjs` (1.067 ms, 562 ms, 220 ms…) e começam por volta de 6,4 s. O `<script type="module">` importa o maplibre de forma estática, e `boot()` monta painéis, `applyLang()` e `new maplibregl.Map` / `new deck.MapLibreOverlay` no mesmo trecho síncrono. Nada aparece na tela antes de tudo isso terminar.

**O que fazer:**
1. Deixar no HTML estático, como as páginas de álbum do tocador, o que hoje é montado por JS e aparece primeiro na tela:
   - a lista de cantões (`#canton-items`);
   - as legendas;
   - o placeholder final da busca.
   Um script inline de poucas linhas no `<head>` escolhe o idioma (`localStorage` ou `navigator.language`) antes da primeira pintura. O JS passa a só ligar os eventos.
2. Esperar um frame antes de criar o mapa: `await new Promise(r => requestAnimationFrame(() => setTimeout(r)))` antes de `new maplibregl.Map`.
3. Opcional: trocar o `import` estático por `await import(...)` do maplibre depois da primeira pintura.
4. Não mudar o `placeholder` depois da pintura. As trocas `searchLoading` → `searchReady` geram um novo candidato a LCP. Mostrar o estado do índice no ícone, que já tem `.loading`, ou numa região `aria-live`.

**Critério de aceite:** LCP < 2,5 s no celular e < 1,0 s no desktop (mediana de 3), CLS continua 0, e a troca de idioma continua funcionando.

### T2. Trocar o deck.gl completo por um pacote só com o necessário (celular: TBT e bytes)

**Evidência.** `deck.gl@9.4.0/dist.min.js` tem 576 KB, **55% sem uso** (320 KB), mais 7 KB de JS legado (`Math.hypot` e outros polyfills). São 736 ms de execução no celular. O código usa só `ScatterplotLayer`, `DataFilterExtension` e `MapLibreOverlay` (e as extrusões 3D, se vierem do deck).

**O que fazer:** gerar em `scripts/build.js` (esbuild, `--format=esm --target=es2022 --minify`) um pacote com `@deck.gl/core`, `@deck.gl/layers`, `@deck.gl/extensions` e `@deck.gl/mapbox`, e servi-lo do próprio site. Isso também tira o unpkg da lista de terceiros que bloqueiam a thread principal. Avaliar o mesmo para o maplibre: em tamanho dá pouco, mas ele passaria a ter o mesmo cache e a mesma origem do site.

**Critério de aceite:** o JS do deck cai para menos de 250 KB, "unused-javascript" do deck fica abaixo de 100 KB, o TBT do celular cai (registrar o antes e o depois) e os filtros por GPU continuam sem reenviar os pontos.

### T3. Tirar da thread principal o trabalho de carregar um cantão (fluidez ao ligar cantões)

**Evidência no código** (o custo em ms ainda não foi medido, veja o critério):
- `gunzipJson` (≈`index.html:1888`) faz fetch, gunzip e `JSON.parse` na **thread principal**: são 3 MB de JSON só para Bern. Depois, `{n,t,lat,lng}` é **clonado** para o worker, e os `points` (objetos com `companies[]`) são **clonados de volta**, o que também custa tempo na thread principal.
- `indexCanton` (≈`:1792`) roda `foldText` em toda empresa na thread principal, a cada cantão carregado. Esse índice local só serve para a busca antes de o índice global ficar pronto.

**O que fazer (do mais barato ao mais caro):**
1. Mandar só a URL para o worker. Ele faz fetch, gunzip e parse, como o worker de busca já faz, e a thread principal deixa de parsear e de clonar a ida.
2. `foldText` preguiçoso: normalizar só na primeira busca local, ou não ter índice local quando o global já está pronto.
3. Trocar `.blob()` → `.text()` → `JSON.parse` por `new Response(stream).json()`.
4. Opção maior: o worker devolve `Float32Array` de posições, `Uint8Array` de cores e `Uint32Array` de máscara como *transferables*, usados como atributos binários do deck.gl (`data: {length, attributes}`). As listas de empresas ficam no worker e são pedidas por índice no hover e no clique. Isso some com a clonagem da volta.

Fazer junto com `tasks/worker-duplicated-parse-logic.md`, porque mexe no mesmo worker.

**Critério de aceite:** medir no DevTools (Performance, CPU 4×) quanto tempo a thread principal gasta para ligar BE e para "Selecionar todos", antes e depois. Nenhuma tarefa acima de 50 ms vinda do carregamento de dados. Contagens da legenda, busca e cartão iguais às de antes.

### T4. CSS do maplibre sem bloquear a renderização (celular: cerca de 900 ms; desktop: cerca de 330 ms)

**Evidência.** `maplibre-gl@6.14.0/dist/maplibre-gl.css` (11 KB) é o único recurso que ainda bloqueia a renderização.

**O que fazer:** colocar o CSS inline no build (o `minifyCSS` já existe) ou carregá-lo com `media="print" onload="this.media='all'"`, como a fonte já faz. Os controles do mapa só aparecem depois do JS, então não há salto visual.

**Critério de aceite:** "render-blocking-resources" passa nos dois perfis e o CLS continua 0.

### T5. Fonte com `display=optional`

Inter usa `display=swap`. No tocador usamos `display=optional`: em rede lenta fica a fonte do sistema e não há troca de fonte no meio da leitura nem um novo candidato a LCP. O `preconnect` para `fonts.gstatic.com` já existe.

**Critério de aceite:** o LCP do celular não piora e o CLS continua 0.

### T6. Service worker: versão por deploy e dados com stale-while-revalidate

**Evidência.** `sw.js` usa um `V = 'swissviz-v5'` fixo e serve tudo que não é navegação (inclusive `data/*.json.gz`, os scripts do unpkg e `search_index.json.gz` de 8,3 MB) **cache-first, para sempre**. Quem já visitou o site nunca recebe dados atualizados (como as datas de abertura do commit `1d5b970`) a menos que alguém lembre de mudar o `V` à mão.

**O que fazer (o padrão do tocador):**
- Em `scripts/build.js`, reescrever o nome do cache para o SHA do commit (`GITHUB_SHA`). Cada deploy instala um worker novo e apaga os caches antigos.
- Para `data/`, usar stale-while-revalidate: responde do cache e atualiza em segundo plano.
- Os arquivos do unpkg têm a versão na URL, então podem continuar cache-first.

**Critério de aceite:** com o worker antigo instalado, publicar um build novo e recarregar duas vezes traz os dados novos. Repetir a visita sem rede continua funcionando.

### T7. Acessibilidade: nome dos botões de idioma

O Lighthouse (desktop) marca `label-content-name-mismatch`: os botões mostram "DE", "FR", "IT", "EN", mas o `aria-label` é "Switch to German". A nota já é 100 porque essa auditoria não conta, mas o nome acessível precisa conter o texto visível (WCAG 2.5.3, Label in Name). Exemplo: `aria-label="DE – Deutsch"`, ou tirar o `aria-label` e usar `lang`/`title`.

**Critério de aceite:** a auditoria passa e o leitor de tela continua dizendo qual é o idioma.

### T8. CI e bibliotecas

- **Bibliotecas:** já estão na versão mais recente (maplibre-gl 6.14.0 e deck.gl 9.4.0, conferidos com `npm view` em 2026-10-15). `bun outdated` não acusa nada. Não há o que atualizar.
- **`deploy.yml`:**
  - `bun-version: latest` → fixar a versão (por exemplo, `1.4.2`), pela mesma lição do tocador.
  - A chave do cache faz `hashFiles('bun.lockb')`, mas o repositório tem **`bun.lock`**. A chave nunca muda, e o cache não invalida quando as dependências mudam.
  - Actions atrasadas em relação ao tocador: `checkout@v4` → `v7`, `configure-pages@v5` → `v6`, `upload-pages-artifact@v3` → `v5`, `deploy-pages@v4` → `v5`.

---

## Expectativa realista

- **Desktop:** T1 + T4 devem levar de 88 para cerca de 100, porque o LCP de 2,2 s é o único problema real (TBT de 10 ms).
- **Celular:** T1 resolve a métrica de maior peso (LCP), e T2 e T3 reduzem o TBT. Defina a meta do celular **depois de medir T1 a T4**. Os cerca de 2 s de execução do maplibre e do deck.gl ao iniciar o mapa (CPU 4×) não somem com divisão de código enquanto o mapa for criado na abertura da página.
- **Celular em 100 de verdade** só acontece se o mapa for criado depois da primeira interação, mostrando antes uma prévia estática (como `mini.jpg`). Isso muda o produto: quem abre o link não vê os pontos de imediato. É uma decisão sua, não uma tarefa.
