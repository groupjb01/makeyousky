import pandas as pd
import streamlit as st
from utils import convert_boolean_to_yes_no, set_default_criteria

def apply_competition_filter(university_info, criteria):
    if '2024년_경쟁률상승여부' not in university_info.columns:
        st.error("데이터 프레임에 '2024년_경쟁률상승여부' 열이 존재하지 않습니다.")
        return pd.DataFrame()

    convert_boolean_to_yes_no(criteria, '2024년_경쟁률상승여부')

    filtered = university_info[
        (university_info['2024년_경쟁강도'] < criteria['2024년_경쟁강도']) &
        (university_info['2024년_경쟁률상승여부'] == criteria['2024년_경쟁률상승여부']) &
        (university_info['2024년_경쟁률상승정도(%)'] >= criteria['2024년_경쟁률상승정도(%)'])
    ]
    return filtered

def apply_entrance_score_filter(university_info, criteria, user_score):
    if '2024년_입결70%하락여부' not in university_info.columns:
        st.error("데이터 프레임에 '2024년_입결70%하락여부' 열이 존재하지 않습니다.")
        return pd.DataFrame()

    convert_boolean_to_yes_no(criteria, '2024년_입결70%하락여부')
    set_default_criteria(criteria)

    if '2024년_입결70%차이(%)' not in university_info.columns:
        st.error("데이터 프레임에 '2024년_입결70%차이(%)' 열이 존재하지 않습니다.")
        return pd.DataFrame()

    filtered = university_info[
        (university_info['2024년_입결70%'] > user_score) &
        (university_info['3개년_평균_입결70%'] > user_score) &
        (university_info['2024년_입결70%하락여부'] == criteria['2024년_입결70%하락여부']) &
        (university_info['2024년_입결70%차이(%)'] >= criteria['2024년_입결70%차이(%)'])
    ]
    return filtered

def apply_acceptance_rate_filter(university_info, criteria):
    if '2024년_충원률(%)' not in university_info.columns:
        st.error("데이터 프레임에 '2024년_충원률(%)' 열이 존재하지 않습니다.")
        return pd.DataFrame()

    filtered = university_info[
        (university_info['2024년_충원률(%)'] >= criteria['2024년_충원률(%)']) &
        (university_info['3개년_평균_충원률'] >= criteria['3개년_평균_충원률'])
    ]
    return filtered
