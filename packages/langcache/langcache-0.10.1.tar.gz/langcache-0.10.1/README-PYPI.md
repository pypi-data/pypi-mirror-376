# langcache

Developer-friendly & type-safe Python SDK specifically catered to leverage *langcache* API.


<!-- Start Summary [summary] -->
## Summary

LangCache: API for managing a [Redis LangCache](https://redis.io/docs/latest/develop/ai/langcache/) service.
<!-- End Summary [summary] -->


<!-- No Table of Contents [toc] -->

<!-- Start SDK Installation [installation] -->
## SDK Installation

> [!NOTE]
> **Python version upgrade policy**
>
> Once a Python version reaches its [official end of life date](https://devguide.python.org/versions/), a 3-month grace period is provided for users to upgrade. Following this grace period, the minimum python version supported in the SDK will be updated.

The SDK can be installed with *uv*, *pip*, or *poetry* package managers.

### uv

*uv* is a fast Python package installer and resolver, designed as a drop-in replacement for pip and pip-tools. It's recommended for its speed and modern Python tooling capabilities.

```bash
uv add langcache
```

### PIP

*PIP* is the default package installer for Python, enabling easy installation and management of packages from PyPI via the command line.

```bash
pip install langcache
```

### Poetry

*Poetry* is a modern tool that simplifies dependency management and package publishing by using a single `pyproject.toml` file to handle project metadata and dependencies.

```bash
poetry add langcache
```

### Shell and script usage with `uv`

You can use this SDK in a Python shell with [uv](https://docs.astral.sh/uv/) and the `uvx` command that comes with it like so:

```shell
uvx --from langcache python
```

It's also possible to write a standalone Python script without needing to set up a whole project like so:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "langcache",
# ]
# ///

from langcache import LangCache

sdk = LangCache(
  # SDK arguments
)

# Rest of script here...
```

Once that is saved to a file, you can run it with `uv run script.py` where
`script.py` can be replaced with the actual file name.
<!-- End SDK Installation [installation] -->

<!-- Start IDE Support [idesupport] -->
## IDE Support

### PyCharm

Generally, the SDK will work well with most IDEs out of the box. However, when using PyCharm, you can enjoy much better integration with Pydantic by installing an additional plugin.

- [PyCharm Pydantic Plugin](https://docs.pydantic.dev/latest/integrations/pycharm/)
<!-- End IDE Support [idesupport] -->

<!-- Start SDK Example Usage [usage] -->
## SDK Example Usage

### Save an entry

Save an entry to the cache

```python
# Synchronous Example
from langcache import LangCache


with LangCache(
    server_url="https://api.example.com",
    cache_id="<id>",
    api_key="<LANGCACHE_API_KEY>",
) as lang_cache:

    res = lang_cache.set(prompt="How does semantic caching work?", response="Semantic caching stores and retrieves data based on meaning, not exact matches.")

    # Handle response
    print(res)
```

</br>

The same SDK client can also be used to make asynchronous requests by importing asyncio.
```python
# Asynchronous Example
import asyncio
from langcache import LangCache

async def main():

    async with LangCache(
        server_url="https://api.example.com",
        cache_id="<id>",
        api_key="<LANGCACHE_API_KEY>",
    ) as lang_cache:

        res = await lang_cache.set_async(prompt="How does semantic caching work?", response="Semantic caching stores and retrieves data based on meaning, not exact matches.")

        # Handle response
        print(res)

asyncio.run(main())
```

### Search for entries

Search for entries in the cache

```python
# Synchronous Example
from langcache import LangCache


with LangCache(
    server_url="https://api.example.com",
    cache_id="<id>",
    api_key="<LANGCACHE_API_KEY>",
) as lang_cache:

    res = lang_cache.search(prompt="How does semantic caching work?")

    # Handle response
    print(res)
```

</br>

The same SDK client can also be used to make asynchronous requests by importing asyncio.
```python
# Asynchronous Example
import asyncio
from langcache import LangCache

async def main():

    async with LangCache(
        server_url="https://api.example.com",
        cache_id="<id>",
        api_key="<LANGCACHE_API_KEY>",
    ) as lang_cache:

        res = await lang_cache.search_async(prompt="How does semantic caching work?")

        # Handle response
        print(res)

asyncio.run(main())
```

### Delete an entry

Delete an entry from the cache by id

```python
# Synchronous Example
from langcache import LangCache


with LangCache(
    server_url="https://api.example.com",
    cache_id="<id>",
    api_key="<LANGCACHE_API_KEY>",
) as lang_cache:

    lang_cache.delete_by_id(entry_id="<id>")

    # Use the SDK ...
```

</br>

The same SDK client can also be used to make asynchronous requests by importing asyncio.
```python
# Asynchronous Example
import asyncio
from langcache import LangCache

async def main():

    async with LangCache(
        server_url="https://api.example.com",
        cache_id="<id>",
        api_key="<LANGCACHE_API_KEY>",
    ) as lang_cache:

        await lang_cache.delete_by_id_async(entry_id="<id>")

        # Use the SDK ...

asyncio.run(main())
```

### Delete entries

Delete entries based on attributes

```python
# Synchronous Example
from langcache import LangCache


with LangCache(
    server_url="https://api.example.com",
    cache_id="<id>",
    api_key="<LANGCACHE_API_KEY>",
) as lang_cache:

    res = lang_cache.delete_query(attributes={
        "language": "en",
        "topic": "ai",
    })

    # Handle response
    print(res)
```

</br>

The same SDK client can also be used to make asynchronous requests by importing asyncio.
```python
# Asynchronous Example
import asyncio
from langcache import LangCache

async def main():

    async with LangCache(
        server_url="https://api.example.com",
        cache_id="<id>",
        api_key="<LANGCACHE_API_KEY>",
    ) as lang_cache:

        res = await lang_cache.delete_query_async(attributes={
            "language": "en",
            "topic": "ai",
        })

        # Handle response
        print(res)

asyncio.run(main())
```
<!-- End SDK Example Usage [usage] -->

### Use exact search

Search for entries in the cache using both exact and semantic search

```python
from langcache import LangCache
from langcache.models import SearchStrategy

with LangCache(
    server_url="https://api.example.com",
    cache_id="<id>",
    api_key="<LANGCACHE_API_KEY>",
) as lang_cache:

    res = lang_cache.search(prompt="How does semantic caching work?", search_strategies=[SearchStrategy.EXACT, SearchStrategy.SEMANTIC])

    # Handle response
    print(res)
```


<!-- No Authentication [security] -->

<!-- Start Available Resources and Operations [operations] -->
## Available Resources and Operations

<details open>
<summary>Available methods</summary>

### [LangCache SDK](https://github.com/redis/langcache-sdks/blob/master/langcache-python-sdk/docs/sdks/langcache/README.md)

* [delete_query](https://github.com/redis/langcache-sdks/blob/master/langcache-python-sdk/docs/sdks/langcache/README.md#delete_query) - Deletes multiple cache entries based on specified attributes. If no attributes are provided, all entries in the cache are deleted.
* [set](https://github.com/redis/langcache-sdks/blob/master/langcache-python-sdk/docs/sdks/langcache/README.md#set) - Adds an entry to the cache with a prompt and response.
* [search](https://github.com/redis/langcache-sdks/blob/master/langcache-python-sdk/docs/sdks/langcache/README.md#search) - Searches the cache for entries that match the prompt and attributes. If no entries are found, this endpoint returns an empty array.
* [delete_by_id](https://github.com/redis/langcache-sdks/blob/master/langcache-python-sdk/docs/sdks/langcache/README.md#delete_by_id) - Deletes a single cache entry by the entry ID.

</details>
<!-- End Available Resources and Operations [operations] -->

<!-- No Global Parameters [global-parameters] -->

<!-- Start Retries [retries] -->
## Retries

Some of the endpoints in this SDK support retries. If you use the SDK without any configuration, it will fall back to the default retry strategy provided by the API. However, the default retry strategy can be overridden on a per-operation basis, or across the entire SDK.

To change the default retry strategy for a single API call, simply provide a `RetryConfig` object to the call:
```python
from langcache import LangCache
from langcache.utils import BackoffStrategy, RetryConfig


with LangCache(
    server_url="https://api.example.com",
    cache_id="<id>",
    api_key="<LANGCACHE_API_KEY>",
) as lang_cache:

    res = lang_cache.delete_query(attributes={
        "language": "en",
        "topic": "ai",
    },
        RetryConfig("backoff", BackoffStrategy(1, 50, 1.1, 100), False))

    # Handle response
    print(res)

```

If you'd like to override the default retry strategy for all operations that support retries, you can use the `retry_config` optional parameter when initializing the SDK:
```python
from langcache import LangCache
from langcache.utils import BackoffStrategy, RetryConfig


with LangCache(
    server_url="https://api.example.com",
    retry_config=RetryConfig("backoff", BackoffStrategy(1, 50, 1.1, 100), False),
    cache_id="<id>",
    api_key="<LANGCACHE_API_KEY>",
) as lang_cache:

    res = lang_cache.delete_query(attributes={
        "language": "en",
        "topic": "ai",
    })

    # Handle response
    print(res)

```
<!-- End Retries [retries] -->

<!-- Start Error Handling [errors] -->
## Error Handling

[`LangCacheError`](https://github.com/redis/langcache-sdks/blob/master/langcache-python-sdk/./src/langcache/errors/langcacheerror.py) is the base class for all HTTP error responses. It has the following properties:

| Property           | Type             | Description                                                                             |
| ------------------ | ---------------- | --------------------------------------------------------------------------------------- |
| `err.message`      | `str`            | Error message                                                                           |
| `err.status_code`  | `int`            | HTTP response status code eg `404`                                                      |
| `err.headers`      | `httpx.Headers`  | HTTP response headers                                                                   |
| `err.body`         | `str`            | HTTP body. Can be empty string if no body is returned.                                  |
| `err.raw_response` | `httpx.Response` | Raw HTTP response                                                                       |
| `err.data`         |                  | Optional. Some errors may contain structured data. [See Error Classes](https://github.com/redis/langcache-sdks/blob/master/langcache-python-sdk/#error-classes). |

### Example
```python
from langcache import LangCache, errors


with LangCache(
    server_url="https://api.example.com",
    cache_id="<id>",
    api_key="<LANGCACHE_API_KEY>",
) as lang_cache:
    res = None
    try:

        res = lang_cache.delete_query(attributes={
            "language": "en",
            "topic": "ai",
        })

        # Handle response
        print(res)


    except errors.LangCacheError as e:
        # The base class for HTTP error responses
        print(e.message)
        print(e.status_code)
        print(e.body)
        print(e.headers)
        print(e.raw_response)

        # Depending on the method different errors may be thrown
        if isinstance(e, errors.BadRequestErrorResponseContent):
            print(e.data.title)  # str
            print(e.data.status)  # Optional[int]
            print(e.data.detail)  # Optional[str]
            print(e.data.instance)  # Optional[str]
            print(e.data.type)  # models.BadRequestErrorURI
```

### Error Classes
**Primary errors:**
* [`LangCacheError`](https://github.com/redis/langcache-sdks/blob/master/langcache-python-sdk/./src/langcache/errors/langcacheerror.py): The base class for HTTP error responses.
  * [`BadRequestErrorResponseContent`](https://github.com/redis/langcache-sdks/blob/master/langcache-python-sdk/./src/langcache/errors/badrequesterrorresponsecontent.py): BadRequestError 400 response. Status code `400`.
  * [`AuthenticationErrorResponseContent`](https://github.com/redis/langcache-sdks/blob/master/langcache-python-sdk/./src/langcache/errors/authenticationerrorresponsecontent.py): AuthenticationError 401 response. Status code `401`.
  * [`ForbiddenErrorResponseContent`](https://github.com/redis/langcache-sdks/blob/master/langcache-python-sdk/./src/langcache/errors/forbiddenerrorresponsecontent.py): ForbiddenError 403 response. Status code `403`.
  * [`NotFoundErrorResponseContent`](https://github.com/redis/langcache-sdks/blob/master/langcache-python-sdk/./src/langcache/errors/notfounderrorresponsecontent.py): NotFoundError 404 response. Status code `404`.
  * [`PayloadTooLargeErrorResponseContent`](https://github.com/redis/langcache-sdks/blob/master/langcache-python-sdk/./src/langcache/errors/payloadtoolargeerrorresponsecontent.py): PayloadTooLargeError 413 response. Status code `413`.
  * [`ResourceUnavailableErrorResponseContent`](https://github.com/redis/langcache-sdks/blob/master/langcache-python-sdk/./src/langcache/errors/resourceunavailableerrorresponsecontent.py): ResourceUnavailableError 424 response. Status code `424`.
  * [`TooManyRequestsErrorResponseContent`](https://github.com/redis/langcache-sdks/blob/master/langcache-python-sdk/./src/langcache/errors/toomanyrequestserrorresponsecontent.py): TooManyRequestsError 429 response. Status code `429`.
  * [`UnexpectedErrorResponseContent`](https://github.com/redis/langcache-sdks/blob/master/langcache-python-sdk/./src/langcache/errors/unexpectederrorresponsecontent.py): UnexpectedError 500 response. Status code `500`.

<details><summary>Less common errors (5)</summary>

<br />

**Network errors:**
* [`httpx.RequestError`](https://www.python-httpx.org/exceptions/#httpx.RequestError): Base class for request errors.
    * [`httpx.ConnectError`](https://www.python-httpx.org/exceptions/#httpx.ConnectError): HTTP client was unable to make a request to a server.
    * [`httpx.TimeoutException`](https://www.python-httpx.org/exceptions/#httpx.TimeoutException): HTTP request timed out.


**Inherit from [`LangCacheError`](https://github.com/redis/langcache-sdks/blob/master/langcache-python-sdk/./src/langcache/errors/langcacheerror.py)**:
* [`ResponseValidationError`](https://github.com/redis/langcache-sdks/blob/master/langcache-python-sdk/./src/langcache/errors/responsevalidationerror.py): Type mismatch between the response data and the expected Pydantic model. Provides access to the Pydantic validation error via the `cause` attribute.

</details>
<!-- End Error Handling [errors] -->

<!-- Start Custom HTTP Client [http-client] -->
## Custom HTTP Client

The Python SDK makes API calls using the [httpx](https://www.python-httpx.org/) HTTP library.  In order to provide a convenient way to configure timeouts, cookies, proxies, custom headers, and other low-level configuration, you can initialize the SDK client with your own HTTP client instance.
Depending on whether you are using the sync or async version of the SDK, you can pass an instance of `HttpClient` or `AsyncHttpClient` respectively, which are Protocol's ensuring that the client has the necessary methods to make API calls.
This allows you to wrap the client with your own custom logic, such as adding custom headers, logging, or error handling, or you can just pass an instance of `httpx.Client` or `httpx.AsyncClient` directly.

For example, you could specify a header for every request that this sdk makes as follows:
```python
from langcache import LangCache
import httpx

http_client = httpx.Client(headers={"x-custom-header": "someValue"})
s = LangCache(client=http_client)
```

or you could wrap the client with your own custom logic:
```python
from langcache import LangCache
from langcache.httpclient import AsyncHttpClient
import httpx

class CustomClient(AsyncHttpClient):
    client: AsyncHttpClient

    def __init__(self, client: AsyncHttpClient):
        self.client = client

    async def send(
        self,
        request: httpx.Request,
        *,
        stream: bool = False,
        auth: Union[
            httpx._types.AuthTypes, httpx._client.UseClientDefault, None
        ] = httpx.USE_CLIENT_DEFAULT,
        follow_redirects: Union[
            bool, httpx._client.UseClientDefault
        ] = httpx.USE_CLIENT_DEFAULT,
    ) -> httpx.Response:
        request.headers["Client-Level-Header"] = "added by client"

        return await self.client.send(
            request, stream=stream, auth=auth, follow_redirects=follow_redirects
        )

    def build_request(
        self,
        method: str,
        url: httpx._types.URLTypes,
        *,
        content: Optional[httpx._types.RequestContent] = None,
        data: Optional[httpx._types.RequestData] = None,
        files: Optional[httpx._types.RequestFiles] = None,
        json: Optional[Any] = None,
        params: Optional[httpx._types.QueryParamTypes] = None,
        headers: Optional[httpx._types.HeaderTypes] = None,
        cookies: Optional[httpx._types.CookieTypes] = None,
        timeout: Union[
            httpx._types.TimeoutTypes, httpx._client.UseClientDefault
        ] = httpx.USE_CLIENT_DEFAULT,
        extensions: Optional[httpx._types.RequestExtensions] = None,
    ) -> httpx.Request:
        return self.client.build_request(
            method,
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            timeout=timeout,
            extensions=extensions,
        )

s = LangCache(async_client=CustomClient(httpx.AsyncClient()))
```
<!-- End Custom HTTP Client [http-client] -->

<!-- Start Resource Management [resource-management] -->
## Resource Management

The `LangCache` class implements the context manager protocol and registers a finalizer function to close the underlying sync and async HTTPX clients it uses under the hood. This will close HTTP connections, release memory and free up other resources held by the SDK. In short-lived Python programs and notebooks that make a few SDK method calls, resource management may not be a concern. However, in longer-lived programs, it is beneficial to create a single SDK instance via a [context manager][context-manager] and reuse it across the application.

[context-manager]: https://docs.python.org/3/reference/datamodel.html#context-managers

```python
from langcache import LangCache
def main():

    with LangCache(
        server_url="https://api.example.com",
        cache_id="<id>",
        api_key="<LANGCACHE_API_KEY>",
    ) as lang_cache:
        # Rest of application here...


# Or when using async:
async def amain():

    async with LangCache(
        server_url="https://api.example.com",
        cache_id="<id>",
        api_key="<LANGCACHE_API_KEY>",
    ) as lang_cache:
        # Rest of application here...
```
<!-- End Resource Management [resource-management] -->

<!-- Start Debugging [debug] -->
## Debugging

You can setup your SDK to emit debug logs for SDK requests and responses.

You can pass your own logger class directly into your SDK.
```python
from langcache import LangCache
import logging

logging.basicConfig(level=logging.DEBUG)
s = LangCache(server_url="https://example.com", debug_logger=logging.getLogger("langcache"))
```

You can also enable a default debug logger by setting an environment variable `LANGCACHE_DEBUG` to true.
<!-- End Debugging [debug] -->

<!-- Placeholder for Future Speakeasy SDK Sections -->

# Development

## Maturity

This SDK is in beta, and there may be breaking changes between versions without a major version update. Therefore, we recommend pinning usage
to a specific package version. This way, you can install the same version each time without breaking changes unless you are intentionally
looking for the latest version.
