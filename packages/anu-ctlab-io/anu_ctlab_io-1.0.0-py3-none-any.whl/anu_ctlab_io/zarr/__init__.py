from pathlib import Path
from typing import Any

import dask.array as da
import zarr

from anu_ctlab_io._dataset import Dataset
from anu_ctlab_io._datatype import DataType
from anu_ctlab_io._voxel_properties import VoxelUnit

__all__ = ["dataset_from_zarr"]


def dataset_from_zarr(path: Path, **kwargs: Any) -> Dataset:
    try:
        data: da.Array = da.from_zarr(path, **kwargs)  # type: ignore[no-untyped-call]
        za = zarr.open_array(
            path, zarr_format=3
        )  # can't get a dask array directly from this
        attrs: dict[str, Any] = dict(za.attrs)["mango"]  # type: ignore[assignment]
        dimension_names: tuple[str, ...] = za.metadata.dimension_names  # type: ignore[assignment, union-attr]
        voxel_unit = VoxelUnit.from_str(attrs["voxel_unit"])
        voxel_size = attrs["voxel_size_xyz"]
        datatype = DataType.from_basename(attrs["basename"])

    except zarr.errors.NodeTypeValidationError:  # happens if this is an ome
        zg = zarr.open_group(path, zarr_format=3)
        multiscale = zg.metadata.attributes["ome"]["multiscales"][0]
        component_path = multiscale["datasets"][0]["path"]
        data = da.from_zarr(path, component=component_path, **kwargs)  # type: ignore[no-untyped-call]
        attrs = dict(zg.attrs)["mango"]  # type: ignore[assignment]
        datatype = DataType.from_basename(attrs["basename"])
        dimension_names = tuple([x["name"] for x in multiscale["axes"]])
        voxel_unit_list: tuple[str, ...] = tuple(
            [x["unit"] for x in multiscale["axes"]]
        )
        assert (
            voxel_unit_list[0] == voxel_unit_list[1]
            and voxel_unit_list[1] == voxel_unit_list[2]
        )  # we only use one unit, so this must hold
        voxel_unit = VoxelUnit.from_str(voxel_unit_list[0])

        voxel_size = multiscale["datasets"][0]["coordinateTransformations"][0]["scale"]

    return Dataset(
        data=data,
        dimension_names=dimension_names,
        datatype=datatype,
        voxel_unit=voxel_unit,
        voxel_size=voxel_size,
        history=attrs["history"],
    )
