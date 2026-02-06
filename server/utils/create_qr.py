import qrcode

from server.utils.paths import STATIC_DIR


def create_qr(country: str) -> None:
    """
    国名を QR コード化して保存する
    """
    if country not in ("JAPAN", "UNITED STATES OF AMERICA"):
        raise ValueError(f"Unsupported content: {country}")

    STATIC_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"{country.replace(' ', '_').lower()}.png"
    imgdir = STATIC_DIR / "imgs"
    imgdir.mkdir(exist_ok=True)
    filepath = imgdir / filename

    img = qrcode.make(country)
    with filepath.open("wb") as f:
        img.save(f)
