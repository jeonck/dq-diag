import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from modules.completeness import CompletenessChecker
from modules.consistency import ConsistencyChecker
from modules.accuracy import AccuracyChecker
from modules.security import SecurityChecker
from modules.timeliness import TimelinessChecker
from modules.usability import UsabilityChecker
from modules.validity import ValidityChecker
from modules.accessibility import AccessibilityChecker
from modules.diversity import DiversityChecker
from modules.uniqueness import UniquenessChecker
from theoretical_framework import show_theoretical_framework

# 페이지 설정
st.set_page_config(
    page_title="데이터 품질 진단 툴",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 탭 생성: 이론 프레임워크 + 실제 진단 툴
tab1, tab2 = st.tabs(["📚 이론 프레임워크", "🔧 실제 데이터 진단 툴"])

with tab1:
    show_theoretical_framework()

with tab2:
    # 제목
    st.title("📊 데이터베이스 품질 진단 툴")
    st.markdown("---")

# 사이드바 (전역 - 모든 탭에서 공유)
with st.sidebar:
    st.header("⚙️ 설정")

    # 파일 업로드
    uploaded_file = st.file_uploader(
        "CSV 파일 업로드",
        type=['csv'],
        help="진단할 데이터베이스 CSV 파일을 업로드하세요"
    )

    st.markdown("---")

    # 진단 지표 선택
    st.header("📋 진단 지표 선택")

    check_completeness = st.checkbox("완전성 (Completeness)", value=True)
    check_validity = st.checkbox("유효성 (Validity)", value=True)
    check_consistency = st.checkbox("일관성 (Consistency)", value=True)
    check_accuracy = st.checkbox("정확성 (Accuracy)", value=True)
    check_security = st.checkbox("보안성 (Security)", value=False)
    check_usability = st.checkbox("유용성 (Usability)", value=False)
    check_accessibility = st.checkbox("접근성 (Accessibility)", value=False)
    check_timeliness = st.checkbox("적시성 (Timeliness)", value=False)
    check_diversity = st.checkbox("다양성 (Diversity)", value=False)
    check_uniqueness = st.checkbox("유일성 (Uniqueness)", value=True)

    st.markdown("---")

    # 샘플 데이터 로드
    if st.button("📂 샘플 데이터 사용"):
        st.session_state['use_sample'] = True

# 메인 영역
if uploaded_file is not None or st.session_state.get('use_sample', False):

    # 데이터 로드
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.success(f"✅ 파일 업로드 완료: {uploaded_file.name}")
    else:
        df = pd.read_csv('sample_data/sample_customer.csv')
        st.info("📂 샘플 데이터를 사용합니다.")

    # 데이터를 session state 에 저장
    st.session_state['df'] = df

    # 데이터 미리보기
    with st.expander("🔍 데이터 미리보기", expanded=False):
        # 인덱스를 1 부터 시작하도록 변경
        df_display = df.copy()
        df_display.index = df_display.index + 1
        st.dataframe(df_display, use_container_width=True, height=400)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("전체 레코드 수", f"{len(df):,}")
        with col2:
            st.metric("컬럼 수", len(df.columns))
        with col3:
            st.metric("메모리 사용량", f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB")
        with col4:
            null_count = df.isnull().sum().sum()
            st.metric("NULL 값 개수", f"{null_count:,}")

    st.markdown("---")

    # 진단 실행 버튼
    if st.button("🚀 진단 시작", type="primary"):

        results = {}

        # 진행 상태 표시
        progress_bar = st.progress(0)
        status_text = st.empty()

        total_checks = sum([
            check_completeness,
            check_validity,
            check_consistency,
            check_accuracy,
            check_security,
            check_usability,
            check_accessibility,
            check_timeliness,
            check_diversity,
            check_uniqueness
        ])

        current_check = 0

        # 완전성 진단
        if check_completeness:
            status_text.text("완전성 진단 중...")
            checker = CompletenessChecker(df)
            results['completeness'] = checker.check()
            current_check += 1
            progress_bar.progress(current_check / total_checks)

        # 유효성 진단
        if check_validity:
            status_text.text("유효성 진단 중...")
            checker = ValidityChecker(df)
            results['validity'] = checker.check()
            current_check += 1
            progress_bar.progress(current_check / total_checks)

        # 일관성 진단
        if check_consistency:
            status_text.text("일관성 진단 중...")
            checker = ConsistencyChecker(df)
            results['consistency'] = checker.check()
            current_check += 1
            progress_bar.progress(current_check / total_checks)

        # 정확성 진단
        if check_accuracy:
            status_text.text("정확성 진단 중...")
            checker = AccuracyChecker(df)
            results['accuracy'] = checker.check()
            current_check += 1
            progress_bar.progress(current_check / total_checks)

        # 보안성 진단
        if check_security:
            status_text.text("보안성 진단 중...")
            checker = SecurityChecker(df)
            results['security'] = checker.check()
            current_check += 1
            progress_bar.progress(current_check / total_checks)

        # 유용성 진단
        if check_usability:
            status_text.text("유용성 진단 중...")
            checker = UsabilityChecker(df)
            results['usability'] = checker.check()
            current_check += 1
            progress_bar.progress(current_check / total_checks)

        # 접근성 진단
        if check_accessibility:
            status_text.text("접근성 진단 중...")
            checker = AccessibilityChecker(df)
            results['accessibility'] = checker.check()
            current_check += 1
            progress_bar.progress(current_check / total_checks)

        # 적시성 진단
        if check_timeliness:
            status_text.text("적시성 진단 중...")
            checker = TimelinessChecker(df)
            results['timeliness'] = checker.check()
            current_check += 1
            progress_bar.progress(current_check / total_checks)

        # 다양성 진단
        if check_diversity:
            status_text.text("다양성 진단 중...")
            checker = DiversityChecker(df)
            results['diversity'] = checker.check()
            current_check += 1
            progress_bar.progress(current_check / total_checks)

        # 유일성 진단
        if check_uniqueness:
            status_text.text("유일성 진단 중...")
            checker = UniquenessChecker(df)
            results['uniqueness'] = checker.check()
            current_check += 1
            progress_bar.progress(current_check / total_checks)

        progress_bar.progress(1.0)
        status_text.text("✅ 진단 완료!")

        st.session_state['results'] = results

    # 진단 결과 표시
    if 'results' in st.session_state:
        st.markdown("---")
        st.header("📊 진단 결과")

        results = st.session_state['results']

        # 전체 품질 점수 계산
        total_score = 0
        total_weight = 0

        for key, result in results.items():
            if 'score' in result:
                total_score += result['score']
                total_weight += 1

        overall_score = total_score / total_weight if total_weight > 0 else 0

        # 전체 점수 표시
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.metric(
                "전체 데이터 품질 점수",
                f"{overall_score:.1f}점",
                help="100점 만점 기준"
            )

            # 품질 등급 표시
            if overall_score >= 90:
                grade = "🟢 우수"
                grade_color = "green"
            elif overall_score >= 70:
                grade = "🟡 양호"
                grade_color = "orange"
            elif overall_score >= 50:
                grade = "🟠 보통"
                grade_color = "orange"
            else:
                grade = "🔴 미흡"
                grade_color = "red"

            st.markdown(f"**품질 등급**: :{grade_color}[{grade}]")

        with col2:
            st.metric("진단 지표 수", len(results))

        with col3:
            st.metric("진단 일시", datetime.now().strftime("%Y-%m-%d %H:%M"))

        # 점수 차트
        st.markdown("### 📈 지표별 품질 점수")

        score_data = []
        for key, result in results.items():
            if 'score' in result:
                score_data.append({
                    '지표': result.get('name', key),
                    '점수': result['score']
                })

        if score_data:
            score_df = pd.DataFrame(score_data)

            fig = px.bar(
                score_df,
                x='지표',
                y='점수',
                color='점수',
                color_continuous_scale=['red', 'yellow', 'green'],
                range_color=[0, 100],
                text='점수'
            )

            fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
            fig.update_layout(
                yaxis_range=[0, 105],
                showlegend=False,
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)

        # 심각도별 이슈 요약 차트
        st.markdown("### ⚠️ 심각도별 이슈 현황")

        severity_data = []
        for key, result in results.items():
            if 'issues' in result and result['issues']:
                high_count = len([i for i in result['issues'] if '🔴' in i.get('severity', '')])
                medium_count = len([i for i in result['issues'] if '🟡' in i.get('severity', '')])
                low_count = len([i for i in result['issues'] if '🟢' in i.get('severity', '')])

                if high_count > 0:
                    severity_data.append({'지표': result.get('name', key), '심각도': '🔴 높음', '개수': high_count})
                if medium_count > 0:
                    severity_data.append({'지표': result.get('name', key), '심각도': '🟡 중간', '개수': medium_count})
                if low_count > 0:
                    severity_data.append({'지표': result.get('name', key), '심각도': '🟢 낮음', '개수': low_count})

        if severity_data:
            severity_df = pd.DataFrame(severity_data)

            fig = px.bar(
                severity_df,
                x='지표',
                y='개수',
                color='심각도',
                color_discrete_map={'🔴 높음': 'red', '🟡 중간': 'orange', '🟢 낮음': 'green'},
                barmode='stack',
                text='개수'
            )

            fig.update_traces(textposition='inside')
            fig.update_layout(height=400)

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("✅ 발견된 이슈가 없습니다!")

        # 상세 결과
        st.markdown("---")
        st.markdown("### 📋 상세 진단 결과")

        # 지표별 색상 매핑
        indicator_colors = {
            'completeness': '🔵',
            'validity': '🟣',
            'consistency': '🟠',
            'accuracy': '🟢',
            'security': '🔴',
            'usability': '🟡',
            'accessibility': '🔷',
            'timeliness': '⏰',
            'diversity': '🌈',
            'uniqueness': '💎'
        }

        for key, result in results.items():
            indicator_icon = indicator_colors.get(key, '📊')
            indicator_name = result.get('name', key)
            score = result.get('score', 0)
            
            # 점수에 따른 색상 표시
            if score >= 90:
                score_color = "green"
                score_icon = "✅"
            elif score >= 70:
                score_color = "orange"
                score_icon = "⚠️"
            elif score >= 50:
                score_color = "yellow"
                score_icon = "⚡"
            else:
                score_color = "red"
                score_icon = "❌"
            
            # 지표별 구분 카드
            st.markdown(f"### {indicator_icon} {indicator_name}")
            
            with st.container():
                # 점수 및 메트릭 표시
                metric_cols = st.columns([2, 1, 1, 1])
                with metric_cols[0]:
                    st.metric("품질 점수", f"{score:.1f}점")
                with metric_cols[1]:
                    st.metric("상태", f"{score_icon}")
                with metric_cols[2]:
                    if 'issues' in result:
                        st.metric("이슈 수", len(result['issues']))
                    else:
                        st.metric("이슈 수", 0)
                with metric_cols[3]:
                    if 'metrics' in result:
                        first_metric = list(result['metrics'].items())[0]
                        st.metric(first_metric[0], first_metric[1])
                
                st.markdown("---")
                
                # 이슈 상세 표시
                if 'issues' in result and result['issues']:
                    # 심각도별로 이슈 그룹화
                    high_issues = [i for i in result['issues'] if '🔴' in i.get('severity', '')]
                    medium_issues = [i for i in result['issues'] if '🟡' in i.get('severity', '')]
                    low_issues = [i for i in result['issues'] if '🟢' in i.get('severity', '')]

                    for i, issue in enumerate(result['issues'], 1):
                        # 심각도에 따른 색상 구분
                        if '🔴' in issue.get('severity', ''):
                            st.error(f"**{i}. {issue['title']}**")
                        elif '🟡' in issue.get('severity', ''):
                            st.warning(f"**{i}. {issue['title']}**")
                        else:
                            st.info(f"**{i}. {issue['title']}**")

                        st.markdown(f"- **심각도**: {issue.get('severity', 'N/A')}")
                        st.markdown(f"- **설명**: {issue.get('description', 'N/A')}")

                        if 'details' in issue:
                            with st.expander("📊 상세 정보"):
                                st.json(issue['details'])

                        st.markdown("---")
                else:
                    st.success("✅ 이슈가 발견되지 않았습니다.")
                
                # 상세 메트릭
                if 'metrics' in result:
                    st.markdown("**📊 상세 메트릭**")
                    metric_cols = st.columns(len(result['metrics']))
                    for i, (metric_name, metric_value) in enumerate(result['metrics'].items()):
                        with metric_cols[i]:
                            st.metric(metric_name, metric_value)
            
            # 구분선
            st.markdown("---")

        # 리포트 다운로드
        st.markdown("---")
        st.markdown("### 📥 리포트 다운로드")

        download_col1, download_col2 = st.columns(2)

        with download_col1:
            # 진단 결과 요약 CSV 다운로드
            if st.button("📊 진단 결과 요약 (CSV)", use_container_width=True):
                import io

                # CSV 형식으로 변환
                csv_buffer = io.StringIO()
                csv_buffer.write("지표,점수,이슈수,메트릭\n")

                for key, result in results.items():
                    indicator_name = result.get('name', key)
                    score = result.get('score', 0)
                    issue_count = len(result.get('issues', []))

                    # 메트릭 문자열로 변환
                    metrics_str = ""
                    if 'metrics' in result:
                        metrics_list = [f"{k}: {v}" for k, v in result['metrics'].items()]
                        metrics_str = "; ".join(metrics_list)

                    # CSV 라인 작성
                    csv_buffer.write(f'"{indicator_name}",{score},{issue_count},"{metrics_str}"\n')

                csv_data = csv_buffer.getvalue()

                st.download_button(
                    label="CSV 다운로드",
                    data=csv_data,
                    file_name=f"dq_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        with download_col2:
            # 원본 데이터 다운로드
            if st.button("📁 원본 데이터 (CSV)", use_container_width=True):
                import io

                # session state 에서 전체 데이터 가져오기
                full_df = st.session_state.get('df', df)

                csv_buffer = io.StringIO()
                full_df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                csv_data = csv_buffer.getvalue()

                st.download_button(
                    label="CSV 다운로드",
                    data=csv_data,
                    file_name=f"original_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        # 상세 이슈 리포트 다운로드
        if st.button("📋 상세 이슈 리포트 (CSV)", use_container_width=True):
            import io

            csv_buffer = io.StringIO()
            csv_buffer.write("지표,심각도,이슈제목,설명,상세정보\n")

            for key, result in results.items():
                indicator_name = result.get('name', key)

                if 'issues' in result and result['issues']:
                    for issue in result['issues']:
                        title = issue.get('title', '').replace('"', '""')
                        severity = issue.get('severity', '')
                        description = issue.get('description', '').replace('"', '""')

                        # 상세정보 JSON 문자열로
                        details_str = ""
                        if 'details' in issue:
                            import json
                            details_str = json.dumps(issue['details'], ensure_ascii=False).replace('"', '""')

                        csv_buffer.write(f'"{indicator_name}","{severity}","{title}","{description}","{details_str}"\n')

            csv_data = csv_buffer.getvalue()

            st.download_button(
                label="상세 이슈 리포트 다운로드",
                data=csv_data,
                file_name=f"dq_issues_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

else:
    # 시작 화면
    st.info("👈 왼쪽 사이드바에서 CSV 파일을 업로드하거나 샘플 데이터를 사용하세요.")

    st.markdown("## 📚 데이터 품질 진단 지표")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### 1️⃣ 완전성 (Completeness)
        - 논리모델 완전성
        - 식별자 존재 여부
        - 물리구조 일치성
        - 속성의미 명확성

        ### 2️⃣ 유효성 (Validity)
        - 데이터 형식 준수
        - 도메인 값 유효성
        - 참조 무결성
        - 논리적 관계 규칙

        ### 3️⃣ 일관성 (Consistency)
        - 속성명 일관성
        - 표준 준수 여부
        - 중복값 존재 여부
        - 연계값 정합성

        ### 4️⃣ 정확성 (Accuracy)
        - 입력값 유효성
        - 업무규칙 준수
        - 범위/형식 정확성
        - 참조관계 무결성
        - 계산식 정확성

        ### 5️⃣ 보안성 (Security)
        - 데이터 오너십
        - 접근 제한
        - DB 보호 정책
        """)

    with col2:
        st.markdown("""
        ### 6️⃣ 유용성 (Usability)
        - 충분한 데이터량
        - 접근 편의성
        - 활용도

        ### 7️⃣ 접근성 (Accessibility)
        - 데이터 접근 용이성
        - 검색 기능 제공
        - API/다운로드 지원
        - 문서화 completeness

        ### 8️⃣ 적시성 (Timeliness)
        - 응답 시간
        - 데이터 제공 시간
        - 최신값 반영

        ### 9️⃣ 다양성 (Diversity)
        - 데이터 분포 균형성
        - 카테고리 다양성
        - 샘플 대표성
        - 편향 지표

        ### 🔟 유일성 (Uniqueness)
        - 중복 레코드 수
        - 고유값 비율
        - 중복 발생 빈도
        """)

    st.markdown("---")
    st.markdown("### 🎯 사용 방법")
    st.markdown("""
    1. 왼쪽 사이드바에서 CSV 파일을 업로드하거나 샘플 데이터를 선택합니다.
    2. 진단할 품질 지표를 선택합니다.
    3. '진단 시작' 버튼을 클릭합니다.
    4. 진단 결과를 확인하고 필요시 리포트를 다운로드합니다.
    """)
