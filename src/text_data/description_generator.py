import random
from typing import List

import pandas as pd


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


if __name__ == '__main__':

    # Test DescriptionGenerator class
    num_images = 85
    description_path = (
        'data/csv_generation/ds-01/instagram-highlight-covers/black-celestial/descriptions.csv'
    )
    df = pd.read_csv(description_path)
    desc_generator = DescriptionGenerator(df=df)
    desc_list = desc_generator.generate_descriptions(num_descriptions=num_images)
    print('Generated Descriptions:', desc_list)
