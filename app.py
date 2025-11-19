import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard CCIH - Sensibilidade", layout="wide")

# Título Principal
st.title("🦠 Painel de Sensibilidade Antimicrobiana")
st.markdown("---")

# --- 1. CARREGAR DADOS ---
@st.cache_data
def carregar_dados():
    arquivo = 'resultado_final_ccih.csv'
    try:
        # Tenta ler com utf-8 (padrão novo)
        df = pd.read_csv(arquivo, sep=';', encoding='utf-8')
    except:
        # Se falhar, tenta latin1 (padrão antigo)
        df = pd.read_csv(arquivo, sep=';', encoding='latin1')
    return df

try:
    df = carregar_dados()
except FileNotFoundError:
    st.error("Erro: O arquivo 'resultado_final_ccih.csv' não foi encontrado na pasta.")
    st.stop()

# --- 2. BARRA LATERAL (FILTROS) ---
st.sidebar.header("🔍 Filtros")

# Filtro de Unidade
todas_unidades = sorted(df['Unidade'].astype(str).unique())
unidade_selecionada = st.sidebar.multiselect(
    "Selecione a Unidade:",
    options=todas_unidades,
    default=todas_unidades # Começa com todas marcadas
)

# Filtro de Mês
todos_meses = df['Mês'].unique()
mes_selecionado = st.sidebar.multiselect(
    "Selecione o Mês:",
    options=todos_meses,
    default=todos_meses
)

# Filtro de Microorganismo (O mais importante)
todos_micros = sorted(df['Microorganismo'].astype(str).unique())
# Remove 'Não Identificado' se existir
if "Não Identificado" in todos_micros: todos_micros.remove("Não Identificado")

micro_selecionado = st.sidebar.selectbox(
    "Selecione o Microorganismo (Obrigatório):",
    options=todos_micros,
    index=0 # Seleciona o primeiro da lista automaticamente
)

# --- 3. APLICAR FILTROS ---
df_filtrado = df[
    (df['Unidade'].isin(unidade_selecionada)) & 
    (df['Mês'].isin(mes_selecionado)) &
    (df['Microorganismo'] == micro_selecionado)
]

# --- 4. PROCESSAMENTO PARA O GRÁFICO ---
# Lista das colunas que são antibióticos (remove as colunas de identificação)
colunas_identificacao = ['Código da O.S.', 'Unidade', 'Mês', 'Microorganismo']
antibioticos = [col for col in df.columns if col not in colunas_identificacao]

# Cria uma lista para armazenar os dados do gráfico
dados_grafico = []

if not df_filtrado.empty:
    total_isolados = len(df_filtrado)
    
    for abx in antibioticos:
        # Pega a contagem de S, R, I para este antibiótico
        contagem = df_filtrado[abx].value_counts()
        
        # Ignora se só tiver "-" (não testado)
        if '-' in contagem:
            contagem = contagem.drop('-')
            
        total_testado = contagem.sum()
        
        if total_testado > 0:
            for status, qtd in contagem.items():
                dados_grafico.append({
                    'Antibiótico': abx.title(), # Deixa bonitinho (Maiúscula)
                    'Resultado': status,
                    'Quantidade': qtd,
                    'Porcentagem': (qtd / total_testado) * 100
                })
else:
    total_isolados = 0

# Cria DataFrame para o gráfico
df_grafico = pd.DataFrame(dados_grafico)

# --- 5. EXIBIÇÃO DOS DADOS (O DASHBOARD) ---

# Cartão de Resumo
col1, col2 = st.columns([1, 3])

with col1:
    st.metric(label="Total de Isolados (N)", value=total_isolados)
    st.info(f"Microorganismo: **{micro_selecionado}**")
    if df_grafico.empty:
        st.warning("Não há testes de sensibilidade para os filtros selecionados.")

with col2:
    if not df_grafico.empty:
        st.subheader("Perfil de Sensibilidade (%)")
        
        # Mapeamento de cores padrão
        cores_mapa = {
            'Sensível': '#2ecc71',      # Verde
            'Resistente': '#e74c3c',    # Vermelho
            'Intermediário': '#f1c40f'  # Amarelo
        }
        
        # Gráfico de Barras Empilhadas (Igual ao exemplo do GitHub)
        fig = px.bar(
            df_grafico, 
            x="Porcentagem", 
            y="Antibiótico", 
            color="Resultado", 
            orientation='h',
            color_discrete_map=cores_mapa,
            text_auto='.1f', # Mostra o número na barra
            height=600,
            hover_data={'Quantidade': True, 'Porcentagem': ':.1f'}
        )
        
        fig.update_layout(
            xaxis_title="% de Sensibilidade",
            yaxis={'categoryorder':'total ascending'}, # Ordena do mais testado pro menos testado
            legend_title="Status"
        )
        
        st.plotly_chart(fig, use_container_width=True)

# --- 6. TABELA DE DADOS ---
st.markdown("---")
with st.expander("📂 Ver Tabela de Dados Brutos"):
    st.dataframe(df_filtrado)