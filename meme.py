# from https://gist.github.com/omz/4034426
# Meme Generator 1
# Demonstrates how to draw text on images using PIL
# (Python Imaging Library)
# 
# The script loads an image from the clipboard (or uses
# a default one if the clipboard is empty) and asks for
# two captions (top and bottom) that are then drawn onto
# the image.

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


def draw_caption(img, text, top=False, padding=10):
	draw = ImageDraw.Draw(img)
	#Find a suitable font size to fill the entire width:
	w = img.size[0]
	s = 100
	while w >= (img.size[0] - 20):
		font = ImageFont.truetype('impact.ttf', s)
		w, h = draw.textsize(text, font=font)
		s -= 1
		if s <= 12: break

        draw_x = (img.size[0] - w) / 2
       
       
	#Draw the text multiple times in black to get the outline:
	for x in xrange(-3, 4):
		for y in xrange(-3, 4):
			draw_y = y + padding if top else img.size[1] - h + y - padding
			draw.text((draw_x + x, draw_y), text, font=font, fill='black')
	#Draw the text once more in white:
	draw_y = 0 + padding if top else img.size[1] - h - padding
	draw.text((draw_x, draw_y), text, font=font, fill='white')

import sys
def main():
  img = Image.open(open(sys.argv[1]))
  draw_caption(img, sys.argv[2], top=True, padding=3)
  draw_caption(img, sys.argv[3], top=False, padding=20)
  img.show()

if __name__ == "__main__":
  main()
  
