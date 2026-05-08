import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from google import genai
from datetime import datetime
import pandas as pd

# --- Configuração da Página ---
st.set_page_config(page_title="InvestAI - Dashboard", page_icon="🚀", layout="wide")

# Estilização CSS (Melhoria nas cores e legibilidade)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .kpi-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        border-top: 5px solid #1f77b4;
    }
    .kpi-label { font-size: 14px; color: #000; font-weight: bold; margin-bottom: 5px; }
    .kpi-value { font-size: 24px; font-weight: bold; color: #1f77b4; }
    .kpi-sub { font-size: 11px; color: #666; }
    </style>
    """, unsafe_allow_html=True)

# --- Funções Core com Resiliência ---
def resolver_ticker(cliente, entrada):
    prompt = f"Retorne apenas o ticker da B3 para: {entrada}. Exemplo: PETR4. Não escreva mais nada."
    try:
        res = cliente.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        # Limpeza radical de qualquer lixo de texto
        ticker = res.text.strip().upper().split('\n')[0].replace(".SA", "").replace("TICKER:", "").strip()
        return ticker
    except:
        return entrada.upper().strip()

def buscar_dados_com_fallback(ticker):
    """Técnica de Failover: Se o .info falhar, usamos o histórico"""
    try:
        acao = yf.Ticker(f"{ticker}.SA")
        # Força a busca de histórico de 1 ano para garantir dados
        hist = acao.history(period="1y")
        
        if hist.empty:
            return None

        # Tenta pegar info, se falhar, usa o hist
        info = acao.info
        val_atual = info.get('currentPrice') or hist['Close'].iloc[-1]
        min_52 = info.get('fiftyTwoWeekLow') or hist['Low'].min()
        max_52 = info.get('fiftyTwoWeekHigh') or hist['High'].max()
        dy = (info.get('dividendYield', 0) * 100)
        val_12m = ((hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1) * 100
        
        return {
            "nome": info.get('longName') or ticker,
            "atual": val_atual, "min": min_52, "max": max_52,
            "dy": dy, "val_12m": val_12m, "hist": hist
        }
    except:
        return None

# --- Sidebar ---
with st.sidebar:
    st.header("🔑 Configuração")
    gemini_key = st.text_input("Gemini API Key", type="password")
    periodo_map = {"1 Mês": "1mo", "3 Meses": "3mo", "1 Ano": "1y", "5 Anos": "5y"}
    periodo_label = st.selectbox("Período do Gráfico", list(periodo_map.keys()), index=2)
    periodo_cod = periodo_map[periodo_label]

# --- Interface ---
st.title("🚀 InvestAI Web")
busca = st.text_input("Qual empresa ou ticker deseja analisar?", placeholder="Ex: JHSF, Vale, Itaú...")

if busca:
    if not gemini_key:
        st.warning("⚠️ Por favor, insira a sua API Key na barra lateral para começar.")
    else:
        cliente = genai.Client(api_key=gemini_key)
        
        with st.spinner(f"🔍 Localizando dados para {busca}..."):
            ticker = resolver_ticker(cliente, busca)
            dados = buscar_dados_com_fallback(ticker)
            
            if dados:
                st.header(f"📊 {ticker} - {dados['nome']}")
                
                # Painel de Cards (Cores ajustadas para Preto/Azul conforme solicitado)
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.markdown(f"<div class='kpi-card'><div class='kpi-label'>VALOR ATUAL</div><div class='kpi-value'>R$ {dados['atual']:.2f}</div></div>", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"<div class='kpi-card'><div class='kpi-label'>MIN / MÁX (52 S)</div><div class='kpi-value' style='font-size:18px'>R$ {dados['min']:.2f} / {dados['max']:.2f}</div></div>", unsafe_allow_html=True)
                with c3:
                    st.markdown(f"<div class='kpi-card'><div class='kpi-label'>DIVIDEND YIELD</div><div class='kpi-value'>{dados['dy']:.2f}%</div></div>", unsafe_allow_html=True)
                with c4:
                    cor = "#008000" if dados['val_12m'] >= 0 else "#FF0000"
                    st.markdown(f"<div class='kpi-card'><div class='kpi-label'>VALORIZAÇÃO (12M)</div><div class='kpi-value' style='color:{cor}'>{dados['val_12m']:.2f}%</div></div>", unsafe_allow_html=True)

                # Gráfico
                st.write("")
                st.subheader(f"📈 Histórico de Preços ({periodo_label})")
                hist_plot = yf.Ticker(f"{ticker}.SA").history(period=periodo_cod)
                st.area_chart(hist_plot['Close'])

                # Análise IA (Prompt melhorado para evitar lixo de texto)
                st.divider()
                st.subheader("🧠 Raio-X Estratégico InvestAI")
                
                prompt = (
                    f"Analise a empresa {ticker}. Preço: R${dados['atual']:.2f}. "
                    "Gere uma análise executiva de 3 parágrafos. Use apenas texto e negritos. "
                    "Não use blocos de código ou a palavra 'markdown'."
                )
                
                try:
                    res_ia = cliente.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                    texto = res_ia.text.replace("```markdown", "").replace("```", "").strip()
                    st.markdown(texto)
                except:
                    st.error("Não foi possível gerar a análise da IA.")
            else:
                st.error(f"❌ Não foi possível encontrar dados para '{ticker}'. Tente usar o código oficial (ex: JHSF3).")
