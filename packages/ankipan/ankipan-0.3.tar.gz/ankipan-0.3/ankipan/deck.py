from collections import OrderedDict, Counter
from pathlib import Path
from wcwidth import wcswidth
from typing import Iterable, Dict, Union, List
import logging
import shutil

from ankipan import Reader, Scraper, File, Client
from ankipan.util import pad_clip

logger = logging.getLogger(__name__)

class Deck:
    def __init__(self,
                 learning_lang: str,
                 native_lang: str,
                 source_words: Dict[str, int] = None,
                 learning_collection_words: Iterable = None,
                 known_collection_words: Iterable = None,
                 example_sentence_source_paths: List[str] = None):
        self.learning_lang = learning_lang
        self.reader = Reader(learning_lang)
        self.scraper = Scraper(learning_lang, native_lang)
        self.source_words = Counter(source_words) if source_words else Counter()

        self.added_files = []
        self.learning_collection_words = learning_collection_words if learning_collection_words else set()
        self.known_collection_words = known_collection_words if known_collection_words else set()
        self.skip_words = set()

        self.example_sentence_source_paths = example_sentence_source_paths if example_sentence_source_paths else set()
        self._lemma_percentiles_by_domain = None

        self.word_lemma_mapping = {}

    @property
    def new_words(self):
        return Counter({word: count for word, count in self.source_words.items() if word not in self.learning_collection_words and word not in self.known_collection_words and word not in self.skip_words})

    @property
    def learning_words(self):
        """Get words that are already being learned in collection"""
        return Counter({word: count for word, count in self.source_words.items() if word in self.learning_collection_words})

    @property
    def known_words(self):
        """Get words that are already specified as known word in collection"""
        return Counter({word: count for word, count in self.source_words.items() if word in self.known_collection_words})

    @property
    def lemma_percentiles_by_domain(self):
        if self._lemma_percentiles_by_domain is None:
            if self.example_sentence_source_paths:
                self._lemma_percentiles_by_domain = OrderedDict(Client.get_lemma_percentiles(self.learning_lang, self.example_sentence_source_paths, list(self.source_words.keys())))
            else:
                logger.warning(f'No example sentence source paths specified for deck, not comparing occurrence frequencies with other sources')
                self._lemma_percentiles_by_domain = OrderedDict()

            common = [word for word, count in self.source_words.most_common()]
            for word in self.source_words:
                self._lemma_percentiles_by_domain.setdefault('Current Deck', {})[word] = common.index(word) / len(self.source_words) if self.source_words[word] != 1 else None
            self._lemma_percentiles_by_domain.move_to_end('Current Deck', last=False)

            for word in self.source_words:
                percentile_values = [lemma_counts[word] for domain, lemma_counts in self._lemma_percentiles_by_domain.items() if lemma_counts.get(word) is not None]
                self._lemma_percentiles_by_domain.setdefault('Average', {})[word] = None if not percentile_values else (sum(percentile_values) / len(percentile_values))
            self._lemma_percentiles_by_domain.move_to_end('Average', last=False)

        return self._lemma_percentiles_by_domain

    def sorted_words(self, domain_name='Average'):
        items = self.lemma_percentiles_by_domain[domain_name].items()
        return [lemma for lemma, v in sorted(items, key=lambda kv: (kv[1] is None, kv[1]))]

    def select_new_words(self, n_words=None):
        """
        Displays words in an ipysheet 'spreadsheet'. Each row has 'Skip', 'Known',
        'Word', and dynamically generated percentile columns.
        """
        import ipysheet
        from ipysheet import sheet, column, cell
        from ipywidgets import Button, VBox, Layout, HTML
        from IPython.display import display
        from IPython import get_ipython
        from functools import partial
        import ipywidgets as widgets

        if not get_ipython():
            raise NotImplementedError("Spreadsheet UI only available in Jupyter.")
        if n_words is not None and n_words > 300:
            logger.warning('Rendering many words will take a long time, please wait a few minutes...')
        if len(self.source_words) > 300:
            logger.warning(f'Only rendering 300 out of {len(self.source_words)}, if you are fine with long loading times then please specify the number of words with `n_words`.')
            n_words = 300
        words_to_show = self.sorted_words() if n_words is None else self.sorted_words()[:n_words]
        print("words_to_show",words_to_show)

        n_rows = len(words_to_show)
        s = sheet(
            rows=n_rows,
            columns=3 + len(self.lemma_percentiles_by_domain),
            column_width=100,
            stretch_headers="none"
        )
        s.column_headers = ["Skip", "Known", "Word"] + list(self.lemma_percentiles_by_domain.keys())

        col_sel   = column(0, [False]*n_rows, type="checkbox", label="Skip",  sheet=s)
        col_known = column(1, [False]*n_rows, type="checkbox", label="Known", sheet=s)
        col_word  = column(2, words_to_show,  type="text",     label="Word",  sheet=s)

        def bg(val: float | None) -> str:
            if val is None:
                return "#ffffff"
            if val < 0.10:
                return "#c6f7c6"
            if val < 0.25:
                return "#fff7b5"
            return "#f7c6c6"
        for col_idx, domain in enumerate(self.lemma_percentiles_by_domain.keys(), start=3):
            for row_idx, word in enumerate(words_to_show):
                val = self.lemma_percentiles_by_domain.get(domain, {}).get(word)
                txt = "" if val is None else f"{val:.4f}"
                ipysheet.cell(
                    row=row_idx,
                    column=col_idx,
                    value=txt,
                    sheet=s,
                    type="text",
                    background_color=bg(val)
                )

        btn  = widgets.Button(description="Set unknown words")
        out  = widgets.Output()
        def on_click(b):
            with out:
                out.clear_output()
                err_mask   = col_sel.value
                known_mask = col_known.value
                words      = col_word.value
                skip_words  = [w for w, m in zip(words, err_mask)   if m]
                known      = [w for w, m in zip(words, known_mask) if m]
                unknown = set(self.source_words) - set(skip_words) - set(known)
                self.set_new_words(unknown, skip_words)
                print("✅ Skip Words:", skip_words[:10], "...")
                print("✅ Known    :", known[:10], "...")
                print("➡️ New  :", sorted(unknown)[:10], "...")
        btn.on_click(on_click)
        display(HTML("""
        <style>
        /* allow wrapping inside header labels */
        .handsontable th .colHeader {
        white-space: normal !important;
        word-break: break-word;
        overflow-wrap: anywhere;
        line-height: 1.2;
        display: inline-block;   /* make height expand reliably */
        width: 100%;
        }

        /* let header THs auto-size in every overlay clone */
        .handsontable .ht_master thead th,
        .handsontable .ht_clone_top thead th,
        .handsontable .ht_clone_top_left thead th {
        height: auto !important;
        vertical-align: middle;  /* optional, looks nicer */
        }

        /* explicitly include the top-left corner header cell */
        .handsontable thead th.ht__corner,
        .handsontable .ht_clone_top_left thead th.ht__corner {
        height: auto !important;
        }

        /* (optional) avoid clipping if Handsontable tries to hide overflow in overlays */
        .handsontable .ht_clone_top .wtHolder,
        .handsontable .ht_clone_top_left .wtHolder {
        overflow: visible !important;
        }
        </style>
        """))
        display(widgets.VBox([s, btn, out]))

    def set_new_words(self, new_words: Iterable, skip_words=None, ignore_unknown=False):
        if not skip_words:
            skip_words = []
        for word in self.source_words.keys():
            if word in new_words:
                self.known_collection_words.discard(word)
                self.learning_collection_words.discard(word)
            elif word in skip_words:
                self.skip_words.add(word)
            elif word not in self.known_collection_words and word not in self.learning_collection_words:
                self.known_collection_words.add(word)
        for word in new_words:
            if word not in self.source_words.keys():
                logger.warning(f'Word {word} not in source words, ' +
                      f'{"ignoring" if ignore_unknown else "adding with occurrence 1"}')
                if not ignore_unknown:
                    self.source_words[word] = 1

    def __repr__(self):
        return str(self)

    def __str__(self):
        if not any([self.new_words, self.learning_words, self.known_words]):
            return "No words in collection"

        titles = [
            f"New Words ({len(self.new_words)})",
            f"Learning Words ({len(self.learning_words)})",
            f"Known Words ({len(self.known_words)})",
        ]

        deck_name = "Current Deck"
        deck_percentiles = self.lemma_percentiles_by_domain.get(deck_name, {})

        def order(word):
            v = deck_percentiles.get(word)
            return (v is None, v)

        columns = {
            titles[0]: sorted(self.new_words.keys(),      key=order),
            titles[1]: sorted(self.learning_words.keys(), key=order),
            titles[2]: sorted(self.known_words.keys(),    key=order),
        }

        samples = ["100.00%", "  0.00%", "Only occurs once"]
        word_width = max(14, max((wcswidth(w) for w in self.source_words.keys()), default=12) + 2)
        pct_width  = max(10, wcswidth(deck_name) + 2, max(wcswidth(s) for s in samples) + 2)

        inner_gap = " "
        block_width = word_width + wcswidth(inner_gap) + pct_width
        outer_gap = " | "

        header = inner_gap.join([pad_clip("word", word_width), pad_clip(deck_name, pct_width)])
        title_line = outer_gap.join(pad_clip(t, block_width) for t in titles)

        lines = [
            title_line,
            "_" * wcswidth(title_line),
            outer_gap.join(pad_clip(header, block_width) for _ in titles),
            "",
        ]

        max_rows = max(len(words) for words in columns.values()) if columns else 0

        for i in range(max_rows):
            row_blocks = []
            for t in titles:
                words = columns[t]
                if i < len(words):
                    w = words[i]
                    v = deck_percentiles.get(w)
                    txt = "Only occurs once" if v is None else ("100.00%" if v == 1.0 else f"{v:.2%}")
                    block = inner_gap.join([pad_clip(w, word_width), pad_clip(txt, pct_width)])
                else:
                    block = ""
                row_blocks.append(pad_clip(block, block_width))
            lines.append(outer_gap.join(row_blocks))

        return "\n".join(lines)


    def add(self,
            path: Union[str, Path] = None,
            *,
            string: str = None,
            lemma_counts: Union[Dict[str, int], Counter] = None):
        """
        Add words from file(s) to word collection

        Parameters
        ----------
        path: path to file(s)
        string (optional): parse string instead of file, only valid if no file is specified

        """
        if path and string:
            raise RuntimeError('Please only supply either a path or a string.')
        elif lemma_counts is not None:
            if not (isinstance(lemma_counts, dict) or isinstance(words, Counter)):
                raise RuntimeError(f'Deck requires Dict- or Counter like datastructure to update, received {type(lemma_counts)}:\n  {lemma_counts}')
        if string is not None:
            files = [File(self.learning_lang, string,)]
        else:
            file_paths = self.reader.collect_file_paths(path)
            files = self.reader.open_files(file_paths)
        self.reader.process_files(files, save_sentence_mapping=True)
        for file in files:
            self.source_words.update(Counter(file.lemma_counts))
            self.word_lemma_mapping.update(file.processed_words)
            self.added_files.append(file)
        self._lemma_percentiles_by_domain = None

    def remove_words(self, words: Union[str, Iterable]):
        """
        Remove words from word collection

        Parameters
        ----------
        words: words to remove

        """
        if isinstance(words, str):
            words = [words]
        elif not (isinstance(words, list) or isinstance(words, set)):
            raise RuntimeError('Only string or list allowed in collection.remove command')
        for word in words:
            if word not in self.source_words: raise RuntimeError(f'Word "{word}" is not part of this wordcollection, abort.')
        [self.source_words.pop(word) for word in words]
        self._lemma_percentiles_by_domain = None

    def remove_range(self, lower: int, upper: int):
        self.remove([word for word, count in self.source_words.items() if count >= lower and count < upper])
