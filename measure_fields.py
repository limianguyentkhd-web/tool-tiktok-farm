from PIL import Image
import sys
sys.stdout.reconfigure(encoding='utf-8')

im = Image.open('gl_reg_page_ok.png')
w, h = im.size
print(f"Image size: {w}x{h}")

# The white boxes have borders around r=200..230, g=200..230, b=230..255 and white inside (255, 255, 255)
# Let's inspect along vertical line x=540
inside_box = False
boxes = []
start_y = 0

for y in range(300, 1600):
    r, g, b, *a = im.getpixel((540, y))
    # background outside card is purple/pink (r > 150, b > 150)
    # card background is white (255, 255, 255)
    # input box border has border color, inside is white
    # Let's check left border at x=100
    r_edge, g_edge, b_edge, *a = im.getpixel((95, y))
    # If edge is near border color (200-240)
    if 180 <= r_edge <= 245 and 180 <= g_edge <= 245 and 200 <= b_edge <= 255:
        boxes.append(y)

print(f"Found border y range: {min(boxes) if boxes else 'None'} to {max(boxes) if boxes else 'None'}")
