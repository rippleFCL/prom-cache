import threading
import requests
import time
from shatter_api.core.api import ApiDescriptor, Mapping
from shatter_api.core.request import RequestCtx, RequestQueryParams
from shatter_api.core.responses import Response, BaseHeaders, JsonResponse, NotFoundData
from typing import Literal
from shatter_api.core.backend import WsgiDispatcher

class BackgroundJob:
    def __init__(self, endpoint, params=None):
        self.endpoint = endpoint
        self.params = params or {}
        self.thread = threading.Thread(target=self.run)
        self._response: requests.Response | None = None
        self.time_since_last_grab = time.time()
        self.stopped = False

    @property
    def response(self):
        self.time_since_last_grab = time.time()
        return self._response

    def run(self):
        while 1:
            try:
                self._response = requests.get(self.endpoint, params=self.params)
                self._response.raise_for_status()
            except requests.RequestException as e:
                print(f"Error during request: {e}")
                self._response = None

            if time.time() - self.time_since_last_grab > 600:
                print("response not served in 10 minutes, stopping thread")
                self.stopped = True
                break
            time.sleep(1)

    def start(self):
        self.thread.start()

class BackgroundJobManager:
    def __init__(self):
        self.jobs = {}

    @staticmethod
    def _job_id(endpoint, params: dict[str, str] | None = None):
        params_full = ''.join([k + v for k, v in (params or {}).items()])
        return f"{endpoint}, {params_full}"

    def get_response(self, endpoint, params: dict[str, str] | None = None):
        job_id_str = self._job_id(endpoint, params)
        if job_id_str not in self.jobs or self.jobs[job_id_str].stopped:
            job = BackgroundJob(endpoint, params)
            self.jobs[job_id_str] = job
            job.start()
        else:
            job = self.jobs[job_id_str]
        return job.response

job_manager = BackgroundJobManager()


class MetricsQueryParams(RequestQueryParams):
    endpoint: str

class MetricsResponseHeaders(BaseHeaders):
    content_type: str = "text/plain; version=0.0.4; charset=utf-8"

class PromCache(ApiDescriptor):
    mapping = Mapping()

    @mapping.route("/metrics")
    def metrics(
        self, ctx: RequestCtx, query_params: MetricsQueryParams
    ) -> Response[str, int, MetricsResponseHeaders] | JsonResponse[NotFoundData, Literal[404]]:
        """
        Fetches metrics from the specified endpoint.
        """
        endpoint = query_params.endpoint
        params = ctx.query_params.copy()
        params.pop("endpoint", None)  # Remove 'endpoint' from query params if it
        response = job_manager.get_response(endpoint, params)

        if response is None:
            return JsonResponse(NotFoundData(), 404)
        return Response(
            body=response.text,
            code=response.status_code,
            header=MetricsResponseHeaders(
                content_type=response.headers.get("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            ),
        )

handler = PromCache()
app = WsgiDispatcher(handler)
