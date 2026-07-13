import pandas as pd

from dibs_datasource_csv.utils import utils_epwfile


def _stations_with_distance():
    return pd.DataFrame(
        [
            {"filename": "far.epw", "latitude": 50.0, "longitude": 8.0, "distance": 2.0},
            {"filename": "near.epw", "latitude": 51.0, "longitude": 9.0, "distance": 1.0},
        ]
    )


def test_closest_station_helpers_reuse_cached_minimum_index():
    stations = _stations_with_distance()

    assert utils_epwfile.get_filename_with_minimum_distance(stations) == "near.epw"
    assert stations.attrs[utils_epwfile._MIN_DISTANCE_INDEX_ATTR] == 1
    assert utils_epwfile.get_coordinates_station(stations) == [51.0, 9.0]
    assert utils_epwfile.get_distance(stations) == 1.0


def test_distance_calculation_invalidates_cached_minimum_index():
    stations = pd.DataFrame(
        [
            {
                "filename": "a.epw",
                "latitude": 50.0,
                "longitude": 8.0,
                "latitude_building": 50.0,
                "longitude_building": 8.0,
            },
            {
                "filename": "b.epw",
                "latitude": 51.0,
                "longitude": 9.0,
                "latitude_building": 50.0,
                "longitude_building": 8.0,
            },
        ]
    )
    stations.attrs[utils_epwfile._MIN_DISTANCE_INDEX_ATTR] = 1

    utils_epwfile.calculate_minimum_distance_to_next_weather_station(stations)

    assert utils_epwfile.get_filename_with_minimum_distance(stations) == "a.epw"
