import logging
import sys

def setup_logger(name):
    """
    Membuat logger yang terkonfigurasi dengan format yang rapi untuk debugging.
    """
    logger = logging.getLogger(name)
    
    # Mencegah duplikasi log jika dipanggil berkali-kali
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        # Format: [WAKTU] [NAMA_MODUL] - PESAN
        formatter = logging.Formatter(
            fmt='[%(asctime)s] [%(name)s] %(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger