import datetime
from typing import List

import pytz


class PublishDateGenerator:
    """A class to generate publish dates and times based on DataFrame column day_id."""

    DEFAULT_TIMES = {
        'Monday': [
            '01:00:00',
            '02:00:00',
            '16:00:00',
            '18:00:00',
            '19:00:00',
            '19:15:00',
            '21:00:00',
            '21:45:00',
            '21:59:00',
            '23:00:00',
        ],
        'Tuesday': [
            '01:00:00',
            '02:00:00',
            '15:00:00',
            '17:00:00',
            '18:00:00',
            '18:15:00',
            '20:00:00',
            '21:00:00',
            '21:15:00',
            '22:05:00',
        ],
        'Wednesday': [
            '00:05:00',
            '01:00:00',
            '16:00:00',
            '17:00:00',
            '18:00:00',
            '19:00:00',
            '20:00:00',
            '21:00:00',
            '23:00:00',
            '23:15:00',
        ],
        'Thursday': [
            '02:00:00',
            '12:00:00',
            '15:00:00',
            '16:00:00',
            '19:00:00',
            '20:00:00',
            '21:30:00',
            '22:00:00',
            '23:00:00',
            '23:15:00',
        ],
        'Friday': [
            '01:00:00',
            '02:00:00',
            '16:00:00',
            '17:00:00',
            '18:00:00',
            '19:15:00',
            '20:15:00',
            '21:00:00',
            '22:00:00',
            '23:00:00',
        ],
        'Saturday': [
            '13:00:00',
            '14:00:00',
            '15:00:00',
            '16:00:00',
            '17:00:00',
            '18:00:00',
            '18:15:00',
            '21:00:00',
            '21:15:00',
            '23:00:00',
        ],
        'Sunday': [
            '00:05:00',
            '12:00:00',
            '14:00:00',
            '15:00:00',
            '16:00:00',
            '17:00:00',
            '18:00:00',
            '19:00:00',
            '21:00:00',
            '23:00:00',
        ],
    }

    def __init__(
        self,
        date: datetime.datetime = None,
    ):
        if date is None:
            self.date = datetime.datetime.now()
        else:
            self.date = date

    def generate_times(
        self,
        num_pins_per_day: int,
    ) -> List[str]:
        utc = pytz.UTC
        publish_time_list = []
        day_of_week = self.date.strftime('%A')
        # Default time is 13:00:00 if not specified
        times_for_day = self.DEFAULT_TIMES.get(day_of_week, ['13:00:00'])

        for time_index in range(num_pins_per_day):
            time = times_for_day[time_index % len(times_for_day)]
            publish_date_time = utc.localize(
                self.date.replace(
                    hour=int(time[:2]),
                    minute=int(time[3:5]),
                    second=int(time[6:]),
                ),
            )
            publish_time_list.append(publish_date_time.strftime('%Y-%m-%dT%H:%M:%S'))

        return publish_time_list


if __name__ == '__main__':

    # Test PublishDateGenerator class
    start_date = '2024-04-21'
    current_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    pins_dict = {
        'canva-instagram-templates': 5,
        'instagram-highlight-covers': 3,
        'instagram-puzzle-feed': 2,
    }
    num_pins_per_day = sum(pins_dict.values())
    publish_date_generator = PublishDateGenerator(date=current_date)
    time_list = publish_date_generator.generate_times(num_pins_per_day)
    print('Generated Times:', time_list)
