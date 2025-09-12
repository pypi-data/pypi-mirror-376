from typing import Annotated
import typer
from .utils import *
from .interact import interact

app = typer.Typer(invoke_without_command=True)

@app.command(name='interact')
def interact_cmd(
        bag_path: Annotated[Path, typer.Argument()] = None,
        fake_lat: Annotated[float, typer.Option(
            help='Fake latitude if no bag is provided',
        )] = 40,
        fake_lon: Annotated[float, typer.Option(
            help='Fake longitude if no bag is provided',
        )] = 116,
        fake_alt: Annotated[float, typer.Option(
            help='Fake altitude if no bag is provided',
        )] = 0,
):
    interact(bag_path, fake_lat, fake_lon, fake_alt)

def main():
    try:
        app()
    except Exception as e:
        print(e)
        exit(1)

if __name__ == '__main__':
    main()
