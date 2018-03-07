import json

import treq
from txhttp import Handler
from werkzeug.exceptions import BadRequest

from .file import File


class IndexHandler(Handler):
    def get(self, request):
        request.setHeader(b'Content-Type', b'text/html; charset=utf-8')
        return open('static/index.html').read()


class TextHandlerMixin(object):
    def handle(self, text):
        self.request.setHeader(b'Content-Type', b'text/plain; charset=utf-8')
        return text


class UploadHandler(Handler, TextHandlerMixin):
    def post(self, request):
        if b'file' in request.args and request.args[b'file'] and request.args[b'file'][0]:
            # We've got the file
            file = File.from_buffer(buffer=request.args[b'file'][0])
            if file.content_type not in ['application/pdf']:
                raise BadRequest('You need to upload a file of type pdf')

            return self.handle(str(file))
        else:
            raise BadRequest('You need to upload a file')


class FetchHandler(Handler, TextHandlerMixin):
    async def post(self, request):
        """
        :param twisted.web.server.Request request:
        :return:
        """
        if b'url' in request.args and request.args[b'url'] and request.args[b'url'][0]:
            url = request.args[b'url'][0].decode()
        else:
            raise BadRequest('You need to provide a valid URL')

        headers = {
            k: v
            for k, v in request.getAllHeaders().items()
            if k in [b'user-agent']
        }
        response = await treq.get(url, headers=headers)

        if request.code != 200:
            request.setResponseCode(502)
            return json.dumps({
                'message': 'Could not fetch resource from remote server',
                'status': response.code,
            })

        content = await treq.content(response)

        file = File.from_buffer(buffer=content)
        if file.content_type not in ['application/pdf']:
            raise BadRequest('You need to fetch a file of type pdf')

        return self.handle(str(file))


class TextHandler(Handler, TextHandlerMixin):
    def post(self, request):
        text = request.args.get(b'text', [b''])[0]
        if not text:
            raise BadRequest('You need to send some text')
        return self.handle(text.decode())
