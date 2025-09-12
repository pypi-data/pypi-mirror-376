# TODO: rewrite with more example

In serverless, use this decorator:
```py
from python_sdk_local.http_response import handler_decorator
from logger_local.Logger import Logger
logger = Logger.create_logger(object=your_logger_object)
@handler_decorator(logger=logger)
def my_handler(request_parameters: dict) -> dict:
  # here you can use both camelCase and snake_case keys from request_parameters
```