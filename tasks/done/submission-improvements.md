# Melhorias para o Swiss Viz Awards (resposta a "são só pontos num mapa")

**Objetivo**: Dar ao mapa uma leitura própria antes de 16/10/2026, para o júri ver mais do que um gráfico de dispersão sobre um mapa-base.
**Arquivos**: `index.html`, `sw.js`, `submission/`
**Status**: Encerrado (2026-10-15). Só o item 6 foi feito, como tour cinematográfico de ~50 s (ramo `feat/tour`, `0262a1c`, sem merge): Genebra (Verein+Stiftung), Zurique (AG+GmbH), Berna (Einzelunternehmen), 2016–2026; Vaud 2019–2021 (encerramentos caíram 25% em 2020); busca por "Nestlé Suisse"; volta à Suíça. Botão "tour" nos chips e `?tour=1`. Os itens 1, 2, 3 e 7 já estavam no main. Os itens 4, 5, 8 e 9 não foram escolhidos, e o 10 ficou de fora.
**Contexto**: o júri inclui um especialista em mapas interativos (Tamedia), o FSO, design crítico de dados (SUPSI) e defensores de visualização direta. Ver `submission/submission.md`.

Ordem = prioridade (impacto no júri ÷ esforço).

---

## 1. Visão padrão: Suíça inteira, modo noturno — **obrigatória**
- Abrir com os 26 cantões e o modo noturno ligado, em vez de só Bern.
- Medir o tempo até a primeira renderização com ~795 mil pontos (carregamento e worker). Se ficar lento, carregar a visão nacional a partir de uma camada pré-agregada (hexbin/densidade) e trocar para os pontos individuais no zoom.
- Opção mais segura: parâmetros na URL (`?all=1&night=1`) para o link do júri, mantendo o padrão atual para os outros visitantes.

## 2. Nome Cantography no site
- `<title>`, cabeçalho, imagens OG e README. O júri tem que ver o mesmo nome do formulário.

## 3. Contagem por edifício ("quantas empresas nesta porta")
- Ao clicar num endereço com várias entidades, listar todas. Endereços com centenas de empresas (domicílios de fachada) viram uma descoberta em si.
- Um modo "Top endereços" com os 20 endereços com mais empresas do país.

## 4. Painel de precisão (transparência)
- Na legenda: "93% dos pontos no edifício exato · 2% no centro da rua · …", e a cor ou opacidade do ponto indicando o nível.
- Uma frase fixa: "Endereço de registro, não necessariamente onde a empresa opera."
- Responde diretamente à crítica de "escolhas por trás dos dados".

## 5. Comparar cantões
- Pequenos múltiplos ou barras empilhadas: a composição por forma jurídica de cada cantão, ordenável. Torna visíveis Zug (AG), Basel (Stiftung) e Jura (Einzel) sem precisar explorar o mapa.

## 6. Três achados guiados ("tour")
- Um botão "Discover" que voa por 3 cenas com uma frase cada: Zug, Basel-Stadt, Jura (ou os achados recalculados).
- Dá ao júri a *história* que falta num mapa exploratório e serve de roteiro para o vídeo.

## 7. Perfil da entidade com link para a fonte
- No popup: forma jurídica, UID (`CHE-…`) e link para a página oficial no Zefix. Cada ponto passa a ser verificável.

## 8. Busca por endereço / "minha rua"
- Digitar um endereço ou CEP leva até ele e mostra quem está registrado ali. É a promessa "at its door" posta em prática.

## 9. Data dos dados e créditos visíveis
- "Data as of DD.MM.YYYY · Zefix/LINDAS · swisstopo · OSM" no rodapé da legenda. Credibilidade e atribuição exigida pelas licenças.

## 10. Evidência de impacto (para o campo Impact)
- Juntar o que existe: estrelas e forks no GitHub (`gh api repos/rafapolo/swissviz`) e menções e compartilhamentos conhecidos.
- Opcional: contador de visitas sem cookies (Plausible/GoatCounter) até a cerimônia, com aviso no README, porque hoje o site promete "no tracking". Decidir antes de instalar.
- Enviar o link a 3–5 pessoas (jornalista, professor, alguém da Opendata.ch) e citar o retorno no Impact.
