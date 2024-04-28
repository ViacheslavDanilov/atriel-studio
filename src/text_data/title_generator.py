import random
from typing import List

import pandas as pd


class TitleGenerator:
    """A class for generating titles based on keywords from a DataFrame."""

    def __init__(
        self,
        df: pd.DataFrame,
        keyword_column: str = 'Keywords',
        min_desired_length: int = 60,
        max_desired_length: int = 100,
        max_limit: int = 150,
        delimiter: str = ' - ',
    ):
        self.df = df
        self.keyword_column = keyword_column
        self.max_limit = max_limit
        self.min_desired_length = min_desired_length
        self.max_desired_length = max_desired_length
        self.delimiter = delimiter

    def generate_titles(self, num_titles: int) -> List[str]:
        result: List[str] = []
        for _ in range(num_titles):
            keyword_list = self.df[self.keyword_column].tolist()
            used_keywords = set()
            attempt_count = 0  # Track the number of attempts to construct a title
            desired_length = random.randint(self.min_desired_length, self.max_desired_length)
            title = ''
            while True:
                attempt_count += 1
                if attempt_count > 10000:  # Limit the number of attempts
                    raise ValueError(
                        'Failed to construct a title. Add more keywords or change min and max limits',
                    )

                keyword = random.choice(keyword_list).capitalize()
                if keyword in used_keywords:
                    continue  # Skip if keyword is already used
                keyword_list = [v for v in keyword_list if v != keyword]
                title += f"{keyword}{self.delimiter}"
                used_keywords.add(keyword)
                title_length = len(title)
                if desired_length <= title_length <= self.max_limit:
                    if title not in result:  # Check if title is unique
                        result.append(title.rstrip(self.delimiter))
                        break
                elif title_length > self.max_limit:
                    break
        return result


if __name__ == '__main__':

    # Test TitleGenerator class
    num_images = 100
    keyword_path = 'data/csv_generation/instagram-highlight-covers/black-celestial/keywords.csv'
    df = pd.read_csv(keyword_path)
    title_generator = TitleGenerator(
        df=df,
        keyword_column='Keywords',
        min_desired_length=60,
        max_desired_length=100,
        max_limit=150,
    )
    title_list = title_generator.generate_titles(num_titles=num_images)
    print('Generated Titles:', title_list)
