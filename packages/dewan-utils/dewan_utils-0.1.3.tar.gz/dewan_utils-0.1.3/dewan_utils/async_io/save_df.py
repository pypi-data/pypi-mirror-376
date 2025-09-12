import os
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def save_df_as_excel(
    df_to_save: pd.DataFrame,
    file_path: os.PathLike,
    debug: bool = False,
    *args,
    **kwargs,
) -> None:
    """
    Private function that saves a Dataframe. This function is submitted to the ThreadPoolExecuter as a job
    Parameters
    ----------
    df_to_save (Pandas.DataFrame):
        Pandas dataframe the user wishes to save to disk
    file_path (os.PathLike):
        File path with extension pointing to the save directory

    Returns
    -------
        None
    """
    try:
        df_to_save.to_excel(file_path, *args, **kwargs)
    except Exception as e:
        logger.error("Unable to save %s", file_path, exc_info=e)
    if debug:
        logger.debug("Saved %s", file_path)


def save_df_as_csv(
    df_to_save: pd.DataFrame,
    file_path: os.PathLike,
    debug: bool = False,
    *args,
    **kwargs,
) -> None:
    """
    Private function that saves a Dataframe. This function is submitted to the ThreadPoolExecuter as a job
    Parameters
    ----------
    df_to_save (Pandas.DataFrame):
        Pandas dataframe the user wishes to save to disk
    file_path (os.PathLike):
        File path with extension pointing to the save directory

    Returns
    -------
        None
    """
    try:
        df_to_save.to_csv(file_path, *args, **kwargs)
    except Exception as e:
        logger.error("Unable to save %s", file_path, exc_info=e)
    if debug:
        logger.debug("Saved %s", file_path)


def save_df_as_pickle(
    df_to_save: pd.DataFrame,
    file_path: os.PathLike,
    debug: bool = False,
    *args,
    **kwargs,
) -> None:
    """
    Private function that saves a Dataframe. This function is submitted to the ThreadPoolExecuter as a job
    Parameters
    ----------
    df_to_save (Pandas.DataFrame):
        Pandas dataframe the user wishes to save to disk
    file_path (os.PathLike):
        File path with extension pointing to the save directory

    Returns
    -------
        None
    """
    try:
        df_to_save.to_pickle(file_path, *args, **kwargs)
    except Exception as e:
        logger.error("Unable to save %s", file_path, exc_info=e)
    if debug:
        logger.debug("Saved %s", file_path)
