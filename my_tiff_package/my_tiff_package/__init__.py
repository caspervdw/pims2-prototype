import dask.array
import tifffile


class TIFFReader:
    """
    Accepts file, filepath, or filepath glob.
    """
    container = 'dask.array.core.Array'

    def __init__(self, file):
        if isinstance(file, str):
            # file is a filepath or filepath glob
            import os
            if os.path.isfile(file):
                self._tiff_files = [tifffile.TiffFile(file)]
            else:
                import glob
                self._tiff_files = [tifffile.TiffFile(file_)
                                    for file_ in glob.glob(file)]
            # TODO Pick off metadata of interest from self._tiff_files.
            self.metadata = {}
        else:
            # file is a file buffer
            self._tiff_files = [tifffile.TiffFile(file)]
        self._file = file  # used in __repr__
        self._closed = False

    def __repr__(self):
        return f"TiffReader({self._file!r})"

    def read(self):
        if self._closed:
            raise Closed(f"{self} is closed and can no longer be read.")
        stack = []
        for tf in self._tiff_files:
            assert len(tf.series) == 1  # should be True by construction
            series = tf.series[0]
            dtype = series.dtype
            for page in series.pages:
                delayed = dask.delayed(page.asarray)()
                stack.append(dask.array.from_delayed(
                    delayed, shape=page.shape, dtype=dtype))
        # TODO Not sure if special-casing one image is the right move here.
        if len(stack) == 1:
            return stack[0]
        else:
            return dask.array.stack(stack)

    def close(self):
        self._closed = True
        for tf in self._tiff_files:
            tf.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc_details):
        self.close()


class Closed(Exception):
    ...
