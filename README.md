# 🚀 InvestAI - Assistente Financeiro Inteligente (B3)

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Gemini](https://img.shields.io/badge/AI-Google_Gemini_2.5-orange.svg)
![Bolsa](https://img.shields.io/badge/Mercado-B3_Brasil-green.svg)
![Status](https://img.shields.io/badge/Status-Produção-success.svg)

O **InvestAI** é um agente financeiro autônomo projetado para o mercado brasileiro em 2026. Ele une a precisão dos dados em tempo real da B3 com o poder de raciocínio da Inteligência Artificial Generativa, entregando relatórios executivos de alto nível (Estilo *StatusInvest*) em formato PDF.

---

## ✨ Funcionalidades Principais

* 🧠 **Busca Semântica (NLP):** Não sabe o código da ação? Digite "Banco do Brasil" e a IA descobrirá automaticamente o ticker `BBAS3`.
* 🛡️ **Tolerância a Falhas (Failover):** Integração principal com a API **BRAPI**. Caso haja instabilidade, o sistema aciona silenciosamente o **Yahoo Finance** como contingência, garantindo que o usuário nunca fique sem dados.
* 📊 **Gráficos Híbridos Premium:** Geração de gráficos avançados com médias móveis, preenchimento de área e anotações dinâmicas utilizando `Matplotlib`.
* 📑 **Relatórios Executivos em PDF:** O motor `FPDF2` constrói um painel visual com Cards de KPIs (Mínimas, Máximas, Dividend Yield, Valorização 12M) e exporta a análise completa pronta para leitura.
* 🤖 **Raio-X Fundamentalista:** O modelo **Gemini 2.5 Flash** analisa os fundamentos da empresa e o contexto do gráfico para gerar um veredito focado nos riscos e oportunidades do setor.

---

## 🛠️ Stack de Tecnologias

* **Linguagem:** Python
* **Inteligência Artificial:** Google GenAI SDK (`gemini-2.5-flash`)
* **Dados Financeiros:** BRAPI API & `yfinance`
* **Visualização e Exportação:** `matplotlib` e `fpdf2`
* **Ambiente de Desenvolvimento:** Google Colab / Jupyter Notebook

---

## 🚀 Como Executar o Projeto

Este projeto foi otimizado para rodar diretamente no **Google Colab**, garantindo facilidade de uso sem necessidade de configuração de ambiente local.

### 1. Pré-requisitos
Você precisará de duas chaves de API gratuitas:
* [API Key do Google Gemini](https://aistudio.google.com/)
* [API Token da BRAPI](https://brapi.dev/docs)

### 2. Configuração no Google Colab
1. Abra um novo Notebook no Google Colab.
2. No menu lateral esquerdo, clique no ícone de **Secrets (Chaves)**.
3. Adicione duas novas chaves:
    * Nome: `BRAPI_KEY` | Valor: *<sua-chave-brapi>*
    * Nome: `GEMINI_KEY` | Valor: *<sua-chave-gemini>*
4. Habilite o acesso aos "Notebook access" para ambas as chaves.

### 3. Instalação e Execução
Copie e rode a seguinte célula de instalação:
```bash
!pip install -q -U fpdf2 matplotlib yfinance google-genai
