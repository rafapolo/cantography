# Tour: roteiro

O tour é um passeio de câmera de ~57 s feito para o vídeo do Swiss Viz Awards. Ele também mostra como usar o site: um cursor desenhado clica nos controles de verdade. Para tocar, use o botão **▶ tour** nos chips de baixo à direita, ou abra `?tour=1`, que começa sozinho quando o mapa termina de carregar. **Esc** ou **✕ esc** interrompem o tour e devolvem filtros, linha do tempo e modo noturno ao estado de antes.

Este arquivo descreve o que acontece em cada cena. Para mudar algo, edite aqui e peça a mudança no código: as cenas ficam em `tourScenes()`, no `index.html`.

## Regras gerais

- **Quadro.** Faixas pretas de cinema em 2,39:1 (no máximo 16% da tela cada) e uma barra de progresso fina na borda da faixa de baixo. Toda a interface fica escondida, menos o controle que a cena está ensinando.
- **Textos.** Em inglês, qualquer que seja o idioma da página. A legenda tem duas partes: um rótulo pequeno em cima (*kicker*) e a frase.
- **Números.** São contados no navegador a partir da linha do tempo; nenhum é fixo no código.
- **Cores.** A legenda só faz sentido com o modo noturno **desligado**: cada forma jurídica aparece na sua cor. O modo noturno volta em Vaud, onde o vermelho dos fechamentos é o que importa.
- **Cursor.** Só aparece em telas largas (acima de 980 px). No celular o tour aplica os filtros sem mostrar os cliques, mas espera o tempo que eles levariam: a câmera pousa antes de girar e o tour dura o mesmo.
- **Celular.** O painel da linha do tempo fica escondido; a data grande no alto à esquerda marca o tempo. A abertura e o fim mostram a Suíça inteira, com o zoom que couber na largura. O cartão da busca abre logo abaixo da busca, longe da legenda.
- **Sair.** O botão **✕ esc** fica no canto de cima à direita, na faixa preta.
- **Movimento reduzido.** Com `prefers-reduced-motion`, a câmera corta de uma tomada para a outra em vez de voar.

## Cenas

Os tempos foram medidos em 2026-10-15, numa janela de 1440×810.

| # | tempo | lugar e câmera | o que acontece | rótulo · frase |
|---|---|---|---|---|
| 0 | 0–5 s | Suíça inteira (zoom 7,15), de cima; desce devagar até zoom 7,6, inclinação 30° | mapa de hoje, modo noturno, todas as formas | **cantography** · *Every Swiss company, lit at its door.* |
| 1a | 5–7 s | voa até Genebra (zoom 12,4, inclinação 60°, rumo −25°) | a barra de busca aparece e o cursor clica no botão do modo noturno (avião), que desliga | **night view** · *Night view off: each legal form in its own colour.* |
| 1b | 7–10,5 s | Genebra | a legenda aparece; o cursor clica em **Deselect all**, depois em **Foundation** e **Association** | **legend** · *Pick legal forms in the legend.* |
| 1c | 10,5–17,5 s | Genebra, girando devagar (rumo até 5°, zoom 12,8) | a linha do tempo corre de jan/2016 até hoje em 7 s; o ano grande aparece no alto à esquerda | **Geneva · 2016–2026** · *N associations and foundations opened in ten years.* (N = 2.009) |
| 2 | 17,5–28,5 s | voa até o centro de Zurique (zoom 13,1, inclinação 66°, rumo 40°), depois gira no sentido contrário | cursor: **Deselect all**, **Corporation (AG)**, **LLC / SARL**; linha do tempo de 2016 até hoje em 7 s | **Zurich · 2016–2026** · *N new AGs and GmbHs in ten years.* (N = 50.769) |
| 3a | 28,5–31 s | voa até Berna, vista de cima (zoom 12,6) | cursor: **Deselect all**, **Sole Proprietorship**; a barra da linha do tempo aparece embaixo | **timeline** · *Play the timeline: every opening and closing since 2018.* |
| 3b | 31–38,5 s | Berna, inclinando até 55° | o cursor aponta o ▶ da linha do tempo, que vira ❚❚; de 2016 até hoje em 6 s | **Bern · 2016–2026** · *N sole proprietors set up shop.* (N = 15.231) |
| 4 | 38,5–47 s | voa até Lausanne (zoom 11,6, inclinação 50°, rumo −30°), gira para −50° | todas as formas; o cursor religa o modo noturno; linha do tempo de jan/2019 a dez/2021 em 6 s, com os fechamentos em vermelho | **Vaud · 2019–2021** · *In 2020 closures fell N%: the year of COVID loans and a pause on debt collection.* (N = 25; se os fechamentos subissem, a frase diria *rose*) |
| 5 | 47–53,5 s | Vevey | some a linha do tempo e volta o mapa de hoje; o cursor clica na busca, "Nestlé Suisse" é digitado letra por letra (1,4 s), o primeiro resultado abre e o cartão fica fixado | **search** · *Any of N companies, at its address.* (N = 795.271) |
| 6 | 53,5–57 s | volta voando para a Suíça inteira (3,5 s) | o cartão fecha | **cantography.ch** · *Switzerland, one company at a time.* |

## De onde vêm os números

- **Aberturas (Genebra, Zurique, Berna):** empresas daquele cantão e daquelas formas jurídicas com data de abertura entre 1/1/2016 e o último dia da linha do tempo. Antes de 2018 só entram as empresas que existem hoje ou que foram canceladas desde então: são as datas de inscrição do registro cantonal.
- **Fechamentos em Vaud:** encerramentos publicados no SHAB em 2020, comparados com 2019. No país inteiro a queda foi de 8%, segundo os dados do SHAB (2019: 31.261; 2020: 28.680). Os empréstimos covid e a suspensão das cobranças (Rechtsstillstand, de 19/3 a 19/4/2020) são o contexto da frase, não uma causa provada.
- **Total da busca:** soma das empresas de hoje nos 26 cantões.

## Ideias que ficaram de fora

- Um mergulho no endereço com mais empresas registradas (Zug, Baar).
- De 1883 até hoje: a Suíça inteira se acendendo desde o primeiro registro comercial.
