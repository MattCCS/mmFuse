
def readonly():
    raise Exception(errno.EROFS)

def deny():
    raise Exception(errno.EACCES)

def notreal():
    raise Exception(errno.ENOENT)

def notreadyyet():
    raise Exception(errno.EAGAIN)
