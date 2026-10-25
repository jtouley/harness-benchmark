import fcntl, socket, struct, sys, os
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ifr = struct.pack('16sH', b'lo', 0)
flags = struct.unpack('16sH', fcntl.ioctl(s, 0x8913, ifr))[1]
fcntl.ioctl(s, 0x8914, struct.pack('16sH', b'lo', flags | 1))
os.execvp(sys.argv[1], sys.argv[1:])
