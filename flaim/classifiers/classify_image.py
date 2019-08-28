import os
import json
import django
import shutil
from django.conf import settings

# Need to do this in order to access the flaim database models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

import shlex

from typing import Optional
from pathlib import Path
from subprocess import Popen, PIPE
from flaim.database.models import ProductImage, FrontOfPackLabel

""" 
Temporary junk script to call the cereal classifier via Popen and generate output files which will then be
read into the database

1. Grab all LoblawsProducts
2. Grab image_directory field
3. Glob all images within the directory
4. Create ProductImage entries for each
5. Run the classifier on each ProductImage
6. Store output results in the FrontOfPackLabel model
"""


def call_subprocess(cmd: str) -> tuple:
    env = os.environ.copy()
    p = Popen(shlex.split(cmd, posix=True), stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=False, env=env)
    stdout, stderr = p.communicate()
    stdout = stdout.decode("utf8").strip()
    stderr = stderr.decode("utf8").strip()
    if p.returncode != 0:
        print(f'Error executing command {cmd}')
    print(f"stderr: {stderr}")
    print(f"stdout: {stdout}")
    return stdout, stderr


def classify_loblaws_image(product_image: ProductImage, outdir: Path):
    print(f"Classifying {product_image}")
    json_file, img = classify_fop_image(product_image=product_image, outdir=outdir)
    if json_file is None:
        return None

    with open(str(json_file), 'r') as f:
        json_data = json.load(f)

    # Pull information from the JSON
    classified_image_path = json_data['classified_image_path']
    label_detected = json_data['label_detected']

    # Strip MEDIA_ROOT from the path so the ImageFile field behaves as expected in Django
    classified_image_path = classified_image_path.replace(settings.MEDIA_ROOT + "/", "")

    # Create object
    fop, created = FrontOfPackLabel.objects.get_or_create(product_image=product_image,
                                                          classifier_result_json=json_data,
                                                          classified_image_path=classified_image_path,
                                                          label_detected=label_detected)
    fop.save()


def classify_fop_image(product_image: ProductImage, outdir: Path) -> Optional[tuple]:
    CLASSIFIER_EXECUTABLE = Path("/home/forest/miniconda3/envs/CerealClassifier/bin/python")
    CLASSIFIER_SCRIPT = Path("/home/forest/PycharmProjects/CerealClassifier/cli.py")
    cmd = f'{CLASSIFIER_EXECUTABLE} {CLASSIFIER_SCRIPT} -i "{product_image.image_path.path}" -o "{outdir}"'
    stdout, stderr = call_subprocess(cmd)
    # There should always be a .json and a .jpg file present
    try:
        json_file = list(outdir.glob("*.json"))[0]
        img = list(outdir.glob("*.jpg"))[0]
    except IndexError:
        print(f"Error, couldn't find expected files in {outdir}")
        return None, None
    return json_file, img


if __name__ == "__main__":
    loblaws_images = ProductImage.objects.all()

    for p_ in loblaws_images:
        outdir_ = Path(p_.image_path.path).parent / (
            Path(p_.image_path.path).with_suffix("").name + '_FOP_classification')
        if outdir_.exists():
            shutil.rmtree(str(outdir_))  # Get rid of old results
        classify_loblaws_image(product_image=p_, outdir=outdir_)
