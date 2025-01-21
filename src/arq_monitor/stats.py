"""
Compute stats
"""

import itertools
import numpy as np
from operator import itemgetter

def compute_stats(data: dict):
    """
    Compute additional stats on reformatted data
    """
    results = data.get("results", {})
    queues = data.get("queues", {})
    results_stats = dict()
    for queue_name, results_data in results.items():
        for function, func_jobs in itertools.groupby(results_data, lambda job: job.get("function")):
            stats = dict()
            func_jobs = tuple(func_jobs)
            start_time = (job.get("start_time") for job in func_jobs)
            time_exec = (job.get("time_exec") for job in func_jobs)
            start_time, time_exec = [list(x) for x in zip(*sorted(zip(start_time, time_exec), key=itemgetter(0)))]
            stats[function] = {
                "ts_start_time": start_time,
                "ts_time_exec": time_exec,
            }
            # TODO percentiles
        results_stats[queue_name] = stats
    queue_stats = dict()
    # TODO queue stats time_inqueue
    data = {"results_stats": results_stats, "queues_stats": queue_stats, }
    return data

# TODO add to stats
# # cdf
# x = range(1, 101)
# y = np.percentile(numbers, x)

# # histogram
# hist_vals, hist_edges = np.histogram(numbers, bins=10)
# hist_vals = hist_vals.tolist()
# hist_vals.append(hist_vals[-1])
# hist_edges = hist_edges.tolist()
# print(hist_edges)
# print(hist_vals)
