# Integração com n8n

A pasta `n8n/` contém dois workflows exportados:

- `cv-shield-analyze-resume.json`: analisa **um** currículo por vez.
- `cv-shield-lote.json`: analisa **vários** currículos de uma vez e gera uma página de relatório.

A ideia que guia os dois: **o Python decide, o n8n coordena e a pessoa tem a palavra final.**

## Workflow de um currículo

1. **Receber currículo (formulário)**: um Form Trigger do n8n que cria uma página web com um campo de upload de PDF.
2. **Analisar com CV Shield**: um nó HTTP Request que envia o PDF para `POST http://127.0.0.1:8000/analyze` e recebe o relatório.

### Como usar

1. Inicie a API (veja o Início Rápido no README principal) e o n8n.
2. No n8n, abra o menu do workflow, escolha **Import from file...** e selecione `n8n/cv-shield-analyze-resume.json`.
3. Clique em **Execute workflow**, envie um PDF no formulário que abrir e confira a saída do nó HTTP Request.

## Workflow de lote (vários currículos)

O formulário aceita vários PDFs. O n8n manda um por vez para a API, junta os resultados e pede ao Python a página do relatório.

1. **Receber currículo (formulário)**: o campo de upload aceita vários PDFs.
2. **Separar PDFs**: o formulário entrega todos os PDFs juntos, em um único item. Este nó (um pequeno código em JavaScript) separa em um item por PDF, guardando o nome do arquivo. Ele não depende do nome do campo binário: pega todos os arquivos que chegarem.
3. **Analisar com CV Shield**: chama `POST /analyze` uma vez por PDF. Está configurado para mandar um PDF por vez, com pausa entre eles (*Batching*), tentar de novo até 3 vezes se a chamada falhar e continuar o fluxo mesmo se um PDF der erro, para que um PDF ruim não derrube os outros.
4. **Montar lote**: transforma o resultado de cada chamada em `{file, report}` (deu certo) ou `{file, error}` (falhou).
5. **Gerar relatório**: chama `POST /batch-report` com o lote inteiro.
6. **Gerar arquivo HTML**: transforma a página devolvida pela API em um arquivo `relatorio_lote.html`, para baixar.

### Como usar

1. Inicie a API: `python -m uvicorn src.api:app --reload`.
2. No n8n, crie um workflow novo, abra o menu e escolha **Import from file...** e selecione `n8n/cv-shield-lote.json`.
3. Clique em **Execute workflow** e, no formulário que abrir, envie vários PDFs de uma vez (segure Ctrl ao clicar nos arquivos).
4. Quando terminar, abra o último nó (**Gerar arquivo HTML**), aba **Output**, e clique em **Download**. Abra o `relatorio_lote.html` no navegador.

### Quem faz o quê

- **n8n**: receber os PDFs, separar, chamar a API um por vez, esperar entre as chamadas, tentar de novo, isolar o erro de cada PDF e juntar os resultados.
- **Python**: detectores, regra das pilhas (`classify_report`), conferência da frase apontada pela IA e montagem da página.

### O endpoint `POST /batch-report`

Entrada (JSON):

```json
{
  "folder": "opcional",
  "items": [
    {"file": "a.pdf", "report": {"...": "resposta do /analyze"}},
    {"file": "b.pdf", "error": "texto do erro"}
  ]
}
```

Resposta: `{"summary": {...}, "html": "<página>"}`.

Regras:

- Cada item tem `file` e **exatamente um** entre `report` e `error`; senão a API responde 422.
- Um `report` sem `summary.finding_count` ou sem `findings` também dá 422, citando o nome do arquivo.
- Campos extras (como um `status` enviado pelo cliente) são ignorados: quem decide o status é o `classify_report`.
- Sem `folder`, a página mostra "Enviados pelo n8n".

### As pilhas da página

- **OK**: sem achados dos detectores. "OK" não prova que o currículo está limpo.
- **Atenção**: achados dos detectores ou risco da IA baixo, médio ou alto.
- **Não analisados**: currículos que ninguém leu de verdade. Junta dois casos: a IA falhou e não havia achados locais (`not_analyzed`), ou o PDF não abriu ou a chamada falhou (`error`).

## Detalhes que vale saber

- O n8n nomeia o campo binário com o rótulo do campo do formulário, trocando os caracteres que ele não aceita. O rótulo `Currículo` vira `Curr_culo`, e com vários arquivos o primeiro chega como `Curr_culo_0`. No workflow de um currículo, o nó HTTP Request espera `Curr_culo` em **Input Data Field Name**; se você renomear o campo do formulário, atualize esse valor também. No workflow de lote isso não importa, porque o nó "Separar PDFs" renomeia tudo para `data`.
- O n8n restringe quais pastas os nós de arquivo podem ler, então ler um PDF de uma pasta qualquer do projeto falha com "Access to the file is not allowed". Usar um formulário de upload evita isso.
- Os JSONs exportados não contêm credenciais nem chaves de API. A chave da Groq fica só no arquivo `.env` da API; o n8n nunca a vê.
- **Formato do erro:** quando o `/analyze` falha (por exemplo, com a API desligada), o nó com "continuar se der erro" entrega o item com um campo `error` (com `message`, como `connect ECONNREFUSED 127.0.0.1:8000`) e um campo `details`. O nó "Montar lote" usa só `error.message`, então detalhes técnicos, como caminhos do computador que aparecem no rastreio do erro, não vão para a página. Isso foi confirmado em um teste com a API parada.
- **Pausa entre as chamadas:** o valor inicial é de 2 segundos (*Options → Batching → Batch Interval*, em milissegundos). Ele é provisório: o ideal é ajustar de acordo com o limite da sua conta Groq (página de limites em console.groq.com).
- **O que a nova tentativa cobre:** falha na chamada HTTP (API fora do ar, por exemplo). Se a Groq falha *dentro* da API, ela responde normalmente com risco "unknown", e a página mostra o currículo como "Não analisado". Essa é a decisão do fluxo: avisar em vez de fingir que leu.
- **Testado:** lotes de 1, 2 e 3 PDFs, e um teste com a API parada.
- **Ainda não feito:** mostrar a página direto na tela, ao final do formulário. Hoje ela sai como arquivo para baixar no último nó.
