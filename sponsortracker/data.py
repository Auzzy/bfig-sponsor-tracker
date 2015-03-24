from collections.abc import Iterable
from enum import Enum

from flask.ext.user import roles_required

class RoleType(Enum):
    DT_READ = "deal-read"
    DT_WRITE = "deal-write"
    AT_READ = "asset-read"
    AT_WRITE = "asset-write"
    
    def __init__(self, type):
        self.type = type

    @staticmethod
    def types(roles):
        types = []
        for role in roles:
            if isinstance(role, Iterable):
                types.append(RoleType.types(role))
            elif isinstance(role, RoleType):
                types.append(role.type)
        return types
        
class UserType(Enum):
    ADMIN = ("admin", RoleType.DT_READ, RoleType.DT_WRITE, RoleType.AT_READ, RoleType.AT_WRITE)
    COORD = ("coord", RoleType.AT_READ, RoleType.AT_WRITE)
    EXEC = ("exec", RoleType.DT_READ, RoleType.DT_WRITE)
    MARKETING = ("marketing", RoleType.AT_READ)
    SALES = ("sales", RoleType.DT_READ, RoleType.DT_WRITE)
    
    def __init__(self, type, *roles):
        self.type = type
        self.roles = roles
    
    @staticmethod
    def from_type(type):
        for user_type in UserType:
            if type == user_type.type:
                return user_type
    
class _Format(Enum):
    def __init__(self, format, ext):
        self.format = format
        self.ext = ext

class _PrintFormat(_Format):
    PDF = ("PDF", "pdf")
    PSD = ("PSD", "psd")
    
    @classmethod
    def preferred(self):
        return _PrintFormat.PSD

class _DigitalFormat(_Format):
    JPG = ("JPEG", "jpg")
    PNG = ("PNG", "png")
    GIF = ("GIF", "gif")
    
    @classmethod
    def preferred(self):
        return _DigitalFormat.PNG

class _LogoFormat(_Format):
    EPS = ("EPS", "eps")
    
    @classmethod
    def preferred(self):
        return _LogoFormat.EPS

ASSET_FORMATS_EXT = [fmt.ext for fmt in list(_PrintFormat) + list(_DigitalFormat) + list(_LogoFormat)]

class _ColorMode(Enum):
    SRGB = "srgb"
    RGB = "rgb"
    CMYK = "cmyk"
    BW = "gray"

class _DimUnits(Enum):
    IN = "in"
    PX = "px"

class ImageSpec:
    def __init__(self, dpi, width, height, unit, color_modes, formats, transparent=None):
        self.dpi = dpi
        self.width = width
        self.height = height
        self.unit = unit
        self.color_modes = color_modes
        self.color_mode_names = [color_mode.value for color_mode in color_modes]
        self.formats = formats
        self.format_names = [format.format for format in formats]
        self.transparent = transparent
    
    def dimensions_as_str(self):
        return "{width}{unit}x{height}{unit}".format(width=self.width, height=self.height, unit=self.unit)
        
    def formats_as_str(self):
        return '/'.join(self.format_names)
        
    def color_modes_as_str(self):
        return '/'.join([mode.value for mode in self.color_modes])
        
    def dpi_as_str(self):
        return "{0}".format(self.dpi)
    
    def __str__(self):
        return "; ".join([
            "Dimensions: {0}".format(self.dimensions_as_str()),
            "Formats: {0}".format(self.formats_as_str()),
            "Color Modes: {0}".format(self.color_modes_as_str()),
            "{0} dpi".format(self.dpi_as_str())
        ])

class AssetLabel:
    def __init__(self, what, where=None):
        self.what = what
        self.where = where
    
    def __str__(self):
        return "{0} - {1}".format(self.where, self.what) if self.where else self.what
    
    def __lt__(self, other):
        return str(self) < str(other)

# Each value should also contain details about each asset's required specs
class AssetType(Enum):
    DIGITAL_BANNER = (AssetLabel("Banner Ad", "Digital Guide"), ImageSpec(72, 640, 240, _DimUnits.PX, [_ColorMode.SRGB, _ColorMode.RGB], [_DigitalFormat.PNG]))
    DIGITAL_MENU = (AssetLabel("Menu Ad", "Digital Guide"), ImageSpec(72, 600, 110, _DimUnits.PX, [_ColorMode.SRGB, _ColorMode.RGB], [_DigitalFormat.PNG]))
    LOGO = (AssetLabel("Logo"), ImageSpec(300, 150, 150, _DimUnits.PX, [_ColorMode.SRGB, _ColorMode.RGB], [_DigitalFormat.PNG, _LogoFormat.EPS, _PrintFormat.PSD], True))
    NEWSLETTER_HEADER = (AssetLabel("Header Ad", "Newsletter"), ImageSpec(72, 728, 90, _DimUnits.PX, [_ColorMode.SRGB, _ColorMode.RGB], list(_DigitalFormat)))
    NEWSLETTER_SIDEBAR = (AssetLabel("Sidebar Ad", "Newsletter"), ImageSpec(72, 250, 300, _DimUnits.PX,  [_ColorMode.SRGB, _ColorMode.RGB],list(_DigitalFormat)))
    NEWSLETTER_FOOTER = (AssetLabel("Footer Ad", "Newsletter"), ImageSpec(72, 728, 90, _DimUnits.PX, [_ColorMode.SRGB, _ColorMode.RGB], list(_DigitalFormat)))
    PROGRAM_QUARTER = (AssetLabel("Quarter Page Ad", "Program"), ImageSpec(300, 5, 2, _DimUnits.IN, [_ColorMode.BW], list(_PrintFormat)))
    PROGRAM_HALF = (AssetLabel("Half Page Ad", "Program"), ImageSpec(300, 5, 4, _DimUnits.IN, [_ColorMode.BW], list(_PrintFormat)))
    PROGRAM_WHOLE = (AssetLabel("Single Page Ad", "Program"), ImageSpec(300, 5, 8, _DimUnits.IN, [_ColorMode.CMYK], list(_PrintFormat)))
    PROGRAM_DOUBLE = (AssetLabel("Two Page Ad", "Program"), ImageSpec(300, 10.5, 8, _DimUnits.IN, [_ColorMode.CMYK], list(_PrintFormat)))
    WEBSITE_SIDEBAR = (AssetLabel("Sidebar Ad", "Website"), ImageSpec(72, 640, 240, _DimUnits.PX, [_ColorMode.SRGB, _ColorMode.RGB], [_DigitalFormat.PNG]))
    
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