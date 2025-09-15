from datetime import datetime
import re
import logging

from typing import List, Tuple

import ankipan

logger = logging.getLogger(__name__)

language_mapping = {
    'de': 'german',
    'en': 'english',
    'jp': 'japanese',
    'fr': 'french'
}

class Translator:
    def __init__(self):
        try:
            import google.generativeai as genai
            genai.configure(api_key=ankipan.Config.get_gemini_api_key())
            self.model_deterministic = genai.GenerativeModel("gemini-1.5-flash", generation_config={"temperature": 0.1})
        except ImportError:
            pass

    def translate_text_segments(self,
                                native_lang: str,
                                learning_lang: str,
                                example_sentences: List[ankipan.TextSegment],
                                max_batch_size: int = 20,
                                max_retries: int = 3) -> List:
        """
        Batches `text_segments_data` into chunks of at most `max_batch_size`,
        translates each batch with retry logic, and concatenates results in order.
        """
        if not example_sentences:
            return []
        res = {}
        for start in range(0, len(example_sentences), max_batch_size):
            batch = example_sentences[start:start + max_batch_size]
            attempts = 0

            while True:
                if attempts == max_retries:
                    raise RuntimeError(
                        f"Failed to prompt translations for batch "
                        f"{start // max_batch_size} (items {start}-{min(start+max_batch_size, len(example_sentences))-1}) "
                        f"after {max_retries} attempts."
                    )
                prompt_response = self.prompt_translation(native_lang, learning_lang, batch)
                parsed_translation = self.parse_prompt_response(prompt_response)
                if len(parsed_translation) != len(batch):
                    logger.error(
                        "Translation prompt parsing failed for batch %d: "
                        "len(parsed_translation) != len(batch) (%d != %d)",
                        start // max_batch_size, len(parsed_translation), len(batch)
                    )
                    attempts += 1
                    continue
                for i, example_sentence in enumerate(batch):
                    res[example_sentence.main_segment] = parsed_translation[i]
                break
        return res

    def parse_prompt_response(self, prompt_response):
        _BULLET_RE = re.compile(r"""
            ^\s*[-•]\s*
            (?P<translation>.*?)
            (?:\s*\((?P<comment>[^()]*)\)\s*)?$
        """, re.MULTILINE | re.VERBOSE)
        items = []
        for m in _BULLET_RE.finditer(prompt_response):
            items.append(
                f'{m.group("translation").strip()}<br>'
                f'{("(" + (m.group("comment") or "").strip() + ")") if m.group("comment") else ""}'
            )
        return items

    def prompt_translation(self, native_lang, learning_lang, example_sentences: List[ankipan.TextSegment]):
        formatted_sentences = []
        words = set()
        for example_sentence in example_sentences:
            words.add(example_sentence.word)
            formatted_sentences.append('- ' + ' '.join([text_segment if i != example_sentence.main_index else f'[{text_segment}]'
                                        for i, text_segment in enumerate(example_sentence.text_segments)]))

        formatted_sentences_str = '\n'.join(formatted_sentences)
        prompt = f'''We have a set of text snippets, which we would like to translate from {language_mapping[learning_lang]} to {language_mapping[native_lang]}.
While we provide some context, we are only interested in the main part of the snippet, wrapped in [] braces.
This means that we only want the translation of the text in the [] braces, and nothing else, the surrounding text is just used for context but should not be included in the translation.
If there is any nuance to the translation from {language_mapping[learning_lang]} to {language_mapping[native_lang]}, we also want to add an optional comment in () braces. Imagine you are a language teacher and want to explain to a {language_mapping[native_lang]} student who doesn't know {language_mapping[learning_lang]} the meaning and nuance of the {language_mapping[learning_lang]} word{'s' if len(words)>1 else ''} [{', '.join(words)}] through these example sentences, with a focus on the words in question in particular.
If the translation to {language_mapping[native_lang]} is very straightforward and there is no linguistic nuance, we can just leave the comment out entirely.

The text segments are provided as a list. The answer must follow exactly the following formatting:

- <translation> (<optional_comments>)
- <translation> (<optional_comments>)
- <translation> (<optional_comments>)
...

What would that look like for the following text segments?

{formatted_sentences_str}

    '''
        response = self.model_deterministic.generate_content(prompt)
        timestamp_day = datetime.now().strftime('%Y-%m-%d')
        timestamp_time = datetime.now().strftime('%H-%M-%S')
        with open(ankipan.PROMPT_HISTORY_DIR / f'translation_{timestamp_day}_{timestamp_time}.txt', 'w', encoding='utf-8') as f:
            f.write(prompt + '\n_____________________________________________________________________________________________________________\n\n' + response.text)
        return response.text

