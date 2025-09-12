# flet-extended-interactive-viewer
[![PyPI version](https://img.shields.io/pypi/v/flet-extended-interactive-viewer.svg)](https://pypi.org/project/flet-extended-interactive-viewer/)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Flet](https://img.shields.io/badge/Flet-0.28.3+-green.svg)](https://flet.dev)
[![License](https://img.shields.io/github/license/PraiseTheDarkFlo/flet-extended-interactive-viewer.svg)](https://github.com/PraiseTheDarkFlo/flet-extended-interactive-viewer/blob/master/LICENSE)
> **Flet-Extended-Interactive-Viewer is a [Flet](https://flet.dev/) control that provides multiple customization options for displaying two-dimensional content.**

## 🌟 Highlights

- **XY Scrollbars:** Synchronized scrollbars for the InteractiveViewer.
- **XY Scrollbar Options:** Easy to customize the experience e.g. you can disable the interaction with the scrollbars or disable Y scrollbars.
- **Panning:** Supports panning like `ft.InteractiveViewer`, with synchronized scrollbars. You can also disable panning to use only the scrollbars.
- **Zoom:** Zoom with the mouse/touchpad or via a function call. When zooming via a function call, the zoom can be limited to the content size.
- **Transformation data:** Provides access to the transformation applied to the content.

## ℹ️ Overview

This extension was developed as part of a Bachelor Thesis, supervised by [Erik Kubaczka](https://github.com/ERIK-KE) at the [Self-Organizing Systems Lab](https://www.bcs.tu-darmstadt.de/welcome/index.en.jsp) of the Technical University Darmstadt. FletExtendedInteractiveViewer is a powerful control for [Flet](https://flet.dev/) which enables the user to customize an interactive content view experience.

## 📖 Documentation

Documentation to this package can be found [here](https://PraiseTheDarkFlo.github.io/flet-extended-interactive-viewer/).

## 🚀 Example
### Demo
![Example](https://github.com/PraiseTheDarkFlo/flet-extended-interactive-viewer/blob/master/docs/gifs/usage_extended_interactive_viewer.gif?raw=true)

### Code
```python
import flet as ft

from flet_extended_interactive_viewer import FletExtendedInteractiveViewer


def main(page: ft.Page):
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    text = ft.Text("MOVE ME",size=50)

    def on_click(ex:FletExtendedInteractiveViewer=None,text_move:ft.Text=None):
        if ex.pan_enabled:
            ex.pan_enabled = False
            text_move.value = "PAN DISABLED"
        else:
            ex.pan_enabled = True
            text_move.value = "MOVE ME"
        ex.update()
        text_move.update()

    def get_transformation_click(ex:FletExtendedInteractiveViewer=None,text_update:ft.Text=None):
        x, y, scale = ex.get_transformation_data()
        text_update.value = f"offset_x={round(x)}, offset_y={round(y)}, scale={scale}"
        text_update.update()
    def toggle_scroll_x(ex:FletExtendedInteractiveViewer=None):
        ex.x_scroll_enabled = not ex.x_scroll_enabled
        ex.update()
    def toggle_scroll_y(ex: FletExtendedInteractiveViewer = None):
        ex.y_scroll_enabled = not ex.y_scroll_enabled
        ex.update()

    def toggle_interactive(ex: FletExtendedInteractiveViewer = None):
        ex.interactive_scroll_enabled = not ex.interactive_scroll_enabled
        ex.update()
        
    extended = FletExtendedInteractiveViewer(
                    content=ft.Container(text,width=900,height=800,gradient=ft.LinearGradient(
                        begin=ft.alignment.top_left,
                        end=ft.alignment.bottom_right,
                        colors=[ft.Colors.PINK, ft.Colors.ORANGE_700],
                    )),
                    width=400, height=250,constrained=False,pan_enabled=True,over_zoom_enabled=False,
                )
    
    text_x_y_scale = ft.Text("offset_x=?, offset_y=?, scale=?")
    page.add(ft.Row([
        ft.Column([text_x_y_scale,
                extended,
                   ft.Row([ft.Button("toggle pan",on_click=lambda e,ex=extended,text_move=text:on_click(ex,text_move)),ft.Button("toggle interactive_scroll_bar",on_click=lambda e,ex=extended:toggle_interactive(ex))]),ft.Row([ft.Button("toggle scroll_bar_x",on_click=lambda e,ex=extended:toggle_scroll_x(ex)),ft.Button("toggle scroll_bar_y",on_click=lambda e,ex=extended:toggle_scroll_y(ex))]),
                   ft.Row([ft.Button("reset",on_click=lambda e,ex=extended:ex.reset(400)),ft.Button("zoom in",on_click=lambda e,ex=extended:ex.zoom(1.25)),ft.Button("zoom out",on_click=lambda e,ex=extended:ex.zoom(0.75))]),
                   ft.Row([ft.Button("get_transformation",on_click=lambda e, ex=extended, x_y_scale=text_x_y_scale: get_transformation_click(ex,text_x_y_scale)),ft.Button("set_transformation(-100.0,-100.0,1.0)",on_click=lambda e,ex=extended:ex.set_transformation_data(offset_x=-100.0,offset_y=-100.0,scale=1.0))])
                   ],alignment=ft.MainAxisAlignment.CENTER)],alignment=ft.MainAxisAlignment.CENTER),

    )


ft.app(main)
```

## ⬇️ Installation


To install the `flet-extended-interactive-viewer` package:

- Using `pip`:

    ```bash
    pip install flet-extended-interactive-viewer
    ```
    After this, you will have to manually add this package to your `requirements.txt` or `pyproject.toml`.

Build your app:
- Using Linux:

    ```bash
    flet build linux -v
    ```
- Using Mac:

    ```bash
    flet build macos -v
    ```
- Using Windows:

    ```bash
    flet build windows -v
    ```

## 📝 License

This project is licensed under the **MIT license** – see the [LICENSE](LICENSE) file for details.

