<p align="center">
  <img src="https://raw.githubusercontent.com/hzacode/huez/main/logo.png" alt="Huez Logo" width="200"/>
</p>

<h1 align="center">Huez</h1>

<p align="center">
  <em>A Unified Color Scheme Solution for Python Visualization</em>
  <br />
  <a href="#features">✨ Features</a> •
  <a href="#installation">🚀 Quick Start</a> •
  <a href="#usage">📚 Libraries</a> •
  <a href="#schemes">🎨 Schemes</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.7+-blue.svg" alt="Python Version"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License"/>
  <img src="https://img.shields.io/badge/status-pre--alpha-red.svg" alt="Status"/>
</p>

<p align="center">
  <em>"Good visualizations should not be ruined by bad color schemes."</em>
</p>

<div align="center">

**Huez** is a unified Python visualization color scheme solution that instantly upgrades your charts from amateur to professional publication-quality. 

*True one-line code, automatic coloring for all libraries!*

</div>

## ✨ Features

- 🚀 **True Automatic Coloring**: All major libraries support native syntax automatic coloring, no manual color specification needed
- 🎯 **Perfect Cross-Library Consistency**: Matplotlib, Seaborn, plotnine, Altair, Plotly completely unified color experience
- 🎨 **Rich Built-in & Custom Schemes**: Professional academic palettes plus easy custom scheme creation and loading
- ⚡ **Zero Learning Cost**: Use native syntax of each library, no need to learn additional APIs
- 🔧 **One Line Does It All**: Just `hz.use("scheme-1")` to enable automatic coloring for all libraries

## 🚀 Quick Start

### Installation

```bash
pip install huez
```

### Basic Usage

```python
import huez as hz

# 🎨 One line of code, global coloring
hz.use("scheme-1")

# ✨ Now all libraries automatically color using native syntax!
```

## 📚 Supported Visualization Libraries

**Matplotlib**

```python
import matplotlib.pyplot as plt
plt.plot(x, y1, label='Data 1')  # Pure native syntax - colors auto-applied!
plt.plot(x, y2, label='Data 2')  # Pure native syntax - colors auto-applied!
plt.legend()
```

**Seaborn**

```python
import seaborn as sns
sns.scatterplot(data=df, x='x', y='y', hue='category')  # Pure native syntax - colors auto-applied!
```

**plotnine**

```python
from plotnine import *
(ggplot(df, aes('x', 'y', color='category')) + 
 geom_point())  # Pure native syntax - colors auto-applied!
```

**Altair**

```python
import altair as alt
alt.Chart(df).mark_circle().encode(
    x='x:Q', y='y:Q', color='category:N'  # Pure native syntax - colors auto-applied!
)
```

**Plotly**

```python
import plotly.graph_objects as go
fig = go.Figure()
fig.add_trace(go.Scatter(x=x, y=y, name='Data'))  # Pure native syntax - colors auto-applied!
```

## 🎨 Rich Built-in & Custom Schemes

Huez comes with a rich collection of **professional color schemes** and supports **easy customization**:

### ✨ Custom Schemes
```python
# Easy custom scheme creation
hz.create_scheme("my_scheme", colors=["#FF6B6B", "#4ECDC4", "#45B7D1"])
hz.use("my_scheme")

# Or load from file
hz.load_scheme("path/to/my_colors.yaml")
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

<div align="center">

---

<sub>Made with ❤️ for the Python visualization community</sub>

⭐ **If this project helps you, please give us a star!** ⭐

</div>
