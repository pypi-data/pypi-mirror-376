########################################################################################################################################################

# 1) Histogram Plot 

########################################################################################################################################################

import matplotlib.pyplot as plt
import seaborn as sns

def plot_histogram(# pe.hist:
                      column, bins=30, color="skyblue", title=None,
                      alpha=0.7, edgecolor="black", linewidth=1.0,
                      density=False, histtype="bar", label=None, rwidth=None,

                      # pe.figure
                      fig_width = 8, fig_height = 5, outer_facecolor = 'lightgray',
                      dpi = 100, fig_edgecolor="darkgray", fig_linewidth = 10, frameon = True,
                      tight_layout = None, constrained_layout = None, layout = None,

                      # ax.set_facecolor
                      inner_facecolor = 'white',

                      # pe.title
                      title_fontsize = '14', title_color = 'black', title_loc = 'center', title_pad = 10,
                      title_fontweight = 'light', title_fontname = None, title_style = 'normal',

                      # pe.tick_params
                      tick_params = 'black',

                      # pe.x_label
                      xlabel_fontsize=10, xlabel_color='black', xlabel_labelpad=10,
                      xlabel_loc='center', xlabel_weight='light', xlabel_rotation=0,
                      xlabel_style='normal', xlabel_fontname=None,

                      # pe.y_label
                      ylabel_fontsize = 10, ylabel_color = 'black',  ylabel_labelpad=10,
                      ylabel_loc='center', ylabel_weight='light', ylabel_rotation=90,
                      ylabel_style='normal', ylabel_fontname=None,

                      # pe.grid
                      grid_boolvalue = True, grid_linestyle="--", grid_alpha=0.75, grid_which = 'major',
                      grid_axis = 'both', grid_color = 'gray', grid_linewidth = 0.8, grid_zorder = None,

                      # pe.legend
                      legend_loc='upper right', legend_fontsize = 10, legend_title = 'Legend',
                      legendtitle_fontsize = 10, legend_frameon = True,legend_facecolor = 'lightgray',
                      legend_edgecolor = 'black', legend_ncol = 1, legend_labelspacing = 0.1,
                      legend_handlelength = 1.35, legend_shadow = True, legend_borderpad = None,
                      legend_fancybox = False, legend_columnspacing = None
):

    if title is None:
        title = f"Distribution of {column.name}"

    fig = plt.figure(figsize=(fig_width, fig_height), facecolor=outer_facecolor, dpi = dpi,
                     edgecolor = fig_edgecolor, linewidth = fig_linewidth, frameon = frameon,
                      tight_layout = tight_layout, constrained_layout = constrained_layout, layout = layout)  # light gray figure bg
    ax = plt.gca()
    ax.set_facecolor(inner_facecolor)  # slightly lighter plot area bg

    # Dynamically build kwargs
    kwargs = {
        "bins": bins,
        "color": color,
        "alpha": alpha,
        "edgecolor": edgecolor,
        "linewidth": linewidth,
        "density": density,
        "histtype": histtype
    }
    if label is not None:
        kwargs["label"] = label
    if rwidth is not None:
        kwargs["rwidth"] = rwidth

    # Plot
    plt.hist(column, **kwargs)

    plt.title(title, fontsize = title_fontsize, color = title_color, loc = title_loc, pad = title_pad,
                      fontweight = title_fontweight, fontname = title_fontname, style = title_style)

    plt.tick_params(colors=tick_params)

    plt.xlabel(column.name, fontsize = xlabel_fontsize, color = xlabel_color, labelpad = xlabel_labelpad,
               weight=xlabel_weight, rotation=xlabel_rotation, style=xlabel_style, fontname=xlabel_fontname)

    plt.ylabel("Density" if density else "Frequency", fontsize = ylabel_fontsize, color = ylabel_color,
               labelpad = ylabel_labelpad, weight= ylabel_weight, rotation=ylabel_rotation, style=ylabel_style,
               fontname=ylabel_fontname)

    if label is not None:
        plt.legend(loc=legend_loc, fontsize = legend_fontsize, title = legend_title, title_fontsize = legendtitle_fontsize,
                   frameon = legend_frameon, facecolor = legend_facecolor, edgecolor = legend_edgecolor, ncol = legend_ncol,
                   labelspacing = legend_labelspacing, handlelength = legend_handlelength, shadow = legend_shadow,
                  borderpad = legend_borderpad, fancybox = legend_fancybox, columnspacing = legend_columnspacing)

    plt.grid(grid_boolvalue, linestyle= grid_linestyle, alpha=grid_alpha, which = grid_which, axis = grid_axis,
             color = grid_color, linewidth = grid_linewidth, zorder = grid_zorder)

    plt.tight_layout()

    plt.show()

############################################################################ 1) plot_histogram_code ############################################################################

def plot_histogram_code():
    """Print example usage of plot_histogram()."""
    example = '''
Example usage of plot_histogram:

from plotease.eda import distribution as dst

dst.plot_histogram(df["Cost of Living Index"], label="Living Cost", rwidth=0.9)
'''
    print(example)

############################################################################ 1) plot_histogram_code ############################################################################

def plot_histogram_params():
    """Print all available parameters for plot_histogram with defaults and descriptions."""
    params = """
✅ --- Histogram Style (pe.hist) ---
🔹 bins (int, default=30): Number of histogram bins.
🔹 color (str, default='skyblue'): Fill color of the bars.
🔹 alpha (float, default=0.7): Transparency level of bars (0 to 1).
🔹 edgecolor (str, default='black'): Border color of bars.
🔹 linewidth (float, default=1.0): Width of bar edges.
🔹 density (bool, default=False): Normalize histogram to probability density.
🔹 histtype (str, default='bar'): Type of histogram ('bar', 'step', 'stepfilled').
🔹 label (str, default=None): Label for legend.
🔹 rwidth (float, default=None): Relative width of bars (0–1).

✅ --- Figure Style (pe.figure) ---
🔹 fig_width (int, default=8): Figure width in inches.
🔹 fig_height (int, default=5): Figure height in inches.
🔹 outer_facecolor (str, default='lightgray'): Background color of figure.
🔹 dpi (int, default=100): Resolution in dots per inch.
🔹 fig_edgecolor (str, default='darkgray'): Border color of figure.
🔹 fig_linewidth (float, default=10): Border line width of figure.
🔹 frameon (bool, default=True): Draw frame around figure.
🔹 tight_layout (bool/None, default=None): Auto-adjust subplot params.
🔹 constrained_layout (bool/None, default=None): Adjust layout to avoid overlaps.
🔹 layout (str/None, default=None): Figure layout engine.

✅ --- Axes Style ---
🔹 inner_facecolor (str, default='white'): Background color of plot area.

✅ --- Title (pe.title) ---
🔹 title (str, default=None): Title text (auto-generated if None).
🔹 title_fontsize (int/str, default=14): Font size of title.
🔹 title_color (str, default='black'): Title text color.
🔹 title_loc (str, default='center'): Alignment ('left', 'center', 'right').
🔹 title_pad (int, default=10): Padding between title and plot.
🔹 title_fontweight (str, default='light'): Font weight ('light','bold', etc).
🔹 title_fontname (str/None, default=None): Title font family.
🔹 title_style (str, default='normal'): Title font style ('normal','italic').

✅ --- Tick Parameters (pe.tick_params) ---
🔹 tick_params (str, default='black'): Color of axis ticks and labels.

✅ --- X-axis Label (plt.xlabel) ---
🔹 xlabel_fontsize (int, default=10): Font size of x-axis label.
🔹 xlabel_color (str, default='black'): Color of x-axis label.
🔹 xlabel_labelpad (int, default=10): Padding from axis.
🔹 xlabel_loc (str, default='center'): Alignment.
🔹 xlabel_weight (str, default='light'): Font weight.
🔹 xlabel_rotation (int, default=0): Rotation angle of label.
🔹 xlabel_style (str, default='normal'): Font style ('normal','italic').
🔹 xlabel_fontname (str/None, default=None): Font family.

✅ --- Y-axis Label (pe.ylabel) ---
🔹 ylabel_fontsize (int, default=10): Font size of y-axis label.
🔹 ylabel_color (str, default='black'): Color of y-axis label.
🔹 ylabel_labelpad (int, default=10): Padding from axis.
🔹 ylabel_loc (str, default='center'): Alignment.
🔹 ylabel_weight (str, default='light'): Font weight.
🔹 ylabel_rotation (int, default=90): Rotation angle.
🔹 ylabel_style (str, default='normal'): Font style.
🔹 ylabel_fontname (str/None, default=None): Font family.

✅ --- Grid (pe.grid) ---
🔹 grid_boolvalue (bool, default=True): Enable grid.
🔹 grid_linestyle (str, default='--'): Line style for grid.
🔹 grid_alpha (float, default=0.75): Transparency of grid lines.
🔹 grid_which (str, default='major'): Apply to 'major' or 'minor' ticks.
🔹 grid_axis (str, default='both'): Apply to 'x','y', or 'both'.
🔹 grid_color (str, default='gray'): Color of grid lines.
🔹 grid_linewidth (float, default=0.8): Line width of grid lines.
🔹 grid_zorder (int/None, default=None): Draw order of grid lines.

✅ --- Legend (pe.legend) ---
🔹 legend_loc (str, default='upper right'): Legend location.
🔹 legend_fontsize (int, default=10): Font size of legend text.
🔹 legend_title (str, default='Legend'): Legend title text.
🔹 legendtitle_fontsize (int, default=10): Font size of legend title.
🔹 legend_frameon (bool, default=True): Draw frame around legend.
🔹 legend_facecolor (str, default='lightgray'): Background color of legend.
🔹 legend_edgecolor (str, default='black'): Border color of legend box.
🔹 legend_ncol (int, default=1): Number of legend columns.
🔹 legend_labelspacing (float, default=0.1): Vertical spacing between labels.
🔹 legend_handlelength (float, default=1.35): Length of legend handles.
🔹 legend_shadow (bool, default=True): Draw shadow under legend.
🔹 legend_borderpad (float/None, default=None): Padding inside legend border.
🔹 legend_fancybox (bool, default=False): Use rounded box.
🔹 legend_columnspacing (float/None, default=None): Spacing between columns.
"""
    print(params)

