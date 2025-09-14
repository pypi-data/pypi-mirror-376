import logging
from types import MethodType
import httpx

from .exceptions import ActionNotFound, ActionURLMatchError
from .models import Request
from .request import make_async_request, make_request
from .curlify import Curlify

logger = logging.getLogger(__name__)


class BaseResource:
    actions = {}

    def __init__(
        self,
        api_root_url=None,
        resource_name=None,
        params=None,
        headers=None,
        timeout=None,
        append_slash=False,
        json_encode_body=False,
        ssl_verify=None,
        ep_suffix="",
        **kwargs,
    ):
        self.api_root_url = api_root_url
        self.resource_name = resource_name
        self.params = params or {}
        self.headers = headers or {}
        self.timeout = timeout or 3
        self.append_slash = append_slash
        self.json_encode_body = json_encode_body
        self.actions = self.actions or self.default_actions
        self.ssl_verify = True if ssl_verify is None else ssl_verify
        self._ep_suffix = ep_suffix
        self.curl_commands=kwargs.get("curl_commands",[])
        self._log_curl=kwargs.get("log_curl_commands",False)

        self._kwargs = kwargs

        if self.json_encode_body:
            self.headers["content-type"] = "application/json"

    def __del__(self):
        self.client.close()

    @property
    def default_actions(self):
        return {
            "list": {"method": "GET", "url": self.resource_name},
            "get": {"method": "GET", "url": self.resource_name},
            "all": {"method": "GET", "url": self.resource_name},
            "create": {"method": "POST", "url": self.resource_name},
            "post": {"method": "POST", "url": self.resource_name},
            "retrieve": {"method": "GET", "url": self.resource_name + "/{}"},
            "update": {"method": "PUT", "url": self.resource_name + "/{}"},
            "put": {"method": "PUT", "url": self.resource_name + "/{}"},
            "partial_update": {"method": "PATCH", "url": self.resource_name + "/{}"},
            "patch": {"method": "PATCH", "url": self.resource_name + "/{}"},
            "destroy": {"method": "DELETE", "url": self.resource_name + "/{}"},
            "delete": {"method": "DELETE", "url": self.resource_name + "/{}"},
        }

    def __call__(self, instance):
        return getattr(self, instance)

    def __getattr__(self, instance):
        resource_name = "/".join([self.resource_name, instance])
        tmp = self.__class__(
            api_root_url=self.api_root_url,
            resource_name=resource_name,
            params=self.params,
            headers=self.headers,
            timeout=self.timeout,
            append_slash=self.append_slash,
            json_encode_body=self.json_encode_body,
            ssl_verify=self.ssl_verify,
            ep_suffix=self._ep_suffix,
            **self._kwargs,
        )
        self.__setattr__(instance, tmp)
        return getattr(self, instance)

    def get_action(self, action_name):
        try:
            return self.actions[action_name]
        except KeyError:
            raise ActionNotFound('action "{}" not found'.format(action_name))

    def get_action_full_url(self, action_name, *parts):
        action = self.get_action(action_name)
        try:
            url = action["url"].format(*parts)
        except IndexError:
            raise ActionURLMatchError('No url match for "{}"'.format(action_name))

        if self.append_slash and not url.endswith("/"):
            url += "/"
        if not self.api_root_url.endswith("/"):
            self.api_root_url += "/"
        if url.startswith("/"):
            url = url.replace("/", "", 1)
        if self._ep_suffix:
            url += self._ep_suffix

        return self.api_root_url + url

    def get_action_method(self, action_name):
        action = self.get_action(action_name)
        return action["method"]


class Resource(BaseResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = httpx.Client(verify=self.ssl_verify)
        for action_name in self.actions.keys():
            self.add_action(action_name)

    def add_action(self, action_name):
        def action_method(
            self,
            *args,
            body=None,
            params=None,
            headers=None,
            action_name=action_name,
            **kwargs,
        ):
            url = self.get_action_full_url(action_name, *args)
            method = kwargs.get("method",self.get_action_method(action_name))
            only_body = True
            if "only_body" in kwargs:
                only_body = kwargs["only_body"]
                del kwargs["only_body"]
            
          

            if action_name in ["all"]:
                offset = 1 
                limit=kwargs.get("limit",500)
                if params:
                    limit = params.get("limit")

                if body:
                    if "page" in body:
                        limit = body["page"].get("limit",limit)
                        offset = body["page"].get("offset",offset)

                if "limit"in kwargs:
                    del kwargs["limit"]
                
                if "method" in kwargs:
                    del kwargs["method"]
                
                request = Request(
                    url=url,
                    method=method,
                    params=params or {},
                    body=body,
                    headers=headers or {},
                    timeout=self.timeout,
                    ssl_verify=self.ssl_verify,
                    kwargs=kwargs,
                )

                request.params.update(self.params)
                request.headers.update(self.headers)
                logging.debug("enabled autopaging, this implicitly forces only_body")
                
                logging.debug(f"request result limit is {limit}")
                
                result_body=[]
                
                finished=False
            
                while not finished:
                    if method.lower() == "get":
                        request.params["limit"]=limit
                        request.params["offset"]=offset
                    elif method.lower() == "post":
                        if body:
                            body["page"]={
                                "limit": limit,
                                "offset": offset
                            }
                            
                    result=make_request(self.client, request)
                    if self._log_curl:
                        self.curl_commands.append((Curlify(request,verify=request.ssl_verify).to_curl(),result))
                    result_count=len(result.body)
                    if result_count < limit:
                        finished=True
                    offset+=limit
                    result_body+=(result.body)
                return result_body
            else:

                request = Request(
                    url=url,
                    method=method,
                    params=params or {},
                    body=body,
                    headers=headers or {},
                    timeout=self.timeout,
                    ssl_verify=self.ssl_verify,
                    kwargs=kwargs,
                )
                request.params.update(self.params)
                request.headers.update(self.headers)
                result=make_request(self.client, request)

                if self._log_curl:
                    self.curl_commands.append((Curlify(request,verify=request.ssl_verify).to_curl(),result))


            if only_body:
                return result.body
            else:
                return result

        setattr(self, action_name, MethodType(action_method, self))


class AsyncResource(BaseResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = httpx.AsyncClient()
        for action_name in self.actions.keys():
            self.add_action(action_name)

    def add_action(self, action_name):
        async def action_method(
            self,
            *args,
            body=None,
            params=None,
            headers=None,
            action_name=action_name,
            **kwargs,
        ):
            url = self.get_action_full_url(action_name, *args)
            method = self.get_action_method(action_name)
            request = Request(
                url=url,
                method=method,
                params=params or {},
                body=body,
                headers=headers or {},
                timeout=self.timeout,
                ssl_verify=self.ssl_verify,
                kwargs=kwargs,
            )
            request.params.update(self.params)
            request.headers.update(self.headers)
            async with self.client as client:
                return await make_async_request(client, request)

        setattr(self, action_name, MethodType(action_method, self))
