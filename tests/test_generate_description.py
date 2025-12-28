import json
import jsonschema
from unittest.mock import patch, MagicMock

import pytest

with patch("google.cloud.storage.Client"):
    from app import generate_description


@pytest.fixture
def mock_generator():
    with patch("app.generator.generator.Generator") as MockGenerator:
        mock_gen_instance = MagicMock()
        MockGenerator.return_value = mock_gen_instance
        yield MockGenerator


def test_generated_description_schema(mock_generator):
    """Generated description object should match the schema
    in description_schema.json.
    """
    # Mock each generator to return a dummy string
    mock_generator().generate.return_value = ""
    with patch("app.utils.gcs._download_all_model_files") as mock_download_all_model_files:
        g = generate_description.DescriptionGenerator(MagicMock())

    with open("tests/description_schema.json") as f:
        schema = json.load(f)

    jsonschema.validate(instance=g(), schema=schema)

def test_render_template_with_no_tokens():
    """Template rendering should return the original value
    when there's no tokens to replace.
    """
    rendered = generate_description._render_template("A B C")
    assert rendered == "A B C"

@patch("random.randint")
@patch("random.choice")
def test_render_template_with_open_token(mock_choice, mock_randint):
    """Test template rendering with {{}} token."""

    # mock random calls to select 2 items
    mock_randint.return_value = 2
    mock_choice.side_effect = ["A", "B"]

    template = "{{}} System Works"
    rendered = generate_description._render_template(template)
    assert rendered == "A B System Works"

@patch("random.randint")
@patch("random.choice")
def test_render_template_with_undetermined_token(mock_choice, mock_randint):
    """Test template rendering with {{?}} token."""

    # One replacement items
    mock_randint.return_value = 1
    mock_choice.return_value = "A"

    template = "{{?}} Gaming"
    rendered = generate_description._render_template(template)
    assert rendered == "A Gaming"

    # No replacement items
    mock_randint.return_value = 0

    template = "{{?}} Gaming"
    rendered = generate_description._render_template(template)
    assert rendered == "Gaming"

@patch("random.sample")
def test_render_template_with_determined_token(mock_sample):
    """Test template rendering with known tokens like {{NOUN}}."""
    mock_sample.side_effect = [["A", "B"], ["C"]]

    template = "{{VERB}} of the {{NOUN}}"
    rendered = generate_description._render_template(template)
    assert rendered == "A B of the C"

def test_number_of_paragraphs_in_config():
    """Test exclusivity of features and subsections in the config:
     * either subsections or features should be enabled
    """
    # since the numbers are randomized, roll n dice rolls and validate counts
    for _ in range(10):
        c = generate_description.create_description_config()

        assert c.num_subsections * c.num_features == 0
        assert max(c.num_subsections, c.num_features) > 0
