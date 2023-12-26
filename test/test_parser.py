from unittest.mock import patch

with patch("google.cloud.storage.Client"):
    from src import parser


def test_description_parsing_on_html_tags():
    """Are html tags remoevd and whitespace added between where a newline would be originalyl rendered?"""

    html = '<h2 class="bb_tag"><strong>INTRODUCTION</strong></h2><strong>Fight against all odds and repel an entire army from the great city of Itenbaal! \
    </strong><br><br>Without warning, an experimental battalion composed entirely of humadroids went haywire during a sandstorm and turned on their \
    very own place of creation.'
    
    expected = 'INTRODUCTION Fight against all odds and repel an entire army from the great city of Itenbaal! \
    Without warning, an experimental battalion composed entirely of humadroids went haywire during a sandstorm and turned on their \
    very own place of creation.'

    # Compare word list to avoid whitespace differences
    assert parser.html_description_to_text(html).split() == expected.split()


    # More tag filtering with an img src reference
    html = '</strong><br><br>Newgame+ is more than just a higher difficulty, more vicous enemies and boss encounters awaits you ahead! \
    <br><br><img src="https://cdn.akamai.steamstatic.com/steam/apps/359970/extras/Encounter.png?t=1608617814" />'
    
    expected = 'Newgame+ is more than just a higher difficulty, more vicous enemies and boss encounters awaits you ahead!'

    assert parser.html_description_to_text(html).split() == expected.split()

def test_description_parsing_with_whitespacing():
    """Is a whitespace added between sentences where a linebreak was originally rendered?"""
    html = 'low-maintenance as possible!<br><br><i>Which makes the current situation much worse. </i><br>'
    expected = 'low-maintenance as possible! Which makes the current situation much worse.'

    assert parser.html_description_to_text(html).split() == expected.split()


def test_description_parsing_on_special_tokens():
    """Are Twitter handles and other blacklisted tokens filtered?"""
    text = "<p>Wes Smith of Juice Recordings, San DiegoFollow us on fb.com/playrise and Twitter @PlayriseDigitalMore \
    information at the Playrise Digital website www.playrisedigital.com *Please adhere to the laws and age</p>"
    
    expected = "Wes Smith of Juice Recordings, San DiegoFollow us on and Twitter \
    information at the Playrise Digital website *Please adhere to the laws and age"

    assert parser.html_description_to_text(text).split() == expected.split()
