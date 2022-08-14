
import errno


def readonly():
    """
    Raise when the OS tries to modify a read-only resource.
    """
    raise Exception(errno.EROFS)


def deny():
    """
    Raise when the OS tries to access a resource with insufficient permission.
    """
    raise Exception(errno.EACCES)


def notreal():
    """
    Raise when the OS tries to access a resource that doesn't exist.
    """
    raise Exception(errno.ENOENT)


def notreadyyet():
    """
    Raise when the OS tries to perform non-blocking I/O on a resource that
    isn't ready yet, but will be in the future.

    Identical to `errno.EWOULDBLOCK`.
    """
    raise Exception(errno.EAGAIN)
