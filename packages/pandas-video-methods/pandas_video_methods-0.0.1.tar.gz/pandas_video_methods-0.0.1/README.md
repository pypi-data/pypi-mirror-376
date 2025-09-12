# Pandas Video Methods

Video methods for pandas dataframes using TorchCodec.

Features:

* Use `torchcodec.decoders.VideoDecoder` objects in pandas dataframes
* Call `torchcodec.decoders.VideoDecoder` methods on a column, for example:
  * TODO
* Save dataframes with `torchcodec.decoders.VideoDecoder` objects to Parquet
* Process videos in parallel with Dask
* Manipulate video datasets from Hugging Face

## Installation

```pip
pip install pandas-video-methods
```

## Usage

You can open videos as `torchcodec.decoders.VideoDecoder` objects using the `.open()` method.

Once the videos are opened, you can call any [VideoDecoder](https://docs.pytorch.org/torchcodec/stable/generated/torchcodec.decoders.VideoDecoder.html):

```python
TODO
```

Here is how to enable video methods for `VideoDecoders` created manually:

```python
TODO
```

## Save

You can save a dataset of `torchcodec.decoders.VideoDecoder` to Parquet:

```python
# Save
df = pd.DataFrame({"file_path": ["path/to/video.mp4"]})
df["video"] = df["file_path"].video_decoder.open()
df.to_parquet("data.parquet")

# Later
df = pd.read_parquet("data.parquet")
df["video"] = df["video"].video_decoder.enable()
```

This doesn't just save the paths to the video files, but the actual videos themselves !

Under the hood it saves dictionaries of `{"bytes": <bytes of the video file>, "path": <path or name of the video file>}`.
The videos are saved as bytes using their video encoding by default. Anyone can load the Parquet data even without `pandas-video-methods` since it doesn't rely on extension types.

Note: if you created the `torchcodec.decoders.VideoDecoder` manually, don't forget to enable the video methods to enable saving to Parquet.

## Run in parallel

Dask DataFrame parallelizes pandas to handle large datasets. It enables faster local processing with multiprocessing as well as distributed large scale processing. Dask mimics the pandas API:

```python
import dask.dataframe as dd
from distributed import Client
from pandas_video_methods import TorchCodecVideoDecoderMethods

dd.extensions.register_series_accessor("video_decoder")(TorchCodecVideoDecoderMethods)

if __name__ == "__main__":
    client = Client()
    df = dd.read_csv("path/to/large/dataset.csv")
    df = df.repartition(npartitions=1000)  # divide the processing in 1000 jobs
    df["video"] = df["file_path"].video_decoder.open()
    # TODO
    df.to_parquet("data_folder")
```

## Hugging Face support

Most video datasets in Parquet format on Hugging Face are compatible with `pandas-video-methods`. For example you can load the [TODO](https://huggingface.co/datasets/TODO):

```python
df = pd.read_parquet(TODO)
df["video"] = df["video"].video_decoder.enable()
```

Datasets created with `pandas-video-methods` and saved to Parquet are also compatible with the [Dataset Viewer](https://huggingface.co/docs/hub/en/datasets-viewer) on Hugging Face and the [datasets](https://github.com/huggingface/datasets) library:

```python
# TODO
df.to_parquet("hf://datasets/username/dataset_name/train.parquet")
```

## Display in Notebooks

You can display a pandas dataframe of videos in a Jupyter Notebook or on Google Colab in HTML:

```python
from IPython.display import HTML
HTML(df.head().to_html(escape=False, formatters={"video": df.video.video_decoder.html_formatter}))
```

TODO
