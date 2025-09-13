from __future__ import annotations

import dateutil
import pandas as pd
from typing import Any, Dict, List, Optional, Sequence

from ..http import HTTPApi


class MetricsAPI:
    """Client for Core Dashboard metrics.

    Provides convenience methods to fetch metric time series with batching
    for high‑frequency spans and returns tidy pandas DataFrames.
    """

    _METRIC_URL_PATH = "/core-data-provider/v1/metric_dynamics"

    def __init__(self, http: HTTPApi):
        self._http = http

    @staticmethod
    def _split_params_to_batches(
        obj_ids: Sequence[int], time_range: Sequence[str], time_freq: Optional[str]
    ) -> List[Dict[str, Any]]:
        MAX_OBJ_IDS = 100
        obj_ids_groups: List[List[int]] = []
        for i in range(0, len(obj_ids), MAX_OBJ_IDS):
            obj_ids_groups.append(list(obj_ids[i : i + MAX_OBJ_IDS]))

        MAX_TIME_RANGE_DAYS = 31
        date_range_groups: List[Sequence[str]] = []
        t0 = dateutil.parser.parse(time_range[0])
        t1 = dateutil.parser.parse(time_range[1])
        if (
            (time_freq is not None)
            and (time_freq.upper() in ("15MIN", "H"))
            and ((t1 - t0).total_seconds() > MAX_TIME_RANGE_DAYS * 24 * 3600)
        ):
            days = pd.date_range(start=t0, end=t1, freq="D")
            for i in range(0, len(days), MAX_TIME_RANGE_DAYS):
                d0 = str(days[i : i + MAX_TIME_RANGE_DAYS][0].date())
                d1 = str(days[i : i + MAX_TIME_RANGE_DAYS][-1].date())
                date_range_groups.append([d0, d1])
        else:
            date_range_groups.append(time_range)

        groups: List[Dict[str, Any]] = []
        for time_range_g in date_range_groups:
            for obj_ids_g in obj_ids_groups:
                groups.append(
                    {
                        "time_range": time_range_g,
                        "obj_ids": obj_ids_g,
                        "time_freq": time_freq,
                    }
                )

        return groups

    def _get_metric(
        self,
        metric: str,
        obj_ids: Sequence[int],
        time_range: Sequence[str],
        *,
        time_freq: Optional[str] = "D",
        alias: Optional[str] = None,
        metric_level: Optional[str] = None,
        object_aggregation: bool = False,
    ) -> Any:
        body: Dict[str, Any] = {
            "input_parameters": {
                "metric": metric,
                "alias": alias,
                "obj_ids": list(obj_ids),
                "object_aggregation": object_aggregation,
                "time_range": list(time_range),
                "time_freq": time_freq,
            }
        }
        if metric_level is not None:
            assert metric_level in ("frozen", "source", "correction", "clean")
            body["input_parameters"]["metric_level"] = metric_level

        rjson = self._http.request("POST", self._METRIC_URL_PATH, json_body=body)
        return rjson["result"]

    def get_metric(
        self,
        metric: str,
        obj_ids: Sequence[int],
        time_range: Sequence[str],
        *,
        time_freq: Optional[str] = "D",
        alias: Optional[str] = None,
        metric_level: Optional[str] = None,
        object_aggregation: bool = False,
    ) -> pd.DataFrame:
        """Fetch a metric time series for one or more objects.

        Parameters:
        - metric: Metric key supported by the backend (including extended metrics).
        - obj_ids: Data object identifiers (<= 100 per batch).
        - time_range: [date_from, date_to] in YYYY‑MM‑DD format.
        - time_freq: Resolution: "D", "H", or "15MIN".
        - alias: Optional label forwarded to the backend.
        - metric_level: Optional quality level: "frozen" | "source" | "correction" | "clean".
        - object_aggregation: When True, aggregate across objects server‑side.

        Returns: pandas.DataFrame with columns:
        metric, object_id, time, value, object_type, object_marker, object_name
        """
        dfs: List[pd.DataFrame] = []
        for batch in self._split_params_to_batches(obj_ids, time_range, time_freq):
            data_lines = self._get_metric(
                metric,
                batch["obj_ids"],
                batch["time_range"],
                time_freq=time_freq,
                alias=alias,
                metric_level=metric_level,
                object_aggregation=object_aggregation,
            )
            for data_line in data_lines:
                df = pd.DataFrame(data_line["items"])
                if not df.empty:
                    df["value"] = df["value"].astype(float)
                df["object_id"] = data_line["context"]["data_objects"][0]["id"]
                df["object_marker"] = data_line["context"]["data_objects"][0]["marker"]
                df["object_name"] = data_line["context"]["data_objects"][0]["name"]
                df["object_type"] = data_line["context"]["data_objects"][0]["type"]
                dfs.append(df)

        if not dfs:
            return pd.DataFrame(
                columns=[
                    "metric",
                    "object_id",
                    "time",
                    "value",
                    "object_type",
                    "object_marker",
                    "object_name",
                ]
            )

        df = pd.concat(dfs)
        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"])
        df["metric"] = metric
        df = df[[
            "metric",
            "object_id",
            "time",
            "value",
            "object_type",
            "object_marker",
            "object_name",
        ]]
        return df

    def get_metrics_bulk(
        self,
        metrics: Sequence[str],
        obj_ids: Sequence[int],
        time_range: Sequence[str],
        *,
        time_freq: Optional[str] = "D",
        metric_level: Optional[str] = None,
        object_aggregation: bool = False,
    ) -> pd.DataFrame:
        """Fetch multiple metrics and concatenate the results.

        Each row contains a "metric" column identifying the metric name.
        """
        frames = []
        for m in metrics:
            frames.append(
                self.get_metric(
                    metric=m,
                    obj_ids=obj_ids,
                    time_range=time_range,
                    time_freq=time_freq,
                    alias=None,
                    metric_level=metric_level,
                    object_aggregation=object_aggregation,
                )
            )
        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True)

__all__ = ["MetricsAPI"]
