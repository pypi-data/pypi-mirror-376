import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Union, Optional, Tuple, Dict, Any

from fairdomseek.cache.cache import Cache
from openapi_client import DataFilesApi

from tenacity import (
    retry, stop_after_attempt, wait_random_exponential,
    retry_if_exception_type, retry_if_result, before_sleep_log, RetryError
)

LOGGER = logging.getLogger(__name__)

class DataFileCache(Cache):

    def __init__(self, actor_service, translator, client, project_name=None):
        super().__init__(client, project_name)
        self.api = DataFilesApi(client)
        self._actor_service = actor_service
        self._translator = translator

        self._df_by_id = {}
        self._df_by_title = {}
        self._external_df = []

    def refresh(self):
        if len(self._external_df) == 0 and len(self._df_by_title) == 0 and len(self._df_by_id) == 0:
            # Fresh cache
            self.__fetch_datafiles(self._project_id)
            return

        all_df_ids = [int(d.id)  for d in self.api.list_data_files().data]
        to_evaluate = []
        for df_id in all_df_ids:
            if df_id in self._df_by_id.keys() or df_id in self._external_df:
                continue
            else:
                to_evaluate.append(df_id)

        if len(to_evaluate) != 0:
            self.__fetch_datafiles(self._project_id, to_evaluate)

    def list_datafile_by_id(self):
        return self._df_by_id

    def list_datafile_by_title(self):
        return self._df_by_title

    def get_datafile(self, datafile: Union[int, str]):
        if isinstance(datafile, int):
            return self._df_by_id.get(datafile, None)
        if isinstance(datafile, str):
            return self._df_by_title.get(datafile, None)
        return None

    def __fetch_datafiles(self, project_id: str, df_ids: Optional[List[int]] = None):
        if not df_ids:
            df_ids_to_cache = [int(d.id) for d in self.api.list_data_files().data]
        else:
            df_ids_to_cache = df_ids

        def _decode_json(resp_obj) -> Dict[str, Any]:
            return json.loads(resp_obj.data.decode("utf-8"))

        def _check_in_project_or_raise(data_node: Dict[str, Any], my_project_id: str) -> bool:
            """Return True if in project, False if not. Raise if JSON is malformed (→ retry)."""
            try:
                rel = data_node["relationships"]["projects"]["data"]
            except Exception as e:
                raise ValueError(f"invalid payload: missing relationships.projects.data ({e})")

            return any(p["id"] == my_project_id for p in rel)

        def _validate_for_domain(data_node: Dict[str, Any]) -> None:
            """Raise if required bits for to_domain are missing."""
            for key in ("id", "attributes", "relationships"):
                if key not in data_node:
                    raise ValueError(f"invalid payload: missing {key}")
            # translator needs projects relationship at least
            if "projects" not in data_node["relationships"]:
                raise ValueError("invalid payload: no projects relationship")

        def read_initial_v1(df_id: int) -> Dict[str, Any]:
            r1 = self.api.read_data_file_without_preload_content(1, df_id)
            if r1 is None:
                raise RuntimeError(f"Data file {df_id}: initial read failed")
            full1 = _decode_json(r1)
            return full1["data"]

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_random_exponential(multiplier=0.25, max=5),
            retry=retry_if_exception_type(Exception),  # retry on KeyError/ValueError/RuntimeError
            reraise=True,
        )
        def read_and_process(df_id: int) -> Tuple[str, Union[str, Dict[str, Any]]]:
            """
            Return ("external", id) if not in project,
                   ("in_project", data_dict) if in project (latest version).
            Raises on malformed data → triggers retry.
            """
            v1_data = read_initial_v1(df_id)

            in_proj = _check_in_project_or_raise(v1_data, project_id)

            if not in_proj:
                return "external", v1_data["id"]

            # We are in project: must fetch latest and validate
            latest_version = v1_data.get("attributes", {}).get("latest_version", 1)
            r2 = self.api.read_data_file_without_preload_content(latest_version, df_id)
            if r2 is None:
                raise RuntimeError(f"Data file {df_id}: latest read failed")
            full2 = _decode_json(r2)
            data2 = full2["data"]

            _validate_for_domain(data2)  # raises if malformed → retry

            return "in_project", data2

        failures = []

        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_id = {executor.submit(read_and_process, sid): sid for sid in df_ids_to_cache}

            for future in as_completed(future_to_id):
                sid = future_to_id[future]
                try:
                    status, payload = future.result()
                except Exception as e:
                    failures.append((sid, repr(e)))
                    continue

                if status == "external":
                    self._external_df.append(payload)  # payload is id str
                else:  # in_project
                    resp = payload
                    try:
                        domain_datafile = self._translator.to_domain(
                            resp,
                            self._actor_service.get_actors_idx_by_id()
                        )
                    except Exception as e:
                        failures.append((sid, f"translate_failed: {e!r}"))
                        continue
                    self._df_by_id[domain_datafile.external_id] = domain_datafile
                    self._df_by_title[domain_datafile.title] = domain_datafile

        return failures

    def set_client(self, client):
        self.api = DataFilesApi(client)
        super().set_client(client)

