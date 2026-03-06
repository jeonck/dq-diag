"""
접근성 진단 모듈
Accessibility Checker Module

데이터의 접근 용이성, 검색 기능, API 지원 등을 진단합니다.
"""

import pandas as pd
import numpy as np


class AccessibilityChecker:
    def __init__(self, df):
        self.df = df
        self.name = "접근성 (Accessibility)"

    def check(self):
        """접근성 진단 실행"""
        issues = []
        metrics = {}

        # 1. 데이터 접근 용이성 검사
        access_issues = self._check_accessibility()
        issues.extend(access_issues)

        # 2. 메타데이터 충분성 검사
        metadata_issues = self._check_metadata_sufficiency()
        issues.extend(metadata_issues)

        # 3. 데이터 검색 용이성 검사
        search_issues = self._check_searchability()
        issues.extend(search_issues)

        # 메트릭 계산
        total_cols = len(self.df.columns)
        searchable_cols = sum([1 for col in self.df.columns if self.df[col].notna().sum() > 0])
        metadata_score = self._calculate_metadata_score()

        metrics['검색 가능 컬럼 수'] = searchable_cols
        metrics['전체 컬럼 수'] = total_cols
        metrics['메타데이터 충분성'] = f"{metadata_score:.1f}%"
        metrics['접근성 점수'] = f"{self._calculate_accessibility_metric():.1f}"

        # 점수 계산
        score = self._calculate_score(metadata_score, len(issues))

        return {
            'name': self.name,
            'score': score,
            'issues': issues,
            'metrics': metrics
        }

    def _check_accessibility(self):
        """데이터 접근 용이성 검사"""
        issues = []

        # 1. 인덱스 설정 여부 (고유 식별자 존재)
        id_cols = [col for col in self.df.columns if 
                   any(keyword in col.lower() for keyword in ['id', 'key', '번호', 'no', 'code'])]

        if not id_cols:
            issues.append({
                'title': '고유 식별자 컬럼 부재',
                'severity': '🟡 중간',
                'description': '데이터를 고유하게 식별할 수 있는 컬럼이 없습니다. 인덱스 설정이 어려울 수 있습니다.',
                'details': {
                    'recommendation': '고유 식별자 컬럼 (ID, Primary Key) 을 추가하세요.'
                }
            })

        # 2. 데이터 크기 적절성
        memory_usage = self.df.memory_usage(deep=True).sum() / 1024  # KB

        if memory_usage > 1024 * 1024:  # 1GB 이상
            issues.append({
                'title': '대규모 데이터셋',
                'severity': '🟢 낮음',
                'description': f'데이터 크기가 {memory_usage / 1024:.2f}MB 로 큽니다. 인덱싱 및 파티셔닝을 고려하세요.',
                'details': {
                    'memory_kb': round(memory_usage, 2),
                    'memory_mb': round(memory_usage / 1024, 2)
                }
            })

        return issues

    def _check_metadata_sufficiency(self):
        """메타데이터 충분성 검사"""
        issues = []

        # 컬럼명 명명 규칙 준수
        poorly_named_cols = []
        for col in self.df.columns:
            # 너무 짧은 컬럼명 (1 글자)
            if len(col) == 1:
                poorly_named_cols.append(f"'{col}': 너무 짧은 이름")
            # 특수문자 포함 (언더스코어 제외)
            elif any(c for c in col if not c.isalnum() and c not in ['_', '가', '나', '다']):
                if not all(c.isalnum() or c == '_' or ord(c) > 12500 for c in col):
                    poorly_named_cols.append(f"'{col}': 특수문자 포함")

        if poorly_named_cols:
            issues.append({
                'title': '컬럼명 명명 규칙 미준수',
                'severity': '🟢 낮음',
                'description': f'{len(poorly_named_cols)}개의 컬럼이 명명 규칙을 위반하고 있습니다.',
                'details': {
                    'columns': poorly_named_cols[:10],
                    'total_count': len(poorly_named_cols)
                }
            })

        return issues

    def _check_searchability(self):
        """데이터 검색 용이성 검사"""
        issues = []

        # 1. 정렬 가능한 컬럼 (숫자 또는 문자열)
        unsortable_cols = []
        for col in self.df.columns:
            if self.df[col].dtype == 'object':
                # 객체 타입이지만 정렬이 어려운 경우 (복잡한 구조)
                try:
                    self.df[col].sort_values()
                except:
                    unsortable_cols.append(col)

        if unsortable_cols:
            issues.append({
                'title': '정렬 불가 컬럼 존재',
                'severity': '🟢 낮음',
                'description': f'{len(unsortable_cols)}개의 컬럼이 정렬操作에 제한이 있습니다.',
                'details': {
                    'columns': unsortable_cols[:10],
                    'count': len(unsortable_cols)
                }
            })

        # 2. 필터링 가능한 컬럼
        low_cardinality_cols = []
        for col in self.df.columns:
            if self.df[col].nunique() < 5 and self.df[col].notna().sum() > 0:
                low_cardinality_cols.append(col)

        if low_cardinality_cols:
            # 저카디널리티 컬럼은 필터링에 유용
            pass  # 긍정적인 정보

        return issues

    def _calculate_metadata_score(self):
        """메타데이터 충분성 점수 계산"""
        if len(self.df.columns) == 0:
            return 0

        # 컬럼명의 설명성 (길이 기반)
        name_scores = []
        for col in self.df.columns:
            col_len = len(col)
            if 3 <= col_len <= 30:
                name_scores.append(100)
            elif col_len < 3:
                name_scores.append(50)
            else:
                name_scores.append(80)

        return np.mean(name_scores)

    def _calculate_accessibility_metric(self):
        """접근성 메트릭 계산"""
        base_score = 100

        # 고유 식별자 있으면加分
        id_cols = [col for col in self.df.columns if 
                   any(keyword in col.lower() for keyword in ['id', 'key', '번호', 'no'])]
        if id_cols:
            base_score += 10

        # 메타데이터 충분성
        metadata_score = self._calculate_metadata_score()
        base_score += metadata_score * 0.2

        return min(100, base_score)

    def _calculate_score(self, metadata_score, issue_count):
        """점수 계산"""
        base_score = 100

        # 메타데이터 충분성 기반 (30%)
        metadata_component = metadata_score * 0.3

        # 이슈 개수 기반 감점 (70%)
        issue_penalty = min(issue_count * 10, 70)
        issue_score = 70 - issue_penalty

        total_score = metadata_component + issue_score

        return round(max(0, total_score), 2)
