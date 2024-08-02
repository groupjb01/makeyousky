import streamlit as st
import pandas as pd


def sort_universities(df, sort_option, sort_order):
    if sort_option == '경쟁률 백분위':
        return df.sort_values('2024년_경쟁률백분위', ascending=(sort_order == '오름차순'))
    elif sort_option == '경쟁률 변동(%)':
        return df.sort_values('2024년_경쟁률변동(%)', ascending=(sort_order == '오름차순'))
    elif sort_option == '3개년 경쟁률 백분위 평균':
        return df.sort_values('3개년_경쟁률백분위_평균', ascending=(sort_order == '오름차순'))
    elif sort_option == '입결70% 변동(%)':
        return df.sort_values('2024년_입결70%변동(%)', ascending=(sort_order == '오름차순'))
    elif sort_option == '3개년 입결70% 평균':
        return df.sort_values('3개년_입결70%_평균', ascending=(sort_order == '오름차순'))
    elif sort_option == '충원율(%)':
        return df.sort_values('2024년_충원율(%)', ascending=(sort_order == '오름차순'))
    elif sort_option == '3개년 충원율 평균':
        return df.sort_values('3개년_충원율_평균', ascending=(sort_order == '오름차순'))
    elif sort_option == '수능최저':
        return df.sort_values('2025년_수능최저코드', ascending=(sort_order == '오름차순'))
    else:
        return df


def order_by_ranking(df):
    if '대학명' not in df.columns:
        st.warning("데이터프레임에 '대학명' 열이 없습니다.")
        return df

    ranking = ['서울대학교', '연세대학교', '고려대학교', 'KAIST', 'POSTECH', '서강대학교', '성균관대학교', '한양대학교', '중앙대학교', '경희대학교', '한국외국어대학교',
               '서울시립대학교', '건국대학교', '동국대학교', '홍익대학교', '국민대학교', '숭실대학교', '세종대학교', '단국대학교', 'DGIST', 'UNIST', 'GIST',
               '이화여자대학교', '성신여자대학교', '숙명여자대학교', '광운대학교', '명지대학교', '상명대학교', '가천대학교', '가톨릭대학교']
    df['ranking'] = df['대학명'].apply(lambda x: ranking.index(x) if x in ranking else len(ranking))
    return df.sort_values('ranking').drop('ranking', axis=1)


def show_final_filtering():
    st.info("교과, 학종 필터링 결과를 조건에 따라 정렬하여 리스트별 최대 10개의 대학을 선정합니다.")

    if 'saved_subject_results' not in st.session_state or 'saved_comprehensive_results' not in st.session_state:
        st.warning("교과 필터링과 학종 필터링을 먼저 완료해주세요.")
        return

    saved_results = st.session_state['saved_subject_results']
    saved_comprehensive_results = st.session_state['saved_comprehensive_results']

    list_names = {'high_list': '상향', 'mid_list': '적정', 'low_list': '하향'}
    list_emojis = {'high_list': '⬆️', 'mid_list': '➖', 'low_list': '⬇️'}
    reverse_list_names = {v: k for k, v in list_names.items()}

    if st.button("전형별 저장 데이터 보기"):
        st.markdown("---")
        st.markdown("&nbsp;")
        st.subheader("1️⃣  전형별 저장 데이터 보기")
        st.subheader("📚 교과 지원 리스트")
        for list_type in ['high_list', 'mid_list', 'low_list']:
            list_name = list_names[list_type]
            emoji = list_emojis[list_type]
            st.write(f"**{emoji} {list_name} 리스트**")
            if list_type in saved_results and not saved_results[list_type].empty:
                df = order_by_ranking(saved_results[list_type])
                st.dataframe(df)
            else:
                st.warning(f"{list_name} 데이터가 없습니다.")

        st.markdown("<hr style='border-top: 3px dashed #bbb;'>", unsafe_allow_html=True)

        st.subheader("📋 학종 지원 리스트")
        for list_type in ['high_list', 'mid_list', 'low_list']:
            list_name = list_names[list_type]
            emoji = list_emojis[list_type]
            st.write(f"**{emoji} {list_name} 리스트**")
            if list_type in saved_comprehensive_results and not saved_comprehensive_results[list_type].empty:
                df = order_by_ranking(saved_comprehensive_results[list_type])
                st.dataframe(df)
            else:
                st.warning(f"{list_name} 데이터가 없습니다.")

    admission_types = ['교과', '학종']
    list_types = ['high_list', 'mid_list', 'low_list']
    sort_options = [
        '경쟁률 백분위',
        '경쟁률 변동(%)',
        '3개년 경쟁률 백분위 평균',
        '입결70% 변동(%)',
        '3개년 입결70% 평균',
        '충원율(%)',
        '3개년 충원율 평균',
        '수능최저'
    ]

    st.markdown("---")
    st.markdown("&nbsp;")
    st.subheader("2️⃣  정렬 조건 설정")

    for admission_type in admission_types:
        emoji = "📚" if admission_type == "교과" else "📋"
        st.subheader(f"{emoji} {admission_type} 전형")
        cols = st.columns(3)
        for i, list_type in enumerate(list_types):
            with cols[i]:
                st.markdown(f"**{list_emojis[list_type]} {list_names[list_type]} 리스트 정렬**")
                sort_option = st.selectbox(
                    "정렬 기준",
                    sort_options,
                    key=f'{admission_type}_{list_type}_sort'
                )
                sort_order = st.selectbox(
                    "정렬 순서",
                    ["내림차순", "오름차순"],
                    key=f'{admission_type}_{list_type}_order'
                )
        st.markdown("&nbsp;")

    if st.button("최종 필터링 적용", key='final_filter_button'):
        final_results = {}
        list_type_map = {'high_list': '상향', 'mid_list': '적정', 'low_list': '하향'}

        for admission_type, results in [('교과', saved_results), ('학종', saved_comprehensive_results)]:
            for list_key in list_types:
                list_type = list_type_map[list_key]
                key = f"{admission_type}_{list_type}"
                df = results.get(list_key, pd.DataFrame())

                if not df.empty:
                    sort_option = st.session_state[f'{admission_type}_{list_key}_sort']
                    sort_order = st.session_state[f'{admission_type}_{list_key}_order']
                    df = sort_universities(df, sort_option, sort_order)
                    final_results[key] = df.head(10)
                else:
                    st.warning(f"{admission_type} {list_type} 리스트에 데이터가 없습니다.")

        st.session_state['final_results'] = final_results
        st.success("최종 필터링이 적용되었습니다.")

    if 'final_results' in st.session_state:
        st.subheader("최종 필터링 결과")
        for i, (key, df) in enumerate(st.session_state['final_results'].items()):
            if i == 3:  # 교과 하향과 학종 상향 사이에 파선 추가
                st.markdown("<hr style='border-top: 3px dashed #bbb;'>", unsafe_allow_html=True)

            admission_type, list_type = key.split('_')
            emoji = "📚" if admission_type == "교과" else "📋"
            list_emoji = list_emojis[reverse_list_names[list_type]]  # 여기를 수정했습니다

            st.write(f"**{emoji} {list_emoji} {admission_type}_{list_type}**")
            df['선택'] = True  # 기본값을 선택된 상태로 설정
            edited_df = st.data_editor(df, hide_index=True, key=f"editor_{key}")
            st.session_state['final_results'][key] = edited_df

        if st.button("리스트 확정"):
            final_selection = {}
            for key, df in st.session_state['final_results'].items():
                selected_df = df[df['선택']]
                if not selected_df.empty:
                    final_selection[key] = selected_df

            if final_selection:
                st.session_state['final_selection'] = final_selection
                counts = {key: len(df) for key, df in final_selection.items()}
                st.success(
                    f"교과 상향 {counts.get('교과_상향', 0)}개, 적정 {counts.get('교과_적정', 0)}개, 하향 {counts.get('교과_하향', 0)}개 / "
                    f"학종 상향 {counts.get('학종_상향', 0)}개, 적정 {counts.get('학종_적정', 0)}개, 하향 {counts.get('학종_하향', 0)}개 저장 완료되었습니다.")
            else:
                st.warning("선택된 항목이 없습니다. 최소한 하나 이상의 항목을 선택해 주세요.")


if __name__ == "__main__":
    show_final_filtering()
