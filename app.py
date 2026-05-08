import streamlit as st
import yfinance as yf
import pandas as pd
from google import genai
from datetime import datetime

# --- Configuração de Estilo e Página ---
st.set_page_config(page_title="InvestAI - Dashboard", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .kpi-card {
        background-color: #fcfcfc;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.08);
        border: 1px solid #eeeeee;
    }
    /* Forçando a cor PRETA para todos os textos dos cards */
    .kpi-label { font-size: 13px; color: #000000 !important; font-weight: bold; margin-bottom: 8px; text-transform: uppercase; }
    .kpi-value { font-size: 26px; font-weight: bold; color: #1f77b4 !important; }
    .kpi-sub { font-size: 11px; color: #000000 !important; margin-top: 5px; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

# --- Funções de Inteligência e Dados ---
def resolver_ticker_ia(cliente, entrada):
    """Usa o Gemini para garantir que temos o código correto da B3"""
    prompt = f"Retorne APENAS o código do ticker da B3 para: {entrada}. Exemplo: PETR4. Não escreva frases."
    try:
        res = cliente.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        # Limpeza de texto para evitar que a IA responda frases
        ticker = res.text.strip().upper().split()[-1].replace(".SA", "").replace(":", "").strip()
        return ticker
    except:
        return entrada.upper().strip()

def buscar_dados_robusto(ticker):
    """Tenta várias combinações para encontrar o ativo no Yahoo Finance"""
    tentativas = [f"{ticker}.SA", ticker]
    
    for t in tentativas:
        try:
            acao = yf.Ticker(t)
            # Tenta um histórico curto primeiro para validar se o ticker existe
            hist = acao.history(period="1y")
            
            if not hist.empty:
                # Recuperação de KPIs
                info = acao.info
                val_atual = info.get('currentPrice') or hist['Close'].iloc[-1]
                min_52 = info.get('fiftyTwoWeekLow') or hist['Low'].min()
                max_52 = info.get('fiftyTwoWeekHigh') or hist['High'].max()
                dy = (info.get('dividendYield', 0) * 100)
                val_12m = ((hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1) * 100
                
                return {
                    "ticker": t,
                    "nome": info.get('longName') or info.get('shortName') or ticker,
                    "atual": val_atual, "min": min_52, "max": max_52,
                    "dy": dy, "val_12m": val_12m, "hist": hist
                }
        except:
            continue
    return None

# --- Interface do Usuário (Sidebar) ---
with st.sidebar:
    st.header("⚙️ Configurações")
    gemini_key = st.text_input("Gemini API Key", type="password")
    periodo_opcoes = {"1 Mês": "1mo", "3 Meses": "3mo", "1 Ano": "1y", "5 Anos": "5y"}
    periodo_sel = st.selectbox("Período do Gráfico", list(periodo_opcoes.keys()), index=2)
    periodo_cod = periodo_opcoes[periodo_sel]

# --- Conteúdo Principal ---
st.title("🚀 InvestAI Web")
entrada_usuario = st.text_input("Digite a empresa ou ticker para análise:", placeholder="Ex: JHSF, Vale, Itaú...")

if entrada_usuario:
    if not gemini_key:
        st.info("💡 Por favor, insira a sua API Key do Gemini na barra lateral para ativar a IA.")
    else:
        cliente = genai.Client(api_key=gemini_key)
        
        with st.spinner(f"📡 Conectando à B3 para analisar {entrada_usuario}..."):
            ticker_resolvido = resolver_ticker_ia(cliente, entrada_usuario)
            dados = buscar_dados_robusto(ticker_resolvido)
            
            if dados:
                st.subheader(f"📊 {dados['ticker']} - {dados['nome']}")
                
                # Painel de Cards (Layout inspirado na sua referência)
                c1, c2, c3, c4 = st.columns(4)
                
                with c1:
                    st.markdown(f"""<div class='kpi-card'>
                        <div class='kpi-label'>VALOR ATUAL</div>
                        <div class='kpi-value'>R$ {dados['atual']:.2f}</div>
                    </div>""", unsafe_allow_html=True)
                
                with c2:
                    st.markdown(f"""<div class='kpi-card'>
                        <div class='kpi-label'>MÍN / MÁX (52 S)</div>
                        <div class='kpi-value' style='font-size:20px'>R$ {dados['min']:.2f} / {dados['max']:.2f}</div>
                    </div>""", unsafe_allow_html=True)
                
                with c3:
                    st.markdown(f"""<div class='kpi-card'>
                        <div class='kpi-label'>DIVIDEND YIELD</div>
                        <div class='kpi-value'>{dados['dy']:.2f}%</div>
                        <div class='kpi-sub'>ÚLTIMOS 12 MESES</div>
                    </div>""", unsafe_allow_html=True)
                
                with c4:
                    cor_val = "#008000" if dados['val_12m'] >= 0 else "#FF0000"
                    sinal = "+" if dados['val_12m'] >= 0 else ""
                    st.markdown(f"""<div class='kpi-card'>
                        <div class='kpi-label'>VALORIZAÇÃO (12M)</div>
                        <div class='kpi-value' style='color:{cor_val} !important;'>{sinal}{dados['val_12m']:.2f}%</div>
                    </div>""", unsafe_allow_html=True)

                # Gráfico de Área (Interativo)
                st.write("")
                st.subheader(f"📈 Evolução de Preço ({periodo_sel})")
                hist_grafico = yf.Ticker(dados['ticker']).history(period=periodo_cod)
                st.area_chart(hist_grafico['Close'])

                # Análise de IA
                st.divider()
                st.subheader("🧠 Análise Estratégica InvestAI")
                
                prompt_ia = (
                    f"Atue como um analista financeiro. Analise a {dados['ticker']}. "
                    f"Preço: R${dados['atual']:.2f}. Dividend Yield: {dados['dy']:.2f}%. "
                    "Gere 3 parágrafos curtos com visão de futuro. Use apenas texto e negritos. "
                    "Remova qualquer tag de código como 'markdown' ou 'json'."
                )
                
                try:
                    res_ia = cliente.models.generate_content(model='gemini-2.5-flash', contents=prompt_ia)
                    # Limpeza extra para garantir que não aparecem tags técnicas
                    texto_final = res_ia.text.replace("```markdown", "").replace("```", "").strip()
                    st.markdown(texto_final)
                except:
                    st.error("Ocorreu um erro ao processar a análise da Inteligência Artificial.")
                    
            else:
                st.error(f"❌ Não foi possível encontrar dados para '{ticker_resolvido}'.")
                st.info("Dica: Tente pesquisar pelo nome da empresa (ex: JHSF) ou certifique-se de que o ticker está correto.")
