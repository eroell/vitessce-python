import os
from os.path import join
import tempfile
import math

import numpy as np
import pandas as pd
import negspy.coordinates as nc
import zarr
from numcodecs import Zlib
from scipy.sparse import csr_matrix
from scipy.sparse import coo_matrix


from starlette.responses import JSONResponse, UJSONResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles

from .constants import DataType as dt, FileType as ft
from .entities import Cells, CellSets

class AbstractWrapper:
    """
    An abstract class that can be extended when
    implementing custom dataset object wrapper classes. 
    """

    def __init__(self, **kwargs):
        """
        Abstract constructor to be inherited by dataset wrapper classes.

        :param str base_url: An optional base URL to use in dataset file definitions.
        """
        self._base_url = kwargs['base_url'] if 'base_url' in kwargs else None

    def get_cells(self, port, dataset_uid, obj_i):
        """
        Get the file definitions and server routes
        corresponding to the ``cells`` data type.

        :param int port: The web server port, meant to be used in the localhost URLs in the file definitions.
        :param str dataset_uid: The unique identifier for the dataset parent of this data object.
        :param int obj_i: The index of this data object child within its dataset parent.

        :returns: The file definitions and server routes.
        :rtype: tuple[list[dict], list[starlette.routing.Route]]
        """
        raise NotImplementedError()

    def get_cell_sets(self, port, dataset_uid, obj_i):
        """
        Get the file definitions and server routes
        corresponding to the ``cell-sets`` data type.

        :param int port: The web server port, meant to be used in the localhost URLs in the file definitions.
        :param str dataset_uid: The unique identifier for the dataset parent of this data object.
        :param int obj_i: The index of this data object child within its dataset parent.

        :returns: The file definitions and server routes.
        :rtype: tuple[list[dict], list[starlette.routing.Route]]
        """
        raise NotImplementedError()

    def get_raster(self, port, dataset_uid, obj_i):
        """
        Get the file definitions and server routes
        corresponding to the ``raster`` data type.

        :param int port: The web server port, meant to be used in the localhost URLs in the file definitions.
        :param str dataset_uid: The unique identifier for the dataset parent of this data object.
        :param int obj_i: The index of this data object child within its dataset parent.

        :returns: The file definitions and server routes.
        :rtype: tuple[list[dict], list[starlette.routing.Route]]
        """
        raise NotImplementedError()

    def get_molecules(self, port, dataset_uid, obj_i):
        """
        Get the file definitions and server routes
        corresponding to the ``molecules`` data type.

        :param int port: The web server port, meant to be used in the localhost URLs in the file definitions.
        :param str dataset_uid: The unique identifier for the dataset parent of this data object.
        :param int obj_i: The index of this data object child within its dataset parent.

        :returns: The file definitions and server routes.
        :rtype: tuple[list[dict], list[starlette.routing.Route]]
        """
        raise NotImplementedError()

    def get_neighborhoods(self, port, dataset_uid, obj_i):
        """
        Get the file definitions and server routes
        corresponding to the ``neighborhoods`` data type.

        :param int port: The web server port, meant to be used in the localhost URLs in the file definitions.
        :param str dataset_uid: The unique identifier for the dataset parent of this data object.
        :param int obj_i: The index of this data object child within its dataset parent.

        :returns: The file definitions and server routes.
        :rtype: tuple[list[dict], list[starlette.routing.Route]]
        """
        raise NotImplementedError()

    def get_expression_matrix(self, port, dataset_uid, obj_i):
        """
        Get the file definitions and server routes
        corresponding to the ``expression-matrix`` data type.

        :param int port: The web server port, meant to be used in the localhost URLs in the file definitions.
        :param str dataset_uid: The unique identifier for the dataset parent of this data object.
        :param int obj_i: The index of this data object child within its dataset parent.

        :returns: The file definitions and server routes.
        :rtype: tuple[list[dict], list[starlette.routing.Route]]
        """
        raise NotImplementedError()

    def get_genomic_profiles(self, port, dataset_uid, obj_i):
        """
        Get the file definitions and server routes
        corresponding to the ``genomic-profiles`` data type.

        :param int port: The web server port, meant to be used in the localhost URLs in the file definitions.
        :param str dataset_uid: The unique identifier for the dataset parent of this data object.
        :param int obj_i: The index of this data object child within its dataset parent.

        :returns: The file definitions and server routes.
        :rtype: tuple[list[dict], list[starlette.routing.Route]]
        """
        raise NotImplementedError()

    def _create_response_json(self, data_json):
        """
        Helper function that can be used for creating JSON responses.

        :param dict data_json: The data to return as JSON in the response body.
        :returns: The response handler function.
        :rtype: function
        """
        async def response_func(req):
            return UJSONResponse(data_json)
        return response_func

    def _get_data(self, data_type, port, dataset_uid, obj_i):
        if data_type == dt.CELLS:
            return self.get_cells(port, dataset_uid, obj_i)
        elif data_type == dt.CELL_SETS:
            return self.get_cell_sets(port, dataset_uid, obj_i)
        elif data_type == dt.RASTER:
            return self.get_raster(port, dataset_uid, obj_i)
        elif data_type == dt.MOLECULES:
            return self.get_molecules(port, dataset_uid, obj_i)
        elif data_type == dt.NEIGHBORHOODS:
            return self.get_neighborhoods(port, dataset_uid, obj_i)
        elif data_type == dt.EXPRESSION_MATRIX:
            return self.get_expression_matrix(port, dataset_uid, obj_i)
        elif data_type == dt.GENOMIC_PROFILES:
            return self.get_genomic_profiles(port, dataset_uid, obj_i)

    def _get_url(self, port, dataset_uid, obj_i, suffix):
        # A base URL is defined for this so this is used outside of Jupyter notebook.
        if self._base_url is not None:
            return f"{self._base_url}/{dataset_uid}/{obj_i}/{suffix}"
        return f"http://localhost:{port}/{dataset_uid}/{obj_i}/{suffix}"

    def _get_route(self, dataset_uid, obj_i, suffix):
        return f"/{dataset_uid}/{obj_i}/{suffix}"


class OmeTiffWrapper(AbstractWrapper):

    def __init__(self, img_path, offsets_path=None, name="", **kwargs):
        super().__init__(**kwargs)
        self.img_path = img_path
        self.offsets_path = offsets_path
        self.name = name

    def create_raster_json(self, img_url, offsets_url):
        raster_json = {
            "schemaVersion": "0.0.2",
            "images": [
                {
                    "name": self.name,
                    "type": "ome-tiff",
                    "url": img_url,
                    "metadata": {
                        **({
                            "omeTiffOffsetsUrl": offsets_url,
                        } if offsets_url is not None else {})
                    }
                }
            ],
        }
        return raster_json

    def _get_offsets_dir(self):
        return os.path.dirname(self.offsets_path)
    
    def _get_offsets_filename(self):
        return os.path.basename(self.offsets_path)

    def get_raster(self, port, dataset_uid, obj_i):
        img_dir_path, img_url = self.img_path, self._get_url(port, dataset_uid, obj_i, "raster_img")
        offsets_dir_path, offsets_url = (None, None) if self.offsets_path is None else (self._get_offsets_dir(), self._get_url(port, dataset_uid, obj_i, join("raster_offsets", self._get_offsets_filename())))

        raster_json = self.create_raster_json(img_url, offsets_url)

        obj_routes = [
            Mount(self._get_route(dataset_uid, obj_i, "raster_img"),
                  app=StaticFiles(directory=img_dir_path, html=False, check_dir=False)),
            Route(self._get_route(dataset_uid, obj_i, "raster"),
                  self._create_response_json(raster_json))
        ]
        if self.offsets_path is not None:
            obj_routes.append(
                Mount(self._get_route(dataset_uid, obj_i, "raster_offsets"),
                      app=StaticFiles(directory=offsets_dir_path, html=False, check_dir=False))
            )

        obj_file_defs = [
            {
                "type": dt.RASTER.value,
                "fileType": ft.RASTER_JSON.value,
                "url": self._get_url(port, dataset_uid, obj_i, "raster")
            }
        ]

        return obj_file_defs, obj_routes


class OmeZarrWrapper(AbstractWrapper):

    def __init__(self, z, name="", **kwargs):
        super().__init__(**kwargs)
        self.z = z
        self.name = name

    def create_raster_json(self, img_url):
        raster_json = {
            "schemaVersion": "0.0.2",
            "images": [
                {
                    "name": self.name,
                    "type": "zarr",
                    "url": img_url,
                    "metadata": {
                        "dimensions": [
                            {
                                "field": "channel",
                                "type": "nominal",
                                "values": [
                                    "DAPI - Hoechst (nuclei)",
                                    "FITC - Laminin (basement membrane)",
                                    "Cy3 - Synaptopodin (glomerular)",
                                    "Cy5 - THP (thick limb)"
                                ]
                            },
                            {
                                "field": "y",
                                "type": "quantitative",
                                "values": None
                            },
                            {
                                "field": "x",
                                "type": "quantitative",
                                "values": None
                            }
                        ],
                        "isPyramid": True,
                        "transform": {
                            "scale": 1,
                            "translate": {
                                "x": 0,
                                "y": 0,
                            }
                        }
                    }
                }
            ],
        }
        return raster_json

    def get_raster(self, port, dataset_uid, obj_i):
        obj_routes = []
        obj_file_defs = []

        if type(self.z) == zarr.hierarchy.Group:
            img_dir_path = self.z.store.path

            raster_json = self.create_raster_json(
                self._get_url(port, dataset_uid, obj_i, "raster_img"),
            )

            obj_routes = [
                Mount(self._get_route(dataset_uid, obj_i, "raster_img"),
                        app=StaticFiles(directory=img_dir_path, html=False)),
                Route(self._get_route(dataset_uid, obj_i, "raster"),
                        self._create_response_json(raster_json))
            ]
            obj_file_defs = [
                {
                    "type": dt.RASTER.value,
                    "fileType": ft.RASTER_JSON.value,
                    "url": self._get_url(port, dataset_uid, obj_i, "raster")
                }
            ]

        return obj_file_defs, obj_routes


class AnnDataWrapper(AbstractWrapper):
    def __init__(self, adata, use_highly_variable_genes=True, **kwargs):
        super().__init__(**kwargs)
        self.adata = adata
        self.tempdir = tempfile.mkdtemp()
        self.use_highly_variable_genes = use_highly_variable_genes

    def create_cells_json(self):
        adata = self.adata
        available_embeddings = list(adata.obsm.keys())

        cell_ids = adata.obs.index.tolist()
        cells = Cells(cell_ids=cell_ids)
        for e in available_embeddings:
            mapping = adata.obsm[e][:, 0:2].tolist()
            cells.add_mapping(e, mapping)
        return cells.json

    def create_cell_sets_json(self):
        adata = self.adata
        cell_sets = CellSets(first_node_name = 'Clusters')

        cell_ids = adata.obs.index.tolist()
        cluster_ids = adata.obs['CellType'].unique().tolist()
        cell_cluster_ids = adata.obs['CellType'].values.tolist()

        cell_cluster_tuples = list(zip(cell_ids, cell_cluster_ids))

        for cluster_id in cluster_ids:
            cell_set = [
                str(cell_id)
                for cell_id, cell_cluster_id in cell_cluster_tuples
                if cell_cluster_id == cluster_id
            ]
            cell_sets.add_node(str(cluster_id), ['Clusters'], cell_set)

        return cell_sets.json
    
    def create_exp_matrix_zarr(self, zarr_filepath):
        adata = self.adata
        gexp_arr = adata.X

        cell_list = adata.obs.index.values.tolist()
        gene_list = adata.var.index.values.tolist()

        if type(gexp_arr) == csr_matrix:
            # Convert from SciPy sparse format to NumPy dense format
            gexp_arr = gexp_arr.toarray()
        
        if self.use_highly_variable_genes and 'highly_variable' in adata.var.columns.values.tolist():
            # Restrict the gene expression matrix to only the genes marked as highly variable
            gene_list = adata.var.index[adata.var['highly_variable']].values.tolist()
            gexp_arr = gexp_arr[:,adata.var['highly_variable'].values]

        
        # Re-scale the gene expression values between 0 and 255
        gexp_arr_min = gexp_arr.min()
        gexp_arr_max = gexp_arr.max()
        gexp_arr_range = gexp_arr_max - gexp_arr_min
        gexp_arr_ratio = 255 / gexp_arr_range

        gexp_norm_arr = (gexp_arr - gexp_arr_min) * gexp_arr_ratio
    
        z = zarr.open(
            zarr_filepath,
            mode='w',
            shape=gexp_norm_arr.shape,
            dtype='uint8',
            compressor=Zlib(level=1)
        )

        z[:] = gexp_norm_arr
        # observations: cells (rows)
        z.attrs["rows"] = cell_list
        # variables: genes (columns)
        z.attrs["cols"] = gene_list
        
        return

    def get_cells(self, port, dataset_uid, obj_i):
        obj_routes = []
        obj_file_defs = []

        cells_json = self.create_cells_json()

        obj_routes = [
            Route(self._get_route(dataset_uid, obj_i, "cells"),
                    self._create_response_json(cells_json)),
        ]
        obj_file_defs = [
            {
                "type": dt.CELLS.value,
                "fileType": ft.CELLS_JSON.value,
                "url": self._get_url(port, dataset_uid, obj_i, "cells")
            }
        ]

        return obj_file_defs, obj_routes

    def get_cell_sets(self, port, dataset_uid, obj_i):
        obj_routes = []
        obj_file_defs = []

            
        cell_sets_json = self.create_cell_sets_json()

        obj_routes = [
            Route(self._get_route(dataset_uid, obj_i, "cell-sets"),
                    self._create_response_json(cell_sets_json)),
        ]
        obj_file_defs = [
            {
                "type": dt.CELL_SETS.value,
                "fileType": ft.CELL_SETS_JSON.value,
                "url": self._get_url(port, dataset_uid, obj_i, "cell-sets")
            }
        ]

        return obj_file_defs, obj_routes
    
    def get_expression_matrix(self, port, dataset_uid, obj_i):
        obj_routes = []
        obj_file_defs = []

        zarr_tempdir = self.tempdir
        zarr_filepath = join(zarr_tempdir, 'matrix.zarr')

        self.create_exp_matrix_zarr(zarr_filepath)

        if zarr_tempdir is not None:
            obj_routes = [
                Mount(self._get_route(dataset_uid, obj_i, "expression"),
                    app=StaticFiles(directory=os.path.dirname(zarr_filepath), html=False, check_dir=False)),
            ]

            obj_file_defs = [
                {
                    "type": dt.EXPRESSION_MATRIX.value,
                    "fileType": ft.EXPRESSION_MATRIX_ZARR.value,
                    "url": self._get_url(port, dataset_uid, obj_i, "expression/matrix.zarr")
                }
            ]

        return obj_file_defs, obj_routes
        


class LoomWrapper(AbstractWrapper):

    def __init__(self, loom, **kwargs):
        super().__init__(**kwargs)
        self.loom = loom

    def get_cells(self, port, dataset_uid, obj_i):
        obj_routes = []
        obj_file_defs = []

        # TODO: append routes
        # TODO: add file definitions
 
        return obj_file_defs, obj_routes

class SnapWrapper(AbstractWrapper):

    # The Snap file is difficult to work with.
    # For now we can use the processed cell-by-bin MTX file
    # However, the HuBMAP pipeline currently computes this with resolution 5000
    # TODO: Make a PR to sc-atac-seq-pipeline to output this at a higher resolution (e.g. 200)
    # https://github.com/hubmapconsortium/sc-atac-seq-pipeline/blob/develop/bin/snapAnalysis.R#L93

    def __init__(self, in_mtx, in_barcodes_df, in_bins_df, in_clusters_df, starting_resolution=5000):
        self.in_mtx = in_mtx # scipy.sparse.coo.coo_matrix (filtered_cell_by_bin.mtx)
        self.in_barcodes_df = in_barcodes_df # pandas dataframe (barcodes.txt)
        self.in_bins_df = in_bins_df # pandas dataframe (bins.txt)
        self.in_clusters_df = in_clusters_df # pandas dataframe (umap_coords_clusters.csv)

        self.tempdir = tempfile.mkdtemp()

        self.starting_resolution = starting_resolution

        # Convert to dense matrix if sparse.
        if type(in_mtx) == coo_matrix:
            self.in_mtx = in_mtx.toarray()


    def create_genomic_multivec_zarr(self, zarr_filepath):
        in_mtx = self.in_mtx
        in_clusters_df = self.in_clusters_df
        in_barcodes_df = self.in_barcodes_df
        in_bins_df = self.in_bins_df

        starting_resolution = self.starting_resolution

        # The bin datafram consists of one column like chrName:binStart-binEnd
        def convert_bin_name_to_chr_name(bin_name):
            try:
                return bin_name[:bin_name.index(':')]
            except ValueError:
                return np.nan
        def convert_bin_name_to_chr_start(bin_name):
            try:
                return int(bin_name[bin_name.index(':')+1:bin_name.index('-')])
            except ValueError:
                return np.nan
        def convert_bin_name_to_chr_end(bin_name):
            try:
                return int(bin_name[bin_name.index('-')+1:])
            except ValueError:
                return np.nan
        
        # The genome assembly is GRCh38 but the chromosome names in the bin names do not start with the "chr" prefix.
        # This is incompatible with the chromosome names from `negspy`, so we need to append the prefix.
        in_bins_df[0] = in_bins_df[0].apply(lambda x: "chr" + x)
        
        in_bins_df["chr_name"] = in_bins_df[0].apply(convert_bin_name_to_chr_name)
        in_bins_df["chr_start"] = in_bins_df[0].apply(convert_bin_name_to_chr_start)
        in_bins_df["chr_end"] = in_bins_df[0].apply(convert_bin_name_to_chr_end)

        # Drop any rows that had incorrect bin strings (missing a chromosome name, bin start, or bin end value).
        in_bins_df = in_bins_df.dropna(subset=["chr_name", "chr_start", "chr_end"])

        # Ensure that the columns have the expect types.
        in_bins_df["chr_name"] = in_bins_df["chr_name"].astype(str)
        in_bins_df["chr_start"] = in_bins_df["chr_start"].astype(int)
        in_bins_df["chr_end"] = in_bins_df["chr_end"].astype(int)

        # Create the Zarr store for the outputs.
        out_f = zarr.open(zarr_filepath, mode='w')
        compressor = Zlib(level=1)

        # Create the chromosomes group in the output store.
        chromosomes_group = out_f.create_group("chromosomes")

        # Prepare to fill in the chromosomes datasets.
        
        # "SnapTools performs quantification using a specified aligner, and HuBMAP has standardized on BWA with the GRCh38 reference genome"
        # Reference: https://github.com/hubmapconsortium/sc-atac-seq-pipeline/blob/bb023f95ca3330128bfef41cc719ffcb2ee6a190/README.md
        chromosomes = nc.get_chromorder('hg38')
        chromosomes = [ str(chr_name) for chr_name in chromosomes[:25] ] # TODO: should more than chr1-chrM be used?
        num_chromosomes = len(chromosomes)
        chroms_length_arr = np.array([ nc.get_chrominfo('hg38').chrom_lengths[x] for x in chromosomes ], dtype="i8")
        chroms_cumsum_arr = np.concatenate((np.array([0]), np.cumsum(chroms_length_arr)))

        chromosomes_set = set(chromosomes)
        chrom_name_to_length = dict(zip(chromosomes, chroms_length_arr))
        chrom_name_to_cumsum = dict(zip(chromosomes, chroms_cumsum_arr))

        # Prepare to fill in resolutions datasets.
        resolutions = [ starting_resolution*(2**x) for x in range(16) ]
        resolution_exps = [ (2**x) for x in range(16) ]

        # Fill in data for each cluster.
        in_clusters_df["cluster"] = in_clusters_df["cluster"].astype(str)
        cluster_ids = in_clusters_df["cluster"].unique().tolist()
        cluster_ids.sort(key=int)

        num_clusters = len(cluster_ids)
        
        # Create each chromosome dataset.
        for chr_name, chr_len in chrom_name_to_length.items():
            chr_group = chromosomes_group.create_group(chr_name)
            # Create each resolution group.
            for resolution in resolutions:
                chr_shape = (num_clusters, math.ceil(chr_len / resolution))
                chr_group.create_dataset(str(resolution), shape=chr_shape, dtype="f4", fill_value=np.nan, compressor=compressor)

            # The bins dataframe frustratingly does not contain every bin.
            # We need to figure out which bins are missing.

            # We want to check for missing bins in each chromosome separately,
            # otherwise too much memory is used during the join step.
            chr_bins_in_df = in_bins_df.loc[in_bins_df["chr_name"] == chr_name]
            if chr_bins_in_df.shape[0] == 0:
                # No processing or output is necessary if there is no data for this chromosome.
                # Continue on through all resolutions of this chromosome to the next chromosome.
                continue
            
            # Determine the indices of the matrix at which the bins for this chromosome start and end.
            chr_bin_i_start = int(chr_bins_in_df.head(1).iloc[0].name)
            chr_bin_i_end = int(chr_bins_in_df.tail(1).iloc[0].name) + 1
            
            # Extract the part of the matrix corresponding to the current chromosome.
            chr_mtx = in_mtx[:,chr_bin_i_start:chr_bin_i_end]

            # Create a list of the "ground truth" bins (all bins from position 0 to the end of the chromosome).
            # We will join the input bins onto this dataframe to determine which bins are missing.
            chr_bins_gt_df = pd.DataFrame()
            chr_bins_gt_df["chr_start"] = np.arange(0, math.ceil(chr_len/starting_resolution)) * starting_resolution
            chr_bins_gt_df["chr_end"] = chr_bins_gt_df["chr_start"] + starting_resolution
            chr_bins_gt_df["chr_start"] = chr_bins_gt_df["chr_start"] + 1
            chr_bins_gt_df["chr_start"] = chr_bins_gt_df["chr_start"].astype(int)
            chr_bins_gt_df["chr_end"] = chr_bins_gt_df["chr_end"].astype(int)
            chr_bins_gt_df["chr_name"] = chr_name
            chr_bins_gt_df[0] = chr_bins_gt_df.apply(lambda r: f"{r['chr_name']}:{r['chr_start']}-{r['chr_end']}", axis='columns')
            
            # We will add a new column "i", which should match the _old_ index, so that we will be able join with the data matrix on the original indices.
            # For the new rows, we will add values for the "i" column that are greater than any of the original indices,
            # to prevent any joining with the incoming data matrix onto these bins for which the data is missing.
            chr_bins_in_df = chr_bins_in_df.reset_index(drop=True)
            chr_bins_in_df["i"] = chr_bins_in_df.index.values
            chr_bins_gt_df["i"] = chr_bins_gt_df.index.values + (in_mtx.shape[1] + 1)
            
            # Set the full bin string column as the index of both data frames.
            chr_bins_gt_df = chr_bins_gt_df.set_index(0)
            chr_bins_in_df = chr_bins_in_df.set_index(0)
            
            # Join the input bin subset dataframe right onto the full bin ground truth dataframe.
            chr_bins_in_join_df = chr_bins_in_df.join(chr_bins_gt_df, how='right', lsuffix="", rsuffix="_gt")
            # The bins which were not present in the input will have NaN values in the "i" column.
            # For these rows, we replace the NaN values with the much higher "i_gt" values which will not match to any index of the data matrix.
            chr_bins_in_join_df["i"] = chr_bins_in_join_df.apply(lambda r: r['i'] if pd.notna(r['i']) else r['i_gt'], axis='columns').astype(int)

            # Clean up the joined data frame by removing unnecessary columns.
            chr_bins_in_join_df = chr_bins_in_join_df.drop(columns=['chr_name', 'chr_start', 'chr_end', 'i_gt'])
            chr_bins_in_join_df = chr_bins_in_join_df.rename(columns={'chr_name_gt': 'chr_name', 'chr_start_gt': 'chr_start', 'chr_end_gt': 'chr_end'})
            
            # Create a dataframe from the data matrix, so that we can join to the joined bins dataframe.
            chr_mtx_df = pd.DataFrame(data=chr_mtx.T)
            
            chr_bins_i_df = chr_bins_in_join_df.drop(columns=['chr_name', 'chr_start', 'chr_end'])

            # Join the data matrix dataframe and the bins dataframe.
            # Bins that are missing from the data matrix will have "i" values higher than any of the data matrix dataframe row indices,
            # and therefore the data values for these bins in the resulting joined dataframe will all be NaN.
            chr_mtx_join_df = chr_bins_i_df.join(chr_mtx_df, how='left', on='i')
            # We fill in these NaN values with 0.
            chr_mtx_join_df = chr_mtx_join_df.fillna(value=0.0)
            
            # Drop the "i" column, since it is not necessary now that we have done the join.
            chr_mtx_join_df = chr_mtx_join_df.drop(columns=['i'])
            # Obtain the new full data matrix, which contains values for all bins of the chromosome.
            chr_mtx = chr_mtx_join_df.values.T

            # Fill in the Zarr store with data for each cluster.
            for cluster_index, cluster_id in enumerate(cluster_ids):
                # Get the list of cells in the current cluster.
                cluster_df = in_clusters_df.loc[in_clusters_df["cluster"] == cluster_id]
                cluster_cell_ids = cluster_df.index.values.tolist()
                cluster_num_cells = len(cluster_cell_ids)
                cluster_cells_tf = (in_barcodes_df[0].isin(cluster_cell_ids)).values

                # Get the rows of the data matrix corresponding to the cells in this cluster.
                cluster_cell_by_bin_mtx = chr_mtx[cluster_cells_tf,:]
                # Take the sum of this cluster along the cells axis.
                cluster_profile = cluster_cell_by_bin_mtx.sum(axis=0)

                # Fill in the data for this cluster and chromosome at each resolution.
                for resolution, resolution_exp in zip(resolutions, resolution_exps):
                    arr_len = math.ceil(chr_len / resolution)
                    chr_shape = (num_clusters, arr_len)

                    # Pad the array of values with zeros if necessary before reshaping.
                    values = cluster_profile
                    padding_len = resolution_exp - (values.shape[0] % resolution_exp)
                    if values.shape[0] % resolution_exp > 0:
                        values = np.concatenate((values, np.zeros((padding_len,))))
                    num_tiles = chr_shape[1]
                    # Reshape to be able to sum every `resolution_exp` number of values.
                    arr = np.reshape(values, (-1, resolution_exp)).sum(axis=-1)

                    padding_len = arr_len - arr.shape[0]
                    if padding_len > 0:
                        arr = np.concatenate((arr, np.zeros((padding_len,))))
                    # Set the array in the Zarr store.
                    chromosomes_group[chr_name][str(resolution)][cluster_index,:] = arr
       
        # out_f.attrs should contain the properties required for HiGlass's "tileset_info" requests.
        out_f.attrs['row_infos'] = [
            { "cluster": cluster_id }
            for cluster_id in cluster_ids
        ]
        out_f.attrs['resolutions'] = sorted(resolutions, reverse=True)
        out_f.attrs['shape'] = [ num_clusters, 256 ]
        out_f.attrs['name'] = "SnapTools"
        out_f.attrs['coordSystem'] = "hg38"
        
        # https://github.com/zarr-developers/zarr-specs/issues/50
        out_f.attrs['multiscales'] = [
            {
                "version": "0.1",
                "name": chr_name,
                "datasets": [
                    { "path": f"chromosomes/{chr_name}/{resolution}" }
                    for resolution in sorted(resolutions, reverse=True)
                ],
                "type": "zarr-multivec",
                "metadata": {
                    "chromoffset": int(chrom_name_to_cumsum[chr_name]),
                    "chromsize": int(chr_len),
                }
            }
            for (chr_name, chr_len) in list(zip(chromosomes, chroms_length_arr))
        ]

        return

    def get_genomic_profiles(self, port, dataset_uid, obj_i):
        obj_routes = []
        obj_file_defs = []
        
        zarr_tempdir = self.tempdir
        zarr_filepath = join(zarr_tempdir, 'profiles.zarr')

        print("Please wait, the following conversion is slow")
        self.create_genomic_multivec_zarr(zarr_filepath)

        if zarr_tempdir is not None:
            obj_routes = [
                Mount(self._get_route(dataset_uid, obj_i, "genomic"),
                    app=StaticFiles(directory=os.path.dirname(zarr_filepath), html=False, check_dir=False)),
            ]

            obj_file_defs = [
                {
                    "type": dt.GENOMIC_PROFILES.value,
                    "fileType": ft.GENOMIC_PROFILES_ZARR.value,
                    "url": self._get_url(port, dataset_uid, obj_i, "genomic/profiles.zarr")
                }
            ]

        return obj_file_defs, obj_routes
    

    def _create_cell_sets_json(self):
        in_clusters_df = self.in_clusters_df
        cell_sets_json = {
            "datatype": "cell",
            "version": "0.1.2",
            "tree": [{
                "name": "Clusters",
                "children": []
            }]
        }

        cell_ids = in_clusters_df.index.values.tolist()
        in_clusters_df['cluster'] = in_clusters_df['cluster'].astype(str)
        cluster_ids = in_clusters_df['cluster'].unique().tolist()
        cluster_ids.sort(key=int)
        cell_cluster_ids = in_clusters_df['cluster'].values.tolist()

        cell_cluster_tuples = list(zip(cell_ids, cell_cluster_ids))

        for cluster_id in cluster_ids:
            cell_sets_json["tree"][0]["children"].append({
                "name": str(cluster_id),
                "set": [
                    str(cell_id)
                    for cell_id, cell_cluster_id in cell_cluster_tuples
                    if cell_cluster_id == cluster_id
                ]
            })

        return cell_sets_json

    
    def get_cell_sets(self, port, dataset_uid, obj_i):
        obj_routes = []
        obj_file_defs = []

        cell_sets_json = self._create_cell_sets_json()

        obj_routes = [
            Route(self._get_route(dataset_uid, obj_i, "cell-sets"),
                    self._create_response_json(cell_sets_json)),
        ]
        obj_file_defs = [
            {
                "type": dt.CELL_SETS.value,
                "fileType": ft.CELL_SETS_JSON.value,
                "url": self._get_url(port, dataset_uid, obj_i, "cell-sets")
            }
        ]

        return obj_file_defs, obj_routes
    
    def _create_cells_json(self):
        in_clusters_df = self.in_clusters_df

        cell_ids = in_clusters_df.index.tolist()
        cell_mappings = []

        mapping = in_clusters_df[["umap.1", "umap.2"]].values.tolist()
        cell_mappings.append(list(zip(
            ["UMAP" for i in range(len(mapping))],
            mapping
        )))
        cell_mappings_zip = list(zip(*cell_mappings))
        cells_json = dict(zip(
            cell_ids,
            [
                {'mappings': dict(cell_mapping), 'genes': {}}
                for cell_mapping in cell_mappings_zip
            ]
        ))
        return cells_json
    
    def get_cells(self, port, dataset_uid, obj_i):
        obj_routes = []
        obj_file_defs = []

        cells_json = self._create_cells_json()

        obj_routes = [
            Route(self._get_route(dataset_uid, obj_i, "cells"),
                    self._create_response_json(cells_json)),
        ]
        obj_file_defs = [
            {
                "type": dt.CELLS.value,
                "fileType": ft.CELLS_JSON.value,
                "url": self._get_url(port, dataset_uid, obj_i, "cells")
            }
        ]

        return obj_file_defs, obj_routes