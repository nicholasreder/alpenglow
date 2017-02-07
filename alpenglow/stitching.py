from skimage import transform
import numpy as np
from skimage.feature import register_translation
from skimage.io import imread_collection, ImageCollection

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

def stitch_zstack(images_1, images_2, current_stack):
    """
    Stitch two z-stacks of tiff strips
    
    Parameters
    ----------
    images_1, images_2 objects of type image_collection
    current_stack is an integer
    
    """
    sub_images_1 = []
    sub_images_2 = []
    ps = []
    for x in range(10,100,10):
        p = int(np.percentile(np.arange(len(images_1)), x))
        sub_images_1_p = images_1[p]
        sub_images_2_p = images_2[p]
        sub_images_1.append(sub_images_1_p)
        sub_images_2.append(sub_images_2_p)
        ps.append(p)
    
    shift = []
    for x in range(len(sub_images_1)):
        shift.append(find_shift(sub_images_1[x], sub_images_2[x]))
    shift = np.array(shift)
    coef = []
    coef = np.polyfit(ps, shift[:,0], 1)
    
    shift_last = int(np.round(np.polyval(coef, len(images_1))))
    rows = images_1[0].shape[0]+images_2[0].shape[0]
    overlap = (images_2[0].shape[0]//2)+shift_last
    chop_index = int(rows - overlap)

    for z_level in range(len(images_1)):
        shift_zero = int(np.round(np.polyval(coef, z_level)))
        shift_one = int(np.round(np.mean(shift[:,1])))
        registered = apply_shift(images_1[z_level], images_2[z_level], [shift_zero, shift_one])
        tiff.imsave("mosaic_%06d_%06d.tif"%(current_stack, z_level+1), registered[:chop_index]) 
    return ImageCollection("mosaic_%06d_*.tif"%(current_stack), plugin="tifffile")
    