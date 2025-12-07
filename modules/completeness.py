"""
완전성 진단 모듈
Completeness Checker Module

데이터 모델의 완전성, 식별자, 물리구조, 속성의미 등을 진단합니다.
"""

import pandas as pd
import numpy as np
from modules.utils import safe_outlier_detection, calculate_uniqueness_metrics


class CompletenessChecker:
    def __init__(self, df):
        self.df = df
        self.name = "완전성 (Completeness)"

    def check(self):
        """완전성 진단 실행"""
        issues = []
        metrics = {}

        # 1. 기본키(PK) 미정의 검사
        pk_issue = self._check_primary_key()
        if pk_issue:
            issues.append(pk_issue)

        # 2. 필수값 완전성 검사
        null_issues = self._check_null_values()
        issues.extend(null_issues)

        # 3. 미사용 컬럼 검사
        unused_cols = self._check_unused_columns()
        if unused_cols:
            issues.append(unused_cols)

        # 4. 데이터 타입 일치성 검사
        type_issue = self._check_data_types()
        if type_issue:
            issues.append(type_issue)

        # 5. 이상치 검사 (추가)
        outlier_issues = self._check_outliers()
        issues.extend(outlier_issues)

        # 메트릭 계산
        total_cells = len(self.df) * len(self.df.columns)
        null_cells = self.df.isnull().sum().sum()
        completeness_rate = ((total_cells - null_cells) / total_cells * 100) if total_cells > 0 else 0

        metrics['완전성 비율'] = f"{completeness_rate:.2f}%"
        metrics['NULL 셀 수'] = f"{null_cells:,}"
        metrics['전체 셀 수'] = f"{total_cells:,}"

        # 점수 계산 (100점 만점)
        score = self._calculate_score(completeness_rate, len(issues))

        return {
            'name': self.name,
            'score': score,
            'issues': issues,
            'metrics': metrics
        }

    def _check_primary_key(self):
        """기본키 존재 여부 확인"""
        # 모든 행이 유일한지 확인
        duplicate_rows = self.df.duplicated().sum()

        if duplicate_rows > 0:
            return {
                'title': '기본키 미정의 또는 중복 레코드',
                'severity': '🔴 높음',
                'description': f'중복된 레코드가 {duplicate_rows}건 발견되었습니다. 각 레코드를 유일하게 구분할 수 있는 식별자가 필요합니다.',
                'details': {
                    'duplicate_count': int(duplicate_rows),
                    'total_rows': len(self.df)
                }
            }
        return None

    def _check_null_values(self):
        """NULL 값 및 공백 값 검사"""
        issues = []

        null_summary = self.df.isnull().sum()
        null_cols = null_summary[null_summary > 0]

        for col, null_count in null_cols.items():
            null_rate = (null_count / len(self.df)) * 100

            # NULL과 Space 혼재 검사 (문자열 컬럼만)
            space_count = 0
            if self.df[col].dtype == 'object':
                # 빈 문자열, 공백만 있는 문자열 검사
                space_count = (self.df[col].fillna('').str.strip() == '').sum() - null_count

                # NULL과 Space가 모두 존재하면 혼재 경고
                if null_count > 0 and space_count > 0:
                    total_empty = null_count + space_count
                    empty_rate = (total_empty / len(self.df)) * 100

                    issues.append({
                        'title': f'컬럼 "{col}"에 NULL과 공백 혼재',
                        'severity': '🔴 높음',
                        'description': f'NULL {null_count}건, 공백 {space_count}건으로 총 {total_empty}건({empty_rate:.2f}%)의 빈 값이 혼재되어 있습니다. 데이터 일관성을 위해 통일이 필요합니다.',
                        'details': {
                            'column': col,
                            'null_count': int(null_count),
                            'space_count': int(space_count),
                            'total_empty': int(total_empty),
                            'empty_rate': round(empty_rate, 2),
                            'total_rows': len(self.df)
                        }
                    })
                    continue  # NULL과 Space 혼재 이슈를 보고했으면 개별 NULL 이슈는 스킵

            # 일반 NULL 값 이슈
            if null_rate > 50:
                severity = '🔴 높음'
            elif null_rate > 20:
                severity = '🟡 중간'
            else:
                severity = '🟢 낮음'

            # 공백만 있는 경우 포함
            total_missing = null_count + space_count
            missing_rate = (total_missing / len(self.df)) * 100

            desc_parts = [f'전체 {len(self.df)}건 중']
            if null_count > 0:
                desc_parts.append(f'NULL {null_count}건')
            if space_count > 0:
                desc_parts.append(f'공백 {space_count}건')
            desc_parts.append(f'(총 {missing_rate:.2f}%)')

            issues.append({
                'title': f'컬럼 "{col}"의 필수값 누락',
                'severity': severity,
                'description': ' '.join(desc_parts) + '이 누락되었습니다.',
                'details': {
                    'column': col,
                    'null_count': int(null_count),
                    'space_count': int(space_count),
                    'total_missing': int(total_missing),
                    'missing_rate': round(missing_rate, 2),
                    'total_rows': len(self.df)
                }
            })

        return issues

    def _check_unused_columns(self):
        """미사용 컬럼 검사"""
        unused_cols = []

        for col in self.df.columns:
            # 모든 값이 NULL인 컬럼
            if self.df[col].isnull().all():
                unused_cols.append(col)
            # 모든 값이 동일한 컬럼
            elif self.df[col].nunique() <= 1:
                unused_cols.append(col)

        if unused_cols:
            return {
                'title': '미사용 또는 무의미한 컬럼 발견',
                'severity': '🟡 중간',
                'description': f'{len(unused_cols)}개의 미사용 컬럼이 발견되었습니다.',
                'details': {
                    'unused_columns': unused_cols,
                    'count': len(unused_cols)
                }
            }
        return None

    def _check_data_types(self):
        """데이터 타입 일치성 검사"""
        type_issues = []

        for col in self.df.columns:
            # 숫자형으로 보이는 컬럼이 문자형인 경우
            if self.df[col].dtype == 'object':
                # NULL이 아닌 값들 중 숫자로 변환 가능한지 확인
                non_null_values = self.df[col].dropna()
                if len(non_null_values) > 0:
                    try:
                        pd.to_numeric(non_null_values)
                        type_issues.append(col)
                    except:
                        pass

        if type_issues:
            return {
                'title': '데이터 타입 불일치',
                'severity': '🟡 중간',
                'description': f'{len(type_issues)}개의 컬럼이 숫자형으로 변환 가능하나 문자형으로 저장되어 있습니다.',
                'details': {
                    'columns': type_issues,
                    'count': len(type_issues)
                }
            }
        return None

    def _check_outliers(self):
        """이상치 검사 (IQR 방법 + Z-score 방법)"""
        issues = []

        for col in self.df.columns:
            if pd.api.types.is_numeric_dtype(self.df[col]):
                # IQR 방법
                outliers_iqr = safe_outlier_detection(self.df[col])

                # Z-score 방법 (더 민감한 탐지)
                non_null = self.df[col].dropna()
                if len(non_null) > 3:
                    mean_val = non_null.mean()
                    std_val = non_null.std()

                    if std_val and std_val != 0:
                        z_scores = ((non_null - mean_val) / std_val).abs()
                        # 데이터가 작을수록 더 민감하게 (10개 이하면 1.5, 그 이상이면 2.0)
                        threshold = 1.5 if len(non_null) <= 10 else 2.0
                        outliers_z = non_null[z_scores > threshold]
                    else:
                        outliers_z = pd.Series(dtype=float)
                else:
                    outliers_z = pd.Series(dtype=float)

                # 두 방법 중 하나라도 탐지되면 보고
                if isinstance(outliers_iqr, pd.Series) and len(outliers_iqr) > 0:
                    outlier_rate = (len(outliers_iqr) / len(self.df)) * 100

                    if outlier_rate > 10:
                        severity = '🔴 높음'
                    elif outlier_rate > 5:
                        severity = '🟡 중간'
                    else:
                        severity = '🟢 낮음'

                    issues.append({
                        'title': f'컬럼 "{col}"에서 이상치 발견 (IQR 방법)',
                        'severity': severity,
                        'description': f'IQR 방법으로 {len(outliers_iqr)}건({outlier_rate:.2f}%)의 이상치가 탐지되었습니다.',
                        'details': {
                            'column': col,
                            'method': 'IQR',
                            'outlier_count': len(outliers_iqr),
                            'outlier_rate': round(outlier_rate, 2),
                            'outlier_values': list(outliers_iqr.head(10))
                        }
                    })
                elif len(outliers_z) > 0:
                    # IQR로 탐지 안되면 Z-score로 탐지
                    outlier_rate = (len(outliers_z) / len(self.df)) * 100

                    if outlier_rate > 10:
                        severity = '🔴 높음'
                    elif outlier_rate > 5:
                        severity = '🟡 중간'
                    else:
                        severity = '🟢 낮음'

                    issues.append({
                        'title': f'컬럼 "{col}"에서 이상치 발견 (Z-score 방법)',
                        'severity': severity,
                        'description': f'Z-score 방법으로 {len(outliers_z)}건({outlier_rate:.2f}%)의 이상치가 탐지되었습니다. (평균: {mean_val:.1f}, 표준편차: {std_val:.1f})',
                        'details': {
                            'column': col,
                            'method': 'Z-score',
                            'outlier_count': len(outliers_z),
                            'outlier_rate': round(outlier_rate, 2),
                            'outlier_values': list(outliers_z.head(10)),
                            'mean': round(mean_val, 2),
                            'std': round(std_val, 2)
                        }
                    })

        return issues

    def _calculate_score(self, completeness_rate, issue_count):
        """점수 계산 (엄격한 기준)"""
        # 완전성 비율 기반 점수 (60%)
        base_score = completeness_rate * 0.6

        # 이슈 개수 기반 감점 (40%)
        # 이슈당 더 큰 감점 적용
        issue_penalty = min(issue_count * 8, 40)
        issue_score = 40 - issue_penalty

        total_score = base_score + issue_score

        # 완전성 비율이 50% 미만이면 추가 감점
        if completeness_rate < 50:
            total_score *= 0.5

        # 완전성 비율이 70% 미만이면 추가 감점
        elif completeness_rate < 70:
            total_score *= 0.7

        return round(max(0, total_score), 2)
