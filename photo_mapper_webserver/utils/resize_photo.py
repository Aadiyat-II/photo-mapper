import io

from django.core.files.uploadedfile import UploadedFile
from PIL import Image, ImageOps

def resize_image(image_file: UploadedFile):
    """
    Resize image in memory and return stream to resized image
    """
    img = Image.open(image_file)
    img= ImageOps.exif_transpose(img)

    img.thumbnail((1920, 1920), Image.Resampling.LANCZOS)

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=80)
    buffer.seek(0)

    from django.core.files.base import ContentFile

    return ContentFile(buffer.read(), name=image_file.name)