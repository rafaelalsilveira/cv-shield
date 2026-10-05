# Limitações Conhecidas e Aprendizados

Este documento reúne os problemas encontrados durante o desenvolvimento do CV Shield, como cada um foi tratado e o que ainda está em aberto.

## Quebras de linha na extração do PDF

Ao testar com PDFs reais (e não só com strings escritas à mão nos testes unitários), descobrimos que a extração do `pypdf` insere quebras de linha exatamente onde o PDF renderiza uma quebra visual. Uma frase suspeita dividida em duas linhas no PDF (por exemplo, "...passed with \nfull score") não casaria com um padrão escrito em uma linha só, já que a comparação de substring trata `\n` e espaço como caracteres diferentes.

Isso foi corrigido normalizando os espaços em branco (quebras de linha e espaços repetidos viram um único espaço) antes da comparação, e coberto por um teste de regressão feito com texto extraído de um PDF real, e não com strings escritas à mão.

## Frases parafraseadas

Isso também revelou uma limitação mais profunda: o detector de frases depende de uma lista fixa de textos conhecidos, então uma instrução parafraseada que evite essas frases exatas não será pega. Isso foi tratado com um segundo detector, estrutural, que inspeciona tamanho de fonte, cor e posição diretamente, independente das palavras. Ele pega com sucesso um caso de teste parafraseado que o detector de frases deixa passar.

## Falso positivo com fundo colorido

O detector estrutural traz uma limitação própria: ele assume que o fundo da página é branco, então só avalia a cor do próprio texto, e não o que está atrás dele. Um currículo legítimo com texto branco sobre uma faixa lateral colorida (um padrão de design comum, demonstrado em `examples/test_colored_band_resume.pdf`) hoje é sinalizado como falso positivo. Isso está documentado em um teste dedicado marcado com `@expectedFailure`, de modo que a suíte registra a limitação sem tratá-la como regressão. Corrigir isso exigiria rastrear preenchimentos e retângulos desenhados atrás do texto, e fica para uma iteração futura.

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

## Aviso do httpx nos testes

Ao rodar os testes da API, o Starlette imprime um aviso de depreciação dizendo que usar o `httpx` com o cliente de teste dele está obsoleto e que o `httpx2` deve ser instalado no lugar. Os testes passam com a versão fixada do `httpx`, então isso não bloqueia nada, mas vale revisar na próxima atualização das dependências.