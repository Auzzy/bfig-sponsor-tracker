import io
import os
import shutil
from os.path import basename, join, relpath, splitext

import wand.image
from flask import flash
from werkzeug.datastructures import FileStorage

from sponsortracker import data, model
from sponsortracker.dealtracker.app import asset_uploader, preview_uploader, thumb_uploader

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
    
    def save(self, deal):
        if not hasattr(self, "UPLOADER") or not self.UPLOADER:
            raise AttributeError("To save this image, an uploader must be defined.")
        
        byte_stream = io.BytesIO()
        super(Image, self).save(file=byte_stream)
        byte_stream.seek(0)
        file_storage = FileStorage(stream=byte_stream, filename=self.filename)
        return self.UPLOADER.save(file_storage, folder=str(deal.sponsor.id))
    
    @classmethod
    def discard(cls, deal, filename):
        os.remove(cls.path(deal, filename))
    
    @classmethod
    def path(cls, deal, filename):
        return cls.UPLOADER.path(cls.relpath(deal, filename))
    
    @classmethod
    def url(cls, deal, filename):
        return cls.UPLOADER.url(cls.relpath(deal, filename))
    
    @classmethod
    def relpath(cls, deal, filename):
        return join(str(deal.sponsor.id), filename)

class Preview(Image):
    UPLOADER = preview_uploader
    
    def __init__(self, filename, *args, **kwargs):
        super(Preview, self).__init__(filename, *args, **kwargs)
    
    @staticmethod
    def stash(deal, type, filename):
        with open(Preview.path(deal, filename), 'rb') as preview_file:
            file_storage = FileStorage(stream=preview_file, filename=filename)
            asset_filename = Asset.stash(deal, type, file_storage)
        
        os.remove(Preview.path(deal, filename))
        return asset_filename

class Thumbnail(Image):
    DEFAULT_WIDTH = 100
    DEFAULT_HEIGHT = 100
    FORMAT = data._DigitalFormat.PNG
    
    UPLOADER = thumb_uploader
    
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
        # thumbnail.format = data._DigitalFormat.PNG.format
        return thumbnail.save(deal)
    
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
    
    def save(self, deal):
        self.format = Thumbnail.FORMAT.format
        return super(Thumbnail, self).save(deal)
    
    @classmethod
    def relpath(cls, deal, filename):
        filename = "{0}.{1}".format(splitext(filename)[0], Thumbnail.FORMAT.ext)
        return super(Thumbnail, cls).relpath(deal, filename)

class Asset(Image):
    UPLOADER = asset_uploader
    
    def __init__(self, filename, *args, **kwargs):
        super(Asset, self).__init__(filename, *args, **kwargs)
    
    @staticmethod
    def stash(deal, type, file_storage):
        asset_filename = Asset.load(file_storage).save(deal)
        Thumbnail.create(file_storage, deal, size={"width": None})
        
        filename = basename(asset_filename)
        Asset._store(deal, type, filename)
        
        return filename
    
    @staticmethod
    def _store(deal, type, filename):
        deal.assets.append(model.Asset(deal.id, type, filename))
        model.db.session.commit()
    
    @staticmethod
    def delete(id):
        asset_model = model.Asset.query.get(id)
        deal = asset_model.deal
        
        Asset.discard(deal, asset_model.filename)
        Thumbnail.discard(deal, asset_model.filename)
        
        model.db.session.delete(asset_model)
        model.db.session.commit()

def verify(deal, form):
    preview = Preview.load(form.asset.data)
    spec = data.AssetType[form.type.data].spec
    
    if preview.format not in spec.format_names:
        flash("Image format was {0}. Expected one of the following: {1}.".format(preview.format, ', '.join(spec.format_names)), 'preview')
        format = spec.formats[0] if len(spec.formats) == 1 else type(spec.formats[0]).preferred()
        preview.format = format.format
    
    if preview.colorspace not in spec.color_mode_names:
        flash("Image color mode was {0}. Expected one of the following: {1}.".format(preview.colorspace, ', '.join(spec.color_mode_names)), 'preview')
        preview.colorspace = spec.color_modes[0].value
    
    if preview.resolution != (spec.dpi, spec.dpi):
        flash("Image resolution was {res[0]}x{res[1]}. Expected {spec.dpi}x{spec.dpi}.".format(res=preview.resolution, spec=spec), 'preview')
        preview.resolution = (spec.dpi, spec.dpi)
    
    if preview.width != spec.width or preview.height != spec.height:
        # Don't do anything about sizes that don't match. Marketing will handle it.
        pass
    
    if preview.dirty:
        filename = preview.save(deal)
        return filename.split('/')[-1]
    else:
        Asset.stash(deal, form.type.data, form.asset.data)
        return None