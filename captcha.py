from random import randint
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO


def generate_captcha(text):
    l = len(text)
    img = Image.new(mode='RGB', size=(70*l, 120))
    for x in range(l):
        letter_img = Image.new(mode='RGB', size=(70, 120))
        dimg = ImageDraw.Draw(letter_img)
        font = ImageFont.truetype('arial.ttf', randint(70, 100))
        dimg.text((randint(0, 15), randint(0, 15)), text[x], (randint(0, 255), randint(0, 255), randint(0, 255)), font)
        letter_img = letter_img.rotate(randint(-40, 40))
        img.paste(letter_img, (70*x, 0))
    dimg = ImageDraw.Draw(img)
    for x in range(20):
        dimg.line((randint(0, 70*l), randint(0, 120), randint(0, 70*l), randint(0, 120)), (randint(0, 255), randint(0, 255), randint(0, 255)), randint(1, 3))

    pseudofile_img = BytesIO()
    img.save(pseudofile_img, format='PNG')
    pseudofile_img.seek(0)
    return pseudofile_img
