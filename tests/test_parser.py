from unittest.mock import patch

with patch("google.cloud.storage.Client"):
    from app import parser


def test_description_parsing_on_html_tags():
    """Are html tags remoevd and whitespace added between where a newline would be originalyl rendered?"""
    ## Simple example with headers and emphasis tags
    html = '<h2 class="bb_tag"><strong>INTRODUCTION</strong></h2><strong>Fight against all odds and repel an entire army from the great city of Itenbaal! \
    </strong><br><br>Without warning, an experimental battalion composed entirely of humadroids went haywire during a sandstorm and turned on their \
    very own place of creation.'
    
    expected = 'INTRODUCTION Fight against all odds and repel an entire army from the great city of Itenbaal! \
    Without warning, an experimental battalion composed entirely of humadroids went haywire during a sandstorm and turned on their \
    very own place of creation.'

    # Compare word list to avoid whitespace differences
    assert parser._html_string_to_text(html).split() == expected.split()

    ## More tag filtering with an img src reference
    html = '</strong><br><br>Newgame+ is more than just a higher difficulty, more vicous enemies and boss encounters awaits you ahead! \
    <br><br><img src="https://cdn.akamai.steamstatic.com/steam/apps/359970/extras/Encounter.png?t=1608617814" />'
    
    expected = 'Newgame+ is more than just a higher difficulty, more vicous enemies and boss encounters awaits you ahead!'

    assert parser._html_string_to_text(html).split() == expected.split()

def test_description_parsing_with_whitespacing():
    """Is a whitespace added between sentences where a linebreak was originally rendered?"""
    html = 'low-maintenance as possible!<br><br><i>Which makes the current situation much worse. </i><br>'
    expected = 'low-maintenance as possible! Which makes the current situation much worse.'

    assert parser._html_string_to_text(html).split() == expected.split()

def test_description_parsing_on_special_tokens():
    """Are Twitter handles and other blacklisted tokens filtered?"""
    text = "<p>Wes Smith of Juice Recordings, San DiegoFollow us on fb.com/playrise and Twitter @PlayriseDigitalMore \
    information at the Playrise Digital website www.playrisedigital.com *Please adhere to the laws and age</p>"
    
    expected = "Wes Smith of Juice Recordings, San DiegoFollow us on and Twitter \
    information at the Playrise Digital website *Please adhere to the laws and age"

    assert parser._html_string_to_text(text).split() == expected.split()

def test_description_parsing_on_regular_string():
    """html parsing should have no effect on regular string."""
    text = 'Fight against all odds and repel an entire army from the great city of Itenbaal! \
    Without warning, an experimental battalion composed entirely of humadroids went haywire during a sandstorm and turned on their \
    very own place of creation.'

    assert parser._html_string_to_text(text).split() == text.split()

def test_requirements_parsing():
    """Test system requirement extraction on html strings."""
    ## pc_requirements only; minimum and recommended
    data = {
        "pc_requirements": {
            "minimum":"""
            <strong>Minimum:</strong><br>
            <ul class="bb_ul">
                <li><strong>OS *:</strong> Windows 7/8.1/10 (64-bit versions)<br></li>
                <li><strong>Processor:</strong> Intel Core i5-2400/AMD FX-8320 or better<br></li>
                <li><strong>Memory:</strong> 8 GB RAM<br></li>
                <li><strong>Graphics:</strong> NVIDIA GTX 670 2GB/AMD Radeon HD 7870 2GB or better<br></li>
                <li><strong>Storage:</strong> 55 GB available space<br></li>
                <li><strong>Additional Notes:</strong> Requires Steam activation and broadband internet connection for Multiplayer and SnapMap</li>
            </ul>""",
            "recommended":"""
                <strong>Recommended:</strong><br>
                <ul class="bb_ul">
                    <li><strong>OS *:</strong> Windows 7/8.1/10 (64-bit versions)<br></li>
                    <li><strong>Processor:</strong> Intel Core i7-3770/AMD FX-8350 or better<br></li>
                    <li><strong>Memory:</strong> 8 GB RAM<br></li><li><strong>Graphics:</strong> NVIDIA GTX 970 4GB/AMD Radeon R9 290 4GB or better<br></li>
                    <li><strong>Storage:</strong> 55 GB available space<br></li>
                    <li><strong>Additional Notes:</strong> Requires Steam activation and broadband internet connection for Multiplayer and SnapMap</li>
                </ul>""",
        },
        "mac_requirements": [],
        "linux_requirements": [],
    }

    expected = {
        "OS": {"Windows 7/8.1/10 (64-bit versions)"},
        "Processor": {
            "Intel Core i5-2400/AMD FX-8320 or better",
            "Intel Core i7-3770/AMD FX-8350 or better",
        },
        "Memory": {"8 GB RAM"},
        "Graphics": {
            "NVIDIA GTX 670 2GB/AMD Radeon HD 7870 2GB or better",
            "NVIDIA GTX 970 4GB/AMD Radeon R9 290 4GB or better",
        },
        "Storage": {"55 GB available space"},
        "Additional Notes": {
            "Requires Steam activation and broadband internet connection for Multiplayer and SnapMap"
        },
    }

    ## More complex example; minimum requirements for multiple OS
    data = {
        "pc_requirements": {
            "minimum": """
                <strong>Minimum:</strong><br>
                <ul class="bb_ul">
                    <li><strong>OS *:</strong> Windows 7/8 64 bit or higher<br></li>
                    <li><strong>Processor:</strong> Intel Core2 Duo or better<br></li>
                    <li><strong>Memory:</strong> 4 GB RAM<br></li><li><strong>Graphics:</strong> DirectX 10.1 compatible 512 MB<br></li>
                    <li><strong>DirectX:</strong> Version 11<br></li><li><strong>Storage:</strong> 700 MB available space<br></li>
                    <li><strong>Sound Card:</strong> DirectX 9.0c compatible<br></li>
                    <li><strong>Additional Notes:</strong> Mouse recommended. Passing can be difficult with the touch pad on some laptops.</li>
                </ul>"""
        },
        "mac_requirements": {
            "minimum": """
                <strong>Minimum:</strong><br>
                <ul class="bb_ul">
                    <li><strong>OS:</strong> Mac OS X 10.6<br></li>
                    <li><strong>Processor:</strong> Quad core Intel or AMD processor, 2.5 GHz +<br></li>
                    <li><strong>Memory:</strong> 4 GB RAM</li>
                </ul>"""
        },
        "linux_requirements": {
            "minimum": """
                <strong>Minimum:</strong><br>
                <ul class="bb_ul">
                    <li><strong>Processor:</strong> Quad core Intel or AMD processor, 2.5 GHz +<br></li>
                    <li><strong>Memory:</strong> 4 GB RAM</li>
                </ul>"""
        },
    }

    expected = {
        "OS": {"Mac OS X 10.6", "Windows 7/8 64 bit or higher"},
        "Processor": {
            "Intel Core2 Duo or better",
            "Quad core Intel or AMD processor, 2.5 GHz +",
        },
        "Memory": {"4 GB RAM"},
        "Graphics": {"DirectX 10.1 compatible 512 MB"},
        "DirectX": {"Version 11"},
        "Storage": {"700 MB available space"},
        "Sound Card": {"DirectX 9.0c compatible"},
        "Additional Notes": {
            "Mouse recommended. Passing can be difficult with the touch pad on some laptops."
        },
    }

    assert parser._extract_requirements(data) == expected

def test_ratings_parsing():
    """Test ratings parsing to a list."""

    # Valid rating providers
    data = {
        "ratings": {
            "esrb": {
                "rating": "m",
                "use_age_gate": "true",
                "required_age": "17",
                "descriptors": "Intense Violence\r\nBlood and Gore\r\nNudity\r\nMature Humor\r\nStrong Language\r\nStrong Sexual Content\r\nUse of Drugs and Alcohol"
            },
            "kgrb": {
                "rating": "18",
                "use_age_gate": "true",
                "required_age": "18",
                "descriptors": "Game Descriptive: Sexual Content, Violence, Inappropriate Language, Drug, Crime, Gambling \r\n\r\nTitle Name:"
            },
            "pegi": {
                "rating": "18",
                "descriptors": "Violence\r\nOnline Play,\r\nStrong Language",
                "use_age_gate": "true",
                "required_age": "17"
            },
            "usk": {
                "rating": "18",
                "use_age_gate": "true",
                "required_age": "17"
            }
        }
    }

    expected = [
        "Intense Violence Blood and Gore Nudity Mature Humor Strong Language Strong Sexual Content Use of Drugs and Alcohol",
        "Violence Online Play, Strong Language",
        "Game Descriptive: Sexual Content, Violence, Inappropriate Language, Drug, Crime, Gambling   Title Name:"
    ]

    assert parser._extract_content_rating(data) == expected

    # Missing ratings
    data = {
        "ratings": None
    }
    assert parser._extract_content_rating(data) == []

    # No valid providers
    data = {
        "ratings": {
            "foo": {
                "descriptors": "Intense Violence\r\nBlood and Gore"
            },
            "bar": {
                "descriptors": "Game Descriptive: Sexual Content"
            }
        }
    }

    assert parser._extract_content_rating(data) == []
