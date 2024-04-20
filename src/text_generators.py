import random
from typing import List

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


class DescriptionGenerator:
    """A class for generating a list of descriptions with diversity and randomness."""

    def __init__(
        self,
        df_desc: pd.DataFrame,
    ) -> None:
        self.descriptions = df_desc['Description'].tolist()
        random.shuffle(self.descriptions)
        self.prev_desc = None

    def generate_descriptions(
        self,
        num_descriptions: int,
    ) -> List[str]:
        result = []
        for desc in self.descriptions:
            if desc != self.prev_desc:
                result.append(desc)
                self.prev_desc = desc
                if len(result) == num_descriptions:
                    break

        # Not enough unique descriptions, fill the remaining with repeats
        if len(result) < num_descriptions:
            remaining = num_descriptions - len(result)
            unique_descriptions = set(self.descriptions)
            remaining_descriptions = [
                desc for desc in unique_descriptions if desc != self.prev_desc
            ]
            random.shuffle(remaining_descriptions)
            result.extend(remaining_descriptions[:remaining])

        return result


if __name__ == '__main__':
    # Test TitleGenerator
    keyword_path = 'data/step_2/ds_01/highlights/black-celestial/keywords.csv'
    df = pd.read_csv(keyword_path)
    title_generator = TitleGenerator(
        df=df,
        keyword_column='Keywords',
        desired_length=100,
        character_limit=150,
    )
    generated_title = title_generator.generate_title()
    print('Title length:', len(generated_title))
    print('Generated Title:', generated_title)

    # Test DescriptionGenerator object
    description_path = 'data/step_2/ds_01/highlights/black-celestial/descriptions.csv'
    df = pd.read_csv(description_path)
    desc_generator = DescriptionGenerator(df_desc=df)
    generated_descriptions = desc_generator.generate_descriptions(num_descriptions=10)
    print('Generated Descriptions:', generated_descriptions)
