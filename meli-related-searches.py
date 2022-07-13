import streamlit as st
st.set_page_config(
    page_title="Mercado Libre: Extractor de Busquedas Relacionadas por Martin Aberastegue",
    page_icon="chart_with_upwards_trend",
    layout="wide",
)
from streamlit_echarts import st_echarts
import requests
import json
from stqdm import stqdm
from user_agent2 import (generate_user_agent)
import pandas as pd

st.title("Mercado Libre: Extractor de Busquedas Relacionadas")
st.subheader("Obtene ideas de palabras claves utilizando las sugerencias de MeLi")
st.write(
    "Desarrollado por [Martin Aberastegue](https://twitter.com/xyborg), inspirado en la herramienta de [@LeeFootSEO](https://twitter.com/LeeFootSEO) para [extraer datos de eBay](https://twitter.com/LeeFootSEO/status/1546122340240588801)")
st.write("Si te gusto, [regalame un cafecito](https://cafecito.app/xyborg) :)")
st.write("")

with st.form(key='columns_in_form_2'):
    seedkwd = st.text_input('Keyword Semilla')
    mercado = st.selectbox(
        'Elige el mercado/pais. Argentina (MLA), Mexico (MLM), Brasil (MLB), Uruguay (MLU), Chile (MLC), Colombia (MCO), Peru (MPE)',
        ('MLA', 'MLM', 'MLB', 'MLU', 'MLC', 'MCO', 'MPE'))
    submitted = st.form_submit_button('Enviar')

if submitted:
    def getkwds(seed_keyword, market):
      ua = generate_user_agent(navigator="chrome")
      header = {'User-Agent': str(ua)}
      getterms_url = "https://http2.mlstatic.com/resources/sites/" + market + "/autosuggest?showFilters=true&limit=6&api_version=2&q="
      response = requests.get(getterms_url + seed_keyword, headers=header)
      return response

    source_kws = []
    final_kws = []

    for i in getkwds(seedkwd, mercado).json()['suggested_queries']:
        print("> ",i['q'])
        for o in stqdm(getkwds(i['q'], mercado).json()['suggested_queries']):
          print(" - ", o['q'])
          source_kws.append(i['q'])
          final_kws.append(o['q'])

    df = pd.DataFrame(None)
    df['seed_keyword'] = source_kws
    df['related_searches'] = final_kws

    try:
        df['related_searches'] = df['related_searches'].str.split(',')
    except Exception:
        st.info("Error: No Related Searches Were Found, Try a Broader Keyword!")
        st.stop()

    df = df.explode('related_searches').reset_index(drop=True)
    df = df.drop_duplicates()


    def visualize_autocomplete(df_autocomplete_full):
        df_autocomplete_full['Keyword'] = seedkwd

        for query in df_autocomplete_full['Keyword'].unique():
            df_autocomplete_full = df_autocomplete_full[df_autocomplete_full['Keyword'] == query]
            children_list = []
            children_list_level_1 = []

            for int_word in df_autocomplete_full['seed_keyword']:
                q_lv1_line = {"name": int_word}
                if not q_lv1_line in children_list_level_1:
                    children_list_level_1.append(q_lv1_line)

                children_list_level_2 = []

                for query_2 in df_autocomplete_full[df_autocomplete_full['seed_keyword'] == int_word][
                    'related_searches']:
                    q_lv2_line = {"name": query_2}
                    children_list_level_2.append(q_lv2_line)

                level2_tree = {'name': int_word, 'children': children_list_level_2}

                if not level2_tree in children_list:
                    children_list.append(level2_tree)

                tree = {'name': query, 'children': children_list}

                opts = {
                    "backgroundColor": "#F0F2F6",


                    "title": {
                        "x": 'center',
                        "y": 'top',
                        "top": "5%",

                        "textStyle": {
                            "fontSize": 22,

                        },
                        "subtextStyle": {
                            "fontSize": 15,
                            "color": '#2ec4b6',

                        },
                    },

                    "series": [
                        {
                            "type": "tree",
                            "data": [tree],
                            "layout": "radial",
                            "top": "10%",
                            "left": "25%",
                            "bottom": "5%",
                            "right": "25%",
                            "symbolSize": 20,
                            "itemStyle": {
                                "color": '#2ec4b6',
                            },
                            "label": {
                                "fontSize": 14,
                            },

                            "expandAndCollapse": True,
                            "animationDuration": 550,
                            "animationDurationUpdate": 750,
                        }
                    ],
                }
            st.header(f"MeLi Related Searches for: {query}")
            st.caption("Right mouse click to save as image.")
            st_echarts(opts, key=query, height=1700)

    # add download button
    def convert_df(df):  # IMPORTANT: Cache the conversion to prevent computation on every rerun
        return df.to_csv().encode('utf-8')

    csv = convert_df(df)

    st.download_button(
        label="📥 Descargar palabras claves!",
        data=csv,
        file_name='meli_related_searches.csv',
        mime='text/csv', )

    # visualisation
    visualize_autocomplete(df)
