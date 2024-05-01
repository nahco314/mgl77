from abc import ABC
from typing import Optional

import flet as ft

from pathlib import Path
from pydantic import BaseModel, ValidationError
import tomllib

import subprocess
from threading import Thread
from multiprocessing import Event

import re

from mgl77.fetch import fetch
from mgl77.game_data import NavigationColumn, AllGameData
from mgl77.time_keeper import time_keep

game_process: Optional[subprocess.Popen] = None
time_keeper_thread: Optional[Thread] = None
kill_window_event: Event = Event()
end_thread_event: Event = Event()

def main(page: ft.Page):
    page.title = "Routes Example"

    img_controller: Optional[ft.Container] = None
    img_part: Optional[ft.Container] = None

    def route_change(e):
        nonlocal img_controller, img_part
        global time_keeper_thread, kill_window_event, end_thread_event

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

        if page.route == "/":
            fetch()

            if time_keeper_thread is not None:
                end_thread_event.set()
                time_keeper_thread.join()

                kill_window_event = Event()
                end_thread_event = Event()

            if game_process is not None:
                game_process.terminate()
                game_process.wait()

        if m := re.match("/games/(.*)", page.route):
            if time_keeper_thread is None:
                def kill():
                    page.window_destroy()
                    if game_process is not None:
                        game_process.terminate()
                        game_process.wait()

                time_keeper_thread = Thread(target=time_keep, args=(kill_window_event, end_thread_event, kill))
                time_keeper_thread.start()

            num = int(m.group(1))

            nav = NavigationColumn(AllGameData())

            game_data = nav.gallery.control_groups[num]

            for it in nav.gallery.control_groups:
                if it.index == num:
                    nav.gallery.selected_control_group = it
                    break

            img_w = page.width / 10 * 7
            img_h = page.height - 200

            if nav.gallery.selected_control_group.screen_shot is not None:
                img_controller = ft.Image(
                    src=str(nav.gallery.selected_control_group.screen_shot.absolute()),
                    width=img_w,
                    height=img_h,
                    fit=ft.ImageFit.COVER,
                    border_radius=ft.border_radius.all(10),
                )
            else:
                img_controller = ft.Container(

                    bgcolor=ft.colors.GREY, width=img_w, height=img_h, border_radius=ft.border_radius.all(10),
                )

            def game_on_click(e):
                global game_process

                if game_process is not None and game_process.poll() is not None:
                    game_process = None

                if game_process is not None:
                    def close_dlg(e):
                        dlg.open = False
                        page.update()

                    dlg = ft.AlertDialog(
                        title=ft.Text("エラー"),
                        content=ft.Text("すでにゲームが起動しています。そちらを終了してから始めてください"),
                        actions=[
                            ft.TextButton("OK", on_click=close_dlg),
                        ],
                        actions_alignment=ft.MainAxisAlignment.END,
                        on_dismiss=lambda e: print("dialog dismissed!"),
                    )

                    page.dialog = dlg
                    dlg.open = True
                    page.update()

                    return

                game_process = subprocess.Popen([str(game_data.game_exe.absolute())])

            img_part = ft.Container(
                ft.Column(
                    [
                        ft.Container(
                            ft.Row(
                                [
                                    ft.Text(game_data.title, size=45),
                                    ft.Text(
                                        game_data.description,
                                        size=20,
                                        expand=True,
                                        overflow=ft.TextOverflow.CLIP,
                                    ),
                                    ft.Container(ft.Text("あそぶ", size=40), bgcolor=ft.colors.GREEN, ink_color=ft.colors.GREEN, on_click=game_on_click, padding=ft.Padding(20, 10, 20, 10), border_radius=ft.border_radius.all(10),)
                                ],
                            ),
                            border=ft.border.all(2),
                            border_radius=ft.border_radius.all(10),
                            padding=ft.Padding(20, 10, 10, 10),
                        ),
                        img_controller,
                    ],
                    width=img_w,
                ),
            )

            def on_keyboard(e: ft.KeyboardEvent):
                nav_items = nav.get_navigation_items()

                if e.key == "Arrow Down":
                    nav.select((num + 1) % len(nav_items))
                    nav.update_selected_item()
                elif e.key == "Arrow Up":
                    nav.select((num - 1) % len(nav_items))
                    nav.update_selected_item()
                elif e.key == "Enter":
                    game_on_click(e)

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
                                img_part,
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.START,
                            alignment=ft.MainAxisAlignment.START,
                        ),
                    ],
                )
            )

        page.update()

    def page_resized(e):
        nonlocal img_controller, img_part
        if img_controller is not None:
            img_controller.width = page.width / 10 * 7
            img_controller.height = page.height - 200
            img_part.width = img_controller.width

        page.update()

    def view_pop(e):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_resize = page_resized
    page.on_view_pop = view_pop

    page.go(page.route)

    def window_event_handler(e):
        if e.data == "close":
            page.window_destroy()
            if game_process is not None:
                game_process.terminate()
                game_process.wait()
                end_thread_event.set()

    page.window_prevent_close = True
    page.on_window_event = window_event_handler


if __name__ == "__main__":
    try:
        ft.app(main)
    finally:
        if game_process is not None:
            game_process.terminate()
            game_process.wait()
