"""
HaloCatalog answer tests



"""

# -----------------------------------------------------------------------------
# Copyright (c) 2017, yt Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

import os

import numpy.testing as npt
import unyt as un

from yt.loaders import load
from yt.testing import requires_file
from yt_astro_analysis.halo_analysis import HaloCatalog
from yt_astro_analysis.halo_analysis.halo_catalog.analysis_operators import add_quantity
from yt_astro_analysis.utilities.testing import data_dir_load


def _nstars(halo):
    sp = halo.data_object
    return (sp["all", "creation_time"] > 0).sum()


add_quantity("nstars", _nstars)


rh0 = "rockstar_halos/halos_0.0.bin"
e64 = "Enzo_64/DD0043/data0043"


@requires_file(rh0)
@requires_file(e64)
def test_halo_quantity(tmp_path):
    data_ds_fn = e64
    halos_ds_fn = rh0
    ds = data_dir_load(data_ds_fn)

    dds = data_dir_load(data_ds_fn)
    hds = data_dir_load(halos_ds_fn)
    hc = HaloCatalog(data_ds=dds, halos_ds=hds, output_dir=str(tmp_path))
    hc.add_callback("sphere")
    hc.add_quantity("nstars")
    hc.create()

    fn = os.path.join(str(tmp_path), str(dds), f"{dds}.0.h5")
    ds = load(fn)
    ad = ds.all_data()
    mi, ma = ad.quantities.extrema("nstars")
    mean = ad.quantities.weighted_average_quantity("nstars", "particle_ones")

    npt.assert_almost_equal(
        un.unyt_array([mean, mi, ma]), [28.53378378, 0.0, 628.0] * un.dimensionless, 8
    )
