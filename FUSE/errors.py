
import errno


class IntentionalException(Exception):
    pass


def readonly():
    """
    Raise when the OS tries to modify a read-only resource.
    """
    raise IntentionalException(errno.EROFS)  # 30


def deny():
    """
    Raise when the OS tries to access a resource with insufficient permission.
    """
    raise IntentionalException(errno.EACCES)  # 13


def notreal():
    """
    Raise when the OS tries to access a resource that doesn't exist.
    """
    raise IntentionalException(errno.ENOENT)  # 2


def notreadyyet():
    """
    Raise when the OS tries to perform non-blocking I/O on a resource that
    isn't ready yet, but will be in the future.

    Identical to `errno.EWOULDBLOCK`.
    """
    raise IntentionalException(errno.EAGAIN)  # 35
