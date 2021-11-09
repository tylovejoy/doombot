from PIL import Image, ImageDraw

x = 934
y = 282

y_offset = 45
x_offset = 30

innerbox = (x_offset, y_offset, x - x_offset, y - y_offset)

img = Image.new("RGBA", (x, y), color=(0, 0, 0, 0))

d = ImageDraw.Draw(img)
d.rounded_rectangle((0, 0, x, y), radius=10, fill=(100, 100, 100, 255))
d.rounded_rectangle(innerbox, radius=10, fill=(0, 0, 0, 150))
 
img.save('test.png', 'PNG')