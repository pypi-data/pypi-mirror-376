from pathlib import Path


def uploaded_file_path(file_name: str, experiment_path: Path) -> Path:
    """Create the full upload path for data file uploads.

    Args:
        file_name (str): The name of the file.
        experiment_path (Path): The path of the experiment.

    Returns:
        Path: The full upload path for the file.
    """
    return experiment_path / file_name


def preprocessed_data_path(file_name: str, experiment_path: Path) -> Path:
    """Create the full path to the directory to save raw data.

    Args:
        file_name (str): The name of the file.
        experiment_path (Path): The path of the experiment.

    Returns:
        Path: The full path for the raw data directory.
    """
    name, ext = file_name.split(".")
    file_name = f"{name}_preprocessed.{ext}"

    return experiment_path / file_name


def log_dir(experiment_path: Path) -> Path:
    """Create the full upload path for experiment log files.

    Args:
        experiment_path (str): The path of the experiment.

    Returns:
        Path: The full path for the log directory.
    """
    return experiment_path / "logs"


def ml_plot_dir(experiment_path: Path) -> Path:
    """Create the full path to the directory to save Machine Learning plots.

    Args:
        experiment_path (Path): The path of the experiment.

    Returns:
        Path: The full path for the Machine Learning plot directory.
    """
    return experiment_path / "plots" / "ml"


def ml_model_dir(experiment_path: Path) -> Path:
    """Create the full path to the directory to save Machine Learning models.

    Args:
        experiment_path (Path): The path of the experiment.

    Returns:
        Path: The full path for the Machine Learning model directory.
    """
    return experiment_path / "models"


def ml_metrics_mean_std_path(experiment_path: Path) -> Path:
    """Create the full path to the file to save the ML models' metrics'cmean
    and standard deviations.

    Args:
        experiment_path (Path): The path of the experiment.

    Returns:
        Path: The full path for the ml models metrics file.
    """
    return experiment_path / "results" / "ml_metrics" / "metrics_mean_std.json"


def ml_metrics_full_path(experiment_path: Path) -> Path:
    """Create the full path to the file to save the full ML models metrics results.

    Args:
        experiment_path (Path): The path of the experiment.

    Returns:
        Path: The full path for the ml models metrics file.
    """
    return experiment_path / "results" / "ml_metrics" / "metrics_full.json"


def ml_predictions_path(experiment_path: Path) -> Path:
    """Create the full path to the directory to save ML models predictions.

    Args:
        experiment_path (Path): The path of the experiment.

    Returns:
        Path: The full path for the ml models predictions file.
    """
    return experiment_path / "results" / "ml_metrics" / "predictions.csv"


def fi_plot_dir(experiment_path: Path) -> Path:
    """Create the full path to the directory to save Feature Importance plots.

    Args:
        experiment_path (Path): The path of the experiment.

    Returns:
        Path: The full path for the Feature Importance plot directory.
    """
    return experiment_path / "plots" / "fi"


def fi_result_dir(experiment_path: Path) -> Path:
    """Create the full path to the directory to save Feature Importance results.

    Args:
        experiment_path (Path): The path of the experiment.

    Returns:
        Path: The full path for the Feature Importance result directory.
    """
    return experiment_path / "results" / "fi"


def fi_options_dir(experiment_path: Path) -> Path:
    """Create the full path to the directory to save Feature Importance options.

    Args:
        experiment_path (Path): The path of the experiment.

    Returns:
        Path: The full path for the Feature Importance options directory.
    """
    return experiment_path / "options" / "fi"


def fuzzy_plot_dir(experiment_path: Path) -> Path:
    """Create the full path to the directory to save Fuzzy plots.

    Args:
        experiment_path (Path): The path of the experiment.

    Returns:
        Path: The full path for the Fuzzy plot directory.
    """
    return experiment_path / "plots" / "fuzzy"


def fuzzy_result_dir(experiment_path: Path) -> Path:
    """Create the full path to the directory to save Fuzzy results.

    Args:
        experiment_path (Path): The path of the experiment.

    Returns:
        Path: The full path for the Fuzzy result directory.
    """
    return experiment_path / "results" / "fuzzy"


def helix_experiments_base_dir() -> Path:
    """Return the path the base directory of all Helix experiments.

    This will be `/Users/<username>/HelixExperiments` on MacOS,
    `/home/<username>/HelixExperiments` on Linux, and
    `C:\\Users\\<username>\\HelixExperiments` on Windows.

    Returns:
        Path: The path to the Helix experiments base directory.
    """
    return Path.home() / "HelixExperiments"


def data_analysis_plots_dir(experiment_path: Path) -> Path:
    """Create the full path to the directory to save Data Analysis plots.

    Args:
        experiment_path (Path): The path of the experiment.

    Returns:
        Path: The full path for the Data Analysis plot directory.
    """
    return experiment_path / "plots" / "data_analysis"


def plot_options_path(experiment_path: Path) -> Path:
    """Return the path to an experiment's plot options.
    The path will be to a `json` file called `plot_options.json`

    Args:
        experiment_path (str): The path of the experiment.

    Returns:
        Path: The path to the experiment's plot options.

    Examples:
    ```python
    experiment_name = "test"
    experiment_path = helix_experiments_base_dir() / experiment_name
    plot_options_file = plot_options_path(experiment_path)
    ```
    """
    return experiment_path / "plot_options.json"


def execution_options_path(experiment_path: Path) -> Path:
    """Return the path to an experiment's execution options.
    The path will be to a `json` file called `execution_options.json`

    Args:
        experiment_path (str): The path of the experiment.

    Returns:
        Path: The path to the experiment's execution options.

    Examples:
    ```python
    experiment_name = "test"
    experiment_path = helix_experiments_base_dir() / experiment_name
    exec_options_file = execution_options_path(experiment_path)
    ```
    """
    return experiment_path / "execution_options.json"


def data_preprocessing_options_path(experiment_path: Path) -> Path:
    """Return the path to an experiment's data preprocessing options.
    The path will be to a `json` file called `data_preprocessing_options.json`

    Args:
        experiment_path (str): The path of the experiment.

    Returns:
        Path: The path to the experiment's data preprocessing options.

    Examples:
    ```python
    experiment_name = "test"
    experiment_path = helix_experiments_base_dir() / experiment_name
    data_preprocessing_options_file = data_preprocessing_options_path(experiment_path)
    ```
    """
    return experiment_path / "data_preprocessing_options.json"


def ml_options_path(experiment_path: Path) -> Path:
    """Return the path to an experiment's ML options.
    The path will be to a `json` file called `ml_options.json`

    Args:
        experiment_path (str): The path of the experiment.

    Returns:
        Path: The path to the experiment's ML options.

    Examples:
    ```python
    experiment_name = "test"
    experiment_path = helix_experiments_base_dir() / experiment_name
    ml_options_file = ml_options_path(experiment_path)
    ```
    """
    return experiment_path / "ml_options.json"


def fi_options_path(experiment_path: Path) -> Path:
    """Return the path to an experiment's FI options.
    The path will be to a `json` file called `fi_options.json`

    Args:
        experiment_path (str): The path of the experiment.

    Returns:
        Path: The path to the experiment's FI options.

    Examples:
    ```python
    experiment_name = "test"
    experiment_path = helix_experiments_base_dir() / experiment_name
    fi_options_file = fi_options_path(experiment_path)
    ```
    """
    return experiment_path / "fi_options.json"


def fuzzy_options_path(experiment_path: Path) -> Path:
    """Return the path to an experiment's Fuzzy options.
    The path will be to a `json` file called `fuzzy_options.json`

    Args:
        experiment_path (str): The path of the experiment.

    Returns:
        Path: The path to the experiment's Fuzzy options.

    Examples:
    ```python
    experiment_name = "test"
    experiment_path = helix_experiments_base_dir() / experiment_name
    fuzzy_options_file = fuzzy_options_path(experiment_path)
    ```
    """
    return experiment_path / "fuzzy_options.json"


def data_options_path(experiment_path: Path) -> Path:
    """Return the path to an experiment's data options.
    The path will be to a `json` file called `data_options.json`

    Args:
        experiment_path (str): The path of the experiment.

    Returns:
        Path: The path to the experiment's data options.

    Examples:
    ```python
    experiment_name = "test"
    experiment_path = helix_experiments_base_dir() / experiment_name
    data_options_file = data_options_path(experiment_path)
    ```
    """
    return experiment_path / "data_options.json"
