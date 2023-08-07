from manager import Manager
from datetime import datetime, timedelta

def pause_work(time: datetime) -> int:

    def is_weekend(day:datetime = datetime.now()) -> bool:
        if day.month == 1:
            january_weekends = [1, 2, 3, 4, 5, 6, 7, 8]
            if day.day in january_weekends:
                return True
        if day.month == 12:
            if day.day == 31:
                return True
        if day.month == 5:
            if day.day == 9:
                return True
        return datetime.weekday(day) == 6
    
    now = time
    sleep = 0
    if is_weekend(now):
        start_hour = 11
        start_minute = 0
        end = 19
    else:
        start_hour = 10
        start_minute = 30
        end = 21
    if now.hour >= end:
        tomorrow = now + timedelta(days=1)
        tomorrow_specific = datetime(year=tomorrow.year, month=tomorrow.month, day=tomorrow.day, hour=start_hour, minute=start_minute, second=0, microsecond=0)
        sleep = tomorrow_specific - now
    elif (now.hour < start_hour) or (now.hour == start_hour and now.minute < start_minute):
        now_specific = datetime(year=now.year, month=now.month, day=now.day, hour=start_hour, minute=start_minute, second=0, microsecond=0)
        sleep = now_specific - now
    # self.logger.info(f'pause {sleep}')
    if sleep == 0:
        return sleep
    return sleep#.total_seconds()   

def main():
    time = datetime(year=2023, month=1, day=7, hour=0, minute=0, second=0)
    minute_1 = timedelta(seconds=1)
    for _ in range(1000):
        print(time, pause_work(time))
        time += minute_1

if __name__ == "__main__":
    main()