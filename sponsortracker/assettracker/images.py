import io
import os
import shutil
from os.path import join, relpath, splitext

import wand.image
from werkzeug.datastructures import FileStorage

from sponsortracker.assettracker.app import asset_uploader, preview_uploader, thumb_uploader

class Image(wand.image.Image):
    def __init__(self, filename, *args, **kwargs):
        if "file" in kwargs:
            kwargs["file"].seek(0)
        
        super(Image, self).__init__(*args, **kwargs)
        
        if "file" in kwargs:
            kwargs["file"].seek(0)
        
        self.filename = filename
    
    @staticmethod
    def load(field):
        return Image(field.filename, file=field.stream)
    
    def __setattr__(self, name, value):
        super(Image, self).__setattr__(name, value)
        if name == "format":
            self.filename = "{file}.{ext}".format(file=splitext(self.filename)[0], ext=self.format.lower())
    
    def save(self, sponsor_id):
        if not self.uploader:
            raise AttributeError("To save this image, an uploader must be defined.")
        
        byte_stream = io.BytesIO()
        super(Image, self).save(file=byte_stream)
        byte_stream.seek(0)
        file_storage = FileStorage(stream=byte_stream, filename=self.filename)
        filename = self.uploader.save(file_storage, folder=str(sponsor_id))
        return relpath(filename, str(sponsor_id))

class Preview(Image):
    def __init__(self, filename, *args, **kwargs):
        super(Preview, self).__init__(filename, *args, **kwargs)
        self.uploader = preview_uploader
    
    @staticmethod
    def get(file_storage):
        return Preview(file_storage.filename, file=file_storage.stream)
    
    @staticmethod
    def url(sponsor_id, filename):
        return preview_uploader.url(Preview._relpath(sponsor_id, filename))
    
    @staticmethod
    def discard(sponsor_id, filename):
        os.remove(Preview._path(sponsor_id, filename))
    
    @staticmethod
    def stash(sponsor_id, filename):
        with open(Preview._path(sponsor_id, filename), 'rb') as preview_file:
            file_storage = FileStorage(stream=preview_file, filename=filename)
            asset_filename = Asset.stash(sponsor_id, file_storage)
        
        os.remove(Preview._path(sponsor_id, filename))
        return asset_filename
    
    @staticmethod
    def _path(sponsor_id, filename):
        return preview_uploader.path(Preview._relpath(sponsor_id, filename))
    
    @staticmethod
    def _relpath(sponsor_id, filename):
        return join(str(sponsor_id), filename)

class Thumbnail(Image):
    DEFAULT_WIDTH = 100
    DEFAULT_HEIGHT = 100
    
    def __init__(self, filename, *args, **kwargs):
        super(Thumbnail, self).__init__(filename, *args, **kwargs)
        self.uploader = thumb_uploader
    
    @staticmethod
    def create(file_storage, sponsor_id, size=None):
        return Thumbnail.create_from_file(file_storage.filename, file_storage.stream, sponsor_id, size)
        
    @staticmethod
    def create_from_file(filename, file, sponsor_id, size=None):
        thumbnail = Thumbnail(filename, file=file)
        thumbnail._resize(size)
        return thumbnail.save(sponsor_id)
    
    def _resize(self, size):
        transform = ""
        if size:
            if "width" in size:
                transform += str(size["width"] or Thumbnail.DEFAULT_WIDTH)
            if "height" in size:
                transform += "x{0}".format(size["height"] or Thumbnail.DEFAULT_HEIGHT)
            if "width" in size and "height" in size:
                transform += "!"
        else:
            transform = "{0}x{1}!".format(Thumbnail.DEFAULT_WIDTH, Thumbnail.DEFAULT_HEIGHT)
        self.transform(resize=transform)

class Asset:
    @staticmethod
    def stash(sponsor_id, file_storage):
        asset_filename = asset_uploader.save(file_storage, folder=str(sponsor_id))
        file_storage.filename = relpath(asset_filename, str(sponsor_id))
        Thumbnail.create(file_storage, sponsor_id, size={"width": None})
        return asset_filename