"""
보안성 진단 모듈
Security Checker Module

개인정보, 민감정보, 접근제한 등의 보안성을 진단합니다.
"""

import pandas as pd
import numpy as np
import re


class SecurityChecker:
    def __init__(self, df):
        self.df = df
        self.name = "보안성 (Security)"

    def check(self):
        """보안성 진단 실행"""
        issues = []
        metrics = {}

        # 1. 개인정보 노출 검사
        pii_issues = self._check_personal_info()
        issues.extend(pii_issues)

        # 2. 민감정보 검사
        sensitive_issues = self._check_sensitive_info()
        issues.extend(sensitive_issues)

        # 3. 암호화 필요 데이터 검사
        encryption_issues = self._check_encryption_needed()
        issues.extend(encryption_issues)

        # 메트릭 계산
        sensitive_cols = len([issue for issue in issues if '개인정보' in issue['title'] or '민감정보' in issue['title']])

        metrics['민감 컬럼 수'] = sensitive_cols
        metrics['전체 컬럼 수'] = len(self.df.columns)
        metrics['보안 위험도'] = '높음' if sensitive_cols > 3 else ('중간' if sensitive_cols > 0 else '낮음')

        # 점수 계산
        score = self._calculate_score(sensitive_cols, len(issues))

        return {
            'name': self.name,
            'score': score,
            'issues': issues,
            'metrics': metrics
        }

    def _check_personal_info(self):
        """개인정보 노출 검사"""
        issues = []

        pii_patterns = {
            '주민등록번호': r'\d{6}-\d{7}',
            '이메일': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            '전화번호': r'01\d-\d{3,4}-\d{4}',
            '신용카드': r'\d{4}-\d{4}-\d{4}-\d{4}'
        }

        for col in self.df.columns:
            # 컬럼명으로 개인정보 추정
            if any(keyword in col.lower() for keyword in ['주민', 'ssn', 'rrn', '이메일', 'email', '전화', 'phone', 'tel', '카드', 'card']):

                if self.df[col].dtype == 'object':
                    non_null = self.df[col].dropna()

                    if len(non_null) > 0:
                        # 패턴 매칭
                        for pii_type, pattern in pii_patterns.items():
                            matches = non_null.astype(str).str.contains(pattern, regex=True, na=False).sum()

                            if matches > 0:
                                issues.append({
                                    'title': f'컬럼 "{col}"에 {pii_type} 노출',
                                    'severity': '🔴 높음',
                                    'description': f'개인정보({pii_type})가 평문으로 {matches}건 저장되어 있습니다. 암호화 또는 마스킹이 필요합니다.',
                                    'details': {
                                        'column': col,
                                        'pii_type': pii_type,
                                        'count': int(matches)
                                    }
                                })
                                break

        return issues

    def _check_sensitive_info(self):
        """민감정보 검사"""
        issues = []

        sensitive_keywords = {
            '비밀번호': ['password', 'pwd', '비밀번호', '패스워드'],
            '계좌정보': ['account', '계좌', 'bank'],
            '소득정보': ['income', '소득', '연봉', 'salary'],
            '건강정보': ['health', '건강', '질병', 'disease'],
            '위치정보': ['location', 'gps', '위치', '좌표', 'latitude', 'longitude']
        }

        for col in self.df.columns:
            for info_type, keywords in sensitive_keywords.items():
                if any(keyword in col.lower() for keyword in keywords):
                    # 비밀번호는 해싱되어야 함
                    if info_type == '비밀번호':
                        if self.df[col].dtype == 'object':
                            non_null = self.df[col].dropna()
                            if len(non_null) > 0:
                                # 평문 비밀번호로 추정되는 값 (길이가 너무 짧거나 패턴이 단순한 경우)
                                simple_passwords = non_null[non_null.astype(str).str.len() < 20].count()

                                if simple_passwords > 0:
                                    issues.append({
                                        'title': f'컬럼 "{col}"의 비밀번호 보안 취약',
                                        'severity': '🔴 높음',
                                        'description': f'비밀번호가 평문 또는 약한 해싱으로 저장되어 있을 가능성이 있습니다.',
                                        'details': {
                                            'column': col,
                                            'info_type': info_type,
                                            'risk': '평문 또는 약한 해싱'
                                        }
                                    })
                    else:
                        issues.append({
                            'title': f'컬럼 "{col}"에 민감정보 포함',
                            'severity': '🟡 중간',
                            'description': f'{info_type}가 포함되어 있습니다. 접근 권한 및 암호화 정책을 확인하세요.',
                            'details': {
                                'column': col,
                                'info_type': info_type
                            }
                        })
                    break

        return issues

    def _check_encryption_needed(self):
        """암호화 필요 데이터 검사"""
        issues = []

        # 숫자만으로 구성된 긴 문자열 (카드번호, 계좌번호 등으로 추정)
        for col in self.df.columns:
            if self.df[col].dtype == 'object':
                non_null = self.df[col].dropna()

                if len(non_null) > 0:
                    # 10자리 이상의 숫자로만 구성된 값
                    numeric_only = non_null.astype(str).str.match(r'^\d{10,}$').sum()

                    if numeric_only > 0:
                        issues.append({
                            'title': f'컬럼 "{col}"의 암호화 필요성 검토',
                            'severity': '🟡 중간',
                            'description': f'10자리 이상의 숫자로만 구성된 값이 {numeric_only}건 있습니다. 계좌번호 또는 카드번호일 경우 암호화가 필요합니다.',
                            'details': {
                                'column': col,
                                'count': int(numeric_only)
                            }
                        })

        return issues

    def _calculate_score(self, sensitive_count, issue_count):
        """점수 계산 (엄격한 기준)"""
        # 민감정보 개수 기반 감점 (10 -> 15)
        sensitive_penalty = min(sensitive_count * 15, 60)

        # 이슈 개수 기반 감점 (5 -> 8)
        issue_penalty = min(issue_count * 8, 40)

        total_score = 100 - sensitive_penalty - issue_penalty

        # 고위험 이슈가 있으면 추가 감점
        if sensitive_count > 5:
            total_score *= 0.6
        elif sensitive_count > 3:
            total_score *= 0.8

        return round(max(0, total_score), 2)
