# Disclaimer: The current scraping methods are only implemented for sources where scraping is not explicitly prohibited.
# The downloaded data is used strictly for educational purposes, and is only stored locally for each individual user who is creating their own flashcards.
# If you are the owner of any of those sources and would like your scraping code removed, please message me and I will do so right away. (daniel.mentock@gmail.com)

import requests
from bs4 import BeautifulSoup
import json
from collections import OrderedDict
from jinja2 import Environment, FileSystemLoader, select_autoescape
import html
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm.notebook import tqdm
import time
import random
import re
import pykakasi
import logging

from typing import List, Dict, Union, Iterable, Tuple, get_args

import ankipan
from ankipan import HTML_TEMPLATE_DIR, Translator, Client, TextSegment

logger = logging.getLogger(__name__)

ContentNode = Union['HeaderAndContent','Collapsible', 'DictEntries', 'RawHtml']
EnumNode = Union['Enumeration', 'BulletEnumeration', 'BracketedList', 'ConcatenatedSections', 'SpanEnumeration']
ScalarNode = Union['Sentence','Placeholder', 'YoutubeEmbed', 'Wikitionary']
AnyNode = Union[EnumNode, ContentNode, ScalarNode, str]

env = Environment(
    loader=FileSystemLoader(HTML_TEMPLATE_DIR),
    autoescape=select_autoescape(['html']),
)
env.filters['render'] = lambda value: str(value)

# color codes: https://htmlcolorcodes.com/color-names/
class CardSection:
    def __init__(self,
                 display_name: str,
                 color: str,
                 content: AnyNode,
                 url: str = None,
                 is_open = False):
        self.display_name = display_name
        self.color = color
        self.content = content
        self.url = url
        self.is_open = is_open

    def as_dict(self):
        def generate_dict(field_element):
            class_name = field_element.__class__.__name__
            if items:= field_element.items() if isinstance(field_element, dict) else \
                       field_element.__dict__.items() if hasattr(field_element, '__dict__') else None:
                result = OrderedDict()
                for attr, value in items:
                    result[attr] = generate_dict(value)
            elif isinstance(field_element, list) or isinstance(field_element, set):
                result = [generate_dict(item) for item in field_element]
            else:
                result = field_element
            return (class_name, result)
        return generate_dict(self)

    @staticmethod
    def from_dict(data, is_type_description_node = True):
        if is_type_description_node:
            if data[0] in [CardSection.__name__] + \
                          [ref.__forward_arg__ for ref in get_args(EnumNode)] + \
                          [ref.__forward_arg__ for ref in get_args(ContentNode)]+ \
                          [ref.__forward_arg__ for ref in get_args(ScalarNode)]:
                ClassRef = globals()[data[0]]
                return ClassRef(**CardSection.from_dict(data[1], is_type_description_node = False))
            else:
                return CardSection.from_dict(data[1], is_type_description_node = False)
        elif isinstance(data, dict):
            return OrderedDict({key: CardSection.from_dict(val) for key, val in data.items()})
        elif isinstance(data, list):
            return [CardSection.from_dict(item) for item in data]
        else:
            return data

    def __str__(self):
        if str(self.content):
            template = env.get_template('flashcard_field.html')
            return template.render(flashcard_field=self)
        else:
            return ''

    def __bool__(self):
        return bool(self.content)

class HeaderAndContent:
    def __init__(self, header: str,
                 content: AnyNode,
                 header_level: int = None,
                 header_color: str = 'white'):
        self.header = header
        self.content = content
        self.header_level = header_level if header_level else 4
        self.header_color = header_color

    def __str__(self):
        template = env.get_template('header_and_content.html')
        return template.render(header_and_content=self)

    def __bool__(self):
        return bool(self.content)

class Collapsible(HeaderAndContent):
    def __init__(self, header: str,
                 content: AnyNode,
                 header_level: int = None,
                 is_open: bool = False,
                 header_color: str = 'white',
                 summary_size: int = None,
                 light: bool = False):
        super().__init__(header, content, header_level, header_color)
        self.is_open = is_open
        self.summary_size = summary_size
        self.light = light

    def __str__(self):
        template = env.get_template('collapsible.html')
        return template.render(collapsible=self)

    def __bool__(self):
        return bool(self.content)

class DictEntries:
    def __init__(self,
                 definitions: Dict[str, AnyNode]):
        self.definitions = definitions

    def __str__(self):
        template = env.get_template('dict_entries.html')
        return template.render(dict_entries=self)

    def __bool__(self):
        return bool(self.definitions)

class Enumeration:
    def __init__(self, entries: Iterable[AnyNode]):
        self.entries = entries

    def __str__(self):
        return '\n'.join([f'{str(item)}' for item in self.entries if item])

    def __bool__(self):
        return bool(self.entries)

class SpanEnumeration(Enumeration):
    def __str__(self):
        return '\n'.join([f'<span style="padding: 0; margin: 0;"> {str(item)}</span><br>' for item in self.entries if item])

class BracketedList(Enumeration):
    def __str__(self):
        if self.entries:
            return '(' + ', '.join([f'{str(item)}' for item in self.entries if item]) + ')'
        else:
            return ''

class ConcatenatedSections(Enumeration):
    def __str__(self):
        return ' '.join([f'{str(item)}' for item in self.entries if item])

class CommaSeparatedSections(Enumeration):
    def __str__(self):
        return '; '.join([f'{str(item)}' for item in self.entries if item])

class BulletEnumeration(Enumeration):
    def __str__(self):
        template = env.get_template('bullet_enumeration.html')
        return template.render(bullet_enumeration=self)

class RawHtml():
    def __init__(self, html):
        self.html = html

    def __str__(self):
        return f'<div style="text-align: center !important;">\n{self.html}\n</div>'

    def __bool__(self):
        return True if self.html else False

class Sentence():
    def __init__(self, sentence, word, youtube_hash = None):
        self.sentence = sentence
        self.word = word

    def __str__(self):
        return re.sub(
            rf'(\s*){re.escape(self.word.strip())}(\s*)',
            lambda m: f'{m.group(1)}&#8239;<div style="color:red !important; display:inline;">{html.escape(self.word.strip())}</div>&#8239;{m.group(2)}',
            html.escape(str(self.sentence)))

    def __bool__(self):
        return True if self.sentence and self.word else False

class YoutubeEmbed():
    def __init__(self, youtube_hash, start_s, end_s):
        self.youtube_hash = youtube_hash
        self.start_s = start_s
        self.end_s = end_s

    def __str__(self):
        template = env.get_template('youtube_embed.html')
        return template.render(youtube_embed=self)

    def __bool__(self):
        return True if self.youtube_hash else False

class Wikitionary():
    def __init__(self, content):
        self.content = content

    def __str__(self):
        template = env.get_template('wikitionary.html')
        return template.render(wikitionary=self)

    def __bool__(self):
        return True if self.content else False

class Scraper:
    def __init__(self, learning_lang, native_lang):
        self.learning_lang = learning_lang
        self.native_lang = native_lang
        self.timeout = 25
        self.kks = pykakasi.kakasi()
        self.translator = Translator()

    def generate_deck_sentence_fields(self, example_sentences_by_words: Dict[str, List[TextSegment]], cache_server: str = 'ankipan_default'):
        deck_sentence_fields_by_word = {}
        for lemma, example_sentences in example_sentences_by_words.items():
            translations_by_text_segments = self.get_text_segments_translation(example_sentences, cache_server)
            source_sentences = self.parse_sentences_into_collapsible_list(
                example_sentences,
                translations_by_text_segments,
                open_entries = False,
                header_color = 'White',
                light_sentence = False
            )
            deck_sentence_fields_by_word[lemma] = CardSection('Deck Example Sentences', 'Red', Enumeration(source_sentences), is_open = False)
        return deck_sentence_fields_by_word

    def download_definitions(self,
                             missing_definitions: Dict[str, List[str]],
                             save_func = None,
                             save_freq = 5):
        """
        Called by Collection.fetch to download definition fields for this word

        missing_definitions: dict, definition_name -> list of lemmas
        scraper: Scraper module passed from collection
            Only one instance is required instead of one for each card
            Especially since it only contains static methods

        """
        logger.debug(f'download_definitions: {missing_definitions.keys()}')
        tasks = []
        for definition_name, words in missing_definitions.items():
            try:
                func = getattr(self, f'fetch_{definition_name}')
            except AttributeError as e:
                raise RuntimeError(f'Section name "{definition_name}" not specified in scraper.py module.')

            for word in words:
                tasks.append((definition_name, word, func))
        random.shuffle(tasks)
        word_to_future = {}
        downloaded_definitions = {}
        with ThreadPoolExecutor(max_workers=5) as executor:
            for field_name, word, func in tasks:
                future = executor.submit(func, word)
                word_to_future[(field_name, word)] = future

            for i, ((field_name, word), future) in enumerate(word_to_future.items()):
                for attempt in range(5):
                    try:
                        result = future.result()
                        continue
                    except Exception as e:
                        logger.error(f'Fail to collect field {field_name} for word "{word}": {e}. Waiting before retry...')
                        time.sleep(150)
                if field_name not in downloaded_definitions:
                    downloaded_definitions[field_name] = {}
                downloaded_definitions[field_name][word] = result
                if not i+1%save_freq and save_func:
                    save_func()
        return downloaded_definitions

    def download_sentences(self, task_ids_by_server: Dict[str, List[str]], cache_translations: bool = True):
        pending: Dict[str, List[str]] = {srv: list(ids or []) for srv, ids in (task_ids_by_server or {}).items()}

        i = 0
        downloaded_example_sentences: Dict[str, Dict[str, Dict[str, List[str]]]] = {}

        def any_pending(d: Dict[str, List[str]]) -> bool:
            return any(d.get(srv) for srv in d)

        while any_pending(pending):
            for server, ids in list(pending.items()):
                for idx in range(len(ids) - 1, -1, -1):
                    task_id = ids[idx]
                    response = Client.poll_sentences(server, task_id)
                    if response.get('status') == 'SUCCESS':
                        ids.pop(idx)
                        examples_results = response.get('result') or {}
                        downloaded_example_sentences.setdefault(server,{}).update(
                            self.collect_finished_sentence_tasks(server, examples_results, cache_translations=cache_translations)
                        )
                    elif response.get('status') == 'FAILURE':
                        raise RuntimeError(f"Task {task_id} on {server} failed: {response.get('result')}")

                if not ids:
                    pending[server] = []

            i += 1
            logger.info(f"Waiting for db sentences query to finish, iteration {i}")
            time.sleep(5)
        return downloaded_example_sentences


    def trigger_example_sentences_generation(self,
                                             missing_example_sentence_fields: Dict[str, Dict[str, List[str]]],
                                             example_sentence_source_paths: List[str],
                                             chunk_size = 5) -> List[int]:
        task_ids_by_server = {}
        for server_name, lemmas_by_source_category in missing_example_sentence_fields.items():
            for source_category, lemmas in lemmas_by_source_category.items():
                relative_source_paths = ['/'.join(source_path.split('/')[2:]) for source_path in example_sentence_source_paths
                                         if source_path.startswith(f'{server_name}/{source_category}')]
                lemma_chunks = [lemmas[i:i + chunk_size] for i in range(0, len(lemmas), chunk_size)]
                for lemma_chunk in lemma_chunks:
                    task_id = Client.trigger_sentences(server_name, self.learning_lang, self.native_lang, source_category, lemma_chunk, relative_source_paths)
                    task_ids_by_server.setdefault(server_name, []).append(task_id)
        return task_ids_by_server

    def collect_finished_sentence_tasks(self, server, db_result, cache_translations = True) -> Dict[str, Dict[str, List[str]]]:
        text_segments_to_translate = []
        for source_category, sentences_by_lemmas in db_result.items():
            for lemma, known_and_unknown_sentences_by_source in sentences_by_lemmas.items():
                for sentence_type in ['entries_from_known_sources', 'entries_from_unknown_sources']:
                    entries_and_sentences_by_source = known_and_unknown_sentences_by_source.get(sentence_type, {})
                    for source_root_name, sentences_by_source_entry in entries_and_sentences_by_source.items():
                        for file_name, file_sentences in sentences_by_source_entry.items():
                            for source_entry_sentence in file_sentences:
                                if source_entry_sentence.get('translation')==None:
                                    text_segments_to_translate.append(TextSegment(source_entry_sentence['main_index'],
                                                                                  source_entry_sentence['text_segments'],
                                                                                  source_entry_sentence['word']))

        translations_by_text_segments = self.get_text_segments_translation(text_segments_to_translate, server)
        sentences_by_source_category = {}
        for source_category, sentences_by_lemmas in db_result.items():
            words_and_sentences = {}
            for lemma, known_and_unknown_sentences_by_source in sentences_by_lemmas.items():
                parsed_sentences = []
                if known_sources := known_and_unknown_sentences_by_source.get('entries_from_known_sources'):
                    sentences_from_known_sources = []
                    for source_root_name, sentences_by_source_entry in known_sources.items():
                        source_sentences = []
                        for file_name, file_sentences in sentences_by_source_entry.items():
                            source_sentences.append(self.parse_sentences_into_collapsible_list(
                                [TextSegment(**example_sentence_dict) for example_sentence_dict in file_sentences],
                                translations_by_text_segments,
                                youtube_hash = file_name.split('_')[0] if source_category == 'youtube' else None))
                        sentences_from_known_sources.append(Collapsible(source_root_name, Enumeration(source_sentences), header_color='31EC81'))
                    logger.debug(f"known_sources: {known_sources}, {len(sentences_from_known_sources)}")
                    parsed_sentences.extend(sentences_from_known_sources)
                if unknown_sources := known_and_unknown_sentences_by_source.get('entries_from_unknown_sources'):
                    sentences_from_unknown_sources = []
                    for source_root_name, sentences_by_source_entry in unknown_sources.items():
                        source_sentences = []
                        for file_name, file_sentences in sentences_by_source_entry.items():
                            source_sentences.append(self.parse_sentences_into_collapsible_list(
                                [TextSegment(**example_sentence_dict) for example_sentence_dict in file_sentences],
                                translations_by_text_segments,
                                youtube_hash = file_name.split('_')[0] if source_category == 'youtube' else None))
                        sentences_from_unknown_sources.append(Collapsible(source_root_name, Enumeration(source_sentences)))
                    logger.debug(f"unknown_sources: {unknown_sources}, {len(sentences_from_unknown_sources)}")
                    parsed_sentences.extend(sentences_from_unknown_sources)
                words_and_sentences[lemma] = CardSection(source_category.title(), 'DarkOrange', Enumeration(parsed_sentences), is_open = True)
            sentences_by_source_category[source_category] = words_and_sentences
        return sentences_by_source_category

    def parse_sentences_into_collapsible_list(self,
                                              example_sentences: List[TextSegment],
                                              translations_by_text_segments: Dict[str, str],
                                              title: str = None,
                                              youtube_hash: str = None,
                                              open_entries = True,
                                              header_color = 'Silver',
                                              light_sentence = True):
        entry_sentences = []
        for i, example_sentence in enumerate(example_sentences):
            sentence_components = []
            text_segment_field = []
            if youtube_hash:
                try:
                    text_segment_field.append(YoutubeEmbed(youtube_hash, example_sentence.start_s, example_sentence.end_s))
                except:
                    pass

            for i, text_segment in enumerate(example_sentence.text_segments):
                if example_sentence.translation == None:
                    translation = translations_by_text_segments.get(text_segment, '')
                elif i == example_sentence.main_index:
                    translation = example_sentence.translation
                if self.learning_lang=='jp':
                    translation+='<br>'+self.add_furigana(text_segment)
                text_segment_field.append(Collapsible(
                    Sentence(text_segment, example_sentence.word), translation, summary_size='14px', light=light_sentence))

            sentence_components.append(Enumeration(text_segment_field))
            entry_sentences.append(Collapsible(f'{title + " - " if title else example_sentence.source_name + " - " if example_sentence.source_name else ""}<{i+1}>',
                                                Enumeration(sentence_components), header_level=6, is_open=open_entries, header_color=header_color))
        return entry_sentences

    def get_text_segments_translation(self, example_sentences: List[TextSegment], cache_server, cache_translations = True):
        if ankipan.Config.get_gemini_api_key():
            if example_sentences:
                translations_by_text_segments = self.translator.translate_text_segments(self.native_lang, self.learning_lang, example_sentences)
                if cache_translations:
                    Client.cache_translations(cache_server, self.learning_lang, self.native_lang, translations_by_text_segments)
            else:
                translations_by_text_segments = {}
        else:
            res = Client.get_translations(cache_server, self.learning_lang, self.native_lang, example_sentences)
            if res.status_code == 404:
                raise RuntimeError(f'Ankipan DB 404 Error: {res.json()}')
            elif res.status_code == 429:
                raise RuntimeError(f'Ankipan DB 429 Error: {res.json()}')
            translations_by_text_segments = res.json()
        return translations_by_text_segments

    def fetch_jisho(self, word: str) -> Dict[str, Dict[str, str]]:
        url="https://jisho.org/search/{}".format(word)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        vstr=requests.get(url, headers=headers, timeout=self.timeout).content
        soup = BeautifulSoup(vstr,features="html.parser",from_encoding='utf8')
        rows = soup.findAll('div', {"class":"concept_light clearfix"})
        jisho = OrderedDict()
        for row in rows:
            furigana = [span.get_text() for span in row.find_all('span', class_='kanji')]
            text_jp_ = row.findAll('span', {"class":"text"})
            text_jp = str(text_jp_).replace('<span class="text">',"").replace("<span>","").replace("</span>","").replace(" ","").replace("[","").replace("]","").replace("\n","").strip()
            text_target_ = row.findAll('span', {"class":"meaning-meaning"})
            text_target = str(text_target_).replace('<span class="meaning-meaning">',"").replace("<span>","").replace("</span>","").replace("[","").replace("]","").replace("\n","").strip()
            if "<span" in text_target:
                text_target = text_target.split("<span")[0]
            if "\n" in text_target:
                text_target = text_target.split("\n")[0]
            if text_jp not in jisho.keys() and furigana and text_jp and text_target:
                jisho[text_jp] = ConcatenatedSections([text_target, BracketedList(furigana)])
        return CardSection('Jisho.org', 'Violet', DictEntries(jisho), url = url)

    def fetch_tatoeba(self, word: str) -> Dict[str, List[str]]:
        lang_mapping = {
            'jp': 'jpn',
            'en': 'eng',
            'de': 'deu',
            'fr': 'fra'
        }
        def fetch(learning_lang, native_lang):
            max_pages = 3
            tatoeba=OrderedDict()
            url= f"https://tatoeba.org/eng/sentences/search?from={lang_mapping[self.learning_lang]}&query={word}&to={lang_mapping[self.native_lang]}"
            vstr=requests.get(url, timeout=self.timeout).content
            soup = BeautifulSoup(vstr,features="html.parser",from_encoding='utf8')
            paging = soup.find('ul', class_='paging')
            if paging:
                li_tags = paging.find_all('li', {'class': lambda x: x != 'next' and x != 'ellipsis'})
                # Get the text of the last li tag (which will be the last page number)
                last_page = min(int(li_tags[-1].a.get_text()), max_pages)
                # last_page = 2
            else:
                last_page = 1
            for page in range(1, last_page+1):
                if page>1:
                    url= f"https://tatoeba.org/eng/sentences/search?from={lang_mapping[self.learning_lang]}&query={word}&to={lang_mapping[self.native_lang]}&page={page}"
                    vstr=requests.get(url, timeout=self.timeout).content
                    soup = BeautifulSoup(vstr,features="html.parser",from_encoding='utf8')
                rows = soup.findAll('div', {"class":"sentence-and-translations"})
                for row in rows:
                    if row:
                        ng_init = row['ng-init']
                        comma_pos = ng_init.find(',')
                        end_bracket_pos = ng_init.rfind(']')
                        json_str = f'[{ng_init[comma_pos+1:end_bracket_pos].strip()}]]'
                        data = json.loads(json_str)
                        example = data[0]['text']
                        translations = []
                        for translation in data[0]['translations']:
                            if translation:
                                translations.append(translation[0]['text'])
                        tatoeba[example] = Enumeration(translations)
            return tatoeba
        examples = fetch(self.learning_lang, self.native_lang) if self.native_lang!='en' else OrderedDict()
        examples.update(fetch(self.learning_lang, 'en'))


        return CardSection('Tatoeba.org', 'Tomato', DictEntries(examples),
            url = f"https://tatoeba.org/eng/sentences/search?from={lang_mapping[self.learning_lang]}&query={word}&to={lang_mapping[self.native_lang]}")

    def fetch_urban(self, word: str) -> List[str]:
        logger.debug(f'fetch_urban: {word}')

        url = f"http://api.urbandictionary.com/v0/define?term={word}"
        response = requests.get(url)
        dictionary = json.loads(response.text)['list']
        definitions = {}
        for definition in dictionary:
            definitions[definition['word']] = {'thumbs': definition['thumbs_up'], 'definition': definition['definition']}

        return CardSection(
            'Urban Dictionary',
            'Violet',
            DictEntries(
                OrderedDict({
                    word: info["definition"] for word, info in sorted(definitions.items(), key=lambda item: item[1]['thumbs'], reverse=True)
            })),
            url = url)

    def fetch_sprachnudel(self, word: str) -> Dict[str, Union[List[str], str]]:
        logger.debug(f'fetch_sprachnudel: {word}')

        url = f'https://www.sprachnudel.de/woerterbuch/{word}'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        html_content = requests.get(url, headers=headers, timeout=self.timeout).content
        if 'Hast du dich verirrt?' in str(html_content):
            content = ''
        else:
            soup = BeautifulSoup(html_content, 'html.parser', from_encoding='utf8')
            main_meaning = secondary_meaning = examples = ''
            for div in soup.find_all('div'):
                text = div.get_text()
                if 'Hauptbedeutung' in text:
                    main_meaning = text.split('Hauptbedeutung')[1].split('Nebenbedeutung')[0].strip()
                elif 'Bedeutung (Definition)' in text and not main_meaning:
                    main_meaning = text.split('Bedeutung (Definition)')[-1].split('Deine Bedeutung')[0].strip()
                if 'Nebenbedeutung' in text:
                    secondary_meaning = text.split('Nebenbedeutung')[1].split('Assoziative Bedeutungen')[0].strip()
                if 'Beispielsätze' in text:
                    examples = [example.strip() for example in text.split('Beispielsätze')[1].split('Dein Beispielsatz')[0].strip().split('\n') if example.strip()]

            def extract_associative_meanings(soup):
                associative_headings = soup.find_all('h3', text='Assoziative Bedeutungen')
                for heading in associative_headings:
                    next_ul = heading.find_next_sibling('ul')
                    if next_ul:
                        associative_meanings = [li.get_text(strip=True) for li in next_ul.find_all('li')]
                        return associative_meanings
                return []
            content = Enumeration([
                HeaderAndContent('Main Meaning', main_meaning),
                HeaderAndContent('Secondary Meaning', secondary_meaning),
                HeaderAndContent('Examples', BulletEnumeration(examples)),
                HeaderAndContent('Associative Meanings', BulletEnumeration(extract_associative_meanings(soup)))
            ])
        return CardSection('Sprachnudel.de', 'Bisque', content, url = url)

    def fetch_wadoku(self, word):
        url = f'https://www.wadoku.de/search/{word}'
        headers = {'User-Agent': 'Mozilla/5.0'}
        html_content = requests.get(url, headers=headers).content
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.find('table', id='resulttable')
        dict_entries = {}
        if table:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    japanese_parts = cells[1].find_all('span', class_='orth')
                    japanese_word = ''.join(part.get_text(strip=True) for part in japanese_parts)
                    furigana_parts = cells[1].find_all('span', class_='reading')
                    furigana = ''.join(part.get_text(strip=True) for part in furigana_parts)
                    japanese_formatted = f'{japanese_word} ({furigana})' if furigana else japanese_word
                    german_translation = ''
                    german_translation_field = cells[2].find('div', class_='d')
                    if german_translation_field:
                        german_translation = RawHtml(str(german_translation_field))
                    else:
                        german_translation = RawHtml(str(cells[2]))
                    dict_entries[japanese_formatted] = german_translation
        return CardSection('Wadoku.de', 'Lavender', DictEntries(dict_entries), url=url)

    def _fetch_wikitionary(self, lang, word):
        logger.debug(f'fetch_wikitionary: {word}')

        url = f'https://{lang}.m.wiktionary.org/wiki/{word}'
        content = []
        headers = {'User-Agent': 'Mozilla/5.0'}
        html_content = requests.get(url, headers=headers).content
        soup = BeautifulSoup(html_content, 'html.parser')
        if ("Wiktionary does not yet have an entry for" in soup.text and lang == 'en') or \
           ("ウィクショナリーには現在この名前の項目はありません" in soup.text and lang == 'ja') or \
           ("ne possède pas de page dédiée à cette suite de lettres." in soup.text and lang == 'fr') or \
           ("Dieser Eintrag existiert noch nicht!" in soup.text and lang == 'de'):
            content = ''
        else:
            rows = soup.findAll('div', {"id":"mw-content-text"})
            content = Wikitionary(RawHtml('\n'.join([str(row) for row in rows]).replace('href="/wiki', 'href="https://en.wiktionary.org/wiki')))
        return CardSection(f'{lang}.Wikitionary.org', 'Gray', content, url = url)

    def fetch_wikitionary_en(self, word):
        return self._fetch_wikitionary('en', word)

    def fetch_wikitionary_jp(self, word):
        return self._fetch_wikitionary('ja', word)

    def fetch_wikitionary_fr(self, word):
        return self._fetch_wikitionary('fr', word)

    def fetch_wikitionary_de(self, word):
        return self._fetch_wikitionary('de', word)

    def add_furigana(self, sentence):
        result = []
        for word in self.kks.convert(sentence):
            if word['orig'] != word['hira']:
                result.append(f"{word['orig']} ({word['hira']})")
            else:
                result.append(word['orig'])
        return ''.join(result)

    # TODO
    # def _fetch_unsplash(self, english_synonyms, count: int = 10) -> List[str]:
    #     unsplash_image_dir = self.project_dir / 'unsplash'
    #     existing_image_ids = [image.split('.')[0] for image in os.listdir(unsplash_image_dir)]
    #     image_ids = []
    #     if not unsplash_image_dir.exists():
    #         unsplash_image_dir.mkdir(parents=True)
    #     url = "https://api.unsplash.com/search/photos"
    #     #todo: print url of all fetched images/number of opened links etc
    #     for word in english_synonyms:
    #         query = {
    #             "query": word,
    #             "client_id": self.unsplash_access_key,
    #             "per_page": count
    #         }
    #         response = requests.get(url, params=query)
    #         if response.status_code == 200:
    #             results = response.json()['results']
    #             for result in results:
    #                 image_url = result['urls']['regular']
    #                 image_id = f'{word}_{result["id"]}'  # Get the image ID from Unsplash
    #                 if image_id not in existing_image_ids:
    #                     print(f'Downloading image {image_id}')
    #                     image_data = requests.get(image_url).content
    #                     image_path = unsplash_image_dir / f"{image_id}.jpg"
    #                     with open(image_path, 'wb') as file:
    #                         file.write(image_data)
    #                 else:
    #                     print(f'Image {image_id} already dowloaded')
    #                 image_ids.append(image_id)
    #             print(f'Downloaded {len(results)} images for "{word}"')
    #         else:
    #             print(f'Error: {response.status_code} when downloading images to {image_path}')
    #     return image_ids
