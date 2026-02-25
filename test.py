from compressor import compress_file
import os

from PIL import Image
import fitz

img = Image.new('RGB', (1000, 1000), color = 'red')
img.save('sample.jpg')

doc = fitz.open()
page = doc.new_page()
page.insert_text((50, 50), "Hello World", fontsize=50)
doc.save('sample.pdf')
doc.close()

# test image compression to 100KB (102400 bytes)
out = compress_file('sample.jpg', 102400)
if out:
    size = os.path.getsize(out)
    print(f"Image compressed to exact size: {size == 102400}. Size: {size}")
else:
    print("Failed to compress image")

# test pdf compression to 150KB (153600 bytes)
out_pdf = compress_file('sample.pdf', 153600)
if out_pdf:
    size = os.path.getsize(out_pdf)
    print(f"PDF compressed to exact size: {size == 153600}. Size: {size}")
else:
    print("Failed to compress pdf")
