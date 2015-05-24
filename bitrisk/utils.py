from qrcode import QRCode

def qrcode(address):
    qr = QRCode()
    qr.add_data('bitcoin:%s' % (address))
    return qr

def qrcode_png_buffer(qr):
    import io
    image = qr.make_image()
    buf = io.BytesIO()
    image.save(buf, 'PNG')
    return buf
