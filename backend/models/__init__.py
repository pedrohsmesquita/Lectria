"""
SQLAlchemy models package
"""
from .user_auth import UserAuth
from .user_profiles import UserProfiles
from .books import Books
from .videos import Videos
from .chapters import Chapters
from .sections import Sections
from .section_assets import SectionAssets
from .transcriptions import Transcription
from .slides import Slide
from .global_references import GlobalReferences

__all__ = [
    "UserAuth",
    "UserProfiles",
    "Books",
    "Videos",
    "Chapters",
    "Sections",
    "SectionAssets",
    "Transcription",
    "Slide",
    "GlobalReferences",
]
