import asyncio

import readchar
from rich.live import Live
from rich.prompt import Prompt
from rich.table import Table

from . import console
from .fid import Fid
from .utils import MODELS_OPTIONS


def select_model():
    current_index = 0
    selected_model = None

    def get_menu_table():
        table = Table(box=None, show_header=False)
        for i, option in enumerate(MODELS_OPTIONS):
            if i == current_index:
                table.add_row(f"> [bold green]{option}[/bold green]")
            else:
                table.add_row(f"  [gray66]{option}[/gray66]")
        return table

    console.print("[magenta]Choose the model:[magenta]")
    with Live(get_menu_table(), refresh_per_second=10, console=console) as live:
        while True:
            key = readchar.readkey()
            if key == readchar.key.UP:
                current_index = (current_index - 1) % len(MODELS_OPTIONS)
            elif key == readchar.key.DOWN:
                current_index = (current_index + 1) % len(MODELS_OPTIONS)
            elif key == readchar.key.ENTER:
                selected_model = MODELS_OPTIONS[current_index]
                break
            live.update(get_menu_table())

    if selected_model:
        prompt_input = Prompt.ask("\n[magenta]Enter a prompt:[/magenta]\n")
        fid = Fid(model=selected_model)
        console.print()
        asyncio.run(fid.run(prompt_input))
