import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from google import genai
from fpdf import FPDF
from datetime import datetime
import pandas as pd
import io

# --- Configurações da Página ---
st.set_page_config(page_title="InvestAI - Dashboard", page_icon="📈", layout="wide")

# Estilização CSS para emular a interface StatusInvest
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .kpi-card {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        border: 1px solid #e0e0e0;
    }
    .kpi-label { font-size: 12px; color: #666; font-weight: bold; }
    .kpi-value { font-size: 22px; font-weight: bold; color: #1f77b4; }
    </style>
    """, unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ InvestAI Config")
    gemini_key = st.text_input("Gemini API Key", type="password", help="Pegue sua chave em aistudio.google.com")
    periodo_opção = st.selectbox("Período do Gráfico", 
                                options=['1mo', '3mo', '1y', '3y', '5y'], 
                                index=2,
                                format_func=lambda x: {'1mo':'30 Dias', '3mo':'3 Meses', '1y':'1 Ano', '3y':'3 Anos', '5y':'5 Anos'}[x])

# --- Funções de Apoio ---
def resolver_ticker(cliente, entrada):
    """Usa o Gemini para traduzir o nome da empresa em um ticker da B3"""
    prompt = f"Retorne APENAS o ticker da B3 (ex: PETR4) para a empresa: {entrada}. Não explique nada."
    try:
        res = cliente.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        return res.text.strip().upper().replace(".SA", "")
    except:
        return entrada.upper()

def get_kpis(ticker):
    """Busca dados fundamentalistas e cotação"""
    try:
        acao = yf.Ticker(f"{ticker}.SA")
        hist = acao.history(period="1y")
        if hist.empty: return None
        
        info = acao.info
        val_atual = info.get('currentPrice', hist['Close'].iloc[-1])
        min_52 = hist['Low'].min()
        max_52 = hist['High'].max()
        dy = (info.get('dividendYield', 0) * 100)
        val_12m = ((hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1) * 100
        
        return {
            "nome": info.get('shortName', ticker),
            "atual": val_atual, "min": min_52, "max": max_52,
            "dy": dy, "val_12m": val_12m, "hist": hist
        }
    except:
        return None

def plot_grafico(ticker, periodo):
    """Gera o gráfico estilizado para o Streamlit"""
    hist = yf.Ticker(f"{ticker}.SA").history(period=periodo)
    fig, ax = plt.subplots(figsize=(10, 4), dpi=100)
    ax.plot(hist.index, hist['Close'], color='#1f77b4', linewidth=2)
    ax.fill_between(hist.index, hist['Close'], color='#1f77b4', alpha=0.1)
    
    ax.set_title(f"Histórico {ticker}", loc='left', fontsize=12, fontweight='bold')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b/%y'))
    plt.tight_layout()
    return fig

# --- Interface Principal ---
st.title("🚀 InvestAI Web")
busca = st.text_input("Qual empresa você quer analisar hoje?", placeholder="Ex: Vale, Itaú, PETR4...")

if busca:
    if not gemini_key:
        st.error("❌ Por favor, insira sua Gemini API Key na barra lateral.")
    else:
        cliente = genai.Client(api_key=gemini_key)
        
        with st.spinner("🔍 Identificando ticker e coletando dados..."):
            ticker = resolver_ticker(cliente, busca)
            dados = get_kpis(ticker)
            
            if dados:
                st.subheader(f"📊 {ticker} - {dados['nome']}")
                
                # Cards de Indicadores
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.markdown(f"<div class='kpi-card'><p class='kpi-label'>VALOR ATUAL</p><p class='kpi-value'>R$ {dados['atual']:.2f}</p></div>", unsafe_allow_html=True)
                with c2: st.markdown(f"<div class='kpi-card'><p class='kpi-label'>MIN/MÁX 52S</p><p class='kpi-value'>R$ {dados['min']:.2f} / {dados['max']:.2f}</p></div>", unsafe_allow_html=True)
                with c3: st.markdown(f"<div class='kpi-card'><p class='kpi-label'>DIVIDEND YIELD</p><p class='kpi-value'>{dados['dy']:.2f}%</p></div>", unsafe_allow_html=True)
                with c4: 
                    cor = "green" if dados['val_12m'] >= 0 else "red"
                    st.markdown(f"<div class='kpi-card'><p class='kpi-label'>VALORIZAÇÃO (12M)</p><p class='kpi-value' style='color:{cor}'>{dados['val_12m']:.2f}%</p></div>", unsafe_allow_html=True)

                # Gráfico
                st.write("")
                figura = plot_grafico(ticker, periodo_opção)
                st.pyplot(figura)

                # Análise da IA
                st.divider()
                st.markdown(f"### 🧠 Raio-X Estratégico")
                prompt_analise = (
                    f"Analise o ativo {ticker}. Preço: R${dados['atual']:.2f}, DY: {dados['dy']:.2f}%. "
                    f"Escreva 3 parágrafos objetivos sobre fundamentos e visão para 2026. "
                    f"Não use blocos de código markdown na resposta, apenas texto com **negrito**."
                )
                
                try:
                    res_ia = cliente.models.generate_content(model='gemini-2.5-flash', contents=prompt_analise)
                    texto_final = res_ia.text.replace("```markdown", "").replace("```", "")
                    st.markdown(texto_final)
                except:
                    st.write("⚠️ Erro ao gerar análise de IA.")

            else:
                st.error(f"❌ Não conseguimos encontrar dados para '{ticker}'. Verifique se o nome está correto.")
