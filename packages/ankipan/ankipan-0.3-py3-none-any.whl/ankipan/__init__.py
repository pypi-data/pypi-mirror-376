from pathlib import Path
from dataclasses import dataclass
import yaml

PROJECT_ROOT = Path(__file__).parent.parent
ANKIPAN_ROOT = PROJECT_ROOT / 'ankipan'
HTML_TEMPLATE_DIR = ANKIPAN_ROOT / 'html_templates'
ANKI_COLLECTIONS_DIR = PROJECT_ROOT / 'anki_collections'

DATA_DIR = PROJECT_ROOT / '.data'
DATA_DIR.mkdir(parents=True, exist_ok=True)

PROMPT_HISTORY_DIR = PROJECT_ROOT / ".prompt_history"
PROMPT_HISTORY_DIR.mkdir(parents=True, exist_ok=True)

USER_DATA_FILE = PROJECT_ROOT / '.user_data.yaml'
if USER_DATA_FILE.exists():
    with open(USER_DATA_FILE, 'r') as f:
        USER_DATA = yaml.safe_load(f)
else:
    USER_DATA = {}

@dataclass
class TextSegment:
    main_index: int
    text_segments: list
    word: str
    start_s: int = None
    end_s: int = None
    translation: str = None
    source_name: str = None

    @property
    def main_segment(self): return self.text_segments[self.main_index]

    def __str__(self): return self.main_segment

from .util import *
from .config import Config
from .client import Client
from .translator import Translator
from .anki_manager import AnkiManager
from .reader import Reader, File
from .scraper import Scraper, CardSection
from .card import Card
from .deck import Deck
from .collection import Collection
