import os
import random
import string
import numpy as np
# pip install -U bootstrap-flask
import pandas as pd
from PIL import Image
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename
from wtforms import SubmitField, FileField
from wtforms.validators import DataRequired


# A prerequisite is to have folder cleaner module of an old images to save your server quota
# Ie running some cron job or include here a code removing older files than dd.mm date ;-)
UPLOAD_FOLDER = 'static\pics'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['SECRET_KEY'] = '89ugUHDGF8yugntrdehaIGJU(KR6b'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
Bootstrap5(app)


# Function changing RGB na Hex
# https://blog.finxter.com/5-best-ways-to-convert-python-rgb-tuples-to-hex/
def rgb_to_hex(red, green, blue):
    """Return color as #rrggbb for the given color values."""
    return '#%02x%02x%02x' % (red, green, blue)

# That is tricky to change RGB to Hex using lambda directly in pandas
# But we can do it directly on webpage at every RGB values


# Generate some random filename to prevent file saving errors
def random_file_name():
    """Return ten char (alpha number) random filename without extension"""
    letters = string.ascii_lowercase
    numbers = string.digits
    txt = ''.join(random.choice(letters) for i in range(6))
    return txt.join(random.choice(numbers) for i in range(4))

# =============== WEB SITE module ===================


class SendPhotoForm(FlaskForm):
    file = FileField("Send us an image (JPG, PNG):", validators=[DataRequired()])
    submit = SubmitField("Show me the colors!")


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


newfilename = str


@app.route('/', methods=['POST', 'GET'])
def home():
    global newfilename
    form = SendPhotoForm()
    if form.validate_on_submit():
        # copycat from Flask docs
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            newfilename_less_ext = random_file_name()
            file_ext = filename.rsplit(".")[1]
            newfilename = newfilename_less_ext + '.' + file_ext
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], newfilename))
            return redirect(url_for('my_colors', name=newfilename))
    return render_template("index.html", form=form)


@app.route('/mycolors', methods=['POST', 'GET'])
def my_colors():
    with Image.open(os.path.join(app.config['UPLOAD_FOLDER'], newfilename)) as im:
        # Big pictures (over 600 px ) must be resized into thumbnail respecting aspect ratio:
        size = 900, 900
        im.thumbnail(size, Image.Resampling.LANCZOS)
        im.save(os.path.join(app.config['UPLOAD_FOLDER'], newfilename))
        im_array = np.array(im)
        # removes file
        # os.remove(os.path.join(app.config['UPLOAD_FOLDER'], newfilename))

    # Playing with NumPy arrays to test if everything is OK
    # print(type(im))
    # print(f'Array has {im.ndim} dimensions')
    # print(im.shape)
    # print(im[1, 1])
    # print(im[1, 5])

    img_x = im_array.shape[0]
    img_y = im_array.shape[1]

    # From 3D array into 2D (kinda list of tuples)
    im_2d = im_array.reshape(img_x * img_y, 3)
    list_of_pixels = [tuple(x) for x in im_2d.tolist()]
    # to Pandas series
    pd_pixels = pd.Series(list_of_pixels)

    # print(pd_pixels)
    # Counting how many colors we have in the image:
    pd_pixels_counted = pd_pixels.value_counts()

    # Checking if there are less than 10 colors:
    if pd_pixels_counted.count() >= 10:
        top_colors = pd_pixels_counted[:10]
    else:
        no_of_colors = pd_pixels_counted.count()
        top_colors = pd_pixels_counted[:no_of_colors]

    # Going from Series to DataFrame plus making indices:
    top_colors = top_colors.to_frame().reset_index()

    # Renaming/adding columns
    top_colors.rename(columns={'index': 'RGB_value', 'count': 'frequency'}, inplace=True)
    top_colors.insert(2, 'Percentage', '')
    top_colors['Percentage'] = ((top_colors.frequency / (img_x * img_y)) * 100).round(2)
    return render_template("mycolors.html", file=os.path.join(app.config['UPLOAD_FOLDER'], newfilename), colors=top_colors)


if __name__ == "__main__":
    app.run(debug=True)