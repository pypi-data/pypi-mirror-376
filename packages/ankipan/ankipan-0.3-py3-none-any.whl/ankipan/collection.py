from pathlib import Path
from collections import OrderedDict, Counter
from copy import deepcopy
import logging
import shutil
from collections.abc import Iterable
import fnmatch
from dataclasses import dataclass, field
from itertools import zip_longest

from typing import Union, Dict, Iterable, List

from ankipan import Deck, Card, Reader ,TextSegment, Scraper, AnkiManager, CardSection, Client, \
    PROJECT_ROOT, DATA_DIR, load_json, save_json
from ankipan.util import estimate_proficiency, pad_clip

logger = logging.getLogger(__name__)

class AvailableSources(OrderedDict):
    def __init__(self, available_by_server: dict, learning_lang: str, present_words: set | None = None):
        super().__init__()
        self.learning_lang = learning_lang
        self.present_words = present_words or set()
        for server_name, sources in (available_by_server or {}).items():
            self[server_name] = self.SourceNode(self, (server_name,))
            for src in sources:
                self[server_name].ensure_child(src)

    @dataclass
    class SourceNode:
        owner: "AvailableSources"
        path: tuple[str, ...]
        metadata: dict = field(default_factory=dict)
        lemma_counts: dict = field(default_factory=dict)
        children: dict[str, "SourceNode"] = field(default_factory=dict)

        @property
        def name(self) -> str:
            return self.path[-1] if self.path else "<root>"

        @property
        def is_leaf(self) -> bool:
            return not self.children

        def child(self, name: str) -> "SourceNode":
            return self.children[name]

        def ensure_child(self, name: str) -> "SourceNode":
            return self.children.setdefault(name, AvailableSources.SourceNode(self.owner, self.path + (name,)))

        def __str__(self) -> str:
            present = getattr(self.owner, "present_words", None) or set()

            meta = [f"{k}: {v}" for k, v in (self.metadata or {}).items()]
            lemmas = [f"{l}: {n}" for l, n in Counter(self.lemma_counts or {}).most_common(200) if l not in present]
            kids = [str(c) for c in sorted(self.children or [])]

            def titled(title, lines):
                return [title, "-" * len(title)] + (lines if lines else ["<none>"])

            col1 = titled("Metadata", meta)
            col2 = titled("Top 200 lemma counts", [f"- {x}" for x in lemmas])
            col3 = titled("Children", [f"- {x}" for x in kids])

            total = shutil.get_terminal_size((100, 20)).columns
            gap = "   "
            colw = max(20, (total - 2 * len(gap)) // 3)

            lines = [f"[{self.name}]\n"]
            for a, b, c in zip_longest(col1, col2, col3, fillvalue=""):
                lines.append(
                    pad_clip(a, colw) + gap +
                    pad_clip(b, colw) + gap +
                    pad_clip(c, colw)
                )

            if len(lines) == 1:
                lines.append("<no info>")
            return "\n".join(lines)

    def _walk(self, segments: list[str], create: bool = False) -> SourceNode | None:
        if not segments:
            return None
        node = self.get(segments[0])
        if node is None:
            return None
        for seg in segments[1:]:
            if create:
                node = node.ensure_child(seg)
            else:
                node = node.children.get(seg)
                if node is None:
                    return None
        return node

    def __call__(self, source_path: str | None = None, *, use_cache: bool = True):
        return self._get_source(source_path=source_path, use_cache=use_cache)

    def __str__(self) -> str:
        if not self:
            return ""
        lines = []
        for server, root in self.items():
            for child in sorted(root.children):
                lines.append(f"- {server}/{child}")
            lines.append("")
        return "\n".join(lines)

    def _get_source(self, source_path: str | None = None, use_cache: bool = True):
        if not source_path:
            return str(self)

        parts = source_path.strip("/").split("/")
        node = self._walk(parts, create=True)
        if node is None:
            raise KeyError("Unknown path component")

        if not (node.metadata or node.lemma_counts or node.children) or not use_cache:
            node.metadata, node.lemma_counts, children = Client.source_list(self.learning_lang, source_path)
            for child_name in children:
                node.ensure_child(child_name)
        return node

class Collection:
    def __init__(self,
                 name: str,
                 learning_lang: str = None,
                 native_lang: str = None,
                 *,
                 data_dir = DATA_DIR):
        """
        Load new or existing collection.
        A collection can hold 0 to n decks.
        A deck can hold 1 to n flashcards.
        Flashcards have 1 to n fields, which refers to information on the backside (dictionary definitions, example sentences etc.)

        Parameters
        ----------
        name : Name of collection.
            Creates new collection for new names, loads existing collection for existing names.
        learning_lang : Name of language the user wants to learn.
        native_lang : Native language of the user for translations and explanations.

        """
        self.name = name
        self.data_dir = data_dir
        self.metadata_path = data_dir / name / 'metadata.json'
        self.flashcard_data_dir = data_dir / name / 'flashcard_fields'
        metadata = load_json(self.metadata_path)
        if metadata:
            if learning_lang or native_lang:
                raise RuntimeError(f'Initializing existing database "{name}", specified kwargs would be ignored')
            self.learning_lang = metadata.get('learning_lang', learning_lang)
            self.native_lang = metadata.get('native_lang', native_lang)
            self.flashcard_fields = metadata.get('flashcard_fields', {})
            self.decks = {deck_name: [Card(word, json_path = self.flashcard_data_dir / f'{word}.json') for word in words] for deck_name, words in metadata.get('decks', {}).items()}
            self.known_words = set(metadata.get('known_words', []))
        else:
            if not (learning_lang and native_lang):
                raise RuntimeError('learning_lang and native_lang kwargs required when initializing new collection')
            self.learning_lang = learning_lang
            self.native_lang = native_lang
            self.flashcard_fields = {'definitions': [], 'example_sentence_source_paths': []}
            self.decks = {}
            self.known_words = set()

        self.anki_manager = AnkiManager()
        self.reader = Reader(self.learning_lang)
        self.scraper = Scraper(self.learning_lang, self.native_lang)
        self.database_unavailable = False
        self._available_definition_fields = None
        self._available_example_sentence_sources = None

    @property
    def cards(self):
        return {card.word: card for cards in self.decks.values() for card in cards}

    @property
    def available_definition_fields(self):
        if not self._available_definition_fields:
            self._available_definition_fields = [func.removeprefix('fetch_') for func in fnmatch.filter([func for func in dir(Scraper)
                                                 if callable(getattr(Scraper, func))], 'fetch_*')]
        return self._available_definition_fields

    @property
    def available_example_sentence_sources(self) -> AvailableSources:
        if self.database_unavailable:
            logger.warning(
                "Previous database connection attempt was unsuccessful; "
                "not attempting to reconnect until Collection.database_unavailable is set to False again"
            )
            return self._available_example_sentence_sources or AvailableSources({}, self.learning_lang, set().union(self.cards, self.known_words))

        if self._available_example_sentence_sources is None:
            try:
                self._available_example_sentence_sources = AvailableSources(Client.available_example_sentence_sources(self.learning_lang),
                                                                            self.learning_lang,
                                                                            set().union(self.cards, self.known_words))
            except Exception as e:
                import traceback
                print(traceback.print_exc())
                logger.error(f"Server to fetch sources not available: {e}")
                self.database_unavailable = True
                return AvailableSources({}, self.learning_lang, set().union(self.cards, self.known_words))
        return self._available_example_sentence_sources

    def set_flashcard_fields(self,
                             definitions: List[str] = None,
                             example_sentence_source_paths: List[str] = None):
        """
        Tracks categories of sources and
        concrete sources that the user is familiar with.


        Parameters
        ----------
        definitions : list of strings
            List of definitions for the flashcards
            see `collection.available_definition_fields`
        example_sentence_source_paths : list of strings
            List of sources to collect example sentences from.
            When flashcards are generated, example sentences for all root categories from all paths will be considered, where specified sources will be prioritized and highlighted.
            e.g. if we specify "ankipan_default/youtube/sushiramen" and "ankipan_default/youtube/hajimesyacho", then flashcards will contain a "youtube" example sentence section,
            where the specified youtubers are included alongside other sources from youtube (~50-50 split).
            Only specifying "ankipan_default/youtube" will cause this youtube example sentence section to only contain various youtubers with no preference.
        """
        invalid_fields = []
        assert isinstance(definitions, Iterable) or definitions is None
        assert isinstance(example_sentence_source_paths, Iterable) or example_sentence_source_paths is None
        if definitions:
            for definition in definitions:
                if definition not in self.available_definition_fields:
                    invalid_fields.append(definition)

        if example_sentence_source_paths:
            for example_sentence_source_path in example_sentence_source_paths:
                available_example_sentence_sources = self.available_example_sentence_sources(example_sentence_source_path)
                if available_example_sentence_sources is None:
                    invalid_fields.append(example_sentence_source_path)

        if invalid_fields:
            raise RuntimeError(
                f"Some of the specified source paths are invalid: {invalid_fields}\n\n"
                f"Valid definition field names (collection.available_definition_fields):\n"
                f"{self.available_definition_fields}\n\n"
                f"Find valid paths with (collection.available_example_sentence_sources(<path>)):\n"
                f"{list(available_example_sentence_sources.keys())}"
            )
        self.flashcard_fields['definitions'] = list(definitions) if definitions is not None else []
        self.flashcard_fields['example_sentence_source_paths'] = example_sentence_source_paths if example_sentence_source_paths is not None else []

    @property
    def all_words(self):
        return set().union(self.cards, self.known_words)

    @property
    def sorted_learning_words(self):
        return [word for word, card in sorted(self.cards.items(), key=lambda kv: kv[1].frequency, reverse=True)]

    @property
    def words_with_content(self):
        return [card.word for card in self.cards.values() if card.json_path is not None and Path(card.json_path).is_file()]

    def collect(self,
                paths: Union[Union[str, Path], Iterable[Union[str, Path]]] = None,
                *,
                source_path: str = None,
                string: str = None,
                lemma_counts: Dict[str, int] = None) -> Deck:
        """
        Collect words from specified source.

        Parameters
        ----------
        path: Path to a file or directory with textfiles to be added to the collection
            Uses stanza lemma parsing from reader.py to parse source files into wordcount dictionary

        kwargs (only consiered if path is not provided):
            source_path: Path of source in db to fetch lemmas from (see help(Collection.available_example_sentence_sources()), does not require stanza)
            string: String to be parsed directly without reading a file
            lemma_counts: Dict of words and lemma_counts, directly adopted as Deck object

        """
        if not (isinstance(paths, list) or isinstance(paths, set)):
            if isinstance(paths, str) or isinstance(paths, Path):
                paths = [paths]
            elif not paths == None:
                raise RuntimeError(f'Unknown type passed as path: {paths}')
        deck = Deck(self.learning_lang, self.native_lang,
                    learning_collection_words = set(self.cards.keys()),
                    known_collection_words = self.known_words,
                    example_sentence_source_paths = self.flashcard_fields['example_sentence_source_paths'])
        if paths:
            for path in paths:
                deck.add(path=path)
        elif string:
            deck.add(string=string)
        elif lemma_counts:
            deck.add(lemma_counts=lemma_counts)
        elif source_path:
            source = self.available_example_sentence_sources(source_path)
            lemma_counts = source.metadata.get('lemma_counts')
            if not lemma_counts:
                raise RuntimeError(f'No lemma counts received for "{source_path}", please check server.')
            deck.source_words.update(lemma_counts)
        return deck

    def add_deck(self,
            deck: Deck,
            deck_name: str):
        """
        Add new deck from new words in Deck to current collection.
        Changes made to the new words and known words in the Deck object are adopted into the collection.

        Parameters
        ----------
        words: Words from Deck
        deck_name: Name of source you are adding, e.g. movie or series title

        """

        if not deck_name:
            raise RuntimeError('deck_name is a mandatory field')
        if deck_name in self.decks:
            raise RuntimeError('source with same name already in collection')

        for lemma, freq in deck.known_words.items():
            self.known_words.add(lemma)
        self.decks[deck_name] = []
        learning_words = set(self.cards.keys())
        for lemma in deck.new_words:
            deck_example_sentences = []
            for file in deck.added_files:
                example_sentences = [
                    TextSegment(
                        main_index = i - max(0, i-1),
                        text_segments = [seg.text for seg in file.stanza_segments[max(0, i-1): i+2]],
                        word = word,
                        source_name = file.path.stem if file.path else 'Deck Example Sentence'
                    ) for i, word in file.lemma_sentences_mapping.get(lemma, []) if 0 <= i < len(file.stanza_segments)
                ]
                deck_example_sentences.extend(example_sentences)

            if lemma not in learning_words:
                self.decks[deck_name].append(Card(lemma, deck_example_sentences=deck_example_sentences))
            else:
                for present_deck, cards in self.decks.items():
                    if lemma in {card.word for card in cards}:
                        break
                logger.warning(f'Word "{lemma}" already present in deck "{present_deck}", not adding to new deck "{deck_name}".')

    def remove(self,
               deck_name: str):
        """
        Remove source added with specific name
                    file_paths = set()
        """
        # TODO: consider caching mechanism so downloaded info isn't destroyed
        if deck_name not in self.decks: raise RuntimeError(f'Deck "{deck_name}" not present in collection')

        for card in self.decks.pop(deck_name):
            shutil.remove(card.json_path)

    @staticmethod
    def aggregate_source_path(source_path):
        """
        Return server and source_category (root node for a source) for any given source path
        """
        parts = source_path.split("/")
        return parts[0], None if len(parts) == 1 else parts[1]

    # TODO: ignores existing sources and overwrites everything for some reason
    def fetch(self,
            deck_name: str,
            force_update = False,
            add_deck_example_sentences = True):
        """
        Scrape/download data for new cards from specified sources

        Parameters
        ----------
        deck_name: Name of source to download data for
        flashcard_fields (optional): restrict fields to download data for
        force_update: overwrite existing data

        """
        if deck_name not in self.decks:
            raise RuntimeError(f'Invalid deck name: {deck_name}')

        missing_definition_fields = {}
        for card in self.decks[deck_name]:
            for field_name in {field for field in self.flashcard_fields['definitions'] if not field in card.definition_fields or force_update}:
                missing_definition_fields.setdefault(field_name, []).append(card.word)
        if missing_definition_fields:
            total_defs = sum(len(v) for v in missing_definition_fields.values())
            logger.info(f"- Definitions: {len(missing_definition_fields)} fields, {total_defs} words to fill")
        else:
            logger.info("- Definitions: up to date")

        missing_deck_sentences_by_word = {}
        if add_deck_example_sentences:
            for card in self.decks[deck_name]:
                if card.deck_example_sentences and not 'deck_example_sentences' in card._example_sentences_fields:
                    missing_deck_sentences_by_word[card.word] = card.deck_example_sentences
            if missing_deck_sentences_by_word:
                logger.info(f"- Deck sentences: {len(missing_deck_sentences_by_word)} words to add")
            else:
                logger.info("- Deck sentences: up to date")
        else:
            logger.info("- Deck sentences: skipped by flag")

        missing_example_sentence_fields = {}
        for source_path in self.flashcard_fields['example_sentence_source_paths']:
            server_name, source_category = self.aggregate_source_path(source_path)
            missing_example_sentence_fields.setdefault(server_name, {})
            if source_category not in missing_example_sentence_fields[server_name]:
                missing_example_sentence_fields[server_name][source_category] = []
                for card in self.decks[deck_name]:
                    if not f'{server_name}/{source_category}' in card.example_sentences_fields or force_update:
                        missing_example_sentence_fields[server_name][source_category].append(card.word)
        if missing_example_sentence_fields:
            total_examples = sum(len(ws) for cats in missing_example_sentence_fields.values() for ws in cats.values())
            logger.info(f"- Example sentences: servers={len(missing_example_sentence_fields)}, total words={total_examples}")
        else:
            logger.info("- Example sentences: up to date")

        if missing_example_sentence_fields:
            logger.info("Triggering example sentence generation...")
            task_ids_by_server = self.scraper.trigger_example_sentences_generation(missing_example_sentence_fields,
                                                                self.flashcard_fields['example_sentence_source_paths'])

        if missing_deck_sentences_by_word:
            logger.info("Generating Deck sentence fields...")
            deck_sentence_fields_by_word = self.scraper.generate_deck_sentence_fields(missing_deck_sentences_by_word)
            for lemma, field in deck_sentence_fields_by_word.items():
                self.cards[lemma]._example_sentences_fields['deck_example_sentences'] = field
            self.save()
            logger.info("Saved Deck sentence fields.")

        if missing_definition_fields:
            logger.info("Downloading definitions...")
            downloaded_definition_fields = self.scraper.download_definitions(missing_definition_fields)
            for field, results in downloaded_definition_fields.items():
                for lemma in missing_definition_fields[field]:
                    if lemma in results.keys():
                        self.cards[lemma]._definition_fields[field] = results[lemma]
                    else:
                        self.cards[lemma]._definition_fields[field] = CardSection('empty', 'black', '')
            self.save()
            logger.info("Saved definitions")

        if missing_example_sentence_fields:
            logger.info("Downloading example sentences...")
            downloaded_example_sentence_fields = self.scraper.download_sentences(task_ids_by_server, cache_translations = True)
            for server_name, lemmas_by_source_category in missing_example_sentence_fields.items():
                for source_category, lemmas in lemmas_by_source_category.items():
                    for lemma in lemmas:
                        result = downloaded_example_sentence_fields.get(server_name, {}).get(source_category, {}).get(lemma)
                        if result:
                            self.cards[lemma]._example_sentences_fields[f'{server_name}/{source_category}'] = result
                        else:
                            self.cards[lemma]._example_sentences_fields[f'{server_name}/{source_category}'] = CardSection('empty', 'black', '')
            self.save()
            logger.info("Saved example sentences")

    def sync_with_anki(self, deck_name: str, overwrite = False):
        """
        Sync collection data with anki database.
        Uses AnkiConnect to interface with anki app functionalities via localhost.
        Requires anki to be installed, open and logged in during execution. (see README.md)
        https://apps.ankiweb.net/

        TODO: Currently slow at adding new cards, improve (windows issue)
        """

        # TODO: add "full_overwrite" kwarg, which bulk-removes and readds card instead of updating one by one (faster)
        incomplete_cards = {}
        for card in self.decks[deck_name]:
            for definition in self.flashcard_fields['definitions']:
                if definition not in card.definition_fields:
                    incomplete_cards.setdefault(card.word, []).append(definition)
            for source_path in self.flashcard_fields['example_sentence_source_paths']:
                if source_path not in card.example_sentences_fields:
                    incomplete_cards.setdefault(card.word, []).append(source_path)
        if incomplete_cards:
            raise RuntimeError(f'Some cards are missing data for fields defined in Collection.flashcard_fields, run collection.fetch(<deck_name>) first: {incomplete_cards}')
        if self.decks[deck_name]:
            print('Syncing anki for words', [card.word for card in self.decks[deck_name]])
            self.anki_manager.sync_deck(deck_name, self.decks[deck_name], overwrite=overwrite)
            self.anki_manager.sync()

    def save(self, name = None):
        """
        Write all collection data to `DATA_DIR`.

        """
        if not name:
            name = self.name
        if not self.flashcard_data_dir.exists():
            self.flashcard_data_dir.mkdir(parents=True, exist_ok=True)
        save_json(self.metadata_path, self.as_dict())
        for word, card in self.cards.items():
            if card.was_modified:
                if not card.json_path:
                    card.json_path = self.flashcard_data_dir / f'{word}.json'
                save_json(card.json_path, card.as_dict())

    def estimate_known_words_for_domain(self, source_path: str, level: int = None):
        """
        Scrape/download data for new cards from specified sources

        Parameters
        ----------
        source_path: '/' separated Path to a file or directory with textfiles
        level: integer value between 1 and 100

        """
        source = self.available_example_sentence_sources(source_path)
        lemma_counts = source.metadata.get('lemma_counts')
        if not lemma_counts:
            raise RuntimeError(f'No lemma counts received for "{source_path}", please check server.')
        # Very vague formula to conservatively estimate the known words for a given domain (TODO: improve):
        proficiency_level = level*0.01*len(lemma_counts) if level else estimate_proficiency(lemma_counts)
        items = Counter(lemma_counts).most_common()[:int(proficiency_level)]
        return self.collect(lemma_counts = dict(items), is_known = True)

    @classmethod
    def load_from_dict(cls, name, dict: Union[str, Union[str, Iterable, Dict[str, Dict[str, Union[int, dict]]]]]) -> 'Collection':
        """
        Initialize collection from dictionary.

        Mostly used for testing.

        """
        dict_ = deepcopy(dict)
        instance = cls(name, **dict_)
        instance.decks = {deck_name: [Card(word, json_path = PROJECT_ROOT / name / 'flashcard_fields' / f'{word}.json') for word in words] for deck_name, words in dict_.pop('decks', {}).items()}
        instance.known_words = set(dict_.pop('known_words', []))

        return instance

    # TODO: Implement safety mechanism to not accidentally lose massive amounts of data
    # TODO: Implement function to recreate database based on current anki database state in case of loss
    def delete_collection(self, name):
        """
        Delete collection from database
        Currently ignores whether collection is present in database or not

        """
        if input('Are you sure? type "yes"') == 'yes':
            shutil.rmtree(self.data_dir / name)

    def as_dict(self):
        return {
            'learning_lang': self.learning_lang,
            'native_lang': self.native_lang,
            'flashcard_fields': self.flashcard_fields,
            'decks': {deck_name: [card.word for card in cards] for deck_name, cards in self.decks.items()},
            'known_words': list(self.known_words),
        }

    def __repr__(self):
        return str(self)

    def __str__(self):
        return '\n'.join([
        f'Collection name: {self.name}',
        f'Learning Language: {self.learning_lang}',
        f'Native Language (for explanations): {self.native_lang}',
        f"Added Decks: { '; '.join(f'{deck_name}: {len(cards)} cards' for deck_name, cards in self.decks.items()) }",
        f'Used Flashcard Fields: {self.flashcard_fields}',
        f'n cards: {len(self.cards)}',
        f'n known_words: {len(self.known_words)}',
        f'n words_with_content: {len(self.words_with_content)}'])
