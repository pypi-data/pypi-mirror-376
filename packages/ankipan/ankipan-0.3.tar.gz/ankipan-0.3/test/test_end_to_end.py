import tempfile
from pathlib import Path
import pytest

from ankipan import Collection, Scraper

def test_split_primary_index_splitting_basic(monkeypatch):
    def mock_get_text_segments_translation(self, example_sentences, cache_server, cache_translations = True):
        """mock method to avoid gemini api calls"""
        res = {}
        for example_sentence in example_sentences:
            res[example_sentence.main_segment] = f'Mock translation of "{example_sentence.main_segment}"'
        return res

    with tempfile.TemporaryDirectory() as temp_dir:
        monkeypatch.setattr(
            Scraper,
            "get_text_segments_translation",
            mock_get_text_segments_translation,
            raising=True,
        )
        collection = Collection('testcollection', learning_lang='jp', native_lang='en', data_dir=Path(temp_dir))
        collection.set_flashcard_fields(definitions=['wikitionary_en'],
                                        example_sentence_source_paths=['ankipan_default/wikipedia'])
        words = collection.collect(string='かつてこの世の全てを手に入れた男、〝海賊王〟ゴールド・ロジャー。')
        collection.add_deck(words, 'testsource')
        assert list(collection.cards.keys()) == ['世', '全て', '手', '入れる', '男', '海賊', '王']

        collection.fetch('testsource')
        assert collection.cards['世'].definition_fields.get('wikitionary_en')
        assert collection.cards['世'].example_sentences_fields.get('deck_example_sentences')
        assert collection.cards['世'].example_sentences_fields.get('ankipan_default/wikipedia')

        collection = Collection('testcollection', data_dir=Path(temp_dir)) # load from local storage
        assert collection.cards['世'].definition_fields.get('wikitionary_en')
        assert collection.cards['世'].example_sentences_fields.get('deck_example_sentences')
        assert collection.cards['世'].example_sentences_fields.get('ankipan_default/wikipedia')
