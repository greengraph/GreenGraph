# %%

import bw2io as bi
import bw2data as bd
import bw2calc as bc


if 'USEEIO-1.1' not in bd.projects:
    bi.install_project(project_key="USEEIO-1.1", overwrite_existing=True)
else:
    pass
bd.projects.set_current(name='USEEIO-1.1')

db = bd.Database('USEEIO-1.1')

list_db_products = [node['name'] for node in db if 'product' in node['type']]
dict_methods = {i[-1]:[i] for i in bd.methods}

chosen_activity = bd.utils.get_node(
    database = 'USEEIO-1.1',
    name = list_db_products[42],
    type = 'product',
    location = 'United States'
)

for method_key in dict_methods.keys():
    lca = bc.LCA( 
            demand={chosen_activity: 100}, 
            method=dict_methods[method_key][0],
        )
    lca.lci()
    lca.lcia()