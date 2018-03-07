import mimetypes
import os
from io import BytesIO
from uuid import uuid4

import magic


class File:
    handlers = {}

    @classmethod
    def set_handler(cls, content_type, handler):
        if content_type in cls.handlers:
            raise ValueError(f'Content Type {content_type} already has a handler')
        cls.handlers[content_type] = handler

    @classmethod
    def get_handler(cls, content_type):
        return cls.handlers.get(content_type, cls)

    @classmethod
    def from_buffer(cls, buffer):
        mime = magic.Magic(mime=True)
        content_type = mime.from_buffer(buffer)
        handler = cls.get_handler(content_type)
        obj = handler()
        setattr(obj, '_content', buffer)
        setattr(obj, '_content_type', content_type)
        return obj

    @classmethod
    def from_file(cls, path):
        with open(path, 'rb') as f:
            buffer = f.read()
        mime = magic.Magic(mime=True)
        content_type = mime.from_buffer(buffer)
        handler = cls.get_handler(content_type)
        obj = handler()
        setattr(obj, '_content', buffer)
        setattr(obj, '_content_type', content_type)
        basename = os.path.basename(path)
        filename, ext = os.path.splitext(basename)
        setattr(obj, '_filename', filename)
        setattr(obj, '_extension', ext)
        setattr(obj, '_basename', basename)
        return obj

    def __init__(self):
        self._content = None

    @property
    def content_type(self):
        if not hasattr(self, '_content_type'):
            mime = magic.Magic(mime=True)
            setattr(self, '_content_type', mime.from_buffer(self._content))
        return getattr(self, '_content_type')

    @property
    def filename(self):
        if not hasattr(self, '_filename'):
            setattr(self, '_filename', uuid4())
        return getattr(self, '_filename')

    @property
    def basename(self):
        if not hasattr(self, '_basename'):
            setattr(self, '_basename', f'{self.filename}{self.extension}')
        return getattr(self, '_basename')

    @property
    def extension(self):
        if not hasattr(self, '_extension'):
            setattr(self, '_extension', mimetypes.guess_extension(self.content_type))
        return getattr(self, '_extension')

    @property
    def exif_data(self):
        if not hasattr(self, '_exif_data'):
            setattr(self, '_exif_data', {})
        return getattr(self, '_exif_data', {})

    def __str__(self):
        return self._content.decode()


class PDFFile(File):
    def __str__(self):
        if not hasattr(self, '_string'):
            from pdftotext import PDF
            pdf = PDF(BytesIO(self._content))
            setattr(self, '_string', '\n\n'.join(pdf))
        return getattr(self, '_string')


File.set_handler('application/pdf', PDFFile)
