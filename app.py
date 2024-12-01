import streamlit as st
import pandas as pd
import plotly.express as px
import geopandas as gpd
import folium
from streamlit_folium import folium_static
from branca.colormap import linear

# Título de la aplicación
st.title('Presencia de Jaguares (*Panthera onca*) en América 🐈')

# ----- Fuentes de datos -----
URL_JAGUAR = 'https://github.com/Emboc7/app_emi/raw/refs/heads/main/datos/Jaguares.csv'
URL_PAISES = 'https://github.com/Emboc7/app_emi/raw/refs/heads/main/datos/paises.gpkg'

# ----- Cargar datos -----

@st.cache_data
def cargar_datos_jaguar():
    # latin1 y delimiter para prevenir errores
    data = pd.read_csv(URL_JAGUAR, encoding='latin1', delimiter=';')
    return data

@st.cache_data
def cargar_datos_paises():
    pais = gpd.read_file(URL_PAISES)
    return pais

data = cargar_datos_jaguar()
pais = cargar_datos_paises()

# ----- Selección de año -----
# Obtener la lista de años disponibles en los datos
años_disponibles = data['year'].unique().tolist()
años_disponibles.sort()

# Añadir la opción "Todos los años"
años_disponibles = ['Todos los años'] + años_disponibles

# Crear el selectbox para seleccionar el año
año_seleccionado = st.sidebar.selectbox('Selecciona un año', años_disponibles)

# ----- Filtrar los datos según el año seleccionado -----
if año_seleccionado != 'Todos los años':
    data_filtrada = data[data['year'] == año_seleccionado]
else:
    data_filtrada = data.copy()

# ----- Nombres de las columnas en español -----
columnas_espaniol = {
    'countryCode': 'Código País',
    'stateProvince': 'Provincia o Estado',
    'year': 'Año',
    'individualCount': 'Número de individuos',
    'rightsHolder': 'Observador'
}
data_filtrada = data_filtrada.rename(columns=columnas_espaniol)

# ----- Preparación de datos para la tabla -----
columnas_mostrar = [
    'Código País',
    'Provincia o Estado',
    'Número de individuos',
    'Año',
    'Observador'
]
data_filtrada = data_filtrada[columnas_mostrar]

# ----- Mostrar la tabla -----
st.subheader(f'Avistamientos de jaguares en América en el año {año_seleccionado}')
st.dataframe(data_filtrada, hide_index=True)

# ----- Gráfico de avistamientos por país -----
avistamientos_por_pais = data_filtrada.groupby('Código País')['Número de individuos'].sum().reset_index()

# Ordenar los datos en orden descendente
avistamientos_por_pais = avistamientos_por_pais.sort_values(by='Número de individuos', ascending=False)

# Crear el gráfico de barras
fig_graph = px.bar(
    avistamientos_por_pais, 
    x='Código País', 
    y='Número de individuos',
    title=f"Avistamientos de jaguares en América por país ({año_seleccionado})",
    labels={'Código País': 'País', 'Número de individuos': 'Avistamientos'},
    color_discrete_sequence=["orange"]
)

# Mostrar el gráfico
st.subheader(f'Gráfico de avistamientos de jaguares en América por país ({año_seleccionado})')
st.plotly_chart(fig_graph)

# ----- Mapa coropletas de avistamientos por país -----
# Agrupar avistamientos por país
avistamientos_pais_mapa = data_filtrada.groupby('Código País')['Número de individuos'].sum().reset_index()

# Unir los datos de avistamientos con el GeoDataFrame de países
pais_merged = pais.merge(
    avistamientos_pais_mapa, 
    how='left', 
    left_on='Code',  # unir país
    right_on='Código País'  # unir csv
)

# Reemplazar nulls por ceros en la columna de avistamientos
pais_merged['Número de individuos'] = pais_merged['Número de individuos'].fillna(0)

# Crear el mapa base
mapa = folium.Map(location=[20, -60], zoom_start=2)  # Centrado en América

# Crear una paleta de colores
colormap = linear.YlOrRd_09.scale(pais_merged['Número de individuos'].min(), pais_merged['Número de individuos'].max())

# Añadir los polígonos al mapa
folium.GeoJson(
    pais_merged,
    name=f'Avistamientos por país ({año_seleccionado})',
    style_function=lambda feature: {
        'fillColor': colormap(feature['properties']['Número de individuos']),
        'color': 'black',
        'weight': 0.5,
        'fillOpacity': 0.7,
    },
    highlight_function=lambda feature: {
        'weight': 3,
        'color': 'black',
        'fillOpacity': 0.9,
    },
    tooltip=folium.features.GeoJsonTooltip(
        fields=['NAME', 'Número de individuos'],
        aliases=['País: ', 'Número de avistamientos: '],
        localize=True
    )
).add_to(mapa)

# Añadir la leyenda al mapa
colormap.caption = f'Avistamientos ({año_seleccionado})'
colormap.add_to(mapa)

# Mostrar el mapa
st.subheader(f'Mapa de avistamientos de jaguares por país ({año_seleccionado})')
folium_static(mapa)