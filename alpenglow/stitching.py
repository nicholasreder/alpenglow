from tempfile import mkdtemp
import os.path as op

import numpy as np

import skimage
from skimage import transform
from skimage.feature import register_translation
from skimage.io import imread_collection, ImageCollection
import skimage.external.tifffile as tiff
import glob as globby


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
    
    # If we have an odd number of rows, we get uneven indexing. 
    # So we correct, by adding one more row:
    if np.mod(rows2, 2):
        im1_register = image1[:rows2//2+1, int(cols2//2-0.1*cols2):int(cols2//2+0.1*cols2)]
    else:
        im1_register = image1[:rows2//2, int(cols2//2-0.1*cols2):int(cols2//2+0.1*cols2)]

    im2_register = image2[rows2//2:, int(cols2//2-0.1*cols2):int(cols2//2+0.1*cols2)]
    
    shift, error, diffphase = register_translation(im1_register, im2_register)
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

    overlap = int(rows2 // 2 + shift[0])
    registered = np.zeros((rows1 + rows2 - overlap, cols1), dtype=int)
    registered[:rows2-margin] = image2[:rows2-margin]
    if shift[1] > 0:
        registered[rows2-margin:, :cols1-int(shift[1])] = image1[overlap-margin:, int(shift[1]):] 
    else:
        registered[rows2-margin:, abs(int(shift[1])):] = image1[overlap-margin:, :int(shift[1])] 
    
    if margin > 0:
        fade2 = image2[rows2 - margin:rows2] * np.arange(1, 0, -0.01)[:, np.newaxis]
        fade1 = np.zeros_like(fade2)
        if shift[1] > 0:
            fade1[:, :cols1-int(shift[1])] = (image1[overlap-margin:overlap, int(shift[1]):] * 
                                              np.arange(0, 1, 0.01)[:, np.newaxis])
        else:
            fade1[:, abs(int(shift[1])):] = image1[overlap-margin:overlap, :int(shift[1])] * np.arange(0, 1, 0.01)[:, np.newaxis]

        registered[rows2 - margin:rows2] = fade1 + fade2

    return registered.astype(int)

def test_image(path, first_strip, last_strip, percentile = 50):
    """ 
    Return test image at specified depth within z-stack
    
    Parameters
    ----------
    path : string
        The string of the path 
    first_strip, last_strip : ints
        The index of the first strip and last strip to be stitched, *in order* (bottom, top)
    percentile: int
        Depth of test image within z-stack (larger number is deeper in stack)
    Returns
    -------
    Stitched image (as array) at specified depth
    """
    p = int(np.percentile(np.arange(len(globby.glob1(path,"%06d_*.tif" % first_strip))), percentile))
    image1 = tif.imread(path + '%06d_%06d.tif' % (first_strip, p))
    image2 = tif.imread(path + '%06d_%06d.tif' % (first_strip + 1, p))
    mosaic, shift = stitch(image1, image2) 
    for x in range (first_strip + 2, last_strip): #
        image2 = tif.imread(path + '%06d_%06d.tif' % (x, p))
        mosaic, shift = stitch(mosaic, image2)
    return mosaic



def stitch_zstack(images_1, images_2, current_stack=None, out_path=None):
    """
    Stitch two z-stacks of tiff strips
    
    Parameters
    ----------
    images_1, images_2 : objects of type ImageCollection, or numpy mem-mapped arrays

    current_stack : int, optional
        The serial number of the current stack that is being stitched. This is only
        consequential in the case in which tiffs are saved (will be saved as 
        "mosaic_%06d_%06d.tif"%(current_stack, z_level+1))

    out_path : str
        Where to save output files (only relevant if input are ImageCollection 
        objects)

    Returns 
    -------
    Depending on the input: ImageCollection or numpy mem-mapped array
    """
    percentiles = [int(np.percentile(np.arange(len(images_1)), x)) for x in range(10, 100, 10)]
    sub_images_1 = np.zeros((len(percentiles), images_1[0].shape[0], images_1[0].shape[1]))
    sub_images_2 = np.zeros((len(percentiles), images_2[0].shape[0], images_2[0].shape[1]))

    for ii, p in enumerate(percentiles):
        sub_images_1[ii]= images_1[p]
        sub_images_2[ii] = images_2[p]
    
    shift = []
    for x in range(len(sub_images_1)):
        shift.append(find_shift(sub_images_1[x], sub_images_2[x]))
    shift = np.array(shift)
    coef = []
    coef = np.polyfit(percentiles, shift[:,0], 1)
    
    shift_last = int(np.round(np.polyval(coef, len(images_1))))
    rows = images_1[0].shape[0]+images_2[0].shape[0]
    overlap = (images_2[0].shape[0]//2)+shift_last
    chop_index = int(rows - overlap)
    
    if isinstance(images_1, skimage.io.collection.ImageCollection):
        # Do the relatively slow thing, but save the results
        if out_path is None:
            out_path = '.'
        if current_stack is None:
            current_stack = 1
        for z_level in range(len(images_1)):
            shift_zero = int(np.round(np.polyval(coef, z_level)))
            shift_one = int(np.round(np.mean(shift[:,1])))
            registered = apply_shift(images_1[z_level], images_2[z_level], [shift_zero, shift_one])
            tiff.imsave(op.join(out_path, "mosaic_%06d_%06d.tif"%(current_stack, z_level+1)), 
                        registered[:chop_index]) 
        return ImageCollection(op.join(out_path, "mosaic_%06d_*.tif"%(current_stack)),
                               plugin="tifffile")
    else:
        # Do the relatively fast thing, without saving
        f3 = op.join(mkdtemp(), 'reg.dat')
        h3 = open(f3, 'w')
        registered = np.memmap(f3, dtype=images_1.dtype, shape=(len(images_1), chop_index, images_1[0].shape[1]))
        for z_level in range(len(images_1)):
            shift_zero = int(np.round(np.polyval(coef, z_level)))
            shift_one = int(np.round(np.mean(shift[:,1])))
            registered[z_level] = apply_shift(images_1[z_level], images_2[z_level], [shift_zero, shift_one])[:chop_index]

        return registered