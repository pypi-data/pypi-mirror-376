import pandas as pd
import plotly.graph_objs as go
from pytest import raises

from bcn_rainfall_core.models import MonthlyRainfall
from bcn_rainfall_core.utils import DataFormatError, Label, Month
from tst.test_config import CONFIG
from tst.test_rainfall import RAINFALL, begin_year, end_year, normal_year

MONTHLY_RAINFALL = RAINFALL.monthly_rainfalls[Month.MAY.value]


class TestMonthlyRainfall:
    @staticmethod
    def test_load_yearly_rainfall():
        data = MONTHLY_RAINFALL.load_yearly_rainfall()

        assert isinstance(data, pd.DataFrame)

    @staticmethod
    def test_load_rainfall():
        data = MONTHLY_RAINFALL.load_rainfall(
            start_month=Month.JUNE, end_month=Month.OCTOBER
        )
        assert isinstance(data, pd.DataFrame)
        assert len(data.columns) == 2
        assert Label.YEAR in data and Label.RAINFALL in data

    @staticmethod
    def test_load_rainfall_fails_because_data_format_error():
        with raises(DataFormatError):
            MonthlyRainfall(
                pd.DataFrame(),
                Month.MAY,
                start_year=CONFIG.get_data_settings.start_year,
                round_precision=CONFIG.get_data_settings.rainfall_precision,
            )

    @staticmethod
    def test_get_yearly_rainfall():
        data = MONTHLY_RAINFALL.get_yearly_rainfall(begin_year, end_year)

        assert isinstance(data, pd.DataFrame)
        assert len(data) == end_year - begin_year + 1

    @staticmethod
    def test_export_as_csv():
        csv_as_str = MONTHLY_RAINFALL.export_as_csv(begin_year, end_year)

        assert isinstance(csv_as_str, str)

    @staticmethod
    def test_get_average_yearly_rainfall():
        avg_rainfall = MONTHLY_RAINFALL.get_average_yearly_rainfall(
            begin_year, end_year
        )

        assert isinstance(avg_rainfall, float)

    @staticmethod
    def test_get_normal():
        normal = MONTHLY_RAINFALL.get_normal(begin_year)

        assert isinstance(normal, float)

    @staticmethod
    def test_get_years_below_average():
        n_years_below_avg = MONTHLY_RAINFALL.get_years_below_normal(
            normal_year, begin_year, end_year
        )

        assert isinstance(n_years_below_avg, int)
        assert n_years_below_avg <= end_year - begin_year + 1

    @staticmethod
    def test_get_years_above_average():
        n_years_above_avg = MONTHLY_RAINFALL.get_years_above_normal(
            normal_year, begin_year, end_year
        )

        assert isinstance(n_years_above_avg, int)
        assert n_years_above_avg <= end_year - begin_year + 1

    @staticmethod
    def test_get_last_year():
        assert isinstance(MONTHLY_RAINFALL.get_last_year(), int)

    @staticmethod
    def test_get_relative_distance_to_normal():
        relative_distance = MONTHLY_RAINFALL.get_relative_distance_to_normal(
            normal_year, begin_year, end_year
        )

        assert isinstance(relative_distance, float)
        assert -100.0 <= relative_distance

    @staticmethod
    def test_get_standard_deviation():
        std = MONTHLY_RAINFALL.get_rainfall_standard_deviation(
            MONTHLY_RAINFALL.starting_year, MONTHLY_RAINFALL.get_last_year()
        )

        assert isinstance(std, float)

        std_weighted_by_avg = MONTHLY_RAINFALL.get_rainfall_standard_deviation(
            MONTHLY_RAINFALL.starting_year,
            MONTHLY_RAINFALL.get_last_year(),
            weigh_by_average=True,
        )

        assert isinstance(std_weighted_by_avg, float)

    @staticmethod
    def test_get_linear_regression():
        (
            (r2_score, slope),
            linear_regression_values,
        ) = MONTHLY_RAINFALL.get_linear_regression(begin_year, end_year)

        assert isinstance(r2_score, float) and r2_score <= 1
        assert isinstance(slope, float)
        assert isinstance(linear_regression_values, list)
        assert len(linear_regression_values) == end_year - begin_year + 1

    @staticmethod
    def test_get_kmeans():
        kmeans_cluster_count = 5
        n_clusters, predict_data = MONTHLY_RAINFALL.get_kmeans(
            begin_year, end_year, kmeans_cluster_count=kmeans_cluster_count
        )

        assert n_clusters == kmeans_cluster_count
        assert isinstance(predict_data, list)
        assert len(predict_data) == end_year - begin_year + 1

        for cluster_label in predict_data:
            assert isinstance(cluster_label, int)
            assert 0 <= cluster_label < kmeans_cluster_count

    @staticmethod
    def test_bar_figure_of_rainfall_according_to_year():
        bar_fig = MONTHLY_RAINFALL.get_bar_figure_of_rainfall_according_to_year(
            begin_year,
            end_year,
            plot_average=True,
            plot_linear_regression=True,
            kmeans_cluster_count=4,
        )

        assert isinstance(bar_fig, go.Figure)
