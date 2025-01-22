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

from .config import JINJA_ENV, logger, TEMPLATES
from .stats import compute_stats
from .utils import get_jobs_data

async def get_dashboard(request: Request):
    """
    Get dashboard page
    """
    data = {}
    response = TEMPLATES.TemplateResponse(
        request=request,
        name="dashboard.html.jinja",
        context=data
    )
    return response

async def dashboard_data_gen(inner_send_chan: MemoryObjectSendStream, arq_conn: ArqRedis):
    """
    adapted from https://github.com/sysid/sse-starlette/blob/main/examples/no_async_generators.py#L22
    """
    async with inner_send_chan:
        try: 
            while True:
                # TODO push only if data has changed?
                await anyio.sleep(1.0)
                jobs_data = await get_jobs_data(arq_conn)
                stats_data = compute_stats(jobs_data)
                queuestats_template = JINJA_ENV.get_template("components/queuestats.html.jinja")
                resultsstats_template = JINJA_ENV.get_template("components/resultsstats.html.jinja")
                table_template = JINJA_ENV.get_template("components/table.html.jinja")
                data = {
                    "queues-data": table_template.render(data=jobs_data.get("queues").get('arq:myqueue')),
                    "queues-stats": queuestats_template.render(data=stats_data.get("queues_stats").get('arq:myqueue')),
                    "jobs-data": table_template.render(data=jobs_data.get("results").get('arq:myqueue')),
                    # "jobs-stats": resultsstats_template.render(data=stats_data.get("results_stats").get('arq:myqueue')),
                }
                for event_name, event_data in data.items():
                    event = {
                        "event": event_name,
                        "data": event_data,
                    }
                    await inner_send_chan.send(event)
        except anyio.get_cancelled_exc_class() as e:
            with anyio.move_on_after(1, shield=True):
                close_msg = {"closing": True, }
                await inner_send_chan.send(close_msg)
                raise e

async def get_dashboard_data(request: Request):
    """
    Get dashboard data
    """
    send_chan, recv_chan = anyio.create_memory_object_stream(max_buffer_size=10)
    arq_conn = request.state.arq_conn
    response = EventSourceResponse(
        data_sender_callable=partial(dashboard_data_gen, send_chan, arq_conn),
        content=recv_chan,
        send_timeout=5
    )
    return response

dashboard_routes = [
    Route(path='/', endpoint=get_dashboard, methods=["GET", ], name="get_dashboard"),
    Route(path='/dashboard-data', endpoint=get_dashboard_data, methods=["GET", ], name="get_dashboard_data"),
]
