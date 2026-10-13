# Limitações Conhecidas e Aprendizados

Este documento reúne os problemas encontrados durante o desenvolvimento do CV Shield, como cada um foi tratado e o que ainda está em aberto.

## Quebras de linha na extração do PDF

Ao testar com PDFs reais (e não só com strings escritas à mão nos testes unitários), descobrimos que a extração do `pypdf` insere quebras de linha exatamente onde o PDF renderiza uma quebra visual. Uma frase suspeita dividida em duas linhas no PDF (por exemplo, "...passed with \nfull score") não casaria com um padrão escrito em uma linha só, já que a comparação de substring trata `\n` e espaço como caracteres diferentes.

Isso foi corrigido normalizando os espaços em branco (quebras de linha e espaços repetidos viram um único espaço) antes da comparação, e coberto por um teste de regressão feito com texto extraído de um PDF real, e não com strings escritas à mão.

## Frases parafraseadas

Isso também revelou uma limitação mais profunda: o detector de frases depende de uma lista fixa de textos conhecidos, então uma instrução parafraseada que evite essas frases exatas não será pega. Isso foi tratado com um segundo detector, estrutural, que inspeciona tamanho de fonte, cor e posição diretamente, independente das palavras. Ele pega com sucesso um caso de teste parafraseado que o detector de frases deixa passar.

## Falso positivo com fundo colorido

O detector estrutural começou assumindo que o fundo da página é branco, então um currículo legítimo com texto branco sobre uma faixa lateral colorida (um padrão de design comum, em `examples/test_colored_band_resume.pdf`) era sinalizado como falso positivo. Isso ficou registrado por um tempo em um teste `@expectedFailure`.

Foi corrigido na Etapa 10: o detector rastreia os retângulos preenchidos desenhados atrás do texto e só marca texto quase branco quando o contraste com o fundo é menor que 3:1 (a razão mínima de contraste da WCAG). A limitação que sobrou: só retângulos preenchidos contam como fundo, então um fundo em imagem ou em degradê ainda não é reconhecido.

## Versões do pypdf

Também descobrimos que as coordenadas de texto reportadas pelo `pypdf` variaram entre versões (5.9.0 e 6.19.0) ao testar o mesmo PDF, o que poderia alterar silenciosamente os resultados da detecção de texto oculto. A versão do `pypdf` agora está fixada no `requirements.txt`, na versão em que o detector foi construído e testado.

## Groq no lugar da Anthropic

Para a análise assistida por IA, começamos tentando a API da Anthropic, mas ela exige um plano pago depois de um pequeno crédito inicial. Trocamos para a Groq, que oferece um plano gratuito de verdade (com limite de requisições e sem cartão de crédito). O catálogo de modelos da Groq difere do que a própria documentação lista e pode mudar com o tempo, então o nome do modelo é confirmado consultando `client.models.list()` na conta real, em vez de ser fixado no código a partir da documentação.

## Dependências que faltavam

Ao preparar a API, descobrimos que o `requirements.txt` listava só o `pypdf`, embora o projeto já importasse `groq` e `python-dotenv` desde a etapa de IA. Um clone novo falharia na importação. Agora todas as dependências diretas estão listadas, com versões fixadas.

## Pipeline reutilizável

Para tornar o pipeline reutilizável, a lógica de análise foi movida da `main()` para uma função que devolve o relatório (`analyze_pdf`). O script de linha de comando e a API chamam a mesma função, em vez de cada um manter uma cópia própria.

## Detalhes do n8n

Ao montar o workflow do n8n, as restrições de acesso a arquivos do n8n e o jeito como ele nomeia campos binários causaram dois erros nada óbvios. Trocar o nó de leitura de arquivo por um formulário de upload evitou o primeiro e deixou o workflow mais fácil de usar (detalhes em [n8n.md](n8n.md)).

## Ataque visível e parafraseado

Um currículo com a manipulação em texto normal e visível, escrita com palavras diferentes das da lista (`examples/CV_Henrique_visible.pdf`), passava pelos dois detectores e a IA nem chegava a rodar, então o relatório dizia `none`, como se o currículo estivesse limpo. Agora, sem achados, o relatório devolve `not_reviewed` ("a IA não leu"), porque a ausência de achados locais não prova que o currículo está limpo. O interruptor `AI_REVIEW_MODE=always` faz a IA ler todo currículo e pega esse caso, ao custo de gastar mais cota e enviar o texto de todos à Groq. O limite de texto enviado à IA subiu de 4000 para 12000 caracteres, porque o ataque costuma estar no fim do currículo, e o relatório marca `text_truncated` quando precisa cortar.

## A IA pode citar o que não está no currículo

Para mostrar a mensagem escondida de cada currículo sinalizado, a IA também devolve a frase exata que achou suspeita (`suspicious_text`). Como um modelo pode errar ou inventar, o código confere se a frase existe no texto que a IA recebeu (ignorando maiúsculas, espaços e quebras de linha, que o PDF costuma partir) e grava `suspicious_text_found`. Se a frase não existir, o relatório HTML mostra um aviso para conferir o PDF antes de confiar nela.

## Resposta da IA cortada pelo limite de tokens

O modelo `openai/gpt-oss-120b` gasta parte do limite de tokens da resposta "pensando". Medimos uma resposta de 436 tokens, dos quais 280 foram só de raciocínio, contra um limite de 500. Em algumas rodadas o raciocínio era um pouco maior, a resposta era cortada no meio do JSON e o parecer virava `unknown`, de forma intermitente. A correção foi subir o limite para 2000 tokens e, quando a Groq informa que a resposta foi cortada (`finish_reason` igual a `length`), dizer isso no parecer em vez de um erro genérico de JSON. A causa só apareceu porque imprimimos o `finish_reason` e o uso de tokens de uma chamada real.

## Lote de currículos

O lote (`python -m src.batch pasta`) reaproveita o `analyze_pdf`, então não duplica a lógica de análise. Algumas decisões:

- Um PDF quebrado vira "erro" na lista e não derruba os outros.
- Um currículo é "atenção" quando os detectores acham algo ou a IA dá risco `low`, `medium` ou `high`. `not_reviewed`, `none` e `unknown` sem achados contam como "ok", porque, no modo padrão, quase todo currículo seria sinalizado se `not_reviewed` contasse. Por isso o relatório avisa que "ok" não prova que o currículo está limpo.
- O relatório HTML é um arquivo único, sem recursos externos, e todo texto vindo de currículo ou da IA passa por `html.escape`: o conteúdo de um currículo é dado não confiável e não pode virar código na página (há testes com `<script>`).
- O relatório tem trechos dos currículos, então o `.gitignore` ignora `relatorio_*.html`.

## Aviso do httpx nos testes

Ao rodar os testes da API, o Starlette imprime um aviso de depreciação dizendo que usar o `httpx` com o cliente de teste dele está obsoleto e que o `httpx2` deve ser instalado no lugar. Os testes passam com a versão fixada do `httpx`, então isso não bloqueia nada, mas vale revisar na próxima atualização das dependências.