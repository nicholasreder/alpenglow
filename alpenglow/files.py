import numpy as np
import os
import boto3
from io import BytesIO
import skimage.external.tifffile as tif
import tempfile


def s3_to_array(f, cci):
    """ 
    Read a tif file straight from an S3 bucket (provided as a cottoncandy 
    interface) into a numpy array
   
    Parameters
    ----------
    f : str
        The name of the file in the bucket
    
    cci : cottoncandy interface
    
    
    """
    o = cci.download_object(f)
    b = BytesIO(o)
    t = tif.TiffFile(b)
    a = t.asarray()
    return a


def read_strip_files(file_list, files_per_strip, ss, cci, dtype, shape):
    """
    From a given list of files read all the tifs in one strip
    and return a memory-mapped array with the data.
    
    Parameters
    ----------
    file_list : list 
        All the file names from one experiment, ordered 
        according to strips 
    
    files_per_strip : int
        How many files (sheets) in each strip.
    
    ss : int
        A strip index.
    
    cci : a cottoncandy interface
    
    Return 
    ------
    Memory-mapped array with dimensions (z, width, sheets)
    """
    mm_fd, mm_fname = tempfile.mkstemp(suffix='.memmap')    
    strip_mm = np.memmap(mm_fname, dtype=dtype, 
                         shape=(files_per_strip, shape[0], shape[1]))
    for ii in range(files_per_strip):
        image_file = file_list[ss * files_per_strip + ii]
        strip_mm[ii] = s3_to_array(image_file, cci)
    
    mm_roll = np.swapaxes(np.swapaxes(strip_mm, 0, 1), 1, 2)
    # Strips are rastered back and forth, so we flip the odds
    if not np.mod(ss, 2):
        return mm_roll[..., ::-1]
    return mm_roll



def download_s3(remote_fname, local_fname, bucket_name="alpenglowoptics"):
    """
    Download a file from S3 to our local file-system
    """
    if not os.path.exists(local_fname):
        s3 = boto3.resource('s3')
        b = s3.Bucket(bucket_name)
        b.download_file(remote_fname, local_fname)    

def create_zstack(scan_name, strip_num, z_levels, sample_image_num = 55):
    """
    creates a zstack from a series of tiff frames for a single strip
    
    Parameters
    ----------
    scan_name = the label for the scan files (string)
    strip_num = the index of the strip (int)
    z_levels = number of pixels in height dimension (int)
    sample_image_num = arbitrarily chosen frame for reading dtype and shape for each frame (int)
    
    Returns
    -------
    ImageCollection
    """
  
    #downloading frames from s3 to ec2 instance
    for x in range(1, z_levels+1):
        fname = "%06d_%06d.tif" % (strip_num, x) # XXX we need to enforce 06d, start from 0
        download_s3('%s/%06d/' %(scan_name, strip_num) + fname, '../data/%s/%06d/' %(scan_name, strip_num) + fname)    

    imread = delayed(skimage.io.imread, pure=True)  # Lazy version of imread
    filenames = []
    for x in range(0, z_levels):
        fname = "%06d_%06d.tif" % (strip_num, x)
        filenames.append('../data/%s/%06d/' %(scan_name, strip_num) + fname)

    lazy_values = [imread(filename) for filename in filenames]    
    sample = skimage.io.imread(filenames[sample_image_num])
    arrays = [da.from_delayed(lazy_value,           # Construct a small Dask array
                              dtype=sample.dtype,   # for every lazy value
                              shape=sample.shape)
              for lazy_value in lazy_values]

    stack = da.stack(arrays, axis=0)  

    for z in range(1,stack.shape[1]):
        filename = 'zstack_%06d_%06d.tif' % (strip_num, z) 
        tiff.imsave(filename, stack[:,z,:].compute())
    zstack = ImageCollection('zstack_%06d_*.tif' % strip_num )
    return zstack

    
### DCIMG file i/o:

"""

The following code is copyright of David Baddeley,
http://www.python-microscopy.org/

It is released under GPL

"""

# best guess at the session header
SESSION_HEADER_DTYPE = [('session_length', 'i4'),
                        ('pad1', 'i4'),
                        ('psuedo_offset', 'i4'),
                        ('pad2', '5i4'),
                        ('num_frames', 'i4'),
                        ('pixel_type', 'i4'),
                        ('num_columns', 'i4'),
                        ('camera_center', 'i4'),
                        ('bytes_per_row', 'i4'),
                        ('num_rows', 'i4'),
                        ('bytes_per_image', 'i4'),
                        ('pad3', '2i4'),
                        ('offset_to_data', 'i4'),
                        ('offset_to_footer', 'i4')]

SESSION_HEADER_BYTES = np.zeros(1, dtype=SESSION_HEADER_DTYPE).nbytes

# immediately folloing this structure, there are a few more non-zero entries at
# dwords +2, +3, & +4, which I ca't make sense of

# newer versions of the dcimg format have a different header
SESSION_HEADER_DTYPE_INT2P24 = [
                        ('session_length', 'i4'),
                        ('pad1', '5i4'),
                        ('psuedo_offset', 'i4'),
                        ('pad2', '8i4'),   # there were mysteries number 1,
                                           # 144, 65537 in padding
                        ('num_frames', 'i4'),
                        ('pixel_type', 'i4'),
                        ('camera_center', 'i4'),
                        ('num_columns', 'i4'),
                        ('num_rows', 'i4'),      # num_rows switched position
                        ('bytes_per_row', 'i4'),
                        ('bytes_per_image', 'i4'),
                        ('pad3', '2i4'),
                        ('offset_to_data', 'i4'),
                        ('pad4', '4i4'),
                        ('bytes_per_frame', 'i4')]  # end_of_a_frame =
                                                    # bytes_per_image + 32
                                                    # bytes

SESSION_HEADER_BYTES_INT2P24 = np.zeros(
                            1,
                            dtype=SESSION_HEADER_DTYPE_INT2P24).nbytes


class DCIMGFile(object):
    def __init__(self, filename):
        with open(filename, 'rb') as hfile:
            # Read enough of the header to open both versions:
            header_bytes = hfile.read(728)

        self._info = self._parse_header(header_bytes)

        self.frames_with_footer = np.memmap(
            filename, dtype='<u2', mode='r',
            offset=int(self._info['session0_data']),
            shape=(int(self._info['bytes_per_frame'] /
                       self._info['bytes_per_pixel']),
                   int(self._info['num_frames'])), order='F')

    def get_frame(self, ind):
        """Get the frame at the given index, discarding a footer if needed

        Parameters
        ----------

        ind : int
            The index of the frame to retrieve
        """
        frame_wo_footer = \
            self.frames_with_footer[0:(self._info['bytes_per_image'] /
                                       self._info['bytes_per_pixel']), ind]
        frame_data = frame_wo_footer.reshape([self._info['num_rows'],
                                              self._info['num_columns']])

        return frame_data

    def get_slice_shape(self):
        return (self._info['num_columns'], self._info['num_rows'])

    def get_num_slices(self):
        return self._info['num_frames']

    def _parse_header(self, header):
        info = {}

        if not header.startswith(b'DCIMG'):
            raise RuntimeError("Not a valid DCIMG file")

        # the file header starts with an itentifying string and then seems to
        # consist (mostly) of uint32 integers, aligned on 4-byte boundaries.

        # after the identifying string, the first non-zero entry is at byte 8
        # it is unclear exactly what this means, but it is 7 in the example
        # data. The number of frames is roughly 7 4-byte dwords away, so this
        # might be an offset. That said, it could also be a version number or
        # pretty much anything. We have encountered two cases format_version =
        # 0x7 or 0x1000000, which have differences in both session_head and
        # frame data format Could this be some form of "flags" register?

        info['format_version'] = int(np.fromstring(header[8:12], 'uint32'))

        if not (info['format_version'] in [0x7, 0x1000000]):

            # in example data this is always 7. Warn if this is not the case,
            # as further assumptions might be invalid

            print("Warning: format_version is %d " % info['format_version'],
                  "rather than 0x7 or ",
                  "0x1000000 as expected")

        # the next non-zero value is 6 dwords further into the file at byte 32.
        # This is most likely to do with sessions. DCIMG files support multiple
        # "sessions", each of which contains a series of frames. I have no
        # multi-session data to test on, so cannot ascertain exactly what this
        # value means. Reasonable candidates are either the number of sessions,
        # or the current/first session ID

        info['num_sessions'] = int(np.fromstring(header[32:36], 'uint32'))
        if not info['num_sessions'] == 1:
            print("Warning: it appears that there",
                  "are %d " % info['num_sessions'],
                  " sessions. We only support one session")

        # the next entry is the number of frames, most likey in the first
        # session. We do not attempt to support multiple sessions

        info['num_frames'] = int(np.fromstring(header[36:40], 'uint32'))

        # and the next entry is an offset to the beginning of what I'm guessing
        # is the first session

        info['session0_offset'] = int(np.fromstring(header[40:44], 'uint32'))

        # this is followed by the filesize in bytes
        info['filesize'] = int(np.fromstring(header[48:52], 'uint32'))

        # NB because there is zero-padding after these offset and size values,
        # it's possible they are long (64 bit) integers instead of uint32. None
        # of the example data breaks the 4GB limit that would require long
        # offsets.

        # The filesize is repeated starting at byte 64, for unknown reasons
        info['filesize2'] = int(np.fromstring(header[64:68], 'uint32'))

        # the next non-zero value is at byte 84, and has the value 1024 in the
        # example data. The meaning is unknown.

        info['mystery1'] = int(np.fromstring(header[84:88], 'uint32'))

        # read the 1st session header  - vormat varies depending on file format
        if info['format_version'] == 7:
            session_head = np.fromstring(header[info['session0_offset']:(info['session0_offset']+SESSION_HEADER_BYTES)],
                                        dtype=SESSION_HEADER_DTYPE)

        elif info['format_version'] == 0x1000000:
            session_head = np.fromstring(header[info['session0_offset']:(info['session0_offset']+SESSION_HEADER_BYTES_INT2P24)],
                                    dtype=SESSION_HEADER_DTYPE_INT2P24)

            # each image include data and 32 bytes footer
        else:
            raise RuntimeError("Unknown file version: %0X" % info['format_version'])

        info['pixel_type'] = session_head['pixel_type']
        info['num_columns'] = session_head['num_columns']
        info['bytes_per_row'] = session_head['bytes_per_row']
        info['bytes_per_pixel'] = info['bytes_per_row']/info['num_columns']
        info['num_rows'] = session_head['num_rows']
        info['session0_data'] = info['session0_offset'] + session_head['offset_to_data']

        #info['session0_footer'] = info['session0_offset'] + session_head['offset_to_footer']

        info['bytes_per_image'] = session_head['bytes_per_image']
        try:
            #if the bytes per frame is different to the bytes per image (e.g.
            # if there is a frame footer)

            info['bytes_per_frame'] = session_head['bytes_per_frame']
        except ValueError:
            info['bytes_per_frame'] = session_head['bytes_per_image']

        return info
