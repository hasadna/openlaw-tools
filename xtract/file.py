import copy
import mimetypes
import os
import subprocess
from io import BytesIO
from uuid import uuid4

import magic
from PyPDF2.pdf import DocumentInformation


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
        absolute_path = os.path.abspath(path)
        if not os.path.exists(absolute_path) or not os.path.exists(path):
            raise ValueError('File does not exist')
        with open(absolute_path, 'rb') as f:
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
        setattr(obj, '_dirname', os.path.dirname(path))
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
    def dirname(self):
        return getattr(self, '_dirname')

    @property
    def filename(self):
        if not hasattr(self, '_filename'):
            setattr(self, '_filename', str(uuid4()))
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
    def absolute_path(self):
        return os.path.join(self.dirname, self.basename)

    def save_as(self, base_dir=None, overwrite=False, inplace=True):
        if not base_dir and not self.dirname:
            raise ValueError('You must provide a base directory to save the file')
        file = self
        if not inplace:
            file = copy.deepcopy(self)
        if file._content is None:
            raise ValueError('No content to save')
        setattr(file, '_dirname', base_dir)
        if os.path.exists(file.absolute_path) and not overwrite:
            raise FileExistsError()
        with open(file.absolute_path, 'wb') as f:
            f.write(file._content)
            f.flush()
        return file

    @property
    def exif_data(self):
        return getattr(self, '_exif_data', {})

    def __str__(self):
        return self._content.decode()


class PDFFile(File):
    @property
    def exif_data(self) -> DocumentInformation:
        if not hasattr(self, '_exif_data'):
            from PyPDF2 import PdfFileReader
            reader = PdfFileReader(BytesIO(self._content))
            setattr(self, '_exif_data', reader.getDocumentInfo())
        return getattr(self, '_exif_data', {})

    def __str__(self):
        if not hasattr(self, '_string'):
            cmd_args = ['pdftotext', self.absolute_path]
            if 'indesign' in self.exif_data.creator.lower():
                cmd_args = ['pdftotext', '-raw', self.absolute_path]
            process = subprocess.Popen(
                cmd_args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                encoding='utf-8',
            )
            process.communicate()
            filename = os.path.join(self.dirname, self.filename)
            txt_file = File.from_file(f'{filename}.txt')
            setattr(self, '_string', str(txt_file))
        return getattr(self, '_string')


File.set_handler('application/pdf', PDFFile)
