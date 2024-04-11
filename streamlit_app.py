import pandas as pd
import numpy as np
import streamlit as st
import altair as alt

# TESTE GIT

st.set_page_config(layout="wide")

st.markdown("<style> * { font-family: 'Petrobras Sans' !important ; font-size:12pt !important } </style>", unsafe_allow_html=True)


pna_pre = pd.read_excel('C:\\Users\\NNA1\\OneDrive - PETROBRAS\\Documents\\simulador_mq_v0.3.xlsx', 0, index_col=0)
pna_dem = pd.read_excel('C:\\Users\\NNA1\\OneDrive - PETROBRAS\\Documents\\simulador_mq_v0.3.xlsx', 1, index_col=0)
pna_vol = pd.read_excel('C:\\Users\\NNA1\\OneDrive - PETROBRAS\\Documents\\simulador_mq_v0.3.xlsx', 2, index_col=0)
pna_fin = pd.read_excel('C:\\Users\\NNA1\\OneDrive - PETROBRAS\\Documents\\simulador_mq_v0.3.xlsx', 3, index_col=0)


### Curva de convergência de market Share

atl_msh = (pna_vol/pna_dem).mean().round(3)

cnv_msh = np.array([0.699,0.699,0.917,0.742,0.0100,0.378])
cnv_ini = np.array([2025,2026,2028,2038,2037,2030])
cnv_fim = np.array([2028,2028,2032,2043,2041,2035])

### Sliders
i=0
st.sidebar.header('Market Share')
for p in pna_vol.columns:
    cnv_msh[i] = st.sidebar.select_slider(p, range(0,101,1), value=round(atl_msh[i]*100,0)) / 100
    i+=1

cnv_crv = pna_vol.copy()
for i in cnv_crv.columns: cnv_crv[i] = cnv_crv.index
add_vol = np.clip((cnv_crv - cnv_ini) / (cnv_fim - cnv_ini),0,1) * (cnv_msh - atl_msh) * pna_dem


### Definição dos múltiplos

sim_opx = np.array([279,252,168,201,224,279])
sim_cpx = np.array([184,176,150,160,167,184])
sim_ldt = np.array([5,5,2,4,1,5])
sim_co2 = np.array([5,5,5,5,5,5])


### Calculo das curvas incrementais

add_rec = add_vol * pna_pre / 1000000
add_opx = add_vol * sim_opx / 1000000

cpx_crv = add_vol.copy()

i=0
for x in cpx_crv.columns:
    cpx_crv[x] = cpx_crv[x].shift(-sim_ldt[i])
    i=i+1

add_cpx = cpx_crv.fillna(0) * sim_cpx / 1000000

add_fco = add_rec - add_opx
add_fcl = add_fco - add_cpx


### Soma dos fluxos à financiabilidade do PN

sim_fin = pna_fin.copy()
sim_fin['FCO'] += add_fco.sum(1)
sim_fin['Caixa'] += add_fcl.sum(1).cumsum()


# ### Reequilíbrio financeiro

sim_cap = np.maximum(8-sim_fin['Caixa'],0)
sim_fin['Caixa'] += sim_cap
sim_fin['Dívida'] += sim_cap.cumsum()
sim_fin['Carbono'] = (pna_pre.iloc[0] / pna_pre * add_rec * sim_co2).sum(1)

# ### Preparação do dataframe

ano_ini = '2025'
ano_fim = '2040'
pna_fin['visao'] = 'Plano'
sim_fin['visao'] = 'Simulação'
pna_fin.index = pna_fin.index.astype(str)
sim_fin.index = sim_fin.index.astype(str)

fin = pd.concat([
    pna_fin.loc[ano_ini:ano_fim],
    sim_fin.loc[ano_ini:ano_fim]
])
fin = fin.melt(ignore_index=False,id_vars='visao')
fin = fin.reset_index()
fin = fin.rename({'index':'ano','variable':'conta','value':'valor'},axis='columns')

# ### Geração dos gráficos

col0, col1 = st.columns(2,gap='large')
i=0

contas = fin['conta'].unique()
for conta in contas:
    col = col0 if i%2 else col1
    with col:
        st.subheader(conta)
        st.altair_chart(alt.Chart(fin[fin['conta']==conta]).mark_bar(width=15).encode(
            x=alt.X('ano',title=None),
            y=alt.Y('valor'),
            xOffset = alt.XOffset('visao'),
            color=alt.Color('visao',title=None, legend=alt.Legend(orient='bottom'))
        ).configure_range(category=alt.RangeScheme(['#00BDA9','#006298'])).configure_axis(labelFontSize=18,titleFontSize=18,labelColor='#000000').properties(height=370),use_container_width=True)
    i+=1