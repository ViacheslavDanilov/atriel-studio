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
        generated_titles: List[str] = []
        for _ in range(num_titles):
            keyword_list = self.df[self.keyword_column].tolist()
            attempt_count = 0  # Track the number of attempts to construct a title
            desired_length = random.randint(self.min_desired_length, self.max_desired_length)
            while True:
                attempt_count += 1
                if attempt_count > 100000:  # Limit the number of attempts
                    raise ValueError(
                        'Failed to construct a title. Add more keywords or change min and max limits',
                    )

                used_keywords = set()
                title = ''
                while len(title) < self.max_limit:
                    keyword = random.choice(keyword_list).capitalize()
                    if keyword in used_keywords:
                        continue  # Skip if keyword is already used
                    used_keywords.add(keyword)
                    title += f"{keyword}{self.delimiter}"
                    if len(title) > desired_length:
                        break

                # Remove the delimiter from the end of the title
                title = title.rstrip(self.delimiter)

                # Check if title is unique and add it to the list
                if title not in generated_titles:
                    generated_titles.append(title)
                    break

        return generated_titles


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
