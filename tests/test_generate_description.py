import json
import jsonschema
from unittest.mock import patch, MagicMock

import pytest

from app import generate_description



@pytest.fixture
def mock_generator():
    """Create a mock Generator class"""
    with patch("app.generator.generator.Generator") as MockGenerator:
        mock_gen_instance = MagicMock()
        MockGenerator.return_value = mock_gen_instance
        yield MockGenerator


def test_generated_description_schema(mock_generator):
    """Generated description object should match the schema
    in description_schema.json.
    """
    mock_generator().generate.return_value = ""
    g = generate_description.DescriptionGenerator()

    with open("tests/description_schema.json") as f:
        schema = json.load(f)

    jsonschema.validate(instance=g(), schema=schema)

@patch("random.randint")
@patch("random.choice")
def test_developer_generation_open(mock_random_choice, mock_random_randint):
    """Test developer template filling with 'open' (ie. {{}} selection."""

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
    """Test exclusivity of features and subsections in the config:
     * either subsections or features should be enabled
    """
    # since the numbers are randomized, roll n dice rolls and validate counts
    for _ in range(10):
        c = generate_description.create_config()

        assert c.num_subsections * c.num_features == 0
        assert max(c.num_subsections, c.num_features) > 0
