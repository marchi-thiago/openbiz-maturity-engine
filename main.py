import os
import json
import markdown
from dotenv import load_dotenv, find_dotenv
from google import genai
from google.genai import types

# Carrega as variáveis de ambiente
load_dotenv()

def obter_dados_interativo(pilar):
    """
    Coleta interativa (fallback)
    """
    print(f"\n--- Coletando dados para: {pilar} ---")
    print("Digite um breve resumo da situação atual deste pilar (ou pressione Enter para usar dados de exemplo):")
    dados = input("> ")
    
    if not dados.strip():
        if pilar == "Gestão Financeira":
            return "O fluxo de caixa é feito em planilhas esporadicamente. Não há DRE estruturado. Mistura de contas PF e PJ."
        elif pilar == "Vendas e Comercial":
            return "Vendas dependem quase que exclusivamente de indicações. Não há CRM ou processo de follow-up."
        elif pilar == "Marketing e Tração":
            return "Postagens esporádicas no Instagram. Nenhum anúncio rodando. Não há clareza de persona."
        elif pilar == "Operações e Processos":
            return "Processos não documentados. Muito retrabalho. O dono apaga incêndios todos os dias."
    return dados

def montar_prompt(empresa, setor, porte, pilar_atual, dados_pilar, historico):
    return f"""DADOS DO DIAGNÓSTICO EM ANDAMENTO:
Empresa: {empresa}
Setor: {setor}
Porte: {porte}

RESUMO DAS ETAPAS ANTERIORES:
{historico}
---

ETAPA ATUAL DO LOOP:
Pilar em Análise: [ {pilar_atual} ]
Dados Coletados neste Pilar:
{dados_pilar}

INSTRUÇÕES DE RESPOSTA PARA ESTE PILAR:
1. Avaliação de Maturidade: Dê uma nota de 1 a 5 para este pilar e justifique com base nos dados.
2. Gargalos Críticos: Liste até 3 gargalos ou pontos ciegos identificados.
3. Plano de Ação Tático: Sugira 3 ações imediatas no formato (O que fazer | Como fazer | Prioridade).
4. Síntese Executiva: Escreva um parágrafo curto resumindo o estado deste pilar para ser anexado ao histórico do relatório final.

Responda em formato Markdown estruturado.
"""

def extrair_sintese(resposta_texto):
    marcadores = ["Síntese Executiva:", "Síntese Executiva", "4. Síntese Executiva:", "4. Síntese Executiva"]
    for marcador in marcadores:
        if marcador in resposta_texto:
            return resposta_texto.split(marcador)[-1].strip()
    return "Síntese não identificada claramente na resposta."

def gerar_html(markdown_text, empresa):
    """
    Converte o Markdown do relatório para HTML estilizado.
    """
    html_content = markdown.markdown(markdown_text, extensions=['tables'])
    
    html_template = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório OpenBiz - {empresa}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; padding: 20px; }}
        h1, h2, h3 {{ color: #2c3e50; }}
        h1 {{ border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ margin-top: 30px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; border: 1px solid #ddd; text-align: left; }}
        th {{ background-color: #f8f9fa; font-weight: bold; }}
        .priority-Alta {{ color: #e74c3c; font-weight: bold; }}
        .priority-Média {{ color: #f39c12; font-weight: bold; }}
        .priority-Baixa {{ color: #27ae60; font-weight: bold; }}
        .executive-summary {{ background-color: #f0f8ff; padding: 20px; border-left: 5px solid #3498db; margin-bottom: 30px; }}
        @media print {{
            body {{ padding: 0; }}
            .page-break {{ page-break-before: always; }}
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>"""
    
    with open("relatorio_final.html", "w", encoding="utf-8") as f:
        f.write(html_template)
    print("✅ Relatório HTML gerado com sucesso (pronto para exportar como PDF).")

def main():
    client = genai.Client()
    
    system_prompt = (
        "Você é o motor de inteligência analítica do OpenBiz Maturity Engine, um projeto open-source "
        "desenvolvido para diagnosticar e acelerar PMEs. Seu papel é atuar como um Consultor Estratégico "
        "de Negócios Sênior.\n"
        "Mantenha um tom profissional, direto, focado em execução e orientado a resultados. "
        "Siga a Metodologia Gestão 360."
    )
    
    print("🚀 Bem-vindo ao OpenBiz Maturity Engine (V2)")
    usar_json = input("Deseja ler os dados do arquivo 'dados_empresa.json'? (S/N) [S]: ").strip().upper() != 'N'
    
    empresa = "Empresa Fictícia"
    setor = "Serviços"
    porte = "Pequena Empresa"
    dados_pilares_json = {}
    
    if usar_json:
        if os.path.exists("dados_empresa.json"):
            with open("dados_empresa.json", "r", encoding="utf-8") as f:
                dados = json.load(f)
                empresa = dados.get("empresa", empresa)
                setor = dados.get("setor", setor)
                porte = dados.get("porte", porte)
                dados_pilares_json = dados.get("pilares", {})
            print(f"✅ Dados carregados: {empresa} ({setor})")
        else:
            print("❌ Arquivo 'dados_empresa.json' não encontrado. Usando modo interativo.")
            usar_json = False
            
    if not usar_json:
        empresa = input("Nome da Empresa: ") or empresa
        setor = input("Setor de Atuação: ") or setor
        porte = input("Porte da Empresa: ") or porte
    
    pilares = ["Gestão Financeira", "Vendas e Comercial", "Marketing e Tração", "Operações e Processos"]
    historico_acumulado = "Nenhum pilar analisado ainda."
    relatorio_final = []
    
    for pilar in pilares:
        if usar_json:
            dados_pilar = dados_pilares_json.get(pilar, f"Sem dados para {pilar}.")
        else:
            dados_pilar = obter_dados_interativo(pilar)
            
        prompt_usuario = montar_prompt(empresa, setor, porte, pilar, dados_pilar, historico_acumulado)
        print(f"\nProcessando análise de {pilar} via LLM...")
        
        try:
            response = client.models.generate_content(
                model='gemini-3.5-flash',
                contents=prompt_usuario,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.3,
                ),
            )
            resposta_texto = response.text
            relatorio_final.append({"pilar": pilar, "analise": resposta_texto})
            sintese = extrair_sintese(resposta_texto)
            
            if "Nenhum pilar analisado ainda." in historico_acumulado:
                historico_acumulado = ""
                
            historico_acumulado += f"\n- {pilar}: {sintese}\n"
            print(f"✅ Análise de {pilar} concluída!")
        except Exception as e:
            print(f"❌ Erro ao analisar {pilar}: {e}")
            break

    # Sumário Executivo Final
    print("\n🧠 Gerando Sumário Executivo e Matriz de Prioridades...")
    prompt_sumario = f"""
    Com base no histórico acumulado das análises dos pilares da empresa {empresa} ({setor}, {porte}):
    {historico_acumulado}
    
    Gere um "Sumário Executivo e Matriz de Prioridades". 
    1. Resuma em 2 parágrafos a situação global da empresa.
    2. Liste as 3 principais prioridades estratégicas absolutas (independentemente do pilar) que o dono deve focar nos próximos 30 dias.
    Responda em Markdown.
    """
    
    try:
        response_sumario = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt_sumario,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.4,
            ),
        )
        sumario_texto = response_sumario.text
        print("✅ Sumário gerado!")
    except Exception as e:
        print(f"❌ Erro ao gerar sumário: {e}")
        sumario_texto = "Erro ao gerar sumário executivo."

    # Compilação e Exportação
    markdown_completo = f"# Diagnóstico de Maturidade: {empresa}\n\n"
    markdown_completo += f"<div class='executive-summary'>\n\n## Sumário Executivo\n\n{sumario_texto}\n\n</div>\n\n"
    
    for item in relatorio_final:
        markdown_completo += f"<div class='page-break'></div>\n\n## Pilar: {item['pilar']}\n\n{item['analise']}\n\n---\n\n"
        
    with open("relatorio_final.md", "w", encoding="utf-8") as f:
        f.write(markdown_completo)
    
    gerar_html(markdown_completo, empresa)
    
    print(f"\n🚀 Relatórios finais salvos em 'relatorio_final.md' e 'relatorio_final.html'.")

if __name__ == "__main__":
    main()
