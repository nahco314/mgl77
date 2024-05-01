from abc import ABC
from typing import Optional

import flet as ft

from pathlib import Path
from pydantic import BaseModel, ValidationError
import tomllib

import subprocess

import re


class GameData(BaseModel):
    title: str
    description: str
    author: str
    game_exe: Path
    screen_shot: Optional[Path]
    index: int


def get_games(games_path: Path) -> list[GameData]:
    # games_path の中からゲーム情報を読み取り、一覧を返す
    # ふつう、games_path は assets/games ということになる

    res = []

    for i, p in enumerate(filter(lambda p: p.is_dir(), games_path.iterdir())):
        toml_path = p / "game.toml"
        if not toml_path.exists():
            raise FileNotFoundError(f"game.toml not found in {p}")

        screen_shot_path = p / "ss.png"
        screen_shot: Optional[Path]
        if screen_shot_path.exists():
            screen_shot = screen_shot_path
        else:
            screen_shot = None

        with open(toml_path, "rb") as f:
            dct = tomllib.load(f)
            dct["screen_shot"] = screen_shot
            dct["index"] = i
            dct["game_exe"] = p / f"{dct["game_exe_name"]}.exe" if "game_exe_name" in dct else None
            try:
                game_data = GameData(**dct)
            except ValidationError:
                raise ValueError(f"Invalid game.toml in {p}")

        if not game_data.game_exe.exists():
            raise FileNotFoundError(f"Game exe not found in {p}")

        res.append(game_data)

    return res


class AllGameData:
    def __init__(self):
        self.control_groups = get_games(Path("assets/games"))
        self.selected_control_group = self.control_groups[0]


class NavigationItem(ft.Container):
    def __init__(self, destination, item_clicked):
        super().__init__()
        self.ink = True
        self.padding = 10
        self.border_radius = 5
        self.destination = destination
        self.text = destination.title
        self.content = ft.Row(
            [ft.Text(self.text), ft.Text(destination.author)],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        self.on_click = item_clicked


class NavigationColumn(ft.Column):
    def __init__(self, gallery: AllGameData):
        super().__init__(alignment=ft.MainAxisAlignment.CENTER, spacing=10)
        self.expand = 4
        self.spacing = 0
        self.scroll = ft.ScrollMode.ALWAYS
        self.width = 200
        self.gallery = gallery
        self.selected_index = 0
        self.controls = self.get_navigation_items()

    def before_update(self):
        super().before_update()
        self.update_selected_item()

    def get_navigation_items(self):
        navigation_items = []
        for destination in self.gallery.control_groups:
            navigation_items.append(
                NavigationItem(destination, item_clicked=self.item_clicked)
            )
        return navigation_items

    def select(self, index: int) -> None:
        self.selected_index = index
        self.gallery.selected_control_group = self.gallery.control_groups[index]
        self.update_selected_item()
        self.page.go(
            f"/games/{index}"
        )  # なんかここはエラー出ることがある　ようわからん

    def item_clicked(self, e):
        self.select(e.control.destination.index)

    def update_selected_item(self):
        self.selected_index = self.gallery.control_groups.index(
            self.gallery.selected_control_group
        )

        for item in self.controls:
            item.bgcolor = None
            # item.content.controls[0].name = item.destination.icon
        self.controls[self.selected_index].bgcolor = ft.colors.SECONDARY_CONTAINER
        # self.controls[self.selected_index].content.controls[0].name = self.controls[
        #     self.selected_index
        # ].destination.selected_icon
