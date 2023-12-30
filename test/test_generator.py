from unittest.mock import patch

import pytest

with patch("google.cloud.storage.Client"):
    from src.generator import generator



@pytest.mark.parametrize(
    "input_key,expected_word,expected_output_key",
    [
        (("If", "you"), "can", ("you", "can")),
        (("which", "grain"), "will", ("grain", "will"))
    ]
)
def test_next_word_selection(input_key, expected_word, expected_output_key):
    """Test model behaviour on successor word selection:
    is the expected word selected and key updated?
    Note: uses single element successor lists to force-select predetermined words
    """
    with patch("src.generator.generator.Generator._load_model") as mock_load_model:
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
        g = generator.Generator("dummy_filename")
        # Fix the initial key so output can be determined
        g._key = input_key

    assert g.get_word() == expected_word
    assert g._key == expected_output_key


@patch("src.generator.generator.Generator.get_word")
def test_valid_seed(mock_get_word):
    """Test generation with valid seed."""
    with patch("src.generator.generator.Generator._load_model") as mock_load_model:
        mock_load_model.return_value = {
            ('If', 'you'): ['can'],
            ('you', 'can'): ['look']
        }
        g = generator.Generator("dummy_filename")

    # Mock get_word to return determined words
    mock_get_word.side_effect = ["one", "two", "three"]

    res = g.generate(seed="A B If you", size=7)
    assert res == "A B If you one two three"

@patch("src.generator.generator.Generator.get_word")
def test_invalid_seed(mock_get_word):
    """Test generation with invalid seed:
    Something should be generated even when seed is not an element of the model.
    (this is mainly to test no execptions are raised)
    """
    with patch("src.generator.generator.Generator._load_model") as mock_load_model:
        mock_load_model.return_value = {
            ('If', 'you'): ['can'],
            ('you', 'can'): ['look']
        }
        g = generator.Generator("dummy_filename")

    mock_get_word.side_effect = ["foo"] * 7

    res = g.generate(seed="No such element", size=7)
    assert len(res.split()) == 7

@patch("src.generator.generator.Generator.get_word")
def test_sentence_completion(mock_get_word):
    """Are sentences continued until a natural break?"""
    with patch("src.generator.generator.Generator._load_model") as mock_load_model:
        mock_load_model.return_value = {
            ('If', 'you'): ['can']
        }
        g = generator.Generator("dummy_filename")


    # terminate to punctuation: stop at last word added
    mock_get_word.side_effect = ["a", "b", "C", "D,", "E?", "F"]
    res = g.generate(complete_sentence=True, size=3)
    assert res == "A b C D, E?"

    # terminate due to conjunction: stop at previous word
    mock_get_word.side_effect = ["a", "b", "C", "D", "E", "and"]
    res = g.generate(complete_sentence=True, size=3)
    assert res == "A b C D E."

def test_output_cleanup():
    """Are special characters removed during string cleanup?"""
    with patch("src.generator.generator.Generator._load_model") as mock_load_model:
        mock_load_model.return_value = {
            ('If', 'you'): ['can'],
            ('you', 'can'): ['look']
        }

        g = generator.Generator("")

    # 1st word capitalized
    tokens = "upgrade and expand your".split()
    assert g.cleanup(tokens) == "Upgrade and expand your"

    # 1st word not changed if already uppercase
    tokens = "EMP devices to aid in your stealthy endeavors.".split()
    assert g.cleanup(tokens) == "EMP devices to aid in your stealthy endeavors."

    # Special characters are replaced
    tokens = "there are those who (call me) heroic®".split()
    assert g.cleanup(tokens) == "There are those who call me heroic"
