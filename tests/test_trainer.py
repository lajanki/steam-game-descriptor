from unittest.mock import patch

from app.generator import trainer


def test_model_train():
    """Test model train output on given input data."""
    train_text_data = "I am not a Russian spy, cross my heart and hope to die"
    t = trainer.Trainer(train_text_data, "dummy_filename")
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
    assert t.model == expected

def test_model_on_duplicate_successors():
    """Test model train with duplicate ngrams."""
    train_text_data = "almost too hot, almost too cold. almost too hot,"
    t = trainer.Trainer(train_text_data, "dummy_filename")
    t.train()

    expected = {
        ("almost", "too"): {"hot,", "cold."},
        ("too", "hot,"): {"almost"},
        ("hot,", "almost"): {"too"},
        ("too", "cold."): {"almost"},
        ("cold.", "almost"): {"too"}
    }
    assert t.model == expected
