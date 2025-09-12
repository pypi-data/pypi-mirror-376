import logging
import os
import warnings

from matplotlib.figure import Figure
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

def save_figure(figure: Figure, file_path: os.PathLike, debug: bool = False, *args, **kwargs):
    """
    Private function that saves a figure. This function is submitted to the ThreadPoolExecuter as a job
    Parameters
    ----------
    figure (matplotlib.figure.Figure):
        Figure to save to disk
    file_path (os.PathLike):
        File path with extension pointing to the save directory

    Returns
    -------
        None
    """

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            figure.savefig(file_path, **kwargs)
            plt.close(figure)
    except Exception as e:
        logger.error("Unable to save %s \n %s", file_path, exc_info=e)
    if debug:
        logger.debug("Saved %s", file_path)