import ast
import asyncio
import csv
import datetime
import importlib.util as ilu
import inspect
import json
import math
import os
import psutil
import re
import struct
import sys
import time
import warnings
import webbrowser
import xml.etree.ElementTree as ET
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path, PurePath
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import platform
import psycopg2
import pyodbc
import seaborn as sns
import subprocess
import sqlalchemy as sa
import threading
import tkinter as tk

from IPython.display import Markdown, display
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.gridspec import GridSpec
from PyPDF2 import PdfReader
from scipy.stats import kurtosis, norm, skew
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sqlalchemy import URL, Column, MetaData, Table, create_engine, func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from tkinter import filedialog, messagebox, ttk, Canvas
from tkinter.colorchooser import askcolor
from tkinter.scrolledtext import ScrolledText

from .pyswitch import Switch, switch


CONFIG_LANG = "en"
NORMAL_SIZE = (10, 6)
BIG_SIZE = (12, 8)
BG_COLOR = "#2d2d2d"
TEXT_COLOR = "#ffffff"
BTN_BG = "#3d3d3d"
HIGHLIGHT_COLOR = "#4e7cad"
CUSTOMGUI = False

def _custom_settings_(state: bool = False):
    global CUSTOMGUI
    try:
        CUSTOMGUI = state
    except Exception as e:
        print(f"Exception: {e}")

config = {"verbose": True, "default_timeout": 5, "counter": 0}


TRANSLATIONS = {}
_translations = {}

def _get_translation_path_(lang: str) -> Path:
    return Path(__file__).parent.parent / "lang" / f"{lang}.json"

def t(key: str, lang: str = None, return_raw: bool = False, **kwargs):
    
    if not key:
        return t("missing_translation_key").format(key=key)
    
    lang = lang or CONFIG_LANG
    
    entry = _translations.get(key, {})
    
    if isinstance(entry, str):
        translated = entry
    else:
        translated = entry.get(lang, f"[{key}]")
    
    if return_raw:
        return translated
    
    if kwargs:
        if isinstance(translated, dict) and "template" in translated:
            return translated["template"].format(**kwargs)
        elif isinstance(translated, str):
            try:
                return translated.format(**kwargs)
            except KeyError:
                return translated
    
    return translated

def load_user_translations(lang_path: str = "lang.json"):
    global _translations

    user_translations = {}
    path = Path(lang_path)

    if path.is_file():
        try:
            with open(path, "r", encoding="utf-8") as f:
                user_translations = json.load(f)
        except Exception as e:
            print(f"Warning: Error loading user translations: {str(e)}")

    _translations = TRANSLATIONS.copy()
    _translations.update(user_translations)

__LANGUAGES__ = [
    "af", "sq", "am", "ar", "hy", "as", "ay", "az", "bm", "eu", "be", "bn", "bho", 
    "bs", "bg", "ca", "ceb", "ny", "zh", "co", "hr", "cs", "da", "dv", 
    "doi", "nl", "en", "eo", "et", "ee", "tl", "fi", "fr", "fy", "gl", "ka", "de", 
    "el", "gn", "gu", "ht", "ha", "haw", "iw", "hi", "hmn", "hu", "is", "ig", "ilo", 
    "id", "ga", "it", "ja", "jw", "kn", "kk", "km", "rw", "gom", "ko", "kri", "ku", 
    "ckb", "ky", "lo", "la", "lv", "ln", "lt", "lg", "lb", "mk", "mai", "mg", "ms", 
    "ml", "mt", "mi", "mr", "lus", "mn", "my", "ne", "no", "or", "om", 
    "ps", "fa", "pl", "pt", "pa", "qu", "ro", "ru", "sm", "sa", "gd", "nso", "sr", 
    "st", "sn", "sd", "si", "sk", "sl", "so", "es", "su", "sw", "sv", "tg", "ta", 
    "tt", "te", "th", "ti", "ts", "tr", "tk", "ak", "uk", "ur", "ug", "uz", "vi", 
    "cy", "xh", "yi", "yo", "zu"
]

def _load_translations_(lang_to_load: str):
    """Carga las traducciones para un idioma específico"""
    global TRANSLATIONS, _translations
    
    translations_path = _get_translation_path_(lang_to_load)
    if translations_path.exists():
        try:
            with open(translations_path, encoding="utf-8") as f:
                TRANSLATIONS = json.load(f)
                _translations = TRANSLATIONS.copy()
                return True
        except Exception as e:
            print(f"Warning: Error loading translations for {lang_to_load}: {str(e)}")
            return False
    else:
        print(f"Warning: Translations not found for language: {lang_to_load}")
        return False

def set_language(lang: str):
    global CONFIG_LANG
    if TRANSLATIONS and lang not in __LANGUAGES__:
        raise ValueError(f"Language '{lang}' is not available.")
    CONFIG_LANG = lang
    _load_translations_(lang_to_load=lang)


TRANSLATIONS_PATH = _get_translation_path_(CONFIG_LANG)
if TRANSLATIONS_PATH.exists():
    with open(TRANSLATIONS_PATH, encoding="utf-8") as f:
        TRANSLATIONS = json.load(f)
        _translations = TRANSLATIONS.copy()
else:
    print("Warning: Default translations not found")


def _load_gui_config_():
    """Carga la configuración de la GUI desde un archivo JSON."""
    config_path = os.path.join(os.getcwd(), "gui_config.json")
    default_config = {
        "theme": "dark",
        "custom_colors": {
            "bg_color": "#2b2b2b",
            "text_color": "#ffffff",
            "btn_bg": "#3c3f41",
            "highlight_color": "#4e5254",
            "preview_bg": "#f0f0f0"
        }
    }
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                # Migrar configuraciones antiguas
                if "bg_color" in user_config and "theme" not in user_config:
                    user_config = {
                        "theme": "custom",
                        "custom_colors": user_config
                    }
                    _save_gui_config_(user_config)
                return {**default_config, **user_config}
    except:
        pass
    
    return default_config

def _save_gui_config_(config):
    """Guarda la configuración de la GUI en un archivo JSON."""
    config_path = os.path.join(os.getcwd(), "gui_config.json")
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error guardando configuración: {str(e)}")

def format_number(
    value: float, use_decimals: bool = True, decimals: int = 2, percent: bool = False
) -> str:
    if value is None:
        return "N/A"
    
    try:
        if isinstance(value, float) and np.isnan(value):
            return "N/A"
    except NameError:
        pass

    if percent:
        value *= 100

    if use_decimals:
        formatted = f"{value:,.{decimals}f}"
    else:
        formatted = f"{int(round(value)):,}"

    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")

    if percent:
        formatted += "%"

    return formatted


def is_jupyter_notebook():
    try:
        from IPython import get_ipython

        ip = get_ipython()
        if ip is None:
            return False

        shell_name = ip.__class__.__name__
        if shell_name == "ZMQInteractiveShell":
            return True
        else:
            return False
    except ImportError:
        return False

IN_JUPYTER = is_jupyter_notebook()


REGISTRY = {}

def register(name=None):
    """Decorator to register a function or class in the global REGISTRY."""
    def wrapper(fn):
        key = name or fn.__name__
        REGISTRY[key] = fn
        return fn
    return wrapper


def show_gui_popup(
    title, content, fig=None, plot_function=None, plot_args=None, 
    preview_mode=False, export_callback=None, table_data=None, is_debug: bool = False
):

    translations = {
        "copy": "copy",
        "close": "close", 
        "save": "save",
        "content": "content",
        "preview": "preview",
        "error_in_gui": "error_in_gui",
        "export": "export",
        "light_theme": "light_theme",
        "dark_theme": "dark_theme",
        "settings": "settings",
        "custom_inactive": "custom_inactive",
        "custom_active": "custom_active"
    }
    

    copy_text = Switch(translations["copy"])(
        lambda x: "copy", lambda: t("copy"),
        "default", lambda: "Copy"
    )
    
    close_text = Switch(translations["close"])(
        lambda x: "close", lambda: t("close"),
        "default", lambda: "Close"
    )
    
    save_text = Switch(translations["save"])(
        lambda x: "save", lambda: t("save"),
        "default", lambda: "Save"
    )
    
    content_text = Switch(translations["content"])(
        lambda x: "content", lambda: t("content"),
        "default", lambda: "Content"
    )
    
    preview_text = Switch(translations["preview"])(
        lambda x: "preview", lambda: t("preview"),
        "default", lambda: "Preview"
    )
    
    gui_error_text = Switch(translations["error_in_gui"])(
        lambda x: "error_in_gui", lambda: t("error_in_gui"),
        "default", lambda: "GUI Error"
    )
    
    export_text = Switch(translations["export"])(
        lambda x: "export", lambda: t("export"),
        "default", lambda: "Export"
    )
    
    light_theme_text = Switch(translations["light_theme"])(
        lambda x: "light_theme", lambda: t("light_theme"),
        "default", lambda: "Light Theme"
    )
    
    dark_theme_text = Switch(translations["dark_theme"])(
        lambda x: "dark_theme", lambda: t("dark_theme"),
        "default", lambda: "Dark Theme"
    )

    custom_inactive_text = Switch(translations["custom_inactive"])(
        lambda x: "custom_inactive", lambda: t("custom_inactive"),
        "default", lambda: "Custom Color Disable"
    )

    custom_active_text = Switch(translations["custom_active"])(
        lambda x: "custom_active", lambda: t("custom_active"),
        "default", lambda: "Custom Color Enable"
    )
    
    settings_text = Switch(translations["settings"])(
        lambda x: "settings", lambda: t("settings"),
        "default", lambda: "Settings"
    )


    config = _load_gui_config_()
    theme = config.get("theme", "dark")
    custom_colors = config.get("custom_colors", {})
    
    if theme == "light":
        BG_COLOR = "#ffffff"
        TEXT_COLOR = "#000000"
        BTN_BG = "#f0f0f0"
        HIGHLIGHT_COLOR = "#e0e0e0"
        PREVIEW_BG = "#f0f0f0"
    elif theme == "custom":
        BG_COLOR = custom_colors.get("bg_color", "#2b2b2b")
        TEXT_COLOR = custom_colors.get("text_color", "#ffffff")
        BTN_BG = custom_colors.get("btn_bg", "#3c3f41")
        HIGHLIGHT_COLOR = custom_colors.get("highlight_color", "#4e5254")
        PREVIEW_BG = custom_colors.get("preview_bg", "#f0f0f0")
    else:  # dark theme por defecto
        BG_COLOR = "#2b2b2b"
        TEXT_COLOR = "#ffffff"
        BTN_BG = "#3c3f41"
        HIGHLIGHT_COLOR = "#4e5254"
        PREVIEW_BG = "#f0f0f0"


    if IN_JUPYTER:
        mpl.use("module://ipykernel.pylab.backend_inline")
    else:
        mpl.use("Agg")

    current_fig = fig
    if plot_function is not None:
        if plot_args is None:
            plot_args = {}
        current_fig = plot_function(**plot_args)

    if preview_mode:
        if current_fig is not None:
            current_fig.patch.set_facecolor(PREVIEW_BG)
            for ax in current_fig.get_axes():
                ax.set_facecolor(PREVIEW_BG)
                ax.title.set_color(TEXT_COLOR)
                ax.xaxis.label.set_color(TEXT_COLOR)
                ax.yaxis.label.set_color(TEXT_COLOR)
                ax.tick_params(colors=TEXT_COLOR)
                for spine in ax.spines.values():
                    spine.set_color(TEXT_COLOR)
        return current_fig


    window = tk.Tk()
    window.title(title)
    window.state("zoomed")
    window.configure(bg=BG_COLOR)


    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Dark.TFrame", background=BG_COLOR)
    style.configure(
        "Dark.TLabel", background=BG_COLOR, foreground=TEXT_COLOR, font=("Consolas", 10)
    )
    style.configure(
        "Dark.TButton", background=BTN_BG, foreground=TEXT_COLOR, borderwidth=1
    )
    style.map("Dark.TButton", background=[("active", HIGHLIGHT_COLOR)])


    window.grid_rowconfigure(0, weight=1)
    window.grid_columnconfigure(0, weight=1)

    main_frame = ttk.Frame(window, style="Dark.TFrame")
    main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    main_frame.grid_rowconfigure(0, weight=1)
    main_frame.grid_columnconfigure(0, weight=1)


    notebook = ttk.Notebook(main_frame)
    notebook.grid(row=0, column=0, sticky="nsew", pady=(0, 10))


    doc_frame = ttk.Frame(notebook, style="Dark.TFrame")
    notebook.add(doc_frame, text=content_text)

    text_area = ScrolledText(
        doc_frame,
        wrap=tk.WORD,
        font=("Consolas", 10),
        bg=BG_COLOR,
        fg=TEXT_COLOR,
        insertbackground=TEXT_COLOR,
        selectbackground=HIGHLIGHT_COLOR,
    )
    text_area.pack(expand=True, fill="both", padx=5, pady=5)
    text_area.insert(tk.END, content)
    text_area.config(state="disabled")


    current_fig = fig
    canvas = None

    if fig is not None or plot_function is not None:

        graph_frame = ttk.Frame(notebook, style="Dark.TFrame")
        notebook.add(graph_frame, text=preview_text)

        if plot_function is not None:
            if plot_args is None:
                plot_args = {}
            current_fig = plot_function(**plot_args)

        if current_fig is not None:
            current_fig.patch.set_facecolor(PREVIEW_BG)
            for ax in current_fig.get_axes():
                ax.set_facecolor(PREVIEW_BG)
                ax.title.set_color("black")
                ax.xaxis.label.set_color("black")
                ax.yaxis.label.set_color("black")
                ax.tick_params(colors="black")
                for spine in ax.spines.values():
                    spine.set_color("black")

            canvas = FigureCanvasTkAgg(current_fig, master=graph_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)


    def copy_to_clipboard():
        window.clipboard_clear()
        window.clipboard_append(content)
        window.update()

    def save_image():
        if current_fig is not None:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("JPEG files", "*.jpg"),
                    ("All files", "*.*"),
                ],
            )
            if filepath:
                current_fig.savefig(filepath, bbox_inches="tight", dpi=300)

    def export_data():
        if export_callback:
            format_menu = tk.Menu(window, tearoff=0)
            formats = ["csv", "json", "excel", "xml", "sql", "parquet", "html"]
            
            for fmt in formats:
                format_menu.add_command(
                    label=fmt.upper(), 
                    command=lambda f=fmt: export_callback(f)
                )
            
            export_btn = btn_frame.winfo_children()[2]
            x = export_btn.winfo_rootx()
            y = export_btn.winfo_rooty() + export_btn.winfo_height()
            format_menu.post(x, y)

    def toggle_theme():
        config = _load_gui_config_()
        current_theme = config.get("theme", "dark")
        new_theme = "light" if current_theme == "dark" else "dark"
        config["theme"] = new_theme
        _save_gui_config_(config)
        
        # Recargar la ventana
        window.destroy()
        show_gui_popup(
            title, content, fig, plot_function, plot_args, 
            False, export_callback, table_data
        )

    def toggle_custom():
        config = _load_gui_config_()
        current_theme = config.get("theme", "dark")
        
        if current_theme == "custom":
            # Volver al tema oscuro si estaba en custom
            config["theme"] = "dark"
        else:
            # Activar tema personalizado
            config["theme"] = "custom"
            # Si no hay colores personalizados, usar los actuales como base
            if "custom_colors" not in config or not config["custom_colors"]:
                config["custom_colors"] = {
                    "bg_color": BG_COLOR,
                    "text_color": TEXT_COLOR,
                    "btn_bg": BTN_BG,
                    "highlight_color": HIGHLIGHT_COLOR,
                    "preview_bg": PREVIEW_BG
                }
        
        _save_gui_config_(config)
        
        # Recargar la ventana
        window.destroy()
        show_gui_popup(
            title, content, fig, plot_function, plot_args, 
            False, export_callback, table_data
        )

    def open_settings():
        settings_window = tk.Toplevel(window)
        settings_window.title("Configuración de GUI")
        settings_window.geometry("400x500")
        settings_window.configure(bg=BG_COLOR)
        
        # Centrar la ventana de configuración
        settings_window.update_idletasks()
        x = window.winfo_x() + (window.winfo_width() // 2) - (400 // 2)
        y = window.winfo_y() + (window.winfo_height() // 2) - (500 // 2)
        settings_window.geometry(f"400x500+{x}+{y}")
        
        ttk.Label(settings_window, text="Configuración de colores", style="Dark.TLabel").pack(pady=10)
        
        colors_frame = ttk.Frame(settings_window, style="Dark.TFrame")
        colors_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Función para crear selectores de color
        def create_color_selector(parent, label, default_color, row):
            ttk.Label(parent, text=label, style="Dark.TLabel").grid(row=row, column=0, sticky="w", padx=5, pady=5)
            color_var = tk.StringVar(value=default_color)
            color_label = ttk.Label(parent, background=default_color, width=10)
            color_label.grid(row=row, column=1, padx=5, pady=5)
            
            def choose_color():
                # Obtener la posición del botón que activó el selector
                button_widget = settings_window.focus_get()
                if button_widget:
                    x_pos = button_widget.winfo_rootx() + button_widget.winfo_width() + 10
                    y_pos = button_widget.winfo_rooty()
                else:
                    # Posición por defecto si no se puede obtener la del botón
                    x_pos = settings_window.winfo_rootx() + settings_window.winfo_width() + 10
                    y_pos = settings_window.winfo_rooty()
                    
                color = askcolor(
                    color=color_var.get(), 
                    title=f"Elegir color para {label}",
                    parent=settings_window
                )[1]
                
                if color:
                    color_var.set(color)
                    color_label.configure(background=color)
            
            color_button = ttk.Button(parent, text="Seleccionar", command=choose_color, style="Dark.TButton")
            color_button.grid(row=row, column=2, padx=5, pady=5)
            
            return color_var
        
        # Crear selectores para cada color
        bg_color_var = create_color_selector(colors_frame, "Color de fondo", custom_colors.get("bg_color", "#2b2b2b"), 0)
        text_color_var = create_color_selector(colors_frame, "Color de texto", custom_colors.get("text_color", "#ffffff"), 1)
        btn_bg_var = create_color_selector(colors_frame, "Color de botones", custom_colors.get("btn_bg", "#3c3f41"), 2)
        highlight_color_var = create_color_selector(colors_frame, "Color de resaltado", custom_colors.get("highlight_color", "#4e5254"), 3)
        preview_bg_var = create_color_selector(colors_frame, "Color de previsualización", custom_colors.get("preview_bg", "#f0f0f0"), 4)
        
        def save_custom_colors():
            config = _load_gui_config_()
            config["custom_colors"] = {
                "bg_color": bg_color_var.get(),
                "text_color": text_color_var.get(),
                "btn_bg": btn_bg_var.get(),
                "highlight_color": highlight_color_var.get(),
                "preview_bg": preview_bg_var.get()
            }
            config["theme"] = "custom"
            _save_gui_config_(config)
            settings_window.destroy()
            window.destroy()
            show_gui_popup(
                title, content, fig, plot_function, plot_args, 
                False, export_callback, table_data
            )
        
        ttk.Button(settings_window, text="Guardar", command=save_custom_colors, style="Dark.TButton").pack(pady=10)
        
        # Hacer que la ventana de configuración sea modal
        settings_window.transient(window)
        settings_window.grab_set()
        settings_window.focus_set()
        
        # Esperar a que la ventana se cierre
        window.wait_window(settings_window)
        
    def on_close():
        if is_debug:
            print("DEBUG: Cerrar ventana")
        if current_fig is not None:
            plt.close(current_fig)
        window.destroy()


    btn_frame = ttk.Frame(main_frame, style="Dark.TFrame")
    btn_frame.grid(row=1, column=0, sticky="ew", pady=(0, 5))

    # Configurar 6 columnas para acomodar todos los botones
    btn_frame.grid_columnconfigure(0, weight=1)
    btn_frame.grid_columnconfigure(1, weight=1)
    btn_frame.grid_columnconfigure(2, weight=1)
    btn_frame.grid_columnconfigure(3, weight=1)
    btn_frame.grid_columnconfigure(4, weight=1)
    btn_frame.grid_columnconfigure(5, weight=1)


    action_btn = ttk.Button(
        btn_frame, text=copy_text, command=copy_to_clipboard, style="Dark.TButton"
    )
    action_btn.grid(row=0, column=0, padx=5, sticky="w")


    if export_callback:
        export_btn = ttk.Button(
            btn_frame, text=export_text, command=export_data, style="Dark.TButton"
        )
        export_btn.grid(row=0, column=1, padx=5)
    else:
        # Espaciador si no hay botón de exportación
        ttk.Frame(btn_frame, width=0).grid(row=0, column=1)

    # Botón de tema claro/oscuro
    theme_btn_text = light_theme_text if theme == "dark" else dark_theme_text
    theme_btn = ttk.Button(
        btn_frame, text=theme_btn_text, command=toggle_theme, style="Dark.TButton"
    )
    
    # Botón de custom
    custom_btn_text = custom_active_text if theme == "custom" else custom_inactive_text
    custom_btn = ttk.Button(
        btn_frame, text=custom_btn_text, command=toggle_custom, style="Dark.TButton"
    )
    
    # Colocar botones según el tema actual
    if theme == "custom":
        custom_btn.grid(row=0, column=2, padx=5)
        # Ocultar botón de tema cuando está en modo custom
        theme_btn.grid_forget()
    else:
        theme_btn.grid(row=0, column=2, padx=5)
        custom_btn.grid(row=0, column=3, padx=5)


    settings_btn = ttk.Button(
        btn_frame, text=settings_text, command=open_settings, style="Dark.TButton"
    )
    settings_btn.grid(row=0, column=4, padx=5)


    close_btn = ttk.Button(
        btn_frame, text=close_text, command=on_close, style="Dark.TButton"
    )
    close_btn.grid(row=0, column=5, padx=5, sticky="e")


    def on_tab_change(event):
        tab_action = Switch(notebook.index("current"))(
            lambda x: 1, lambda: {"action_text": save_text, "action_command": save_image},
            "default", lambda: {"action_text": copy_text, "action_command": copy_to_clipboard}
        )
        action_btn.config(text=tab_action["action_text"], command=tab_action["action_command"])

    notebook.bind("<<NotebookTabChanged>>", on_tab_change)

    def _jup_func_():
        import ipywidgets as widgets

        output = widgets.Output(),
        display(output),

        def run_in_jupyter():
            with output:
                try:
                    window.mainloop()
                except Exception as e:
                    print(f"{gui_error_text}: {str(e)}")

        return window.after(100, run_in_jupyter)


    if fig is not None or plot_function is not None:
        if notebook.index("current") == 1:
            action_btn.config(text=save_text, command=save_image)


    if IN_JUPYTER:
         _jup_func_()
    else:
        window.mainloop()

    if current_fig is not None:
        plt.close(current_fig)

def show_alert_popup(type: str, message: str, detail: str = None):
    """Muestra un popup de advertencia o error con colores predefinidos."""


    type = type.strip().lower()
    if type not in ("warning", "error"):
        raise ValueError("type debe ser 'warning' o 'error'")


    if type == "warning":
        bg_color = "#ffd9a3cc"   # naranja muy claro
        fg_color = "#663c00"   # marrón/naranja oscuro
        accent_color = "#ff9800"
        title = "Warning"
    else:
        bg_color = "#ee978d"   # rojo claro
        fg_color = "#611a15"   # rojo oscuro
        accent_color = "#f44336"
        title = "Error"


    win = tk.Toplevel()
    win.title(title)
    win.configure(bg=bg_color)
    win.resizable(False, False)

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Custom.TButton", background=accent_color, foreground="white")
    style.map("Custom.TButton", background=[("active", fg_color)])


    lbl_msg = ttk.Label(win, text=message, background=bg_color, foreground=fg_color, font=("Segoe UI", 11, "bold"))
    lbl_msg.pack(padx=15, pady=(15,5), anchor="w")


    btn_frame = ttk.Frame(win)
    btn_frame.pack(fill="x", padx=10, pady=(10, 10))


    def copy_message():
        win.clipboard_clear()
        win.clipboard_append(message)
        win.update()

    btn_copy = ttk.Button(btn_frame, text="Copiar mensaje", command=copy_message, style="Custom.TButton")
    btn_copy.pack(side="left", padx=5)


    def close_win():
        win.destroy()

    btn_close = ttk.Button(btn_frame, text="Cerrar", command=close_win, style="Custom.TButton")
    btn_close.pack(side="right", padx=5)


    if detail:
        detail_frame = ttk.Frame(win)
        detail_frame.pack(fill="both", expand=True, padx=10, pady=(5,10))


        def toggle_detail():
            if not hasattr(toggle_detail, "shown"):
                toggle_detail.shown = False

            if not toggle_detail.shown:
                text_detail.pack(fill="both", expand=True, pady=(5,5))
                btn_copy_detail.pack(side="left", padx=5)
                btn_detail.config(text="Ocultar detalle")
            else:
                text_detail.pack_forget()
                btn_copy_detail.pack_forget()
                btn_detail.config(text="Mostrar detalle")

            toggle_detail.shown = not toggle_detail.shown

        btn_detail = ttk.Button(detail_frame, text="Mostrar detalle", command=toggle_detail, style="Custom.TButton")
        btn_detail.pack(fill="x", pady=(0,5))


        text_detail = ScrolledText(detail_frame, wrap="word", height=8, background="white", foreground="black")
        text_detail.insert("1.0", detail)
        text_detail.configure(state="disabled")


        def copy_detail():
            win.clipboard_clear()
            win.clipboard_append(detail)
            win.update()

        btn_copy_detail = ttk.Button(detail_frame, text="Copiar detalle", command=copy_detail, style="Custom.TButton")


    win.update_idletasks()
    w = win.winfo_width()
    h = win.winfo_height()
    x = (win.winfo_screenwidth() // 2) - (w // 2)
    y = (win.winfo_screenheight() // 2) - (h // 2)
    win.geometry(f"+{x}+{y}")

    win.transient()   # Se mantiene encima
    win.grab_set()    # Bloquea interacción con otras ventanas
    win.mainloop()

def show_yesno_popup(title, message):
        """Muestra un popup con botones Sí/No"""
        root = tk.Tk()
        root.withdraw()  # Ocultar ventana principal
        root.attributes('-topmost', True)  # Traer al frente
        result = messagebox.askyesno(t(title), t(message))
        root.destroy()
        return result
