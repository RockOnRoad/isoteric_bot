ARCANA_MAP = {
    1: "Маг",
    2: "Жрица",
    3: "Императрица",
    4: "Император",
    5: "Иерофант",
    6: "Влюбленные",
    7: "Колесница",
    8: "Справедливость",
    9: "Отшельник",
    10: "Колесо фортуны",
    11: "Сила",
    12: "Повешенный",
    13: "Смерть и жизнь",
    14: "Умеренность",
    15: "Дьявол",
    16: "Башня",
    17: "Звезда",
    18: "Луна",
    19: "Солнце",
    20: "Суд",
    21: "Мир",
    22: "Шут",
}


def calculate_arcana(birthday: str) -> dict:
    map_birthday = list(enumerate(birthday))
    #  [(0, '1'), (1, '2'), (2, '.'), (3, '0'), (4, '7'), (5, '.'), (6, '1'), (7, '9'), (8, '9'), (9, '6')]

    day, month, year = birthday.split(".")

    def calculate_arcana(value) -> int:
        while int(value) > 22:
            value = sum(int(d) for d in str(value))
        return int(value)

    day_arcana = calculate_arcana(day)

    month_arcana = calculate_arcana(month)

    year_arcana = calculate_arcana(year)

    main_arcana_raw = day_arcana + month_arcana + year_arcana
    main_arcana = calculate_arcana(main_arcana_raw)

    the_arcana_raw = day_arcana + month_arcana + year_arcana + main_arcana
    the_arcana = calculate_arcana(the_arcana_raw)

    return {
        "day_arcana": day_arcana,
        "month_arcana": month_arcana,
        "year_arcana": year_arcana,
        "main_arcana": main_arcana,
        "the_arcana": the_arcana,
    }
