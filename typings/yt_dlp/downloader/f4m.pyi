"""
This type stub file was generated by pyright.
"""

import io
from .fragment import FragmentFD

class DataTruncatedError(Exception):
    ...


class FlvReader(io.BytesIO):
    """
    Reader for Flv files
    The file format is documented in https://www.adobe.com/devnet/f4v.html
    """
    def read_bytes(self, n): # -> bytes:
        ...
    
    def read_unsigned_long_long(self): # -> Any:
        ...
    
    def read_unsigned_int(self): # -> Any:
        ...
    
    def read_unsigned_char(self): # -> Any:
        ...
    
    def read_string(self): # -> bytes:
        ...
    
    def read_box_info(self): # -> tuple[Any, bytes, bytes]:
        """
        Read a box and return the info as a tuple: (box_size, box_type, box_data)
        """
        ...
    
    def read_asrt(self): # -> dict[str, list[Unknown]]:
        ...
    
    def read_afrt(self): # -> dict[str, list[Unknown]]:
        ...
    
    def read_abst(self): # -> dict[str, Any | list[Unknown]]:
        ...
    
    def read_bootstrap_info(self): # -> dict[str, Any | list[Unknown]]:
        ...
    


def read_bootstrap_info(bootstrap_bytes): # -> dict[str, Any | list[Unknown]]:
    ...

def build_fragments_list(boot_info): # -> list[Unknown]:
    """ Return a list of (segment, fragment) for each fragment in the video """
    ...

def write_unsigned_int(stream, val): # -> None:
    ...

def write_unsigned_int_24(stream, val): # -> None:
    ...

def write_flv_header(stream): # -> None:
    """Writes the FLV header to stream"""
    ...

def write_metadata_tag(stream, metadata): # -> None:
    """Writes optional metadata tag to stream"""
    ...

def remove_encrypted_media(media): # -> list[Unknown]:
    ...

def get_base_url(manifest): # -> None:
    ...

class F4mFD(FragmentFD):
    """
    A downloader for f4m manifests or AdobeHDS.
    """
    def real_download(self, filename, info_dict):
        ...
    


