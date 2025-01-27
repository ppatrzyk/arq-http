"""
Compute stats
"""

from datetime import datetime
import itertools
import numpy as np
from operator import itemgetter

def _get_stats(jobs: tuple, x_name: str, y_name: str):
    """
    get time series, cdf, and histogram data
    """
    stats = None
    if len(jobs) >= 2:
        stats = dict()
        x = (job.get(x_name) for job in jobs)
        if x_name == "start_time":
            x = (datetime.fromisoformat(date).timestamp() for date in x)
        y = (job.get(y_name) for job in jobs)
        x, y = [list(x) for x in zip(*sorted(zip(x, y), key=itemgetter(0)))]
        hist_vals, hist_edges = np.histogram(y, bins=10)
        hist_vals = hist_vals.tolist()
        hist_vals.append(hist_vals[-1])
        hist_edges = hist_edges.tolist()
        stats = {
            "y_name": y_name,
            "ts_x": x,
            "ts_y": y,
            "cdf_x": list(range(1, 101)),
            "cdf_y": np.percentile(y, range(1, 101)).tolist(),
            "hist_edges": hist_edges,
            "hist_vals": hist_vals,
        }
    return stats

def compute_stats(data: dict, queue_name: str):
    """
    Compute additional stats on reformatted data
    """
    results = data.get("results", {}).get(queue_name, [])
    data = None
    if len(results) >= 2:
        results_stats = dict()
        queues_stats = dict()
        queues_stats = _get_stats(results, "start_time", "time_inqueue")
        stats = dict()
        for function, func_jobs in itertools.groupby(results, lambda job: job.get("function")):
            func_jobs = tuple(func_jobs)
            stats[function] = _get_stats(func_jobs, "start_time", "time_exec")
        results_stats = stats
        data = {"results_stats": results_stats, "queues_stats": queues_stats, }
    return data
