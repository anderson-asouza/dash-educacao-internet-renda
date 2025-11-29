import streamlit as st
import plotly.express as px
import pandas as pd
from geobr import read_state
from sklearn.linear_model import LinearRegression
import json

def coluna_para_float(series):
    """Converte uma coluna com vírgula decimal, moeda, porcentagem ou milhar para float."""
    cleaned = (
        series.astype(str)
        .str.replace(r"[^\d,.\-]", "", regex=True)
        .str.replace(r"\.(?=\d{3}\b)", "", regex=True)
        .str.replace(",", ".", regex=True)
    )
    return cleaned.astype(float)

def formata_pt_br(valor, tipo="R$", decimais=2):
    """
    Formata valor numérico US para o padrão pt-BR.
    tipo: "R$" para moeda, "%" para percentual, ou apenas número.
    decimais: número de casas decimais
    """
    valor_formatado = f"{valor:,.{decimais}f}".replace(",", "X").replace(".", ",").replace("X", ".")

    if tipo == "R$":
        return f"R$ {valor_formatado}"
    elif tipo == "%":
        return f"{valor_formatado}%"
    else:
        return valor_formatado



df = pd.read_csv("educacao_internet_brasil_2018_2025.csv", sep='|', thousands='.', decimal=',', encoding='utf-8')

## ---- Layout ---- ##

st.set_page_config(
    page_title="Dashboard comparativo da Educação, Internet e Renda no Brasil",
    page_icon="📊",
    layout="wide"
)

st.title("Dashboard comparativo da Educação, Internet e Renda no Brasil")

indicadorMedio_Internet, indicadorMedio_Alfabetizacao, indicadorMedio_NivelSuperior, indicadorMedio_Renda = st.columns(4)
indicador_Internet, indicador_Alfabetizacao, indicador_NivelSuperior, indicador_Renda = st.columns(4)
graf_coropletico, graf_barra_internet_estado = st.columns([2, 8])
graf_linha_relacionamento_Internet, graf_linha_relacionamento_Alfabetizacao = st.columns(2)
graf_linha_relacionamento_Superior, graf_linha_relacionamento_Renda = st.columns(2)

ano_min = df['ANO'].min()
ano_max = df['ANO'].max()

obs_Media = f"(média de {ano_min} a {ano_max})"

## ---- Ajusta Valores Float ---- ##

cols = [
    "PERCENTUAL_COM_ACESSO_INTERNET",
    "TAXA_ALFABETIZACAO",
    "PERCENTUAL_COM_ENSINO_SUPERIOR",
    "RENDA_MEDIA_DOMICILIAR"
]

for col in cols:
    df[col] = coluna_para_float(df[col])

## ---- Criando Geometria ---- ##

@st.cache_data
def carregando_dados_IBGE():
    return read_state()

estados_geo = carregando_dados_IBGE()

df['ESTADO_RELACIONAMENTO'] = df['ESTADO'].str.strip().str.upper()
df['ESTADO_RELACIONAMENTO'] = df['ESTADO_RELACIONAMENTO'].replace({
    'ESPÍRITO SANTO': 'ESPIRITO SANTO' # Falha na base do IBGE: "Espírito Santo" está sem acento. Corrigido apenas na coluna de relacionamento entre dados para o merge.
})

estados_geo['name_state'] = estados_geo['name_state'].str.strip().str.upper()

geo = estados_geo.merge(df, left_on="name_state", right_on="ESTADO_RELACIONAMENTO", how='left')

## ---- Filtros ---- ##

opcoes = ["Todas"] + sorted(geo["name_region"].unique().tolist())
regioes = st.sidebar.selectbox("Filtrar por Região:", opcoes)

opcoes = ["Todos"] + sorted(df["ANO"].unique().tolist())
anos = st.sidebar.selectbox("Filtrar por Ano:", opcoes)

opcoes = ["Todos"] + sorted(df["ESTADO"].unique().tolist())
estados = st.sidebar.selectbox("Filtrar por Estado:", opcoes)

opcoes = ["Não Exibir"] + ["Exibir"]
valoresGraficosLinha = st.sidebar.selectbox("Valores nos Gráficos de Linha:", opcoes)

geo_filtrado = geo.copy()

if regioes != "Todas":
    geo_filtrado = geo_filtrado[geo_filtrado["name_region"] == regioes]

if anos == "Todos":
  obsMedia = " "+obs_Media

if anos != "Todos":
    geo_filtrado = geo_filtrado[geo_filtrado["ANO"] == anos]
    obsMedia = ""

if estados != "Todos":
    geo_filtrado = geo_filtrado[geo_filtrado["ESTADO"] == estados]

geojson = json.loads(geo_filtrado.to_json()) 

## ---- Indicadores ---- ##

df_medias_estaduais = geo_filtrado.groupby("ESTADO").agg({
    "PERCENTUAL_COM_ACESSO_INTERNET": "mean",  # pega a média
    "TAXA_ALFABETIZACAO": "mean",             # se quiser média das outras colunas numéricas também
    "PERCENTUAL_COM_ENSINO_SUPERIOR": "mean",
    "RENDA_MEDIA_DOMICILIAR": "mean",
    "name_region": "first" # pega a primeira ocorrência para colunas de texto
}).reset_index()

s = formata_pt_br(pd.to_numeric(df_medias_estaduais['PERCENTUAL_COM_ACESSO_INTERNET']).mean(), '%')

with indicadorMedio_Internet:
    st.write(f"<h5>Média de Acesso à Internet: "+ f"{s} </h5>", unsafe_allow_html=True)

s = formata_pt_br(pd.to_numeric(df_medias_estaduais['TAXA_ALFABETIZACAO']).mean(), '%')

with indicadorMedio_Alfabetizacao:
    st.write(f"<h5>Média de Alfabetização: " + f"{s} </h5>", unsafe_allow_html=True)

s = formata_pt_br(pd.to_numeric(df_medias_estaduais['PERCENTUAL_COM_ENSINO_SUPERIOR']).mean(), '%')    

with indicadorMedio_NivelSuperior:
    st.write(f"<h5>Média de Ensino Superior: " + f"{s} </h5>", unsafe_allow_html=True)

s = formata_pt_br(pd.to_numeric(df_medias_estaduais['RENDA_MEDIA_DOMICILIAR']).mean())

with indicadorMedio_Renda:
    st.write(f"<h5>Renda Média Domiciliar: " + f"{s} </h5>", unsafe_allow_html=True)


up = "🔺"
down ="🔻"

df_temp = df_medias_estaduais.sort_values(by="PERCENTUAL_COM_ACESSO_INTERNET", ascending=True)
s = up+df_temp.iloc[-1]["ESTADO"] +" "+formata_pt_br(df_temp.iloc[-1]["PERCENTUAL_COM_ACESSO_INTERNET"], '%')+ "<br>" +down+ df_temp.iloc[0]["ESTADO"] +" "+formata_pt_br(df_temp.iloc[0]["PERCENTUAL_COM_ACESSO_INTERNET"], '%')

with indicador_Internet:
    st.write(f"<h6>" + f"{s}</h6>", unsafe_allow_html=True)

df_temp = df_medias_estaduais.sort_values(by="TAXA_ALFABETIZACAO", ascending=True)
s = up+df_temp.iloc[-1]["ESTADO"] +" "+formata_pt_br(df_temp.iloc[-1]["TAXA_ALFABETIZACAO"], '%')+ "<br>" +down+ df_temp.iloc[0]["ESTADO"] +" "+formata_pt_br(df_temp.iloc[0]["TAXA_ALFABETIZACAO"], '%')

with indicador_Alfabetizacao:
    st.write(f"<h6>" + f"{s}</h6>", unsafe_allow_html=True)

df_temp = df_medias_estaduais.sort_values(by="PERCENTUAL_COM_ENSINO_SUPERIOR", ascending=True)
s = up+df_temp.iloc[-1]["ESTADO"] +" "+formata_pt_br(df_temp.iloc[-1]["PERCENTUAL_COM_ENSINO_SUPERIOR"], '%')+ "<br>" +down+ df_temp.iloc[0]["ESTADO"] +" "+formata_pt_br(df_temp.iloc[0]["PERCENTUAL_COM_ENSINO_SUPERIOR"], '%')

with indicador_NivelSuperior:
    st.write(f"<h6>" + f"{s}</h6>", unsafe_allow_html=True)

df_temp = df_medias_estaduais.sort_values(by="RENDA_MEDIA_DOMICILIAR", ascending=True)
s = up+df_temp.iloc[-1]["ESTADO"] +" "+formata_pt_br(df_temp.iloc[-1]["RENDA_MEDIA_DOMICILIAR"])+ "<br>" +down+ df_temp.iloc[0]["ESTADO"] +" "+formata_pt_br(df_temp.iloc[0]["RENDA_MEDIA_DOMICILIAR"])

with indicador_Renda:
    st.write(f"<h6>" + f"{s}</h6>", unsafe_allow_html=True)    

## ---- Gráfico - Coroplético (Acesso à internet por estado) ---- ##

df_medias_estaduais.sort_values("PERCENTUAL_COM_ACESSO_INTERNET")
df_medias_estaduais["Acesso Internet"] = df_medias_estaduais["PERCENTUAL_COM_ACESSO_INTERNET"].map(lambda x: formata_pt_br(x, "%"))


fig_coropletico = px.choropleth(
    df_medias_estaduais,
    geojson=geojson,
    locations='ESTADO',
    featureidkey="properties.ESTADO",
    color="PERCENTUAL_COM_ACESSO_INTERNET",
    hover_name='ESTADO',
    hover_data={
        "Acesso Internet": True,
        "ESTADO": False,
        "PERCENTUAL_COM_ACESSO_INTERNET": False
    },
    color_continuous_scale="Blues",
    projection="mercator",
    title="Mapa de acesso à Internet<br>"+obsMedia
)

fig_coropletico.update_coloraxes(showscale=False)
fig_coropletico.update_geos(fitbounds="locations", visible=False)

graf_coropletico.plotly_chart(fig_coropletico, width='stretch')

## ---- Gráfico - Barras (Acesso à internet por estado) ---- ##

fig_barras_internet_estado = px.bar(
    df_medias_estaduais.sort_values("PERCENTUAL_COM_ACESSO_INTERNET"),
    title="Percentual de acesso à internet por estado"+obsMedia,
    x="ESTADO",
    y="PERCENTUAL_COM_ACESSO_INTERNET",
    color="ESTADO",
    text="Acesso Internet",  
    text_auto=False,
    labels={"ESTADO": "Estados", "PERCENTUAL_COM_ACESSO_INTERNET": "Acesso Internet"}
)

fig_barras_internet_estado.update_layout(yaxis={'categoryorder':'total ascending'})

fig_barras_internet_estado.update_layout(
    legend_title_text="Estados"
)

legendas = {
    row["ESTADO"]: f'{row["ESTADO"]} — {row["Acesso Internet"]}'
    for _, row in df_medias_estaduais.iterrows()
}

fig_barras_internet_estado.for_each_trace(
    lambda t: t.update(
        name=legendas[t.name],
        legendgroup=legendas[t.name],
        hovertemplate=t.hovertemplate.replace(t.name, legendas[t.name])
    )
)

graf_barra_internet_estado.plotly_chart(fig_barras_internet_estado, width='stretch')

## ---- Gráfico - Linhas (Relação Educação Renda e Internet) ---- ##

df_long = geo_filtrado.melt(
    id_vars=["ESTADO", "ANO"],
    value_vars=[
        "PERCENTUAL_COM_ACESSO_INTERNET",
        "TAXA_ALFABETIZACAO",
        "PERCENTUAL_COM_ENSINO_SUPERIOR",
        "RENDA_MEDIA_DOMICILIAR"
    ],
    var_name="Indicador",
    value_name="Valor"
)

rename_indicadores = {
    "PERCENTUAL_COM_ACESSO_INTERNET": "Acesso à Internet (%)",
    "TAXA_ALFABETIZACAO": "Taxa de Alfabetização (%)",
    "PERCENTUAL_COM_ENSINO_SUPERIOR": "Ensino Superior (%)",
    "RENDA_MEDIA_DOMICILIAR": "Renda Média Domiciliar (R$)"
}

df_long["Indicador"] = df_long["Indicador"].replace(rename_indicadores)

def plot_indicador(df_long, indicador, container):
    df_temp = df_long[df_long["Indicador"] == indicador]

    fig = px.line(
        df_temp,
        x="ANO",
        y="Valor",
        color="ESTADO",
        markers=True,
        hover_name="ESTADO",
        title=indicador,
        labels={"ANO": "Ano", "Valor": "Valor", "ESTADO": "Estado"}
    )

    if valoresGraficosLinha  == "Exibir":
        if "R$" in indicador:
            text_values = [f"{formata_pt_br(v)}" for v in df_temp["Valor"]]
        else:
            text_values = [f"{formata_pt_br(v, '%')}" for v in df_temp["Valor"]]

        fig.update_traces(
            text=text_values,
            textposition="top center",
            mode="lines+markers+text"
        )

    fig.update_yaxes(nticks=6)

    fig_dict = fig.to_dict()
    tickvals = fig_dict["layout"]["yaxis"].get("tickvals", [])

    if tickvals:
        if "R$" in indicador:
            ticktext = [f"R$ {formata_pt_br(v)}" for v in tickvals]
        else:
            ticktext = [formata_pt_br(v, '%') for v in tickvals]

        fig.update_yaxes(tickvals=tickvals, ticktext=ticktext)

    if "R$" in indicador:
        fig.update_traces(
            hovertemplate="%{hovertext}<br>%{customdata}"
        )
        fig.update_traces(
            customdata=[formata_pt_br(v) for v in df_temp["Valor"]]
        )

    elif "%" in indicador:
        fig.update_traces(
            hovertemplate="%{hovertext}<br>%{customdata}"
        )
        fig.update_traces(
            customdata=[formata_pt_br(v, '%') for v in df_temp["Valor"]]
        )

    
    container.plotly_chart(fig, width='stretch')


plot_indicador(df_long, "Acesso à Internet (%)", graf_linha_relacionamento_Internet)
plot_indicador(df_long, "Taxa de Alfabetização (%)", graf_linha_relacionamento_Alfabetizacao)

plot_indicador(df_long, "Ensino Superior (%)", graf_linha_relacionamento_Superior)
plot_indicador(df_long, "Renda Média Domiciliar (R$)", graf_linha_relacionamento_Renda)

## ---- Regressão Linear ---- ##

st.write(f"<h2>Aplicação de 'Regressão Linear' para analisar a relação entre acesso à internet, renda e escolaridade.</h2>", unsafe_allow_html=True)

df_reg = geo_filtrado[[
    "ESTADO",
    "ANO",
    "PERCENTUAL_COM_ACESSO_INTERNET",
    "TAXA_ALFABETIZACAO",
    "PERCENTUAL_COM_ENSINO_SUPERIOR",
    "RENDA_MEDIA_DOMICILIAR"
]].dropna()

X = df_reg[["RENDA_MEDIA_DOMICILIAR", "PERCENTUAL_COM_ENSINO_SUPERIOR"]]

y = df_reg["PERCENTUAL_COM_ACESSO_INTERNET"]

modelo = LinearRegression()

modelo.fit(X, y)

coef_renda, coef_superior = modelo.coef_
intercepto = modelo.intercept_

st.write(f"Intercepto: {formata_pt_br(intercepto, '')}")
st.write(f"Coeficiente Renda: {formata_pt_br(coef_renda, '', 4)}")
st.write(f"Coeficiente Ensino Superior: {formata_pt_br(coef_superior, '', 4)}")

def prever_acesso(renda, ensino_superior):
    return modelo.predict([[renda, ensino_superior]])[0]

st.subheader("Previsão de Acesso à Internet (%)")

renda_input = st.number_input("Renda Média Domiciliar (R$):", value=3000)
superior_input = st.number_input("Ensino Superior (%):", value=12)

pred = prever_acesso(renda_input, superior_input)
st.metric("Previsão de Acesso (%)", formata_pt_br(pred, "%"))

df_reg["ACESSO_PREVISTO"] = modelo.predict(X)

df_reg["ACESSO_FORMAT"] = df_reg["PERCENTUAL_COM_ACESSO_INTERNET"].apply(lambda x: formata_pt_br(x, '%'))

df_reg["ACESSO_PREVISTO_FORMAT"] = df_reg["ACESSO_PREVISTO"].apply(lambda x: formata_pt_br(x, '%'))
df_reg["RENDA_FORMAT"] = df_reg["RENDA_MEDIA_DOMICILIAR"].apply(lambda x: formata_pt_br(x))
df_reg["ALFABETIZACAO_FORMAT"] = df_reg["TAXA_ALFABETIZACAO"].apply(lambda x: formata_pt_br(x, '%'))
df_reg["ENSINO_FORMAT"] = df_reg["PERCENTUAL_COM_ENSINO_SUPERIOR"].apply(lambda x: formata_pt_br(x, '%'))

fig = px.scatter(
    df_reg,
    x="RENDA_MEDIA_DOMICILIAR",
    y="PERCENTUAL_COM_ACESSO_INTERNET",
    color="ESTADO",
    hover_name="ESTADO",
    labels={"PERCENTUAL_COM_ACESSO_INTERNET": "Acesso a Internet", "RENDA_MEDIA_DOMICILIAR": "Renda Média Familiar", "ESTADO": "Estado"}
)

fig.update_xaxes(tickprefix="R$ ")
fig.update_yaxes(ticksuffix=" %")

fig.update_traces(
    customdata=df_reg[["RENDA_FORMAT","ACESSO_FORMAT","ALFABETIZACAO_FORMAT","ENSINO_FORMAT"]].values,
    hovertemplate=(
        "Estado: %{hovertext}<br>"
        "Renda Média: %{customdata[0]}<br>"
        "Acesso à Internet: %{customdata[1]}<br>"
        "Taxa de Alfabetização: %{customdata[2]}<br>"
        "Ensino Superior: %{customdata[3]}"
    )
)

fig.add_traces(
    px.line(
        df_reg.sort_values("RENDA_MEDIA_DOMICILIAR"),
        x="RENDA_MEDIA_DOMICILIAR",
        y="ACESSO_PREVISTO"
    ).update_traces(
        customdata=df_reg.sort_values("RENDA_MEDIA_DOMICILIAR")[
            ["RENDA_FORMAT", "ACESSO_PREVISTO_FORMAT"]
        ].values,
        hovertemplate="Renda: %{customdata[0]}<br>Acesso previsto: %{customdata[1]}"
    ).data
)


st.plotly_chart(fig, width='stretch')

st.write(
    "<h6>Interpretação: As variáveis analisadas apresentam forte correlação temporal, "
    "o que indica que evoluem em conjunto devido a condições sociais externas, "
    "não necessariamente que uma causa a outra diretamente.</h6>", unsafe_allow_html=True)
