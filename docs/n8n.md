# Integração com n8n

A pasta `n8n/` contém um workflow exportado (`cv-shield-analyze-resume.json`) que envia um currículo para a API do CV Shield e mostra o relatório.

## Workflow

1. **Receber currículo (formulário)**: um Form Trigger do n8n que cria uma página web com um campo de upload de PDF.
2. **Analisar com CV Shield**: um nó HTTP Request que envia o PDF para `POST http://127.0.0.1:8000/analyze` e recebe o relatório.

## Como usar

1. Inicie a API (veja o Início Rápido no README principal) e o n8n.
2. No n8n, abra o menu do workflow, escolha **Import from file...** e selecione `n8n/cv-shield-analyze-resume.json`.
3. Clique em **Execute workflow**, envie um PDF no formulário que abrir e confira a saída do nó HTTP Request.

## Detalhes que vale saber

- O n8n nomeia o campo binário com o rótulo do campo do formulário, trocando os caracteres que ele não aceita. O rótulo `Currículo` vira `Curr_culo`, que é o valor que o nó HTTP Request espera em **Input Data Field Name**. Se você renomear o campo do formulário, atualize esse valor também.
- O n8n restringe quais pastas os nós de arquivo podem ler, então ler um PDF de uma pasta qualquer do projeto falha com "Access to the file is not allowed". Usar um formulário de upload evita isso.
- O JSON exportado não contém credenciais nem chaves de API. A chave da Groq fica só no arquivo `.env` da API; o n8n nunca a vê.