import pandas as pd
from data_loader import SCHOOL_TYPE_ADJUSTMENT


def apply_filters(df, filters, student_info, list_type):
    if not filters[list_type]:
        return df

    for key, value in filters[list_type].items():
        if '경쟁률백분위' in key or '입결70%변동(%)' in key:
            df = df[df[key] < value]
        elif '경쟁률변동(%)' in key or '충원율(%)' in key or '3개년_충원율_평균' in key:
            df = df[df[key] > value]
        elif '3개년_입결70%_평균' in key:
            df = df[df[key] > student_info['adjusted_score'] * value]
    return df


def filter_data(student_info, data):
    filtered_data = data[data['계열'].isin(student_info['field'])]

    if '교과' in student_info['admission_type']:
        filtered_data = filtered_data[filtered_data['전형구분'] == '교과']
    else:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    if student_info['gender'] == '남자':
        filtered_data = filtered_data[~filtered_data['대학명'].str.contains('여자')]

    if student_info['school_type'] == '과학고':
        filtered_data = filtered_data[filtered_data['과학고'] == 1]
    elif student_info['school_type'] == '전사고':
        filtered_data = filtered_data[filtered_data['전사고'] == 1]
    elif student_info['school_type'] == '외고':
        filtered_data = filtered_data[filtered_data['외고'] == 1]

    school_type = student_info['school_type']
    adjustment_factor = SCHOOL_TYPE_ADJUSTMENT.get(school_type, 1.0)

    adjusted_score = max(student_info['score'] * adjustment_factor, 1.00)
    high_score_factor = student_info['high_score_factor']
    low_score_factor = student_info['low_score_factor']

    high_threshold = max(adjusted_score * high_score_factor, 1.00)
    low_threshold = min(adjusted_score * low_score_factor, 9.00)

    def get_entry_score(row):
        entry_score_70 = row['2024년_입결70%']
        entry_score_50 = row['2024년_입결50%']

        if pd.isna(entry_score_70) or entry_score_70 in [0, -9999]:
            if pd.isna(entry_score_50) or entry_score_50 in [0, -9999]:
                return None
            return entry_score_50
        return entry_score_70

    filtered_data['입결'] = filtered_data.apply(get_entry_score, axis=1)
    filtered_data = filtered_data.dropna(subset=['입결'])

    high_list = filtered_data[(filtered_data['입결'] >= high_threshold) & (filtered_data['입결'] < adjusted_score * 0.9)]
    mid_list = filtered_data[
        (filtered_data['입결'] >= adjusted_score * 0.9) & (filtered_data['입결'] < adjusted_score * 1.1)]
    low_list = filtered_data[(filtered_data['입결'] >= adjusted_score * 1.1) & (filtered_data['입결'] <= low_threshold)]

    # 수능최저역량 필터링 수정
    if 'lowest_ability_filter' in student_info and student_info['lowest_ability_filter']:
        high_list = high_list[high_list['2025년_수능최저코드'] <= student_info['lowest_ability_code']]
        mid_list = mid_list[mid_list['2025년_수능최저코드'] <= student_info['lowest_ability_code']]
        low_list = low_list[low_list['2025년_수능최저코드'] <= student_info['lowest_ability_code']]
    else:
        max_code = data['2025년_수능최저코드'].max()
        high_list = high_list[high_list['2025년_수능최저코드'] <= max_code]
        mid_list = mid_list[mid_list['2025년_수능최저코드'] <= max_code]
        low_list = low_list[low_list['2025년_수능최저코드'] <= max_code]

    return high_list, mid_list, low_list


def filter_data_comprehensive(student_info, data):
    filtered_data = data[data['계열'].isin(student_info['field'])]
    filtered_data = filtered_data[filtered_data['전형구분'] == '종합']

    if student_info['gender'] == '남자':
        filtered_data = filtered_data[~filtered_data['대학명'].str.contains('여자')]

    if student_info['school_type'] == '과학고':
        filtered_data = filtered_data[filtered_data['과학고'] == 1]
    elif student_info['school_type'] == '전사고':
        filtered_data = filtered_data[filtered_data['전사고'] == 1]
    elif student_info['school_type'] == '외고':
        filtered_data = filtered_data[filtered_data['외고'] == 1]

    school_type = student_info['school_type']
    adjustment_factor = SCHOOL_TYPE_ADJUSTMENT.get(school_type, 1.0)

    adjusted_score = max(student_info['score'] * adjustment_factor, 1.00)
    high_score_factor = student_info['high_score_factor']
    low_score_factor = student_info['low_score_factor']

    high_threshold = max(adjusted_score * high_score_factor, 1.00)
    low_threshold = min(adjusted_score * low_score_factor, 9.00)

    def get_entry_score(row):
        entry_score_70 = row['2024년_입결70%']
        entry_score_50 = row['2024년_입결50%']

        if pd.isna(entry_score_70) or entry_score_70 in [0, -9999]:
            if pd.isna(entry_score_50) or entry_score_50 in [0, -9999]:
                return None
            return entry_score_50
        return entry_score_70

    filtered_data['입결'] = filtered_data.apply(get_entry_score, axis=1)
    filtered_data = filtered_data.dropna(subset=['입결'])

    high_list = filtered_data[(filtered_data['입결'] >= high_threshold) & (filtered_data['입결'] < adjusted_score * 0.9)]
    mid_list = filtered_data[
        (filtered_data['입결'] >= adjusted_score * 0.9) & (filtered_data['입결'] < adjusted_score * 1.1)]
    low_list = filtered_data[(filtered_data['입결'] >= adjusted_score * 1.1) & (filtered_data['입결'] <= low_threshold)]

    # 수능최저역량 필터링 수정
    if 'lowest_ability_filter' in student_info and student_info['lowest_ability_filter']:
        high_list = high_list[high_list['2025년_수능최저코드'] <= student_info['lowest_ability_code']]
        mid_list = mid_list[mid_list['2025년_수능최저코드'] <= student_info['lowest_ability_code']]
        low_list = low_list[low_list['2025년_수능최저코드'] <= student_info['lowest_ability_code']]
    else:
        max_code = data['2025년_수능최저코드'].max()
        high_list = high_list[high_list['2025년_수능최저코드'] <= max_code]
        mid_list = mid_list[mid_list['2025년_수능최저코드'] <= max_code]
        low_list = low_list[low_list['2025년_수능최저코드'] <= max_code]

    return high_list, mid_list, low_list


