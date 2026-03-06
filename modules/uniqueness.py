"""
유일성 진단 모듈
Uniqueness Checker Module

데이터의 중복 여부, 고유성 등을 진단합니다.
"""

import pandas as pd
import numpy as np


class UniquenessChecker:
    def __init__(self, df):
        self.df = df
        self.name = "유일성 (Uniqueness)"

    def check(self):
        """유일성 진단 실행"""
        issues = []
        metrics = {}

        # 1. 중복 레코드 검사
        duplicate_issues = self._check_duplicate_records()
        issues.extend(duplicate_issues)

        # 2. 고유값 비율 검사
        uniqueness_issues = self._check_uniqueness_ratio()
        issues.extend(uniqueness_issues)

        # 3. 키 컬럼 중복 검사
        key_issues = self._check_key_duplicates()
        issues.extend(key_issues)

        # 4. 부분 중복 검사
        partial_issues = self._check_partial_duplicates()
        issues.extend(partial_issues)

        # 메트릭 계산
        total_rows = len(self.df)
        duplicate_rows = self.df.duplicated().sum()
        unique_rows = len(self.df.drop_duplicates())

        duplicate_rate = (duplicate_rows / total_rows * 100) if total_rows > 0 else 0
        uniqueness_rate = ((total_rows - duplicate_rows) / total_rows * 100) if total_rows > 0 else 0

        metrics['전체 레코드 수'] = f"{total_rows:,}"
        metrics['중복 레코드 수'] = f"{duplicate_rows:,}"
        metrics['고유 레코드 수'] = f"{unique_rows:,}"
        metrics['중복률'] = f"{duplicate_rate:.2f}%"
        metrics['유일성 비율'] = f"{uniqueness_rate:.2f}%"

        # 점수 계산
        score = self._calculate_score(duplicate_rate, len(issues))

        return {
            'name': self.name,
            'score': score,
            'issues': issues,
            'metrics': metrics
        }

    def _check_duplicate_records(self):
        """중복 레코드 검사"""
        issues = []

        duplicate_rows = self.df.duplicated().sum()

        if duplicate_rows > 0:
            duplicate_rate = (duplicate_rows / len(self.df)) * 100

            if duplicate_rate > 10:
                severity = '🔴 높음'
            elif duplicate_rate > 5:
                severity = '🟡 중간'
            else:
                severity = '🟢 낮음'

            # 중복된 레코드 샘플
            duplicates = self.df[self.df.duplicated(keep=False)]
            duplicate_sample = duplicates.head(5).to_dict()

            issues.append({
                'title': '중복 레코드 발견',
                'severity': severity,
                'description': f'전체 {len(self.df)}건 중 {duplicate_rows}건 ({duplicate_rate:.2f}%) 이 중복입니다.',
                'details': {
                    'duplicate_count': int(duplicate_rows),
                    'duplicate_rate': round(duplicate_rate, 2),
                    'total_rows': len(self.df),
                    'unique_rows': len(self.df.drop_duplicates()),
                    'duplicate_sample': duplicate_sample
                }
            })

        return issues

    def _check_uniqueness_ratio(self):
        """컬럼별 고유값 비율 검사"""
        issues = []

        for col in self.df.columns:
            non_null = self.df[col].dropna()

            if len(non_null) == 0:
                continue

            unique_count = non_null.nunique()
            total_count = len(non_null)
            uniqueness_ratio = (unique_count / total_count) * 100

            # ID/키 컬럼인데 고유하지 않은 경우
            if any(keyword in col.lower() for keyword in ['id', 'key', '번호', 'no', 'code', 'uuid']):
                if uniqueness_ratio < 100:
                    duplicate_count = total_count - unique_count
                    issues.append({
                        'title': f'키 컬럼 "{col}"의 유일성 위반',
                        'severity': '🔴 높음',
                        'description': f'고유해야 할 키 컬럼에서 {duplicate_count}건의 중복이 발견되었습니다.',
                        'details': {
                            'column': col,
                            'unique_count': unique_count,
                            'total_count': total_count,
                            'uniqueness_ratio': round(uniqueness_ratio, 2),
                            'duplicate_count': int(duplicate_count)
                        }
                    })
            # 일반 컬럼인데 유일성이 매우 낮은 경우
            elif uniqueness_ratio < 1 and total_count > 100:
                issues.append({
                    'title': f'컬럼 "{col}"의 유일성 낮음',
                    'severity': '🟢 낮음',
                    'description': f'전체 {total_count}건 중 유니크 값이 {unique_count}개 ({uniqueness_ratio:.2f}%) 뿐입니다.',
                    'details': {
                        'column': col,
                        'unique_count': unique_count,
                        'total_count': total_count,
                        'uniqueness_ratio': round(uniqueness_ratio, 2)
                    }
                })

        return issues

    def _check_key_duplicates(self):
        """키 컬럼 중복 검사"""
        issues = []

        # ID/키 컬럼 찾기
        key_cols = [col for col in self.df.columns if 
                    any(keyword in col.lower() for keyword in ['id', 'key', '번호', 'no', 'code', 'uuid'])]

        for col in key_cols:
            non_null = self.df[col].dropna()

            if len(non_null) == 0:
                continue

            # 중복 값 찾기
            duplicate_counts = non_null.value_counts()
            duplicates = duplicate_counts[duplicate_counts > 1]

            if len(duplicates) > 0:
                dup_count = len(duplicates)
                total_dup_records = duplicates.sum()

                if dup_count > 100:
                    severity = '🔴 높음'
                elif dup_count > 10:
                    severity = '🟡 중간'
                else:
                    severity = '🟢 낮음'

                issues.append({
                    'title': f'키 컬럼 "{col}"에서 중복 값 발견',
                    'severity': severity,
                    'description': f'{dup_count}개의 중복 값이 총 {total_dup_records}건 발견되었습니다.',
                    'details': {
                        'column': col,
                        'duplicate_value_count': int(dup_count),
                        'duplicate_record_count': int(total_dup_records),
                        'top_duplicates': {str(k): int(v) for k, v in duplicates.head(10).items()}
                    }
                })

        return issues

    def _check_partial_duplicates(self):
        """부분 중복 검사 (여러 컬럼 조합)"""
        issues = []

        # 주요 컬럼 조합으로 중복 검사
        # ID 관련 컬럼들이 있으면 조합하여 검사
        key_cols = [col for col in self.df.columns if 
                    any(keyword in col.lower() for keyword in ['id', 'key', '번호', 'no'])]

        if len(key_cols) >= 2:
            # 복합 키 중복 검사
            duplicates = self.df.duplicated(subset=key_cols, keep=False)
            dup_count = duplicates.sum()

            if dup_count > 0:
                dup_rate = (dup_count / len(self.df)) * 100

                issues.append({
                    'title': f'복합 키 중복 ({", ".join(key_cols)})',
                    'severity': '🟡 중간',
                    'description': f'복합 키 ({", ".join(key_cols)}) 에서 {dup_count}건 ({dup_rate:.2f}%) 의 중복이 발견되었습니다.',
                    'details': {
                        'key_columns': key_cols,
                        'duplicate_count': int(dup_count),
                        'duplicate_rate': round(dup_rate, 2)
                    }
                })

        return issues

    def _calculate_score(self, duplicate_rate, issue_count):
        """점수 계산"""
        # 중복률 기반 점수 (60%)
        duplicate_score = max(0, 100 - duplicate_rate * 2) * 0.6

        # 이슈 개수 기반 감점 (40%)
        issue_penalty = min(issue_count * 8, 40)
        issue_score = 40 - issue_penalty

        total_score = duplicate_score + issue_score

        # 중복률이 높으면 추가 감점
        if duplicate_rate > 20:
            total_score *= 0.5
        elif duplicate_rate > 10:
            total_score *= 0.7

        return round(max(0, total_score), 2)
