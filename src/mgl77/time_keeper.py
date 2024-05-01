import time
from abc import ABC
from typing import Optional

import flet as ft

from pathlib import Path
from pydantic import BaseModel, ValidationError
import tomllib

import subprocess

from multiprocessing import Event

import re

from mgl77.fetch import fetch
from mgl77.game_data import NavigationColumn, AllGameData

import tkinter as tk
from tkinter import messagebox


WARNING_SECS = 5 * 60
KILL_SECS = 10 * 60

game_process: Optional[subprocess.Popen] = None

def time_keep(kill_window_event: Event, end_thread_event: Event, kill_func):
    done_warning = False
    done_kill = False

    start = time.time()

    while True:
        if end_thread_event.is_set():
            break

        if (not done_warning) and time.time() - start > WARNING_SECS:
            root = tk.Tk()
            root.withdraw()  # メインウィンドウを表示しない
            root.attributes('-topmost', True)  # ウィンドウを最前面にする

            messagebox.showwarning("警告", "そろそろ交代してください！ご協力をお願いします。")

            done_warning = True

        if (not done_kill) and time.time() - start > KILL_SECS:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)

            messagebox.showerror("警告", "長く遊びすぎなので、強制的に終了します。展示を一回出てからまた来てね")

            kill_window_event.set()
            done_kill = True
            kill_func()
            break
