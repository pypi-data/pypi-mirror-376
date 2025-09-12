"""
Built-in default configurations for huez.
"""

from ..config import Config, Scheme, FontConfig, PalettesConfig, FigureConfig, StyleConfig


def get_default_config() -> Config:
    """Get the built-in default configuration."""
    return Config(
        schemes={
            "scheme-1": Scheme(
                title="Nature Journal Style",
                fonts=FontConfig(family="DejaVu Sans", size=9),
                palettes=PalettesConfig(discrete="npg", sequential="viridis", diverging="vik", cyclic="twilight"),
                figure=FigureConfig(dpi=300),
                style=StyleConfig(grid="y", legend_loc="best", spine_top_right_off=True)
            ),
            "scheme-2": Scheme(
                title="Science Journal Style",
                fonts=FontConfig(family="DejaVu Sans", size=9),
                palettes=PalettesConfig(discrete="aaas", sequential="plasma", diverging="coolwarm", cyclic="twilight"),
                figure=FigureConfig(dpi=300),
                style=StyleConfig(grid="both", legend_loc="upper right", spine_top_right_off=True)
            ),
            "scheme-3": Scheme(
                title="NEJM Style",
                fonts=FontConfig(family="DejaVu Sans", size=9),
                palettes=PalettesConfig(discrete="nejm", sequential="cividis", diverging="RdBu", cyclic="twilight"),
                figure=FigureConfig(dpi=300),
                style=StyleConfig(grid="y", legend_loc="best", spine_top_right_off=False)
            ),
            "scheme-4": Scheme(
                title="Lancet Style",
                fonts=FontConfig(family="DejaVu Sans", size=9),
                palettes=PalettesConfig(discrete="lancet", sequential="viridis", diverging="RdYlBu", cyclic="twilight"),
                figure=FigureConfig(dpi=300),
                style=StyleConfig(grid="y", legend_loc="best", spine_top_right_off=True)
            ),
            "scheme-5": Scheme(
                title="JAMA Style",
                fonts=FontConfig(family="DejaVu Sans", size=9),
                palettes=PalettesConfig(discrete="jama", sequential="plasma", diverging="Spectral", cyclic="twilight"),
                figure=FigureConfig(dpi=300),
                style=StyleConfig(grid="y", legend_loc="best", spine_top_right_off=True)
            )
        }
    )
