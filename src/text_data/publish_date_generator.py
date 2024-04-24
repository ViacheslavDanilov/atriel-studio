import datetime
from typing import List

import pytz


class PublishDateGenerator:
    """A class to generate publish dates and times based on DataFrame column day_id."""

    DEFAULT_TIMES = {
        'Monday': ['20:00:00', '16:00:00', '14:00:00', '21:00:00', '15:00:00'],
        'Tuesday': ['20:00:00', '16:00:00', '14:00:00', '21:00:00', '15:00:00'],
        'Wednesday': ['20:00:00', '16:00:00', '14:00:00', '21:00:00', '15:00:00'],
        'Thursday': ['20:00:00', '16:00:00', '14:00:00', '21:00:00', '15:00:00'],
        'Friday': ['20:00:00', '16:00:00', '14:00:00', '21:00:00', '15:00:00'],
        'Saturday': ['20:00:00', '16:00:00', '14:00:00', '21:00:00', '15:00:00'],
        'Sunday': ['20:00:00', '12:00:00', '21:00:00', '22:00:00', '16:00:00'],
    }

    def __init__(
        self,
        start_date: str = None,
    ):
        if start_date is None:
            self.start_date = datetime.datetime.now()
        else:
            self.start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')

    def generate_times(
        self,
        total_pins: int,
        num_pins_per_day: int,
    ) -> List[str]:
        utc = pytz.UTC
        publish_time_list = []
        current_date = self.start_date
        for _ in range(total_pins // num_pins_per_day):
            day_of_week = current_date.strftime('%A')
            times_for_day = self.DEFAULT_TIMES.get(
                day_of_week,
                ['09:00:00'],
            )  # Default time is 09:00:00 if not specified
            for time_index in range(num_pins_per_day):
                time = times_for_day[time_index % len(times_for_day)]
                publish_date_time = utc.localize(
                    current_date.replace(
                        hour=int(time[:2]),
                        minute=int(time[3:5]),
                        second=int(time[6:]),
                    ),
                )
                publish_time_list.append(publish_date_time.strftime('%Y-%m-%dT%H:%M:%S'))
            current_date += datetime.timedelta(days=1)
        return publish_time_list


if __name__ == '__main__':

    # Test PublishDateGenerator class
    pins_dict = {
        'canva-instagram-templates': 5,
        'instagram-highlight-covers': 3,
        'instagram-puzzle-feed': 2,
    }
    publish_date_generator = PublishDateGenerator(start_date='2024-04-21')
    time_list = publish_date_generator.generate_times(
        total_pins=50,
        num_pins_per_day=sum(pins_dict.values()),
    )
    print('Generated Times:', time_list)