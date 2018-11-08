from geographiclib.geodesic import Geodesic
import urllib.request
from urllib.parse import urlencode
import requests
import os
import json
import utils
from pprint import pprint
import shutil


def download_street(way, nodes, cautious=True, download=True):
    """
    Download StreetView images for an entire street.

        Strategy:

    Take a StreetView image from the middle node of a way.

    Check if the node is available in Street View. To do this, check that the
    Street View location is within X meters of the node location.

        If not, try the next node.

    Once a suitable node has been found,

        If the street is two-way, take it in both directions
        If one-way, take it in the direction of the road.

    Save the image as <way_id>_<node_id>.jpg in the data/images/ directory.
    """

    way_id = way['id']
    # print(way_id)

    # Get the list of nodes from the way
    potential_nodes = way.get('nodes')

    # Filter out nodes not in our nodes dataset
    potential_nodes = [n for n in potential_nodes if nodes.get(str(n)) is not None]

    # If there are less than 3 nodes in our ndoes dataset, exclude this road
    if len(potential_nodes) < 2:
        print("Not enough nodes found for way:", way_id)
        return

    # Flip reversed oneway streets: consider last node as first (uncommon)
    if way.get('tags', {}).get('oneway') == '-1':
        potential_nodes = list(reversed(potential_nodes))
        print('flipped:', potential_nodes)

    # Get the midpoint node, where we'll take our photo
    l = len(potential_nodes)
    if l % 2 == 0:
        middle_idx = len(potential_nodes) // 2 - 1
    else:
        middle_idx = len(potential_nodes) // 2

    middle_node_id, next_node_id = potential_nodes[middle_idx], potential_nodes[middle_idx + 1]
    # print(middle_node_id, next_node_id)

    middle_node = nodes.get(str(middle_node_id))
    next_node = nodes.get(str(next_node_id))
    # pprint(middle_node)
    # pprint(next_node)

    heading = Geodesic.WGS84.Inverse(*middle_node, *next_node)['azi1']
    location = "{},{}".format(*middle_node)
    query_params = {
        'size': '640x640',
        'location': location,
        'heading': heading,
        'pitch': '0',
        'key': os.environ['GOOGLE_MAPS_API_KEY'],
        'radius': 10
    }

    # Fist, do a meta-data query to see if the image is available.
    metadata_url = 'https://maps.googleapis.com/maps/api/streetview/metadata'
    metadata_link = metadata_url + '?' + urlencode(query_params)
    metadata = requests.get(metadata_link, stream=True).json()
    # print(metadata_link)
    # pprint(metadata)

    if metadata['status'] != 'OK':
        print("No image found.")
        return

    # Check the distance between our OSM node and Street View image
    osm_sv_diff = Geodesic.WGS84.Inverse(
        metadata['location']['lat'],
        metadata['location']['lng'],
        middle_node[0],
        middle_node[1]
    )
    # print(osm_sv_diff)
    print(way_id, ' distance:', osm_sv_diff['s12'])

    image_url = 'https://maps.googleapis.com/maps/api/streetview'
    image_link = image_url + '?' + urlencode(query_params)
    image_filepath = os.path.join('../data/images/',
                                  'w{}_n{}.jpg'.format(way_id, middle_node_id))

    if cautious:
        print("************** CAUTION *******************")
        print("About to download a StreetView Image.")
        input("Press Enter to continue..., or ctrl+c to quit.")

    if download:
        r = requests.get(image_link, stream=True)
        if r.status_code == 200:
            with open(image_filepath, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
            print(image_filepath, "saved.")
        else:
            print('error code:', r.status_code)


def test_street(way_id, ways, nodes):
    download_street(ways[way_id], nodes, cautious=True)


def test_portland():

    ways = utils.read_osm("../data/processed/ways_portland.json")
    nodes = utils.read_osm("../data/processed/nodes_portland.json")

    # Good street
    # test_street("5542164", ways, nodes)

    # Out of portland street
    test_street("5293752", ways, nodes)

    # Long street
    # test_street("5289260", ways, nodes)

    # Bad street - google maps routes us to a nearby but different road
    # test_street("5282846", ways, nodes)
    # These end up 30-40 meters away ???

def test_boulder():

    ways = utils.read_osm("../data/processed/ways_boulder.json")
    nodes = utils.read_osm("../data/processed/nodes_boulder.json")

    # Good street
    # download_street(ways['382375782'], nodes)

    hundred_ways = list(ways.keys())[:100]
    for way in hundred_ways:
        download_street(ways[str(way)], nodes)

    # 10 meter distance node - looks fine to me
    # download_street(ways['8021402'], nodes)


def test_small():

    ways = utils.read_osm("../data/processed/ways_portland.json")
    nodes = utils.read_osm("../data/processed/nodes_portland.json")

    print(len(ways))

    import random
    for _ in range(3):
        way_id = random.choice(list(ways.keys()))
        download_street(ways[str(way_id)], nodes, cautious=False, download=True)

def test_large_no_download():

    ways = utils.read_osm("../data/processed/ways_portland.json")
    nodes = utils.read_osm("../data/processed/nodes_portland.json")

    print(len(ways))

    import random
    for _ in range(100):
        way_id = random.choice(list(ways.keys()))
        download_street(ways[str(way_id)], nodes, cautious=False, download=False)

# def test_large_download():
#     """ NOTE: Each image costs 0.7 cents to download; be careful """
#     ways = utils.read_osm("../data/processed/ways_portland.json")
#     nodes = utils.read_osm("../data/processed/nodes_portland.json")
#
#     print(len(ways))
#
#     import random
#     for _ in range(100):
#         way_id = random.choice(list(ways.keys()))
#         download_street(ways[str(way_id)], nodes, cautious=False, download=False)


def test_complete_no_download():

    for region in ["boulder", "pittsburgh", "seattle", "portland"]:

        ways = utils.read_osm("../data/processed/ways_{}.json".format(region))
        nodes = utils.read_osm("../data/processed/nodes_{}.json".format(region))

        print(region, " - {} ways".format(len(ways)))

        for way_id in ways.keys():
            download_street(ways[way_id], nodes, cautious=False, download=False)


def download_boulder():

    ways = utils.read_osm("../data/processed/ways_boulder.json")
    nodes = utils.read_osm("../data/processed/nodes_boulder.json")

    print(len(ways), "ways")

    for way_id in ways.keys():
        download_street(ways[way_id], nodes, cautious=False, download=True)


def download_region(region):

    ways = utils.read_osm("../data/processed/ways_{}.json".format(region))
    nodes = utils.read_osm("../data/processed/nodes_{}.json".format(region))

    print(len(ways), "ways")

    for way_id in ways.keys():
        download_street(ways[way_id], nodes, cautious=False, download=True)


def download_rest_of_portland():

    ways = utils.read_osm("../data/processed/ways_portland.json")
    nodes = utils.read_osm("../data/processed/nodes_portland.json")

    for way_id in list(ways.keys())[6719:]:
        download_street(ways[way_id], nodes, cautious=False, download=True)


if __name__ == '__main__':

    # test_portland()
    # test_boulder()
    # test_small()
    # test_large_no_download()
    # test_complete_no_download()
    # download_boulder()
    # download_region("pittsburgh")
    # download_region("portland")
    # download_error_causing_image()
    # download_rest_of_portland()
    download_region("seattle")
