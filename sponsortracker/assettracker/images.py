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
    
    @classmethod
    def load(cls, file_storage):
        return cls(file_storage.filename, file=file_storage.stream)
    
    def __setattr__(self, name, value):
        super(Image, self).__setattr__(name, value)
        if name == "format":
            self.filename = "{file}.{ext}".format(file=splitext(self.filename)[0], ext=self.format.lower())
    
    def save(self, sponsor_id):
        if not hasattr(self, "UPLOADER") or not self.UPLOADER:
            raise AttributeError("To save this image, an uploader must be defined.")
        
        byte_stream = io.BytesIO()
        super(Image, self).save(file=byte_stream)
        byte_stream.seek(0)
        file_storage = FileStorage(stream=byte_stream, filename=self.filename)
        return self.UPLOADER.save(file_storage, folder=str(sponsor_id))
    
    @classmethod
    def url(cls, sponsor_id, filename):
        return cls.UPLOADER.url(join(str(sponsor_id), filename))
    
    @classmethod
    def _path(cls, sponsor_id, filename):
        return cls.UPLOADER.path(join(str(sponsor_id), filename))
    
    @classmethod
    def discard(cls, sponsor_id, filename):
        os.remove(cls._path(sponsor_id, filename))

class Preview(Image):
    UPLOADER = preview_uploader
    
    def __init__(self, filename, *args, **kwargs):
        super(Preview, self).__init__(filename, *args, **kwargs)
    
    @staticmethod
    def stash(sponsor_id, filename):
        with open(Preview._path(sponsor_id, filename), 'rb') as preview_file:
            file_storage = FileStorage(stream=preview_file, filename=filename)
            asset_filename = Asset.stash(sponsor_id, file_storage)
        
        os.remove(Preview._path(sponsor_id, filename))
        return asset_filename

class Thumbnail(Image):
    DEFAULT_WIDTH = 100
    DEFAULT_HEIGHT = 100
    
    UPLOADER = thumb_uploader
    
    def __init__(self, filename, *args, **kwargs):
        super(Thumbnail, self).__init__(filename, *args, **kwargs)
    
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

class Asset(Image):
    UPLOADER = asset_uploader
    
    def __init__(self, filename, *args, **kwargs):
        super(Asset, self).__init__(filename, *args, **kwargs)
    
    @staticmethod
    def stash(sponsor_id, file_storage):
        asset_filename = Asset.load(file_storage).save(sponsor_id)
        file_storage.filename = relpath(asset_filename, str(sponsor_id))
        Thumbnail.create(file_storage, sponsor_id, size={"width": None})
        return asset_filename
    
    @staticmethod
    def delete(sponsor_id, filename):
        relfilename = relpath(filename, str(sponsor_id))
        Asset.discard(sponsor_id, relfilename)
        Thumbnail.discard(sponsor_id, relfilename)