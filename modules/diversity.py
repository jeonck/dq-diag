"""
다양성 진단 모듈
Diversity Checker Module

데이터의 분포 균형성, 카테고리 다양성, 편향 지표 등을 진단합니다.
"""

import pandas as pd
import numpy as np


class DiversityChecker:
    def __init__(self, df):
        self.df = df
        self.name = "다양성 (Diversity)"

    def check(self):
        """다양성 진단 실행"""
        issues = []
        metrics = {}

        # 1. 데이터 분포 균형성 검사
        distribution_issues = self._check_distribution_balance()
        issues.extend(distribution_issues)

        # 2. 카테고리 다양성 검사
        category_issues = self._check_category_diversity()
        issues.extend(category_issues)

        # 3. 샘플 대표성 검사
        representation_issues = self._check_sample_representation()
        issues.extend(representation_issues)

        # 4. 편향 지표 검사
        bias_issues = self._check_bias_metrics()
        issues.extend(bias_issues)

        # 메트릭 계산
        total_cols = len(self.df.columns)
        categorical_cols = len([col for col in self.df.columns if self.df[col].dtype == 'object' or 
                                pd.api.types.is_categorical_dtype(self.df[col])])

        avg_diversity = self._calculate_average_diversity()

        metrics['범주형 컬럼 수'] = categorical_cols
        metrics['전체 컬럼 수'] = total_cols
        metrics['평균 다양성 지수'] = f"{avg_diversity:.2f}"
        metrics['데이터 레코드 수'] = f"{len(self.df):,}"

        # 점수 계산
        score = self._calculate_score(avg_diversity, len(issues))

        return {
            'name': self.name,
            'score': score,
            'issues': issues,
            'metrics': metrics
        }

    def _check_distribution_balance(self):
        """데이터 분포 균형성 검사"""
        issues = []

        for col in self.df.columns:
            # 범주형 컬럼만 검사
            if self.df[col].dtype == 'object' or pd.api.types.is_categorical_dtype(self.df[col]):
                non_null = self.df[col].dropna()

                if len(non_null) == 0:
                    continue

                value_counts = non_null.value_counts()
                total = len(non_null)
                unique_count = len(value_counts)

                if unique_count < 2:
                    continue

                # 최대값과 최소값의 비율 (편향도)
                max_count = value_counts.iloc[0]
                min_count = value_counts.iloc[-1]

                if max_count > 0 and min_count > 0:
                    bias_ratio = max_count / min_count

                    # 편향도가 심한 경우 (10 배 이상)
                    if bias_ratio > 10:
                        issues.append({
                            'title': f'컬럼 "{col}"의 분포 편향 심각',
                            'severity': '🔴 높음',
                            'description': f'최대 카테고리 ({value_counts.index[0]}) 가 최소 카테고리 ({value_counts.index[-1]}) 보다 {bias_ratio:.1f}배 많습니다.',
                            'details': {
                                'column': col,
                                'bias_ratio': round(bias_ratio, 2),
                                'max_category': str(value_counts.index[0]),
                                'max_count': int(max_count),
                                'min_category': str(value_counts.index[-1]),
                                'min_count': int(min_count),
                                'total_records': total
                            }
                        })
                    elif bias_ratio > 5:
                        issues.append({
                            'title': f'컬럼 "{col}"의 분포 편향',
                            'severity': '🟡 중간',
                            'description': f'데이터 분포가 편향되어 있습니다 (편향도: {bias_ratio:.1f}배).',
                            'details': {
                                'column': col,
                                'bias_ratio': round(bias_ratio, 2),
                                'top_category': str(value_counts.index[0]),
                                'top_count': int(max_count)
                            }
                        })

        return issues

    def _check_category_diversity(self):
        """카테고리 다양성 검사"""
        issues = []

        for col in self.df.columns:
            if self.df[col].dtype == 'object' or pd.api.types.is_categorical_dtype(self.df[col]):
                non_null = self.df[col].dropna()

                if len(non_null) == 0:
                    continue

                unique_count = non_null.nunique()
                total_count = len(non_null)

                # 카디널리티가 너무 낮은 경우
                if unique_count == 1:
                    issues.append({
                        'title': f'컬럼 "{col}"의 카테고리 단일화',
                        'severity': '🟡 중간',
                        'description': f'모든 값이 동일한 값으로만 구성되어 있습니다. 다양성이 없습니다.',
                        'details': {
                            'column': col,
                            'unique_count': unique_count,
                            'total_count': total_count,
                            'single_value': str(non_null.iloc[0])
                        }
                    })
                elif unique_count < 3 and total_count > 100:
                    issues.append({
                        'title': f'컬럼 "{col}"의 카테고리 부족',
                        'severity': '🟢 낮음',
                        'description': f'전체 {total_count}건 중 유니크 값이 {unique_count}개뿐입니다.',
                        'details': {
                            'column': col,
                            'unique_count': unique_count,
                            'total_count': total_count,
                            'categories': list(non_null.unique())[:10]
                        }
                    })

        return issues

    def _check_sample_representation(self):
        """샘플 대표성 검사"""
        issues = []

        # 전체 레코드 수가 충분한지 확인
        total_rows = len(self.df)

        if total_rows < 30:
            issues.append({
                'title': '샘플 크기 부족',
                'severity': '🔴 높음',
                'description': f'전체 레코드가 {total_rows}건으로 통계적 대표성을 확보하기 어렵습니다.',
                'details': {
                    'total_rows': total_rows,
                    'recommended_min': 100,
                    'statistical_min': 30
                }
            })
        elif total_rows < 100:
            issues.append({
                'title': '샘플 크기 작음',
                'severity': '🟡 중간',
                'description': f'전체 레코드가 {total_rows}건으로 통계적 신뢰도가 낮을 수 있습니다.',
                'details': {
                    'total_rows': total_rows,
                    'recommended_min': 100
                }
            })

        return issues

    def _check_bias_metrics(self):
        """편향 지표 검사"""
        issues = []

        # 성별, 연령대 등 민감한 속성의 편향 검사
        sensitive_cols = {
            'gender': ['gender', 'sex', '성별', '남여'],
            'age_group': ['age_group', 'age_grp', '연령대', '세대'],
            'region': ['region', 'area', '지역', '시도']
        }

        for category, keywords in sensitive_cols.items():
            for col in self.df.columns:
                if any(keyword in col.lower() for keyword in keywords):
                    non_null = self.df[col].dropna()

                    if len(non_null) == 0:
                        continue

                    value_counts = non_null.value_counts()
                    total = len(non_null)

                    # 특정 카테고리에 과도하게 편향된 경우
                    if len(value_counts) > 0:
                        top_ratio = value_counts.iloc[0] / total * 100

                        if top_ratio > 80:
                            issues.append({
                                'title': f'민감 속성 "{col}"의 편향',
                                'severity': '🟡 중간',
                                'description': f'특정 카테고리 ({value_counts.index[0]}) 가 {top_ratio:.1f}% 로 과도하게 편향되어 있습니다.',
                                'details': {
                                    'column': col,
                                    'category_type': category,
                                    'top_category': str(value_counts.index[0]),
                                    'top_ratio': round(top_ratio, 2),
                                    'distribution': {str(k): int(v) for k, v in value_counts.head(5).items()}
                                }
                            })

        return issues

    def _calculate_average_diversity(self):
        """평균 다양성 지수 계산 (Shannon Diversity Index 기반)"""
        diversity_scores = []

        for col in self.df.columns:
            if self.df[col].dtype == 'object' or pd.api.types.is_categorical_dtype(self.df[col]):
                non_null = self.df[col].dropna()

                if len(non_null) > 1:
                    # Shannon Diversity Index
                    value_counts = non_null.value_counts()
                    proportions = value_counts / len(non_null)

                    # H' = -Σ(pi * ln(pi))
                    shannon_index = -sum(p * np.log(p) for p in proportions if p > 0)

                    # 정규화 (0-100)
                    max_diversity = np.log(len(non_null))
                    if max_diversity > 0:
                        normalized_diversity = (shannon_index / max_diversity) * 100
                        diversity_scores.append(normalized_diversity)

        if diversity_scores:
            return np.mean(diversity_scores)
        return 50.0  # 기본값

    def _calculate_score(self, avg_diversity, issue_count):
        """점수 계산"""
        # 다양성 지수 기반 점수 (50%)
        diversity_score = avg_diversity * 0.5

        # 이슈 개수 기반 감점 (50%)
        issue_penalty = min(issue_count * 10, 50)
        issue_score = 50 - issue_penalty

        total_score = diversity_score + issue_score

        return round(max(0, total_score), 2)
