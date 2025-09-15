"""
A blessed terminal-based image viewer
"""

import click
import numpy
from blessed import Terminal
from PIL import Image


@click.command()
@click.argument("filename")
def blessedviewer(filename: str) -> None:
    """
    A blessed terminal-based image viewer
    """

    terminal = Terminal()
    image = Image.open(filename)
    image.thumbnail((terminal.width, terminal.height * 2 - 2))

    print(terminal.clear(), end=terminal.home)

    image = numpy.array(image)

    for yid, y in enumerate(image[::2]):
        for xid, x in enumerate(y):
            x2 = image[yid * 2 + 1, xid]
            if isinstance(x, numpy.uint8):
                x = [255 - x, 255 - x, 255 - x]
                x2 = [255 - x2, 255 - x2, 255 - x2]

            elif len(x) == 4:
                x = x[:3]
                x2 = x[:3]

            print(
                terminal.moveyx(yid, xid),
                terminal.color_rgb(*x),
                "" if yid * 2 + 1 > image.shape[0] else terminal.on_color_rgb(*x2),
                "▀",
                sep="",
                end=""
            )
        print(terminal.normal)

if __name__ == "__main__":
    blessedviewer()
