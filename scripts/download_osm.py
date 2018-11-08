from OSMPythonTools.nominatim import Nominatim
from OSMPythonTools.overpass import overpassQueryBuilder, Overpass
import json
import utils

"""
Tools to download OSM nodes and ways. Running this script without arguments
will download, filter, and format way and node data for selected cities.
"""


def download_osm(area_name):
    """ Given an area name, download corresponding OSM elements """

    # Get area id
    nomanatim = Nominatim()
    area_id = nomanatim.query(area_name).areaId()

    # Form and ask query
    overpass = Overpass()
    query = overpassQueryBuilder(area=area_id, elementType=['way', 'node'], out='body')
    osm_data = overpass.query(query, timeout=600)

    # Display results
    utils.display_results(osm_data)

    # Keep elements (ways and nodes) in JSON format
    elements = osm_data.toJSON()['elements']
    return elements


def filter_osm(elements):
    """
    Given OSM element data, filter nodes and ways by custom business logic.
    Return filtered OSM data with the nodes and elements we will use.
    """
    filtered_ways = {}

    filtered_node_ids = set()
    filtered_nodes = {}

    for ele in elements:

        tags = ele.get('tags', {})

        ele_id = ele.get('id')
        element_type = ele.get('type')
        highway_type = tags.get('highway')
        nodes = ele.get('nodes', [])
        highway_length = len(nodes)

        valid_highway_types = ['primary', 'secondary', 'tertiary', 'motorway']

        # Apply exclusion criteria
        if all([element_type == 'way',
                highway_type in valid_highway_types,
                highway_length >= 2]):

            filtered_node_ids = filtered_node_ids.union(set(nodes))
            filtered_ways[ele_id] = ele

    for ele in elements:

        if ele.get('type') == 'node':
            node_id = ele.get('id')
            if node_id in filtered_node_ids:
                filtered_nodes[node_id] = (ele.get('lat'), ele.get('lon'))

    return filtered_ways, filtered_nodes


def download_and_filter_all_regions(regions):

    for region in regions:
        city_name = region.split(",")[0].lower().replace(" ", "")
        print("Downloading city:", city_name)

        raw_data_filename = "../data/raw/raw_osm_{}.json".format(city_name)
        ways_filename = "../data/processed/ways_{}.json".format(city_name)
        nodes_filename = "../data/processed/nodes_{}.json".format(city_name)

        # Download
        elements = download_osm(region)

        # Save raw data
        utils.write_osm(elements, raw_data_filename)

        # Filter
        ways, nodes = filter_osm(elements)
        print(len(ways), "ways in filtered data")
        print(len(nodes), "nodes in filtered data")

        # Save processed data
        utils.write_osm(ways, ways_filename)
        utils.write_osm(nodes, nodes_filename)


def download_portland():

    raw_data_filename = "all_of_portland.json"
    filtered_ways_filename = "ways.json"
    filtered_nodes_filename = "nodes.json"

    # # Uncomment these lines to re-download the data.
    # portland = download_osm("Portland, Oregon")
    # utils.write_osm(portland, raw_data_filename)
    # print("Data written to ", raw_data_filename)

    portland = utils.read_osm(raw_data_filename)
    ways, nodes = filter_osm(portland)
    print(len(portland), "elements in all of portland data")
    print(len(ways), "ways in all of filtered_portland data")
    print(len(nodes), "nodes in all of filtered_portland data")

    utils.write_osm(ways, filtered_ways_filename)
    utils.write_osm(nodes, filtered_nodes_filename)

if __name__ == '__main__':

    # regions = ["Portland, Oregon",
    #            "Boulder, Colorado",
    #            "Seattle, Washington",
    #            "Pittsburgh, Pennsylvania"]

    download_and_filter_all_regions(regions)
