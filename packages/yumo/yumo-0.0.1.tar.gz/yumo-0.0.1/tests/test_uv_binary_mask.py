import os
import platform

import numpy as np
import pytest
from PIL import Image, ImageChops

from yumo.geometry_utils import unwrap_uv, uv_mask
from yumo.utils import load_mesh

pytestmark = pytest.mark.skipif(
    platform.system() != "Darwin",
    reason="Golden standards are only available on macOS (for now, where this is mainly developed).",
)


def test_uv_binary_mask(test_data, tmp_path):
    """
    End-to-end test of UV binary mask generation.

    Steps:
    1. Load a mesh model from test_data/sample.STL
    2. Perform UV unwrapping via xatlas
    3. Generate a binary UV mask
    4. Save mask image for debugging
    5. Compare against golden reference mask image pixel-by-pixel
    """

    # -- 1. Load mesh (vertices, faces) --
    mesh_path = os.path.join(test_data, "sample.STL")

    vertices, faces = load_mesh(mesh_path)

    # -- 2. Unwrap UVs --
    (
        param_corner,
        H,
        W,
        vmapping,
        faces_unwrapped,
        uvs,
        vertices_unwrapped,
    ) = unwrap_uv(vertices, faces, brute_force=True)  # set to True for deterministic results

    # -- 3. Generate UV binary mask --
    mask = uv_mask(uvs, faces_unwrapped, W, H)

    # Convert to an image for comparison
    mask_img = Image.fromarray((mask * 255).astype(np.uint8))
    out_file = tmp_path / "uv_mask.png"
    mask_img.save(out_file)

    # -- 4. Compare with golden reference --
    gt_file = os.path.join(test_data, "uv_mask_gt.png")
    gt_img = Image.open(gt_file).convert("L")

    assert mask_img.size == gt_img.size, "UV mask image size mismatch"

    diff = ImageChops.difference(mask_img, gt_img)
    if diff.getbbox() is not None:
        diff_file = tmp_path / "uv_mask_diff.png"
        diff.save(diff_file)
        raise AssertionError(
            f"UV mask result does not match golden reference.\n"
            f"Generated: {out_file}\n"
            f"Diff: {diff_file}\n"
            f"Expected: {gt_file}"
        )
