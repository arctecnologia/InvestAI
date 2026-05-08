# 🏛️ Arquitetura do Sistema: InvestAI

Este documento detalha a arquitetura de software, o fluxo de dados e os padrões de resiliência implementados no **InvestAI**, um assistente financeiro autônomo baseado em Python e Inteligência Artificial Generativa.

---

## 1. Visão Geral da Arquitetura (Fluxograma)

O diagrama abaixo ilustra o ciclo de vida completo de uma requisição de usuário, desde a entrada em linguagem natural até a exportação do relatório executivo em PDF.

```mermaid
graph TD
    A[Usuário / Google Colab] -->|1. Digita Nome ou Ticker| B(Módulo NLP: Gemini 2.5 Flash)
    B -->|2. Resolve Ticker Oficial Ex: 'BB' -> 'BBAS3'| C{Módulo de Dados Financeiros}
    
    C -->|3. Tenta BRAPI API| D[Cotação em Tempo Real]
    C -.->|Falha BRAPI| E[Failover: YFinance]
    
    D --> F[Módulo Yahoo Finance]
    E --> F
    
    F -->|4. Extrai KPIs e Histórico 1 a 5 Anos| G[Motor de Processamento]
    
    G -->|5. Renderiza Imagem| H[Matplotlib: Gráfico Premium]
    G -->|6. Injeta Contexto| I(Motor de Raciocínio: Gemini 2.5 Flash)
    
    H --> J[Exportador PDF FPDF2]
    I -->|Gera Raio-X Fundamentalista| J
    
    J -->|7. Compila Relatório| K((PDF Final Baixado))
