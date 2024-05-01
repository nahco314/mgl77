from abc import ABC
from typing import Optional

import flet as ft

from pathlib import Path
from pydantic import BaseModel, ValidationError
import tomllib

import re


class GameData(BaseModel):
    title: str
    description: str
    author: str
    game_exe_name: str
    screen_shot: Optional[Path]
    index: int


def get_games(games_path: Path) -> list[GameData]:
    # games_path の中からゲーム情報を読み取り、一覧を返す
    # ふつう、games_path は assets/games ということになる

    res = []

    for i, p in enumerate(games_path.iterdir()):
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
            try:
                game_data = GameData(**dct)
            except ValidationError:
                raise ValueError(f"Invalid game.toml in {p}")

        exe_path = p / f"{game_data.game_exe_name}.exe"
        if not exe_path.exists():
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
        self.content = ft.Row([ft.Text(self.text)])
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
        print(self.selected_index, self.gallery.selected_control_group)

        print(1, self.selected_index)

        self.selected_index = self.gallery.control_groups.index(
            self.gallery.selected_control_group
        )
        print(2, self.selected_index)

        for item in self.controls:
            item.bgcolor = None
            # item.content.controls[0].name = item.destination.icon
        self.controls[self.selected_index].bgcolor = ft.colors.SECONDARY_CONTAINER
        # self.controls[self.selected_index].content.controls[0].name = self.controls[
        #     self.selected_index
        # ].destination.selected_icon


def main(page: ft.Page):
    page.title = "Routes Example"

    img_controller: Optional[ft.Container] = None

    def route_change(e):
        nonlocal img_controller

        page.views.clear()
        page.views.append(
            ft.View(
                "/",
                [
                    ft.Text(
                        "AGC展ミニゲーム集", size=100, text_align=ft.TextAlign.CENTER
                    ),
                    ft.ElevatedButton(
                        content=ft.Text("はじめる", size=36),
                        width=200,
                        height=80,
                        on_click=lambda _: page.go("/games/0"),
                    ),
                ],
                spacing=80,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

        if m := re.match("/games/(.*)", page.route):
            num = int(m.group(1))

            nav = NavigationColumn(AllGameData())

            for it in nav.gallery.control_groups:
                if it.index == num:
                    nav.gallery.selected_control_group = it
                    break

            img_w = page.width / 10 * 7
            img_h = page.height - 100

            if nav.gallery.selected_control_group.screen_shot is not None:
                img_controller = ft.Image(
                    src=str(nav.gallery.selected_control_group.screen_shot.absolute()),
                    width=img_w,
                    height=img_h,
                    fit=ft.ImageFit.COVER,
                )
            else:
                img_controller = ft.Container(
                    bgcolor=ft.colors.GREY, width=img_w, height=img_h
                )

            def on_keyboard(e: ft.KeyboardEvent):
                nav_items = nav.get_navigation_items()

                if e.key == "Arrow Down":
                    nav.select((num + 1) % len(nav_items))
                    nav.update_selected_item()
                elif e.key == "Arrow Up":
                    nav.select((num - 1) % len(nav_items))
                    nav.update_selected_item()

            page.on_keyboard_event = on_keyboard

            page.views.append(
                ft.View(
                    "/games",
                    [
                        ft.AppBar(
                            title=ft.Text("ミニゲーム一覧"),
                            leading=ft.Container(
                                ft.ElevatedButton(
                                    "やめる", on_click=lambda _: page.go("/")
                                ),
                                padding=5,
                            ),
                            leading_width=120,
                            bgcolor=ft.colors.SURFACE_VARIANT,
                        ),
                        ft.Row(
                            [
                                nav,
                                ft.Stack(
                                    [
                                        img_controller,
                                        ft.Column(
                                            [
                                                ft.Text(
                                                    "たいとる",
                                                    bgcolor=ft.colors.with_opacity(
                                                        0.4, ft.colors.WHITE
                                                    ),
                                                    size=60,
                                                ),
                                                ft.Text(
                                                    "せつめい",
                                                    bgcolor=ft.colors.with_opacity(
                                                        0.4, ft.colors.WHITE
                                                    ),
                                                    size=20,
                                                ),
                                            ]
                                        ),
                                    ]
                                ),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.START,
                            alignment=ft.MainAxisAlignment.START,
                        ),
                    ],
                )
            )

        page.update()

    def page_resized(e):
        print(e)

        nonlocal img_controller
        if img_controller is not None:
            img_controller.width = page.width / 10 * 7
            img_controller.height = page.height - 100

        page.update()

    def view_pop(e):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_resize = page_resized
    page.on_view_pop = view_pop

    page.go(page.route)


if __name__ == "__main__":
    ft.app(main)
