import streamlit as st
import os
import json
from dotenv import load_dotenv
from ai_provider import create_resilient_provider
import time

# Configuração inicial da página Streamlit
st.set_page_config(page_title="OpenBiz Maturity Engine", page_icon="🚀", layout="wide")

# Tenta carregar do .env local (fallback)
load_dotenv()

# --- Funções do Motor Analítico (Adaptadas do main.py) ---
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


# --- Interface Gráfica ---

st.title("🚀 OpenBiz Maturity Engine")
st.markdown("Diagnóstico e Plano de Ação Estratégico (Metodologia Gestão 360)")

# SIDEBAR (Configurações e Dados da Empresa)
with st.sidebar:
    st.header("⚙️ Configurações")
    api_key = st.text_input("Gemini API Key", value=os.environ.get("GEMINI_API_KEY", ""), type="password")
    
    st.divider()
    
    st.header("🏢 Dados da Empresa")
    empresa = st.text_input("Nome da Empresa", value="TechCorp Solutions")
    setor = st.text_input("Setor de Atuação", value="Tecnologia / B2B")
    porte = st.text_input("Porte da Empresa", value="Média Empresa")
    
    st.divider()
    st.markdown("*OpenBiz Maturity Engine v2.0 - Open Source*")

# MAIN AREA (Coleta dos Pilares)
st.subheader("📊 Situação dos Pilares")
st.info("Descreva a situação atual de cada área da empresa. Quanto mais detalhes sobre as dores, melhor o diagnóstico da IA.")

col1, col2 = st.columns(2)

with col1:
    fin_data = st.text_area("💰 Gestão Financeira", height=120, placeholder="Ex: Fluxo de caixa confuso, sem DRE, mistura contas PF e PJ...")
    mkt_data = st.text_area("📣 Marketing e Tração", height=120, placeholder="Ex: Sem anúncios, apenas Instagram sem estratégia, leads fracos...")

with col2:
    ven_data = st.text_area("🤝 Vendas e Comercial", height=120, placeholder="Ex: Dependência de indicação, sem CRM, follow-up falho...")
    ope_data = st.text_area("⚙️ Operações e Processos", height=120, placeholder="Ex: Processos de cabeça, retrabalho constante, gargalo no dono...")

# Botão para preencher com dados mockados (para facilitar testes rápidos)
if st.button("Preencher com Dados de Exemplo"):
    # Como st.text_area não tem st.session_state atrelado nativamente sem keys, 
    # faremos uma injeção simples caso o usuário não saiba usar session_state
    st.warning("Dados de exemplo carregados! (Para evitar sobreposição, recarregue a página se os campos não atualizarem sozinhos ou cole os dados abaixo)")
    st.code('''Financeiro: "Controle rígido de custos, mas sem previsibilidade de receita. DRE mensal atrasado."\nVendas: "Time de 3 vendedores, sem CRM definido. Ciclo de vendas longo (6 meses)."\nMarketing: "Foco em Inbound Marketing, mas com baixa conversão de Leads para MQLs."\nOperações: "Processos mapeados no papel, mas não seguidos pela equipe. Muito retrabalho na entrega."''')

st.divider()

if st.button("🚀 Gerar Diagnóstico 360", type="primary"):
    if not api_key:
        st.error("Por favor, insira a chave da API do Gemini na barra lateral.")
        st.stop()
        
    if not fin_data or not ven_data or not mkt_data or not ope_data:
        st.warning("Recomendamos preencher (mesmo que resumidamente) os 4 pilares antes de rodar, ou clicar no botão de Dados de Exemplo.")
    
    # Inicializa cliente
    provider = create_resilient_provider(api_key=api_key)
    system_prompt = (
        "Você é o motor de inteligência analítica do OpenBiz Maturity Engine, um projeto open-source "
        "desenvolvido para diagnosticar e acelerar PMEs. Seu papel é atuar como um Consultor Estratégico "
        "de Negócios Sênior.\n"
        "Mantenha um tom profissional, direto, focado em execução e orientado a resultados. "
        "Siga a Metodologia Gestão 360."
    )
    
    # Mapeamento do Dicionário
    dados_pilares = {
        "Gestão Financeira": fin_data or "Sem dados reportados.",
        "Vendas e Comercial": ven_data or "Sem dados reportados.",
        "Marketing e Tração": mkt_data or "Sem dados reportados.",
        "Operações e Processos": ope_data or "Sem dados reportados."
    }
    
    historico_acumulado = "Nenhum pilar analisado ainda."
    relatorio_final = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Container para o resultado final
    result_container = st.container()
    
    for idx, pilar in enumerate(dados_pilares.keys()):
        status_text.text(f"Analisando {pilar} (Encadeando prompts...)")
        
        prompt_usuario = montar_prompt(empresa, setor, porte, pilar, dados_pilares[pilar], historico_acumulado)
        
        try:
            response = provider.generate(
                contents=prompt_usuario,
                system_instruction=system_prompt,
                temperature=0.3,
            )
            resposta_texto = response.text
            relatorio_final.append({"pilar": pilar, "analise": resposta_texto})
            sintese = extrair_sintese(resposta_texto)
            
            if "Nenhum pilar analisado ainda." in historico_acumulado:
                historico_acumulado = ""
                
            historico_acumulado += f"\n- {pilar}: {sintese}\n"
            
        except Exception as e:
            st.error(f"Erro ao processar o pilar {pilar}: {e}")
            st.stop()
            
        # Atualiza a barra de progresso (20% por pilar, total 80%)
        progress_bar.progress(int(((idx+1)/5)*100))
        time.sleep(0.5)

    status_text.text("Gerando Sumário Executivo Global...")
    prompt_sumario = f"""
    Com base no histórico acumulado das análises dos pilares da empresa {empresa} ({setor}, {porte}):
    {historico_acumulado}
    
    Gere um "Sumário Executivo e Matriz de Prioridades". 
    1. Resuma em 2 parágrafos a situação global da empresa de forma sistêmica.
    2. Liste as 3 principais prioridades estratégicas absolutas (independentemente do pilar) que o dono deve focar nos próximos 30 dias para estabilizar ou acelerar o negócio.
    Responda em Markdown profissional.
    """
    
    try:
        response_sumario = provider.generate(
            contents=prompt_sumario,
            system_instruction=system_prompt,
            temperature=0.4,
        )
        sumario_texto = response_sumario.text
    except Exception as e:
        st.error(f"Erro ao gerar sumário: {e}")
        sumario_texto = "Erro na geração do sumário."

    # Finaliza progresso (100%)
    progress_bar.progress(100)
    status_text.text("✅ Relatório Gerado com Sucesso!")
    
    # Compilação Markdown
    markdown_completo = f"# Diagnóstico de Maturidade: {empresa}\n\n"
    markdown_completo += f"## Sumário Executivo\n\n{sumario_texto}\n\n---\n\n"
    
    for item in relatorio_final:
        markdown_completo += f"## Pilar: {item['pilar']}\n\n{item['analise']}\n\n---\n\n"
    
    # Exibição na Interface
    with result_container:
        st.success("Diagnóstico concluído! O histórico foi repassado camada a camada para garantir uma análise sistêmica.")
        st.download_button(
            label="📄 Baixar Relatório (Markdown)",
            data=markdown_completo,
            file_name=f"Relatorio_{empresa.replace(' ', '_')}.md",
            mime="text/markdown"
        )
        
        st.markdown(markdown_completo, unsafe_allow_html=True)
