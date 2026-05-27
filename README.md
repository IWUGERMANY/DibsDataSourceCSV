# DibsDataSourceCSV

`dibs_datasource_csv` translates CSV and Excel input files into the DIBS data
structures required by `dibs_computing_core`.

## Responsibilities

The package provides:

- building input loading
- occupancy schedule lookup
- gain and usage profile lookup
- TEK hot-water lookup
- EPW weather-file selection and loading
- primary energy and emission factor loading

## Relevance for heating-period diagnostics

No new input columns are required for the heating-period diagnostics feature.
The existing interfaces already provide the required source data:

- `get_schedule()` returns hourly `People` and `Appliances` factors
- `choose_and_get_the_right_weather_data_from_path()` returns hourly weather data,
  including `drybulb_C`

Those values are consumed by `dibs_computing_core` to derive:

- heating-day masks based on daily mean outdoor temperature
- `HeatingDays`, `HeatingDegreeDays`, and `RoomHeatingDegreeDays`
- annual and heating-period mean dry-bulb temperature
- annual and heating-period totals and hourly means for:
  - global horizontal radiation
  - direct normal radiation
  - diffuse horizontal radiation
- annual and heating-period mean occupancy/appliance factors

## Branch-linked development

For the coordinated feature work, `pyproject.toml` points to:

- `dibs_computing_core@heating-period-diagnostics`
- `dibs_data@dd101copy`

## License

This project is licensed under the [MIT License](LICENSE).
