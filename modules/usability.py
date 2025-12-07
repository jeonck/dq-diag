"""
유용성 진단 모듈
Usability Checker Module

데이터의 충분성, 접근성, 활용도 등을 진단합니다.
"""

import pandas as pd
import numpy as np


class UsabilityChecker:
    def __init__(self, df):
        self.df = df
        self.name = "유용성 (Usability)"

    def check(self):
        """유용성 진단 실행"""
        issues = []
        metrics = {}

        # 1. 데이터 충분성 검사
        sufficiency_issues = self._check_data_sufficiency()
        issues.extend(sufficiency_issues)

        # 2. 컬럼 유용성 검사
        column_issues = self._check_column_usability()
        issues.extend(column_issues)

        # 3. 데이터 다양성 검사
        diversity_issues = self._check_data_diversity()
        issues.extend(diversity_issues)

        # 메트릭 계산
        total_rows = len(self.df)
        total_cols = len(self.df.columns)
        usable_cols = sum([1 for col in self.df.columns if self.df[col].notna().sum() > 0])

        metrics['전체 레코드 수'] = f"{total_rows:,}"
        metrics['전체 컬럼 수'] = total_cols
        metrics['유효 컬럼 수'] = usable_cols
        metrics['컬럼 유용성'] = f"{(usable_cols/total_cols*100):.1f}%" if total_cols > 0 else "0%"

        # 점수 계산
        score = self._calculate_score(total_rows, usable_cols, total_cols, len(issues))

        return {
            'name': self.name,
            'score': score,
            'issues': issues,
            'metrics': metrics
        }

    def _check_data_sufficiency(self):
        """데이터 충분성 검사"""
        issues = []

        total_rows = len(self.df)

        # 데이터가 너무 적은 경우
        if total_rows < 10:
            issues.append({
                'title': '데이터 레코드 수 부족',
                'severity': '🔴 높음',
                'description': f'전체 {total_rows}건의 데이터만 존재합니다. 통계적 분석 및 활용에 제약이 있을 수 있습니다.',
                'details': {
                    'total_rows': total_rows,
                    'recommended_min': 100
                }
            })
        elif total_rows < 100:
            issues.append({
                'title': '데이터 레코드 수 적음',
                'severity': '🟡 중간',
                'description': f'전체 {total_rows}건의 데이터가 존재합니다. 통계적 신뢰성을 위해 더 많은 데이터가 권장됩니다.',
                'details': {
                    'total_rows': total_rows,
                    'recommended_min': 100
                }
            })

        return issues

    def _check_column_usability(self):
        """컬럼 유용성 검사"""
        issues = []

        for col in self.df.columns:
            non_null_count = self.df[col].notna().sum()
            total_count = len(self.df)

            if total_count == 0:
                continue

            # 값이 거의 없는 컬럼
            fill_rate = (non_null_count / total_count) * 100

            if fill_rate < 10:
                issues.append({
                    'title': f'컬럼 "{col}"의 데이터 부족',
                    'severity': '🔴 높음',
                    'description': f'전체 {total_count}건 중 {non_null_count}건({fill_rate:.1f}%)만 값이 존재합니다. 활용도가 매우 낮습니다.',
                    'details': {
                        'column': col,
                        'fill_rate': round(fill_rate, 1),
                        'non_null_count': int(non_null_count),
                        'total_count': total_count
                    }
                })
            elif fill_rate < 30:
                issues.append({
                    'title': f'컬럼 "{col}"의 값 채워짐 비율 낮음',
                    'severity': '🟡 중간',
                    'description': f'전체 {total_count}건 중 {non_null_count}건({fill_rate:.1f}%)만 값이 존재합니다.',
                    'details': {
                        'column': col,
                        'fill_rate': round(fill_rate, 1),
                        'non_null_count': int(non_null_count),
                        'total_count': total_count
                    }
                })

        return issues

    def _check_data_diversity(self):
        """데이터 다양성 검사"""
        issues = []

        for col in self.df.columns:
            non_null = self.df[col].dropna()

            if len(non_null) == 0:
                continue

            unique_count = non_null.nunique()
            total_count = len(non_null)

            # 다양성이 너무 낮은 경우 (모든 값이 거의 동일)
            diversity_rate = (unique_count / total_count) * 100

            if diversity_rate < 1 and total_count > 10:
                issues.append({
                    'title': f'컬럼 "{col}"의 데이터 다양성 부족',
                    'severity': '🟡 중간',
                    'description': f'전체 {total_count}건 중 유니크 값이 {unique_count}개({diversity_rate:.2f}%)만 존재합니다.',
                    'details': {
                        'column': col,
                        'unique_count': unique_count,
                        'total_count': total_count,
                        'diversity_rate': round(diversity_rate, 2),
                        'top_values': list(non_null.value_counts().head(5).to_dict().items())
                    }
                })

            # 카디널리티가 너무 높은 경우 (ID나 고유값이 아닌데 모든 값이 다른 경우)
            elif diversity_rate > 95 and total_count > 100:
                # ID나 고유 식별자로 보이지 않는 경우
                if not any(keyword in col.lower() for keyword in ['id', 'key', 'uuid', 'guid', '번호', 'no']):
                    issues.append({
                        'title': f'컬럼 "{col}"의 카디널리티 과다',
                        'severity': '🟢 낮음',
                        'description': f'전체 {total_count}건 중 유니크 값이 {unique_count}개({diversity_rate:.2f}%)로 매우 높습니다. 분류나 그룹화가 어려울 수 있습니다.',
                        'details': {
                            'column': col,
                            'unique_count': unique_count,
                            'total_count': total_count,
                            'diversity_rate': round(diversity_rate, 2)
                        }
                    })

        return issues

    def _calculate_score(self, total_rows, usable_cols, total_cols, issue_count):
        """점수 계산 (엄격한 기준)"""
        base_score = 100

        # 데이터 양 기반 점수 (더 엄격하게)
        if total_rows < 10:
            base_score -= 40  # 30 -> 40
        elif total_rows < 100:
            base_score -= 20  # 15 -> 20
        elif total_rows < 1000:
            base_score -= 10  # 5 -> 10

        # 컬럼 유용성 기반 점수 (더 엄격하게)
        if total_cols > 0:
            col_usability = (usable_cols / total_cols) * 100
            if col_usability < 50:
                base_score -= 30  # 20 -> 30
            elif col_usability < 75:
                base_score -= 15  # 10 -> 15

        # 이슈 개수 기반 감점 (3 -> 8)
        issue_penalty = min(issue_count * 8, 40)
        total_score = base_score - issue_penalty

        # 데이터가 너무 적으면 추가 감점
        if total_rows < 10:
            total_score *= 0.6

        return round(max(0, total_score), 2)
