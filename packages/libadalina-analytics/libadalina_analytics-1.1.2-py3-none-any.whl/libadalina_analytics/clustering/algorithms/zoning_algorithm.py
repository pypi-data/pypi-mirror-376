from libadalina_analytics.utils import GeometryFormats
from .zoning_model_simple import AdalinaZoningModelSimple
from libadalina_core.sedona_utils import DataFrame, EPSGFormats

from ..models.adalina_zoning_data import AdalinaZoningData
from ..models.adalina_zoning_distance import ClusteringDistance
from ..models.adalina_zoning_solution import AdalinaZoningSolution


def clustering_algorithm(data: DataFrame,
                         epsg: EPSGFormats,
                         geometry_column: str = 'geometry',
                         geometry_format: GeometryFormats = GeometryFormats.WKT,
                         weight_column: str | None = None,
                         k_min: int | None = None,
                         k_max: int | None = None,
                         f_min: float | None = None,
                         distances: list[ClusteringDistance] | None = None,
                         timelimit: int = 60) -> AdalinaZoningSolution | None:
    """
    Create clusters of similar areas minimizing their internal distance.

    Distances are given as a list of ClusteringDistance objects, each containing:
    - name: the name of the column in the input data
    - weight: the weight of the distance in the overall distance calculation
    - function: the distance function to use

    Parameters
    ----------
    data : pandas.DataFrame or geopandas.GeoDataFrame or pyspark.sql.DataFrame
        The input data containing the geometries and attributes to be clustered.
    epsg : EPSGFormats
        The EPSG format of the input geometries.
    geometry_column : str
        The name of the column containing the geometries. Default is 'geometry'.
    geometry_format : GeometryFormats
        The format of the geometries in the geometry column. Default is GeometryFormats.WKT.
    weight_column : str | None
        The name of the column to use as the optional weight of an area. Default is None.
    k_min : int | None
        The minimum number of clusters to create. If None, defaults to 1.
    k_max : int | None
        The maximum number of clusters to create. Default is None.
    f_min : float | None
        The minimum total weight of a cluster. If None, defaults to 1.
    distances : list[ClusteringDistance] | None
        List of distances to use for clustering. If None, no only distance between area centroids will be used.
        Each distance is represented as a ClusteringDistance object that includes the name of the column,
        the weight of the distance, and the distance function to use.
    timelimit : int
        The maximum time (in seconds) to run the algorithm. Default is 60 seconds.

    Returns
    -------
    AdalinaZoningSolution

    """
    user_input: dict = {
        "epsg": epsg,
        "geometry_type": geometry_format,
        "geometry": geometry_column,
        "timelimit": timelimit
    }
    if weight_column is not None:
        user_input["weight"] = weight_column
    if k_min is not None:
        user_input["Kmin"] = k_min
    if k_max is not None:
        user_input["Kmax"] = k_max
    if f_min is not None:
        user_input["Fmin"] = f_min
    if distances is not None:
        user_input["distances"] = [{
            'name': distance.name,
            'weight': distance.weight,
            'func': distance.function
        } for distance in distances]

    data = AdalinaZoningData.from_Amelia(amelia_file=data, user_input=user_input)

    model = AdalinaZoningModelSimple(data)

    _ = model.run(timelimit=timelimit)

    sol = model.get_solution(False)

    return sol
