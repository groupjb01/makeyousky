### data_loader.py ###
# data_loader.py
import streamlit as st
import pandas as pd
import json

@st.cache_data
def load_data(file_path):
    return pd.read_excel(file_path)

def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

data = load_data('data_240802_1846.xlsx')
additional_data = load_data('uni_info_summary_240802.xlsx')
lowest_ability_codes = load_json('lowest_ability_codes.json')

def load_expert_knowledge(file_path='expert_knowledge.txt'):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

expert_knowledge = load_expert_knowledge()




SCHOOL_TYPE_ADJUSTMENT = {
    "일반고": 1.0,
    "학군지 일반고": 0.9,
    "지역자사고": 0.9,
    "전사고": 0.7,
    "과학고": 0.7,
    "외고": 0.8
}
