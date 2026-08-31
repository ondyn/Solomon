"""QR code rendering for asset tag labels."""

import io

import qrcode
import qrcode.constants
from qrcode.image.svg import SvgPathImage

ERROR_CORRECTION_LEVELS = {
    "L": qrcode.constants.ERROR_CORRECT_L,
    "M": qrcode.constants.ERROR_CORRECT_M,
    "Q": qrcode.constants.ERROR_CORRECT_Q,
    "H": qrcode.constants.ERROR_CORRECT_H,
}


def build_qr_svg(data, error_correction="M", box_size=10, border=2):
    """Return an SVG document (as text) encoding `data`."""
    code = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECTION_LEVELS.get(
            str(error_correction).upper(), qrcode.constants.ERROR_CORRECT_M
        ),
        box_size=box_size,
        border=border,
        image_factory=SvgPathImage,
    )
    code.add_data(data)
    code.make(fit=True)
    buffer = io.BytesIO()
    code.make_image().save(buffer)
    return buffer.getvalue().decode("utf-8")
