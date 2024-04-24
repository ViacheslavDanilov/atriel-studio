import datetime
import random
from typing import List

import pandas as pd
import pytz


class TitleGenerator:
    """A class for generating titles based on keywords from a DataFrame."""

    def __init__(
        self,
        df: pd.DataFrame,
        keyword_column: str = 'Keywords',
        desired_length: int = 80,
        max_limit: int = 150,
        delimiter: str = ' - ',
    ):
        self.df = df
        self.keyword_column = keyword_column
        self.max_limit = max_limit
        self.desired_length = desired_length
        self.delimiter = delimiter

    def generate_titles(
        self,
        num_titles: int,
    ) -> List[str]:
        result: List[str] = []
        for _ in range(num_titles):
            keyword_list = self.df[self.keyword_column].tolist()
            output_list = []
            used_keywords = set()
            attempt_count = 0  # Track the number of attempts to construct a title
            while True:
                attempt_count += 1
                if attempt_count > 100:  # Limit the number of attempts
                    raise ValueError(
                        'Failed to construct a title. Add more keywords or change min and max limits',
                    )
                if len(keyword_list) > 0:
                    keyword = random.choice(keyword_list).capitalize()
                else:
                    raise ValueError('Add more keywords or change min and max limits')
                if keyword in used_keywords:
                    continue  # Skip if keyword is already used
                keyword_list = [v for v in keyword_list if v != keyword]
                output_list.append(keyword)
                used_keywords.add(keyword)
                title = self.delimiter.join(output_list)
                title_length = len(title)
                if self.desired_length <= title_length <= self.max_limit:
                    result.append(title)
                    break
                elif title_length > self.max_limit:
                    output_list.pop()  # Remove the last added keyword if title exceeds character limit
        return result


class DescriptionGenerator:
    """A class for generating a list of descriptions with diversity and randomness."""

    def __init__(
        self,
        df: pd.DataFrame,
    ) -> None:
        self.descriptions = df['Description'].tolist()
        self.unique_descriptions = set(self.descriptions)
        random.shuffle(self.descriptions)
        self.prev_desc = None

    def generate_descriptions(
        self,
        num_descriptions: int,
    ) -> List[str]:
        result: List[str] = []
        remaining_unique = self.unique_descriptions.copy()

        while len(result) < num_descriptions:
            if self.prev_desc is not None:
                remaining_unique.discard(self.prev_desc)

            remaining_descriptions = list(remaining_unique)
            random.shuffle(remaining_descriptions)

            for desc in remaining_descriptions:
                if desc != self.prev_desc:
                    result.append(desc)
                    self.prev_desc = desc
                    remaining_unique.discard(desc)
                    break

            if not remaining_unique:
                random.shuffle(self.descriptions)
                for desc in self.descriptions:
                    if desc != self.prev_desc:
                        result.append(desc)
                        self.prev_desc = desc
                        break
        return result[:num_descriptions]


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
            for time in times_for_day:
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

    num_images = 85
    # Test TitleGenerator class
    keyword_path = 'data/step_2/ds-01/instagram-highlight-covers/black-celestial/keywords.csv'
    df = pd.read_csv(keyword_path)
    title_generator = TitleGenerator(
        df=df,
        keyword_column='Keywords',
        desired_length=80,
        max_limit=150,
    )
    title_list = title_generator.generate_titles(num_titles=num_images)
    print('Generated Titles:', title_list)

    # Test DescriptionGenerator class
    description_path = (
        'data/step_2/ds-01/instagram-highlight-covers/black-celestial/descriptions.csv'
    )
    df = pd.read_csv(description_path)
    desc_generator = DescriptionGenerator(df=df)
    desc_list = desc_generator.generate_descriptions(num_descriptions=num_images)
    print('Generated Descriptions:', desc_list)

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
