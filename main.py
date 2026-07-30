import os
from dotenv import load_dotenv, find_dotenv
from google import genai
from google.genai import types

# Carrega as variáveis de ambiente (ex: GEMINI_API_KEY)
load_dotenv(find_dotenv())

def obter_dados(pilar):
    """
    Função de mock para simular a coleta de dados de um pilar.
    Em um ambiente real, isso viria de um formulário ou banco de dados.
    """
    print(f"\n--- Coletando dados para: {pilar} ---")
    print("Digite um breve resumo da situação atual deste pilar (ou pressione Enter para usar dados de exemplo):")
    dados = input("> ")
    
    if not dados.strip():
        # Retorna dados mockados para facilitar o teste inicial
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
    """
    Extrai apenas a parte da 'Síntese Executiva' da resposta do LLM 
    para não inflar demais o histórico.
    """
    # Uma heurística simples para o MVP: procurar por 'Síntese Executiva' e pegar o que vem depois
    marcadores = ["Síntese Executiva:", "Síntese Executiva", "4. Síntese Executiva:", "4. Síntese Executiva"]
    for marcador in marcadores:
        if marcador in resposta_texto:
            return resposta_texto.split(marcador)[-1].strip()
    return "Síntese não identificada claramente na resposta."

def main():
    # Inicializa o cliente do Gemini
    # Certifique-se de ter GEMINI_API_KEY no seu arquivo .env
    client = genai.Client()
    
    # Prompt do Sistema (Persona do Motor)
    system_prompt = (
        "Você é o motor de inteligência analítica do OpenBiz Maturity Engine, um projeto open-source "
        "desenvolvido para diagnosticar e acelerar PMEs. Seu papel é atuar como um Consultor Estratégico "
        "de Negócios Sênior.\n"
        "Mantenha um tom profissional, direto, focado em execução e orientado a resultados. "
        "Siga a Metodologia Gestão 360."
    )
    
    # Dados base da empresa analisada
    print("Bem-vindo ao OpenBiz Maturity Engine (MVP)")
    empresa = input("Nome da Empresa: ") or "Empresa Fictícia"
    setor = input("Setor de Atuação: ") or "Serviços"
    porte = input("Porte da Empresa: ") or "Pequena Empresa"
    
    pilares = [
        "Gestão Financeira", 
        "Vendas e Comercial", 
        "Marketing e Tração", 
        "Operações e Processos"
    ]
    
    historico_acumulado = "Nenhum pilar analisado ainda."
    relatorio_final = []
    
    for pilar in pilares:
        dados_pilar = obter_dados(pilar)
        
        prompt_usuario = montar_prompt(
            empresa=empresa,
            setor=setor,
            porte=porte,
            pilar_atual=pilar,
            dados_pilar=dados_pilar,
            historico=historico_acumulado
        )
        
        print(f"\nProcessando análise de {pilar} via LLM...")
        
        try:
            # Chamada real para a API do Gemini
            # Usaremos o gemini-2.5-flash como padrão (é rápido, custo-benefício e bom para textos estruturados)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt_usuario,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.3,
                ),
            )
            
            resposta_texto = response.text
            
            # Armazena o resultado e atualiza o histórico para a próxima volta do loop
            relatorio_final.append({"pilar": pilar, "analise": resposta_texto})
            sintese = extrair_sintese(resposta_texto)
            
            # Remove a mensagem inicial se for a primeira vez
            if "Nenhum pilar analisado ainda." in historico_acumulado:
                historico_acumulado = ""
                
            historico_acumulado += f"\n- {pilar}: {sintese}\n"
            
            print(f"✅ Análise de {pilar} concluída!")
            
        except Exception as e:
            print(f"❌ Erro ao analisar {pilar}: {e}")
            break

    # Compilação do relatório executivo no console e em arquivo
    print("\n" + "="*50)
    print("RELATÓRIO EXECUTIVO COMPLETO")
    print("="*50)
    
    with open("relatorio_final.md", "w", encoding="utf-8") as f:
        f.write(f"# Diagnóstico de Maturidade: {empresa}\n\n")
        for item in relatorio_final:
            print(f"\n--- {item['pilar']} ---")
            print(item['analise'])
            
            # Grava no arquivo Markdown
            f.write(f"## Pilar: {item['pilar']}\n\n")
            f.write(item['analise'] + "\n\n")
            f.write("---\n\n")
            
    print("\nRelatório final também foi salvo em 'relatorio_final.md'.")

if __name__ == "__main__":
    main()
