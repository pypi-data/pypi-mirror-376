<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif">
<div align="center">
  
# JiggleCoord: A geocoding utility for python

<img align="center" alt="GIF" src="https://i.imgur.com/2gKEklX.jpeg" width="500px" height="500" />
  
</div><img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif">

## Summary

This package provides a robust solution for reverse geocoding geographical coordinates (**returns the address details and merges them into a dataframe**), a task often complicated by points falling on administrative boundaries 
which results in the coordinate mobing to that boundaries official location, obfuscating where the location actually is.   
It intelligently addresses this challenge by employing a "snowflake" perturbation strategy, where it systematically tests nearby coordinates to "escape" the boundary and find a valid, non-ambiguous location. 
This functionality is seamlessly integrated with pandas DataFrames, allowing for efficient and reliable geocoding of large datasets for data science and analysis.


## Features
- Smart Geocoding: Automatically handles cases where a coordinate falls on a geographical boundary.
- "Snowflake" Perturbation: When a boundary is detected, the package generates a small, structured grid of surrounding points to find the nearest valid location using the Haversine formula.
- DataFrame Integration: Seamlessly processes large datasets by integrating directly with pandas DataFrames.
- Rate-Limited: Uses geopy's built-in rate limiter to respect API usage policies.

## Installation
You can install the package directly from PyPI:

``` pip install JiggleCoord ```

## License
This project is licensed under the MIT License - see the LICENSE file for details.
## Dependencies
- pandas
- geopy

## Quickstart

### Full output 


### Example 1: Geocoding all rows from a DataFrame
    print("--- Example 1: Geocoding All Rows ---")
    sample_df_all = pd.DataFrame({
        'latitude': [40.7128, 51.5074, 38.8977],
        'longitude': [-74.0060, -0.1278, -77.0365]
    })

    # The function will geocode all coordinates since `geocode_on` is not specified
    all_results = geopy_df_geocoder(
        sample_df_all,
        latitude_col='latitude',
        longitude_col='longitude',
        perturb_levels=2,
        perturb_distance=500
    )
    print("\nDataFrame after geocoding all rows:")
    print(all_results[['latitude', 'longitude', 'display_name', 'status', 'perturbation_layer']])


### Example 2: Geocoding specific rows based on a condition
    print("\n--- Example 2: Geocoding Specific Rows (Boundary Condition) ---")
    sample_df_selective = pd.DataFrame({
        'id': [1, 2, 3],
        'latitude': [40.7128, 38.8977, 51.5074],
        'longitude': [-74.0060, -77.0365, -0.1278],
        'class': ['place', 'boundary', 'place'],
        'type': ['city', 'administrative', 'city']
    })

    # The function will only process the row where 'class' is 'boundary'
    selective_results = geopy_df_geocoder(
        sample_df_selective,
        latitude_col='latitude',
        longitude_col='longitude',
        geocode_on="`class` == 'boundary'",
        perturb_levels=2,
        perturb_distance=500
    )
    print("\nDataFrame after selectively geocoding 'boundary' rows:")
    print(selective_results[['id', 'latitude', 'longitude', 'class', 'status', 'perturbation_layer', 'display_name']]) 




