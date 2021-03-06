import io
import os
import shutil
from os.path import basename, join, relpath, splitext

import boto
import wand.image
from flask import flash
from werkzeug.datastructures import FileStorage

from sponsortracker import data, model
from sponsortracker.app import app, preview_uploader

s3conn = boto.connect_s3()
dealtracker_bucket = s3conn.get_bucket(app.config["S3_BUCKET"])

class Image(wand.image.Image):
    def __init__(self, name, *args, **kwargs):
        if "file" in kwargs:
            kwargs["file"].seek(0)
        
        super(Image, self).__init__(*args, **kwargs)
        
        if "file" in kwargs:
            kwargs["file"].seek(0)
        
        self.filename = name
    
    @classmethod
    def load(cls, file_storage):
        return cls(file_storage.filename, file=file_storage.stream)
    
    def __setattr__(self, name, value):
        super(Image, self).__setattr__(name, value)
        if name == "format":
            self.filename = "{file}.{ext}".format(file=splitext(self.filename)[0], ext=self.format.lower())
    
    def stash(self, deal):
        key = self._s3key(deal, self.filename)
        key.set_contents_from_string(self.make_blob(), headers={"Content-Type": self.mimetype})
        return key.key.rsplit('/', 1)[-1]
    
    @classmethod
    def _s3key(cls, deal, filename):
        key = "{sponsor}/{year}/{cls}/{filename}".format(sponsor=deal.sponsor.name, year=deal.year, cls=cls.__name__.lower(), filename=filename)
        return boto.s3.key.Key(dealtracker_bucket, key)
    
    @classmethod
    def discard(cls, deal, filename):
        cls._s3key(deal, filename).delete()
    
    @classmethod
    def url(cls, deal, filename):
        return cls._s3key(deal, filename).generate_url(expires_in=0, query_auth=False)
    
    @classmethod
    def get(cls, deal, filename, dest=None):
        dest = dest or filename
        cls._s3key(deal, filename).get_contents_to_filename(dest)
        return dest

class Preview(Image):
    def __init__(self, filename, *args, **kwargs):
        super(Preview, self).__init__(filename, *args, **kwargs)
    
    @staticmethod
    def keep(deal, type, filename):
        with open(Preview.path(deal, filename), 'rb') as preview_file:
            file_storage = FileStorage(stream=preview_file, filename=filename)
            asset_filename = Asset.create(deal, type, file_storage)
        Preview.discard(deal, filename)
        return asset_filename
    
    def stash(self, deal):
        byte_stream = io.BytesIO()
        self.save(file=byte_stream)
        byte_stream.seek(0)
        
        filename = "{0}-{1}".format(deal.sponsor.name, self.filename).replace(' ', '-')
        file_storage = FileStorage(stream=byte_stream, filename=filename)
        return preview_uploader.save(file_storage)
    
    @staticmethod
    def discard(deal, filename):
        os.remove(Preview.path(deal, filename))
    
    @staticmethod
    def path(deal, filename):
        return preview_uploader.path(filename)
    
    @staticmethod
    def url(deal, filename):
        return preview_uploader.url(filename)

class Thumbnail(Image):
    DEFAULT_WIDTH = 100
    DEFAULT_HEIGHT = 100
    FORMAT = data._DigitalFormat.PNG
    
    def __init__(self, filename, *args, **kwargs):
        super(Thumbnail, self).__init__(filename, *args, **kwargs)
        
        self.format = Thumbnail.FORMAT.format
    
    @staticmethod
    def create(file_storage, deal, size=None):
        return Thumbnail.create_from_file(file_storage.filename, file_storage.stream, deal, size)
        
    @staticmethod
    def create_from_file(filename, file, deal, size=None):
        thumbnail = Thumbnail(filename, file=file)
        thumbnail._resize(size)
        return thumbnail.stash(deal)
    
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
    
    @classmethod
    def url(cls, deal, filename):
        filename = "{0}.{1}".format(os.path.splitext(filename)[0], Thumbnail.FORMAT.ext)
        return super(Thumbnail, cls).url(deal, filename)

class Asset(Image):
    def __init__(self, filename, *args, **kwargs):
        super(Asset, self).__init__(filename, *args, **kwargs)
    
    @staticmethod
    def create(deal, type, file_storage):
        asset_filename = Asset.load(file_storage).stash(deal)
        thumb = Thumbnail.create(file_storage, deal, size={"width": None})
        
        filename = basename(asset_filename)
        deal.assets.append(model.Asset(deal.id, type, filename))
        model.db.session.commit()
        
        return filename
    
    @staticmethod
    def delete(id):
        asset = model.Asset.query.get(id)
        deal = asset.deal
        
        Asset.discard(deal, asset.filename)
        Thumbnail.discard(deal, asset.filename)
        
        model.db.session.delete(asset)
        model.db.session.commit()