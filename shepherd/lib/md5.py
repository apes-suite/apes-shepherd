## small functions to prepare and create md5_hashes
import hashlib
import os
import tarfile
import logging

def create_md5(input):
    md5 = hashlib.md5()
    if os.path.exists(input):
        if os.path.isdir(input):
            for root, dirs, files in os.walk(input):
                for names in files:
                    filepath = os.path.join(root,names)
                    try:
                        f1 = open(filepath, 'rb')
                    except:
                        # You can't open the file for some reason
                        f1.close()
                        continue
                    while 1:
                        # Read file in as little chunks
                        buf = f1.read(4096)
                        if not buf : break
                        md5.update(buf)
                    f1.close()
        if os.path.isfile(input):
            f1 = open(input, 'rb')
            while 1:
                buf = f1.read(4096)
                if not buf : break
                md5.update(buf)
            f1.close()
    else:
        try:
            input = input.encode('utf-8')
        except:
            logging.exception('Encoding failed')
            pass
        md5.update(input)

    md5_sum = md5.hexdigest()
    return md5_sum

def filechecksum_for(glob_pattern):
    import os
    import glob
    import zlib
    fsum = 0
    for match in glob.glob(glob_pattern):
        if os.path.isdir(match):
            for root, dirs, files in os.walk(match):
                for file in files:
                    fsum = zlib.crc32(
                            open(os.path.join(root,file), "rb").read(),
                            fsum)
        else:
            fsum = zlib.crc32(open(match, "rb").read(), fsum)
    return fsum

