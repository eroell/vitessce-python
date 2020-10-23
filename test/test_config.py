import json
import unittest

from vitessce import (
    VitessceConfig,
    CoordinationType as ct,
    Component as cm,
    DataType as dt,
    FileType as ft,
)

class TestConfig(unittest.TestCase):

    def test_config_creation(self):
        vc = VitessceConfig()
        vc_dict = vc.to_dict()
        vc_json = json.dumps(vc_dict)

        self.assertEqual(vc_dict, {
            "version": "1.0.0",
            "name": "",
            "description": "",
            "datasets": [],
            "coordinationSpace": {},
            "layout": [],
            "initStrategy": "auto"
        })
    
    def test_config_add_dataset(self):
        vc = VitessceConfig()
        my_dataset = vc.add_dataset(name='My Dataset')

        vc_dict = vc.to_dict()
        vc_json = json.dumps(vc_dict)

        self.assertEqual(len(vc_dict["datasets"]), 1)
        self.assertEqual(len(vc_dict["coordinationSpace"]["dataset"]), 1)

        self.assertEqual(vc_dict, {
            "version": "1.0.0",
            "name": "",
            "description": "",
            "datasets": [
                {
                    'uid': 'A',
                    'name': 'My Dataset',
                    'files': []
                }
            ],
            'coordinationSpace': {
                'dataset': {
                    'A': 'A'
                },
            },
            "layout": [],
            "initStrategy": "auto"
        })
    
    def test_config_add_dataset_add_files_chained(self):
        vc = VitessceConfig()
        my_dataset = (vc.add_dataset(name='My Chained Dataset')
            .add_file(
                url="http://example.com/cells.json",
                data_type=dt.CELLS,
                file_type=ft.CELLS_JSON,
            ).add_file(
                url="http://example.com/cell_sets.json",
                data_type=dt.CELL_SETS,
                file_type=ft.CELL_SETS_JSON,
            )
        )

        vc_dict = vc.to_dict()
        vc_json = json.dumps(vc_dict)

        self.assertEqual(len(vc_dict["datasets"]), 1)
        self.assertEqual(len(vc_dict["coordinationSpace"]["dataset"]), 1)

        self.assertEqual(vc_dict, {
            "version": "1.0.0",
            "name": "",
            "description": "",
            "datasets": [
                {
                    'uid': 'A',
                    'name': 'My Chained Dataset',
                    'files': [
                        {
                            'url': 'http://example.com/cells.json',
                            'type': 'cells',
                            'fileType': 'cells.json'
                        },
                        {
                            'url': 'http://example.com/cell_sets.json',
                            'type': 'cell-sets',
                            'fileType': 'cell-sets.json'
                        }
                    ]
                },
            ],
            'coordinationSpace': {
                'dataset': {
                    'A': 'A'
                },
            },
            "layout": [],
            "initStrategy": "auto"
        })
    
    def test_config_add_spatial_view(self):
        vc = VitessceConfig()
        my_dataset = vc.add_dataset(name='My Dataset')

        my_view = vc.add_view(my_dataset, cm.SPATIAL)

        vc_dict = vc.to_dict()
        vc_json = json.dumps(vc_dict)

        self.assertEqual(len(vc_dict["datasets"]), 1)
        self.assertEqual(len(vc_dict["layout"]), 1)

        self.assertEqual(vc_dict, {
            "version": "1.0.0",
            "name": "",
            "description": "",
            "datasets": [
                {
                    'uid': 'A',
                    'name': 'My Dataset',
                    'files': []
                }
            ],
            'coordinationSpace': {
                'dataset': {
                    'A': 'A'
                },
            },
            "layout": [
                {
                    'component': 'spatial',
                    'coordinationScopes': {
                        'dataset': 'A',
                    },
                    'h': 1,
                    'w': 1,
                    'x': 0,
                    'y': 0
                }
            ],
            "initStrategy": "auto"
        })
    
    def test_config_add_scatterplot_view_with_mapping(self):
        vc = VitessceConfig()
        my_dataset = vc.add_dataset(name='My Dataset')

        my_view = vc.add_view(my_dataset, cm.SCATTERPLOT, mapping="X_umap")

        vc_dict = vc.to_dict()
        vc_json = json.dumps(vc_dict)

        self.assertEqual(len(vc_dict["datasets"]), 1)
        self.assertEqual(len(vc_dict["layout"]), 1)

        self.assertEqual(vc_dict, {
            "version": "1.0.0",
            "name": "",
            "description": "",
            "datasets": [
                {
                    'uid': 'A',
                    'name': 'My Dataset',
                    'files': []
                }
            ],
            'coordinationSpace': {
                'dataset': {
                    'A': 'A'
                },
                'embeddingType': {
                    'A': 'X_umap'
                }
            },
            "layout": [
                {
                    'component': 'scatterplot',
                    'coordinationScopes': {
                        'dataset': 'A',
                        'embeddingType': 'A'
                    },
                    'h': 1,
                    'w': 1,
                    'x': 0,
                    'y': 0
                }
            ],
            "initStrategy": "auto"
        })
    
    def test_config_add_scatterplot_view_with_embedding_coordinations(self):
        vc = VitessceConfig()
        my_dataset = vc.add_dataset(name='My Dataset')

        my_view = vc.add_view(my_dataset, cm.SCATTERPLOT)

        et_scope, ez_scope, ex_scope, ey_scope = vc.add_coordination(ct.EMBEDDING_TYPE, ct.EMBEDDING_ZOOM, ct.EMBEDDING_TARGET_X, ct.EMBEDDING_TARGET_Y)
        my_view.use_coordination(et_scope, ez_scope, ex_scope, ey_scope)

        et_scope.set_value("X_pca")
        ez_scope.set_value(2)
        ex_scope.set_value(10)
        ey_scope.set_value(11)

        vc_dict = vc.to_dict()
        vc_json = json.dumps(vc_dict)

        self.assertEqual(len(vc_dict["datasets"]), 1)
        self.assertEqual(len(vc_dict["layout"]), 1)

        self.assertEqual(vc_dict, {
            "version": "1.0.0",
            "name": "",
            "description": "",
            "datasets": [
                {
                    'uid': 'A',
                    'name': 'My Dataset',
                    'files': []
                }
            ],
            'coordinationSpace': {
                'dataset': {
                    'A': 'A'
                },
                'embeddingType': {
                    'A': 'X_pca'
                },
                'embeddingZoom': {
                    'A': 2
                },
                'embeddingTargetX': {
                    'A': 10
                },
                'embeddingTargetY': {
                    'A': 11
                },
            },
            "layout": [
                {
                    'component': 'scatterplot',
                    'coordinationScopes': {
                        'dataset': 'A',
                        'embeddingType': 'A',
                        'embeddingZoom': 'A',
                        'embeddingTargetX': 'A',
                        'embeddingTargetY': 'A',
                    },
                    'h': 1,
                    'w': 1,
                    'x': 0,
                    'y': 0
                }
            ],
            "initStrategy": "auto"
        })

    def test_load_config(self):
        vc = VitessceConfig(config={
            "version": "1.0.0",
            "name": "Test name",
            "description": "Test description",
            "datasets": [
                {
                    'uid': 'A',
                    'name': 'My First Dataset',
                    'files': [
                        {
                            'url': 'http://cells.json',
                            'type': 'cells',
                            'fileType': 'cells.json'
                        }
                    ]
                }
            ],
            'coordinationSpace': {
                'dataset': {
                    'A': 'A'
                },
            },
            "layout": [],
            "initStrategy": "auto"
        })

        my_second_dataset = vc.add_dataset(name='My Second Dataset')
        
        vc_dict = vc.to_dict()
        vc_json = json.dumps(vc_dict)

        self.assertEqual(len(vc_dict["datasets"]), 2)
        self.assertEqual(vc_dict, {
            "version": "1.0.0",
            "name": "Test name",
            "description": "Test description",
            "datasets": [
                {
                    'uid': 'A',
                    'name': 'My First Dataset',
                    'files': [
                        {
                            'url': 'http://cells.json',
                            'type': 'cells',
                            'fileType': 'cells.json'
                        }
                    ]
                },
                {
                    'uid': 'B',
                    'name': 'My Second Dataset',
                    'files': []
                }
            ],
            'coordinationSpace': {
                'dataset': {
                    'A': 'A',
                    'B': 'B'
                },
            },
            "layout": [],
            "initStrategy": "auto"
        })

