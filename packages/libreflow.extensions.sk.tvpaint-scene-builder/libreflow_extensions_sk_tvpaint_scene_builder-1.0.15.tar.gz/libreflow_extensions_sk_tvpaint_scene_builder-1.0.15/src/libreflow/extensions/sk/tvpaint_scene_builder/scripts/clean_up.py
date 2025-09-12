import sys
import argparse
import os

from pytvpaint import george
from pytvpaint.project import Project


def process_remaining_args(args):
    parser = argparse.ArgumentParser(
        description='TVPaint Remove Animatic Arguments'
    )
    parser.add_argument('--destination', dest='destination')
    parser.add_argument('--animatic-path', dest='animatic_path')


    values, _ = parser.parse_known_args(args)

    return (
        values.destination, values.animatic_path,
    )

DEST = process_remaining_args(sys.argv)[0]
print (f'{DEST=}')
ANIMATIC_PATH = process_remaining_args(sys.argv)[1]
print (f'{ANIMATIC_PATH=}')

project = Project.current_project()

new_project = project.duplicate()
clip = new_project.current_clip
project.close()

if ANIMATIC_PATH and ANIMATIC_PATH != 'None':
    print("[SCENE UPDATE] Updating Animatic Layer")

    filename = os.path.split(os.path.splitext(ANIMATIC_PATH)[0])[1]

    clip.get_layer_color(by_index=11).select_layers(True)

    if all(False for _ in clip.selected_layers):
        print('No Animatic found - creating the layer')

        new_layer = clip.load_media(media_path=ANIMATIC_PATH, with_name=f"Animatic_{filename}", preload=True)
        new_layer.color = clip.get_layer_color(by_index=11)

    else :
        clip.get_layer_color(by_index=11).select_layers(True)
        *_,layer = clip.selected_layers

        layer.make_current()

        new_layer = clip.load_media(media_path=ANIMATIC_PATH, with_name=filename, preload=True)
        new_layer.color = clip.get_layer_color(by_index=11)
        
        layer.remove()

#clean white layers

clip.get_layer_color(10).select_layers(True)

for l in clip.selected_layers:
    l.remove()


# animatic_layer = clip.get_layer(by_name="[REF]")
# if animatic_layer:
#     animatic_layer.remove()


new_project.save(save_path = DEST)
new_project.close_all(True)
# george.tv_save_project()