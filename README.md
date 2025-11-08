# YouTube Downloader

A small command-line utility for downloading YouTube videos with your chosen
resolution, ranging from 360p up to 4K (2160p). The downloader is powered by
[yt-dlp](https://github.com/yt-dlp/yt-dlp) and will merge separate audio/video
streams automatically when needed.

## Prerequisites

- Python 3.9 or newer
- [FFmpeg](https://ffmpeg.org/) available on your `PATH` (required for merging
  high-resolution video and audio tracks)

Install the Python dependency:

```bash
pip install -r requirements.txt
```

## Usage

```bash
python downloader.py <youtube-url> [--resolution {360,480,720,1080,1440,2160}] [--output /path/to/save]
```

- If you omit `--resolution`, the script inspects the video and presents an
  interactive list of the available qualities between 360p and 4K.
- When the requested quality is not available, you will be asked to choose
  another option.
- Downloads are saved in the specified output directory (default: current
  working directory) and named using the video title and selected resolution.

### Examples

Download a video after interactively choosing the quality:

```bash
python downloader.py https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

Download the same video immediately at 1080p into `~/Videos`:

```bash
python downloader.py https://www.youtube.com/watch?v=dQw4w9WgXcQ --resolution 1080 --output ~/Videos
```

## Notes

- Some videos may not offer every resolution. The script filters the available
  options to those between 360p and 2160p.
- 4K downloads often require more disk space and bandwidth; the script prints
  approximate file sizes when the information is available.
