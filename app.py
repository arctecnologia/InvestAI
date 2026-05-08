import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from google import genai
from fpdf import FPDF
from datetime import datetime
import io
import pandas as pd
import re

# --- 1. Configuração da Página e Estilo ---
st.set_page_config(page_title="InvestAI - Dashboard", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    .kpi-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.05);
        border: 1px solid #eeeeee;
    }
    .kpi-label { font-size: 13px; color: #000000 !important; font-weight: bold; margin-bottom: 5px; text-transform: uppercase; }
    .kpi-value { font-size: 24px; font-weight: bold; color: #1f77b4 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Funções de Suporte (Backend) ---

def gerar_pdf_bytes(ticker, nome, d, analise, fig):
    """Gera o PDF COMPLETO com Notas de Metodologia no rodapé"""
    pdf = FPDF()
    pdf.add_page()
    
    # --- HEADER ---
    pdf.set_fill_color(31, 119, 180) 
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 15, f" RELATORIO EXECUTIVO: {ticker} - {nome[:25]} ", align="C", fill=True)
    
    # --- CARDS DE INDICADORES ---
    pdf.set_y(30)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(245, 245, 245)
    
    # Card 1: Valor
    pdf.rect(10, 30, 45, 25, 'F')
    pdf.set_xy(10, 33); pdf.set_font("helvetica", "B", 8); pdf.cell(45, 5, "VALOR ATUAL", align="C")
    pdf.set_xy(10, 40); pdf.set_font("helvetica", "B", 12); pdf.cell(45, 10, f"R$ {d['atual']:.2f}", align="C")

    # Card 2: Min/Max
    pdf.rect(57, 30, 45, 25, 'F')
    pdf.set_xy(57, 33); pdf.set_font("helvetica", "B", 8); pdf.cell(45, 5, "MIN / MAX (52S)", align="C")
    pdf.set_xy(57, 40); pdf.set_font("helvetica", "B", 10); pdf.cell(45, 10, f"{d['min']:.2f} / {d['max']:.2f}", align="C")

    # Card 3: DY
    pdf.rect(104, 30, 45, 25, 'F')
    pdf.set_xy(104, 33); pdf.set_font("helvetica", "B", 8); pdf.cell(45, 5, "DIVIDEND YIELD", align="C")
    pdf.set_xy(104, 40); pdf.set_font("helvetica", "B", 12); pdf.cell(45, 10, f"{d['dy']:.2f}%", align="C")

    # Card 4: Valorização
    pdf.rect(151, 30, 45, 25, 'F')
    pdf.set_xy(151, 33); pdf.set_font("helvetica", "B", 8); pdf.cell(45, 5, "VALORIZACAO (12M)", align="C")
    pdf.set_xy(151, 40); pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(0, 120, 0) if d['val_12m'] >= 0 else pdf.set_text_color(200, 0, 0)
    pdf.cell(45, 10, f"{d['val_12m']:.2f}%", align="C")
    
    # --- GRÁFICO ---
    pdf.set_text_color(0, 0, 0)
    img_buf = io.BytesIO()
    fig.savefig(img_buf, format='png', dpi=200)
    img_buf.seek(0)
    pdf.image(img_buf, x=10, y=60, w=190)
    
    # --- ANÁLISE IA ---
    pdf.set_y(160)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Analise Estrategica InvestAI", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 10)
    analise_limpa = analise.replace('**', '').replace('*', '')
    analise_latin = analise_limpa.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 6, analise_latin)

    # --- RODAPÉ COM NOTA DE FONTES ---
    pdf.set_y(-25)
    pdf.set_font("helvetica", "I", 7)
    pdf.set_text_color(100, 100, 100)
    nota = (
        "Nota: Dados via Yahoo Finance. Diferencas em relacao a outros portais podem ocorrer devido ao uso de precos ajustados "
        "(dividendos/splits) e delay de ate 20 min. Este documento nao e uma recomendacao de investimento."
    )
    pdf.multi_cell(0, 4, nota.encode('latin-1', 'replace').decode('latin-1'), align="C")
    
    return bytes(pdf.output())

def resolver_ticker(cliente, entrada):
    prompt = f"Retorne apenas o ticker da B3 (letras e numero) para: {entrada}. Nada mais."
    try:
        res = cliente.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        texto = res.text.strip().upper()
        ticker = re.sub(r'[^A-Z0-9]', '', texto.split()[-1])
        return ticker.replace("SA", "")
    except:
        return re.sub(r'[^A-Z0-9]', '', entrada.upper())

def buscar_dados(ticker):
    for t in [f"{ticker}.SA", ticker]:
        try:
            acao = yf.Ticker(t)
            hist = acao.history(period="1y")
            if not hist.empty:
                info = acao.info
                val_atual = info.get('currentPrice') or hist['Close'].iloc[-1]
                min_52 = info.get('fiftyTwoWeekLow') or hist['Low'].min()
                max_52 = info.get('fiftyTwoWeekHigh') or hist['High'].max()
                dy = (info.get('dividendYield', 0) * 100)
                val_12m = ((hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1) * 100
                return {
                    "ticker": t, "nome": info.get('longName', ticker),
                    "atual": val_atual, "min": min_52, "max": max_52,
                    "dy": dy, "val_12m": val_12m, "hist_df": hist
                }
        except: continue
    return None

# --- 3. Interface Principal ---

with st.sidebar:
    st.header("⚙️ Configuração")
    gemini_key_raw = st.text_input("Gemini API Key", type="password")
    gemini_key = gemini_key_raw.strip() if gemini_key_raw else None
    periodo_dict = {"1 Mes": "1mo", "3 Meses": "3mo", "1 Ano": "1y", "5 Anos": "5y"}
    periodo_sel = st.selectbox("Periodo do Grafico", list(periodo_dict.keys()), index=2)
    
    st.divider()
    with st.expander("📖 Metodologia e Fontes"):
        st.write("""
        **Fonte de Dados:** Yahoo Finance via biblioteca `yfinance`.
        
        **Delay:** As cotações da B3 possuem um atraso de 15 a 20 minutos.
        
        **Preços Ajustados:** Diferente de portais como StatusInvest, o Yahoo Finance utiliza preços ajustados por proventos (dividendos/JCP) e eventos corporativos (splits), o que pode impactar as métricas de Mín/Máx e Valorização.
        """)

st.title("🚀 InvestAI Web")
busca_usuario = st.text_input("Busque empresa ou Ticker:", placeholder="Ex: JHSF, Vale, Petrobras...")

if busca_usuario:
    if not gemini_key:
        st.info("Insira sua API Key na lateral.")
    else:
        cliente = genai.Client(api_key=gemini_key)
        with st.spinner("Analisando mercado..."):
            ticker_limpo = resolver_ticker(cliente, busca_usuario)
            d = buscar_dados(ticker_limpo)
            
            if d:
                st.subheader(f"📊 {d['ticker']} - {d['nome']}")
                
                # Cards Web
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>VALOR ATUAL</div><div class='kpi-value'>R$ {d['atual']:.2f}</div></div>", unsafe_allow_html=True)
                with c2: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>MIN/MAX (52S)</div><div class='kpi-value' style='font-size:18px'>R$ {d['min']:.2f} / {d['max']:.2f}</div></div>", unsafe_allow_html=True)
                with c3: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>DIVIDEND YIELD</div><div class='kpi-value'>{d['dy']:.2f}%</div></div>", unsafe_allow_html=True)
                with c4:
                    cor_v = "green" if d['val_12m'] >= 0 else "red"
                    st.markdown(f"<div class='kpi-card'><div class='kpi-label'>VALORIZACAO (12M)</div><div class='kpi-value' style='color:{cor_v} !important;'>{d['val_12m']:.2f}%</div></div>", unsafe_allow_html=True)

                # Gráfico Web
                hist_grafico = yf.Ticker(d['ticker']).history(period=periodo_dict[periodo_sel])
                fig, ax = plt.subplots(figsize=(12, 4), dpi=100)
                ax.plot(hist_grafico.index, hist_grafico['Close'], color='#1f77b4', lw=2.5)
                ax.fill_between(hist_grafico.index, hist_grafico['Close'], color='#1f77b4', alpha=0.1)
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%b/%y'))
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                st.pyplot(fig)

                # Análise IA
                st.divider()
                prompt_ia = (
                    f"Analise o ativo {d['ticker']}. Preco: {d['atual']:.2f}. "
                    f"Dividend Yield: {d['dy']:.2f}%. Faca uma analise executiva de 3 paragrafos. "
                    "Use negritos nos pontos chave."
                )
                res_ia = cliente.models.generate_content(model='gemini-2.5-flash', contents=prompt_ia)
                texto_ia = res_ia.text.replace("```markdown", "").replace("```", "").strip()
                st.markdown(texto_ia)

                # --- Botão de PDF ---
                st.write("")
                pdf_data = gerar_pdf_bytes(d['ticker'], d['nome'], d, texto_ia, fig)
                st.download_button(
                    label="📥 Baixar Relatório Completo em PDF",
                    data=pdf_data,
                    file_name=f"InvestAI_{d['ticker']}.pdf",
                    mime="application/pdf"
                )
                
                # Rodapé Web
                st.markdown("---")
                st.caption("ℹ️ **Nota de Transparência:** Os dados são provenientes do Yahoo Finance. Diferenças em relação ao StatusInvest ocorrem devido ao delay de rede (15-20m) e ao uso de preços ajustados. Esta análise é gerada por IA e não é uma recomendação de investimento.")
            else:
                st.error("Ativo não encontrado.")
