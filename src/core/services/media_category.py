IMAGE_EXTENSIONS = {
    "jpg", "jpeg", "png", "gif", "bmp", "webp",
    "tiff", "tif", "ico", "heic", "heif", "svg"
}

IMAGES_TAG_NAME = "images"
VIDEOS_TAG_NAME = "videos"

SYSTEM_TAG_NAMES = {
    IMAGES_TAG_NAME,
    VIDEOS_TAG_NAME
}


def classify_extension(extension: str) -> str:
    """
    Classifies a file extension as "image" or "video".

    Anything not recognized as an image is treated as a video,
    since SecureMediaVault only supports these two categories
    and video container formats can be uncommon or proprietary.
    """

    ext = (extension or "").lower().lstrip(".")

    if ext in IMAGE_EXTENSIONS:
        return "image"

    return "video"


def category_to_tag_name(category: str) -> str:

    if category == "image":
        return IMAGES_TAG_NAME

    return VIDEOS_TAG_NAME