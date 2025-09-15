# 한국 공휴일 패키지 (kr_holidays)

캘린더 등에 활용하기 편한 **평일, 주말, 공휴일, 대체공휴일** 정보를 제공하는 Python 패키지입니다.

[![PyPI version](https://badge.fury.io/py/kr-holidays.svg)](https://badge.fury.io/py/kr-holidays)
[![Python versions](https://img.shields.io/pypi/pyversions/kr-holidays.svg)](https://pypi.org/project/kr-holidays/)

## ✨ 주요 기능

- 🗓️ **한국 공휴일 정보**: 법정공휴일, 대체공휴일 완벽 지원
- 📅 **다양한 날짜 형식**: 문자열, date 객체 모두 지원
- ⚡ **빠른 조회**: 메모리 캐싱으로 최적화된 성능
- 🔧 **편리한 API**: 간단한 함수부터 고급 클래스까지
- 📊 **업무일 계산**: 근무일 수 계산, 영업일 더하기 등

## 🔧 설치

### 최신 버전 설치
```bash
# pip 사용
pip install kr_holidays

# uv 사용 (권장)
uv add kr_holidays
```

### 특정 버전 설치
```bash
# pip 사용
pip install kr_holidays==1.0.0

# uv 사용
uv add kr_holidays==1.0.0
```

## 🚀 빠른 시작

### 기본 사용법
```python
from kr_holidays import is_holiday, get_holidays, is_working_day

# 공휴일 확인
print(is_holiday('2024-01-01'))  # True (신정)
print(is_holiday('2024-05-06'))  # True (어린이날 대체공휴일)
print(is_holiday('2024-01-02'))  # False

# 주말/근무일 확인
print(is_working_day('2024-01-02'))  # True (화요일, 공휴일 아님)

# 연도별 공휴일 조회
holidays_2024 = get_holidays(2024)
print(f"2024년 공휴일: {len(holidays_2024)}개")
```

### 고급 사용법
```python
from kr_holidays import KoreanHolidays

kh = KoreanHolidays()

# 다음 공휴일 찾기
next_holiday = kh.get_next_holiday('2024-01-02')
print(f"다음 공휴일: {next_holiday}")

# 근무일 계산
working_days = kh.count_working_days('2024-01-01', '2024-01-31')
print(f"1월 근무일: {working_days}일")

# 근무일 더하기 (공휴일/주말 제외)
target_date = kh.add_working_days('2024-01-01', 10)  # 1/1부터 10 근무일 후
print(f"신정부터 10 근무일 후: {target_date}")

# 공휴일 이름 조회
holiday_name = kh.get_holiday_name('2024-05-06')
print(f"5월 6일: {holiday_name}")  # 어린이날 대체공휴일
```

### 월별 조회
```python
# 특정 월의 공휴일만
may_holidays = kh.get_holidays_in_month(2024, 5)
print("5월 공휴일:", may_holidays)

# 특정 월의 근무일만
may_workdays = kh.get_working_days_in_month(2024, 5)
print(f"5월 근무일: {len(may_workdays)}일")
```

## 📋 지원 데이터

### 포함된 공휴일
- **법정공휴일**: 신정, 삼일절, 어린이날, 현충일, 광복절, 개천절, 한글날, 성탄절
- **음력 공휴일**: 설날 연휴 (3일), 부처님오신날, 추석 연휴 (3일)  
- **대체공휴일**: 공휴일이 주말과 겹칠 때 평일로 대체
- **임시공휴일**: 정부에서 지정하는 특별 공휴일

### 지원 연도
- **2000년 ~ 2050년** (확장 가능)
- 공공데이터포털 API 기준 정확한 데이터

## 🛠️ 시스템 요구사항

- **Python**: 3.8, 3.9, 3.10, 3.11, 3.12
- **의존성**: 없음 (외부 라이브러리 불필요)
- **운영체제**: Windows, macOS, Linux 모두 지원

## 📚 API 문서

### 편의 함수 (권장)
```python
# 날짜 확인
is_holiday(date)          # 공휴일 여부
is_weekend(date)          # 주말 여부  
is_working_day(date)      # 근무일 여부

# 데이터 조회
get_holidays(year)        # 연도별 공휴일 목록
get_holiday_name(date)    # 공휴일 이름
get_next_holiday(date)    # 다음 공휴일

# 근무일 계산
count_working_days(start, end)    # 기간 내 근무일 수
add_working_days(start, days)     # 근무일 더하기
```

### KoreanHolidays 클래스
```python
kh = KoreanHolidays()

# 모든 편의 함수 + 추가 기능
kh.get_holidays_in_month(year, month)     # 월별 공휴일
kh.get_working_days_in_month(year, month) # 월별 근무일  
kh.get_year_summary(year)                 # 연도 요약 정보
```

## 🔄 버전 호환성

| 버전 | Python 지원 | 주요 변경사항 |
|------|-------------|---------------|
| 1.0.0 | 3.8 ~ 3.12 | 초기 릴리스 |

## 📝 변경 로그

### v1.0.0 (2024-09-01)  
- 🎉 초기 릴리스
- ✅ 기본 공휴일 조회 기능
- ✅ 대체공휴일 지원
- ✅ 근무일 계산 기능

## ⚠️ 알려진 이슈

- Python 3.7 이하 버전은 지원하지 않습니다 (EOL)
- 2000년 이전 연도 데이터 | 2050년 이후 연도 데이터는 현재 미지원 (추후 확장 예정입니다!)

## 🤝 기여하기

버그 리포트나 기능 제안은 언제나 환영합니다!

- 이슈 제출: [GitHub Issues](https://github.com/g-rebels/kr-holiday/issues)
- 기능 제안: [GitHub Discussions](https://github.com/g-rebels/kr-holiday/discussions)

## 📄 라이센스

MIT License - 자유롭게 사용하세요!

## 🙏 감사 인사

이 패키지는 [공공데이터포털](https://www.data.go.kr/)의 공휴일 정보를 활용하여 개발되었습니다.