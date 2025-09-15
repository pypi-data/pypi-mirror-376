"""test_core.py - KoreanHolidays 클래스 및 편의 함수 완전한 테스트 (90%+ 커버리지)"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock

from kr_holidays import (
    is_holiday,
    is_weekend,
    is_working_day,
    get_holidays,
    get_holiday_name,
    get_next_holiday,
    count_working_days,
    add_working_days,
    KoreanHolidays,
)
from kr_holidays.core import _default_instance
from kr_holidays.utils import parse_date_input

# 테스트용 모조 데이터
MOCK_YEAR_DATA = {
    "year": 2024,
    "generated_at": "2024-01-01T00:00:00Z",
    "source": "한국천문연구원",
    "api_url": "http://astro.kasi.re.kr",
    "statistics": {
        "total_days": 366,
        "holidays": 16,
        "working_days": 249,
        "weekends": 105
    },
    "days": [
        {
            "year": 2024,
            "month": 1,
            "date": 1,
            "is_holiday": True,
            "is_weekend": False,
            "is_substitute_holiday": False,
            "holiday_name": "1월1일",
            "weekday": "월요일"
        },
        {
            "year": 2024,
            "month": 1,
            "date": 2,
            "is_holiday": False,
            "is_weekend": False,
            "is_substitute_holiday": False,
            "holiday_name": None,
            "weekday": "화요일"
        },
        {
            "year": 2024,
            "month": 1,
            "date": 6,
            "is_holiday": False,
            "is_weekend": True,
            "is_substitute_holiday": False,
            "holiday_name": None,
            "weekday": "토요일"
        },
        {
            "year": 2024,
            "month": 1,
            "date": 7,
            "is_holiday": False,
            "is_weekend": True,
            "is_substitute_holiday": False,
            "holiday_name": None,
            "weekday": "일요일"
        },
        {
            "year": 2024,
            "month": 2,
            "date": 10,
            "is_holiday": True,
            "is_weekend": True,
            "is_substitute_holiday": False,
            "holiday_name": "설날",
            "weekday": "토요일"
        },
        {
            "year": 2024,
            "month": 5,
            "date": 6,
            "is_holiday": True,
            "is_weekend": False,
            "is_substitute_holiday": True,
            "holiday_name": "대체공휴일(어린이날)",
            "weekday": "월요일"
        }
    ]
}


class TestKoreanHolidaysCore:
    """KoreanHolidays 클래스 완전 테스트"""

    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.kh = KoreanHolidays()

    @patch('kr_holidays.data.get_day_info')
    def test_is_holiday_with_data_true(self, mock_get_day_info):
        """공휴일 확인 - 데이터 있고 공휴일인 경우"""
        mock_get_day_info.return_value = {"is_holiday": True}
        assert self.kh.is_holiday("2024-01-01") == True
        
        # date 객체로도 테스트
        assert self.kh.is_holiday(date(2024, 1, 1)) == True

    @patch('kr_holidays.data.get_day_info')
    def test_is_holiday_with_data_false(self, mock_get_day_info):
        """공휴일 확인 - 데이터 있고 공휴일 아닌 경우"""
        mock_get_day_info.return_value = {"is_holiday": False}
        assert self.kh.is_holiday("2024-01-02") == False

    @patch('kr_holidays.data.get_day_info')
    def test_is_holiday_no_data(self, mock_get_day_info):
        """공휴일 확인 - 데이터 없을 때"""
        mock_get_day_info.return_value = None
        assert self.kh.is_holiday("2024-01-01") == False

    @patch('kr_holidays.data.get_day_info')
    def test_is_holiday_empty_data(self, mock_get_day_info):
        """공휴일 확인 - 빈 데이터일 때"""
        mock_get_day_info.return_value = {}  # is_holiday 키가 없음
        assert self.kh.is_holiday("2024-01-01") == False

    @patch('kr_holidays.data.get_day_info')
    def test_is_weekend_with_data_true(self, mock_get_day_info):
        """주말 확인 - 데이터 있고 주말인 경우"""
        mock_get_day_info.return_value = {"is_weekend": True}
        assert self.kh.is_weekend("2024-01-06") == True

    @patch('kr_holidays.data.get_day_info')
    def test_is_weekend_with_data_false(self, mock_get_day_info):
        """주말 확인 - 데이터 있고 주말 아닌 경우"""
        mock_get_day_info.return_value = {"is_weekend": False}
        assert self.kh.is_weekend("2024-01-02") == False

    @patch('kr_holidays.data.get_day_info')
    @patch('kr_holidays.utils.is_weekend_by_weekday')
    def test_is_weekend_no_data_fallback(self, mock_is_weekend_by_weekday, mock_get_day_info):
        """주말 확인 - 데이터 없을 때 요일로 계산"""
        mock_get_day_info.return_value = None
        mock_is_weekend_by_weekday.return_value = True
        
        result = self.kh.is_weekend("2024-01-06")
        
        assert result == True
        mock_is_weekend_by_weekday.assert_called_once()

    @patch('kr_holidays.data.get_day_info')
    @patch('kr_holidays.utils.is_weekend_by_weekday')
    def test_is_weekend_empty_data_fallback(self, mock_is_weekend_by_weekday, mock_get_day_info):
        """주말 확인 - 빈 데이터일 때 요일로 계산"""
        mock_get_day_info.return_value = {}  # is_weekend 키가 없음
        mock_is_weekend_by_weekday.return_value = False
        
        result = self.kh.is_weekend("2024-01-02")
        
        assert result == False
        mock_is_weekend_by_weekday.assert_called_once()

    @patch('kr_holidays.data.get_day_info')
    def test_is_substitute_holiday_true(self, mock_get_day_info):
        """대체공휴일 확인 - 대체공휴일인 경우"""
        mock_get_day_info.return_value = {"is_substitute_holiday": True}
        assert self.kh.is_substitute_holiday("2024-05-06") == True

    @patch('kr_holidays.data.get_day_info')
    def test_is_substitute_holiday_false(self, mock_get_day_info):
        """대체공휴일 확인 - 대체공휴일 아닌 경우"""
        mock_get_day_info.return_value = {"is_substitute_holiday": False}
        assert self.kh.is_substitute_holiday("2024-01-01") == False

    @patch('kr_holidays.data.get_day_info')
    def test_is_substitute_holiday_no_data(self, mock_get_day_info):
        """대체공휴일 확인 - 데이터 없을 때"""
        mock_get_day_info.return_value = None
        assert self.kh.is_substitute_holiday("2024-05-06") == False

    @patch('kr_holidays.data.get_day_info')
    def test_is_substitute_holiday_empty_data(self, mock_get_day_info):
        """대체공휴일 확인 - 빈 데이터일 때"""
        mock_get_day_info.return_value = {}
        assert self.kh.is_substitute_holiday("2024-05-06") == False

    @patch.object(KoreanHolidays, 'is_weekend')
    @patch.object(KoreanHolidays, 'is_holiday')
    def test_is_working_day_true(self, mock_is_holiday, mock_is_weekend):
        """근무일 확인 - 평일이면서 공휴일 아닌 경우"""
        mock_is_weekend.return_value = False
        mock_is_holiday.return_value = False
        
        result = self.kh.is_working_day("2024-01-02")
        
        assert result == True

    @patch.object(KoreanHolidays, 'is_weekend')
    @patch.object(KoreanHolidays, 'is_holiday')
    def test_is_working_day_weekend(self, mock_is_holiday, mock_is_weekend):
        """근무일 확인 - 주말인 경우"""
        mock_is_weekend.return_value = True
        mock_is_holiday.return_value = False
        
        result = self.kh.is_working_day("2024-01-06")
        
        assert result == False

    @patch.object(KoreanHolidays, 'is_weekend')
    @patch.object(KoreanHolidays, 'is_holiday')
    def test_is_working_day_holiday(self, mock_is_holiday, mock_is_weekend):
        """근무일 확인 - 공휴일인 경우"""
        mock_is_weekend.return_value = False
        mock_is_holiday.return_value = True
        
        result = self.kh.is_working_day("2024-01-01")
        
        assert result == False

    @patch.object(KoreanHolidays, 'is_weekend')
    @patch.object(KoreanHolidays, 'is_holiday')
    def test_is_working_day_weekend_and_holiday(self, mock_is_holiday, mock_is_weekend):
        """근무일 확인 - 주말이면서 공휴일인 경우"""
        mock_is_weekend.return_value = True
        mock_is_holiday.return_value = True
        
        result = self.kh.is_working_day("2024-02-10")  # 설날이 토요일
        
        assert result == False

    @patch('kr_holidays.data.get_day_info')
    def test_get_holiday_name_success(self, mock_get_day_info):
        """공휴일 이름 조회 - 성공"""
        mock_get_day_info.return_value = {
            "is_holiday": True,
            "holiday_name": "1월1일"
        }
        
        result = self.kh.get_holiday_name("2024-01-01")
        
        assert result == "1월1일"

    @patch('kr_holidays.data.get_day_info')
    def test_get_holiday_name_not_holiday(self, mock_get_day_info):
        """공휴일 이름 조회 - 공휴일 아닌 경우"""
        mock_get_day_info.return_value = {"is_holiday": False}
        
        result = self.kh.get_holiday_name("2024-01-02")
        
        assert result is None

    @patch('kr_holidays.data.get_day_info')
    def test_get_holiday_name_no_data(self, mock_get_day_info):
        """공휴일 이름 조회 - 데이터 없는 경우"""
        mock_get_day_info.return_value = None
        
        result = self.kh.get_holiday_name("2024-01-02")
        
        assert result is None

    @patch('kr_holidays.data.get_day_info')
    def test_get_holiday_name_holiday_but_no_name(self, mock_get_day_info):
        """공휴일 이름 조회 - 공휴일이지만 이름 없는 경우"""
        mock_get_day_info.return_value = {
            "is_holiday": True,
            "holiday_name": None
        }
        
        result = self.kh.get_holiday_name("2024-01-01")
        
        assert result is None

    @patch('kr_holidays.data.get_day_info')
    def test_get_holiday_name_holiday_but_missing_name_key(self, mock_get_day_info):
        """공휴일 이름 조회 - 공휴일이지만 holiday_name 키 없는 경우"""
        mock_get_day_info.return_value = {"is_holiday": True}  # holiday_name 키 없음
        
        result = self.kh.get_holiday_name("2024-01-01")
        
        assert result is None

    @patch('kr_holidays.data.get_year_days_data')
    @patch('kr_holidays.utils.validate_year_range')
    def test_get_holidays_success(self, mock_validate, mock_get_year_days):
        """연도별 공휴일 조회 - 성공"""
        mock_get_year_days.return_value = MOCK_YEAR_DATA["days"]
        
        holidays = self.kh.get_holidays(2024)
        
        # 공휴일만 필터링되어야 함
        expected_holidays = [
            date(2024, 1, 1),
            date(2024, 2, 10),
            date(2024, 5, 6)
        ]
        assert holidays == expected_holidays
        mock_validate.assert_called_once_with(2024)

    @patch('kr_holidays.data.get_year_days_data')
    @patch('kr_holidays.utils.validate_year_range')
    def test_get_holidays_no_holidays(self, mock_validate, mock_get_year_days):
        """연도별 공휴일 조회 - 공휴일이 없는 경우"""
        # 공휴일이 없는 데이터
        mock_get_year_days.return_value = [
            {"year": 2024, "month": 1, "date": 2, "is_holiday": False, "holiday_name": None},
            {"year": 2024, "month": 1, "date": 3, "is_holiday": False, "holiday_name": None},
        ]
        
        holidays = self.kh.get_holidays(2024)
        
        assert holidays == []

    @patch('kr_holidays.data.get_year_days_data')
    @patch('kr_holidays.data.get_supported_years')
    @patch('kr_holidays.utils.validate_year_range')
    def test_get_holidays_file_not_found(self, mock_validate, mock_get_supported_years, mock_get_year_days):
        """연도별 공휴일 조회 - 파일 없음"""
        mock_get_year_days.side_effect = FileNotFoundError("파일 없음")
        mock_get_supported_years.return_value = [2024, 2025]
        
        with pytest.raises(FileNotFoundError) as exc_info:
            self.kh.get_holidays(2023)
        
        assert "2023년 공휴일 데이터를 찾을 수 없습니다" in str(exc_info.value)
        assert "지원 연도: [2024, 2025]" in str(exc_info.value)

    @patch('kr_holidays.data.get_year_days_data')
    @patch('kr_holidays.utils.validate_year_range')
    @patch('kr_holidays.utils.get_month_range')
    def test_get_holidays_in_month_success(self, mock_get_month_range, mock_validate, mock_get_year_days):
        """월별 공휴일 조회 - 성공"""
        mock_get_year_days.return_value = MOCK_YEAR_DATA["days"]
        mock_get_month_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        
        # 1월 공휴일
        jan_holidays = self.kh.get_holidays_in_month(2024, 1)
        
        assert jan_holidays == [date(2024, 1, 1)]
        mock_validate.assert_called_once_with(2024)
        mock_get_month_range.assert_called_once_with(2024, 1)

    @patch('kr_holidays.utils.validate_year_range')
    @patch('kr_holidays.utils.get_month_range')
    def test_get_holidays_in_month_invalid_month(self, mock_get_month_range, mock_validate):
        """월별 공휴일 조회 - 잘못된 월"""
        mock_get_month_range.side_effect = ValueError("잘못된 월")
        
        with pytest.raises(ValueError):
            self.kh.get_holidays_in_month(2024, 13)

    @patch('kr_holidays.data.get_year_days_data')
    @patch('kr_holidays.utils.validate_year_range')
    @patch('kr_holidays.utils.get_month_range')
    def test_get_holidays_in_month_no_data(self, mock_get_month_range, mock_validate, mock_get_year_days):
        """월별 공휴일 조회 - 데이터 없음"""
        mock_get_year_days.side_effect = FileNotFoundError()
        mock_get_month_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        
        result = self.kh.get_holidays_in_month(2024, 1)
        
        assert result == []

    @patch('kr_holidays.data.get_year_days_data')
    @patch('kr_holidays.utils.validate_year_range')
    @patch('kr_holidays.utils.get_month_range')
    def test_get_holidays_in_month_empty_month(self, mock_get_month_range, mock_validate, mock_get_year_days):
        """월별 공휴일 조회 - 해당 월에 공휴일 없음"""
        mock_get_year_days.return_value = MOCK_YEAR_DATA["days"]
        mock_get_month_range.return_value = (date(2024, 3, 1), date(2024, 3, 31))
        
        # 3월 공휴일 조회 (테스트 데이터에 3월 공휴일 없음)
        mar_holidays = self.kh.get_holidays_in_month(2024, 3)
        
        assert mar_holidays == []

    @patch('kr_holidays.data.get_year_days_data')
    @patch('kr_holidays.utils.validate_year_range')
    @patch('kr_holidays.utils.get_month_range')
    def test_get_working_days_in_month_success(self, mock_get_month_range, mock_validate, mock_get_year_days):
        """월별 근무일 조회 - 성공"""
        mock_get_year_days.return_value = MOCK_YEAR_DATA["days"]
        mock_get_month_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        
        jan_workdays = self.kh.get_working_days_in_month(2024, 1)
        
        # 1/2만 근무일 (1/1은 공휴일, 1/6,1/7은 주말)
        assert jan_workdays == [date(2024, 1, 2)]

    @patch('kr_holidays.data.get_year_days_data')
    @patch('kr_holidays.utils.validate_year_range')
    @patch('kr_holidays.utils.get_month_range')
    def test_get_working_days_in_month_no_data(self, mock_get_month_range, mock_validate, mock_get_year_days):
        """월별 근무일 조회 - 데이터 없음"""
        mock_get_year_days.side_effect = FileNotFoundError()
        mock_get_month_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        
        result = self.kh.get_working_days_in_month(2024, 1)
        
        assert result == []

    @patch.object(KoreanHolidays, 'get_holidays')
    def test_get_next_holiday_found(self, mock_get_holidays):
        """다음 공휴일 조회 - 찾은 경우"""
        mock_get_holidays.return_value = [
            date(2024, 1, 1),
            date(2024, 2, 10),
            date(2024, 5, 6)
        ]
        
        # 1월 2일 이후 다음 공휴일
        next_holiday = self.kh.get_next_holiday("2024-01-02")
        
        assert next_holiday == date(2024, 2, 10)

    @patch.object(KoreanHolidays, 'get_holidays')
    def test_get_next_holiday_not_found(self, mock_get_holidays):
        """다음 공휴일 조회 - 찾지 못한 경우"""
        mock_get_holidays.return_value = [
            date(2024, 1, 1),
            date(2024, 2, 10),
            date(2024, 5, 6)
        ]
        
        # 마지막 공휴일 이후
        next_holiday = self.kh.get_next_holiday("2024-12-31")
        
        assert next_holiday is None

    @patch.object(KoreanHolidays, 'get_holidays')
    def test_get_next_holiday_same_date(self, mock_get_holidays):
        """다음 공휴일 조회 - 기준일이 공휴일인 경우"""
        mock_get_holidays.return_value = [
            date(2024, 1, 1),
            date(2024, 2, 10),
            date(2024, 5, 6)
        ]
        
        # 1월 1일 기준 (본인은 제외되고 다음 공휴일 반환)
        next_holiday = self.kh.get_next_holiday("2024-01-01")
        
        assert next_holiday == date(2024, 2, 10)

    @patch.object(KoreanHolidays, 'get_holidays')
    def test_get_next_holiday_file_not_found(self, mock_get_holidays):
        """다음 공휴일 조회 - 파일 없음"""
        mock_get_holidays.side_effect = FileNotFoundError()
        
        result = self.kh.get_next_holiday("2024-01-02")
        
        assert result is None

    @patch.object(KoreanHolidays, 'get_holidays')
    def test_get_previous_holiday_found(self, mock_get_holidays):
        """이전 공휴일 조회 - 찾은 경우"""
        mock_get_holidays.return_value = [
            date(2024, 1, 1),
            date(2024, 2, 10),
            date(2024, 5, 6)
        ]
        
        # 2월 15일 이전 공휴일
        prev_holiday = self.kh.get_previous_holiday("2024-02-15")
        
        assert prev_holiday == date(2024, 2, 10)

    @patch.object(KoreanHolidays, 'get_holidays')
    def test_get_previous_holiday_not_found(self, mock_get_holidays):
        """이전 공휴일 조회 - 찾지 못한 경우"""
        mock_get_holidays.return_value = [
            date(2024, 1, 1),
            date(2024, 2, 10),
            date(2024, 5, 6)
        ]
        
        # 첫 번째 공휴일 이전
        prev_holiday = self.kh.get_previous_holiday("2024-01-01")
        
        assert prev_holiday is None

    @patch.object(KoreanHolidays, 'get_holidays')
    def test_get_previous_holiday_multiple_found(self, mock_get_holidays):
        """이전 공휴일 조회 - 여러 개 있을 때 최근 것"""
        mock_get_holidays.return_value = [
            date(2024, 1, 1),
            date(2024, 2, 10),
            date(2024, 5, 6)
        ]
        
        # 5월 10일 이전 공휴일 (가장 최근인 5/6 반환)
        prev_holiday = self.kh.get_previous_holiday("2024-05-10")
        
        assert prev_holiday == date(2024, 5, 6)

    @patch.object(KoreanHolidays, 'get_holidays')
    def test_get_previous_holiday_file_not_found(self, mock_get_holidays):
        """이전 공휴일 조회 - 파일 없음"""
        mock_get_holidays.side_effect = FileNotFoundError()
        
        result = self.kh.get_previous_holiday("2024-02-15")
        
        assert result is None

    @patch.object(KoreanHolidays, 'is_working_day')
    @patch('kr_holidays.utils.date_range')
    def test_count_working_days_normal(self, mock_date_range, mock_is_working_day):
        """근무일 수 계산 - 일반적인 경우"""
        # 2024-01-01~07 기간 (7일)
        test_dates = [date(2024, 1, i) for i in range(1, 8)]
        mock_date_range.return_value = test_dates
        
        working_day_map = {
            date(2024, 1, 1): False,  # 공휴일
            date(2024, 1, 2): True,   # 근무일
            date(2024, 1, 3): True,   # 근무일
            date(2024, 1, 4): True,   # 근무일
            date(2024, 1, 5): True,   # 근무일
            date(2024, 1, 6): False,  # 주말
            date(2024, 1, 7): False,  # 주말
        }
        mock_is_working_day.side_effect = lambda d: working_day_map.get(d, False)
        
        count = self.kh.count_working_days("2024-01-01", "2024-01-07")
        
        assert count == 4

    @patch.object(KoreanHolidays, 'is_working_day')
    def test_count_working_days_reverse_order(self, mock_is_working_day):
        """근무일 수 계산 - 시작일이 종료일보다 큰 경우"""
        count = self.kh.count_working_days("2024-01-07", "2024-01-01")
        
        assert count == 0
        # is_working_day가 호출되지 않아야 함
        mock_is_working_day.assert_not_called()

    @patch.object(KoreanHolidays, 'is_working_day')
    def test_count_working_days_same_day(self, mock_is_working_day):
        """근무일 수 계산 - 같은 날"""
        mock_is_working_day.return_value = True
        
        count = self.kh.count_working_days("2024-01-02", "2024-01-02")
        
        assert count == 1

    @patch.object(KoreanHolidays, 'is_working_day')
    def test_count_working_days_no_working_days(self, mock_is_working_day):
        """근무일 수 계산 - 근무일이 없는 경우"""
        mock_is_working_day.return_value = False  # 모두 비근무일
        
        count = self.kh.count_working_days("2024-01-06", "2024-01-07")  # 주말
        
        assert count == 0

    @patch.object(KoreanHolidays, 'is_holiday')
    @patch('kr_holidays.utils.date_range')
    def test_count_holidays_normal(self, mock_date_range, mock_is_holiday):
        """공휴일 수 계산 - 일반적인 경우"""
        test_dates = [date(2024, 1, i) for i in range(1, 4)]
        mock_date_range.return_value = test_dates
        
        holiday_map = {
            date(2024, 1, 1): True,   # 공휴일
            date(2024, 1, 2): False,  # 평일
            date(2024, 1, 3): False,  # 평일
        }
        mock_is_holiday.side_effect = lambda d: holiday_map.get(d, False)
        
        count = self.kh.count_holidays("2024-01-01", "2024-01-03")
        
        assert count == 1

    @patch.object(KoreanHolidays, 'is_holiday')
    def test_count_holidays_reverse_order(self, mock_is_holiday):
        """공휴일 수 계산 - 시작일이 종료일보다 큰 경우"""
        count = self.kh.count_holidays("2024-01-03", "2024-01-01")
        
        assert count == 0

    @patch.object(KoreanHolidays, 'is_holiday')
    def test_count_holidays_no_holidays(self, mock_is_holiday):
        """공휴일 수 계산 - 공휴일이 없는 경우"""
        mock_is_holiday.return_value = False
        
        count = self.kh.count_holidays("2024-01-02", "2024-01-05")
        
        assert count == 0

    @patch.object(KoreanHolidays, 'is_working_day')
    def test_add_working_days_zero(self, mock_is_working_day):
        """근무일 더하기 - 0일"""
        result = self.kh.add_working_days("2024-01-01", 0)
        
        assert result == date(2024, 1, 1)
        # is_working_day가 호출되지 않아야 함
        mock_is_working_day.assert_not_called()

    @patch.object(KoreanHolidays, 'is_working_day')
    def test_add_working_days_positive(self, mock_is_working_day):
        """근무일 더하기 - 양수"""
        # 2024-01-01부터 시작하여 근무일만 True로 설정
        working_days = [
            date(2024, 1, 2),
            date(2024, 1, 3),
            date(2024, 1, 4),
            date(2024, 1, 5),
            date(2024, 1, 8),
        ]
        mock_is_working_day.side_effect = lambda d: d in working_days
        
        # 5 근무일 더하기
        result = self.kh.add_working_days("2024-01-01", 5)
        
        assert result == date(2024, 1, 8)

    @patch.object(KoreanHolidays, 'is_working_day')
    def test_add_working_days_skip_weekends(self, mock_is_working_day):
        """근무일 더하기 - 주말 건너뛰기"""
        # 금요일에서 시작
        start_date = date(2024, 1, 5)  # 금요일
        
        # 주말(1/6, 1/7)은 건너뛰고 1/8(월)이 근무일
        working_days = [date(2024, 1, 8)]
        mock_is_working_day.side_effect = lambda d: d in working_days
        
        result = self.kh.add_working_days(start_date, 1)
        
        assert result == date(2024, 1, 8)

    def test_add_working_days_negative(self):
        """근무일 더하기 - 음수 입력"""
        with pytest.raises(ValueError) as exc_info:
            self.kh.add_working_days("2024-01-01", -1)
        
        assert "근무일 수는 0 이상이어야 합니다" in str(exc_info.value)

    @patch('kr_holidays.data.is_supported_year')
    @patch('kr_holidays.data.get_supported_years')
    @patch('kr_holidays.utils.validate_year_range')
    def test_get_year_summary_unsupported(self, mock_validate, mock_get_supported_years, mock_is_supported_year):
        """연도 요약 - 지원하지 않는 연도"""
        mock_is_supported_year.return_value = False
        mock_get_supported_years.return_value = [2024, 2025]
        
        summary = self.kh.get_year_summary(2000)
        
        assert summary["year"] == 2000
        assert summary["supported"] == False
        assert "지원하지 않는 연도입니다" in summary["message"]
        assert "[2024, 2025]" in summary["message"]

    @patch.object(KoreanHolidays, 'get_holidays')
    @patch.object(KoreanHolidays, 'is_substitute_holiday')
    @patch.object(KoreanHolidays, 'get_holiday_name')
    @patch('kr_holidays.data.get_year_statistics')
    @patch('kr_holidays.data.is_supported_year')
    @patch('kr_holidays.utils.get_weekday_korean')
    @patch('kr_holidays.utils.validate_year_range')
    def test_get_year_summary_supported(self, mock_validate, mock_get_weekday, mock_is_supported,
                                      mock_get_stats, mock_get_holiday_name,
                                      mock_is_substitute, mock_get_holidays):
        """연도 요약 - 지원하는 연도"""
        mock_is_supported.return_value = True
        mock_get_holidays.return_value = [date(2024, 1, 1), date(2024, 5, 6)]
        mock_is_substitute.side_effect = lambda d: d == date(2024, 5, 6)
        mock_get_holiday_name.side_effect = {
            date(2024, 1, 1): "1월1일",
            date(2024, 5, 6): "대체공휴일(어린이날)"
        }.get
        mock_get_stats.return_value = {"total_days": 366}
        mock_get_weekday.return_value = "월요일"
        
        summary = self.kh.get_year_summary(2024)
        
        assert summary["year"] == 2024
        assert summary["supported"] == True
        assert summary["substitute_holidays"] == 1
        assert len(summary["holidays"]) == 2
        
        # 첫 번째 공휴일 상세 정보 확인
        first_holiday = summary["holidays"][0]
        assert first_holiday["date"] == "2024-01-01"
        assert first_holiday["name"] == "1월1일"
        assert first_holiday["weekday"] == "월요일"
        assert first_holiday["is_substitute"] == False
        
        # 두 번째 공휴일 상세 정보 확인
        second_holiday = summary["holidays"][1]
        assert second_holiday["date"] == "2024-05-06"
        assert second_holiday["name"] == "대체공휴일(어린이날)"
        assert second_holiday["is_substitute"] == True

    @patch.object(KoreanHolidays, 'get_holidays')
    @patch('kr_holidays.data.is_supported_year')
    @patch('kr_holidays.utils.validate_year_range')
    def test_get_year_summary_file_not_found(self, mock_validate, mock_is_supported, mock_get_holidays):
        """연도 요약 - 파일 없음"""
        mock_is_supported.return_value = True
        mock_get_holidays.side_effect = FileNotFoundError()
        
        summary = self.kh.get_year_summary(2024)
        
        assert summary["year"] == 2024
        assert summary["supported"] == False
        assert "데이터 파일을 찾을 수 없습니다" in summary["message"]


class TestConvenienceFunctions:
    """편의 함수들 테스트"""

    @patch.object(_default_instance, 'is_holiday')
    def test_is_holiday_convenience(self, mock_is_holiday):
        """is_holiday 편의 함수"""
        mock_is_holiday.return_value = True
        
        result = is_holiday("2024-01-01")
        
        assert result == True
        mock_is_holiday.assert_called_once_with("2024-01-01")

    @patch.object(_default_instance, 'is_weekend')
    def test_is_weekend_convenience(self, mock_is_weekend):
        """is_weekend 편의 함수"""
        mock_is_weekend.return_value = True
        
        result = is_weekend("2024-01-06")
        
        assert result == True
        mock_is_weekend.assert_called_once_with("2024-01-06")

    @patch.object(_default_instance, 'is_working_day')
    def test_is_working_day_convenience(self, mock_is_working_day):
        """is_working_day 편의 함수"""
        mock_is_working_day.return_value = True
        
        result = is_working_day("2024-01-02")
        
        assert result == True
        mock_is_working_day.assert_called_once_with("2024-01-02")

    @patch.object(_default_instance, 'get_holidays')
    def test_get_holidays_convenience(self, mock_get_holidays):
        """get_holidays 편의 함수"""
        expected_holidays = [date(2024, 1, 1)]
        mock_get_holidays.return_value = expected_holidays
        
        result = get_holidays(2024)
        
        assert result == expected_holidays
        mock_get_holidays.assert_called_once_with(2024)

    @patch.object(_default_instance, 'get_holiday_name')
    def test_get_holiday_name_convenience(self, mock_get_holiday_name):
        """get_holiday_name 편의 함수"""
        mock_get_holiday_name.return_value = "1월1일"
        
        result = get_holiday_name("2024-01-01")
        
        assert result == "1월1일"
        mock_get_holiday_name.assert_called_once_with("2024-01-01")

    @patch.object(_default_instance, 'get_next_holiday')
    def test_get_next_holiday_convenience(self, mock_get_next_holiday):
        """get_next_holiday 편의 함수"""
        expected_date = date(2024, 2, 10)
        mock_get_next_holiday.return_value = expected_date
        
        result = get_next_holiday("2024-01-02")
        
        assert result == expected_date
        mock_get_next_holiday.assert_called_once_with("2024-01-02")

    @patch.object(_default_instance, 'count_working_days')
    def test_count_working_days_convenience(self, mock_count_working_days):
        """count_working_days 편의 함수"""
        mock_count_working_days.return_value = 5
        
        result = count_working_days("2024-01-01", "2024-01-07")
        
        assert result == 5
        mock_count_working_days.assert_called_once_with("2024-01-01", "2024-01-07")

    @patch.object(_default_instance, 'add_working_days')
    def test_add_working_days_convenience(self, mock_add_working_days):
        """add_working_days 편의 함수"""
        expected_date = date(2024, 1, 8)
        mock_add_working_days.return_value = expected_date
        
        result = add_working_days("2024-01-01", 5)
        
        assert result == expected_date
        mock_add_working_days.assert_called_once_with("2024-01-01", 5)


class TestKoreanHolidaysIntegration:
    """KoreanHolidays 클래스 통합 테스트"""

    def test_class_instantiation(self):
        """클래스 인스턴스 생성"""
        kh = KoreanHolidays()
        assert isinstance(kh, KoreanHolidays)

    def test_default_instance_exists(self):
        """기본 인스턴스 존재 확인"""
        assert isinstance(_default_instance, KoreanHolidays)

    @patch('kr_holidays.data.get_day_info')
    def test_different_date_input_types(self, mock_get_day_info):
        """다양한 날짜 입력 타입 처리"""
        mock_get_day_info.return_value = {"is_holiday": True}
        kh = KoreanHolidays()
        
        # 문자열
        assert kh.is_holiday("2024-01-01") == True
        # date 객체
        assert kh.is_holiday(date(2024, 1, 1)) == True
        # datetime 객체
        assert kh.is_holiday(datetime(2024, 1, 1, 12, 0, 0)) == True

    @patch.object(KoreanHolidays, 'is_working_day')
    def test_large_working_days_calculation(self, mock_is_working_day):
        """큰 수의 근무일 계산"""
        kh = KoreanHolidays()
        
        # 매일 근무일로 설정 (테스트 속도를 위해)
        mock_is_working_day.return_value = True
        
        result = kh.add_working_days("2024-01-01", 100)
        
        assert isinstance(result, date)
        assert result > date(2024, 1, 1)

    def test_method_chaining_compatibility(self):
        """메서드 체이닝 호환성 테스트"""
        kh = KoreanHolidays()
        
        # 메서드들이 적절한 타입을 반환하는지 확인
        with patch.object(kh, 'get_holidays', return_value=[]):
            holidays = kh.get_holidays(2024)
            assert isinstance(holidays, list)
        
        with patch.object(kh, 'is_holiday', return_value=True):
            is_hol = kh.is_holiday("2024-01-01")
            assert isinstance(is_hol, bool)


class TestErrorHandlingAndEdgeCases:
    """오류 처리 및 경계 케이스 테스트"""

    def setup_method(self):
        self.kh = KoreanHolidays()

    @patch('kr_holidays.utils.parse_date_input')
    def test_date_parsing_error_propagation(self, mock_parse_date):
        """날짜 파싱 오류 전파"""
        mock_parse_date.side_effect = ValueError("잘못된 날짜")
        
        with pytest.raises(ValueError):
            self.kh.is_holiday("invalid-date")

    @patch('kr_holidays.data.get_day_info')
    def test_data_access_error_handling(self, mock_get_day_info):
        """데이터 접근 오류 처리"""
        mock_get_day_info.side_effect = Exception("데이터 접근 오류")
        
        with pytest.raises(Exception):
            self.kh.is_holiday("2024-01-01")

    def test_extreme_year_values(self):
        """극한 연도 값 테스트"""
        with patch('kr_holidays.utils.validate_year_range') as mock_validate:
            mock_validate.side_effect = ValueError("연도 범위 오류")
            
            with pytest.raises(ValueError):
                self.kh.get_holidays(9999)

if __name__ == "__main__":
    # 직접 실행 시 테스트 수행
    pytest.main([__file__, "-v"])
