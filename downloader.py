"""Command-line YouTube downloader with selectable video quality.

This module uses yt-dlp to fetch metadata for a YouTube video and allows
the user to choose a resolution between 360p and 4K before downloading.
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import Dict, Iterable, Optional

from yt_dlp import YoutubeDL

SUPPORTED_HEIGHTS = [360, 480, 720, 1080, 1440, 2160]


class DownloadError(RuntimeError):
    """Raised when a download fails."""


def fetch_video_info(url: str) -> Dict:
    """Return metadata for *url* without downloading the video."""
    with YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
        return ydl.extract_info(url, download=False)


def available_resolutions(formats: Iterable[Dict]) -> Dict[int, Dict]:
    """Return a mapping of supported heights to representative format data."""
    matches: Dict[int, Dict] = {}
    for fmt in formats:
        height = fmt.get("height")
        if not height or fmt.get("vcodec") == "none":
            # Skip audio-only entries and items without a resolution.
            continue
        if height not in SUPPORTED_HEIGHTS:
            continue
        # Prefer formats with an estimated file size so we can surface it to the user.
        current = matches.get(height)
        if not current:
            matches[height] = fmt
            continue
        if fmt.get("filesize", 0) and fmt.get("filesize", 0) > current.get("filesize", 0):
            matches[height] = fmt
    return matches


def build_format_string(height: int) -> str:
    """Return a yt-dlp format string that targets *height* when possible."""
    return (
        f"bestvideo[height={height}][ext=mp4]+bestaudio[ext=m4a]/"
        f"bestvideo[height={height}]+bestaudio/"
        f"best[height={height}]"
    )


def prompt_for_resolution(matches: Dict[int, Dict]) -> Optional[int]:
    """Prompt the user to choose a resolution from *matches* via stdin."""
    if not matches:
        return None

    print("Available download options:")
    ordered = sorted(matches.items(), key=lambda item: SUPPORTED_HEIGHTS.index(item[0]))
    for idx, (height, fmt) in enumerate(ordered, start=1):
        size_mb = None
        if fmt.get("filesize"):
            size_mb = fmt["filesize"] / (1024 * 1024)
        elif fmt.get("filesize_approx"):
            size_mb = fmt["filesize_approx"] / (1024 * 1024)
        size_text = f" (~{size_mb:.1f} MB)" if size_mb else ""
        print(f"  {idx}. {height}p{size_text}")

    while True:
        selection = input("Enter the number for the desired resolution: ").strip()
        if not selection:
            print("Please enter a selection.")
            continue
        if not selection.isdigit():
            print("Please enter a numeric selection.")
            continue
        index = int(selection)
        if not 1 <= index <= len(ordered):
            print("Selection out of range. Try again.")
            continue
        return ordered[index - 1][0]


def download_video(url: str, resolution: Optional[int], output_dir: str) -> None:
    """Download *url* at *resolution* to *output_dir* using yt-dlp."""
    ydl_opts = {
        "outtmpl": os.path.join(output_dir, "%(title)s [%(height)sp].%(ext)s"),
        "merge_output_format": "mp4",
        "quiet": False,
        "noplaylist": True,
    }
    if resolution:
        ydl_opts["format"] = build_format_string(resolution)

    with YoutubeDL(ydl_opts) as ydl:
        result = ydl.download([url])
    if result != 0:
        raise DownloadError("yt-dlp failed to download the requested video.")


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download a YouTube video with a chosen quality.")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument(
        "-r",
        "--resolution",
        type=int,
        choices=SUPPORTED_HEIGHTS,
        help="Target resolution (in p). If omitted, the script prompts with the available options.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=os.getcwd(),
        help="Directory where the downloaded file should be saved. Defaults to the current working directory.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)

    info = fetch_video_info(args.url)
    matches = available_resolutions(info.get("formats", []))

    resolution = args.resolution
    if resolution and resolution not in matches:
        print(
            f"Requested resolution {resolution}p is not available for this video. "
            "You will need to choose an available option.",
            file=sys.stderr,
        )
        resolution = None

    if not resolution:
        resolution = prompt_for_resolution(matches)
        if not resolution:
            print(
                "No supported resolutions (360p to 4K) were found for this video.",
                file=sys.stderr,
            )
            return 1

    try:
        download_video(args.url, resolution, args.output)
    except DownloadError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
