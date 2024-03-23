# -*- coding=utf-8 -*-
r"""

"""
import io
import os
from zlib import adler32
import flask
from PIL import Image


def optimize_image(fp: str):
    filesize = os.path.getsize(fp)
    if filesize < flask.current_app.config.get('IMAGE_OPTIMIZATION_MINIMUM_SIZE', 1024 * 1024):
        return None

    with Image.open(fp) as image:
        # we don't support animated images
        if getattr(image, 'is_animated', False):
            return None

        # support for giant image commonly found in comics or mangas
        boundary = (2000, 2000)
        if image.width > 2 * image.height or image.height > image.width * 2:
            boundary = (4000, 4000)

        image.thumbnail(boundary, resample=Image.Resampling.BICUBIC)  # resize but keep aspect

        buffer = io.BytesIO()
        # WebP should be better than JPEG or PNG
        image.save(buffer, format='WEBP',
                   lossless=False, quality=75, method=3, exact=False)
        buffer.seek(0)

    stat = os.stat(fp)
    check = adler32(fp.encode('utf-8')) & 0xFFFFFFFF
    etag = f"{stat.st_mtime}-{stat.st_size}-{check}-optimized"

    return flask.send_file(buffer, "image/webp", as_attachment=False,
                           download_name="optimized.webp", conditional=False, etag=etag)
