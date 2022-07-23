from unittest.mock import patch

import pytest

from src.generator import generator



@pytest.mark.parametrize(
    "input_key,expected",
    [
        (("If", "you"), ("can", ("you", "can"))),
        (("which", "grain"), ("will", ("grain", "will")))
    ]
)
def test_next_word_selection(input_key, expected):
    """Test successor word selection."""
    with patch("src.generator.generator.Generator.load_model") as mock_load_model:
        mock_load_model.return_value = {
            ('If', 'you'): ['can'],
            ('you', 'can'): ['look'],
            ('can', 'look'): ['into'],
            ('look', 'into'): ['the'],
            ('into', 'the'): ['seeds'],
            ('the', 'seeds'): ['of'],
            ('seeds', 'of'): ['time,'],
            ('of', 'time,'): ['And'],
            ('time,', 'And'): ['say'],
            ('And', 'say'): ['which'],
            ('say', 'which'): ['grain'],
            ('which', 'grain'): ['will'],
            ('grain', 'will'): ['grow'],
            ('will', 'grow'): ['and'],
            ('grow', 'and'): ['which'],
            ('and', 'which'): ['will'],
            ('which', 'will'): ['not.']
        }
        g = generator.Generator()

    assert g.next_word(input_key) == expected

@patch("src.generator.generator.Generator.next_word")
def test_seed(mock_next_word):
    """Test seed given to generate."""
    with patch("src.generator.generator.Generator.load_model") as mock_load_model:
        mock_load_model.return_value = {
            ('If', 'you'): ['can'],
            ('you', 'can'): ['look']
        }
        g = generator.Generator()

    # Mock next_word to return determined words
    mock_next_word.side_effect = [("one", None), ("two", None), ("three", None)]

    seed = "A B If you" # the last 2 words has to be in the model
    res = g.generate(seed, size=7)

    assert res == "A B If you one two three"

@patch("src.generator.generator.Generator.next_word")
def test_sentence_completion(mock_next_word):
    """Are sentences continued until a natural break?"""
    with patch("src.generator.generator.Generator.load_model") as mock_load_model:
        mock_load_model.return_value = {
            ('If', 'you'): ['can']
        }
        g = generator.Generator()


    # terminate to punctuation: keep last word added
    mock_next_word.side_effect = [("a", None), ("b", None), ("C", None), ("D,", None), ("E?", None), ("F", None)]
    res = g.generate(complete_sentence=True, size=3)
    assert res == "A b C D, E?"

    # terminate due to conjunction: keep previous words
    mock_next_word.side_effect = [("a", None), ("b", None), ("C", None), ("D", None), ("E", None), ("and", None)]
    res = g.generate(complete_sentence=True, size=3)
    assert res == "A b C D E."
