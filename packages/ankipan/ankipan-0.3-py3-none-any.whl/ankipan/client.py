from __future__ import annotations
import logging
from typing import Dict, Iterable, Optional, Tuple, List
from dataclasses import asdict
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from ankipan import Config, TextSegment

logger = logging.getLogger(__name__)


class Client:
    DEFAULT_TIMEOUT: float = 600
    DEFAULT_MAX_WORKERS: Optional[int] = None

    @classmethod
    def _servers(cls) -> Dict[str, str]:
        servers = Config.list_servers()
        if not servers:
            raise RuntimeError("No servers configured. Use ankipan.Config.add_server(...).")
        return servers

    @staticmethod
    def _post(base_url: str, path: str, payload: dict, *, timeout: float) -> requests.Response:
        url = f"{base_url.rstrip('/')}{path}"
        return requests.post(url, json=payload, timeout=timeout)

    @staticmethod
    def _workers(count: int, max_workers: Optional[int]) -> int:
        return max_workers or min(8, max(1, count))

    @staticmethod
    def _split_server_and_path(full_path: str) -> tuple[str, Optional[str]]:
        s = (full_path or "").strip("/")
        if not s:
            raise ValueError("Malformed source path, expected '<server>/<category>/...'.")
        parts = s.split("/", 1)
        server = parts[0]
        remainder = parts[1] if len(parts) > 1 else None
        return server, remainder

    @classmethod
    def available_example_sentence_sources(cls, learning_lang: str):
        servers = cls._servers()
        payload = {"lang": learning_lang}
        res = {}
        for server, address in servers.items():
            resp = cls._post(address, "/available_sources", payload, timeout=cls.DEFAULT_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            res[server] = data
        return res

    @classmethod
    def source_list(
        cls,
        learning_lang: str,
        source_path: str,
        *,
        timeout: Optional[float] = None,
    ):
        """
        Parameters
        ----------
        learning_lang : Name of language the user wants to learn.
        source_path : Native language of the user for translations and explanations.

        Returns
        -------
        metadata: Dict[str, Any]
            metadata of source node
        lemma_counts: Dict[str, int]
            (aggregated) lemma counts of source node
            picking most frequent 10.000 if there are more than that
        children: List[str]
            List of child names

        """
        servers = cls._servers()
        server, remainder = cls._split_server_and_path(source_path)

        if server not in servers:
            known = ", ".join(sorted(servers)) or "(none)"
            raise KeyError(f"Unknown server '{server}'. Known: {known}")

        eff_timeout = timeout if timeout is not None else cls.DEFAULT_TIMEOUT
        payload = {"lang": learning_lang, "source_path": remainder}
        resp = cls._post(servers[server], "/source_list", payload, timeout=eff_timeout)

        if resp.status_code == 404:
            raise RuntimeError(f"Path not found on {server}: {source_path}")
        resp.raise_for_status()

        data = resp.json()
        metadata, lemma_counts, children = data
        return metadata, lemma_counts, children

    # TODO parallelize server accesses
    @classmethod
    def get_lemma_percentiles(
        cls,
        learning_lang: str,
        source_paths: str,
        lemmas: List[str],
        *,
        timeout: Optional[float] = None):
        eff_timeout = timeout if timeout is not None else cls.DEFAULT_TIMEOUT
        servers = cls._servers()

        percentiles_by_source = {}
        for source_path in source_paths:
            server, remainder = cls._split_server_and_path(source_path)
            if server not in servers:
                known = ", ".join(sorted(servers)) or "(none)"
                raise KeyError(f"Unknown server '{server}' in path '{source_path}'. Known: {known}")
            resp = cls._post(servers[server], "/get_lemma_percentiles", {
                    "learning_lang": learning_lang,
                    "lemmas": lemmas,
                    "source_path": remainder},
                timeout=eff_timeout)
            if resp.status_code != 200:
                logger.warning(f'Could not fetch lemma count for {source_path}')
            else:
                percentiles_by_source[source_path] = resp.json()
        return percentiles_by_source

    @staticmethod
    def _get(base_url: str, path: str, *, timeout: float) -> requests.Response:
        url = f"{base_url.rstrip('/')}{path}"
        return requests.get(url, timeout=timeout)

    @classmethod
    def _pick_server(cls, server: str | None) -> Tuple[str, str]:
        servers = cls._servers()
        if server is None:
            if len(servers) != 1:
                raise RuntimeError('More than one server in servers.yaml config, please specify')
            server = next(iter(servers.keys()))
        if server not in servers:
            known = ", ".join(sorted(servers)) or "(none)"
            raise KeyError(f"Unknown server '{server}'. Known: {known}")
        return server, servers[server]

    @classmethod
    def trigger_sentences(
        cls,
        server: str,
        learning_lang: str,
        native_lang: str,
        source_category: str,
        lemmas: Dict[str, List[str]],
        relative_source_paths: Dict[str, List[str]],
        timeout: Optional[float] = None) -> List[str]:
        """
        POST /sentences to a single server.
        Returns a list of task_ids.
        """
        _, base = cls._pick_server(server)
        eff_timeout = timeout if timeout is not None else cls.DEFAULT_TIMEOUT
        resp = cls._post(base, "/sentences", {
                        "source_category": source_category,
                        "lemmas": lemmas,
                        "relative_source_paths": relative_source_paths,
                        "learning_lang": learning_lang,
                        "native_lang": native_lang,
                }, timeout=eff_timeout)
        resp.raise_for_status()
        payload = resp.json()
        return payload["task_id"]

    @classmethod
    def poll_sentences(
        cls,
        server: str,
        task_id: str,
        timeout: Optional[float] = None,
    ) -> Dict[str, dict]:
        """
        Polls /sentences/status/<task_id> until all complete.
        Returns: {task_id: result_dict} (only for SUCCESS). Raises on FAILURE.
        """
        _, base = cls._pick_server(server)
        eff_timeout = timeout if timeout is not None else cls.DEFAULT_TIMEOUT

        resp = cls._get(base, f"/sentences/status/{task_id}", timeout=eff_timeout)
        resp.raise_for_status()
        return resp.json()

    @classmethod
    def cache_translations(
        cls,
        server: str,
        learning_lang: str,
        native_lang: Optional[str],
        translations_by_text_segments: list,
        *,
        timeout: Optional[float] = None) -> None:
        _, base = cls._pick_server(server)
        eff_timeout = timeout if timeout is not None else cls.DEFAULT_TIMEOUT
        resp = cls._post(
            base,
            "/cache_translations",
            {
                "learning_lang": learning_lang,
                "native_lang": native_lang,
                "translations_by_text_segments": translations_by_text_segments,
            },
            timeout=eff_timeout,
        )
        if resp.status_code != 200:
            logger.debug(f'Translation caching failed with status code {resp.status_code}: {resp.text}')

    @classmethod
    def get_translations(
        cls,
        server: str,
        learning_lang: str,
        native_lang: str,
        example_sentences: List[TextSegment],
        *,
        timeout: Optional[float] = None,
    ) -> list:
        """
        Calls the server-side translation endpoint (will enforce server's quota).
        Raises for 404/429 automatically via raise_for_status().
        """
        _, base = cls._pick_server(server)
        eff_timeout = timeout if timeout is not None else cls.DEFAULT_TIMEOUT
        resp = cls._post(
            base,
            "/get_translations",
            {
                "learning_lang": learning_lang,
                "native_lang": native_lang,
                "example_sentences": [asdict(example_sentence) for example_sentence in example_sentences],
            },
            timeout=eff_timeout,
        )
        if resp.status_code in (404, 429):
            raise requests.HTTPError(f"{resp.status_code}: {resp.text}", response=resp)
        resp.raise_for_status()
        translations_by_text_segments = resp.json()
        return translations_by_text_segments
