import pandas as pd

def get_university_list(score, university_ranges):
    result = []
    for range_str, universities in university_ranges.items():
        lower, upper = map(float, range_str.split('-'))
        if lower <= score <= upper:
            result.extend(universities)
    return result

def get_university_info(university_list, data):
    pattern = '|'.join([f'^{uni}$' for uni in university_list])
    university_info = data[data['대학명'].str.contains(pattern, regex=True)]
    return university_info

def preprocess_data(df):
    numeric_cols = ['2024년_경쟁률', '2023년_경쟁률', '2022년_경쟁률', '2024년_입결70%', '2024년_입결70%차이(%)', '2024년_입결50%차이(%)']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def find_related_majors(keywords, major_data):
    related_majors = set()
    for keyword in keywords:
        for main_category, subcategories in major_data.items():
            for subcategory, majors in subcategories.items():
                if any(keyword in major for major in majors):
                    related_majors.update(majors)
    return list(related_majors)

def convert_boolean_to_yes_no(criteria, key):
    if key in criteria and isinstance(criteria[key], bool):
        criteria[key] = "YES" if criteria[key] else "NO"

def set_default_criteria(criteria):
    default_values = {
        '2024년_입결50%차이(%)': 0,
        '2024년_입결70%차이(%)': 0,
        '2024년_경쟁률상승여부': 'NO',
        '2024년_입결70%하락여부': 'NO',
        '신설': 'NO'
    }
    for key, value in default_values.items():
        if key not in criteria:
            criteria[key] = value

def filter_top_n(df, sort_column, ascending=True):
    return df.sort_values(by=sort_column, ascending=ascending).head(10)
