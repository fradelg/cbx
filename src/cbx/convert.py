from pathlib import Path
from tqdm import tqdm, trange
from PIL import Image
import patoolib
import logging
import tempfile


from pdf2image import convert_from_path, pdfinfo_from_path


logger = logging.getLogger(__name__)


def convert(input_path: Path, pdf_dpi: int = 300):
    cwd = input_path
    if input_path.is_file():
        cwd = input_path.parent

    all_files = list(cwd.glob("*.cbr")) + list(cwd.glob("*.pdf"))
    for cbr_path in all_files:
        if input_path.is_file() and input_path != cbr_path:
            continue

        with tempfile.TemporaryDirectory() as tmp_dir:
            convert_file(cbr_path, Path(tmp_dir), pdf_dpi)


def convert_file(cbr_path: Path, tmp_dir: Path, pdf_dpi: int):
    """Extracts the images in the temp dir and repack as webp."""
    webp_files = []
    if cbr_path.suffix == ".pdf":
        # Render the images from the PDF using poppler
        logger.info(f"Extracting pages from {cbr_path}...")
        page_count = pdfinfo_from_path(cbr_path)["Pages"]
        for first_page in trange(1, page_count + 1, 100):
            last_page = min(first_page + 100 - 1, page_count)
            images = convert_from_path(
                cbr_path,
                dpi=pdf_dpi,
                first_page=first_page,
                last_page=last_page,
            )
            for i, image in enumerate(tqdm(images)):
                webp_path = tmp_dir / f"page_{first_page + i:03d}.webp"
                image.save(webp_path, "webp")
                webp_files.append(str(webp_path))
    elif cbr_path.suffix == ".cbr":
        # Convert all the images to WebP, preserving the stem of the filename
        logger.info(f"Extracting pages from {cbr_path}...")
        patoolib.extract_archive(str(cbr_path), outdir=str(tmp_dir), interactive=False)
        jpg_paths = list(tmp_dir.glob("**/*.jp*g"))
        for im_path in tqdm(jpg_paths, desc="Converting images to WebP"):
            webp_path = tmp_dir / f"{im_path.stem}.webp"
            Image.open(im_path).save(webp_path, "webp")
            webp_files.append(str(webp_path))
    else:
        raise ValueError(cbr_path)

    # Repack the images into a CBZ file
    zip_path = cbr_path.parent / f"{cbr_path.stem}.zip"
    cbz_path = cbr_path.parent / f"{cbr_path.stem}.cbz"
    patoolib.create_archive(str(zip_path), filenames=webp_files, interactive=False)
    zip_path.rename(cbz_path)

    # Estimate the gain
    jpeg_size = cbr_path.stat().st_size
    webp_size = cbz_path.stat().st_size
    gain = (jpeg_size - webp_size) / jpeg_size
    print(f"Before: {jpeg_size}, After: {webp_size}, Compression rate: {gain}")
