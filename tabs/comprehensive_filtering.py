import streamlit as st
import pandas as pd
from data_loader import data
from filters import filter_data_comprehensive, apply_filters
from ui_components import create_option_filters, display_university_checklist
from category_mapping import DETAIL_TO_MID_CATEGORY, MID_TO_MAIN_CATEGORY

def create_filter_box(title, content):
    st.markdown(f"""
    <style>
    .filter-box {{
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
    }}
    .filter-title {{
        font-weight: bold;
        margin-bottom: 5px;
        color: #262730;
    }}
    </style>
    <div class="filter-box">
        <div class="filter-title">{title}</div>
        {content}
    </div>
    """, unsafe_allow_html=True)

def add_search_range_selector(prefix):
    search_range = st.radio(
        "대계열은 '인문'/ 중계열은 '상경계열'/ 소계열은 '경영'을 뜻합니다.",
        ("대계열 검색", "중계열 검색", "소계열 검색"),
        horizontal=True,
        key=f"{prefix}_search_range"
    )
    return search_range


def filter_by_search_range(df, student_info, search_range):
    if df.empty:
        return df

    if search_range == "대계열 검색":
        return df[df['계열'].isin(student_info['field'])]

    elif search_range == "중계열 검색":
        mid_categories = list(set([DETAIL_TO_MID_CATEGORY.get(field, "") for field in student_info['detail_fields']]))
        return df[df['계열구분'].isin(mid_categories)]

    elif search_range == "소계열 검색":
        return df[df['계열상세명'].apply(
            lambda x: any(field.lower() in str(x).lower() for field in student_info['detail_fields']))]

    return df
def show_comprehensive_filtering():
    if 'student_info' not in st.session_state:
        st.warning("정보입력 탭에서 먼저 정보를 입력하세요.")
        return

    student_info = st.session_state['student_info']

    st.info("학종 전형 필터링을 위한 조건을 설정해보세요.")

    # 검색 범위 선택
    create_filter_box("🔍 검색 범위", "")
    search_range = add_search_range_selector("comprehensive")

    # 필터 옵션들
    create_filter_box("⚙️ 옵션 필터", "")
    filters = create_option_filters(prefix="comprehensive_")

    # 수능최저역량 필터
    create_filter_box("📊 수능최저역량", "")
    lowest_ability_filter = st.checkbox("수능최저역량 반영", key="comprehensive_lowest_ability")
    st.session_state['student_info']['lowest_ability_filter'] = lowest_ability_filter


    st.markdown("&nbsp;")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("1차 필터링", key="comprehensive_first_filter_button"):
            high_list, mid_list, low_list = filter_data_comprehensive(student_info, data)

            high_list = filter_by_search_range(high_list, student_info, search_range)
            mid_list = filter_by_search_range(mid_list, student_info, search_range)
            low_list = filter_by_search_range(low_list, student_info, search_range)

            high_list = apply_filters(high_list, filters, student_info, '상향')
            mid_list = apply_filters(mid_list, filters, student_info, '적정')
            low_list = apply_filters(low_list, filters, student_info, '하향')

            if lowest_ability_filter:
                high_list = high_list[high_list['2025년_수능최저코드'] <= student_info['lowest_ability_code']]
                mid_list = mid_list[mid_list['2025년_수능최저코드'] <= student_info['lowest_ability_code']]
                low_list = low_list[low_list['2025년_수능최저코드'] <= student_info['lowest_ability_code']]

            st.session_state['comprehensive_first_filter_results'] = {
                'high_list': high_list if not high_list.empty else pd.DataFrame(),
                'mid_list': mid_list if not mid_list.empty else pd.DataFrame(),
                'low_list': low_list if not low_list.empty else pd.DataFrame()
            }
            st.success("1차 필터링이 완료되었습니다.")

    if 'comprehensive_first_filter_results' in st.session_state:
        st.markdown("---")
        st.markdown("&nbsp;")
        st.subheader("1️⃣ 1차 필터링 결과")
        for list_type, list_name in [('high_list', '상향'), ('mid_list', '적정'), ('low_list', '하향')]:
            df = st.session_state['comprehensive_first_filter_results'][list_type]
            if not df.empty and '대학명' in df.columns:
                selected = display_university_checklist(df, f"{list_name} 리스트", prefix="comprehensive_")
                st.session_state[f'comprehensive_{list_type}_selected'] = selected
            else:
                st.warning(f"{list_name} 리스트에 데이터가 없거나 '대학명' 열이 없습니다.")

    with col2:
        if st.button("2차 필터링", key="comprehensive_second_filter_button"):
            st.session_state['comprehensive_second_filter_results'] = {}
            for list_type in ['high_list', 'mid_list', 'low_list']:
                df = st.session_state['comprehensive_first_filter_results'].get(list_type, pd.DataFrame())
                selected = st.session_state.get(f'comprehensive_{list_type}_selected', [])
                if not df.empty and '대학명' in df.columns:
                    filtered_df = df[df['대학명'].isin(selected)]
                    st.session_state['comprehensive_second_filter_results'][list_type] = filtered_df
            st.success("2차 필터링이 완료되었습니다.")

    if 'comprehensive_second_filter_results' in st.session_state:
        st.markdown("---")
        st.markdown("&nbsp;")
        st.subheader("2️⃣ 2차 필터링 결과")
        for index, (list_type, list_name, emoji) in enumerate(
                [('high_list', '상향', '⬆️'), ('mid_list', '적정', '➖'), ('low_list', '하향', '⬇️')]):
            if index > 0:
                st.markdown("<hr style='border-top: 3px dashed #bbb;'>", unsafe_allow_html=True)  # 파선 추가
            df = st.session_state['comprehensive_second_filter_results'].get(list_type, pd.DataFrame())
            if not df.empty:
                st.write(f"**{emoji} {list_name} 리스트**")
                if '대학명' in df.columns:
                    for univ in df['대학명'].unique():
                        st.write(f"**{univ}**")
                        group = df[df['대학명'] == univ]

                        # 선택 컬럼을 추가하고 기본값을 True로 설정
                        group['선택'] = True

                        # 선택 컬럼을 맨 앞으로 이동
                        cols = ['선택'] + [col for col in group.columns if col != '선택']
                        group = group[cols]

                        edited_df = st.data_editor(
                            group,
                            hide_index=True,
                            column_config={
                                "선택": st.column_config.CheckboxColumn(
                                    "선택",
                                    help="이 행을 선택하려면 체크하세요"
                                )
                            },
                            disabled=group.columns.drop('선택'),
                            key=f"editor_comprehensive_{list_type}_{univ}"
                        )
                        st.session_state[f'comprehensive_displayed_{list_type}_{univ}'] = edited_df[edited_df['선택']]
                else:
                    st.warning(f"'{list_name}' 리스트에 '대학명' 열이 없습니다.")
            else:
                st.warning(f"{emoji} {list_name} 리스트에 데이터가 없습니다.")

    with col3:
        if st.button("결과 저장", key="save_comprehensive_results_button"):
            saved_results = {
                'high_list': pd.DataFrame(),
                'mid_list': pd.DataFrame(),
                'low_list': pd.DataFrame()
            }
            for list_type in ['high_list', 'mid_list', 'low_list']:
                df = st.session_state['comprehensive_second_filter_results'].get(list_type, pd.DataFrame())
                if not df.empty and '대학명' in df.columns:
                    for univ in df['대학명'].unique():
                        if f'comprehensive_displayed_{list_type}_{univ}' in st.session_state:
                            saved_results[list_type] = pd.concat([saved_results[list_type],
                                                                  st.session_state[
                                                                      f'comprehensive_displayed_{list_type}_{univ}']])
                elif not df.empty:
                    st.warning(f"'{list_type}' 리스트에 '대학명' 열이 없습니다.")

            st.session_state['saved_comprehensive_results'] = saved_results
            total_count = sum(len(df) for df in saved_results.values())
            st.success(f"결과가 저장되었습니다. 총 {total_count}개의 학과가 저장되었습니다.")

if __name__ == "__main__":
    show_comprehensive_filtering()
