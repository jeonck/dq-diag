"""
유효성 진단 모듈
Validity Checker Module

데이터의 형식, 도메인, 참조 무결성 등의 유효성을 진단합니다.
"""

import pandas as pd
import numpy as np
import re
from datetime import datetime


class ValidityChecker:
    def __init__(self, df):
        self.df = df
        self.name = "유효성 (Validity)"

    def check(self):
        """유효성 진단 실행"""
        issues = []
        metrics = {}

        # 1. 데이터 형식 유효성 검사
        format_issues = self._check_format_validity()
        issues.extend(format_issues)

        # 2. 도메인 값 유효성 검사
        domain_issues = self._check_domain_validity()
        issues.extend(domain_issues)

        # 3. 참조 무결성 검사
        ref_issues = self._check_referential_integrity()
        issues.extend(ref_issues)

        # 4. 논리적 관계 규칙 검사
        logic_issues = self._check_logical_rules()
        issues.extend(logic_issues)

        # 메트릭 계산
        total_validations = len(self.df.columns) * 4  # 4 가지 검사 항목
        invalid_count = sum([issue['details'].get('error_count', 1) for issue in issues])
        validity_rate = ((total_validations - invalid_count) / total_validations * 100) if total_validations > 0 else 0

        metrics['유효성 비율'] = f"{validity_rate:.2f}%"
        metrics['검증된 컬럼 수'] = len(self.df.columns)
        metrics['전체 검증 항목'] = total_validations

        # 점수 계산
        score = self._calculate_score(validity_rate, len(issues))

        return {
            'name': self.name,
            'score': score,
            'issues': issues,
            'metrics': metrics
        }

    def _check_format_validity(self):
        """데이터 형식 유효성 검사"""
        issues = []

        for col in self.df.columns:
            if self.df[col].dtype == 'object':
                non_null = self.df[col].dropna()

                if len(non_null) == 0:
                    continue

                # 이메일 형식 검사
                if any(keyword in col.lower() for keyword in ['email', '이메일', 'mail']):
                    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    invalid_mask = ~non_null.astype(str).str.match(email_pattern)
                    invalid_count = invalid_mask.sum()

                    if invalid_count > 0:
                        issues.append({
                            'title': f'컬럼 "{col}"의 이메일 형식 오류',
                            'severity': '🟡 중간',
                            'description': f'유효하지 않은 이메일 형식이 {invalid_count}건 발견되었습니다.',
                            'details': {
                                'column': col,
                                'error_count': int(invalid_count),
                                'format_type': '이메일'
                            }
                        })

                # 날짜 형식 검사
                if any(keyword in col.lower() for keyword in ['date', 'dt', '일자', '날짜']):
                    invalid_dates = []
                    for val in non_null:
                        try:
                            pd.to_datetime(val)
                        except:
                            invalid_dates.append(val)

                    if invalid_dates:
                        issues.append({
                            'title': f'컬럼 "{col}"의 날짜 형식 오류',
                            'severity': '🔴 높음',
                            'description': f'유효하지 않은 날짜 형식이 {len(invalid_dates)}건 발견되었습니다.',
                            'details': {
                                'column': col,
                                'error_count': len(invalid_dates),
                                'format_type': '날짜',
                                'examples': invalid_dates[:10]
                            }
                        })

                # 전화번호 형식 검사
                if any(keyword in col.lower() for keyword in ['phone', 'tel', '전화', '연락처']):
                    phone_pattern = r'^[\d\-\(\)\+\s]+$'
                    invalid_mask = ~non_null.astype(str).str.match(phone_pattern)
                    invalid_count = invalid_mask.sum()

                    if invalid_count > 0:
                        issues.append({
                            'title': f'컬럼 "{col}"의 전화번호 형식 오류',
                            'severity': '🟡 중간',
                            'description': f'유효하지 않은 전화번호 형식이 {invalid_count}건 발견되었습니다.',
                            'details': {
                                'column': col,
                                'error_count': int(invalid_count),
                                'format_type': '전화번호'
                            }
                        })

        return issues

    def _check_domain_validity(self):
        """도메인 값 유효성 검사"""
        issues = []

        for col in self.df.columns:
            # Y/N 여부 컬럼 검사
            if any(keyword in col.lower() for keyword in ['yn', '여부', '유무']):
                valid_values = {'Y', 'N', 'y', 'n', '1', '0', 'true', 'false', 'True', 'False'}
                invalid_mask = ~self.df[col].isin(valid_values) & self.df[col].notna()
                invalid_count = invalid_mask.sum()

                if invalid_count > 0:
                    invalid_values = self.df.loc[invalid_mask, col].unique()
                    issues.append({
                        'title': f'컬럼 "{col}"의 도메인 값 오류',
                        'severity': '🔴 높음',
                        'description': f'유효하지 않은 도메인 값이 {invalid_count}건 발견되었습니다.',
                        'details': {
                            'column': col,
                            'error_count': int(invalid_count),
                            'invalid_values': list(invalid_values)[:10],
                            'valid_values': list(valid_values)
                        }
                    })

            # 성별 코드 검사
            if any(keyword in col.lower() for keyword in ['gender', 'sex', '성별']):
                valid_values = {'M', 'F', 'm', 'f', '남', '여', '남자', '여자', '1', '2'}
                invalid_mask = ~self.df[col].isin(valid_values) & self.df[col].notna()
                invalid_count = invalid_mask.sum()

                if invalid_count > 0:
                    invalid_values = self.df.loc[invalid_mask, col].unique()
                    issues.append({
                        'title': f'컬럼 "{col}"의 성별 코드 오류',
                        'severity': '🔴 높음',
                        'description': f'유효하지 않은 성별 코드가 {invalid_count}건 발견되었습니다.',
                        'details': {
                            'column': col,
                            'error_count': int(invalid_count),
                            'invalid_values': list(invalid_values)[:10],
                            'valid_values': list(valid_values)
                        }
                    })

        return issues

    def _check_referential_integrity(self):
        """참조 무결성 검사"""
        issues = []

        # 외래키로 추정되는 컬럼 찾기
        for col in self.df.columns:
            if any(keyword in col.lower() for keyword in ['id', 'code', 'no', '번호', '코드']):
                # ID 컬럼이 다른 테이블을 참조할 것으로 추정
                # 실제 참조 테이블이 없으므로 NULL 비율만 확인
                null_count = self.df[col].isnull().sum()
                null_rate = (null_count / len(self.df)) * 100

                if null_rate > 20:
                    issues.append({
                        'title': f'컬럼 "{col}"의 참조값 누락',
                        'severity': '🟡 중간',
                        'description': f'참조해야 할 값이 {null_count}건 ({null_rate:.2f}%) 누락되었습니다.',
                        'details': {
                            'column': col,
                            'error_count': int(null_count),
                            'null_rate': round(null_rate, 2)
                        }
                    })

        return issues

    def _check_logical_rules(self):
        """논리적 관계 규칙 검사"""
        issues = []

        # 시작일 < 종료일 검사
        start_cols = [col for col in self.df.columns if any(keyword in col.lower() for keyword in ['시작', 'start', 'from'])]
        end_cols = [col for col in self.df.columns if any(keyword in col.lower() for keyword in ['종료', 'end', 'to'])]

        for start_col in start_cols:
            for end_col in end_cols:
                try:
                    start_dates = pd.to_datetime(self.df[start_col], errors='coerce')
                    end_dates = pd.to_datetime(self.df[end_col], errors='coerce')

                    invalid_mask = (start_dates > end_dates) & start_dates.notna() & end_dates.notna()
                    invalid_count = invalid_mask.sum()

                    if invalid_count > 0:
                        issues.append({
                            'title': f'시작-종료 날짜 논리 오류',
                            'severity': '🔴 높음',
                            'description': f'"{start_col}"이 "{end_col}"보다 늦은 데이터가 {invalid_count}건 발견되었습니다.',
                            'details': {
                                'start_column': start_col,
                                'end_column': end_col,
                                'error_count': int(invalid_count)
                            }
                        })
                except:
                    pass

        # 계산식 검증 (총액 = 단가 × 수량)
        amount_cols = [col for col in self.df.columns if any(keyword in col.lower() for keyword in ['총액', 'total', 'amount', '금액'])]
        price_cols = [col for col in self.df.columns if any(keyword in col.lower() for keyword in ['단가', 'price', '가격'])]
        qty_cols = [col for col in self.df.columns if any(keyword in col.lower() for keyword in ['수량', 'qty', 'quantity'])]

        for amount_col in amount_cols:
            for price_col in price_cols:
                for qty_col in qty_cols:
                    try:
                        amount = pd.to_numeric(self.df[amount_col], errors='coerce')
                        price = pd.to_numeric(self.df[price_col], errors='coerce')
                        qty = pd.to_numeric(self.df[qty_col], errors='coerce')

                        calculated = price * qty
                        invalid_mask = (amount.notna() & price.notna() & qty.notna() & 
                                       (amount != calculated))
                        invalid_count = invalid_mask.sum()

                        if invalid_count > 0:
                            issues.append({
                                'title': f'계산식 오류: {amount_col} ≠ {price_col} × {qty_col}',
                                'severity': '🔴 높음',
                                'description': f'총액이 단가 × 수량과 일치하지 않는 데이터가 {invalid_count}건 발견되었습니다.',
                                'details': {
                                    'amount_column': amount_col,
                                    'price_column': price_col,
                                    'qty_column': qty_col,
                                    'error_count': int(invalid_count)
                                }
                            })
                    except:
                        pass

        return issues

    def _calculate_score(self, validity_rate, issue_count):
        """점수 계산"""
        # 유효성 비율 기반 점수 (60%)
        base_score = validity_rate * 0.6

        # 이슈 개수 기반 감점 (40%)
        issue_penalty = min(issue_count * 10, 40)
        issue_score = 40 - issue_penalty

        total_score = base_score + issue_score

        # 유효성이 낮으면 추가 감점
        if validity_rate < 50:
            total_score *= 0.5
        elif validity_rate < 70:
            total_score *= 0.7

        return round(max(0, total_score), 2)
