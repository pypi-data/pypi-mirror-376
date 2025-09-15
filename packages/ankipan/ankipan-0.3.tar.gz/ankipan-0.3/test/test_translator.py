from ankipan import Translator

def test_translation_prompt_parsing():
    t = Translator()
    res = t.parse_prompt_response("""
    - She was the daughter of Mithridates III and Iotapa, and [she had the blood of Armenia, Greece, and the Median kingdom.]
    - Albrecht IV, Duke of Mecklenburg Albrecht IV (German: Albrecht IV), before 1363 – December 24/31, 1388
    - The Duke of Windsor travelled to France by destroyer.
    - His main wins include the 1993 Sussex Stakes (G1).
    - It was stopped by the Nara Prefectural Police - the NPP.
""")
    assert len(res) == 5
