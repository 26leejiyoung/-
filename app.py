#인디사
#터미널 환경 설정 pip install streamlit pandas openpyxl
#스트림릿 실행 streamlit run app.py
import streamlit as st
import pandas as pd
import os

# 1. 페이지 기본 설정 및 디자인
st.set_page_config(page_title="한국 관광 통계 대시보드", layout="wide", page_icon="📊")

st.title("📊 한국관광공사 연도별 관광 통계 대시보드")
st.markdown("방한 외래객, 해외관광객, 관광수지 등을 시각화하는 웹앱입니다.")

# 2. 알려주신 파일의 절대 경로 설정
EXCEL_PATH = "/workspaces/codespaces-blank/.venv/한국관광공사_관광_연도별_통계.xlsx"

# 3. 엑셀 안의 5개 시트 이름 매핑
SHEET_MAP = {
    "방한 외래관광객": "방한 외래관광객",
    "국민 해외관광객": "국민 해외관광객",
    "관광수입": "관광수입",
    "관광지출": "관광지출",
    "관광수지": "관광수지"
}

# 사이드바에서 조회하고 싶은 데이터 선택
st.sidebar.header("📁 데이터 분석 설정")
selected_sheet = st.sidebar.selectbox("조회할 통계 시트 선택", list(SHEET_MAP.keys()))


# 4. 데이터 로드 및 텍스트/공백 정제 함수
@st.cache_data
def load_and_clean_data(file_path, sheet_name):
    if not os.path.exists(file_path):
        return None

    # 헤더(연도 행)의 정확한 위치를 찾기 위해 우선 전체 행을 읽음
    df_raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

    header_idx = 0
    for idx, row in df_raw.iterrows():
        # [수정 포인트] 리스트 컴프리헨션을 사용하여 빈 칸(NaN)을 포함한 모든 요소를 강제로 str로 변환합니다.
        row_str = "".join([str(val) for val in row])
        if '연도' in row_str or '연  도' in row_str or 'Year' in row_str:
            header_idx = idx
            break

    # 발견한 헤더 위치를 기준으로 데이터 다시 읽기
    df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=header_idx)

    # 컬럼명의 줄바꿈(\n) 및 불필요한 앞뒤 공백 제거
    df.columns = [str(col).strip().replace('\n', ' ') for col in df.columns]

    # 첫 번째 데이터 행이 영문 서브 레이블(Year, Total 등)인 경우 데이터셋에서 제외
    if len(df) > 0:
        first_val = str(df.iloc[0, 0]).strip()
        if first_val == 'Year' or 'Total' in str(df.iloc[0, 1]):
            df = df.drop(df.index[0])

    # 첫 번째 컬럼명을 '연도'로 일치시킴
    df.rename(columns={df.columns[0]: '연도'}, inplace=True)

    # '계' 또는 'Total'이 들어간 컬럼명을 '계'로 통일
    for col in df.columns:
        if '계' in col or 'Total' in col:
            df.rename(columns={col: '계'}, inplace=True)
            break

    # '성장률' 또는 'Change'가 들어간 컬럼명을 '성장률'로 통일
    for col in df.columns:
        if '성장률' in col or 'Change' in col:
            df.rename(columns={col: '성장률'}, inplace=True)
            break

    # 각 월별 컬럼명 표준화
    month_mapping = {}
    for col in df.columns:
        for m in range(1, 13):
            if f"{m}월" in col or f"{m} 월" in col:
                month_mapping[col] = f"{m}월"
    df.rename(columns=month_mapping, inplace=True)

    # 연도 열을 숫자로 바꾸고 빈 값(결측치) 행 제거
    df['연도'] = pd.to_numeric(df['연도'], errors='coerce')
    df = df.dropna(subset=['연도'])
    df['연도'] = df['연도'].astype(int)

    # 연도를 제외한 나머지 수치 데이터 컬럼들의 쉼표(,) 제거 및 숫자 데이터 처리
    for col in df.columns:
        if col != '연도':
            df[col] = df[col].astype(str).str.replace(',', '').str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


# 5. 메인 화면 시각화 로직
if os.path.exists(EXCEL_PATH):
    df = load_and_clean_data(EXCEL_PATH, SHEET_MAP[selected_sheet])

    if df is not None and not df.empty:
        # 사이드바 연도 범위 조절 슬라이더
        min_year = int(df['연도'].min())
        max_year = int(df['연도'].max())
        year_range = st.sidebar.slider("분석 연도 범위 선택", min_year, max_year, (min_year, max_year))

        # 선택한 연도 범위 데이터만 필터링
        filtered_df = df[(df['연도'] >= year_range[0]) & (df['연도'] <= year_range[1])].sort_values('연도')

        # 통계 항목에 따른 화폐/인원 단위 구분 설정
        if "수입" in selected_sheet or "지출" in selected_sheet or "수지" in selected_sheet:
            unit = "US$ 1,000"
        else:
            unit = "명"

        # [지표 요약] 선택 범위 중 최종 연도 기준 핵심 데이터 표시
        st.subheader(f"📌 {year_range[1]}년 주요 통계 지표 요약")
        latest_data = filtered_df[filtered_df['연도'] == year_range[1]]

        if not latest_data.empty:
            m_col1, m_col2 = st.columns(2)
            with m_col1:
                if '계' in latest_data.columns:
                    st.metric(label=f"{year_range[1]}년 연간 총합", value=f"{int(latest_data['계'].values[0]):,} {unit}")
            with m_col2:
                if '성장률' in latest_data.columns and not pd.isna(latest_data['성장률'].values[0]):
                    st.metric(label="전년 대비 성장률", value=f"{latest_data['성장률'].values[0]:.2f} %")

        # [시각화 1] 연도별 총합 변동 추이 선 그래프
        st.markdown("---")
        st.subheader(f"📈 {selected_sheet} 연도별 추이 선 그래프 ({year_range[0]}년 ~ {year_range[1]}년)")
        st.caption(f"단위: {unit}")
        if '계' in filtered_df.columns:
            chart_data = filtered_df[['연도', '계']].set_index('연도')
            st.line_chart(chart_data)

        # [시각화 2] 특정 연도 선택 시 1월~12월 월별 상세 분석 막대 그래프
        st.markdown("---")
        st.subheader("🗓️ 월별 세부 분석 막대 그래프")
        select_years = sorted(filtered_df['연도'].unique(), reverse=True)
        chosen_year = st.selectbox("상세히 확인해볼 연도를 선택하세요", select_years)

        year_specific_data = filtered_df[filtered_df['연도'] == chosen_year]
        months_list = [f"{m}월" for m in range(1, 13)]
        available_months = [m for m in months_list if m in year_specific_data.columns]

        if available_months and not year_specific_data.empty:
            monthly_series = year_specific_data[available_months].iloc[0]
            st.bar_chart(monthly_series)
        else:
            st.info("해당 연도의 월별 데이터 세부가 정리되지 않았거나 데이터가 비어있습니다.")

        # [시각화 3] 필터링된 가공 데이터 원본 표 출력
        st.markdown("---")
        st.subheader("📋 선택된 조건의 데이터 원본 표")
        st.dataframe(filtered_df, use_container_width=True)

    else:
        st.error("❌ 데이터를 로드하는 과정에서 오류가 발생했거나 시트가 비어있습니다.")
else:
    st.error("❌ 지정된 경로에서 엑셀 파일을 찾을 수 없습니다.")
    st.warning(f"예상 경로: {EXCEL_PATH}")
    st.info("파일 이름이 정확한지 혹은 `.venv` 폴더 내에 실물 파일이 올바르게 위치해 있는지 재확인해주세요.")