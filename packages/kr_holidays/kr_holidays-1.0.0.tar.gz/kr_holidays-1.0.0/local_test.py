from kr_holidays import is_holiday, get_holidays, count_working_days, get_holiday_name

# 간단한 확인
print(is_holiday("2024-01-01"))  # True

print(get_holiday_name("2024-01-01"))


# 연도별 공휴일
holidays_2024 = get_holidays(2024)

print(holidays_2024)

# 근무일 계산
working_days = count_working_days("2024-01-01", "2024-01-31")

print(working_days)
