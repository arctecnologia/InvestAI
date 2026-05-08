import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from google import genai
from fpdf import FPDF
from datetime import datetime
import pandas as pd

# Configuração da Página
st.set_page_config(page_title="InvestAI - Dashboard", page_icon="📈", layout="wide")

# Estilização CSS para os Cards
st.markdown("""
    <style>
    .kpi-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        border-left: 5px solid #1f77b4;
    }
    .kpi-value {
        font-size: 24px;
        font-weight: bold;
        color: #0e1117;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Sidebar de Configurações ---
with st.sidebar:
    st.title("⚙️ Configurações")
    gemini_key = st.text_input("Gemini API Key", type="password")
    periodo = st.selectbox("Período do Gráfico", 
                          options=['1mo', '3mo', '1y', '3y', '5y'], 
                          format_func=lambda x: {'1mo':'30 Dias', '3mo':'3 Meses', '1y':'1 Ano', '3y':'3 Anos', '5y':'5 Anos'}[x],
                          index=2)

# --- Lógica de Negócio (Adaptada do nosso InvestAI) ---
def get_data(ticker):
    acao = yf.Ticker(f"{ticker}.SA")
    info = acao.info
    hist = acao.history(period="1y")
    
    val_atual = info.get('currentPrice', hist['Close'].iloc[-1] if not hist.empty else 0)
    min_52 = hist['Low'].min() if not hist.empty else 0
    max_52 = hist['High'].max() if not hist.empty else 0
    
    return {
        "ticker": ticker,
        "nome": info.get('shortName', ticker),
        "atual": val_atual,
        "min": min_52,
        "max": max_52,
        "dy": (info.get('dividendYield', 0) * 100),
        "val_12m": ((hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1) * 100 if not hist.empty else 0
    }

# --- Interface Principal ---
st.title("🚀 InvestAI - Inteligência Financeira")
st.subheader("Transformando dados da B3 em decisões estratégicas.")

busca = st.text_input("Digite o nome da empresa ou Ticker (ex: Vale, PETR4):", placeholder="Busque aqui...")

if busca:
    # 1. NLP para Ticker (Simulado ou via Gemini se a chave estiver presente)
    ticker = busca.upper() # Em um app real, usaríamos o método descobrir_ticker aqui
    
    with st.spinner(f"Analisando {ticker}..."):
        data = get_data(ticker)
        
        # 2. Exibição dos Cards (KPIs)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"<div class='kpi-card'>VALOR ATUAL<br><span class='kpi-value'>R$ {data['atual']:.2f}</span></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='kpi-card'>MÍN/MÁX 52S<br><span class='kpi-value'>R$ {data['min']:.2f} / {data['max']:.2f}</span></div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='kpi-card'>DIVIDEND YIELD<br><span class='kpi-value'>{data['dy']:.2f}%</span></div>", unsafe_allow_html=True)
        with col4:
            cor = "green" if data['val_12m'] >= 0 else "red"
            st.markdown(f"<div class='kpi-card'>VALORIZAÇÃO (12M)<br><span class='kpi-value' style='color:{cor}'>{data['val_12m']:.2f}%</span></div>", unsafe_allow_html=True)

        # 3. Gráfico Interativo
        hist_plot = yf.Ticker(f"{ticker}.SA").history(period=periodo)
        st.line_chart(hist_plot['Close'])

        # 4. Raio-X da IA (Gemini)
        if gemini_key:
            client = genai.Client(api_key=gemini_key)
            prompt = f"Analise o ativo {ticker}. Preço R${data['atual']}. Gere 3 parágrafos sobre fundamentos e riscos."
            res = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            
            st.divider()
            st.markdown(f"### 🧠 Raio-X do InvestAI para {ticker}")
            st.write(res.text)
            
            # Botão de Exportação (Simulado)
            st.button("📥 Baixar Relatório Completo em PDF")
        else:
            st.warning("⚠️ Insira sua Gemini API Key na sidebar para liberar a análise de IA.")
