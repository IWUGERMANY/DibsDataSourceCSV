# DibsDataSourceCSV

## Overview

This repository contains a set of utilities `utils` and a Python file named `datasource_csv`. The primary purpose
of `datasource_csv` is to provide functionality for handling Excel and CSV files, performing
calculations on data and returning objects as results. `DataSourceCSV`implements the `DataSource` interface defined in
another module called `dibs_computing_core`.

## File Structure

- **utils/**: This directory contains several Python files, each housing methods that are utilized
  within `datasource_csv`.
- **datasource_csv.py**: This Python file implements the `DataSource` interface, defined in `dibs_computing_core`, to
  interact with Excel and CSV files, converting them into appropriate objects (performing
  calculations on data and returning objects
  as results.)

### Arguments:

- `path`: Path to the file containing building data type of `str`. (Required)
- `profile_from_norm`: type of `str`. (Optional)
- `gains_from_group_values`: type of `str`. (Optional)
- `usage_from_norm`: type of `str`. (Optional)
- `weather_period`: type of `str`. (Optional)

## Usage

To use the functionalities provided by this repository, follow these steps:

1. **Installation**: Use pip to install the module. This will automatically install the required dependencies
   mentioned in `pyproject.toml`.

    ```bash
    pip install dibs_datasource_csv
    ```

2. **Importing DatasourceCSV**: You can import and use the `DataSourceCSV` class directly from the terminal or any
   Python
   environment.

    ```bash
    python
    ```

    ```python
   from dibs_computing_core.iso_simulator.dibs.dibs import DIBS
   from dibs_datasource_csv.datasource_csv import DataSourceCSV
   import dibs_data
   ```


1. **Performing Simulation**: Use the methods provided in `dibs class` (`calculate_result_of_one_building`
   or `multi`) to perform calculations on your data. The method `calculate_result_of_one_building` simulates one
   building and `multi` simulates multiple building simultaneously for more performance.

    ```python
    # Example usage
    datasource_csv = DataSourceCSV(path="path_to_your_data", "din18599", "mid", "sia2024", "2007-2021") or 
    datasource_csv = DataSourceCSV(path="path_to_your_data", profile_from_norm="din18599", gains_from_group_values="mid", usage_from_norm="sia2024", weather_period="2007-2021")
   
    dibs = DIBS(datasource_csv)
   
    simulation_time, result_of_all_hours, summary_result = dibs.calculate_result_of_one_building()
   
    # To see the hourly result of the simulated building
    print(result_of_all_hours)
   
    # To see the summary result of the simulated building
    print(summary_result)
   ```

## Contributing

Contributions to this repository are welcome. If you find any bugs, have feature requests, or want to contribute
enhancements, feel free to open an issue or submit a pull request.

## License

This repository is licensed under the [MIT License](LICENSE). Feel free to use, modify, and distribute the code as per
the terms of this license.

## Acknowledgments

Special thanks to contributors and maintainers who have helped shape and improve this repository. Your efforts are
greatly appreciated.
