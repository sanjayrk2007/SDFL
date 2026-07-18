import os
import tempfile
import numpy as np
from PIL import Image


def test_sanitize_rgb_image():
    from scripts.sanitize import sanitize
    img = Image.fromarray(
        np.random.randint(0, 200, (256, 256, 3), dtype=np.uint8)
    )
    out, passed = sanitize(img)
    assert isinstance(out, Image.Image)
    assert passed is True
    assert out.size == (256, 256)


def test_sanitize_grayscale_input():
    from scripts.sanitize import sanitize
    gray = Image.fromarray(
        np.random.randint(0, 200, (256, 256), dtype=np.uint8), mode="L"
    )
    out, passed = sanitize(gray)
    assert out.mode == "RGB"


def test_sanitize_exif_stripped():
    from scripts.sanitize import sanitize
    img = Image.fromarray(
        np.random.randint(0, 200, (256, 256, 3), dtype=np.uint8)
    )
    img.info = {"exif": b"fake-exif-data", "dpi": (300, 300)}
    out, _ = sanitize(img)
    assert out.info == {}


def test_phi_gate_rejects_high_inpaint():
    from scripts.sanitize import sanitize
    img = np.zeros((256, 256, 3), dtype=np.uint8)
    img[:25, :, :] = 255
    img[:, :, :] = 0
    img[0:25, 0:200] = [255, 255, 255]
    pil_img = Image.fromarray(img)
    out, passed = sanitize(pil_img)
    assert passed is False


def test_dicom_conversion():
    import pydicom
    from pydicom.dataset import Dataset, FileDataset
    from pydicom.dataelem import DataElement

    ds = Dataset()
    ds.PatientName = "Test^Patient"
    ds.Modality = "CT"
    ds.SOPClassUID = "1.2.840.10008.5.1.4.1.1.2"
    ds.SOPInstanceUID = pydicom.uid.generate_uid()
    ds.StudyInstanceUID = pydicom.uid.generate_uid()
    ds.SeriesInstanceUID = pydicom.uid.generate_uid()
    ds.Rows = 256
    ds.Columns = 256
    ds.file_meta = Dataset()
    ds.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.2"
    ds.file_meta.MediaStorageSOPInstanceUID = ds.SOPInstanceUID
    ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
    arr = np.random.randint(0, 255, (256, 256), dtype=np.uint16)
    ds.PixelData = arr.tobytes()
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 0
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"

    from pydicom.pixel_data_handlers.util import apply_voi_lut
    pixel_array = ds.pixel_array
    img = apply_voi_lut(pixel_array, ds)
    img = img.astype(np.float32)
    img = (img - img.min()) / (img.max() - img.min() + 1e-8) * 255.0
    img = img.astype(np.uint8)
    if img.ndim == 2:
        img = np.stack([img] * 3, axis=-1)
    pil_img = Image.fromarray(img, mode="RGB")

    from scripts.sanitize import sanitize
    sanitized, passed = sanitize(pil_img)
    assert isinstance(sanitized, Image.Image)

    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "test_synthetic.png")
        sanitized.save(out_path)
        assert os.path.exists(out_path)
        loaded = Image.open(out_path)
        assert loaded.size == (256, 256)
