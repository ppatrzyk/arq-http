"""
Dashboard routes
"""

from starlette.requests import Request
from starlette.routing import Route
from sse_starlette.sse import EventSourceResponse

import anyio
from anyio.streams.memory import MemoryObjectSendStream
from arq.connections import ArqRedis
from functools import partial

from .config import DEFAULT_REFRESH, JINJA_ENV, logger, TEMPLATES
from .stats import compute_stats
from .utils import get_jobs_data

async def list_dashboards(request: Request):
    """
    List available dashboards
    """
    jobs_data = await get_jobs_data(request.state.arq_conn)
    queue_names = tuple(jobs_data.get("results", {}).keys())
    response = TEMPLATES.TemplateResponse(
        request=request,
        name="dashboard_listing.html.jinja",
        context={"queue_names": queue_names}
    )
    return response

async def get_dashboard(request: Request):
    """
    Get dashboard page
    """
    queue_name = request.path_params['queue_name']
    refresh = request.query_params.get("refresh")
    jobs_data = await get_jobs_data(request.state.arq_conn)
    results = jobs_data.get("results", {}).get(queue_name, [])
    functions = set(entry.get("function") for entry in results)
    response = TEMPLATES.TemplateResponse(
        request=request,
        name="dashboard.html.jinja",
        context={"functions": functions, "refresh": refresh}
    )
    return response

async def dashboard_data_gen(inner_send_chan: MemoryObjectSendStream, arq_conn: ArqRedis, queue_name: str, refresh: float):
    """
    adapted from https://github.com/sysid/sse-starlette/blob/main/examples/no_async_generators.py#L22
    """
    async with inner_send_chan:
        try: 
            while True:
                jobs_data = await get_jobs_data(arq_conn)
                stats_data = compute_stats(jobs_data, queue_name)
                noplot_template = JINJA_ENV.get_template("components/noplotdata.html.jinja")
                stats_template = JINJA_ENV.get_template("components/stats.html.jinja")
                table_template = JINJA_ENV.get_template("components/table.html.jinja")

                queue = jobs_data.get("queues").get(queue_name, [])
                queues_data = table_template.render(
                    data=queue,
                    details_id="queues-table",
                    table_length=len(queue)
                )
                
                results = jobs_data.get("results").get(queue_name, [])
                results_data = table_template.render(
                    data=results,
                    details_id="jobs-table",
                    table_length=len(results)
                )
                
                if stats_data:
                    queues_ids={"parent_id": "queues-plots", "cdf_id": "queues-cdf-plot", "hist_id": "queues-hist-plot", "ts_id": "queues-ts-plot", }
                    queues_stats = stats_template.render(
                        data=stats_data.get("queues_stats"),
                        ids=queues_ids,
                        title_label="queue"
                    )
                    results_stats_list = list()
                    for function, job_stats_data in stats_data.get("results_stats").items():
                        results_ids={"parent_id": "jobs-plots", "cdf_id": f"{function}-jobs-cdf-plot", "hist_id": f"{function}-jobs-hist-plot", "ts_id": f"{function}-jobs-ts-plot", }
                        entry = stats_template.render(
                            data=job_stats_data,
                            ids=results_ids,
                            title_label=function
                        )
                        results_stats_list.append(entry)
                    if results_stats_list:
                        results_stats = "\n".join(results_stats_list)
                else:
                    queues_stats = noplot_template.render(ids={"parent_id": "queues-plots"})
                    results_stats = noplot_template.render(ids={"parent_id": "jobs-plots"})
                
                data = {
                    "updated-at": jobs_data.get("updated_at", ""),
                    "queues-data": queues_data,
                    "queues-stats": queues_stats,
                    "results-data": results_data,
                    "results-stats": results_stats,
                }
                for event_name, event_data in data.items():
                    event = {
                        "event": event_name,
                        "data": event_data,
                    }
                    await inner_send_chan.send(event)
                await anyio.sleep(refresh)
        except anyio.get_cancelled_exc_class() as e:
            with anyio.move_on_after(1, shield=True):
                close_msg = {"closing": True, }
                await inner_send_chan.send(close_msg)
                raise e

async def get_dashboard_data(request: Request):
    """
    Get dashboard data
    """
    queue_name = request.path_params['queue_name']
    refresh = float(request.query_params.get("refresh", DEFAULT_REFRESH))
    send_chan, recv_chan = anyio.create_memory_object_stream(max_buffer_size=10)
    arq_conn = request.state.arq_conn
    response = EventSourceResponse(
        data_sender_callable=partial(dashboard_data_gen, send_chan, arq_conn, queue_name, refresh),
        content=recv_chan,
        send_timeout=5
    )
    return response

dashboard_routes = [
    Route(path='/', endpoint=list_dashboards, methods=["GET", ], name="list_dashboards"),
    Route(path='/{queue_name:str}', endpoint=get_dashboard, methods=["GET", ], name="get_dashboard"),
    Route(path='/data/{queue_name:str}', endpoint=get_dashboard_data, methods=["GET", ], name="get_dashboard_data"),
]
