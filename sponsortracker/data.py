from enum import Enum

class _Format(Enum):
    def __init__(self, name, ext):
        self.format = format
        self.ext = ext

class _PrintFormat(_Format):
    PDF = ("PDF", "pdf")
    PSD = ("PSD", "psd")

class _DigitalFormat(_Format):
    JPG = ("JPEG", "jpg")
    PNG = ("PNG", "png")
    GIF = ("GIF", "gif")

class _LogoFormat(_Format):
    EPS = ("EPS", "eps")

ASSET_FORMATS_EXT = [fmt.ext for fmt in list(_PrintFormat) + list(_DigitalFormat) + list(_LogoFormat)]

class _ColorMode(Enum):
    RGB = "rgb"
    SRGB = "srgb"
    CMYK = "cmyk"
    BW = "gray"

class _DimUnits(Enum):
    IN = "in"
    PX = "px"

class ImageSpec:
    def __init__(self, dpi, width, height, unit, transparent, color_modes, formats, transparent=None):
        self.dpi = dpi
        self.width = width
        self.height = height
        self.unit = unit
        self.color_modes = color_modes
        self.formats = formats
        self.transparent = transparent
    
    def dimensions_as_str(self):
        return "{width}{unit}x{height}{unit}".format(width=self.width, height=self.height, unit=self.unit)
        
    def formats_as_str(self):
        return '/'.join([format.format for format in self.formats])
        
    def color_modes_as_str(self):
        return '/'.join([mode.value for mode in self.color_modes])
        
    def dpi_as_str(self):
        return "{0}".format(self.dpi)
    
    def __str__(self):
        dimensions_str = "Dimensions: {0}".format(self.dimensions_as_str())
        formats_str = "Formats: {0}".format(self.formats_as_str())
        color_modes_str = "Color Modes: {0}".format(self.color_mode_as_str())
        dpi_str = "{0} dpi".format(self.dpi_as_str())
        return "; ".join([
            "Dimensions: " self.dimensions_as_str(),
            self.formats_as_str(),
            self.color_mode_as_str(),
            self.dpi_as_str()
        ])

# Each value should also contain details about each asset's required specs
class AssetType(Enum):
    DIGITAL_BANNER = ("Digital Guide - Banner", ImageSpec(72, 640, 240, _DimUnits.PX, [_ColorMode.RGB, _ColorMode.SRGB], [_DigitalFormat.PNG]))
    DIGITAL_MENU = ("Digital Guide - Menu", ImageSpec(72, 600, 110, _DimUnits.PX, [_ColorMode.RGB, _ColorMode.SRGB], [_DigitalFormat.PNG]))
    LOGO = ("Logo", ImageSpec(300, 150, 150, _DimUnits.PX, [_ColorMode.RGB, _ColorMode.SRGB], [_LogoFormat.EPS, _PrintFormat.PSD, _DigitalFormat.PNG], True))
    NEWSLETTER_HEADER = ("Newsletter - Header", ImageSpec(72, 728, 90, _DimUnits.PX, [_ColorMode.RGB, _ColorMode.SRGB], list(_DigitalFormat)))
    NEWSLETTER_SIDEBAR = ("Newsletter - Sidebar", ImageSpec(72, 250, 300, _DimUnits.PX,  [_ColorMode.RGB, _ColorMode.SRGB],list(_DigitalFormat)))
    NEWSLETTER_FOOTER = ("Newsletter - Footer", ImageSpec(72, 728, 90, _DimUnits.PX, [_ColorMode.RGB, _ColorMode.SRGB], list(_DigitalFormat)))
    PROGRAM_QUARTER = ("Program - Quarter Page", ImageSpec(300, 5, 2, _DimUnits.IN, [_ColorMode.BW], list(_PrintFormat)))
    PROGRAM_HALF = ("Program - Half Page", ImageSpec(300, 5, 4, _DimUnits.IN, [_ColorMode.BW], list(_PrintFormat)))
    PROGRAM_WHOLE = ("Program - Single Page", ImageSpec(300, 5, 8, _DimUnits.IN, [_ColorMode.CMYK], list(_PrintFormat)))
    PROGRAM_DOUBLE = ("Program - Two Page", ImageSpec(300, 10.5, 8, _DimUnits.IN, [_ColorMode.CMYK], list(_PrintFormat)))
    WEBSITE_SIDEBAR = ("Website - Sidebar", ImageSpec(72, 640, 240, _DimUnits.PX, [_ColorMode.RGB, _ColorMode.SRGB], [_DigitalFormat.PNG]))
    
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