import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from openai import OpenAI
import os
from dotenv import load_dotenv
import matplotlib.font_manager as fm

load_dotenv()
api_key = os.getenv('API_KEY')
client = OpenAI(api_key=api_key)

# 한글 폰트 설정
font_path = '/Users/isaac/Library/Fonts/maruburi/MaruBuri-Regular.otf'
font_prop = fm.FontProperties(fname=font_path)
fm.fontManager.addfont(font_path)
plt.rcParams['font.family'] = font_prop.get_name()
plt.rcParams['font.size'] = 12
plt.rcParams['axes.unicode_minus'] = False


def generate_report(high_info, mid_info, low_info, student_info, all_data):
    report = ""

    # 기본 정보
    report += "### 기본 정보 🏫\n\n"
    report += f"""
| 학교명 | 학교유형 | 희망계열 | 희망전공 | 내신점수 |
|--------|----------|----------|----------|----------|
|        | {student_info['school_type']} |          | {student_info['desired_major']} | {student_info['gpa']} |

"""

    # 지원 가능선
    report += "### 지원 가능선 🎯\n\n"
    report += "| | 학생부 종합 | 교과 | 논술 |\n"
    report += "|------|-------------|------|------|\n"

    for level, df in [('상향', high_info), ('적정', mid_info), ('안정', low_info)]:
        report += f"| {level} | "
        for category in ['종합', '교과', '논술']:
            filtered_df = df[df['전형구분'] == category]
            if not filtered_df.empty:
                unis = [f"{row['대학명']} {row['전공']}" for _, row in filtered_df.iterrows()]
                report += ", ".join(unis[:10])  # 최대 10개까지만 표시
            report += " | "
        report += "\n"

    # 종합 의견 (GPT로 작성)
    gpt_prompt = f"""
    다음 정보를 바탕으로 대학 지원에 대한 종합적인 의견을 제시해주세요. (가이드라인은 일절 출력에 언급하지 말 것)
    - 학생의 정보(학교 유형, 희망전공, 내신점수)를 고려하고, 필터 정보를 기반으로 지원가능선에 대해 종합적인 의견을 제시
    - 2개~3개의 문단 형태로 가독성 있게 기술할 것
    - 현재 시점은 2025학년도 입시를 준비하는 상황임을 고려할 것

    학생 정보:
    - 학교 유형: {student_info['school_type']}
    - 희망전공: {student_info['desired_major']}
    - 내신점수: {student_info['gpa']}

    필터 정보:
    {student_info['filter_info']}
    """

    gpt_response = generate_gpt_response(gpt_prompt)
    report += f"### 종합 의견 📝\n\n{gpt_response}\n\n"
    report += "---\n\n"

    # 상향 지원 BEST 3
    report += "#### 상향 지원 BEST 3 🌟\n\n"
    report += """
경쟁률과 입결은 해마다 변동성이 큰 지표이며 상승과 하락을 반복하는 경향이 있지만, 장기적으로 볼 때 각 학과별로 어느 정도 일정한 추세를 보입니다. 반면 충원율의 경우에는 학과마다 비교적 안정적인 경향성을 나타내고 있습니다.

상향 지원은 통상 적정이나 안정 지원에 비해 합격 가능성이 다소 낮습니다. 그러나 철저한 분석을 바탕으로 전략적으로 접근한다면 상향 지원 역시 충분히 의미 있는 도전이 될 수 있습니다. 상향 지원을 고려하실 때에는 단순히 경쟁률이나 경쟁률 추이만 보는 것이 아니라, 경쟁 강도, 입결 상승율, 충원 강도 등 다양한 요소를 종합적으로 고려하시는 것이 중요합니다.

지략에서는 이러한 데이터를 바탕으로 상향 지원 대상 학과를 선정하여 추천 리스트를 제공해 드리고 있습니다. 적정이나 안정 지원만큼이나 상향 지원도 여러분께는 소중한 기회가 될 수 있습니다. 아래는 경쟁률, 입결, 충원율에 기반한 상향지원 BEST 3입니다.
"""

    # GPT로 상향지원전략 작성
    gpt_strategy_prompt = f"""
    아래 상향 지원 대상 대학 정보를 바탕으로 상향지원전략을 작성해주세요: 
    - 상향지원 리스트에서 상위 3개에 대해서만 기술, 되도록 대학명, 전형구분, 전공이 중복되지 않아야 함
      예시 )
    - MUST : 현재 상향지원 정보가 없을 경우 "상향지원 정보가 없는 상태입니다."라고만 출력할 것. 
    - 상향지원 정보가 있는 경우 출력 예시) 
      1. 한양대의 신소재공학과 교과전형의 경우 2024학년도 경쟁률이 ~로 전년대비 % 상승, 70% 입결은 ~로 전년 대비 % 하락(성적 상승)이 있었습니다. 작년 충원률은 ~%이며 3개년 충원률은 ~%이므로 상향지원 카드로 적절해 보입니다.
      2. 
      3. 

    상향 지원 대상 대학 정보:
    {high_info.head(3).to_dict('records')}
    """

    gpt_strategy_response = generate_gpt_response(gpt_strategy_prompt)
    report += f"\n{gpt_strategy_response}\n\n"
    report += "---\n\n"

    report += "각 상향지원 안에 대해 자세히 설명드리겠습니다.\n\n"

    for i, (_, row) in enumerate(high_info.head(3).iterrows(), 1):
        report += f"### {i}. {row['대학명']} {row['전공']} {row['전형구분']}\n\n"

        # 경쟁률 분석
        report += "##### 경쟁률 분석\n\n"
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20, 5))

        # 3개년 경쟁률
        years = ['2022년', '2023년', '2024년']
        competition_rates = [row['2022년_경쟁률'], row['2023년_경쟁률'], row['2024년_경쟁률']]
        sns.lineplot(x=years, y=competition_rates, ax=ax1, marker='o')
        ax1.set_title('3개년 경쟁률', fontproperties=font_prop, fontsize=16)
        ax1.set_ylabel('경쟁률', fontproperties=font_prop)

        # 전형구분별 전체 전공 경쟁 강도
        university_data = all_data[(all_data['대학명'] == row['대학명']) & (all_data['전형구분'] == row['전형구분'])]
        sns.boxplot(x='2024년_경쟁강도', data=university_data, ax=ax2)
        ax2.axvline(x=row['2024년_경쟁강도'], color='red', linestyle='--')
        ax2.set_title('전형구분별 전체 전공 경쟁 강도', fontproperties=font_prop, fontsize=16)
        ax2.set_xlabel('2024년 경쟁강도', fontproperties=font_prop)

        # 전공별 경쟁률 변화율
        sns.barplot(x='2024년_경쟁률상승정도(%)', y='전공', data=university_data, ax=ax3)
        ax3.axvline(x=row['2024년_경쟁률상승정도(%)'], color='red', linestyle='--')
        ax3.set_title('전공별 경쟁률 변화율', fontproperties=font_prop, fontsize=16)
        ax3.set_xlabel('2024년 경쟁률 상승정도(%)', fontproperties=font_prop)
        ax3.set_ylabel('')
        ax3.set_yticklabels([])  # 전공명 제거

        plt.tight_layout()
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()

        report += f"![Competition Rate Graphs](data:image/png;base64,{image_base64})\n\n"

        report += f"- 2024학년도 경쟁률 : {row['2024년_경쟁률']}\n"
        report += f"- 2024학년도 경쟁률 상승 정도(%) : {row['2024년_경쟁률상승정도(%)']}\n"
        report += f"- 2024학년도 경쟁 강도 : {row['2024년_경쟁강도']}\n"
        report += f"- 3개년 평균 경쟁률 : {row['3개년_경쟁률_평균']}\n\n"

        # 입결 분석
        report += "##### 입결 분석\n\n"
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20, 5))

        # 3개년 입결 70%
        entrance_scores_70 = [row['2022년_입결70%'], row['2023년_입결70%'], row['2024년_입결70%']]
        sns.lineplot(x=years, y=entrance_scores_70, ax=ax1)
        ax1.set_title('3개년 입결 70%', fontproperties=font_prop, fontsize=16)
        ax1.set_ylabel('입결 70%', fontproperties=font_prop)

        # 2024학년도 입결 70%와 평균 비교
        avg_70 = university_data['2024년_입결70%'].mean()
        sns.scatterplot(x=['2024년 입결 70%', '2024년 평균 입결 70%'], y=[row['2024년_입결70%'], avg_70], ax=ax2)
        ax2.set_title('2024학년도 입결 70% 비교', fontproperties=font_prop, fontsize=16)
        ax2.set_xlabel('')
        ax2.set_ylabel('')

        # 전공별 입결 70% 변화율
        sns.barplot(x='2024년_입결70%차이(%)', y='전공', data=university_data, ax=ax3)
        ax3.axvline(x=row['2024년_입결70%차이(%)'], color='red', linestyle='--')
        ax3.set_title('전공별 입결 70% 변화율', fontproperties=font_prop, fontsize=16)
        ax3.set_xlabel('2024년 입결 70% 차이(%)', fontproperties=font_prop)
        ax3.set_ylabel('')
        ax3.set_yticklabels([])  # 전공명 제거

        plt.tight_layout()
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()

        report += f"![Entrance Score Graphs](data:image/png;base64,{image_base64})\n\n"

        report += f"- 2024학년도 50% 입결 : {row['2024년_입결50%']}\n"
        report += f"- 2024학년도 70% 입결 : {row['2024년_입결70%']}\n"
        report += f"- 전년대비 2024학년도 50% 입결 변화율 : {row['2024년_입결50%차이(%)']}\n"
        report += f"- 전년대비 2024학년도 70% 입결 변화율 : {row['2024년_입결70%차이(%)']}\n"
        report += f"- 3개년 평균 50% 입결 : {row['3개년_평균_입결50%']}\n"
        report += f"- 3개년 평균 70% 입결 : {row['3개년_평균_입결70%']}\n\n"

        # 추가합격 분석
        report += "##### 추가합격 분석\n\n"
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20, 5))

        # 3개년 충원율
        fill_rates = [row['2022년_충원률(%)'], row['2023년_충원률(%)'], row['2024년_충원률(%)']]
        sns.barplot(x=years, y=fill_rates, ax=ax1)
        ax1.set_title('3개년 충원율', fontproperties=font_prop, fontsize=16)
        ax1.set_ylabel('충원율 (%)', fontproperties=font_prop)

        # 전형구분별 전체 전공 충원 강도
        sns.scatterplot(x='2024년_충원강도', y='전공', data=university_data, ax=ax2)
        ax2.axvline(x=row['2024년_충원강도'], color='red', linestyle='--')
        ax2.set_title('전형구분별 전체 전공 충원 강도', fontproperties=font_prop, fontsize=16)
        ax2.set_xlabel('2024년 충원강도', fontproperties=font_prop)
        ax2.set_ylabel('')
        ax2.set_yticklabels([])  # 전공명 제거

        # 전공별 충원율 변화율
        sns.barplot(x='2024년_충원률변화(%)', y='전공', data=university_data, ax=ax3)
        ax3.axvline(x=row['2024년_충원률변화(%)'], color='red', linestyle='--')
        ax3.set_title('전공별 충원율 변화율', fontproperties=font_prop, fontsize=16)
        ax3.set_xlabel('2024년 충원율 변화(%)', fontproperties=font_prop)
        ax3.set_ylabel('')
        ax3.set_yticklabels([])  # 전공명 제거

        plt.tight_layout()
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()

        report += f"![Fill Rate Graphs](data:image/png;base64,{image_base64})\n\n"

        report += f"- 2024학년도 추가합격자 수 : {row['2024년_추가합격자수']}\n"
        report += f"- 2024학년도 충원율 : {row['2024년_충원률(%)']}\n"
        report += f"- 2024학년도 충원 강도 : {row['2024년_충원강도']}\n"
        report += f"- 전년대비 2024학년도 충원율 변화율 : {row['2024년_충원률변화(%)']}\n"
        report += f"- 3개년 평균 충원율 : {row['3개년_평균_충원률']}\n\n"

        report += "\n\n"

    # 지원 가능안 상세
    report += "---\n\n"
    report += "### 지원 가능안 상세 📋\n\n"
    for level, df in [('상향', high_info), ('적정', mid_info), ('안정', low_info)]:
        report += f"#### {level} 지원\n"  # 줄바꿈 제거

        fig, ax = plt.subplots(figsize=(30, len(df) * 1.2))
        ax.axis('off')
        table = ax.table(cellText=df[['대학명', '전형구분', '전형명', '전공', '2025년_모집인원', '수능_최저요건',
                                      '2024년_경쟁률', '2023년_경쟁률', '2024년_입결70%', '2024년_추가합격자수',
                                      '2025_주요_변경사항', '대학별_고사_일정']].values,
                         colLabels=['대학교', '전형유형', '전형명', '전공', '모집인원', '최저학력기준',
                                    '2024학년도\n경쟁률', '2023학년도\n경쟁률', '2024학년도\n70% 입결',
                                    '2024학년도\n충원', '지원시\n유의사항', '대학별\n고사 실시일'],
                         loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(14)
        table.scale(1, 2.2)

        for (row, col), cell in table.get_celld().items():
            if row == 0:
                cell.set_text_props(weight='bold', color='white')
                cell.set_facecolor('#4472C4')
            else:
                cell.set_facecolor('#E9EFF7' if row % 2 == 0 else 'white')
            cell.set_edgecolor('white')
            cell.set_text_props(wrap=True)

        plt.tight_layout()

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()

        report += f"![{level} 지원 가능안](data:image/png;base64,{image_base64})\n"  # 줄바꿈 제거

    return report

def generate_gpt_response(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system",
             "content": "You are a helpful assistant that generates reports based on university admission data."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000
    )
    return response.choices[0].message.content.strip()
