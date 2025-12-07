"""
적시성 진단 모듈
Timeliness Checker Module

데이터의 최신성, 갱신 주기 등을 진단합니다.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class TimelinessChecker:
    def __init__(self, df):
        self.df = df
        self.name = "적시성 (Timeliness)"

    def check(self):
        """적시성 진단 실행"""
        issues = []
        metrics = {}

        # 1. 최신값 검사
        freshness_issues = self._check_data_freshness()
        issues.extend(freshness_issues)

        # 2. 날짜 컬럼 갱신 주기 검사
        update_issues = self._check_update_frequency()
        issues.extend(update_issues)

        # 3. 미래 날짜 검사
        future_issues = self._check_future_dates()
        issues.extend(future_issues)

        # 메트릭 계산
        date_cols = self._get_date_columns()

        if date_cols:
            latest_date = None
            for col in date_cols:
                try:
                    dates = pd.to_datetime(self.df[col], errors='coerce')
                    max_date = dates.max()
                    if pd.notna(max_date):
                        if latest_date is None or max_date > latest_date:
                            latest_date = max_date
                except:
                    pass

            if latest_date:
                days_old = (pd.Timestamp.now() - latest_date).days
                metrics['최신 데이터'] = latest_date.strftime('%Y-%m-%d')
                metrics['경과 일수'] = f"{days_old}일"
            else:
                metrics['최신 데이터'] = 'N/A'
                metrics['경과 일수'] = 'N/A'
        else:
            metrics['최신 데이터'] = '날짜 컬럼 없음'
            metrics['경과 일수'] = 'N/A'

        metrics['날짜 컬럼 수'] = len(date_cols)

        # 점수 계산
        score = self._calculate_score(issues, metrics)

        return {
            'name': self.name,
            'score': score,
            'issues': issues,
            'metrics': metrics
        }

    def _get_date_columns(self):
        """날짜 컬럼 추출"""
        date_cols = []

        for col in self.df.columns:
            # 컬럼명으로 날짜 컬럼 추정
            if any(keyword in col.lower() for keyword in ['date', 'dt', '일자', '날짜', '시간', 'time', '등록', '수정', '생성', 'created', 'updated', 'modified']):
                date_cols.append(col)
            # datetime 타입인 경우
            elif pd.api.types.is_datetime64_any_dtype(self.df[col]):
                date_cols.append(col)

        return date_cols

    def _check_data_freshness(self):
        """데이터 최신성 검사"""
        issues = []

        date_cols = self._get_date_columns()

        for col in date_cols:
            try:
                dates = pd.to_datetime(self.df[col], errors='coerce')
                valid_dates = dates.dropna()

                if len(valid_dates) > 0:
                    max_date = valid_dates.max()
                    days_old = (pd.Timestamp.now() - max_date).days

                    # 수정/갱신 날짜인 경우
                    if any(keyword in col.lower() for keyword in ['수정', '갱신', 'updated', 'modified']):
                        if days_old > 180:  # 6개월
                            severity = '🔴 높음'
                            description = f'최근 수정일이 {days_old}일 전입니다. 데이터가 장기간 갱신되지 않았습니다.'
                        elif days_old > 90:  # 3개월
                            severity = '🟡 중간'
                            description = f'최근 수정일이 {days_old}일 전입니다. 데이터 갱신이 필요할 수 있습니다.'
                        else:
                            continue

                        issues.append({
                            'title': f'컬럼 "{col}"의 데이터 최신성 부족',
                            'severity': severity,
                            'description': description,
                            'details': {
                                'column': col,
                                'latest_date': max_date.strftime('%Y-%m-%d'),
                                'days_old': days_old
                            }
                        })

            except:
                pass

        return issues

    def _check_update_frequency(self):
        """갱신 주기 검사"""
        issues = []

        date_cols = self._get_date_columns()

        for col in date_cols:
            try:
                dates = pd.to_datetime(self.df[col], errors='coerce')
                valid_dates = dates.dropna().sort_values()

                if len(valid_dates) > 1:
                    # 날짜 간격 계산
                    date_diffs = valid_dates.diff().dt.days.dropna()

                    if len(date_diffs) > 0:
                        avg_interval = date_diffs.mean()
                        std_interval = date_diffs.std()

                        # 간격이 불규칙한 경우 (표준편차가 평균의 50% 이상)
                        if std_interval > avg_interval * 0.5:
                            issues.append({
                                'title': f'컬럼 "{col}"의 갱신 주기 불규칙',
                                'severity': '🟡 중간',
                                'description': f'데이터 갱신 주기가 불규칙합니다. 평균 {avg_interval:.1f}일, 표준편차 {std_interval:.1f}일',
                                'details': {
                                    'column': col,
                                    'avg_interval_days': round(avg_interval, 1),
                                    'std_interval_days': round(std_interval, 1)
                                }
                            })

            except:
                pass

        return issues

    def _check_future_dates(self):
        """미래 날짜 검사"""
        issues = []

        date_cols = self._get_date_columns()
        now = pd.Timestamp.now()

        for col in date_cols:
            try:
                dates = pd.to_datetime(self.df[col], errors='coerce')
                future_dates = (dates > now).sum()

                if future_dates > 0:
                    # 예약/예정 날짜가 아닌 경우
                    if not any(keyword in col.lower() for keyword in ['예약', '예정', 'scheduled', 'planned', 'expected']):
                        issues.append({
                            'title': f'컬럼 "{col}"에 미래 날짜 존재',
                            'severity': '🟡 중간',
                            'description': f'현재 시점보다 미래의 날짜가 {future_dates}건 존재합니다.',
                            'details': {
                                'column': col,
                                'future_count': int(future_dates)
                            }
                        })

            except:
                pass

        return issues

    def _calculate_score(self, issues, metrics):
        """점수 계산 (엄격한 기준)"""
        base_score = 100

        # 경과 일수 기반 감점 (더 엄격하게)
        if metrics['경과 일수'] != 'N/A':
            try:
                days_old = int(metrics['경과 일수'].replace('일', ''))
                if days_old > 365:
                    base_score -= 40  # 30 -> 40
                elif days_old > 180:
                    base_score -= 25  # 20 -> 25
                elif days_old > 90:
                    base_score -= 15  # 10 -> 15
            except:
                pass

        # 이슈 개수 기반 감점 (5 -> 10)
        issue_penalty = min(len(issues) * 10, 40)
        total_score = base_score - issue_penalty

        # 매우 오래된 데이터면 추가 감점
        if metrics['경과 일수'] != 'N/A':
            try:
                days_old = int(metrics['경과 일수'].replace('일', ''))
                if days_old > 730:  # 2년 이상
                    total_score *= 0.5
            except:
                pass

        return round(max(0, total_score), 2)
