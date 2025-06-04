import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.special import factorial

# Título e descrição
st.set_page_config(page_title="Simulação de Fila M/M/c", layout="wide")
st.title("🍽️ Simulação de Fila M/M/c - Restaurante Universitário")
st.markdown("Simule o comportamento de um sistema de atendimento com múltiplos servidores (M/M/c) com base em dados de chegada e atendimento.")

# Entrada de dados - barra lateral
with st.sidebar:
    st.header("📂 Entrada de Dados")
    uploaded_file = st.file_uploader("Upload CSV com 'interarrival_time' e 'service_time'", type=["csv"])
    c = st.number_input("Número de servidores", min_value=1, max_value=10, value=3, step=1)

# Função para calcular P0
def calc_p0(lam, mu, c, rho):
    sum_terms = sum(((lam/mu)**n) / factorial(n) for n in range(c))
    last_term = ((lam/mu)**c) / (factorial(c) * (1 - rho))
    return 1 / (sum_terms + last_term)

# Quando há arquivo carregado
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    if 'interarrival_time' not in df.columns or 'service_time' not in df.columns:
        st.error("❌ CSV deve conter colunas 'interarrival_time' e 'service_time'")
    else:
        # Coleta e prepara os dados
        interarrival_times = df['interarrival_time'].values
        service_times = df['service_time'].values
        arrival_times = np.cumsum(interarrival_times)

        n = len(arrival_times)
        start_service = np.zeros(n)
        end_service = np.zeros(n)
        servers_free_at = np.zeros(c)

        for i in range(n):
            arrival = arrival_times[i]
            service = service_times[i]
            server_index = np.argmin(servers_free_at)
            start = max(arrival, servers_free_at[server_index])
            servers_free_at[server_index] = start + service
            start_service[i] = start
            end_service[i] = start + service

        Wq = start_service - arrival_times
        W = end_service - arrival_times

        lam = 1 / np.mean(interarrival_times)
        mu = 1 / np.mean(service_times)
        rho = lam / (c * mu)

        P0 = calc_p0(lam, mu, c, rho)
        P_wait = (((lam/mu)**c) / factorial(c)) * (rho / (1 - rho)) * P0
        Lq = np.mean(Wq) / np.mean(service_times)
        L = np.mean(W) / np.mean(service_times)

        # Exibição das métricas
        st.subheader("📊 Métricas da Simulação")
        col1, col2, col3 = st.columns(3)
        col1.metric("P₀ (Sistema vazio)", f"{P0:.4f}")
        col2.metric("Prob. de Espera", f"{P_wait:.4f}")
        col3.metric("Servidores (c)", c)

        col4, col5, col6 = st.columns(3)
        col4.metric("Lq (Média na fila)", f"{Lq:.2f}")
        col5.metric("Wq (Espera média na fila)", f"{np.mean(Wq):.2f}")
        col6.metric("W (Tempo médio no sistema)", f"{np.mean(W):.2f}")

        # Visualizações
        st.subheader("📈 Gráficos da Simulação")

        fig1, ax1 = plt.subplots()
        ax1.plot(range(n), Wq, marker='o', color='darkblue')
        ax1.set_title('Tempo de Espera na Fila por Cliente')
        ax1.set_xlabel('Cliente')
        ax1.set_ylabel('Tempo (min)')
        ax1.grid(True)
        st.pyplot(fig1)

        # Geração dos dados para os gráficos de fila e ocupação (vetorizado)
        time_points = np.linspace(0, max(end_service), 1000)

        arrival_broadcast = arrival_times[:, np.newaxis]
        start_broadcast = start_service[:, np.newaxis]
        end_broadcast = end_service[:, np.newaxis]

        queue_matrix = (arrival_broadcast <= time_points) & (start_broadcast > time_points)
        busy_matrix = (start_broadcast <= time_points) & (end_broadcast > time_points)

        queue_sizes = queue_matrix.sum(axis=0)
        servers_busy = busy_matrix.sum(axis=0)

        col7, col8 = st.columns(2)

        with col7:
            fig2, ax2 = plt.subplots()
            ax2.plot(time_points, queue_sizes, color='orange')
            ax2.set_title('Tamanho da Fila ao Longo do Tempo')
            ax2.set_xlabel('Tempo')
            ax2.set_ylabel('Número de Pessoas na Fila')
            ax2.grid(True)
            st.pyplot(fig2)

        with col8:
            fig3, ax3 = plt.subplots()
            ax3.plot(time_points, servers_busy, color='green')
            ax3.set_title('Ocupação dos Servidores')
            ax3.set_xlabel('Tempo')
            ax3.set_ylabel('Servidores Ocupados')
            ax3.grid(True)
            st.pyplot(fig3)

        # Exportar resultados
        results = pd.DataFrame({
            'arrival_time': arrival_times,
            'start_service': start_service,
            'end_service': end_service,
            'wait_time': Wq,
            'total_time': W
        })

        csv = results.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Baixar Resultados da Simulação (CSV)",
            data=csv,
            file_name='resultados_simulacao.csv',
            mime='text/csv',
        )
