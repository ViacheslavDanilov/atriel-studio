import random
from typing import List

import pandas as pd


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


if __name__ == '__main__':

    # Test TitleGenerator class
    num_images = 85
    keyword_path = 'data/csv_generation/instagram-highlight-covers/black-celestial/keywords.csv'
    df = pd.read_csv(keyword_path)
    title_generator = TitleGenerator(
        df=df,
        keyword_column='Keywords',
        desired_length=80,
        max_limit=150,
    )
    title_list = title_generator.generate_titles(num_titles=num_images)
    print('Generated Titles:', title_list)
