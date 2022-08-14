
import abc


class AbstractReadOnlyBackend(abc.ABC):
    def has(path: str) -> bool:
        """
        Return whether the given path exists (as a file or directory).
        """
        raise NotImplementedError()

    def is_dir(path: str) -> bool:
        """
        Return whether the given path exists, and is a directory.
        """
        raise NotImplementedError()

    def list(path: str) -> list[str]:
        """
        Return a list of filenames/directory names under the given path.

        Names should not include paths (i.e., slashes), as they must be
        relative to the search path provided.
        """
        raise NotImplementedError()

    def read(path: str, length: int, offset: int) -> bytes:
        """
        Read bytes from the file at the given path, starting at `offset`
        and up to `length`.

        If the path is a directory, raise `errno.EACCES` (13).

        If the path does not exist, raise `errno.ENOENT` (2).
        """
        raise NotImplementedError()

    def size(path: str) -> int:
        """
        Return the size of the file or directory at the given path.

        If the path is a directory, return 96.

        If the path does not exist, raise `errno.ENOENT` (2).
        """
        raise NotImplementedError()
