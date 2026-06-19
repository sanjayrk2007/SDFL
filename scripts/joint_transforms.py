"""
SDFL — Joint image/mask augmentation pipeline
Owner: Sameer (Step 1b)

Built with torchvision (functional API), not albumentations, so the same
random params drawn for the image are reused verbatim on the mask.

Rule enforced here:
    Spatial transforms (flip, rotate, resized-crop, elastic) -> image AND mask
    Photometric transforms (color jitter, normalize)         -> image ONLY

Augmentation is applied ONLY for the "train" split. Val/test get a simple
deterministic resize+normalize (no randomness).
"""

import sys
import os
import random

import torch
import torchvision.transforms.v2.functional as F
from torchvision.transforms import InterpolationMode

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg


class JointTransform:
    """Applies the exact augmentation order from config.AUGMENTATION_ORDER
    to an (image, mask) pair, keeping spatial transforms synced and
    restricting photometric transforms to the image.

    image: PIL.Image or tensor, RGB
    mask:  PIL.Image or tensor, single-channel (L mode)
    """

    def __init__(self, params=None, train: bool = True):
        self.p = params or cfg.AUGMENTATION_PARAMS
        self.train = train

    def __call__(self, image, mask):
        image = F.to_image(image)
        mask = F.to_image(mask)
        image = F.to_dtype(image, torch.float32, scale=True)
        mask = F.to_dtype(mask, torch.float32, scale=True)

        if self.train:
            image, mask = self._apply_train(image, mask)
        else:
            image, mask = self._apply_eval(image, mask)

        return image, mask

    # ------------------------------------------------------------------
    # Train: full augmentation pipeline, order matches config exactly
    # ------------------------------------------------------------------
    def _apply_train(self, image, mask):
        p = self.p

        # 1. RandomHorizontalFlip — same coin flip for image + mask
        if random.random() < p["random_horizontal_flip"]["p"]:
            image = F.horizontal_flip(image)
            mask = F.horizontal_flip(mask)

        # 2. RandomVerticalFlip
        if random.random() < p["random_vertical_flip"]["p"]:
            image = F.vertical_flip(image)
            mask = F.vertical_flip(mask)

        # 3. RandomRotation — same angle for both, mask uses NEAREST
        #    so we never invent fractional/blended mask values
        deg = p["random_rotation"]["degrees"]
        angle = random.uniform(-deg, deg)
        image = F.rotate(image, angle, interpolation=InterpolationMode.BILINEAR)
        mask = F.rotate(mask, angle, interpolation=InterpolationMode.NEAREST)

        # 4. ColorJitter — IMAGE ONLY
        cj = p["color_jitter"]
        image = self._color_jitter(image, **cj)

        # 5. RandomResizedCrop — same crop box + resize for image & mask
        size = p["random_resized_crop"]["size"]
        scale = p["random_resized_crop"]["scale"]
        i, j, h, w = self._get_resized_crop_params(image, scale)
        image = F.resized_crop(image, i, j, h, w, [size, size],
                                interpolation=InterpolationMode.BILINEAR)
        mask = F.resized_crop(mask, i, j, h, w, [size, size],
                               interpolation=InterpolationMode.NEAREST)

        # 6. ElasticTransform — same displacement field for image & mask
        alpha = p["elastic_transform"]["alpha"]
        sigma = p["elastic_transform"]["sigma"]
        image, mask = self._elastic_transform(image, mask, alpha, sigma)

        # 7. Normalize — IMAGE ONLY. Mask stays a binary/float [0,1] target.
        norm = p["normalize"]
        image = F.normalize(image, mean=norm["mean"], std=norm["std"])

        return image, mask

    # ------------------------------------------------------------------
    # Eval (val/test): deterministic resize only, no augmentation
    # ------------------------------------------------------------------
    def _apply_eval(self, image, mask):
        size = cfg.IMG_SIZE
        image = F.resize(image, [size, size], interpolation=InterpolationMode.BILINEAR)
        mask = F.resize(mask, [size, size], interpolation=InterpolationMode.NEAREST)
        norm = self.p["normalize"]
        image = F.normalize(image, mean=norm["mean"], std=norm["std"])
        return image, mask

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _color_jitter(image, brightness, contrast, saturation):
        b = random.uniform(max(0, 1 - brightness), 1 + brightness)
        c = random.uniform(max(0, 1 - contrast), 1 + contrast)
        s = random.uniform(max(0, 1 - saturation), 1 + saturation)
        # apply in random order, matching torchvision's ColorJitter behavior
        ops = [
            lambda im: F.adjust_brightness(im, b),
            lambda im: F.adjust_contrast(im, c),
            lambda im: F.adjust_saturation(im, s),
        ]
        random.shuffle(ops)
        for op in ops:
            image = op(image)
        return image

    @staticmethod
    def _get_resized_crop_params(image, scale):
        height, width = image.shape[-2], image.shape[-1]
        area = height * width
        target_area = random.uniform(scale[0], scale[1]) * area
        aspect_ratio = random.uniform(3 / 4, 4 / 3)

        w = int(round((target_area * aspect_ratio) ** 0.5))
        h = int(round((target_area / aspect_ratio) ** 0.5))
        w = min(w, width)
        h = min(h, height)

        i = random.randint(0, max(0, height - h))
        j = random.randint(0, max(0, width - w))
        return i, j, h, w

    @staticmethod
    def _elastic_transform(image, mask, alpha, sigma):
        """Same random displacement field applied to image (bilinear) and
        mask (nearest), so warped mask edges stay binary, not blended."""
        from torchvision.transforms import ElasticTransform as _ET

        h, w = image.shape[-2], image.shape[-1]
        displacement = _ET.get_params([alpha, alpha], [sigma, sigma], [h, w])

        image = F.elastic_transform(image, displacement,
                                     interpolation=InterpolationMode.BILINEAR)
        mask = F.elastic_transform(mask, displacement,
                                    interpolation=InterpolationMode.NEAREST)
        return image, mask
