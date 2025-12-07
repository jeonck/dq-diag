"""
일관성 진단 모듈
Consistency Checker Module

속성명, 표준 준수, 중복값, 연계값 등의 일관성을 진단합니다.
"""

import pandas as pd
import numpy as np
import re


class ConsistencyChecker:
    def __init__(self, df):
        self.df = df
        self.name = "일관성 (Consistency)"

    def check(self):
        """일관성 진단 실행"""
        issues = []
        metrics = {}

        # 1. 컬럼명 일관성 검사
        naming_issue = self._check_column_naming()
        if naming_issue:
            issues.append(naming_issue)

        # 2. 데이터 타입 일관성 검사
        type_issues = self._check_type_consistency()
        issues.extend(type_issues)

        # 3. 중복 데이터 검사
        duplicate_issues = self._check_duplicates()
        issues.extend(duplicate_issues)

        # 4. 코드값 일관성 검사
        code_issues = self._check_code_consistency()
        issues.extend(code_issues)

        # 5. 날짜 형식 일관성 검사
        date_issues = self._check_date_format_consistency()
        issues.extend(date_issues)

        # 메트릭 계산
        duplicate_rate = (self.df.duplicated().sum() / len(self.df) * 100) if len(self.df) > 0 else 0

        # ID 컬럼 중복률 계산
        id_duplicate_rate = 0
        id_cols = [col for col in self.df.columns if any(keyword in col.lower() for keyword in ['id', 'key', 'uuid', 'guid', '번호', 'no'])]
        if id_cols:
            max_id_dup_rate = 0
            for col in id_cols:
                non_null = self.df[col].dropna()
                if len(non_null) > 0:
                    dup_rate = (non_null.duplicated().sum() / len(non_null) * 100)
                    max_id_dup_rate = max(max_id_dup_rate, dup_rate)
            id_duplicate_rate = max_id_dup_rate

        metrics['중복 레코드 비율'] = f"{duplicate_rate:.2f}%"
        metrics['ID 중복 비율'] = f"{id_duplicate_rate:.2f}%"
        metrics['컬럼 수'] = len(self.df.columns)
        metrics['고유 레코드 수'] = f"{len(self.df.drop_duplicates()):,}"

        # 점수 계산 (ID 중복률도 고려)
        score = self._calculate_score(duplicate_rate, id_duplicate_rate, len(issues))

        return {
            'name': self.name,
            'score': score,
            'issues': issues,
            'metrics': metrics
        }

    def _check_column_naming(self):
        """컬럼명 명명 규칙 검사"""
        issues_detail = []

        for col in self.df.columns:
            # 공백 포함 확인
            if ' ' in col:
                issues_detail.append(f"'{col}': 공백 포함")

            # 특수문자 확인 (언더스코어 제외)
            if re.search(r'[^a-zA-Z0-9_가-힣]', col):
                issues_detail.append(f"'{col}': 특수문자 포함")

            # 대소문자 혼용 확인
            if col != col.lower() and col != col.upper():
                if not col.replace('_', '').isalnum():
                    issues_detail.append(f"'{col}': 대소문자 혼용")

        if issues_detail:
            return {
                'title': '컬럼명 명명 규칙 위반',
                'severity': '🟡 중간',
                'description': f'{len(issues_detail)}개의 컬럼명이 명명 규칙을 위반하고 있습니다.',
                'details': {
                    'issues': issues_detail[:10],  # 최대 10개만 표시
                    'total_count': len(issues_detail)
                }
            }
        return None

    def _check_type_consistency(self):
        """데이터 타입 일관성 검사"""
        issues = []

        # 동일한 접미사를 가진 컬럼들의 타입 일치 여부 확인
        suffix_groups = {}

        for col in self.df.columns:
            # 날짜 관련 컬럼
            if any(keyword in col.lower() for keyword in ['date', 'dt', '일자', '날짜', '시간']):
                suffix_groups.setdefault('날짜', []).append((col, self.df[col].dtype))

            # 금액 관련 컬럼
            elif any(keyword in col.lower() for keyword in ['amount', 'amt', 'price', '금액', '가격']):
                suffix_groups.setdefault('금액', []).append((col, self.df[col].dtype))

            # 코드 관련 컬럼
            elif any(keyword in col.lower() for keyword in ['code', 'cd', '코드']):
                suffix_groups.setdefault('코드', []).append((col, self.df[col].dtype))

        # 각 그룹 내에서 타입 일관성 확인
        for group_name, columns in suffix_groups.items():
            types = set([dtype for _, dtype in columns])
            if len(types) > 1:
                issues.append({
                    'title': f'{group_name} 컬럼 타입 불일치',
                    'severity': '🟡 중간',
                    'description': f'{group_name} 관련 컬럼들이 서로 다른 데이터 타입을 사용하고 있습니다.',
                    'details': {
                        'group': group_name,
                        'columns': [(col, str(dtype)) for col, dtype in columns]
                    }
                })

        # 동일 명칭 다른 타입/길이 검사
        # 핵심 단어 추출하여 유사한 컬럼 그룹핑
        from collections import defaultdict
        import re

        # 컬럼명에서 핵심 단어 추출
        col_info = {}
        for col in self.df.columns:
            # 언더스코어나 camelCase로 분리
            words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)|\d+|[가-힣]+', col)
            # 주요 명사 추출 (코드, 명, 명칭, id 등 제외한 핵심 단어)
            key_words = [w.lower() for w in words if w.lower() not in ['cd', 'code', 'id', 'no', 'nm', 'name']]

            if key_words:
                key = '_'.join(key_words)
                if key not in col_info:
                    col_info[key] = []

                # 타입과 길이 정보 저장
                dtype = self.df[col].dtype
                if dtype == 'object':
                    max_len = self.df[col].astype(str).str.len().max()
                else:
                    max_len = None

                col_info[key].append((col, dtype, max_len))

        # 동일 핵심 단어를 가진 컬럼들의 타입/길이 비교
        for key, cols in col_info.items():
            if len(cols) > 1:
                # 타입 불일치 검사
                types = set([dtype for _, dtype, _ in cols])
                if len(types) > 1:
                    issues.append({
                        'title': f'유사 명칭 컬럼의 타입 불일치',
                        'severity': '🟡 중간',
                        'description': f'유사한 명칭의 컬럼들이 서로 다른 데이터 타입을 사용하고 있습니다.',
                        'details': {
                            'key_words': key,
                            'columns': [(col, str(dtype), max_len) for col, dtype, max_len in cols]
                        }
                    })

                # 길이 불일치 검사 (문자열 컬럼만)
                str_cols = [(col, max_len) for col, dtype, max_len in cols if dtype == 'object' and max_len]
                if len(str_cols) > 1:
                    lengths = set([max_len for _, max_len in str_cols])
                    if len(lengths) > 1:
                        # 길이 차이가 2배 이상이면 경고
                        min_len = min(lengths)
                        max_len_val = max(lengths)
                        if max_len_val / min_len >= 2:
                            issues.append({
                                'title': f'유사 명칭 컬럼의 길이 불일치',
                                'severity': '🟢 낮음',
                                'description': f'유사한 명칭의 문자열 컬럼들이 서로 다른 최대 길이를 가지고 있습니다. ({min_len} vs {max_len_val})',
                                'details': {
                                    'key_words': key,
                                    'columns': [(col, max_len) for col, max_len in str_cols],
                                    'min_length': int(min_len),
                                    'max_length': int(max_len_val)
                                }
                            })

        return issues

    def _check_duplicates(self):
        """중복 데이터 검사"""
        issues = []

        # 1. 전체 레코드 중복 검사
        duplicate_count = self.df.duplicated().sum()

        if duplicate_count > 0:
            duplicate_rate = (duplicate_count / len(self.df)) * 100

            if duplicate_rate > 10:
                severity = '🔴 높음'
            elif duplicate_rate > 5:
                severity = '🟡 중간'
            else:
                severity = '🟢 낮음'

            issues.append({
                'title': '중복 레코드 발견',
                'severity': severity,
                'description': f'전체 {len(self.df)}건 중 {duplicate_count}건({duplicate_rate:.2f}%)이 중복입니다.',
                'details': {
                    'duplicate_count': int(duplicate_count),
                    'duplicate_rate': round(duplicate_rate, 2),
                    'total_rows': len(self.df)
                }
            })

        # 2. ID/키 컬럼 중복 검사
        for col in self.df.columns:
            # ID나 고유 식별자로 추정되는 컬럼
            if any(keyword in col.lower() for keyword in ['id', 'key', 'uuid', 'guid', '번호', 'no', 'code', 'cd']):
                # NULL 제외하고 중복 확인
                non_null = self.df[col].dropna()
                if len(non_null) > 0:
                    dup_count = non_null.duplicated().sum()
                    if dup_count > 0:
                        dup_rate = (dup_count / len(non_null)) * 100

                        if dup_rate > 10:
                            severity = '🔴 높음'
                        elif dup_rate > 5:
                            severity = '🟡 중간'
                        else:
                            severity = '🟢 낮음'

                        # 중복된 값들 확인
                        dup_values = non_null[non_null.duplicated(keep=False)].value_counts()

                        issues.append({
                            'title': f'컬럼 "{col}"에서 중복 ID 발견',
                            'severity': severity,
                            'description': f'고유해야 할 ID 컬럼에서 {dup_count}건({dup_rate:.2f}%)의 중복이 발견되었습니다.',
                            'details': {
                                'column': col,
                                'duplicate_count': int(dup_count),
                                'duplicate_rate': round(dup_rate, 2),
                                'duplicate_values': {str(k): int(v) for k, v in dup_values.head(5).items()}
                            }
                        })

        return issues

    def _check_code_consistency(self):
        """코드값 일관성 검사"""
        issues = []

        for col in self.df.columns:
            # 코드 컬럼으로 추정되는 경우
            if any(keyword in col.lower() for keyword in ['code', 'cd', '코드', 'yn', '여부', '구분']):
                unique_values = self.df[col].dropna().unique()

                # 유니크 값이 너무 많으면 스킵 (코드 컬럼이 아닐 가능성)
                if len(unique_values) > 20:
                    continue

                # 대소문자 혼용 확인
                if self.df[col].dtype == 'object':
                    values_lower = set([str(v).lower() for v in unique_values])
                    if len(values_lower) < len(unique_values):
                        issues.append({
                            'title': f'컬럼 "{col}"의 코드값 대소문자 불일치',
                            'severity': '🟡 중간',
                            'description': '동일한 코드값이 대소문자를 달리하여 저장되어 있습니다.',
                            'details': {
                                'column': col,
                                'unique_values': list(unique_values)[:20]
                            }
                        })

        return issues

    def _check_date_format_consistency(self):
        """날짜 형식 일관성 검사"""
        issues = []

        for col in self.df.columns:
            # 날짜 컬럼으로 추정되는 경우
            if any(keyword in col.lower() for keyword in ['date', 'dt', '일자', '날짜']):

                if self.df[col].dtype == 'object':
                    # NULL이 아닌 값들의 형식 확인
                    non_null_values = self.df[col].dropna().astype(str)

                    if len(non_null_values) == 0:
                        continue

                    # 다양한 날짜 형식 패턴
                    formats = {
                        'YYYY-MM-DD': r'^\d{4}-\d{2}-\d{2}',
                        'YYYY/MM/DD': r'^\d{4}/\d{2}/\d{2}',
                        'YYYYMMDD': r'^\d{8}$',
                        'DD-MM-YYYY': r'^\d{2}-\d{2}-\d{4}',
                        'DD/MM/YYYY': r'^\d{2}/\d{2}/\d{4}'
                    }

                    format_counts = {}
                    for format_name, pattern in formats.items():
                        count = non_null_values.str.match(pattern).sum()
                        if count > 0:
                            format_counts[format_name] = count

                    # 여러 형식이 혼용되는 경우
                    if len(format_counts) > 1:
                        issues.append({
                            'title': f'컬럼 "{col}"의 날짜 형식 불일치',
                            'severity': '🟡 중간',
                            'description': '여러 가지 날짜 형식이 혼용되어 있습니다.',
                            'details': {
                                'column': col,
                                'format_counts': format_counts
                            }
                        })

        return issues

    def _calculate_score(self, duplicate_rate, id_duplicate_rate, issue_count):
        """점수 계산 (엄격한 기준)"""
        # 레코드 중복률 기반 점수 (25%)
        duplicate_score = max(0, 100 - duplicate_rate * 5) * 0.25

        # ID 중복률 기반 점수 (25%) - ID 중복은 더욱 치명적
        id_duplicate_score = max(0, 100 - id_duplicate_rate * 10) * 0.25

        # 이슈 개수 기반 감점 (50%)
        # 이슈당 더 큰 감점 적용
        issue_penalty = min(issue_count * 10, 50)
        issue_score = 50 - issue_penalty

        total_score = duplicate_score + id_duplicate_score + issue_score

        # 중복률이 20% 이상이면 추가 감점
        if duplicate_rate >= 20 or id_duplicate_rate >= 20:
            total_score *= 0.5
        # 중복률이 10% 이상이면 추가 감점
        elif duplicate_rate >= 10 or id_duplicate_rate >= 10:
            total_score *= 0.7

        return round(max(0, total_score), 2)
