# Huez

A unified color scheme solution for Python visualization libraries.

## Installation

```bash
pip install huez
```

## Quick Start

```python
import huez as hz
import matplotlib.pyplot as plt

# Apply a color scheme
hz.use("scheme-1")

# Create plots with automatic coloring
plt.plot(x, y1, label='Data 1')
plt.plot(x, y2, label='Data 2')
plt.legend()
plt.show()
```

## Supported Libraries

- **Matplotlib** - Automatic color cycling
- **Seaborn** - Consistent palette integration  
- **plotnine** - Native ggplot2-style coloring
- **Altair** - Theme-based color schemes
- **Plotly** - Template-based styling

## Built-in Schemes

- `scheme-1` - Nature journal style (NPG colors)
- `scheme-2` - Science journal style (AAAS colors)
- `scheme-3` - NEJM medical journal style
- `scheme-4` - Lancet journal style
- `scheme-5` - JAMA journal style

## Custom Configuration

Create a YAML config file:

```yaml
version: 1
default_scheme: my_style
schemes:
  my_style:
    title: "My Custom Style"
    fonts: { family: "Arial", size: 11 }
    palettes:
      discrete: "npg"
      sequential: "viridis"
      diverging: "coolwarm"
      cyclic: "twilight"
    figure: { dpi: 300 }
    style: { grid: "y", legend_loc: "best", spine_top_right_off: true }
```

Load and use:

```python
hz.load_config("my_config.yaml")
hz.use("my_style")
```

## License

MIT License - see [LICENSE](LICENSE) file for details.
