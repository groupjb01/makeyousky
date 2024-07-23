import pandas as pd
import json
import streamlit as st

@st.cache_data
def load_data(file_path):
    df = pd.read_excel(file_path)
    df.replace('-', pd.NA, inplace=True)
    return df

@st.cache_resource
def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)
