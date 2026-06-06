#터미널환경설정 pip install streamlit pandas plotly openpyxl
#스트림릿 실행 streamlit run app2.py
import streamlit as st
import pandas as pd
import plotly.express as px


# -------------------------------------------------------------------
# [1] 웹 페이지 기본 설정 및 디자인
# -------------------------------------------------------------------
st.set_page_config(
    page_title="국내 여행 일정 추천 서비스",
    layout="wide",
    initial_sidebar_state="expanded"
)


# -------------------------------------------------------------------
# [2] 데이터 로드 (캐싱 처리)
# -------------------------------------------------------------------
@st.cache_data
def load_data():
    
    file_path = r"/workspaces/codespaces-blank/.venv/tourism_weather_merged.xlsx"
    df = pd.read_excel('tourism_weather_merged.xlsx')

    # [안전장치] 엑셀의 '월' 컬럼이 문자열('1월')이거나 소수점(1.0)일 경우를 대비해 숫자로 강제 정제
    if '월' in df.columns:
        if df['월'].dtype == object:
            df['월'] = df['월'].str.replace('월', '', errors='ignore')
        df['월'] = pd.to_numeric(df['월'], errors='coerce').fillna(0).astype(int)

    return df


try:
    df_raw = load_data()
except Exception as e:
    st.error(f"데이터 파일을 불러오지 못했습니다. 경로를 확인해주세요. 에러 내용: {e}")
    st.stop()

# -------------------------------------------------------------------
# [3] 사이드바 설정: 사용자 입력 (여행 예정 월 선택)
# -------------------------------------------------------------------
st.sidebar.header("✈️ 국내 여행 일정 계획")
selected_month = st.sidebar.selectbox(
    "여행을 떠나실 예정 월을 선택하세요:",
    options=list(range(1, 13)),
    format_func=lambda x: f"{x}월"
)

st.sidebar.markdown("---")
st.sidebar.caption("💡 본 서비스는 과거의 기상 및 관광객 데이터를 융합 분석하여 최적의 여행 시기를 추천하는 인공지능·디지털 사고 프로젝트 결과물입니다.")

# -------------------------------------------------------------------
# [4] 메인 화면: 제목 및 서비스 소개
# -------------------------------------------------------------------
st.title("🗺️ 과거 관광·기상 데이터를 활용한 국내 여행 일정 추천 서비스")
st.markdown("### 🏫 인공지능과 디지털 사고 프로젝트")
st.markdown(
    f"과거의 데이터 분석을 통해 **{selected_month}월**의 여행 환경을 평가하고, "
    "기상 쾌적성과 밀집도를 종합하여 **여행 적합도 점수**를 제공합니다."
)
st.markdown("---")

# -------------------------------------------------------------------
# [5] 로직 처리: 해당 월의 기상 및 관광객 평균 데이터 추출 & 점수 계산
# -------------------------------------------------------------------
# 전체 월별 평균 계산 (기준점 마련용)
df_month_avg = df_raw.groupby('월').mean(numeric_only=True)

# [안전장치] 혹시나 데이터에 해당 월의 데이터가 없을 경우 예외처리
if selected_month not in df_month_avg.index:
    st.error(f"데이터셋에 {selected_month}월에 해당하는 데이터가 존재하지 않습니다. 엑셀 데이터를 확인해 주세요.")
    st.stop()

# 선택된 월의 구체 데이터
target_data = df_month_avg.loc[selected_month]
avg_tourists = int(target_data.get('관광객수', 0))
avg_temp = target_data.get('평균기온', 0)
avg_rain = target_data.get('강수량', 0)
avg_hum = target_data.get('평균상대습도', 0)
avg_sun = target_data.get('일조시간', 0)

# 1. 혼잡도 분석 (관광객 수 분위수 기준)
q25 = df_month_avg['관광객수'].quantile(0.25)
q50 = df_month_avg['관광객수'].quantile(0.50)
q75 = df_month_avg['관광객수'].quantile(0.75)

if avg_tourists >= q75:
    congestion = "매우 혼잡"
    congestion_color = "red"
elif avg_tourists >= q50:
    congestion = "혼잡"
    congestion_color = "orange"
elif avg_tourists >= q25:
    congestion = "보통"
    congestion_color = "green"
else:
    congestion = "여유"
    congestion_color = "blue"

# 2. 여행 적합도 점수 알고리즘 (100점 만점 자체 설계)
score_temp = max(0, 30 - abs(avg_temp - 18) * 1.5)
score_rain = max(0, 25 - (avg_rain / 15))
score_hum = max(0, 20 - abs(avg_hum - 55) * 0.5)

max_t = df_month_avg['관광객수'].max()
min_t = df_month_avg['관광객수'].min()
# 분모가 0이 되는 것을 방지하기 위해 1e-5 더함
score_tourist = 25 * (1 - (avg_tourists - min_t) / (max_t - min_t + 1e-5))

total_score = int(score_temp + score_rain + score_hum + score_tourist)
total_score = min(100, max(0, total_score))  # 0~100점 제한

# 3. 추천 이유 자동 생성 규칙
reasons = []
if 15 <= avg_temp <= 23:
    reasons.append("기온이 선선하고 쾌적하여 야외 활동을 하기에 아주 좋은 시기입니다.")
elif avg_temp < 5:
    reasons.append("기온이 낮고 추운 편이므로 따뜻한 옷차림과 실내 여행 코스를 추천합니다.")
elif avg_temp > 25:
    reasons.append("기온이 높고 무더운 여름 기후이므로 시원한 실내 활동이나 물놀이를 추천합니다.")

if avg_rain < 60:
    reasons.append("평균 강수량이 적어 비로 인한 일정 차질 확률이 낮습니다.")
else:
    reasons.append("강수량이 다소 많은 편이므로 휴대용 우산과 실내 대피 동선을 준비하는 것이 좋습니다.")

if congestion in ["여유", "보통"]:
    reasons.append(f"관광객 밀집도가 '{congestion}' 수준으로 비교적 한적하고 여유로운 여행이 가능합니다.")
else:
    reasons.append(f"관광객이 많이 몰리는 '{congestion}' 시기이므로 주요 명소는 사전 예약이나 이른 오전 방문을 추천합니다.")

# -------------------------------------------------------------------
# [6] 최종 추천 결과 리포트 (시각적 대형 요약 창)
# -------------------------------------------------------------------
st.subheader(f"🔮 {selected_month}월 최종 여행 분석 결과")

res_col1, res_col2, res_col3 = st.columns([1, 1, 2])

with res_col1:
    st.metric(label="📊 여행 적합도 점수", value=f"{total_score}점 / 100점")
with res_col2:
    st.metric(label="👥 예상 관광객 수", value=f"{avg_tourists:,} 명")
with res_col3:
    st.markdown(f"#### 🚦 혼잡도: :{congestion_color}[**{congestion}**]")

# 추천 이유 출력 Box
st.info(f"**📢 {selected_month}월 종합 추천 이유:**\n\n" + "\n".join([f"- {r}" for r in reasons]))

st.markdown("---")

# -------------------------------------------------------------------
# [7] 해당 월 과거 기상 상세 정보 출력 (Metric 카드 구성)
# -------------------------------------------------------------------
st.subheader(f"🌦️ {selected_month}월의 과거 기상 정보 (평균 데이터)")
m_col1, m_col2, m_col3, m_col4 = st.columns(4)

with m_col1:
    st.metric(label="🌡️ 평균 기온", value=f"{avg_temp:.1f} °C")
with m_col2:
    st.metric(label="🌧️ 평균 강수량", value=f"{avg_rain:.1f} mm")
with m_col3:
    st.metric(label="💧 평균 습도", value=f"{avg_hum:.1f} %")
with m_col4:
    st.metric(label="☀️ 평균 일조시간", value=f"{avg_sun:.1f} 시간")

st.markdown("---")

# -------------------------------------------------------------------
# [8] 과거 관광 데이터 분석 그래프 (전체 추이 분석)
# -------------------------------------------------------------------
st.subheader("📊 데이터 기반 과거 관광 트렌드 종합 분석")

tab1, tab2, tab3 = st.tabs(["📈 연도별/월별 추이", "🏆 관광객 TOP 5 명소 달", "😷 코로나 전후 비교"])

with tab1:
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        df_year = df_raw.groupby('연도')['관광객수'].sum().reset_index()
        fig_year = px.line(df_year, x='연度' if '연度' in df_year.columns else '연도', y='관광객수', markers=True,
                           title="연도별 총 관광객 수 추이",
                           labels={'연도': '연도', '관광객수': '관광객 수'})
        st.plotly_chart(fig_year, use_container_width=True)
    with col_t2:
        fig_month = px.bar(df_month_avg.reset_index(), x='월', y='관광객수', color='관광객수', title="월별 평균 관광객 분포 (선택 월 비교용)",
                           color_continuous_scale="Cividis")
        fig_month.update_layout(xaxis=dict(dtick=1))
        st.plotly_chart(fig_month, use_container_width=True)

with tab2:
    st.markdown("#### 🥇 역사상 가장 많은 관광객이 방문했던 시기 TOP 5")
    df_top5 = df_raw.sort_values(by='관광객수', ascending=False).head(5).reset_index(drop=True)
    df_top5.index = df_top5.index + 1
    st.table(df_top5[['연도', '월', '관광객수', '평균기온', '강수량']].style.format({'관광객수': '{:,}'}))

with tab3:
    st.markdown("#### 😷 코로나19 발생 전후 관광객 수요 패턴 변화 분석")

    # [수정] 원본 보존 및 SettingWithCopyWarning 방지를 위해 .copy() 사용
    df_covid_target = df_raw.copy()
    df_covid_target['기간구분'] = df_covid_target['연도'].apply(
        lambda x: '코로나 전 (2018-2019)' if x in [2018, 2019] else ('코로나 시기 (2020-2021)' if x in [2020, 2021] else '기타 기간')
    )
    df_covid_analysis = df_covid_target[df_covid_target['기간구분'] != '기타 기간'].groupby(['기간구분', '월'])[
        '관광객수'].mean().reset_index()

    if not df_covid_analysis.empty:
        fig_covid = px.line(df_covid_analysis, x='월', y='관광객수', color='기간구분', markers=True,
                            title="코로나 전 vs 코로나 시기 월별 평균 관광객 변화")
        fig_covid.update_layout(xaxis=dict(dtick=1))
        st.plotly_chart(fig_covid, use_container_width=True)
    else:
        st.info("데이터프레임에 2018~2021년 데이터가 부족하여 패턴 비교 그래프를 생략합니다.")