"""Design free energy diagrams with `FancyPlots`.

A Python interface to the `FancyPlots` is available via
:func:`~ccu.fancyplots.plotting.generate_figure`.

The FancyPlots GUI can be launched programatically via the following idiom:

.. code-block:: python

    import tkinter as tk
    from ccu.fancyplots import FancyPlotsGUI

    root = tk.Tk()
    app = FancyPlotsGUI(master=root)
    app.master.mainloop()

Alternatively, the GUI can be launched from the command line, via the
:program:`ccu-fancyplots` subcommand::

    ccu fed

In both cases, one has the option to load data from a previous FancyPlots
session by specifying a cache file via the ``cache_file`` parameter of
the :class:`~ccu.fancyplots._gui.root.FancyPlotsGUI` constructor or the
:option:`ccu-fancyplots --cache` CLI option of ``ccu fed``.
"""

from ccu.fancyplots._gui.annotation import auto_annotate as auto_annotate
from ccu.fancyplots._gui.root import FancyPlotsGUI as FancyPlotsGUI
from ccu.fancyplots.data import DEFAULT_PARAMETERS as DEFAULT_PARAMETERS
from ccu.fancyplots.plotting import generate_figure as generate_figure
