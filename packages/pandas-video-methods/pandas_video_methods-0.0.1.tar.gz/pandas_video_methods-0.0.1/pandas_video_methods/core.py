import base64
import inspect
from functools import partialmethod
from io import BytesIO
from math import prod

import fsspec
import numpy as np
import pandas as pd
import pyarrow as pa
from pandas._typing import Dtype
from pandas.api.extensions import ExtensionArray
from torchcodec.decoders import VideoDecoder

from . import dask
from . import huggingface


dask.init()
huggingface.init()
# TODO: initial list, we should check the compatibility of other formats
_VIDEO_COMPRESSION_FORMATS = [
    ".mkv",
    ".mp4",
    ".avi",
    ".mpeg",
    ".mov",
]


def _video_to_bytes(video: "VideoDecoder") -> bytes:
    """Convert a PIL Video object to bytes using native compression if possible, otherwise use PNG/TIFF compression."""
    buffer = BytesIO()
    # TODO
    return buffer.getvalue()


def _encode_video_decoder(video: "VideoDecoder") -> dict:
    # TODO
    raise NotImplementedError()


def _decode_video_decoder(encoded_video: dict) -> "VideoDecoder":
    # TODO
    raise NotImplementedError()


class VideoArray(ExtensionArray):
    _pa_type = pa.struct({"bytes": pa.binary(), "path": pa.string()})

    def __init__(self, data: np.ndarray) -> None:
        self.data = data

    @property
    def dtype(self):
        dtype = pd.core.dtypes.dtypes.NumpyEADtype("object")
        dtype.construct_array_type = lambda: VideoArray
        return dtype

    @property
    def nbytes(self):
        return sum(prod(video.size) * getattr(video, "bits", 8) for video in self)

    @property
    def feature(self):
        return {"_type": "Video"}

    @classmethod
    def _from_sequence_of_strings(cls, strings, *, dtype: Dtype | None = None, copy: bool = False):
        a = np.empty(len(strings), dtype=object)
        # TODO
        return cls(a)

    @classmethod
    def _from_sequence_of_videos(cls, videos, *, dtype: Dtype | None = None, copy: bool = False):
        a = np.empty(len(videos), dtype=object)
        a[:] = videos
        return cls(a)

    @classmethod
    def _from_sequence_of_encoded_videos(cls, encoded_videos, *, dtype: Dtype | None = None, copy: bool = False):
        a = np.empty(len(encoded_videos), dtype=object)
        a[:] = [_decode_video_decoder(encoded_video) if encoded_video is not None else None for encoded_video in encoded_videos]
        return cls(a)

    @classmethod
    def _from_sequence(cls, scalars, *, dtype: Dtype | None = None, copy: bool = False):
        if len(scalars) == 0:
            return cls(np.array([], dtype=object))
        if isinstance(scalars[0], str):
            return cls._from_sequence_of_strings(scalars, dtype=dtype, copy=copy)
        if isinstance(scalars[0], dict) and set(scalars[0]) == {"bytes", "path"}:
            return cls._from_sequence_of_encoded_videos(scalars, dtype=dtype, copy=copy)
        elif isinstance(scalars[0], VideoDecoder):
            return cls._from_sequence_of_videos(scalars, dtype=dtype, copy=copy)
        raise TypeError(type(scalars[0].__name__))

    def __eq__(self, value: object) -> bool:
        return self.data == value.data

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, item) -> "VideoDecoder | VideoArray":
        if isinstance(item, int):
            return self.data[item]
        return type(self)(self.data[item])

    def copy(self) -> "VideoArray":
        return VideoArray(self.data.copy())

    def __arrow_array__(self, type=None):
        return pa.array([_encode_video_decoder(video) if video is not None else None for video in self.data], type=self._pa_type)

    def _formatter(self, boxed=False):
        # TODO
        raise NotImplementedError()
    
    @classmethod
    def _empty(cls, shape, dtype=None):
        return cls(np.array([None] * shape, dtype=object))
    
    @classmethod
    def _concat_same_type(cls, to_concat):
        return VideoArray._from_sequence([video for array in to_concat for video in array])
    
    def take(self, indices, *, allow_fill=False, fill_value=None):
        from pandas.api.extensions import take

        if allow_fill and fill_value is None:
            fill_value = self.dtype.na_value

        result = take(self.data, indices, fill_value=fill_value, allow_fill=allow_fill)
        return self._from_sequence(result, dtype=self.dtype)


VideoArray._array_empty = VideoArray._empty(0)
# TODO
_dummy_video = None
VideoArray._array_nonempty = VideoArray._from_sequence_of_videos([_dummy_video] * 2)


class TorchCodecVideoDecoderMethods:
    _meta = pd.Series(VideoArray._array_empty)
    _meta_nonempty = pd.Series(VideoArray._array_nonempty)

    def __init__(self, data: pd.Series) -> None:
        self.data = data
    
    @classmethod
    def pil_method(cls, data, *, func, args, kwargs):
        return func(cls(data), *args, **kwargs)

    @dask.wrap_method
    def open(self):
        return pd.Series(VideoArray._from_sequence_of_strings(self.data))

    @dask.wrap_method
    def enable(self):
        return pd.Series(VideoArray._from_sequence(self.data))

    @dask.wrap_method
    def _apply(self, *args, _func, **kwargs):
        if not isinstance(self.data.array, VideoArray):
            raise Exception("You need to enable video methods first, using for example: df['video'] = df['video'].video_decoder.enable()")
        out = [_func(x, *args, **kwargs) for x in self.data]
        try:
            return pd.Series(type(self.data.array)._from_sequence(out))
        except TypeError:
            return pd.Series(out)

    @staticmethod
    def html_formatter(x):
        # TODO
        raise NotImplementedError()

for _name, _func in inspect.getmembers(VideoDecoder, predicate=inspect.isfunction):
    if not _name.startswith("_") and _name not in ["open", "save", "load"]:
        setattr(TorchCodecVideoDecoderMethods, _name, partialmethod(TorchCodecVideoDecoderMethods._apply, _func=_func))


_sts = pd.Series.to_string
def _new_sts(self, *args, **kwargs):
    return _sts(self, *args, **kwargs) + (", video methods enabled" if isinstance(self.array, VideoArray) else "")
    
pd.Series.to_string = _new_sts
