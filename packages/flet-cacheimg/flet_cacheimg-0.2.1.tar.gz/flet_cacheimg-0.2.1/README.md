# flet-cacheimg
Cacheimg and CacheCircleAvatar control for Flet.

### Warning
Images will only be cached in built packages.
 ```
flet build ...
```

If you run project via 
```
flet run
```
those controls will act exactly the same as basic ```ft.Image``` and ```ft.CircleAvatar```.  
This is limitation of the current Flet version (0.28.3).

## Usage

```python
import flet as ft
from flet_cacheimg import CacheImage, CacheCircleAvatar


def main(page: ft.Page):
    page.add(
        CacheImage(
            src="https://flet.dev/img/logo.svg",
            width=150,
            height=150,
            tooltip="Cached image",
            opacity=0.9,
        )
    )
    page.add(
        CacheCircleAvatar(
            radius=24,
            foreground_image_src='https://flet.dev/img/logo.svg',
        )
    )
    page.add(
        ft.CircleAvatar(
            radius=20,
            content=CacheImage(
                src='https://flet.dev/img/logo.svg',
                width=40,
                height=40,
                fit=ft.ImageFit.COVER,
            ),
        )
    )


ft.app(main)
```

## Installation

Add dependency to `pyproject.toml` of your Flet app:

* **Git dependency**

Link to git repository:

```
dependencies = [
  "flet-cacheimg @ git+https://github.com/ReYaNOW/flet-cacheimg",
  "flet>=0.28.3",
]
```

* **PyPi dependency**  

If the package is published on pypi.org:

```
dependencies = [
  "flet-cacheimg",
  "flet>=0.28.3",
]
```

Build your app:
```
flet build apk -v
```
