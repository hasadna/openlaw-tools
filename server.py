import os

from txhttp import Application
from werkzeug.exceptions import HTTPException, InternalServerError

from openlaw_tools.handlers import IndexHandler, UploadHandler, FetchHandler, TextHandler


class ToolsServer(object):
    app = Application()

    def __init__(self) -> None:
        self.base_dir = os.path.abspath(os.path.dirname(__file__))
        directories = [
            'uploads/file',
            'uploads/remote-file',
            'uploads/text',
        ]
        for directory in directories:
            os.makedirs(os.path.join(self.base_dir, directory), 0o755, True)

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.app_host = os.environ.get('APP_HOST', 'localhost')
        self.app_port = int(os.environ.get('APP_PORT', 8081))
        self.debug = bool(os.environ.get('DEBUG'))

        self.bot_lib = os.environ.get('OPENLAW_BOT_LIB')

    # @app.handle_errors(Exception)
    def handle_exceptions(self, request, failure):
        """
        :param twisted.web.server.Request request:
        :param twisted.python.failure.Failure failure:
        :rtype: str
        """
        if self.debug and not isinstance(failure.value, HTTPException):
            raise failure.value

        exception = failure.value
        if not isinstance(failure.value, HTTPException):
            # This should be avoided, possible exception occurrences should be handled in-place
            exception = InternalServerError()

        request.setResponseCode(exception.code)
        raise exception

    def run(self):
        self.app.run(host=self.app_host, port=self.app_port)


if __name__ == '__main__':
    tools = ToolsServer()

    tools.app.set_handler('/', IndexHandler.as_handler(), methods=['GET'])
    tools.app.set_handler('/upload', UploadHandler.as_handler(), methods=['POST'])
    tools.app.set_handler('/fetch', FetchHandler.as_handler(), methods=['POST'])
    tools.app.set_handler('/text', TextHandler.as_handler(), methods=['POST'])

    tools.run()
