# MethodSecurity Python Library

[![fern shield](https://img.shields.io/badge/%F0%9F%8C%BF-Built%20with%20Fern-brightgreen)](https://buildwithfern.com?utm_source=github&utm_medium=github&utm_campaign=readme&utm_source=https%3A%2F%2Fgithub.com%2Fmethod-security%2Fmethod-python-sdk)
[![pypi](https://img.shields.io/pypi/v/methodsdk)](https://pypi.python.org/pypi/methodsdk)

The MethodSecurity Python library provides convenient access to the MethodSecurity APIs from Python.

## Installation

```sh
pip install methodsdk
```

## Reference

A full reference for this library is available [here](https://github.com/method-security/method-python-sdk/blob/HEAD/./reference.md).

## Usage

Instantiate and use the client with the following:

```python
from method_security import MethodSecurityApi

client = MethodSecurityApi(
    o_auth_2_0_bearer_token="YOUR_O_AUTH_2_0_BEARER_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.issues.get_issue(
    id="ri.method.ontology.issue.8c99d39e-4b5f-331c-8119-7d177fb4f498",
)
```

## Async Client

The SDK also exports an `async` client so that you can make non-blocking calls to our API.

```python
import asyncio

from method_security import AsyncMethodSecurityApi

client = AsyncMethodSecurityApi(
    o_auth_2_0_bearer_token="YOUR_O_AUTH_2_0_BEARER_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)


async def main() -> None:
    await client.issues.get_issue(
        id="ri.method.ontology.issue.8c99d39e-4b5f-331c-8119-7d177fb4f498",
    )


asyncio.run(main())
```

## Exception Handling

When the API returns a non-success status code (4xx or 5xx response), a subclass of the following error
will be thrown.

```python
from method_security.core.api_error import ApiError

try:
    client.issues.get_issue()
except ApiError as e:
    print(e.status_code)
    print(e.body)
```

## Advanced

### Access Raw Response Data

The SDK provides access to raw response data, including headers, through the `.with_raw_response` property.
The `.with_raw_response` property returns a "raw" client that can be used to access the `.headers` and `.data` attributes.

```python
from method_security import MethodSecurityApi

client = MethodSecurityApi(
    ...,
)
response = client.issues.with_raw_response.get_issue()
print(response.headers)  # access the response headers
print(response.data)  # access the underlying object
```

### Retries

The SDK is instrumented with automatic retries with exponential backoff. A request will be retried as long
as the request is deemed retryable and the number of retry attempts has not grown larger than the configured
retry limit (default: 2).

A request is deemed retryable when any of the following HTTP status codes is returned:

- [408](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/408) (Timeout)
- [429](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/429) (Too Many Requests)
- [5XX](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/500) (Internal Server Errors)

Use the `max_retries` request option to configure this behavior.

```python
client.issues.get_issue(request_options={
    "max_retries": 1
})
```

### Timeouts

The SDK defaults to a 60 second timeout. You can configure this with a timeout option at the client or request level.

```python

from method_security import MethodSecurityApi

client = MethodSecurityApi(
    ...,
    timeout=20.0,
)


# Override timeout for a specific method
client.issues.get_issue(request_options={
    "timeout_in_seconds": 1
})
```

### Custom Client

You can override the `httpx` client to customize it for your use-case. Some common use-cases include support for proxies
and transports.

```python
import httpx
from method_security import MethodSecurityApi

client = MethodSecurityApi(
    ...,
    httpx_client=httpx.Client(
        proxies="http://my.test.proxy.example.com",
        transport=httpx.HTTPTransport(local_address="0.0.0.0"),
    ),
)
```

## Contributing

While we value open-source contributions to this SDK, this library is generated programmatically.
Additions made directly to this library would have to be moved over to our generation code,
otherwise they would be overwritten upon the next generated release. Feel free to open a PR as
a proof of concept, but know that we will not be able to merge it as-is. We suggest opening
an issue first to discuss with us!

On the other hand, contributions to the README are always very welcome!
