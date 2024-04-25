# DibsDataSourceCSV

## Overview

This repository contains a set of utilities `utils` and a Python file named `datasource_csv`. The primary purpose
of `datasource_csv` is to provide functionality for handling Excel and CSV files, performing
calculations on data and returning objects as results. `DataSourceCSV` implements the `DataSource` interface defined in
another module called [dibs_computing_core](https://github.com/IWUGERMANY/DibsComputingCore). Both packages are part of Python non-domestic building simulation program called 'Dynamic ISO Building Simulator' or short [DIBS](https://iwugermany.github.io/dibs/).

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

    To use the full DIBS [model](https://iwugermany.github.io/dibs/overview) it is recommended to install the [DibsCLI](https://github.com/IWUGERMANY/DibsCLI) bundling the
    DibsComputingCore, [DibsDataSourceCSV](https://github.com/IWUGERMANY/DibsDataSourceCSV) and the [DibsData](https://github.com/IWUGERMANY/DibsData). To install the DIBS
    Command Line Interface (DibsCLI) use the following command:

    ```bash
    pip install dibs_cli
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

## Further information
For a detailed installation guide and further information on DIBS see the [wiki](https://github.com/IWUGERMANY/DibsCLI/wiki) and the [DIBS Project Page](https://iwugermany.github.io/dibs/).

## How to cite
Please cite the Dynamic ISO Building Simulator (DIBS) as defined [here](https://iwugermany.github.io/dibs/contri).


## Legacy
The current Dynamic ISO Building Simulator (DIBS) is a PyPI package implementation of the initial [DIBS implementation](https://github.com/IWUGERMANY/DIBS---Dynamic-ISO-Building-Simulator) by Julian Bischof, Simon Knoll and Michael Hörner.


## Contributing
Contributions to this repository are welcome. If you find any bugs, have feature requests, or want to contribute
enhancements, feel free to open an issue or submit a pull request.

## License

This repository is licensed under the [MIT License](LICENSE). Feel free to use, modify, and distribute the code as per
the terms of this license.

## Acknowledgement
The Dynamic ISO Building Simulator has been developed in context of the 'ENOB:DataNWG Forschungsdatenbank Nichtwohngebäude' (www.datanwg.de) project and the project 'FlexGeber - Demonstration of flexibility options in the building sector and their integration with the energy system in Germany' at Institut Wohnen und Umwelt (IWU), Darmstadt. The preparation of the publication as a [Python package on Pypi](https://pypi.org/project/dibs-computing-core/) was undertaken within the [EnOB:LezBAU](https://www.lezbau.de/) project, where the DIBS model provides the basis for the calculation of the operational energy within the LezBAU web tool.
<p float="left">
  <img src="https://github.com/IWUGERMANY/DibsComputingCore/blob/main/src/img/IWU_Logo.PNG" width="15%" /> 
</p>  

<b>ENOB:DataNWG<b>
<b>Funding code:</b>  Fkz.: 03ET1315  
<b>Project duration:</b>  01.12.2015 until 31.05.2021

<b>FlexGeber<b>
<b>Funding code:</b>  Fkz.: 03EGB0001  
<b>Project duration:</b>  01.10.2017 until 31.07.2022

<b>ENOB:LezBAU<b>
<b>Funding code:</b>  Fkz.: 03EN1074A
</br><b>Project duration:</b>  01.01.2023 until 31.12.2025
  
