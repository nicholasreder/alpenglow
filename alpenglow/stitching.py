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
    shift = find_shift(image1, image2)
    registered = apply_shift(image1, image2, shift)
    return registered, shift


def find_shift(image1, image2):
    """ 
    Identify lateral shifts to stitch two images
    
    Parameters
    ----------
    image1, image2 : 2D arrays
        The images to be stitched, *in order* (bottom, top)

    Returns
    -------
    tuple : lateral shifts (x, y)
    """
    
    cols1 = image1.shape[1]
    cols2 = image2.shape[1]
    rows1 = image1.shape[0]
    rows2 = image2.shape[0]
    shift, error, diffphase = register_translation(image1[:rows2//2, int(cols2//2-0.1*cols2):int(cols2//2+0.1*cols2)],
                                                   image2[rows2//2:, int(cols2//2-0.1*cols2):int(cols2//2+0.1*cols2)])
    return shift


def apply_shift(image1, image2, shift, margin=100):
    """ 
    Apply a lateral shift between two images, stitching them together
    
    Parameters
    ----------
    image1, image2 : 2D arrays
        The images to be stitched, *in order* (bottom, top)
    
    shift : sequence of length 2 
        x, y lateral shifts
    
    Returns
    -------
    Stitched image
    
    """
    
    cols1 = image1.shape[1]
    cols2 = image2.shape[1]
    rows1 = image1.shape[0]
    rows2 = image2.shape[0]

    overlap=rows2 // 2 + shift[0]
    registered = np.zeros((rows1 + rows2 - overlap, cols1), dtype=int)
    registered[:rows2-margin] = image2[:rows2-margin]
    if shift[1] > 0:
        registered[rows2-margin:, :cols1-shift[1]] = image1[overlap-margin:, shift[1]:] 
    else:
        registered[rows2-margin:, abs(shift[1]):] = image1[overlap-margin:, :shift[1]] 
    
    if margin > 0:
        fade2 = image2[rows2 - margin:rows2] * np.arange(1, 0, -0.01)[:, np.newaxis]
        fade1 = np.zeros_like(fade2)
        if shift[1] > 0:
            fade1[:, :cols1-shift[1]] = image1[overlap-margin:overlap, shift[1]:] * np.arange(0, 1, 0.01)[:, np.newaxis]
        else:
            fade1[:, abs(shift[1]):] = image1[overlap-margin:overlap, :shift[1]] * np.arange(0, 1, 0.01)[:, np.newaxis]

        registered[rows2 - margin:rows2] = fade1 + fade2

    return registered.astype(int)
