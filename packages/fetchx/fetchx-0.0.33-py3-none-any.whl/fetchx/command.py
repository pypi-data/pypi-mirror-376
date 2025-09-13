"""

uuRest
===================================

Implementation of the Command structure used in rest API
by most Unicorn applications

"""

from dataclasses import fields
from .generaltypes import __itemList__, HttpBody
from .common import (RestMethod, uuDict, escape_text, repeat_letter, timestamp, shorten_text, DataType)
from .ioutils import save_json, save_textfile, save_binary

import math
import base64
import httpx
import json
import threading
import asyncio
import concurrent.futures
import contextlib
from pathlib import Path
from io import BufferedReader


class uuRequest:
    """
    class containing all important http, https request properties
    """
    def __init__(self, command, url: str, method: str, body: HttpBody, setup: uuDict):
        self._command: uuCommand = command
        self.url: str = url
        self._body: HttpBody = body
        self.method = method
        self._setup = setup

    def create_copy(self):
        return uuRequest(command=self._command, url=self.url, method=self.method, body=self._body, setup=self._setup)

    @property
    def body(self) -> HttpBody:
        return self._body

    @body.setter
    def body(self, value: HttpBody):
        self._body = value


class uuResponse:
    """
    class containing all important http, https response properties
    """
    def __init__(self, command):
        self._command: uuCommand = command
        self._payload: uuDict | None = None
        self.http_status_code = 0
        self.content_type: str = ""
        self.encoding: str = ""

    @property
    def payload_json(self) -> dict | None:
        return self._payload

    @payload_json.setter
    def payload_json(self, value):
        self._payload = uuDict(value)
        if self._payload is not None:
            self._payload.indentation = 4

def raise_exception(message: str | dict, setup: uuDict) -> httpx.Response:
    if setup["fail_strategy"] == "fail_fast":
        raise Exception(str(message))
    if isinstance(message, str):
        message = {DataType.ERROR.value: message}
    return httpx.Response(504, content=json.dumps(message).encode(), 
                          headers={"Content-Type": "application/json; charset=utf-8"})


def _parse_charset_from_content_type(content_type_value: str) -> str | None:
    content_type_value_lower = content_type_value.lower()
    charset_position = content_type_value_lower.find(f'charset=')
    if charset_position > -1:
        charset_value = content_type_value_lower[charset_position + 8:]
        charset_value += " "
        charset_value = charset_value.split(";")[0]
        charset_value = charset_value.split(",")[0]
        charset_value = charset_value.split(" ")[0]
        return charset_value
    return None


def _get_response_content_type_and_charset(headers: uuDict):
    """
    Get the response content type and charset from headers.
    """
    # get content type
    content_type_value = str(headers.case_insensitive_get_value("content-type"))
    if content_type_value is None:
        content_type_value = "application/octet-stream"
    # get charset
    charset_value = _parse_charset_from_content_type(content_type_value)
    if charset_value is None:
        charset_value = "utf-8"
    # return content type and charset
    return content_type_value, charset_value


def _get_content_type_of_file(filename: Path) -> str:
    result = 'application/octet-stream'
    extension = filename.resolve().suffix.lower().strip()
    if extension == ".zip":
        result = 'application/zip'
    if extension == ".pdf":
        result = 'application/pdf'
    if extension == ".json":
        result = 'application/json'
    if extension == ".xml":
        result = 'application/xml'
    if extension == ".png":
        result = 'image/png'
    if extension == ".jpg" or extension == ".jpeg":
        result = 'image/jpg'
    return result


def get_server_name_and_port(url: str) -> tuple[str, int | None]:
    """
    Parses the server name and port from the given URL.
    """
    parsed_url = httpx.URL(url)
    server_name = parsed_url.host
    port = parsed_url.port
    return server_name, port


_get_client_lock = threading.Lock()
def _get_client(url: str, setup: uuDict) -> httpx.Client:
    """
    Returns httpx.Client instance from setup or creates a new one.
    """
    with _get_client_lock:
        if "url" is None or len(str(url).strip()) < 1:
            raise Exception(f'url must be a valid string')
        if setup is None or not isinstance(setup, uuDict) or "http_version" not in setup.keys():
            raise Exception(f'setup must be a valid dictionary created by fetch_setup() function')
        # get server name and port
        server_name, port = get_server_name_and_port(url)
        client_name = f"{server_name}_{port}" if port else f"{server_name}:default"
        # create httpx_clients dict if not exists and save it to globals
        if "httpx_clients" not in globals():
            globals()["httpx_clients"] = {}
        clients: dict[str, httpx.Client] = globals()["httpx_clients"]
        # get http version
        http_version = setup["http_version"]
        # create httpx.Client instance
        if client_name not in clients.keys():
            client: httpx.Client = httpx.Client(http2=(http_version == "2.0"), verify=False)
        else:
            client: httpx.Client = clients.pop(client_name)
        # store httpx.Client instance as the last one in the dictionary
        globals()["httpx_clients"][client_name] = client
        # limit the number of clients
        if len(clients) > 3:
            # remove the first client from the dictionary
            first_key = next(iter(clients))
            first_client = clients.pop(first_key)
            first_client.close()
        return client


_pool = concurrent.futures.ThreadPoolExecutor()
@contextlib.asynccontextmanager
async def _get_async_client_lock(lock):
    """
    Asynchronous context manager for acquiring a lock.
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(_pool, lock.acquire)
    try:
        yield
    finally:
        lock.release()

def _get_async_client(url: str) -> httpx.AsyncClient:
    """
    Returns httpx.AsyncClient instance from setup or creates a new one.
    """
    server_name, port = get_server_name_and_port(url)
    client_name = f"{server_name}_{port}" if port else f"{server_name}:default"
    clients = globals().get("httpx_async_clients", {})
    if client_name not in clients:
        clients[client_name] = httpx.AsyncClient()
    return clients[client_name]


def _get_files_from_request_body(request_body: HttpBody) -> dict[str, tuple[str, BufferedReader, str]] | None:
    """
    Extracts files from a request body dictionary where values are file URIs.
    Iterates over the request body, identifies values that are file URIs (starting with "file:///"),
    opens the corresponding files in binary mode, determines their content type, and returns a dictionary
    mapping each key to a tuple containing the file name, file object, and content type.
    Args:
        request_body (HttpBody): The request body, expected to be a dictionary with possible file URIs as values.
    Returns:
        dict[str, tuple[str, BufferedReader, str]] | None: 
            A dictionary mapping keys to tuples of (file name, file object, content type), or None if no files are found.
    Raises:
        Exception: If a specified file does not exist.
    """
    if not isinstance(request_body, dict):
        return None
    # collect all files from request body
    files = {}
    # check if request body is a dictionary
    for key, value in request_body.items():
        # check if value is a file
        if isinstance(value, str) and value.lower().startswith("file:///"):
            # remove file:/// prefix and get file path
            value_str = value[len(f'file:///'):]
            # open file
            filename = Path(value_str)
            if not filename.exists():
                raise Exception(f'Cannot load file from "{str(filename)}"')
            # get pure file name
            pure_filename = filename.stem + ''.join(filename.suffixes)
            # open file
            f = open(str(filename.resolve()), 'rb')
            # get file content type
            file_content_type = _get_content_type_of_file(filename)
            # add new field containing the file
            file_item = (pure_filename, f, file_content_type)
            files[key] = file_item
    # delete processed files from request body
    for key in files.keys():
        del request_body[key]
    # if no files were found then return None
    if len(files) == 0:
        files = None
    return files


def _close_files(files: dict[str, tuple[str, BufferedReader, str]] | None) -> None:
    """
    Close all open file handles.
    :param files:
    :return:
    """
    if files is None:
        return
    for _, f, _ in files.values():
        try:
            f.close()
        except Exception as e:
            pass

def _translate_request_body(request_body: HttpBody) -> HttpBody:
    """
    Translates the request body into a format suitable for the HTTP call.
    :param request_body:
    :param setup:
    :return:
    """
    # If the request body is a dictionary, convert it to JSON
    if isinstance(request_body, dict):
        first_key = next(iter(request_body))
        if first_key == DataType.DICT.value or first_key == DataType.LIST.value:
            return request_body[first_key]
        if first_key == DataType.TEXT.value:
            return request_body[first_key]   
        if first_key == DataType.BINARY.value:
            return base64.b64decode(request_body[first_key])
        return request_body
    # If the request body is a string, return it as is
    elif isinstance(request_body, str):
        return request_body
    # If the request body is None, return an empty JSON object
    elif request_body is None:
        return None
    # If the request body is of an unexpected type, raise an exception
    else:
        raise Exception(f"Unexpected request body type: {type(request_body)}")


def _http_call_without_files(url: str, method: str, request_body: HttpBody, setup: uuDict) -> httpx.Response:
    """

    :param url:
    :param method:
    :param request_headers:
    :param request_body:
    :param setup:
    :return:
    """
    # get headers
    headers: uuDict = setup["http_headers"]
    # gets client setup
    client = _get_client(url, setup)
    # translates request body
    request_body = _translate_request_body(request_body)
    # get files from request body
    content = None
    data = None
    json = None
    params = None
    files = _get_files_from_request_body(request_body)
    is_post_put_patch = method in [RestMethod.POST.value, RestMethod.PUT.value, RestMethod.PATCH.value]
    if len(files or {}) > 0 and not is_post_put_patch:
        # if there are files and method is not POST then raise exception
        return raise_exception(f'File uploads are not supported for HTTP method {method}. '
                               f'Only the POST, PUT, PATCH methods support file uploads.', setup)
    # detect content type    
    content_type = headers.case_insensitive_get_value("content-type")
    if content_type is not None:
        content_type = str(content_type).lower()
    if request_body is not None:
        # if method is post and files are present
        if is_post_put_patch and len(files or {}) > 0 and (isinstance(request_body, dict) or isinstance(request_body, list)):
            json = request_body
        # if method is post and no files are present and content_type is application/x-www-form-urlencoded
        elif is_post_put_patch and isinstance(request_body, dict) and content_type == "application/x-www-form-urlencoded":
            data = request_body
        # if method is post and no files are present
        elif is_post_put_patch and isinstance(request_body, dict):
            json = request_body
        # if method is get and request_body is a dict
        elif not is_post_put_patch and isinstance(request_body, dict):
            params = request_body
        # if method is post and request_body is a string and content_type is multipart/form-data
        elif is_post_put_patch and isinstance(request_body, str) and isinstance(content_type, str) and \
            content_type.find("multipart/form-data") > -1 and content_type.find("boundary=") > -1:
            content = request_body.encode()
        # if method is post and request_body is a string and content_type is application/x-www-form-urlencoded
        elif is_post_put_patch and isinstance(request_body, str):
            content = request_body.encode()
        # if method is get and request_body is a string
        elif not is_post_put_patch and isinstance(request_body, str):
            params = request_body
            #content = request_body.encode()
        # if method is post and request_body is a string and content_type is application/binary or application/zip
        elif is_post_put_patch and isinstance(request_body, (bytes, bytearray)):
            content = request_body
            if content_type is None:
                headers.case_insensitive_update({"content-type": "application/binary"}) 
        # if method is get and request_body is a string
        else:
            return raise_exception("Unknown content-type of the request_body. content-type header "
                                   "is not set and Fetch is not able to detect the content-type automatically", setup)

    try:
        # if verbose then print header
        if setup["verbose_level"] >= 2:
            verbose_message = ""
            # get inputs to request
            content_str = str(content) if content is not None else None
            data_str = str(data) if data is not None else None
            json_str = str(json) if json is not None else None
            params_str = str(params) if params is not None else None
            files_str = str([key for key in files.keys()]) if files is not None and len(files or {}) > 0 else None
            if is_post_put_patch:
                arguments = {"url": url, "headers": headers, "content": content_str, "data": data_str, "json": json_str, "files": files_str}
            else:
                arguments = {"url": url, "headers": headers, "params": params_str}
            # create message
            verbose_message += repeat_letter(value=f' HTTP_REQUEST_{method} ', letter='-')
            verbose_message += repeat_letter(value=f' {timestamp()} ', letter='-')
            request_str = uuDict(arguments).to_str()
            if setup["verbose_level"] == 2:
                request_str = str(shorten_text(request_str))
            verbose_message += request_str + "\n"
            print(verbose_message.strip())
        # call the server and return response
        if method == str(RestMethod.POST):
            result = client.post(url, content=content, data=data, json=json, files=files, headers=headers, timeout=setup["timeout"], follow_redirects=True)
        elif method == str(RestMethod.PUT):
            result = client.put(url, content=content, data=data, json=json, files=files, headers=headers, timeout=setup["timeout"], follow_redirects=True)
        elif method == str(RestMethod.PATCH):
            result = client.patch(url, content=content, data=data, json=json, files=files, headers=headers, timeout=setup["timeout"], follow_redirects=True)
        elif method == str(RestMethod.GET):
            result = client.get(url, params=params, headers=headers, timeout=setup["timeout"], follow_redirects=True)
        elif method == str(RestMethod.OPTIONS):
            result = client.options(url, params=params, headers=headers, timeout=setup["timeout"], follow_redirects=True)
        elif method == str(RestMethod.HEAD):
            result = client.head(url, params=params, headers=headers, timeout=setup["timeout"], follow_redirects=True)
        elif method == str(RestMethod.DELETE):
            result = client.delete(url, params=params, headers=headers, timeout=setup["timeout"], follow_redirects=True)
        else:
            return raise_exception({DataType.ERROR.value: f'Unknown method in uuRest._http_call. Currently only GET, POST, '
                                                 f'OPTIONS, HEAD, PUT, DELETE and PATCH methods are supported.'}, setup)
        _close_files(files)
        return result
    except Exception as err:
        _close_files(files)
        return raise_exception({DataType.ERROR.value: f'Error when calling "{str(url)}" with body "{str(request_body)}" using method "{str(method)}". '
                                             f'Exception "{str(type(err))}" was triggered.\n\n{escape_text(str(err))}'}, setup)


def _http_call(url: str, method: str, request_body: HttpBody, setup: uuDict) -> httpx.Response:
    """
    Calls rest api endpoint
    :param url: URL of the REST api endpoint
    :param method: POST or GET
    :param request_headers:
    :param request_body: json body of the request
    :param setup:
    :return:
    """
    # if _request_contains_files(request_body):
    #     r = _http_call_including_files(url=url, method=method, request_body=request_body, setup=setup)
    # else:
    r = _http_call_without_files(url=url, method=method, request_body=request_body, setup=setup)
    # get response content type and charset
    response_content_type, response_charset = _get_response_content_type_and_charset(uuDict(r.headers))

    # if there was an error then return error message
    if r.status_code < 200 or r.status_code >= 300:
        error_message = {
            DataType.ERROR.value: f'Http/Https error code "{str(r.status_code)}" occured. '
                         f'Cannot process data when calling "{str(url)}" with body "{str(request_body)}" using method "{str(method)}".'
        }
        response_payload = uuDict(r.content, str(response_charset))
        response_payload = {} if response_payload is None else response_payload
        response_payload = {**error_message, **response_payload}
        error_message = {
            "http_code": r.status_code,
            "content_type": response_content_type,
            "payload": response_payload
        }
        return raise_exception(error_message, setup)
    return r


def get_data_type(value: uuDict | None) -> str:
    if isinstance(value, uuDict):
        return value.data_type.value
    return DataType.UNKNOWN.value


class uuCommand:
    def __init__(self, url: str, method: str, request_body: HttpBody, setup: uuDict):
        # create a request
        self._initial_request = uuRequest(command=self, url=url, method=method, body=request_body, setup=setup)
        self.requests: list[uuRequest] = []
        self.responses: list[uuResponse] = []
        self._http_code: int = 0
        self._url: str = url
        self._method: str = method
        self._setup = setup
        self._call()

    @property
    def http_status_code(self) -> int:
        if len(self.responses) > 0:
            return self.responses[-1].http_status_code
        return 0

    @property
    def content_type(self) -> str:
        if len(self.responses) > 0:
            return self.responses[-1].content_type
        return ""
    
    @property
    def encoding(self) -> str:
        if len(self.responses) > 0:
            return self.responses[-1].encoding
        return ""

    @property
    def data_type(self) -> str:
        value = self.json
        return get_data_type(value)

    @property
    def json(self) -> uuDict:
        result = None
        if len(self.responses) > 0:
            result = self.responses[-1].payload_json
        if result is None:
            result = {DataType.ERROR.value: "Fatal error. Response was not correctly received."}
        result = uuDict(result)
        result.indentation = 4
        return result

    @property
    def text(self) -> str:
        data_type = self.data_type
        if data_type == DataType.TEXT.value:
            return self.json[DataType.TEXT.value]
        raise Exception(f'Response data type is not {DataType.TEXT.value}, it is {str(data_type)}. '
                        f'Please check property "data_type"')

    @property
    def binary(self) -> bytes:
        data_type = self.data_type
        if data_type == DataType.BINARY.value:
            return base64.b64decode(self.json[DataType.BINARY.value])
        raise Exception(f'Response data type is not {str(DataType.BINARY.value)}, it is {str(data_type)}. '
                        f'Please check property "data_type"')


    def save_json(self, filename: str, encoding="utf-8"):
        save_json(value=self.json, filename=filename, encoding=encoding)

    def save_text(self, filename: str, encoding="utf-8"):
        save_textfile(value=self.text, filename=filename, encoding=encoding)

    def save_binary(self, filename: str):
        save_binary(value=self.binary, filename=filename)

    def _print_verbose_output(self):
        # if verbose then print result
        verbose_message = ""
        if self._setup["verbose_level"] >= 2:
            verbose_message += repeat_letter(value=f' HTTP_RESPONSE_STATUS ', letter='-')
            verbose_message += repeat_letter(value=f' {timestamp()} ', letter='-')
            http_response_status = {
                "http_status_code": self.http_status_code,
                "content_type": self.content_type,
                "data_type": self.data_type
            }
            verbose_message += uuDict(http_response_status).to_str() + "\n"
        if self._setup["verbose_level"] >= 3:
            verbose_message += repeat_letter(value=f' HTTP_RESPONSE_CONTENT ', letter='-')
            verbose_message += repeat_letter(value=f' {timestamp()} ', letter='-')
            verbose_message += str(self) + "\n"
        if self._setup["verbose_level"] in [1, 2]:
            verbose_message += repeat_letter(value=f' HTTP_RESPONSE_CONTENT ', letter='-')
            verbose_message += repeat_letter(value=f' {timestamp()} ', letter='-')
            payload = str(self)
            payload = str(shorten_text(payload)) + "\n"
            verbose_message += payload + "\n"
        if self._setup["verbose_level"] >= 3:
            verbose_message += repeat_letter(f' HINT ', "-")
            verbose_message += f'# Use "fetch_setup()[\'verbose_level\'] = 0" to stop console output\n'
        if self._setup["verbose_level"] >= 1:
            print(verbose_message.strip())

    def _call(self, new_page_info: dict | None = None):
        # get initial request
        request = self._initial_request.create_copy()
        # if this is a paged call then update request and jump to a proper page
        if new_page_info is not None and isinstance(request.body, dict):
            request.body.update({f'pageInfo': new_page_info})
        # append request to requests
        self.requests.append(request)
        # call the server
        result = _http_call(url=request.url, method=request.method, request_body=request.body, setup=self._setup)
        # process the result
        response = uuResponse(self)
        response.http_status_code = result.status_code
        response.content_type = result.headers.get("content-type", "")
        response.encoding = result.encoding if result.encoding is not None else ""
        #response.payload_json = result[f'payload']
        response.payload_json = uuDict(result.content, encoding=result.encoding if result.encoding is not None else "utf-8")
        self.responses.append(response)
        self._print_verbose_output()

    def _page_info_list_items_on_a_page(self, list_name) -> int:
        result = 0
        # take the very last response
        if len(self.responses) > 0:
            payload = self.responses[-1].payload_json
            # check if element exists in the response payload
            if isinstance(payload, dict) and list_name in payload.keys():
                if isinstance(payload[list_name], list):
                    # get count of elements on currently displayed page
                    result = len(payload[list_name])
        return result

    def _page_info(self, list_name) -> dict | None:
        """
        Gets a page infor from the response
        :return:
        """
        result = None
        # take the very last response
        if len(self.responses) > 0:
            payload = self.responses[-1].payload_json
            # test if pageInfo exists
            if isinstance(payload, dict) and "pageInfo" in payload.keys():
                result = payload["pageInfo"]
                # check pageSize
                if "pageSize" not in result.keys():
                    raise Exception(f'PageInfo should contain "pageSize". Received following pageInfo: {result}')
                if not isinstance(result["pageSize"], int):
                    raise Exception(f'pageSize located in the pageInfo element must be integer, but it is type of {str(type(result["pageSize"]))}.')
                if result["pageSize"] < 1:
                    raise Exception(f'pageSize located in the pageInfo element must be must be higher than 0. Received following pageInfo: {result}')
                # if there are more items on a page then pageSize - update pageSize
                list_items_count = self._page_info_list_items_on_a_page(list_name)
                # if there is no item with list_name then return none
                if list_items_count < 1:
                    return None
                if result["pageSize"] < list_items_count:
                    result["pageSize"] = list_items_count
                # setup pageIndex
                if "pageIndex" not in result.keys():
                    result.update({"pageIndex": 0})
                # create total if it does not exist
                if "total" not in result.keys():
                    result.update({"total": min(result["pageSize"]-1, list_items_count)})
        return result

    def _items_on_page(self, page_index, start_index_on_page, stop_index_on_page, list_name):
        # get page info
        page_info = self._page_info(list_name=list_name)
        if page_info is None:
            return None
        # check if already loaded page is the requested one
        current_page_index = page_info["pageIndex"]
        current_page_size = page_info["pageSize"]
        # if it is not, call the api and download requested page
        if page_index != current_page_index:
            new_page_info = {
                f'pageIndex': page_index,
                f'pageSize': current_page_size
            }
            self._call(new_page_info=new_page_info)
            # verify that requested page was downloaded
            page_info = self._page_info(list_name=list_name)
            if page_info is None:
                return None
            # get current page index
            current_page_index = page_info["pageIndex"]
            if current_page_index != page_index:
                raise Exception(f'Cannot download page "{page_index}" in _items_on_page.')
        # check that item list is not empty
        if list_name not in self.json:
            return None
        item_list = self.json[list_name]
        # check that start and stop index is in the boundaries
        stop_index_on_page = min(stop_index_on_page, len(item_list))
        if start_index_on_page < 0 or stop_index_on_page < 0 or start_index_on_page >= len(item_list) or start_index_on_page > stop_index_on_page:
            return None
        # yield items
        for i in range(start_index_on_page, stop_index_on_page):
            yield item_list[i]

    def items(self, start_index: int | None = None, stop_index: int | None = None, list_name: str = __itemList__):
        # get page info
        page_info = self._page_info(list_name=list_name)
        # if there are no items on the page then exit immediately
        if page_info is None:
            return
        # get pageSize and total
        page_size = page_info["pageSize"]
        total = page_info["total"]
        # setup start index and stop index
        start_index = 0 if start_index is None else start_index
        stop_index = total if stop_index is None else stop_index
        start_index = total - (-start_index % total) if start_index < 0 else start_index
        stop_index = total - (-stop_index % total) if stop_index < 0 else stop_index
        if start_index > stop_index:
            raise Exception(f'Cannot iterate through items. Start index "{start_index}" is higher than stop index "{stop_index}".')
        # setup start page and stop page
        start_page = math.floor(start_index / page_size)
        stop_page = math.floor(stop_index / page_size)
        # yield values
        for page_index in range(start_page, stop_page + 1):
            start_index_on_page = 0 if page_index != start_page else start_index % page_size
            stop_index_on_page = page_size if page_index != stop_page else stop_index % page_size
            # get items
            items = self._items_on_page(page_index, start_index_on_page, stop_index_on_page, list_name=list_name)
            if items is None:
                return
            # return item
            for item in self._items_on_page(page_index, start_index_on_page, stop_index_on_page, list_name=list_name):
                yield item

    def items_count(self, list_name=__itemList__) -> int:
        page_info = self._page_info(list_name=list_name)
        if page_info is None:
            return -1
            # raise Exception(f'Cannot resolve items_count. This is not a paged call.')
        total = page_info["total"]
        return total

    def __str__(self):
        result = self.json
        if result is not None:
            return result.to_str()
        return result
