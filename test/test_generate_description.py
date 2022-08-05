from unittest.mock import patch

from src import generate_description


@patch("random.randint")
@patch("random.choice")
def test_developer_generation_open(mock_random_choice, mock_random_randint):
    """Test developer template filling with 'open' (ie. {{}}) selection."""

    # Mock random.X calls to return 2 replacement words
    mock_random_randint.return_value = 2
    mock_random_choice.side_effect = ["{{}} System Works", "A", "B"]

    res = generate_description.generate_developer()
    assert res == "A B System Works"

@patch("random.sample")
@patch("random.randint")
@patch("random.choice")
def test_developer_generation_undetermined(mock_random_choice, mock_random_randint, mock_random_sample):
    """Test developer template filling with 'undetermined' (ie. {{?}}) selection."""

    mock_random_randint.side_effect = [1, 1]
    mock_random_choice.side_effect = ["{{?}} {{NOUN}} Gaming", "A"]
    mock_random_sample.return_value = "B"

    res = generate_description.generate_developer()
    assert res == "A B Gaming"

def test_number_of_paragraphs_in_config():
    """Test exclusivity of features and subsections in the config."""
    c = generate_description.create_config()

    assert c["subsections"] * c["features"] == 0
    assert max(c["subsections"], c["features"]) > 0
