import streamlit as st
from data_loader import load_data, load_json
from filters import apply_competition_filter, apply_entrance_score_filter, apply_acceptance_rate_filter
from utils import get_university_list, get_university_info, preprocess_data, find_related_majors, filter_top_n
from report_generator import generate_report
from config import DATA_FILE_PATH, UNIVERSITY_RANGES_FILE_PATH, MAJOR_DATA_FILE_PATH, FILTER_DATA_FILE_PATH
import pandas as pd
import io
from docx import Document
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import base64

def save_as_docx(report):
    doc = Document()
    doc.add_paragraph(report)
    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    return doc_io

def save_as_pdf(report):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # 한글 폰트 설정
    font_path = '/Users/isaac/Library/Fonts/maruburi/MaruBuri-Regular.ttf'
    pdfmetrics.registerFont(TTFont('MaruBuri', font_path))
    c.setFont('MaruBuri', 12)

    # 페이지 크기와 여백 설정
    width, height = letter
    text = report.split('\n')
    y = height - 72

    for line in text:
        c.drawString(72, y, line)
        y -= 15  # 줄 간격

    c.save()
    buffer.seek(0)
    return buffer

def save_as_markdown(report):
    return io.BytesIO(report.encode())


def main():
    st.title("지략 수시전략 컨설팅 지원 시스템 🎓")

    # 탭의 크기를 화면에 꽉 차도록 설정
    tabs_css = """
    <style>
    [data-testid="stHorizontalBlock"] [data-testid="stVerticalBlock"] {
        display: flex;
        justify-content: space-between;
    }
    [data-testid="stTabs"] button {
        flex: 1;
    }
    .stTabs [data-testid="stTabs"] {
        margin-bottom: 20px;
    }
    .stButton button {
        width: 100%;
        display: block;
        margin: 0 auto;
        background-color: #4CAF50;
        color: white;
    }
    </style>
    """
    st.markdown(tabs_css, unsafe_allow_html=True)

    tabs = st.tabs(["1단계 검색", "2단계 검색", "필터링", "보고서 작성"])

    # 데이터 로드
    data = load_data(DATA_FILE_PATH)
    university_ranges = load_json(UNIVERSITY_RANGES_FILE_PATH)
    major_data = load_json(MAJOR_DATA_FILE_PATH)
    filter_data = load_json(FILTER_DATA_FILE_PATH)

    with tabs[0]:
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("1단계 검색: 학생 정보와 성적을 기반으로 대학을 검색합니다.")
        school_type = st.radio("학교 유형을 선택하세요", ["일반고", "자사/특목고"])
        major_interest_input = st.text_input("희망 전공 또는 계열을 입력하세요 (쉼표로 구분)")

        if major_interest_input:
            major_interests = [major.strip() for major in major_interest_input.split(',') if major.strip()]
            st.write("입력된 전공 또는 계열: ", ", ".join(major_interests))

        score = st.number_input("성적을 입력하세요", min_value=1.0, max_value=5.0)
        high_factor = st.slider("상향 성적 배수", min_value=0.5, max_value=1.0, value=0.7, step=0.01)
        low_factor = st.slider("안정 성적 배수", min_value=1.1, max_value=1.5, value=1.3, step=0.01)
        include_womens_universities = st.checkbox("여대 포함 여부")

        admission_types = st.multiselect(
            "전형구분을 선택하세요",
            ["종합", "교과", "논술", "기타"],
            default=["종합", "교과", "논술"]
        )

        submit_button = st.button("결과 확인")

        if submit_button:
            st.session_state['student_info'] = {
                'school_type': school_type,
                'desired_major': ", ".join(major_interests),
                'gpa': score,
                'high_factor': high_factor,
                'low_factor': low_factor,
                'include_womens_universities': include_womens_universities,
                'admission_types': admission_types
            }

            major_interests = [major.strip() for major in major_interest_input.split(',')]
            related_majors = find_related_majors(major_interests, major_data)

            high_score = max(score * high_factor, 1.0)
            mid_score = score
            low_score = score * low_factor

            st.session_state['high_score'] = high_score
            st.session_state['mid_score'] = mid_score
            st.session_state['low_score'] = low_score
            st.session_state['major_interests'] = major_interests
            st.session_state['related_majors'] = related_majors
            st.session_state['school_type'] = school_type
            st.session_state['score'] = score
            st.session_state['high_factor'] = high_factor
            st.session_state['low_factor'] = low_factor
            st.session_state['include_womens_universities'] = include_womens_universities
            st.session_state['admission_types'] = admission_types

            if school_type == "일반고":
                selected_university_ranges = university_ranges['general']
            else:
                selected_university_ranges = university_ranges['special_purpose']

            high_universities = get_university_list(high_score, selected_university_ranges)
            mid_universities = get_university_list(mid_score, selected_university_ranges)
            low_universities = get_university_list(low_score, selected_university_ranges)

            high_universities_info = get_university_info(high_universities, data)
            mid_universities_info = get_university_info(mid_universities, data)
            low_universities_info = get_university_info(low_universities, data)

            if not include_womens_universities:
                high_universities_info = high_universities_info[~high_universities_info['대학명'].str.contains('여대')]
                mid_universities_info = mid_universities_info[~mid_universities_info['대학명'].str.contains('여대')]
                low_universities_info = low_universities_info[~low_universities_info['대학명'].str.contains('여대')]

            # 전형구분 필터링 추가
            if admission_types:
                pattern = '|'.join([f'^{at}$' for at in admission_types])
                high_universities_info = high_universities_info[
                    high_universities_info['전형구분'].str.contains(pattern, regex=True)]
                mid_universities_info = mid_universities_info[
                    mid_universities_info['전형구분'].str.contains(pattern, regex=True)]
                low_universities_info = low_universities_info[
                    low_universities_info['전형구분'].str.contains(pattern, regex=True)]

            high_universities_info = preprocess_data(high_universities_info)
            mid_universities_info = preprocess_data(mid_universities_info)
            low_universities_info = preprocess_data(low_universities_info)

            high_universities_info = high_universities_info[high_universities_info['2025년_모집인원'] > 0]
            mid_universities_info = mid_universities_info[mid_universities_info['2025년_모집인원'] > 0]
            low_universities_info = low_universities_info[low_universities_info['2025년_모집인원'] > 0]

            st.session_state['high_university_info'] = high_universities_info
            st.session_state['mid_university_info'] = mid_universities_info
            st.session_state['low_university_info'] = low_universities_info

            st.write(f"### 상향 대학교 목록 : {len(high_universities_info)}개")
            st.write(high_universities_info)
            st.write(f"### 적정 대학교 목록 : {len(mid_universities_info)}개")
            st.write(mid_universities_info)
            st.write(f"### 안정 대학교 목록 : {len(low_universities_info)}개")
            st.write(low_universities_info)

    with tabs[1]:
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("2단계 검색: 1단계 검색 결과를 기반으로 세부 조건을 설정하여 대학을 필터링합니다.")
        if 'high_university_info' in st.session_state and 'mid_university_info' in st.session_state and 'low_university_info' in st.session_state and 'major_interests' in st.session_state and 'related_majors' in st.session_state:
            high_university_info = st.session_state['high_university_info']
            mid_university_info = st.session_state['mid_university_info']
            low_university_info = st.session_state['low_university_info']
            major_interests = st.session_state['major_interests']
            related_majors = st.session_state['related_majors']

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.subheader("전공 필터")
                major_type = st.radio("전공 필터 선택", ["무관", "계열 매칭", "키워드 매칭"])

            with col2:
                st.subheader("경쟁률 필터")
                competition_rate_filter = st.checkbox("경쟁률 필터")
                if competition_rate_filter:
                    with st.expander("세부 조건 설정"):
                        st.markdown("**상향**")
                        competition_rate_value_high = st.number_input("상향 경쟁률 강도", value=float(
                            filter_data['competition_strength']['high_support'].get('2024년_경쟁강도', 0)), min_value=0.0,
                                                                      step=0.1, key='comp_high')
                        competition_rate_increase_high = st.selectbox("상향 경쟁률 상승 여부", options=["NO", "YES"],
                                                                      index=0 if filter_data['competition_strength'][
                                                                                     'high_support'].get(
                                                                          '2024년_경쟁률상승여부', 'NO') == "NO" else 1,
                                                                      key='comp_inc_high')
                        competition_rate_percentage_high = st.number_input("상향 경쟁률 상승 정도(%)", value=float(
                            filter_data['competition_strength']['high_support'].get('2024년_경쟁률상승정도(%)', 0)),
                                                                           min_value=0.0, step=0.1, key='comp_per_high')
                        st.markdown("---")
                        st.markdown("**적정**")
                        competition_rate_value_mid = st.number_input("적정 경쟁률 강도", value=float(
                            filter_data['competition_strength']['adequate_support'].get('2024년_경쟁강도', 0)),
                                                                     min_value=0.0, step=0.1, key='comp_mid')
                        competition_rate_increase_mid = st.selectbox("적정 경쟁률 상승 여부", options=["NO", "YES"],
                                                                     index=0 if filter_data['competition_strength'][
                                                                                    'adequate_support'].get(
                                                                         '2024년_경쟁률상승여부', 'NO') == "NO" else 1,
                                                                     key='comp_inc_mid')
                        competition_rate_percentage_mid = st.number_input("적정 경쟁률 상승 정도(%)", value=float(
                            filter_data['competition_strength']['adequate_support'].get('2024년_경쟁률상승정도(%)', 0)),
                                                                          min_value=0.0, step=0.1, key='comp_per_mid')
                        st.markdown("---")
                        st.markdown("**안정**")
                        competition_rate_value_low = st.number_input("안정 경쟁률 강도", value=float(
                            filter_data['competition_strength']['low_support'].get('2024년_경쟁강도', 0)), min_value=0.0,
                                                                     step=0.1, key='comp_low')
                        competition_rate_increase_low = st.selectbox("안정 경쟁률 상승 여부", options=["NO", "YES"],
                                                                     index=0 if filter_data['competition_strength'][
                                                                                    'low_support'].get('2024년_경쟁률상승여부',
                                                                                                       'NO') == "NO" else 1,
                                                                     key='comp_inc_low')
                        competition_rate_percentage_low = st.number_input("안정 경쟁률 상승 정도(%)", value=float(
                            filter_data['competition_strength']['low_support'].get('2024년_경쟁률상승정도(%)', 0)),
                                                                          min_value=0.0, step=0.1, key='comp_per_low')

            with col3:
                st.subheader("입결 필터")
                entrance_score_filter = st.checkbox("입결 필터")
                if entrance_score_filter:
                    with st.expander("세부 조건 설정"):
                        st.markdown("**상향**")
                        entrance_score_difference_high = st.number_input("상향 입결 차이(%)", value=float(
                            filter_data['entrance_score']['high_support'].get('2024년_입결70%차이(%)', 0)), min_value=0.0,
                                                                         step=0.1, key='ent_diff_high')
                        entrance_score_decrease_high = st.selectbox("상향 입결 하락 여부", options=["NO", "YES"],
                                                                    index=0 if filter_data['entrance_score'][
                                                                                   'high_support'].get(
                                                                        '2024년_입결70%하락여부', 'NO') == "NO" else 1,
                                                                    key='ent_dec_high')
                        st.markdown("---")
                        st.markdown("**적정**")
                        entrance_score_difference_mid = st.number_input("적정 입결 차이(%)", value=float(
                            filter_data['entrance_score']['adequate_support'].get('2024년_입결70%차이(%)', 0)),
                                                                        min_value=0.0, step=0.1, key='ent_diff_mid')
                        entrance_score_decrease_mid = st.selectbox("적정 입결 하락 여부", options=["NO", "YES"],
                                                                   index=0 if filter_data['entrance_score'][
                                                                                  'adequate_support'].get(
                                                                       '2024년_입결70%하락여부', 'NO') == "NO" else 1,
                                                                   key='ent_dec_mid')
                        st.markdown("---")
                        st.markdown("**안정**")
                        entrance_score_difference_low = st.number_input("안정 입결 차이(%)", value=float(
                            filter_data['entrance_score']['low_support'].get('2024년_입결70%차이(%)', 0)), min_value=0.0,
                                                                        step=0.1, key='ent_diff_low')
                        entrance_score_decrease_low = st.selectbox("안정 입결 하락 여부", options=["NO", "YES"],
                                                                   index=0 if filter_data['entrance_score'][
                                                                                  'low_support'].get('2024년_입결70%하락여부',
                                                                                                     'NO') == "NO" else 1,
                                                                   key='ent_dec_low')

            with col4:
                st.subheader("충원률 필터")
                acceptance_rate_filter = st.checkbox("충원률 필터")
                if acceptance_rate_filter:
                    with st.expander("세부 조건 설정"):
                        st.markdown("**상향**")
                        acceptance_rate_value_high = st.number_input("상향 충원률(%)", value=float(
                            filter_data['acceptance_rate']['high_support'].get('2024년_충원률(%)', 0)), min_value=0.0,
                                                                     step=0.1, key='acc_high')
                        acceptance_rate_average_high = st.number_input("상향 3개년 평균 충원률", value=float(
                            filter_data['acceptance_rate']['high_support'].get('3개년_평균_충원률', 0)), min_value=0.0,
                                                                       step=0.1, key='acc_avg_high')
                        st.markdown("---")
                        st.markdown("**적정**")
                        acceptance_rate_value_mid = st.number_input("적정 충원률(%)", value=float(
                            filter_data['acceptance_rate']['adequate_support'].get('2024년_충원률(%)', 0)), min_value=0.0,
                                                                    step=0.1, key='acc_mid')
                        acceptance_rate_average_mid = st.number_input("적정 3개년 평균 충원률", value=float(
                            filter_data['acceptance_rate']['adequate_support'].get('3개년_평균_충원률', 0)), min_value=0.0,
                                                                      step=0.1, key='acc_avg_mid')
                        st.markdown("---")
                        st.markdown("**안정**")
                        acceptance_rate_value_low = st.number_input("안정 충원률(%)", value=float(
                            filter_data['acceptance_rate']['low_support'].get('2024년_충원률(%)', 0)), min_value=0.0,
                                                                    step=0.1, key='acc_low')
                        acceptance_rate_average_low = st.number_input("안정 3개년 평균 충원률", value=float(
                            filter_data['acceptance_rate']['low_support'].get('3개년_평균_충원률', 0)), min_value=0.0,
                                                                      step=0.1, key='acc_avg_low')

            new_department_include = st.checkbox("신설 무조건 포함")

            st.markdown("<br><br>", unsafe_allow_html=True)  # Add space before button

            # Place '2단계 탐색' button prominently
            if st.button("2단계 탐색", key='explore_button'):
                filtered_high_info = high_university_info
                filtered_mid_info = mid_university_info
                filtered_low_info = low_university_info

                if major_type == "계열 매칭":
                    filtered_high_info = filtered_high_info[
                        filtered_high_info['전공'].apply(lambda x: any(major in x for major in related_majors))]
                    filtered_mid_info = filtered_mid_info[
                        filtered_mid_info['전공'].apply(lambda x: any(major in x for major in related_majors))]
                    filtered_low_info = filtered_low_info[
                        filtered_low_info['전공'].apply(lambda x: any(major in x for major in related_majors))]

                elif major_type == "키워드 매칭":
                    filtered_high_info = filtered_high_info[
                        filtered_high_info['전공'].apply(lambda x: any(keyword in x for keyword in major_interests))]
                    filtered_mid_info = filtered_mid_info[
                        filtered_mid_info['전공'].apply(lambda x: any(keyword in x for keyword in major_interests))]
                    filtered_low_info = filtered_low_info[
                        filtered_low_info['전공'].apply(lambda x: any(keyword in x for keyword in major_interests))]

                if competition_rate_filter:
                    filter_criteria_high = {
                        '2024년_경쟁강도': competition_rate_value_high,
                        '2024년_경쟁률상승여부': competition_rate_increase_high,
                        '2024년_경쟁률상승정도(%)': competition_rate_percentage_high
                    }
                    filter_criteria_mid = {
                        '2024년_경쟁강도': competition_rate_value_mid,
                        '2024년_경쟁률상승여부': competition_rate_increase_mid,
                        '2024년_경쟁률상승정도(%)': competition_rate_percentage_mid
                    }
                    filter_criteria_low = {
                        '2024년_경쟁강도': competition_rate_value_low,
                        '2024년_경쟁률상승여부': competition_rate_increase_low,
                        '2024년_경쟁률상승정도(%)': competition_rate_percentage_low
                    }

                    filtered_high_info = apply_competition_filter(filtered_high_info, filter_criteria_high)
                    filtered_mid_info = apply_competition_filter(filtered_mid_info, filter_criteria_mid)
                    filtered_low_info = apply_competition_filter(filtered_low_info, filter_criteria_low)

                if entrance_score_filter:
                    filter_criteria_high = {
                        '2024년_입결70%차이(%)': entrance_score_difference_high,
                        '2024년_입결70%하락여부': entrance_score_decrease_high
                    }
                    filter_criteria_mid = {
                        '2024년_입결70%차이(%)': entrance_score_difference_mid,
                        '2024년_입결70%하락여부': entrance_score_decrease_mid
                    }
                    filter_criteria_low = {
                        '2024년_입결70%차이(%)': entrance_score_difference_low,
                        '2024년_입결70%하락여부': entrance_score_decrease_low
                    }

                    filtered_high_info = apply_entrance_score_filter(filtered_high_info, filter_criteria_high,
                                                                     st.session_state['mid_score'])
                    filtered_mid_info = apply_entrance_score_filter(filtered_mid_info, filter_criteria_mid,
                                                                    st.session_state['mid_score'])
                    filtered_low_info = apply_entrance_score_filter(filtered_low_info, filter_criteria_low,
                                                                    st.session_state['mid_score'])

                if acceptance_rate_filter:
                    filter_criteria_high = {
                        '2024년_충원률(%)': acceptance_rate_value_high,
                        '3개년_평균_충원률': acceptance_rate_average_high
                    }
                    filter_criteria_mid = {
                        '2024년_충원률(%)': acceptance_rate_value_mid,
                        '3개년_평균_충원률': acceptance_rate_average_mid
                    }
                    filter_criteria_low = {
                        '2024년_충원률(%)': acceptance_rate_value_low,
                        '3개년_평균_충원률': acceptance_rate_average_low
                    }

                    filtered_high_info = apply_acceptance_rate_filter(filtered_high_info, filter_criteria_high)
                    filtered_mid_info = apply_acceptance_rate_filter(filtered_mid_info, filter_criteria_mid)
                    filtered_low_info = apply_acceptance_rate_filter(filtered_low_info, filter_criteria_low)

                if new_department_include:
                    new_departments_high = high_university_info[high_university_info['신설'] == 'YES']
                    new_departments_mid = mid_university_info[mid_university_info['신설'] == 'YES']
                    new_departments_low = low_university_info[low_university_info['신설'] == 'YES']

                    filtered_high_info = pd.concat(
                        [filtered_high_info, new_departments_high]).drop_duplicates().reset_index(drop=True)
                    filtered_mid_info = pd.concat(
                        [filtered_mid_info, new_departments_mid]).drop_duplicates().reset_index(drop=True)
                    filtered_low_info = pd.concat(
                        [filtered_low_info, new_departments_low]).drop_duplicates().reset_index(drop=True)

                st.session_state['filtered_high_info'] = filtered_high_info
                st.session_state['filtered_mid_info'] = filtered_mid_info
                st.session_state['filtered_low_info'] = filtered_low_info

                if competition_rate_filter:
                    st.session_state['filter_criteria_high'] = filter_criteria_high
                    st.session_state['filter_criteria_mid'] = filter_criteria_mid
                    st.session_state['filter_criteria_low'] = filter_criteria_low

                if entrance_score_filter:
                    st.session_state['filter_criteria_high'] = filter_criteria_high
                    st.session_state['filter_criteria_mid'] = filter_criteria_mid
                    st.session_state['filter_criteria_low'] = filter_criteria_low

                if acceptance_rate_filter:
                    st.session_state['filter_criteria_high'] = filter_criteria_high
                    st.session_state['filter_criteria_mid'] = filter_criteria_mid
                    st.session_state['filter_criteria_low'] = filter_criteria_low

                st.write(
                    f"### 필터 적용 후 상향 대학교 목록 : {len(filtered_high_info)}개, 신설 {len(filtered_high_info[filtered_high_info['신설'] == 'YES'])}개")
                st.write(filtered_high_info)
                st.write(
                    f"### 필터 적용 후 적정 대학교 목록 : {len(filtered_mid_info)}개, 신설 {len(filtered_mid_info[filtered_mid_info['신설'] == 'YES'])}개")
                st.write(filtered_mid_info)
                st.write(
                    f"### 필터 적용 후 안정 대학교 목록 : {len(filtered_low_info)}개, 신설 {len(filtered_low_info[filtered_low_info['신설'] == 'YES'])}개")
                st.write(filtered_low_info)

    with tabs[2]:
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("필터링: 2단계 검색 결과를 기준으로 정렬하여 상위 10개의 대학을 추출합니다.")
        if 'filtered_high_info' in st.session_state and 'filtered_mid_info' in st.session_state and 'filtered_low_info' in st.session_state:
            filtered_high_info = st.session_state['filtered_high_info']
            filtered_mid_info = st.session_state['filtered_mid_info']
            filtered_low_info = st.session_state['filtered_low_info']

            col1, col2, col3 = st.columns(3)

            with col1:
                st.subheader("상향 정렬 기준")
                high_sort_criteria = st.selectbox("정렬 기준", ["2025년_모집인원", "2024년_경쟁률", "2024년_충원률(%)", "2024년_입결50%",
                                                            "2024년 입결 70%", "3개년 경쟁률 평균", "2024년 경쟁강도", "수능 최저 없음 우선",
                                                            "신설"], key='high_sort')
                if high_sort_criteria in ["수능 최저 없음 우선"]:
                    high_sort_order = st.selectbox("정렬 옵션", ["미적용 우선"], key='high_order')
                elif high_sort_criteria == "신설":
                    high_sort_order = st.selectbox("정렬 옵션", ["YES", "NO"], key='high_order')
                else:
                    high_sort_order = st.selectbox("정렬 순서", ["오름차순", "내림차순"], key='high_order')

            with col2:
                st.subheader("적정 정렬 기준")
                mid_sort_criteria = st.selectbox("정렬 기준", ["2025년_모집인원", "2024년_경쟁률", "2024년_충원률(%)", "2024년_입결50%",
                                                           "2024년 입결 70%", "3개년 경쟁률 평균", "2024년 경쟁강도", "수능 최저 없음 우선",
                                                           "신설"], key='mid_sort')
                if mid_sort_criteria in ["수능 최저 없음 우선"]:
                    mid_sort_order = st.selectbox("정렬 옵션", ["미적용 우선"], key='mid_order')
                elif mid_sort_criteria == "신설":
                    mid_sort_order = st.selectbox("정렬 옵션", ["YES", "NO"], key='mid_order')
                else:
                    mid_sort_order = st.selectbox("정렬 순서", ["오름차순", "내림차순"], key='mid_order')

            with col3:
                st.subheader("안정 정렬 기준")
                low_sort_criteria = st.selectbox("정렬 기준", ["2025년_모집인원", "2024년_경쟁률", "2024년_충원률(%)", "2024년_입결50%",
                                                           "2024년 입결 70%", "3개년 경쟁률 평균", "2024년 경쟁강도", "수능 최저 없음 우선",
                                                           "신설"], key='low_sort')
                if low_sort_criteria in ["수능 최저 없음 우선"]:
                    low_sort_order = st.selectbox("정렬 옵션", ["미적용 우선"], key='low_order')
                elif low_sort_criteria == "신설":
                    low_sort_order = st.selectbox("정렬 옵션", ["YES", "NO"], key='low_order')
                else:
                    low_sort_order = st.selectbox("정렬 순서", ["오름차순", "내림차순"], key='low_order')

            st.markdown("<br><br>", unsafe_allow_html=True)

            if st.button("필터링 적용", key='filter_button'):
                sort_order_map = {"오름차순": True, "내림차순": False}

                def sort_and_filter(df, criteria, order):
                    if criteria == "수능 최저 없음 우선":
                        sorted_df = df.sort_values(by=['2025년_수능최저'], key=lambda col: col == '없음', ascending=False).head(
                            10)
                    elif criteria == "신설":
                        sorted_df = df[df['신설'] == order].head(10)
                    else:
                        sorted_df = df.sort_values(by=criteria, ascending=sort_order_map[order]).head(10)
                    return sorted_df

                st.session_state['filtered_high_info'] = sort_and_filter(filtered_high_info, high_sort_criteria,
                                                                         high_sort_order)
                st.session_state['filtered_mid_info'] = sort_and_filter(filtered_mid_info, mid_sort_criteria,
                                                                        mid_sort_order)
                st.session_state['filtered_low_info'] = sort_and_filter(filtered_low_info, low_sort_criteria,
                                                                        low_sort_order)

            st.write(f"### 필터링 적용 후 상향 대학교 목록 : {len(st.session_state['filtered_high_info'])}개")
            st.write(st.session_state['filtered_high_info'])
            st.write(f"### 필터링 적용 후 적정 대학교 목록 : {len(st.session_state['filtered_mid_info'])}개")
            st.write(st.session_state['filtered_mid_info'])
            st.write(f"### 필터링 적용 후 안정 대학교 목록 : {len(st.session_state['filtered_low_info'])}개")
            st.write(st.session_state['filtered_low_info'])

    with tabs[3]:
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("보고서 작성: 필터링된 결과를 바탕으로 보고서를 작성합니다.")
        col1, col2, col3 = st.columns(3)

        with col1:
            with st.expander("학생 정보"):
                st.write("학교 유형:", st.session_state.get('school_type', ''))
                st.write("성적:", st.session_state.get('score', ''))
                st.write("상향 성적 배수:", st.session_state.get('high_factor', ''))
                st.write("안정 성적 배수:", st.session_state.get('low_factor', ''))
                st.write("여대 포함 여부:", st.session_state.get('include_womens_universities', ''))
                st.write("희망 전공 또는 계열:", ", ".join(st.session_state.get('major_interests', [])))

        with col2:
            with st.expander("2단계 탐색 현황"):
                st.write(
                    f"상향 대학교 목록 : {len(st.session_state.get('filtered_high_info', []))}개, 신설 {len(st.session_state.get('filtered_high_info', pd.DataFrame()).loc[st.session_state.get('filtered_high_info', pd.DataFrame())['신설'] == 'YES'])}개")
                st.write(
                    f"적정 대학교 목록 : {len(st.session_state.get('filtered_mid_info', []))}개, 신설 {len(st.session_state.get('filtered_mid_info', pd.DataFrame()).loc[st.session_state.get('filtered_mid_info', pd.DataFrame())['신설'] == 'YES'])}개")
                st.write(
                    f"안정 대학교 목록 : {len(st.session_state.get('filtered_low_info', []))}개, 신설 {len(st.session_state.get('filtered_low_info', pd.DataFrame()).loc[st.session_state.get('filtered_low_info', pd.DataFrame())['신설'] == 'YES'])}개")

        with col3:
            with st.expander("2단계 필터 설정"):
                st.markdown("**상향 필터:**")
                st.write(st.session_state.get('filter_criteria_high', {}))
                st.markdown("**적정 필터:**")
                st.write(st.session_state.get('filter_criteria_mid', {}))
                st.markdown("**안정 필터:**")
                st.write(st.session_state.get('filter_criteria_low', {}))

        if st.button("보고서 작성"):
            with st.spinner("보고서 작성 중..."):
                if 'filtered_high_info' in st.session_state and 'filtered_mid_info' in st.session_state and 'filtered_low_info' in st.session_state:
                    student_info = {
                        'school_type': st.session_state.get('school_type', ''),
                        'desired_major': ", ".join(st.session_state.get('major_interests', [])),
                        'gpa': st.session_state.get('score', ''),
                        'filter_info': str(st.session_state.get('filter_criteria_high', {}))
                    }
                    report = generate_report(
                        st.session_state['filtered_high_info'],
                        st.session_state['filtered_mid_info'],
                        st.session_state['filtered_low_info'],
                        student_info,
                        data
                    )
                    st.markdown(report, unsafe_allow_html=True)

                    # 보고서 저장 옵션
                    st.write("보고서 저장 옵션:")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("PDF로 저장"):
                            pdf_buffer = save_as_pdf(report)
                            st.download_button(
                                label="PDF 다운로드",
                                data=pdf_buffer,
                                file_name="report.pdf",
                                mime="application/pdf"
                            )
                    with col2:
                        if st.button("Word로 저장"):
                            docx_buffer = save_as_docx(report)
                            st.download_button(
                                label="Word 다운로드",
                                data=docx_buffer,
                                file_name="report.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
                    with col3:
                        if st.button("Markdown으로 저장"):
                            markdown_buffer = save_as_markdown(report)
                            st.download_button(
                                label="Markdown 다운로드",
                                data=markdown_buffer,
                                file_name="report.md",
                                mime="text/markdown"
                            )
                else:
                    st.warning("필터링된 데이터가 없습니다. 먼저 필터링을 수행해주세요.")


if __name__ == "__main__":
    main()
