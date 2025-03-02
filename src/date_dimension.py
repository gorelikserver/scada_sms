# src/date_dimension.py
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# Define Jewish holidays with sabbatical restrictions (yom tov)
# Where work is generally prohibited similar to Shabbat
SABBATICAL_HOLIDAYS = {
    "Rosh Hashanah": True,
    "Rosh Hashanah (2nd day)": True,
    "Yom Kippur": True,
    "Sukkot": True,  # 1st day
    "Shemini Atzeret": True,
    "Simchat Torah": True,
    "Passover (1st day)": True,
    "Passover (2nd day)": True,
    "Passover (7th day)": True,
    "Passover (8th day)": True,
    "Shavuot": True,
    "Shavuot (2nd day)": True
}


def create_date_dimension(start_date = '2024-01-01', end_date = '2099-12-31'):
    """
    Create a date dimension table with Jewish holidays.

    Args:
        start_date (str): Start date in 'YYYY-MM-DD' format
        end_date (str): End date in 'YYYY-MM-DD' format

    Returns:
        pandas.DataFrame: Date dimension table
    """
    # Import pyluach here to make it an explicit dependency
    try:
        import pyluach.dates
        from pyluach.hebrewcal import HebrewDate
        import pyluach.hebrewcal as hcal
    except ImportError:
        raise ImportError("This function requires pyluach. Install it with: pip install pyluach")

    # Convert string dates to datetime objects
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')

    # Generate list of dates
    date_list = []
    current_date = start

    while current_date <= end:
        date_list.append(current_date)
        current_date += timedelta(days=1)

    # Create DataFrame
    df = pd.DataFrame({'date': date_list})

    # Extract date components
    df['date_id'] = df['date'].dt.strftime('%Y%m%d').astype(int)  # Surrogate key
    df['full_date'] = df['date']
    df['day_of_week'] = df['date'].dt.dayofweek  # 0 = Monday, 6 = Sunday
    df['day_name'] = df['date'].dt.day_name()
    df['day_of_month'] = df['date'].dt.day
    df['day_of_year'] = df['date'].dt.dayofyear
    df['week_of_year'] = df['date'].dt.isocalendar().week
    df['month'] = df['date'].dt.month
    df['month_name'] = df['date'].dt.month_name()
    df['quarter'] = df['date'].dt.quarter
    df['year'] = df['date'].dt.year
    df['is_weekend'] = np.where(df['day_of_week'].isin([5, 6]), 1, 0)  # Weekend is Saturday and Sunday

    # Initialize Jewish holiday columns
    df['jewish_holiday'] = None
    df['hebrew_date'] = None
    df['is_jewish_holiday'] = 0
    df['is_sabbatical_holiday'] = 0

    # Map each date to its corresponding Hebrew date and check for holidays
    for idx, row in df.iterrows():
        greg_date = row['date']
        hebrew_date = HebrewDate.from_pydate(greg_date)

        # Store Hebrew date in format: Month Day, Year (e.g., "Nisan 15, 5783")
        df.at[idx, 'hebrew_date'] = f"{hebrew_date.month_name()} {hebrew_date.day}, {hebrew_date.year}"

        # Check for Jewish holidays
        jewish_holiday = get_jewish_holiday(hebrew_date)
        if jewish_holiday:
            df.at[idx, 'jewish_holiday'] = jewish_holiday
            df.at[idx, 'is_jewish_holiday'] = 1

            # Check if it's a sabbatical holiday (yom tov with work restrictions)
            if jewish_holiday in SABBATICAL_HOLIDAYS:
                df.at[idx, 'is_sabbatical_holiday'] = 1

    # Convert date to string for easier export/use in databases
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
    df['full_date'] = df['full_date'].dt.strftime('%Y-%m-%d')

    return df


def get_jewish_holiday(hebrew_date):
    """
    Check if the given Hebrew date is a Jewish holiday.

    Args:
        hebrew_date: pyluach.dates.HebrewDate object

    Returns:
        str: Holiday name or None if not a holiday
    """
    month = hebrew_date.month
    day = hebrew_date.day
    year = hebrew_date.year

    # Major holidays
    if month == 1 and day == 15:  # Nisan 15
        return "Passover (1st day)"
    elif month == 1 and day == 16:  # Nisan 16
        return "Passover (2nd day)"
    elif month == 1 and day == 21:  # Nisan 21
        return "Passover (7th day)"
    elif month == 1 and day == 22:  # Nisan 22
        return "Passover (8th day)"
    elif month == 3 and day == 6:  # Sivan 6
        return "Shavuot"
    elif month == 3 and day == 7:  # Sivan 7 (outside Israel)
        return "Shavuot (2nd day)"
    elif month == 7 and day == 1:  # Tishrei 1
        return "Rosh Hashanah"
    elif month == 7 and day == 2:  # Tishrei 2
        return "Rosh Hashanah (2nd day)"
    elif month == 7 and day == 10:  # Tishrei 10
        return "Yom Kippur"
    elif month == 7 and day == 15:  # Tishrei 15
        return "Sukkot"
    elif month == 7 and day == 22:  # Tishrei 22
        return "Shemini Atzeret"
    elif month == 7 and day == 23:  # Tishrei 23
        return "Simchat Torah"
    elif month == 9 and day == 25:  # Kislev 25
        return "Hanukkah (1st day)"
    elif month == 9 and day >= 26 and day <= 30:  # Kislev 26-30
        return f"Hanukkah ({day - 24}th day)"
    elif month == 10 and day >= 1 and day <= 3:  # Tevet 1-3 (potential Hanukkah days)
        return f"Hanukkah ({day + 6}th day)"
    elif month == 10 and day == 10:  # Tevet 10
        return "Asara B'Tevet"
    elif month == 11 and day == 15:  # Shevat 15
        return "Tu BiShvat"
    elif month == 12 and day == 14:  # Adar 14 (or Adar II in leap years)
        return "Purim"
    elif month == 12 and day == 15:  # Adar 15 (or Adar II in leap years)
        return "Shushan Purim"

    # Minor fast days
    elif month == 4 and day == 17:  # Tammuz 17
        return "Fast of Tammuz 17"
    elif month == 5 and day == 9:  # Av 9
        return "Tisha B'Av"
    elif month == 7 and day == 3:  # Tishrei 3
        return "Fast of Gedaliah"
    elif month == 12 and day == 13:  # Adar 13 (or Adar II in leap years)
        return "Fast of Esther"

    # Modern holidays
    elif month == 1 and day == 27:  # Nisan 27
        return "Yom HaShoah"
    elif month == 2 and day == 4:  # Iyar 4
        return "Yom HaZikaron"
    elif month == 2 and day == 5:  # Iyar 5
        return "Yom HaAtzmaut"
    elif month == 2 and day == 28:  # Iyar 28
        return "Yom Yerushalayim"

    return None