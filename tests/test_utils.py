from unittest.mock import patch

from app import setup_gcs_models

with patch("google.cloud.storage.Client"):
    from app import utils


def test_merge_requirements_list():
    """A list containing requirements from multiple source
    files should be merged into one.
    """
    requirements = [
        {
            "requirements": {
                "OS": ["Windows 7 / 8 / 10"],
                "Processor": ["1.5 Ghz"],
                "Memory": ["256 MB RAM"],
                "Graphics": ["256 MB", "128 MB"],
                "DirectX": ["Version 9.0"],
                "Storage": ["250 MB available space"],
                "Sound Card": ["DirectX comaptble Soundcard"],
            }
        },
        {
            "requirements": {
                "OS": [
                    "Ubuntu 18.04 (64-bit)",
                    "Windows 10 or higher (64-bit)",
                ],
                "Processor": [
                    "3.2 Ghz Quad Core CPU or faster",
                    "2.8 Ghz Quad Core CPU",
                ],
                "Memory": ["8 GB RAM", "12 GB RAM"],
                "Graphics": ["2 GB Dedicated Memory", "4 GB Dedicated Memory"],
                "DirectX": ["Version 11"],
                "Network": ["Broadband Internet connection"],
                "Storage": ["15 GB available space"],
                "Sound Card": ["Sound Card"],
                "Additional Notes": [
                    "Running the Dedicated Server and Client on the same computer will double ram requirements. Also future releases may require more hard drive space.",
                    "Running a Dedicated Server and Client on the same computer will double ram requirements. Also future releases may require more hard drive space.",
                ],
            }
        },
        {
            "requirements": {
                "OS": ["Windows XP, Vista, 7, 8, or 10"],
                "Processor": ["1.2 GHZ"],
                "Memory": ["2 GB RAM"],
                "Storage": ["256 MB available space"],
            }
        },
    ]

    expected = {
        "OS": [
            "Windows 7 / 8 / 10",
            "Ubuntu 18.04 (64-bit)",
            "Windows 10 or higher (64-bit)",
            "Windows XP, Vista, 7, 8, or 10",
        ],
        "Processor": [
            "1.5 Ghz",
            "3.2 Ghz Quad Core CPU or faster",
            "2.8 Ghz Quad Core CPU",
            "1.2 GHZ",
        ],
        "Memory": ["256 MB RAM", "8 GB RAM", "12 GB RAM", "2 GB RAM"],
        "Graphics": [
            "256 MB",
            "128 MB",
            "2 GB Dedicated Memory",
            "4 GB Dedicated Memory",
        ],
        "DirectX": ["Version 9.0", "Version 11"],
        "Storage": [
            "250 MB available space",
            "15 GB available space",
            "256 MB available space",
        ],
        "Sound Card": ["DirectX comaptble Soundcard", "Sound Card"],
        "Additional Notes": [
            "Running the Dedicated Server and Client on the same computer will double ram requirements. Also future releases may require more hard drive space.",
            "Running a Dedicated Server and Client on the same computer will double ram requirements. Also future releases may require more hard drive space.",
        ],
    }

    assert setup_gcs_models._merge_requirements(requirements) == expected


def test_ignore_non_whitelisted_caegories():
    """Non-whitelisted categories should be ignored."""
    requirements = [
        {
            "requirements": {
                "OS": ["Windows 7 / 8 / 10"],
                "Processor": ["1.5 Ghz"],
                "Memory": ["256 MB RAM"],
                "Graphics": ["256 MB", "128 MB"],
                "DirectX": ["Version 9.0"],
                "Storage": ["250 MB available space"],
                "Extra Category": ["80 Flerps / herz"]
            }
        }
    ]

    expected = {
        "OS": ["Windows 7 / 8 / 10"],
        "Processor": ["1.5 Ghz"],
        "Memory": ["256 MB RAM"],
        "Graphics": ["256 MB", "128 MB"],
        "DirectX": ["Version 9.0"],
        "Storage": ["250 MB available space"],
        "Additional Notes": []  # Missing category should default to an empty list
    }

    assert setup_gcs_models._merge_requirements(requirements) == expected

def test_merge_similar_categories():
    """Some categories can occur with different keys in different sources.
    These should be ignored.
    """
    requirements = [
        {
            "requirements": {
                "OS": ["Windows 7 / 8 / 10"],
                "Processor": ["1.5 Ghz"],
                "Memory": ["256 MB RAM"],
                "Storage": ["250 MB available space"]
            }
        },
        {
            "requirements": {
                "Hard Disk Space": ["15 GB available space"]
            }
        },
        {
            "requirements": {
                "Additional": ["A powered computer recommended"]
            }
        }

    ]

    expected = {
        "OS": ["Windows 7 / 8 / 10"],
        "Processor": ["1.5 Ghz"],
        "Memory": ["256 MB RAM"],
        "Storage": [
            "250 MB available space",
            "15 GB available space"
            ],
        "Additional Notes": ["A powered computer recommended"]
    }

    assert setup_gcs_models._merge_requirements(requirements) == expected
