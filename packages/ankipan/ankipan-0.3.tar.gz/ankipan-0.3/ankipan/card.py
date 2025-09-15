import functools
from jinja2 import Template
import logging
from typing import Dict, List, Iterable, Any, Optional, Callable
from collections import UserDict, UserList
from functools import wraps
from dataclasses import asdict

from ankipan import HTML_TEMPLATE_DIR, TextSegment, load_json
from ankipan.scraper import CardSection

logger = logging.getLogger(__name__)


class Card:
    def __init__(self,
                 word: str,
                 *,
                 deck_example_sentences: List[TextSegment] = None,
                 json_path: str = None,
                 anki_id: int = None):
        """
        Flashcard object.

        Backside contents are kept in two dicts:
          - definition_fields: general definitions (dictionaries etc.)
          - example_sentences_fields: example sentences from sources specified in collection

        Values are lazy-loaded from json to prevent a collection with many cards from cluttering memory.

        Parameters
        ----------
        word: Word of the flashcard
        json_path: path to local json path with all fields (saves compute for many cards)
        sources: added sources where this word occurs
        anki_id: optional, filled when card is synced with anki
        """
        self.word = word
        self.json_path = json_path
        self._anki_id = anki_id

        self.was_modified = False
        self.is_initialized = False if json_path else True

        self._definition_fields: Dict[str, CardSection] = {}
        self._example_sentences_fields: Dict[str, CardSection] = {}

        self._deck_example_sentences: List[TextSegment] = deck_example_sentences if deck_example_sentences else []

    def ensure_initialized(method):
        """
        Lazy loading of card content from json file.

        """
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            if not self.is_initialized and self.json_path:
                card_dict = load_json(self.json_path)
                self._anki_id = card_dict.get('anki_id')
                self._definition_fields = {field_name: CardSection.from_dict(field) for field_name, field in card_dict.get('definition_fields', {}).items()}
                self._example_sentences_fields = {field_name: CardSection.from_dict(field) for field_name, field in card_dict.get('example_sentences_fields', {}).items()}
                self._deck_example_sentences = [TextSegment(**example_sentence) for example_sentence in card_dict.get('deck_example_sentences', [])]
            self.is_initialized = True
            return method(self, *args, **kwargs)
        return wrapper

    @ensure_initialized
    def touch(self):
        if not self.was_modified:
            self.was_modified = True

    @property
    def definition_fields(self):
        self.touch()
        return self._definition_fields

    @property
    def example_sentences_fields(self):
        self.touch()
        return self._example_sentences_fields

    @property
    def deck_example_sentences(self):
        self.touch()
        return self._deck_example_sentences

    @property
    @ensure_initialized
    def anki_id(self):
        return self._anki_id

    @anki_id.setter
    @ensure_initialized
    def anki_id(self, value):
        self._anki_id = value
        if not self.was_modified:
            self.was_modified = True

    @property
    def frontside(self):
        return f'<p style="font-size: 30px;">{self.word}</p>'

    @property
    @ensure_initialized
    def backside(self):
        """
        Generate flashcard html from downloaded fields
        """
        with open(HTML_TEMPLATE_DIR / 'static.html', 'r') as f:
            static = f.read()
        css_files = HTML_TEMPLATE_DIR.glob('*.css')
        css = '\n'.join(css_file.read_text(encoding='utf-8') for css_file in css_files)
        js_files = HTML_TEMPLATE_DIR.glob('*.js')
        js = '\n'.join(js_file.read_text(encoding='utf-8') for js_file in js_files)

        with open(HTML_TEMPLATE_DIR / 'flashcard.html', 'r') as f:
            template = Template(f.read())

        content = [str(field) for field in self.example_sentences_fields.values()] + \
                  [str(field) for field in self.definition_fields.values()]
        back = template.render(
            static_content=static,
            css_content=css,
            js_content=js,
            flashcard_content='<br>'.join(content),
        )
        return back

    @ensure_initialized
    def as_dict(self):
        """
        Dump card info as dict
        Relevant when storing nosql database and for printing
        """
        return {
            'definition_fields': {field_name: field.as_dict()
                                  for field_name, field in self.definition_fields.items()},
            'example_sentences_fields': {field_name: field.as_dict()
                                  for field_name, field in self.example_sentences_fields.items()},
            'deck_example_sentences': [asdict(text_segment) for text_segment in  self.deck_example_sentences],
            'anki_id': self.anki_id
        }

    @ensure_initialized
    def __str__(self):
        return f'word: {self.word}\n' + \
               'definition fields with content: \n' + \
               '\n'.join([f'    {field_name}' for field_name in self.definition_fields.keys()]) + '\n' + \
               'example sentences fields with content: \n' + \
               '\n'.join([f'    {field_name}' for field_name in self.example_sentences_fields.keys()]) + '\n' + \
               'example sentences from deck: \n' + \
               '\n'.join([f'    - {deck_example_sentence}' for deck_example_sentence in self.deck_example_sentences]) + '\n' + \
               f'anki_id: {self.anki_id}'
