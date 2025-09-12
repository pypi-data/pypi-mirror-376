"""
Utilities for generic project tree navigation and io. The basic project tree structure assumed is that
the project has a data folder and an output folder
"""
import os
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.utils import estimator_html_repr
from cheutils.loggers import LoguruWrapper
from cheutils.common_utils import label, datestamp
from cheutils.properties_util import AppProperties
from cheutils.project_tree_handler import ProjectTreeProperties
from cheutils.datasource_utils import DSWrapper
from typing import cast

LOGGER = LoguruWrapper().get_logger()

def get_root_dir():
    """
    Get the root directory of the project. The assumption execution is from the root folder (.).
    :return: the path to the root directory.
    :rtype:
    """
    __proj_handler: ProjectTreeProperties = cast(ProjectTreeProperties, AppProperties().get_subscriber('proj_handler'))
    return __proj_handler.get_proj_root()


def get_data_dir():
    """
    Get the data directory of the project, which is expected to be in the project root directory.
    :return: the path to the data directory.
    :rtype:
    """
    __proj_handler: ProjectTreeProperties = cast(ProjectTreeProperties, AppProperties().get_subscriber('proj_handler'))
    return __proj_handler.get_proj_data()


def get_output_dir():
    """
    Get the output directory of the project, which is expected to be in the project root directory.
    :return: the path to the output directory.
    :rtype:
    """
    __proj_handler: ProjectTreeProperties = cast(ProjectTreeProperties, AppProperties().get_subscriber('proj_handler'))
    return __proj_handler.get_proj_output()

def get_namespace():
    """
    Gets the project namespace
    :return:
    :rtype:
    """
    __proj_handler: ProjectTreeProperties = cast(ProjectTreeProperties, AppProperties().get_subscriber('proj_handler'))
    return __proj_handler.get_proj_namespace()

def load_dataset(file_name: str = None, is_csv: bool = True, date_cols: list = None, chunksize: int=None, ):
    """
    Load the project dataset provided. The specified file is expected to be in either a CSV or Excel.
    :param file_name: the file name to be read from the data folder - so, only the file name and not the path is required
    :param is_csv: the default is CSV
    :param date_cols: columns with  dates that require parsing
    :return: a dataframe with the raw dataset
    """
    assert file_name is not None, 'file_name must be specified'
    path_to_dataset = os.path.join(get_data_dir(), file_name)
    dataset_df = None
    ds_wrapper = DSWrapper(is_file_ds=True)
    ds_config = {'data_file': path_to_dataset, 'is_csv': is_csv, 'is_raw': True, }
    dataset_df = ds_wrapper.read_from_datasource(ds_config=ds_config, parse_date_cols=date_cols, chunksize=chunksize, )
    if chunksize is not None:
        dataset_df = pd.concat(dataset_df)
    LOGGER.info('Loaded dataset ({}) shape = {}', file_name, dataset_df.shape)
    return dataset_df


def save_excel(df: [pd.DataFrame, pd.Series], file_name: str, index: bool = False, tag_label: str=None, date_stamped: bool = False, **kwargs):
    """
    Save the specified dataframe or series to Excel.
    :param df: the dataframe or series to be saved
    :param file_name: the file name to be saved, which is expected to be saved in the data folder in the project root directory
    :param index: to include the index column or not
    :param tag_label: the label to be added to the file name - e.g., test-<tag_label>.xlsx
    :param date_stamped: to include the date stamped to the file name - e.g., test-<date_stamped>.xlsx
    :return:
    """
    assert df is not None, 'A valid DataFrame expected as input'
    assert file_name is not None, 'A valid file name expected as input'
    os.makedirs(get_output_dir(), exist_ok=True)
    target_file = os.path.join(get_output_dir(), file_name) if tag_label is None else os.path.join(get_output_dir(),
                                                                                                   label(file_name,
                                                                                                         label=tag_label))
    target_file = datestamp(target_file) if date_stamped else target_file

    df.to_excel(target_file, index=index, **kwargs)

def save_csv(df: [pd.DataFrame, pd.Series], file_name: str, index: bool = False, tag_label: str=None, date_stamped: bool = False, **kwargs):
    """
    Save the specified dataframe or series to Excel.
    :param df: the dataframe or series to be saved
    :param file_name: the file name to be saved, which is expected to be saved in the data folder in the project root directory
    :param index: to include the index column or not
    :param tag_label: the label to be added to the file name - e.g., test-<tag_label>.csv
    :param date_stamped: to include the date stamped to the file name - e.g., test-<date_stamped>.csv
    :return:
    """
    assert df is not None, 'A valid DataFrame expected as input'
    assert file_name is not None, 'A valid file name expected as input'
    os.makedirs(get_output_dir(), exist_ok=True)
    target_file = os.path.join(get_output_dir(), file_name) if tag_label is None else os.path.join(get_output_dir(),
                                                                                                   label(file_name,
                                                                                                         label=tag_label))
    target_file = datestamp(target_file) if date_stamped else target_file
    df.to_csv(target_file, index=index, **kwargs)


def save_current_fig(file_name: str, **kwargs):
    """
    Save the current figure as a file in the output folder of the project.
    :param file_name: the file name to be saved, which is expected to be saved in the output folder in the project root directory
    :type file_name:
    :param kwargs: any additional parameters to be passed to the underlying Matplotlib
    :type kwargs:
    :return:
    :rtype:
    """
    assert file_name is not None, 'A valid file name expected'
    os.makedirs(get_output_dir(), exist_ok=True)
    plt.savefig(os.path.join(get_output_dir(), file_name), bbox_inches='tight', **kwargs)


def save_to_html(estimator, file_name: str, **kwargs):
    """
    Save an image representation of a pipeline or estimator or search object.
    :param estimator:
    :param file_name:
    :param kwargs:
    :return:
    """
    assert estimator is not None, 'A valid html renderable object expected'
    assert file_name is not None, 'A valid file name expected'
    # make the pipelines directory
    try:
        os.makedirs(get_output_dir(), exist_ok=True)
        html_dir = os.path.join(get_output_dir(), 'html')
        os.makedirs(html_dir, exist_ok=True)
        with open(os.path.join(html_dir + '/', file_name), 'w', encoding='utf-8') as file:
            file.write(estimator_html_repr(estimator))
    except OSError as error:
        LOGGER.exception("Directory '%s' cannot be created")


