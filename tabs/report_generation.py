import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from openai import OpenAI
import os
from dotenv import load_dotenv
import matplotlib.font_manager as fm
import numpy as np
import time
from data_loader import expert_knowledge

# 환경 변수 로드 및 OpenAI 클라이언트 설정
load_dotenv()
api_key = os.getenv('API_KEY')
client = OpenAI(api_key=api_key)

# 한글 폰트 설정
font_path = 'KoPubDotumLight.ttf'
font_prop = fm.FontProperties(fname=font_path)
plt.rcParams['font.family'] = font_prop.get_name()
plt.rcParams['font.size'] = 12
plt.rcParams['axes.unicode_minus'] = False

# Seaborn 스타일 설정
sns.set_theme(style="whitegrid", palette="pastel")

# 여기에 format_value 함수를 추가
def format_value(value):
    if pd.isna(value):
        return '-'
    elif isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


# 필요한 컬럼 리스트 수정
needed_columns = [
    '대학명', '전형구분', '전형명', '모집단위', '계열', '계열구분', '계열상세명',
    '2025년_모집인원', '2024년_모집인원', '2023년_모집인원', '2022년_모집인원',
    '전년대비2025년_모집인원변화',
    '2024년_경쟁률', '2023년_경쟁률', '2022년_경쟁률',
    '2024년_입결70%', '2023년_입결70%', '2022년_입결70%',
    '2024년_입결50%', '2023년_입결50%', '2022년_입결50%',
    '2024년_충원율(%)', '2023년_충원율(%)', '2022년_충원율(%)',
    '2024년_추가합격자수', '2023년_추가합격자수', '2022년_추가합격자수',
    '2025년_최저요약', '2025년_수능최저코드', '2024년_수능최저',
    '2024년_경쟁률백분위', '2024년_경쟁률변동(%)', '2024년_계열경쟁률변동(%)',
    '3개년_경쟁률_평균', '3개년_경쟁률_변동(%)',
    '2024년_입결70%변동(%)', '3개년_입결70%_평균', '3개년_입결50%_평균',
    '2024년_충원율백분위', '2024년_충원율변동(%)', '3개년_충원율_평균',
    '2024년_계열경쟁률', '2023년_계열경쟁률', '2022년_계열경쟁률',
    '2024년_계열입결70%', '2023년_계열입결70%', '2022년_계열입결70%', '2024년_계열입결70%변동(%)',
    '2024년_계열충원율(%)', '2023년_계열충원율(%)', '2022년_계열충원율(%)',
    '3개년_계열경쟁률_평균', '3개년_계열입결70%_평균', '3개년_계열충원율_평균', '2024년_계열충원율변동(%)'
]


def generate_overall_opinion_prompt(student_info, university_list):
    prompt = f"""
    다음 전문지식과 학생 정보, 지원 가능 대학 목록을 참고하여 학생의 대학 지원에 대한 전략적이고 간결한 종합 의견을 제시해주세요.

    전문지식:
    {expert_knowledge}

    학생 정보:
    {student_info}

    지원 가능 대학 목록:
    {university_list}

    요구사항:
    1. 학생의 현재 성적과 목표 대학 간의 격차를 분석하세요.
    2. 상향, 적정, 하향 지원의 균형을 제안하되, 각 카테고리별로 1-2개 대학을 추천하세요.
    3. 추천 대학의 3개년 입시 결과(경쟁률, 입결, 충원율)를 간략히 언급하고, 주기적 변동 가능성을 고려하세요.
    4. 200단어 이내로 작성하세요.
    """
    return prompt


def generate_top_3_recommendations_prompt(university_data):
    prompt = f"""
    다음 전문지식과 상향 지원 대상 대학 정보를 참고하여 상향 지원 BEST 3에 대한 간결하고 전략적인 분석을 제공해주세요. 전문지식을 참고하여 작성하세요.
    
    전문지식:
    {expert_knowledge}

    상향 지원 대상 대학 정보:
    {university_data}

    요구사항:
    1. 각 대학/학과의 3개년 경쟁률, 입결, 충원율 추이를 요약하고, 주기적 변동 패턴이 있는지 분석하세요.
    2. 경쟁률이 6대 1 이하인 경우 특별히 언급하고, 그 의미와 다음 해 변동 가능성을 설명하세요.
    3. 모집인원의 변화가 40% 이상인 경우 이를 지적하고, 그 영향을 분석하세요.
    4. 50%와 70% 컷의 차이가 큰 경우 이를 언급하고, 그 의미를 설명하세요.
    5. 각 대학/학과의 전형 방법이나 수능 최저 기준 변화가 있다면 언급하세요.
    6. 각 대학/학과별로 100단어 이내로 작성하되, 대학별로 한 문단씩 나누어 작성하세요.
    """
    return prompt


def generate_detailed_analysis_prompt(university_info, admission_data):
    prompt = f"""
    다음 전문지식과 대학/학과 정보와 입시 데이터를 참고하여 상세 분석 보고서를 작성해 주세요. 전문지식을 참고하여 작성하세요.

    전문지식:
    {expert_knowledge}
    
    대학/학과 정보:
    {university_info}

    입시 데이터:
    {admission_data}

    요구사항: 
    1. 3개년 데이터를 바탕으로 경쟁률, 입결, 충원율의 추이를 분석하고, 주기적 변동 패턴이 있는지 확인하세요.
    2. 경쟁률이 6대 1 이하이거나 10대 1 이상인 경우, 그 의미를 분석하고 다음 해 변동 가능성을 예측하세요.
    3. 모집인원 변화가 40% 이상인 경우, 그 영향을 설명하세요.
    4. 50%와 70% 컷의 차이를 분석하고, 그 의미를 설명하세요.
    5. 전형 방법이나 수능 최저 기준의 변화가 있다면 그 영향을 분석하세요.
    6. 학과의 선호도 변화 가능성(예: 경영학, 교육학, 행정학 등)을 고려하여 분석하세요.
    7. 주기적 변동성을 고려한 의견도 포함하세요.
    8. 이 모든 것을 한 문단으로, 300단어 이내로 작성하세요.
    """
    return prompt

def generate_gpt_response(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates reports based on university admission data. Please refer to the expert knowledge provided in the prompt when answering. Answer in Korean."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000
    )
    return response.choices[0].message.content.strip()


def analyze_university(row, all_data, index, admission_type):
    report = f"### {index}. {row['대학명']} {row['모집단위']} - {admission_type} 전형\n\n"

    # 경쟁률 분석
    report += "#### 경쟁률 분석\n\n"
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20, 5))

    years = ['2022년', '2023년', '2024년']
    competition_rates = [row['2022년_경쟁률'], row['2023년_경쟁률'], row['2024년_경쟁률']]
    series_rates = [row['2022년_계열경쟁률'], row['2023년_계열경쟁률'], row['2024년_계열경쟁률']]

    ax1.plot(years, competition_rates, marker='o', label='모집단위')
    ax1.plot(years, series_rates, marker='o', linestyle='--', label='계열평균')
    ax1.set_title('3개년 경쟁률 추이', fontproperties=font_prop)
    ax1.set_ylabel('경쟁률', fontproperties=font_prop)
    ax1.legend(prop=font_prop)

    labels = ['2024년 경쟁률', '3개년 평균']
    unit_values = [row['2024년_경쟁률'], row['3개년_경쟁률_평균']]
    series_values = [row['2024년_계열경쟁률'], row['3개년_계열경쟁률_평균']]

    x = np.arange(len(labels))
    width = 0.35

    ax2.bar(x - width / 2, unit_values, width, label='모집단위')
    ax2.bar(x + width / 2, series_values, width, label='계열평균')
    ax2.set_title('2024년 vs 3개년 평균 경쟁률', fontproperties=font_prop)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontproperties=font_prop)
    ax2.legend(prop=font_prop)

    labels = ['모집단위', '계열평균']
    values = [row['2024년_경쟁률변동(%)'], row['2024년_계열경쟁률변동(%)']]

    ax3.bar(labels, values)
    ax3.set_title('2024년 경쟁률 변동(%)', fontproperties=font_prop)
    ax3.set_ylabel('변동률 (%)', fontproperties=font_prop)

    plt.tight_layout()
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()

    report += f"![Competition Rate Analysis](data:image/png;base64,{image_base64})\n\n"

    report += f"- 2024학년도 경쟁률: {format_value(row['2024년_경쟁률'])} (계열 평균: {format_value(row['2024년_계열경쟁률'])})\n"
    report += f"- 2024학년도 경쟁률 변동(%): {format_value(row['2024년_경쟁률변동(%)'])} (계열 평균: {format_value(row['2024년_계열경쟁률변동(%)'])})\n"
    report += f"- 3개년 평균 경쟁률: {format_value(row['3개년_경쟁률_평균'])} (계열 평균: {format_value(row['3개년_계열경쟁률_평균'])})\n\n"



    # 입결 분석
    report += "#### 입결 분석\n\n"
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20, 5))

    entrance_scores = [row['2022년_입결70%'], row['2023년_입결70%'], row['2024년_입결70%']]
    series_scores = [row['2022년_계열입결70%'], row['2023년_계열입결70%'], row['2024년_계열입결70%']]

    ax1.plot(years, entrance_scores, marker='o', label='모집단위')
    ax1.plot(years, series_scores, marker='o', linestyle='--', label='계열평균')
    ax1.set_title('3개년 입결 70% 추이', fontproperties=font_prop)
    ax1.set_ylabel('입결 70%', fontproperties=font_prop)
    ax1.legend(prop=font_prop)

    labels = ['2024년 입결 70%', '3개년 평균']
    unit_values = [row['2024년_입결70%'], row['3개년_입결70%_평균']]
    series_values = [row['2024년_계열입결70%'], row['3개년_계열입결70%_평균']]

    ax2.bar(x - width / 2, unit_values, width, label='모집단위')
    ax2.bar(x + width / 2, series_values, width, label='계열평균')
    ax2.set_title('2024년 vs 3개년 평균 입결 70%', fontproperties=font_prop)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontproperties=font_prop)
    ax2.legend(prop=font_prop)

    labels = ['모집단위', '계열평균']
    values = [row['2024년_입결70%변동(%)'], row['2024년_계열입결70%변동(%)']]

    ax3.bar(labels, values)
    ax3.set_title('2024년 입결 70% 변동(%)', fontproperties=font_prop)
    ax3.set_ylabel('변동률 (%)', fontproperties=font_prop)

    plt.tight_layout()
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()

    report += f"![Entrance Score Analysis](data:image/png;base64,{image_base64})\n\n"

    report += f"- 2024학년도 70% 입결: {format_value(row['2024년_입결70%'])} (계열 평균: {format_value(row['2024년_계열입결70%'])})\n"
    report += f"- 2024학년도 70% 입결 변동(%): {format_value(row['2024년_입결70%변동(%)'])} (계열 평균: {format_value(row['2024년_계열입결70%변동(%)'])})\n"
    report += f"- 3개년 평균 70% 입결: {format_value(row['3개년_입결70%_평균'])} (계열 평균: {format_value(row['3개년_계열입결70%_평균'])})\n\n"


    # 충원율 분석
    report += "#### 충원율 분석\n\n"
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))

    fill_rates = [row['2022년_충원율(%)'], row['2023년_충원율(%)'], row['2024년_충원율(%)']]
    series_fill_rates = [row['2022년_계열충원율(%)'], row['2023년_계열충원율(%)'], row['2024년_계열충원율(%)']]

    ax1.plot(years, fill_rates, marker='o', label='모집단위')
    ax1.plot(years, series_fill_rates, marker='o', linestyle='--', label='계열평균')
    ax1.set_title('3개년 충원율 추이', fontproperties=font_prop)
    ax1.set_ylabel('충원율 (%)', fontproperties=font_prop)
    ax1.legend(prop=font_prop)

    labels = ['2024년 충원율', '3개년 평균']
    unit_values = [row['2024년_충원율(%)'], row['3개년_충원율_평균']]
    series_values = [row['2024년_계열충원율(%)'], row['3개년_계열충원율_평균']]

    ax2.bar(x - width / 2, unit_values, width, label='모집단위')
    ax2.bar(x + width / 2, series_values, width, label='계열평균')
    ax2.set_title('2024년 vs 3개년 평균 충원율', fontproperties=font_prop)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontproperties=font_prop)
    ax2.legend(prop=font_prop)

    plt.tight_layout()
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()

    report += f"![Fill Rate Analysis](data:image/png;base64,{image_base64})\n\n"

    report += f"- 2024학년도 충원율: {format_value(row['2024년_충원율(%)'])}% (계열 평균: {format_value(row['2024년_계열충원율(%)'])}%)\n"
    report += f"- 2024학년도 충원율 변동(%): {format_value(row['2024년_충원율변동(%)'])} (계열 평균: {format_value(row['2024년_계열충원율변동(%)'])})\n"
    report += f"- 3개년 평균 충원율: {format_value(row['3개년_충원율_평균'])}% (계열 평균: {format_value(row['3개년_계열충원율_평균'])}%)\n\n"

    # 심층 분석
    report += "#### 심층 분석\n\n"

    # GPT를 활용한 종합 분석 및 인사이트 생성
    university_info = f"{row['대학명']} {row['모집단위']} {admission_type} 전형"
    admission_data = row.to_dict()
    gpt_insight_prompt = generate_detailed_analysis_prompt(university_info, admission_data)
    gpt_insight_response = generate_gpt_response(gpt_insight_prompt)
    report += f"{gpt_insight_response}\n\n"

    report += "---\n\n"

    return report


def generate_university_list(high_info, mid_info, low_info):
    university_list = ""
    for level, df in [('상향', high_info), ('적정', mid_info), ('하향', low_info)]:
        university_list += f"{level}:\n"
        for _, row in df.iterrows():
            university_list += f"- {row['대학명']} {row['모집단위']} ({row['전형구분']})\n"
    return university_list


def generate_report(high_info, mid_info, low_info, student_info, all_data, addtional_data):
    report = ""

    # 기본 정보
    report += "### 기본 정보 🏫\n\n"
    basic_info = pd.DataFrame([
        {'학교유형': student_info['school_type'],
         '계열(인문/자연)': ', '.join(student_info['field']),
         '희망계열(세부계열)': student_info['major_interest'],
         '내신성적': student_info['score'],
         '수능최저역량': student_info['lowest_ability'],
         '비교과 활동수준': student_info['non_subject_level'],
         '주요과목 우수': 'Yes' if student_info['major_subjects_strong'] == 'YES' else 'No'}
    ])
    report += basic_info.to_markdown(index=False) + "\n\n"


    # 지원 가능선
    report += "### 지원 가능선 🎯\n\n"
    report += "| | 교과 | 학생부 종합 |\n"
    report += "|------|------|-------------|\n"

    for level, df in [('상향', high_info), ('적정', mid_info), ('하향', low_info)]:
        report += f"| {level} | "
        for category in ['교과', '종합']:
            if '전형구분' in df.columns:
                filtered_df = df[df['전형구분'] == category]
            else:
                filtered_df = df

            if not filtered_df.empty:
                unis = []
                for _, row in filtered_df.iterrows():
                    uni_info = row.get('대학명', '')
                    if '모집단위' in row:
                        uni_info += f" {row['모집단위']}"
                    unis.append(uni_info)
                report += ", ".join(unis[:5])
            report += " | "
        report += "\n"

    # 종합 의견 (GPT로 작성)
    university_list = generate_university_list(high_info, mid_info, low_info)
    gpt_prompt = generate_overall_opinion_prompt(student_info, university_list)
    gpt_response = generate_gpt_response(gpt_prompt)
    report += f"### 종합 의견 📝\n\n{gpt_response}\n\n"
    report += "---\n\n"

    # 상향 지원 BEST 3
    report += "### 상향 지원 BEST 3 🌟\n\n"
    report += """
    경쟁률과 입결은 해마다 변동성이 큰 지표이며 상승과 하락을 반복하는 경향이 있지만, 장기적으로 볼 때 각 학과별로 어느 정도 일정한 추세를 보입니다. 반면 충원율의 경우에는 학과마다 비교적 안정적인 경향성을 나타내고 있습니다.

    상향 지원은 통상 적정이나 안정 지원에 비해 합격 가능성이 다소 낮습니다. 그러나 철저한 분석을 바탕으로 전략적으로 접근한다면 상향 지원 역시 충분히 의미 있는 도전이 될 수 있습니다. 상향 지원을 고려하실 때에는 단순히 경쟁률이나 경쟁률 추이만 보는 것이 아니라, 경쟁 강도, 입결 상승율, 충원 강도 등 다양한 요소를 종합적으로 고려하시는 것이 중요합니다.

    지략에서는 이러한 데이터를 바탕으로 상향 지원 대상 학과를 선정하여 추천 리스트를 제공해 드리고 있습니다. 적정이나 안정 지원만큼이나 상향 지원도 여러분께는 소중한 기회가 될 수 있습니다. 아래는 경쟁률, 입결, 충원율에 기반한 상향지원 BEST 3입니다.

    """
    report += " \n\n"

    # GPT로 상향지원전략 작성 (교과와 종합 모두 포함)
    gpt_strategy_prompt = generate_top_3_recommendations_prompt(high_info.to_dict('records'))
    gpt_strategy_response = generate_gpt_response(gpt_strategy_prompt)
    report += gpt_strategy_response + "\n\n"
    report += "---\n\n"

    report += "각 상향지원 안에 대해 자세히 설명드리겠습니다.\n\n"

    # 교과 전형 분석
    report += "### 교과 전형 분석\n\n"
    for i, (_, row) in enumerate(high_info[high_info['전형구분'] == '교과'].head(3).iterrows(), 1):
        report += analyze_university(row, all_data, i, '교과')

    # 학생부 종합 전형 분석
    report += "### 학생부 종합 전형 분석\n\n"
    for i, (_, row) in enumerate(high_info[high_info['전형구분'] == '종합'].head(3).iterrows(), 1):
        report += analyze_university(row, all_data, i, '학종')

    tables = generate_detailed_tables(high_info, mid_info, low_info)

    return report, tables


def generate_detailed_tables(high_info, mid_info, low_info):
    tables = []
    for admission_type in ['교과', '종합']:
        columns_to_display = ['구분', '대학명', '전형구분', '전형명', '모집단위', '2025년_모집인원',
                              '2025년_최저요약', '2024년_경쟁률', '2023년_경쟁률', '2024년_입결70%', '2024년_충원율(%)']

        combined_df = pd.DataFrame()
        for level, df in [('상향', high_info), ('적정', mid_info), ('하향', low_info)]:
            df_filtered = df[df['전형구분'] == admission_type].copy()
            df_filtered['구분'] = level
            combined_df = pd.concat([combined_df, df_filtered], ignore_index=True)

        if not combined_df.empty:
            tables.append({
                'title': f"{admission_type} 전형",
                'data': combined_df[columns_to_display]
            })
        else:
            tables.append({
                'title': f"{admission_type} 전형",
                'data': None
            })

    return tables


def show_report_generation():
    st.info("최종 필터링된 데이터로 보고서를 작성합니다.")

    if 'final_selection' not in st.session_state or 'student_info' not in st.session_state:
        st.warning("최종 필터링과 학생 정보 입력을 먼저 완료해주세요.")
        return

    final_selection = st.session_state['final_selection']
    student_info = st.session_state['student_info']
    all_data = st.session_state.get('all_data', pd.DataFrame())

    # 데이터 전처리 함수
    def preprocess_data(df):
        df = df[df.columns.intersection(needed_columns)]
        for col in needed_columns:
            if col not in df.columns:
                df[col] = np.nan
        return df[needed_columns]

    if st.button("보고서 생성"):
        with st.spinner("보고서 작성 중입니다..."):
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(1)  # 0.01초마다 진행 상황 업데이트
                progress_bar.progress(i + 1)

            high_info = pd.concat([preprocess_data(final_selection.get('교과_상향', pd.DataFrame())),
                                   preprocess_data(final_selection.get('학종_상향', pd.DataFrame()))],
                                  ignore_index=True)
            mid_info = pd.concat([preprocess_data(final_selection.get('교과_적정', pd.DataFrame())),
                                  preprocess_data(final_selection.get('학종_적정', pd.DataFrame()))],
                                 ignore_index=True)
            low_info = pd.concat([preprocess_data(final_selection.get('교과_하향', pd.DataFrame())),
                                  preprocess_data(final_selection.get('학종_하향', pd.DataFrame()))],
                                 ignore_index=True)

            # all_data도 전처리
            all_data = preprocess_data(all_data)

            additional_data = st.session_state['additional_data']
            report, tables = generate_report(high_info, mid_info, low_info, student_info, all_data, additional_data)

        st.success("보고서 생성이 완료되었습니다!")
        st.markdown(report, unsafe_allow_html=True)

        # 지원 가능안 상세 표 출력
        st.markdown("---\n\n### 지원 가능안 상세 📋\n\n")
        for table in tables:
            st.subheader(table['title'])
            if table['data'] is not None:
                # NaN 값을 '-'로 대체
                display_data = table['data'].applymap(format_value)
                st.dataframe(
                    display_data,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "구분": st.column_config.TextColumn("구분", width=50),
                        "대학명": st.column_config.TextColumn("대학명", width=80),
                        "전형구분": st.column_config.TextColumn("전형", width=60),
                        "전형명": st.column_config.TextColumn("전형명", width=100),
                        "모집단위": st.column_config.TextColumn("모집단위", width=100),
                        "2025년_모집인원": st.column_config.TextColumn("모집", width=50),
                        "2025년_최저요약": st.column_config.TextColumn("수능최저", width=80),
                        "2024년_경쟁률": st.column_config.TextColumn("24경쟁", width=60),
                        "2023년_경쟁률": st.column_config.TextColumn("23경쟁", width=60),
                        "2024년_입결70%": st.column_config.TextColumn("입결70", width=60),
                        "2024년_추가합격자수": st.column_config.TextColumn("추가", width=50),
                    },
                    height=400  # 테이블의 높이를 제한
                )
            else:
                st.warning(f"{table['title']} 지원 데이터가 없거나 필요한 열이 존재하지 않습니다.")

        # 대학별 2025학년도 핵심정리
        st.markdown("---\n\n### 대학별 2025학년도 핵심정리 🎓\n\n")

        # 모든 필터링된 데이터를 합치기
        all_filtered_data = pd.concat([high_info, mid_info, low_info], ignore_index=True)

        # 중복 제거
        unique_universities = all_filtered_data.drop_duplicates(subset=['대학명', '전형구분', '전형명'])

        # 추가 데이터와 매칭하여 핵심정리 출력
        additional_data = st.session_state['additional_data']

        for admission_type in ['교과', '종합']:
            st.subheader(f"{admission_type} 전형")
            filtered_universities = unique_universities[unique_universities['전형구분'] == admission_type]

            for _, row in filtered_universities.iterrows():
                match = additional_data[(additional_data['대학명'] == row['대학명']) &
                                        (additional_data['전형구분'] == row['전형구분']) &
                                        (additional_data['전형명'] == row['전형명'])]
                if not match.empty:
                    st.markdown(f"**{row['대학명']} - {row['전형명']}**")

                    core_summary = match.iloc[0]['2025학년도_핵심정리']
                    core_summary_html = core_summary.replace('\n', '<br>')

                    st.markdown(
                        f"<div style='background-color: rgba(0, 0, 0, 0.1); color: black; padding: 10px; border-radius: 5px;'>{core_summary_html}</div>",
                        unsafe_allow_html=True)

                    st.markdown("---")


if __name__ == "__main__":
    show_report_generation()
