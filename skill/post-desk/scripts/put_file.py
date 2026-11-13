"""Upload a local file to the presigned URL that Blotato's blotato_create_presigned_upload_url tool returns.

  put_file.py "<presignedUrl>" "<path to file>"

It sends the raw file bytes in one PUT with the file's real type (video/mp4, image/png and so on), because Blotato's
storage serves the file with whatever type the upload declared, and the platforms check it. It works on Mac and Windows,
and falls back to curl if Python cannot make a secure connection. After it prints OK, use the publicUrl from the same
tool call in mediaUrls.
"""
import mimetypes
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

common.utf8_stdout()


class _Reader:
    """Streams the file so a large video does not sit in memory."""

    def __init__(self, path):
        self.f = open(path, "rb")
        self.size = os.path.getsize(path)

    def read(self, n=-1):
        return self.f.read(n if n and n > 0 else 1024 * 1024)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    url, path = sys.argv[1], common.expand(sys.argv[2])
    if not os.path.isfile(path):
        sys.exit("File not found: %s" % path)
    ctype = TYPES.get(os.path.splitext(path)[1].lower()) or mimetypes.guess_type(path)[0] or "application/octet-stream"
    size = os.path.getsize(path)
    try:
        status = _put_python(url, path, ctype)
    except urllib.error.HTTPError as e:
        sys.exit("Upload failed: HTTP %s %s" % (e.code, e.read()[:300]))
    except (urllib.error.URLError, OSError) as e:
        status = _put_curl(url, path, ctype, e)
    if 200 <= status < 300:
        print("OK  %s (%.1f MB, %s) uploaded" % (os.path.basename(path), size / 1e6, ctype))
    else:
        sys.exit("Upload failed: HTTP %s" % status)


TYPES = {".mp4": "video/mp4", ".mov": "video/quicktime", ".png": "image/png", ".jpg": "image/jpeg",
         ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp", ".pdf": "application/pdf"}


def _put_python(url, path, ctype):
    body = _Reader(path)
    req = urllib.request.Request(url, data=body, method="PUT")
    req.add_header("Content-Length", str(body.size))
    req.add_header("Content-Type", ctype)
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return r.status
    finally:
        body.f.close()


def _put_curl(url, path, ctype, first_error):
    # Some Mac Python installs have no SSL certificates. curl ships with macOS and Windows 10+.
    curl = shutil.which("curl.exe") or shutil.which("curl")
    if not curl:
        sys.exit("Upload failed: %s" % first_error)
    out = subprocess.run([curl, "-sS", "-o", os.devnull, "-w", "%{http_code}", "-X", "PUT",
                          "-H", "Content-Type: " + ctype, "--data-binary", "@" + path, url],
                         capture_output=True, text=True, timeout=900)
    try:
        return int(out.stdout.strip() or 0)
    except ValueError:
        return 0


if __name__ == "__main__":
    main()
