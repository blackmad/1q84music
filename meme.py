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


def draw_caption(img, text, top=False):
	draw = ImageDraw.Draw(img)
	#Find a suitable font size to fill the entire width:
	w = img.size[0]
	s = 100
	while w >= (img.size[0] - 20):
		font = ImageFont.truetype('impact.ttf', s)
		w, h = draw.textsize(text, font=font)
		s -= 1
		if s <= 12: break
	#Draw the text multiple times in black to get the outline:
	for x in xrange(-3, 4):
		for y in xrange(-3, 4):
			draw_y = y if top else img.size[1] - h + y
			draw.text((10 + x, draw_y), text, font=font, fill='black')
	#Draw the text once more in white:
	draw_y = 0 if top else img.size[1] - h
	draw.text((10, draw_y), text, font=font, fill='white')
