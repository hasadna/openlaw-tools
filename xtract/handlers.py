import json
import os
import subprocess

import treq
from txhttp import Handler
from werkzeug.exceptions import BadRequest

from .file import File


class IndexHandler(Handler):
    def get(self, request):
        request.setHeader(b'Content-Type', b'text/html; charset=utf-8')
        return open('static/xtract/index.html').read()


class TextHandlerMixin(object):
    def handle(self, text):
        try:
            clear_pl = os.path.join(self.app.bot_lib, 'clear.pl')
            process = subprocess.Popen(
                [clear_pl, '-t=1'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                encoding='utf-8',
            )
            clean_text, err = process.communicate(text)
        except Exception as e:
            clean_text = str(e)

        if self.request.args.get(b'syntax') == [b'on']:
            basic_syntax = os.path.join(self.app.bot_lib, 'basic-syntax.pl')
            try:
                process = subprocess.Popen(
                    [basic_syntax],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    encoding='utf-8',
                )
                clean_text, err = process.communicate(clean_text)
            except Exception as e:
                clean_text = str(e)

        self.request.setHeader(b'Content-Type', b'text/plain; charset=utf-8')
        return clean_text


class UploadHandler(Handler, TextHandlerMixin):
    def post(self, request):
        if b'file' in request.args and request.args[b'file'] and request.args[b'file'][0]:
            # We've got the file
            file = File.from_buffer(buffer=request.args[b'file'][0])
            if file.content_type not in ['application/pdf']:
                raise BadRequest('You need to upload a file of type pdf')

            file.save_as(os.path.join(self.app.base_dir, 'uploads', 'file'))

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

        file.save_as(os.path.join(self.app.base_dir, 'uploads', 'remote-file'))

        return self.handle(str(file))


class TextHandler(Handler, TextHandlerMixin):
    def post(self, request):
        text = request.args.get(b'text', [b''])[0]
        if not text:
            raise BadRequest('You need to send some text')
        return self.handle(text.decode())
