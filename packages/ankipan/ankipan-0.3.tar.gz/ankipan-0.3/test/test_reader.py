from pathlib import Path

from ankipan import Reader


STANZA_DELIMITER = '\n\n'

def test_subtitle_alignment():
    r = Reader('jp')
    files = r.open_files([Path('resources/example_subtitle.srt')])
    files[0].analyze_lemmas(r._get_shared_pipeline(0), get_indices=True)
    assert len(files[0].stanza_segments) == len(files[0].sub_timestamps)

def test_split_primary_index_splitting_basic():
    text = "A.B。C\nD"
    out = Reader.prepare_stanza_input(
        text,
        index_separators=[".", "。", "\n"],
        secondary_separators=[",", ";", "、"],
        thr=9999,
    )
    assert out == STANZA_DELIMITER.join(["A.", "B。", "C", "D"])

def test_split_secondary_greedy_splitting_english():
    text = "foo, bar, baz, qux."
    out = Reader.prepare_stanza_input(
        text,
        index_separators=[".", "。", "\n"],
        secondary_separators=[",", ";", "、"],
        thr=10,
    )
    assert out == STANZA_DELIMITER.join(["foo, bar,", "baz, qux."])

def test_split_no_secondary_split_when_short():
    text = "Short clause, ok."
    out = Reader.prepare_stanza_input(
        text,
        index_separators=[".", "。", "\n"],
        secondary_separators=[",", ";", "、"],
        thr=40,
    )
    assert out == "Short clause, ok."

def test_split_japanese_secondary_comma():
    text = "私は学生、そして研究者、時々作家です。"
    out = Reader.prepare_stanza_input(
        text,
        index_separators=["。"],
        secondary_separators=["、"],
        thr=8,
    )
    assert out == STANZA_DELIMITER.join(["私は学生、", "そして研究者、", "時々作家です。"])

def test_split_empty_input():
    out = Reader.prepare_stanza_input(
        "",
        index_separators=[".", "。", "\n"],
        secondary_separators=[",", ";", "、"],
        thr=10,
    )
    assert out == ""

def test_split_no_separators_present():
    text = "Just one long run without separators"
    out = Reader.prepare_stanza_input(
        text,
        index_separators=[".", "。", "\n"],
        secondary_separators=[",", ";", "、"],
        thr=1000,
    )
    assert out == text

def test_split_mixed_index_separators_in_one_pass():
    text = "Alpha. Beta。Gamma\nDelta, Epsilon; Zeta."
    out = Reader.prepare_stanza_input(
        text,
        index_separators=[".", "。", "\n"],
        secondary_separators=[",", ";", "、"],
        thr=25,
    )
    expected = STANZA_DELIMITER.join(["Alpha.", "Beta。", "Gamma", "Delta, Epsilon; Zeta."])
    assert out == expected
