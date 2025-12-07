"""
유틸리티 함수 모듈
안전한 데이터 처리를 위한 헬퍼 함수들
"""

import pandas as pd
import numpy as np
import re


def safe_get_column_index(default_index, max_index):
    """Safely get column index, ensuring it's within bounds"""
    return min(max(0, default_index), max(0, max_index))


def safe_is_unique(series):
    """Safely check if a series has unique values, handling edge cases"""
    try:
        if series.dtype == 'object':
            # For object types, handle NaN values properly
            non_null_values = series.dropna()
            return non_null_values.is_unique and len(non_null_values) == len(series.dropna())
        return series.is_unique
    except:
        return True  # Default to unique if we can't determine


def safe_to_datetime(series):
    """Safely convert series to datetime"""
    try:
        return pd.to_datetime(series, errors='coerce')
    except:
        return series


def safe_email_pattern_check(series):
    """Safely check email patterns"""
    try:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if series.dtype == 'object':
            email_matches = series.str.contains(email_pattern, na=False, regex=True)
            invalid_emails = series[~series.str.match(email_pattern, na=False)]
            return email_matches.any(), invalid_emails
        return False, pd.Series(dtype=object)
    except:
        return False, pd.Series(dtype=object)


def safe_check_business_rules(df, col_name):
    """Safely apply business rules"""
    try:
        if col_name in df.columns and pd.api.types.is_numeric_dtype(df[col_name]):
            negative_values = df[df[col_name] < 0][col_name]
            return negative_values
        return pd.Series(dtype=object)
    except:
        return pd.Series(dtype=object)


def safe_outlier_detection(series):
    """
    Safely detect outliers using IQR method

    IQR (Interquartile Range) 방법:
    - Q1: 25번째 백분위수
    - Q3: 75번째 백분위수
    - IQR = Q3 - Q1
    - 이상치: Q1 - 1.5*IQR 미만 또는 Q3 + 1.5*IQR 초과
    """
    try:
        if pd.api.types.is_numeric_dtype(series):
            series_numeric = pd.to_numeric(series, errors='coerce')
            series_clean = series_numeric.dropna()

            if len(series_clean) < 4:  # Need at least 4 points for IQR
                return pd.Series(dtype='object', name=series.name if hasattr(series, 'name') else None)

            Q1 = series_clean.quantile(0.25)
            Q3 = series_clean.quantile(0.75)
            IQR = Q3 - Q1

            if IQR == 0:  # All values are the same
                return pd.Series(dtype='object', name=series.name if hasattr(series, 'name') else None)

            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            series_as_numeric = pd.to_numeric(series, errors='coerce')
            outlier_mask = (series_as_numeric < lower_bound) | (series_as_numeric > upper_bound)
            outliers = series[outlier_mask]

            return outliers
        return pd.Series(dtype='object', name=series.name if hasattr(series, 'name') else None)
    except:
        return pd.Series(dtype='object', name=series.name if hasattr(series, 'name') else None)


def calculate_uniqueness_metrics(series):
    """
    Calculate detailed uniqueness metrics

    Returns:
        dict: {
            'total_count': 전체 개수,
            'unique_count': 고유값 개수,
            'unique_once_count': 1회만 나타나는 값 개수,
            'duplicate_occurrences': 중복 발생 총 횟수,
            'uniqueness_rate': 고유성 비율 (%)
        }
    """
    try:
        total_count = len(series)
        unique_count = series.nunique()

        value_counts = series.value_counts()
        unique_once_count = (value_counts == 1).sum()
        duplicate_occurrences = value_counts[value_counts > 1].sum() if not value_counts.empty else 0
        uniqueness_rate = (unique_once_count / total_count * 100) if total_count > 0 else 0

        return {
            'total_count': total_count,
            'unique_count': unique_count,
            'unique_once_count': unique_once_count,
            'duplicate_occurrences': int(duplicate_occurrences),
            'uniqueness_rate': round(uniqueness_rate, 2)
        }
    except:
        return {
            'total_count': len(series),
            'unique_count': 0,
            'unique_once_count': 0,
            'duplicate_occurrences': 0,
            'uniqueness_rate': 0
        }


def detect_pattern_deviation(series):
    """
    Detect pattern deviations in data

    For numeric data: Uses Z-score (values with |Z| > 3)
    For text data: Analyzes length variations
    """
    try:
        if pd.api.types.is_numeric_dtype(series):
            # 수치형 데이터: Z-score 기반 이상치
            if series.count() > 0:
                mean_val = series.mean()
                std_val = series.std()
                if std_val and std_val != 0:
                    z_scores = ((series - mean_val) / std_val).abs()
                    return (z_scores > 3).sum()
            return 0

        elif pd.api.types.is_object_dtype(series):
            # 텍스트 데이터: 길이 분석
            lengths = series.astype(str).str.len()
            if len(lengths) > 0:
                mean_len = lengths.mean()
                std_len = lengths.std()
                if std_len and std_len != 0:
                    z_scores = ((lengths - mean_len) / std_len).abs()
                    return (z_scores > 3).sum()
            return 0

        return 0
    except:
        return 0


def format_percentage(value, total):
    """Safely format percentage"""
    try:
        if total == 0:
            return "0.00%"
        return f"{(value / total * 100):.2f}%"
    except:
        return "N/A"


def get_severity_color(severity):
    """Get color for severity level"""
    severity_colors = {
        '🔴 높음': 'red',
        '🟡 중간': 'orange',
        '🟢 낮음': 'green'
    }
    return severity_colors.get(severity, 'gray')


def get_grade_color(grade):
    """Get color for quality grade"""
    if '우수' in grade:
        return 'green'
    elif '양호' in grade:
        return 'blue'
    elif '보통' in grade:
        return 'orange'
    else:
        return 'red'
