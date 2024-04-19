import random

import pandas as pd


class TitleGenerator:
    """A class for generating titles based on keywords from a DataFrame."""

    def __init__(
        self,
        df: pd.DataFrame,
        keyword_column: str,
        desired_length: int = 100,
        character_limit: int = 150,
        delimiter: str = ' - ',
    ):
        self.df = df
        self.keyword_column = keyword_column
        self.character_limit = character_limit
        self.desired_length = desired_length
        self.delimiter = delimiter

    def generate_title(self) -> str:
        keyword_list = self.df[self.keyword_column].tolist()
        output_list = []
        used_keywords = set()
        while True:
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
            if self.desired_length <= title_length <= self.character_limit:
                return title
            elif title_length > self.character_limit:
                output_list.pop()  # Remove the last added keyword if title exceeds character limit


if __name__ == '__main__':
    # Create a sample DataFrame
    keywords_path = 'data/step_2/highlights/black_celestial/keywords.csv'
    df = pd.read_csv(keywords_path)

    # Initialize TitleGenerator object
    title_generator = TitleGenerator(
        df=df,
        keyword_column='Keywords',
        desired_length=100,
        character_limit=150,
    )

    # Generate title
    generated_title = title_generator.generate_title()
    print('Title length:', len(generated_title))
    print('Generated Title:', generated_title)
