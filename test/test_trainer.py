from unittest.mock import patch

from src.generator import trainer


@patch("src.utils.download_descriptions")
def test_model_train(mock_download_descriptions):
    """Test model train output on given input data."""
    mock_download_descriptions.return_value = "I am not a Russian spy, cross my heart and hope to die"
    t = trainer.Trainer()
    t.train()

    expected = {
        ("I", "am"): {"not"},
        ("am", "not"): {"a"},
        ("not", "a"): {"Russian"},
        ("a", "Russian"): {"spy,"},
        ("Russian", "spy,"): {"cross"},
        ("spy,", "cross"): {"my"},
        ("cross", "my"): {"heart"},
        ("my", "heart"): {"and"},
        ("heart", "and"): {"hope"},
        ("and", "hope"): {"to"},
        ("hope", "to"): {"die"}
    }
    assert t.model_data == expected

@patch("src.utils.download_descriptions")
def test_model_on_duplicate_successors(mock_download_descriptions):
    """Test model train with duplicate ngrams."""
    mock_download_descriptions.return_value = "almost too hot, almost too cold. almost too hot,"
    t = trainer.Trainer()
    t.train()

    expected = {
        ("almost", "too"): {"hot,", "cold."},
        ("too", "hot,"): {"almost"},
        ("hot,", "almost"): {"too"},
        ("too", "cold."): {"almost"},
        ("cold.", "almost"): {"too"}
    }
    assert t.model_data == expected
