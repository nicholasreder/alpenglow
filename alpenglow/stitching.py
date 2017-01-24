from skimage import transform
import numpy as np
from skimage.feature import register_translation

def stitch(image1, image2):
    """
    stitches two images together
    
    Parameters
    ----------
    image1 = first image in sequence (2D numpy array)
    image2 = second image in sequence (2D numpy array)
    
    Returns
    -------
    Stitched 2D numpy array
    """
    
    cols1 = image1.shape[1]
    cols2 = image2.shape[1]
    rows1 = image1.shape[0]
    rows2 = image2.shape[0]
    shift, error, diffphase = register_translation(image1[:rows1//2, int(cols1//2-0.1*cols1):int(cols1//2+0.1*cols1)],
                                                   image2[rows2//2:, int(cols2//2-0.1*cols2):int(cols2//2+0.1*cols2)])

    overlap=rows1//2+shift[0]
    overlap

    offset = transform.SimilarityTransform(translation=(overlap, -shift[1]))
    no_offset = transform.SimilarityTransform(translation=(0, 0))

    image1_transformed = transform.warp(image1, inverse_map=offset, output_shape=((2*rows1-overlap), (2*cols1-cols1-shift[1])))
    image2_transformed = transform.warp(image2, inverse_map=no_offset, output_shape=((2*rows2-overlap), (2*cols2-cols2-shift[1])))

    mask = (image1_transformed != 0) & (image2_transformed != 0)
    registered = image1_transformed + image2_transformed
    registered[mask] /= 2
    return registered