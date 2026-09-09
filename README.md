# OpenBiz Maturity Engine 🚀

O **OpenBiz Maturity Engine** é um motor de inteligência analítica open-source desenvolvido para diagnosticar e acelerar Pequenas e Médias Empresas (PMEs). Ele atua como um Consultor Estratégico de Negócios Sênior automatizado, utilizando Inteligência Artificial (LLMs) e a Metodologia Gestão 360 para identificar gargalos operacionais e gerar planos de ação táticos.

## 🧠 Arquitetura: Prompt Chaining e Memória Acumulativa
Este projeto utiliza um padrão avançado de IA chamado **Prompt Chaining** (Encadeamento de Prompts). 
O diagnóstico não analisa a empresa de forma fragmentada. Ele itera sobre 4 pilares fundamentais:
1. **Gestão Financeira**
2. **Vendas e Comercial**
3. **Marketing e Tração**
4. **Operações e Processos**

A cada iteração, a síntese do pilar analisado é injetada no contexto do próximo pilar. Isso permite que a IA "lembre" que a empresa tem, por exemplo, problemas de caixa ao analisar o pilar de Marketing, resultando em um diagnóstico integrado, sistêmico e realista. Ao final, o motor gera um **Sumário Executivo e Matriz de Prioridades**.

## 🛠️ Instalação

1. Clone o repositório:
```bash
git clone https://github.com/SeuUsuario/openbiz-maturity-engine.git
cd openbiz-maturity-engine
```

2. Crie um ambiente virtual e instale as dependências:
```bash
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure os provedores:
Copie `.env.example` para `.env` e preencha somente as chaves dos provedores que você pretende usar:
```env
GEMINI_API_KEY=sua_chave_gemini
ANTHROPIC_API_KEY=sua_chave_claude
AI_PRIMARY_PROVIDER=gemini
AI_FALLBACK_PROVIDER=claude
AI_FALLBACK_ENABLED=false
```

Os modelos padrão são `gemini-3.5-flash` e `claude-sonnet-4-20250514`. Eles podem ser substituídos por `AI_GEMINI_MODEL` e `AI_CLAUDE_MODEL` conforme a disponibilidade da conta e do ambiente. Para habilitar fallback, configure as duas chaves e altere `AI_FALLBACK_ENABLED` para `true`.

Nunca versione `.env` nem coloque chaves em código, prompts, relatórios ou logs.

## 🚀 Como Usar

Você pode fornecer os dados da empresa de forma **interativa** pelo terminal ou de forma **dinâmica via arquivo JSON**.

### Modo JSON (Recomendado)
1. Copie o arquivo de exemplo: `cp dados_empresa.example.json dados_empresa.json`.
2. Preencha o arquivo `dados_empresa.json` com o contexto real da empresa.
3. Rode o script principal:
```bash
python main.py
```
O sistema reconhecerá o arquivo e realizará toda a análise automaticamente.

### Saída (Output)
O script irá gerar dois arquivos no diretório raiz:
- `relatorio_final.md`: O diagnóstico completo em Markdown.
- `relatorio_final.html`: Um relatório estilizado e formatado para apresentação. **Dica:** Abra o arquivo HTML em seu navegador (Chrome/Edge) e use o atalho `Ctrl+P` (ou `Cmd+P`) e escolha **Salvar como PDF** para gerar um documento PDF perfeito e elegante.

## 📄 Licença
Este projeto está licenciado sob a Licença MIT. Veja o arquivo `LICENSE` para mais detalhes.
