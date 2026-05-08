import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from google import genai
from fpdf import FPDF
from datetime import datetime
import io
import pandas as pd

# --- Configuração de Página ---
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
    .kpi-label { font-size: 13px; color: #000000 !important; font-weight: bold; margin-bottom: 5px; }
    .kpi-value { font-size: 24px; font-weight: bold; color: #1f77b4 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- Funções de Suporte ---
def gerar_pdf_bytes(ticker, nome, kpis, analise, fig):
    """Gera o PDF e garante o retorno em formato BYTES para o Streamlit"""
    pdf = FPDF()
    pdf.add_page()
    
    # Cabeçalho Azul
    pdf.set_fill_color(31, 119, 180)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 15, f" RELATORIO EXECUTIVO: {ticker} ", align="C", fill=True)
    
    # Inserir Gráfico
    img_buf = io.BytesIO()
    fig.savefig(img_buf, format='png', dpi=200)
    img_buf.seek(0)
    pdf.image(img_buf, x=10, y=30, w=190)
    
    # Texto da IA
    pdf.set_y(130)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 10)
    # Limpeza de caracteres especiais que podem quebrar o PDF
    analise_limpa = analise.replace('**', '').replace('*', '').encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 6, analise_limpa)
    
    # O SEGREDO: converter bytearray para bytes
    return bytes(pdf.output())

def resolver_ticker(cliente, entrada):
    prompt = f"Retorne apenas o ticker da B3 para: {entrada}. Ex: PETR4. Nada mais."
    try:
        res = cliente.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        return res.text.strip().upper().split()[-1].replace(".SA", "").strip()
    except:
        return entrada.upper().strip()

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
                    "dy": dy, "val_12m": val_12m, "hist_completo": hist
                }
        except: continue
    return None

# --- UI Sidebar ---
with st.sidebar:
    st.header("⚙️ Configuração")
    gemini_key = st.text_input("Gemini API Key", type="password")
    periodo_op = {"1 Mes": "1mo", "3 Meses": "3mo", "1 Ano": "1y", "5 Anos": "5y"}
    periodo_sel = st.selectbox("Periodo do Grafico", list(periodo_op.keys()), index=2)

# --- UI Principal ---
st.title("🚀 InvestAI Web")
busca = st.text_input("Qual empresa ou ticker deseja analisar?", placeholder="Ex: JHSF3, Vale, Itau...")

if busca:
    if not gemini_key:
        st.info("Insira a API Key na lateral para começar.")
    else:
        cliente = genai.Client(api_key=gemini_key)
        with st.spinner("🔍 Coletando inteligência de mercado..."):
            ticker_resolvido = resolver_ticker(cliente, busca)
            d = buscar_dados(ticker_resolvido)
            
            if d:
                st.subheader(f"📊 {d['ticker']} - {d['nome']}")
                
                # Cards
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>VALOR ATUAL</div><div class='kpi-value'>R$ {d['atual']:.2f}</div></div>", unsafe_allow_html=True)
                with c2: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>MIN/MAX (52S)</div><div class='kpi-value' style='font-size:18px'>R$ {d['min']:.2f} / {d['max']:.2f}</div></div>", unsafe_allow_html=True)
                with c3: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>DIVIDEND YIELD</div><div class='kpi-value'>{d['dy']:.2f}%</div></div>", unsafe_allow_html=True)
                with c4:
                    cor = "green" if d['val_12m'] >= 0 else "red"
                    st.markdown(f"<div class='kpi-card'><div class='kpi-label'>VALORIZACAO (12M)</div><div class='kpi-value' style='color:{cor} !important;'>{d['val_12m']:.2f}%</div></div>", unsafe_allow_html=True)

                # Grafico
                st.write("")
                st.subheader(f"📈 Evolução de Preço ({periodo_sel})")
                hist_plot = yf.Ticker(d['ticker']).history(period=periodo_op[periodo_sel])
                
                fig, ax = plt.subplots(figsize=(12, 4), dpi=100)
                ax.plot(hist_plot.index, hist_plot['Close'], color='#1f77b4', lw=2.5)
                ax.fill_between(hist_plot.index, hist_plot['Close'], color='#1f77b4', alpha=0.1)
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%b/%y'))
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                st.pyplot(fig)

                # Analise IA
                st.divider()
                st.subheader("🧠 Raio-X Estratégico InvestAI")
                prompt_ia = f"Analise {d['ticker']}. Preço R${d['atual']:.2f}, DY {d['dy']:.2f}%. 3 paragrafos com negritos."
                res_ia = cliente.models.generate_content(model='gemini-2.5-flash', contents=prompt_ia)
                texto_ia = res_ia.text.replace("```markdown", "").replace("```", "").strip()
                st.markdown(texto_ia)

                # BOTAO DE DOWNLOAD CORRIGIDO
                st.write("")
                try:
                    pdf_data = gerar_pdf_bytes(d['ticker'], d['nome'], d, texto_ia, fig)
                    st.download_button(
                        label="📥 Baixar Relatório Completo em PDF",
                        data=pdf_data,
                        file_name=f"InvestAI_{d['ticker']}.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"Erro ao preparar PDF: {e}")
            else:
                st.error("Ativo não encontrado.")
