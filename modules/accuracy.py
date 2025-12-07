"""
정확성 진단 모듈
Accuracy Checker Module

입력값, 업무규칙, 범위/형식, 참조관계, 계산식 등의 정확성을 진단합니다.
"""

import pandas as pd
import numpy as np
import re
from datetime import datetime


class AccuracyChecker:
    def __init__(self, df):
        self.df = df
        self.name = "정확성 (Accuracy)"

    def check(self):
        """정확성 진단 실행"""
        issues = []
        metrics = {}

        # 1. 도메인 정확성 검사
        domain_issues = self._check_domain_accuracy()
        issues.extend(domain_issues)

        # 2. 범위 정확성 검사
        range_issues = self._check_range_accuracy()
        issues.extend(range_issues)

        # 3. 형식 정확성 검사
        format_issues = self._check_format_accuracy()
        issues.extend(format_issues)

        # 4. 날짜 유효성 검사
        date_issues = self._check_date_validity()
        issues.extend(date_issues)

        # 5. 논리적 일관성 검사
        logic_issues = self._check_logical_consistency()
        issues.extend(logic_issues)

        # 메트릭 계산
        total_values = len(self.df) * len(self.df.columns)
        invalid_count = sum([issue['details'].get('error_count', 0) for issue in issues])

        accuracy_rate = ((total_values - invalid_count) / total_values * 100) if total_values > 0 else 0

        metrics['정확성 비율'] = f"{accuracy_rate:.2f}%"
        metrics['오류 데이터 수'] = f"{invalid_count:,}"
        metrics['전체 데이터 수'] = f"{total_values:,}"

        # 점수 계산
        score = self._calculate_score(accuracy_rate, len(issues))

        return {
            'name': self.name,
            'score': score,
            'issues': issues,
            'metrics': metrics
        }

    def _check_domain_accuracy(self):
        """도메인(여부, 코드 등) 정확성 검사"""
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
                        'title': f'컬럼 "{col}"의 여부 도메인 오류',
                        'severity': '🔴 높음',
                        'description': f'유효하지 않은 값이 {invalid_count}건 발견되었습니다.',
                        'details': {
                            'column': col,
                            'error_count': int(invalid_count),
                            'invalid_values': list(invalid_values)[:10],
                            'valid_values': list(valid_values)
                        }
                    })

        return issues

    def _check_range_accuracy(self):
        """범위 정확성 검사"""
        issues = []

        for col in self.df.columns:
            # 숫자형 컬럼만 검사
            if pd.api.types.is_numeric_dtype(self.df[col]):

                # 음수가 있으면 안되는 컬럼
                if any(keyword in col.lower() for keyword in ['수량', '건수', '횟수', 'count', 'quantity', '나이', 'age']):
                    negative_count = (self.df[col] < 0).sum()

                    if negative_count > 0:
                        issues.append({
                            'title': f'컬럼 "{col}"에 음수 값 존재',
                            'severity': '🔴 높음',
                            'description': f'수량/건수 컬럼에 음수 값이 {negative_count}건 발견되었습니다.',
                            'details': {
                                'column': col,
                                'error_count': int(negative_count),
                                'min_value': float(self.df[col].min())
                            }
                        })

                # 퍼센트/비율 컬럼 (0-100 또는 0-1 범위)
                if any(keyword in col.lower() for keyword in ['율', 'rate', 'ratio', 'percent', '%']):
                    out_of_range = ((self.df[col] < 0) | (self.df[col] > 100)).sum()

                    if out_of_range > 0:
                        issues.append({
                            'title': f'컬럼 "{col}"의 범위 오류',
                            'severity': '🔴 높음',
                            'description': f'비율 값이 유효 범위(0-100)를 벗어난 데이터가 {out_of_range}건 발견되었습니다.',
                            'details': {
                                'column': col,
                                'error_count': int(out_of_range),
                                'min_value': float(self.df[col].min()),
                                'max_value': float(self.df[col].max())
                            }
                        })

                # 나이 컬럼 (0-150 범위)
                if any(keyword in col.lower() for keyword in ['나이', 'age']):
                    out_of_range = ((self.df[col] < 0) | (self.df[col] > 150)).sum()

                    if out_of_range > 0:
                        issues.append({
                            'title': f'컬럼 "{col}"의 나이 범위 오류',
                            'severity': '🔴 높음',
                            'description': f'나이 값이 유효 범위(0-150)를 벗어난 데이터가 {out_of_range}건 발견되었습니다.',
                            'details': {
                                'column': col,
                                'error_count': int(out_of_range),
                                'min_value': float(self.df[col].min()),
                                'max_value': float(self.df[col].max())
                            }
                        })

                # 연도 컬럼 범위 검사
                if any(keyword in col.lower() for keyword in ['년도', 'year', '연도', 'join_year', 'birth_year', '가입년도', '생년']):
                    from datetime import datetime
                    current_year = datetime.now().year

                    # 컬럼 종류에 따라 다른 범위 적용
                    if any(keyword in col.lower() for keyword in ['birth', '생년', '출생']):
                        # 출생 연도: 1900 ~ 현재
                        min_year, max_year = 1900, current_year
                        range_desc = f'{min_year}-{max_year}'
                    elif any(keyword in col.lower() for keyword in ['join', '가입', '등록', 'register']):
                        # 가입 연도: 최근 10년 ~ 현재 (그 이전은 너무 오래됨)
                        min_year, max_year = current_year - 10, current_year
                        range_desc = f'{min_year}-{max_year} (최근 10년)'
                    else:
                        # 일반 연도: 1900 ~ 현재+1
                        min_year, max_year = 1900, current_year + 1
                        range_desc = f'{min_year}-{max_year}'

                    out_of_range = ((self.df[col] < min_year) | (self.df[col] > max_year)).sum()

                    if out_of_range > 0:
                        # 과거/미래 분리
                        too_old = (self.df[col] < min_year).sum()
                        too_new = (self.df[col] > max_year).sum()

                        detail_msg = []
                        if too_old > 0:
                            detail_msg.append(f'과거 연도 {too_old}건')
                        if too_new > 0:
                            detail_msg.append(f'미래 연도 {too_new}건')

                        issues.append({
                            'title': f'컬럼 "{col}"의 연도 범위 오류',
                            'severity': '🔴 높음',
                            'description': f'연도 값이 유효 범위({range_desc})를 벗어난 데이터가 {out_of_range}건 발견되었습니다. ({", ".join(detail_msg)})',
                            'details': {
                                'column': col,
                                'error_count': int(out_of_range),
                                'too_old_count': int(too_old),
                                'too_new_count': int(too_new),
                                'min_value': float(self.df[col].min()),
                                'max_value': float(self.df[col].max()),
                                'valid_range': range_desc
                            }
                        })

        return issues

    def _check_format_accuracy(self):
        """형식 정확성 검사"""
        issues = []

        for col in self.df.columns:
            if self.df[col].dtype == 'object':
                # 한글 문자 유효성 검사
                if any(keyword in col.lower() for keyword in ['이름', 'name', '성명', '직위', '부서', '명칭']):
                    non_null = self.df[col].dropna()

                    if len(non_null) > 0:
                        # 비완성형 한글, 특수문자 혼입 검사
                        import re
                        invalid_korean = []

                        for val in non_null:
                            val_str = str(val).strip()
                            if not val_str:
                                continue

                            # 비완성형 한글 검사 (ㄱ-ㅎ, ㅏ-ㅣ 단독)
                            if re.search(r'[ㄱ-ㅎㅏ-ㅣ]', val_str):
                                invalid_korean.append(val_str)
                            # 유효하지 않은 문자열 패턴 (숫자만, 특수문자만 등)
                            elif re.match(r'^[^가-힣a-zA-Z]+$', val_str) and not val_str.isdigit():
                                invalid_korean.append(val_str)

                        if invalid_korean:
                            invalid_count = len(invalid_korean)
                            issues.append({
                                'title': f'컬럼 "{col}"의 한글 문자 유효성 오류',
                                'severity': '🔴 높음',
                                'description': f'비완성형 한글이나 유효하지 않은 문자열이 {invalid_count}건 발견되었습니다.',
                                'details': {
                                    'column': col,
                                    'error_count': invalid_count,
                                    'examples': list(set(invalid_korean))[:10]
                                }
                            })

                # 이메일 형식 검사
                if any(keyword in col.lower() for keyword in ['email', '이메일', 'mail']):
                    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    non_null = self.df[col].dropna()

                    if len(non_null) > 0:
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
                                    'examples': list(non_null[invalid_mask].head(5))
                                }
                            })

                # 전화번호 형식 검사
                if any(keyword in col.lower() for keyword in ['phone', 'tel', '전화', '연락처', '휴대폰']):
                    phone_pattern = r'^[\d\-\(\)\+\s]+$'
                    non_null = self.df[col].dropna()

                    if len(non_null) > 0:
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
                                    'examples': list(non_null[invalid_mask].head(5))
                                }
                            })

        return issues

    def _check_date_validity(self):
        """날짜 유효성 검사"""
        issues = []

        for col in self.df.columns:
            # 날짜 컬럼으로 추정되는 경우
            if any(keyword in col.lower() for keyword in ['date', 'dt', '일자', '날짜']):

                if self.df[col].dtype == 'object':
                    non_null = self.df[col].dropna()

                    if len(non_null) > 0:
                        invalid_dates = []

                        for val in non_null:
                            try:
                                # 다양한 형식으로 파싱 시도
                                pd.to_datetime(val)
                            except:
                                invalid_dates.append(val)

                        if invalid_dates:
                            issues.append({
                                'title': f'컬럼 "{col}"의 날짜 유효성 오류',
                                'severity': '🔴 높음',
                                'description': f'유효하지 않은 날짜 값이 {len(invalid_dates)}건 발견되었습니다.',
                                'details': {
                                    'column': col,
                                    'error_count': len(invalid_dates),
                                    'examples': invalid_dates[:10]
                                }
                            })

        return issues

    def _check_logical_consistency(self):
        """논리적 일관성 검사"""
        issues = []

        # 시작일 < 종료일 검사
        start_cols = [col for col in self.df.columns if any(keyword in col.lower() for keyword in ['시작', 'start', 'from', '등록', '착공'])]
        end_cols = [col for col in self.df.columns if any(keyword in col.lower() for keyword in ['종료', 'end', 'to', '완료', '준공'])]

        for start_col in start_cols:
            for end_col in end_cols:
                try:
                    start_dates = pd.to_datetime(self.df[start_col], errors='coerce')
                    end_dates = pd.to_datetime(self.df[end_col], errors='coerce')

                    # 둘 다 날짜로 변환 가능한 경우
                    if start_dates.notna().any() and end_dates.notna().any():
                        invalid_mask = (start_dates > end_dates) & start_dates.notna() & end_dates.notna()
                        invalid_count = invalid_mask.sum()

                        if invalid_count > 0:
                            issues.append({
                                'title': f'시작-종료 날짜 순서 오류',
                                'severity': '🔴 높음',
                                'description': f'"{start_col}"이 "{end_col}"보다 늦은 데이터가 {invalid_count}건 발견되었습니다. (예: 착공일자 > 준공일자)',
                                'details': {
                                    'start_column': start_col,
                                    'end_column': end_col,
                                    'error_count': int(invalid_count)
                                }
                            })
                except:
                    pass

        # 컬럼 간 논리관계 검사 (종속 관계)
        # 폐기일자가 있으면 폐기사유도 있어야 함
        discard_date_cols = [col for col in self.df.columns if any(keyword in col.lower() for keyword in ['폐기일', '삭제일', 'delete_date'])]
        discard_reason_cols = [col for col in self.df.columns if any(keyword in col.lower() for keyword in ['폐기사유', '폐기이유', '삭제사유', 'delete_reason'])]

        for date_col in discard_date_cols:
            for reason_col in discard_reason_cols:
                # 폐기일자가 NOT NULL인데 폐기사유가 NULL인 경우
                has_date = self.df[date_col].notna()
                missing_reason = self.df[reason_col].isna()

                if self.df[reason_col].dtype == 'object':
                    # 공백도 NULL로 취급
                    missing_reason = missing_reason | (self.df[reason_col].str.strip() == '')

                invalid_count = (has_date & missing_reason).sum()

                if invalid_count > 0:
                    issues.append({
                        'title': f'컬럼 간 논리관계 오류: {date_col} vs {reason_col}',
                        'severity': '🔴 높음',
                        'description': f'"{date_col}"가 존재하는데 "{reason_col}"가 누락된 데이터가 {invalid_count}건 발견되었습니다.',
                        'details': {
                            'date_column': date_col,
                            'reason_column': reason_col,
                            'error_count': int(invalid_count)
                        }
                    })

        return issues

    def _calculate_score(self, accuracy_rate, issue_count):
        """점수 계산 (엄격한 기준)"""
        # 정확성 비율 기반 점수 (60%)
        # 정확성에 더 민감하게 반응
        base_score = accuracy_rate * 0.6

        # 이슈 개수 기반 감점 (40%)
        # 이슈당 더 큰 감점 적용 (4 -> 10)
        issue_penalty = min(issue_count * 10, 40)
        issue_score = 40 - issue_penalty

        total_score = base_score + issue_score

        # 정확성이 낮으면 추가 감점
        if accuracy_rate < 50:
            total_score *= 0.5
        elif accuracy_rate < 70:
            total_score *= 0.7

        return round(max(0, total_score), 2)
