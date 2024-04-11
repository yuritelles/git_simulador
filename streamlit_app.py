import pandas as pd
import numpy as np
import streamlit as st
import altair as alt
import numpy_financial as npf

st.set_page_config(layout="wide")

st.markdown("<style> * { font-family: 'Petrobras Sans' !important }</style>", unsafe_allow_html=True)
st.markdown("<style> *.ew7r33m0 { display:none !important }</style>", unsafe_allow_html=True)
st.markdown("<style> *.eczjsme11 * { font-size:14px !important }</style>", unsafe_allow_html=True)




### LEITURA DO EXCEL ###

pna_pre = pd.read_excel('simulador_mq_v0.3.xlsx', 0, index_col=0)
pna_dem = pd.read_excel('simulador_mq_v0.3.xlsx', 1, index_col=0)
pna_vol = pd.read_excel('simulador_mq_v0.3.xlsx', 2, index_col=0)
pna_fin = pd.read_excel('simulador_mq_v0.3.xlsx', 3, index_col=0)

cnv_ini = np.array([2025,2025,2025,2025,2025,2025])
cnv_fim = np.array([2050,2050,2050,2050,2050,2050])
sim_opx = np.array([279,252,168,201,224,279])
sim_cpx = np.array([184,176,150,160,167,184])
sim_ldt = np.array([5,5,2,4,1,5])
sim_co2 = np.array([5,5,5,5,5,5])
pna_avp = pna_vol.mean()
pna_avd = pna_dem.mean()
sim_avp = pna_avp.copy()
cnv_crv = pna_vol.copy()




### SLIDERS ###

i=0
st.sidebar.header('Simulações')

for p in pna_vol.columns:
    exp = st.sidebar.expander(p)
    vol_ano = int(pna_avp[p])
    dem_ano = int(pna_avd[p])

    cnv_ini[i], cnv_fim[i] = exp.slider('Período de Convergência', value=[cnv_ini[i],cnv_fim[i]],min_value=2025,max_value=2050, key='sld_cnv_' + str(i))

    sim_avp[i] = exp.select_slider('Produção adicional',range(-vol_ano,vol_ano,1), value=0,key='sld_avp_' + str(i))

    i+=1




### CURVA DE PRODUCAO ###

for i in cnv_crv.columns: cnv_crv[i] = cnv_crv.index
add_vol = np.clip((cnv_crv - cnv_ini) / (cnv_fim - cnv_ini),0,1) * sim_avp

st.sidebar.header('Período')
anos = st.sidebar.slider('Anos',value=[2025,2040],min_value=2025,max_value=2050,label_visibility='collapsed')




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

sim_vol = pna_vol + add_vol

sim_fin = pna_fin.copy()
sim_fin['FCO'] += add_fco.sum(1)
sim_fin['Caixa'] += add_fcl.sum(1).cumsum()


# Reequilíbrio financeiro

sim_cap = np.maximum(8-sim_fin['Caixa'],0)
sim_fin['Caixa'] += sim_cap
sim_fin['Dívida'] += sim_cap.cumsum()
sim_fin['Carbono'] = (pna_pre.iloc[0] / pna_pre * add_rec * sim_co2).sum(1)

##################################
#                                #
#      Geração dos gráficos      #
#                                #
##################################

def gerar_graficos(tab, df_pna, df_sim, label_pna='PE atual', label_sim='Simulação'):

    col0, col1 = tab.columns(2,gap='large')

    df_pna['x'] = label_pna
    df_sim['x'] = label_sim

    df = pd.concat([df_pna.loc[anos[0]:anos[1]],df_sim.loc[anos[0]:anos[1]]])
    df = df.melt(ignore_index=False,id_vars='x')
    df = df.reset_index()
    df['index'] = df['index'].astype(str)

    i=0
    w = 150/(anos[1]-anos[0])+7

    xs = df['variable'].unique()
    for x in xs:
        col = col1 if i%2 else col0
        with col:
            st.subheader(x)
            cht = alt.Chart(df[df['variable']==x])
            cht = cht.mark_bar(width=w).encode(
                x=alt.X('index',title=None),
                y=alt.Y('value',axis=None),
                xOffset = alt.XOffset('x'),
                color=alt.Color('x',title=None, legend=alt.Legend(orient='bottom'))
            )

            txt_al = alt.expr(alt.expr.if_(alt.datum.value>=0,'right','left'))
            txt_dx = alt.expr(alt.expr.if_(alt.datum.value>=0,-5,5))

            cht += cht.mark_text(baseline='middle',dx=txt_dx,size=12,angle=270, align=txt_al, fill='#ffffff').encode(
                text = alt.Text('value', format='.1f')
            )

            cht = cht.configure_range(category=alt.RangeScheme(['#00BDA9','#006298']))
            cht = cht.configure_axis(labelFontSize=18,titleFontSize=18,labelColor='#000000',domain=False,grid=False)
            cht = cht.properties(height=320)

            st.altair_chart(cht,use_container_width=True)
        i+=1

tab1, tab2 = st.tabs(['Financiabilidade','Volumes'])
gerar_graficos(tab1, pna_fin, sim_fin)
gerar_graficos(tab2, pna_vol, sim_vol)