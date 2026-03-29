"""
AI Photo Dedup - Smart Duplicate Photo Cleaner

A tool that uses perceptual hashing and machine learning to detect
and remove duplicate photos from your collection.
"""

__version__ = "1.0.0"
__author__ = "wmtcool"
__email__ = "wmt008@gmail.com"

from photo_dedup.scanner import PhotoScanner
from photo_dedup.deduplicator import Deduplicator
from photo_dedup.reporter import Reporter

__all__ = ["PhotoScanner", "Deduplicator", "Reporter"]
