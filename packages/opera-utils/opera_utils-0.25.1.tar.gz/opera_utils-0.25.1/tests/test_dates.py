import datetime
from pathlib import Path

from opera_utils import _dates


def test_date_format_to_regex():
    # Test date format strings with different specifiers and delimiters
    date_formats = ["%Y-%m-%d", "%Y/%m/%d", "%Y%m%d", "%d-%m-%Y", "%m/%d/%Y", "%j0.%y"]
    matching_dates = [
        "2021-01-01",
        "2022/02/02",
        "20230103",
        "01-04-2024",
        "05/06/2025",
        "1300.23",
    ]
    for date_format, date in zip(date_formats, matching_dates):
        pattern = _dates._date_format_to_regex(date_format)

        # Test that the date matches the regular expression
        assert pattern.match(date) is not None

    # Test date formats that should not match the dates in "non_matching_dates"
    non_matching_dates = [
        "01-01-2021",
        "2022-02-03",
        "2022-03-04",
        "2022/05/06",
        "117.22",
        "23.0090",
    ]
    for date, date_format in zip(non_matching_dates, date_formats):
        pattern = _dates._date_format_to_regex(date_format)

        # Test that the date does not match the regular expression
        assert pattern.match(date) is None


def test_datetime_format_to_regex():
    # Check on a Sentinel-1-like datetime format
    date_format = "%Y%m%dT%H%M%S"
    date = "20221204T005230"
    pattern = _dates._date_format_to_regex(date_format)

    # Test that the date matches the regular expression
    assert pattern.match(date)


def test_get_dates():
    assert _dates.get_dates("20200303_20210101.int") == [
        datetime.datetime(2020, 3, 3),
        datetime.datetime(2021, 1, 1),
    ]

    assert _dates.get_dates("20200303.slc")[0] == datetime.datetime(2020, 3, 3)
    assert _dates.get_dates(Path("20200303.slc"))[0] == datetime.datetime(2020, 3, 3)
    # Check that it's the filename, not the path
    assert _dates.get_dates(Path("/usr/19990101/asdf20200303.tif"))[
        0
    ] == datetime.datetime(2020, 3, 3)
    assert _dates.get_dates("/usr/19990101/asdf20200303.tif")[0] == datetime.datetime(
        2020, 3, 3
    )
    assert _dates.get_dates("/usr/19990101/20200303_20210101.int") == [
        datetime.datetime(2020, 3, 3),
        datetime.datetime(2021, 1, 1),
    ]

    assert _dates.get_dates("/usr/19990101/notadate.tif") == []


def test_get_dates_with_format():
    # try other date formats
    fmt = "%Y-%m-%d"
    assert _dates.get_dates("2020-03-03_2021-01-01.int", fmt) == [
        datetime.datetime(2020, 3, 3),
        datetime.datetime(2021, 1, 1),
    ]

    fmt = "%j0.%y"
    # check for TEC file format
    assert _dates.get_dates("/usr/19990101/jplg0900.23i", fmt)[0] == datetime.datetime(
        2023, 3, 31, 0, 0
    )

    fmt = "%Y%m%dT%H%M%S"
    # Check the OPERA name
    fn = "OPERA_L2_CSLC-S1_T087-185678-IW2_20180210T232711Z_20230101T100506Z_S1A_VV_v1.0.h5"
    assert _dates.get_dates(fn, fmt) == [
        datetime.datetime(2018, 2, 10, 23, 27, 11),
        datetime.datetime(2023, 1, 1, 10, 5, 6),
    ]

    # Check the Sentinel name
    fn = "S1A_IW_SLC__1SDV_20221204T005230_20221204T005257_046175_05873C_3B80.zip"
    assert _dates.get_dates(fn, fmt) == [
        datetime.datetime(2022, 12, 4, 0, 52, 30),
        datetime.datetime(2022, 12, 4, 0, 52, 57),
    ]

    # Check without a format using default
    assert _dates.get_dates(fn) == [
        datetime.datetime(2022, 12, 4, 0, 0, 0),
        datetime.datetime(2022, 12, 4, 0, 0, 0),
    ]


def test_get_dates_with_gdal_string():
    # Checks that is can parse 'NETCDF:"/path/to/file.nc":variable'
    assert _dates.get_dates('NETCDF:"/usr/19990101/20200303_20210101.nc":variable') == [
        datetime.datetime(2020, 3, 3),
        datetime.datetime(2021, 1, 1),
    ]
    assert _dates.get_dates(
        'NETCDF:"/usr/19990101/20200303_20210101.nc":"//variable/2"'
    ) == [
        datetime.datetime(2020, 3, 3),
        datetime.datetime(2021, 1, 1),
    ]
    # Check the derived dataset name too
    assert _dates.get_dates(
        'DERIVED_SUBDATASET:AMPLITUDE:"/usr/19990101/20200303_20210101.int"'
    ) == [datetime.datetime(2020, 3, 3), datetime.datetime(2021, 1, 1)]


def test_sort_files_by_date():
    files = [
        "slc_20200303.tif",
        "slc_20210101.tif",
        "slc_20190101.tif",
        "slc_20180101.tif",
    ]
    expected_dates = [
        [datetime.datetime(2018, 1, 1)],
        [datetime.datetime(2019, 1, 1)],
        [datetime.datetime(2020, 3, 3)],
        [datetime.datetime(2021, 1, 1)],
    ]
    expected_files = sorted(files)

    sorted_files, sorted_dates = _dates.sort_files_by_date(files)
    assert sorted_files == expected_files
    assert sorted_dates == expected_dates

    # Check that it works with Path objects
    files = [Path(f) for f in files]
    sorted_files, sorted_dates = _dates.sort_files_by_date(files)
    assert [Path(f) for f in expected_files] == sorted_files
    assert sorted_dates == expected_dates

    # check it ignores paths leading up to file name
    files = [
        "/usr/20200101/asdf20180101.tif",
        "/usr/19900101/asdf20190101.tif",
        "/usr/20000101/asdf20200303.tif",
        "/usr/19990101/asdf20210101.tif",
    ]
    sorted_files, sorted_dates = _dates.sort_files_by_date(files)
    assert sorted_files == files  # they were in sorted order already
    assert sorted_dates == expected_dates


def test_sort_files_by_date_interferograms():
    # Make files with 2-date names
    files = [
        "ifg_20200303_20210101.tif",
        "ifg_20200303_20220101.tif",
        "ifg_20190101_20200303.tif",
        "ifg_20180101_20210101.tif",
    ]
    dates = [
        [datetime.datetime(2018, 1, 1), datetime.datetime(2021, 1, 1)],
        [datetime.datetime(2019, 1, 1), datetime.datetime(2020, 3, 3)],
        [datetime.datetime(2020, 3, 3), datetime.datetime(2021, 1, 1)],
        [datetime.datetime(2020, 3, 3), datetime.datetime(2022, 1, 1)],
    ]
    sorted_files, sorted_dates = _dates.sort_files_by_date(files)
    assert sorted_files == sorted(files)  # here lexicographic order is correct
    assert sorted_dates == sorted(dates)


def test_sort_files_with_varying_date_lengths():
    """Check we handle files with varying date lengths, looking at first date only."""
    unsorted_files = [
        "slc_20200101.tif",
        "slc_20210101.tif",
        "slc_20190101.tif",
        "compressed_20180101_20200101.tif",
        "slc_20180102.tif",
        "compressed_20200102_20210101.tif",
    ]
    expected_dates = [
        [datetime.datetime(2018, 1, 1), datetime.datetime(2020, 1, 1)],
        [datetime.datetime(2018, 1, 2)],
        [datetime.datetime(2019, 1, 1)],
        [datetime.datetime(2020, 1, 1)],
        [datetime.datetime(2020, 1, 2), datetime.datetime(2021, 1, 1)],
        [datetime.datetime(2021, 1, 1)],
    ]

    sorted_files, sorted_dates = _dates.sort_files_by_date(unsorted_files)
    assert sorted_files == [
        "compressed_20180101_20200101.tif",
        "slc_20180102.tif",
        "slc_20190101.tif",
        "slc_20200101.tif",
        "compressed_20200102_20210101.tif",
        "slc_20210101.tif",
    ]
    assert sorted_dates == expected_dates


def test_sort_by_date_different_fmt():
    # Check that it works with different date formats
    files = [
        "slc_2020-03-03.tif",
        "slc_2021-01-01.tif",
        "slc_2019-01-01.tif",
        "slc_2018-01-01.tif",
    ]
    expected_dates = [
        [datetime.datetime(2018, 1, 1)],
        [datetime.datetime(2019, 1, 1)],
        [datetime.datetime(2020, 3, 3)],
        [datetime.datetime(2021, 1, 1)],
    ]
    expected_files = sorted(files)

    sorted_files, sorted_dates = _dates.sort_files_by_date(
        files, file_date_fmt="%Y-%m-%d"
    )
    assert sorted_files == expected_files
    assert sorted_dates == expected_dates

    files = [
        "slc_2020-03-03_2021-01-01.tif",
        "slc_2020-03-03_2022-01-01.tif",
        "slc_2019-01-01_2020-03-03.tif",
        "slc_2018-01-01_2021-01-01.tif",
    ]
    expected_dates = [
        [datetime.datetime(2018, 1, 1), datetime.datetime(2021, 1, 1)],
        [datetime.datetime(2019, 1, 1), datetime.datetime(2020, 3, 3)],
        [datetime.datetime(2020, 3, 3), datetime.datetime(2021, 1, 1)],
        [datetime.datetime(2020, 3, 3), datetime.datetime(2022, 1, 1)],
    ]
    expected_files = sorted(files)

    sorted_files, sorted_dates = _dates.sort_files_by_date(
        files, file_date_fmt="%Y-%m-%d"
    )
    assert sorted_files == expected_files
    assert sorted_dates == expected_dates


def test_group_by_date():
    files = [
        "slc_20180101.tif",
        "slc_1_20190101.tif",
        "slc_2_20190101.tif",
        "slc_20210101.tif",
    ]
    expected = {
        (datetime.datetime(2018, 1, 1),): [
            "slc_20180101.tif",
        ],
        (datetime.datetime(2019, 1, 1),): [
            "slc_1_20190101.tif",
            "slc_2_20190101.tif",
        ],
        (datetime.datetime(2021, 1, 1),): [
            "slc_20210101.tif",
        ],
    }
    assert expected == _dates.group_by_date(files)


def test_group_by_date_with_idx():
    files = [
        "slc_20170101_20180101.tif",
        "slc_20170101_20190101.tif",
        "slc_20170101_20210101.tif",
    ]
    expected = {
        (
            datetime.datetime(2017, 1, 1),
            datetime.datetime(2018, 1, 1),
        ): [
            "slc_20170101_20180101.tif",
        ],
        (
            datetime.datetime(2017, 1, 1),
            datetime.datetime(2019, 1, 1),
        ): [
            "slc_20170101_20190101.tif",
        ],
        (
            datetime.datetime(2017, 1, 1),
            datetime.datetime(2021, 1, 1),
        ): [
            "slc_20170101_20210101.tif",
        ],
    }
    assert expected == _dates.group_by_date(files)

    expected_idx1 = {
        (datetime.datetime(2018, 1, 1),): [
            "slc_20170101_20180101.tif",
        ],
        (datetime.datetime(2019, 1, 1),): [
            "slc_20170101_20190101.tif",
        ],
        (datetime.datetime(2021, 1, 1),): [
            "slc_20170101_20210101.tif",
        ],
    }
    assert expected_idx1 == _dates.group_by_date(files, date_idx=1)

    expected_idx0 = {
        (datetime.datetime(2017, 1, 1),): [
            "slc_20170101_20180101.tif",
            "slc_20170101_20190101.tif",
            "slc_20170101_20210101.tif",
        ]
    }
    assert expected_idx0 == _dates.group_by_date(files, date_idx=0)
