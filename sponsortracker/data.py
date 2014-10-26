from enum import Enum

class _Format(Enum):
    def __init__(self, ext):
        self.ext = ext

class _PrintFormat(_Format):
    PDF = "pdf"
    PSD = "psd"
    AI = "al"

class _DigitalFormat(_Format):
    JPG = "jpg"
    PNG = "png"
    GIF = "gif"

class _LogoFormat(_Format):
    EPS = "eps"

ASSET_FORMATS_EXT = [fmt.ext for fmt in list(_PrintFormat) + list(_DigitalFormat) + list(_LogoFormat)]

class _ColorMode(Enum):
    RGB = "RGB"
    CMYK = "CMYK"
    BW = "Black & White"

class _DimUnits(Enum):
    IN = "in"
    PX = "px"

class ImageSpec:
    def __init__(self, dpi, color_mode, width, height, unit, formats):
        self.dpi = dpi
        self.color_mode = color_mode
        self.width = width
        self.height = height
        self.unit = unit
        self.formats = formats
    
    def __str__(self):
        dimensions_str = "Dimensions: {width}{unit}x{height}{unit}".format(width=self.width, height=self.height, unit=self.unit)
        formats_str = "Formats: {0}".format('/'.join([format.name for format in formats]))
        color_mode_str = "Color Mode: {0}".format(color_mode=self.color_mode)
        dpi_str = "{0}dpi".format(self.dpi)
        return "; ".join([dimensions_str, formats_str, color_mode_str, dpi_str])

class TextSpec:
    pass


# Each value should also contain details about each asset's required specs
class AssetType(Enum):
    DIGITAL_BANNER = ("Digital Guide - Banner", ImageSpec(72, _ColorMode.RGB, 640, 240, _DimUnits.PX, [_DigitalFormat.PNG]))
    DIGITAL_MENU = ("Digital Guide - Menu", ImageSpec(72, _ColorMode.RGB, 600, 110, _DimUnits.PX, [_DigitalFormat.PNG]))
    LOGO = ("Logo", ImageSpec(300, _ColorMode.RGB, 150, 150, _DimUnits.PX, [_PrintFormat.AI, _LogoFormat.EPS, _PrintFormat.PSD, _DigitalFormat.PNG]))
    NEWSLETTER_HEADER = ("Newsletter - Header", ImageSpec(72, _ColorMode.RGB, 728, 90, _DimUnits.PX, list(_DigitalFormat)))
    NEWSLETTER_SIDEBAR = ("Newsletter - Sidebar", ImageSpec(72, _ColorMode.RGB, 250, 300, _DimUnits.PX, list(_DigitalFormat)))
    NEWSLETTER_FOOTER = ("Newsletter - Footer", ImageSpec(72, _ColorMode.RGB, 728, 90, _DimUnits.PX, list(_DigitalFormat)))
    PROGRAM_QUARTER = ("Program - Quarter Page", ImageSpec(300, _ColorMode.BW, 5, 2, _DimUnits.IN, list(_PrintFormat)))
    PROGRAM_HALF = ("Program - Half Page", ImageSpec(300, _ColorMode.BW, 5, 4, _DimUnits.IN, list(_PrintFormat)))
    PROGRAM_WHOLE = ("Program - Single Page", ImageSpec(300, _ColorMode.CMYK, 5, 8, _DimUnits.IN, list(_PrintFormat)))
    PROGRAM_DOUBLE = ("Program - Two Page", ImageSpec(300, _ColorMode.CMYK, 10.5, 8, _DimUnits.IN, list(_PrintFormat)))
    WEBSITE_SIDEBAR = ("Website - Sidebar", ImageSpec(72, _ColorMode.RGB, 640, 240, _DimUnits.PX, [_DigitalFormat.PNG]))
    
    def __init__(self, label, spec):
        self.label = label
        self.spec = spec

class Level(Enum):
    INDIE = ("Indie")
    COPPER = ("Copper", AssetType.PROGRAM_QUARTER)
    SILVER = ("Silver", AssetType.PROGRAM_HALF, AssetType.NEWSLETTER_FOOTER)
    GOLD = ("Gold", AssetType.PROGRAM_WHOLE, AssetType.NEWSLETTER_SIDEBAR, AssetType.DIGITAL_MENU)
    PLATINUM = ("Platinum", AssetType.PROGRAM_DOUBLE, AssetType.NEWSLETTER_HEADER, AssetType.DIGITAL_MENU, AssetType.WEBSITE_SIDEBAR)
    SERVICE = ("Service Sponsor")
    CHARITY = ("Charity")
    
    def __init__(self, label, *assets):
        self.label = label
        self.assets = set(assets)

_BASE_ASSETS = (AssetType.LOGO, AssetType.DIGITAL_BANNER)
for level in Level:
    level.assets.update(_BASE_ASSETS)