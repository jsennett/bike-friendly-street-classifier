from geographiclib.geodesic import Geodesic
import google_streetview.api
import urllib.request
from urllib.parse import urlencode
import requests
import os
import json
import utils
from pprint import pprint

def download_street(way, nodes, cautious=True):
    """
    Download StreetView images for an entire street.

    For now, download an image at every node other than the endpoint nodes.
    For each node in a way's listed nodes:
    - Calculate the direction to orient the StreetView camera, using the
      previous and following nodes
    - Try to download from the StreetView API
    - Record the results of the download in a file

    Input:
    - way is a dictionary object representing the street
    - nodes is a dictionary of relevant nodes

    NOTE: Later on, we may choose to download images for every other node,
    or perhaps just a set number of nodes per street.
    """

    # Get nodes from our way list of nodes.
    # If any are not in Portland, remove them.
    node_ids = [node for node in way.get("nodes") if str(node) in nodes]

    way_id = way.get("id")
    way_length = len(node_ids)
    node_idx_to_download = range(1, way_length - 1)
    print("Downloading from way", way_id)
    print("Downloading nodes from this list:", node_ids)

    street_queries = []
    for idx in node_idx_to_download:

        # Note: we could also determine direction using previous/current node
        # instead of current/next node. We'll see how the results are.
        current_node_id, next_node_id = str(node_ids[idx]), str(node_ids[idx + 1])
        current_node, next_node = nodes[current_node_id], nodes[next_node_id]
        print(current_node, next_node)

        heading = Geodesic.WGS84.Inverse(*current_node, *next_node)['azi1']
        location = "{},{}".format(*current_node)

        # TODO: Modify query params to optimize images for machine learning
        # If we can download lower resolution, that's great - save $$$.
        query_params = {
            'size': '640x640',
            'location': location,
            'heading': heading,
            'pitch': '0',
            'key': os.environ['GOOGLE_MAPS_API_KEY']
        }

        street_queries.append(query_params)

        print("Calling the google maps API with parameters: ", query_params)
        # unique_id = 'sv_{}_{}.jpg'.format(way_id, node_ids[idx])
        # print("Saving as", unique_id)


    if cautious:
        print("************** CAUTION *******************")
        print("About to download {} StreetView Images.".format(len(street_queries)))
        print("************** CAUTION *******************")
        input("Press Enter to continue...")

    way_directory = "../data/images/way{}".format(way_id)
    print("Saved images in {}/".format(way_directory))

    # This line actually calls the download function
    download_images(street_queries, way_directory)

def download_images(queries, outdir, cautious=True):
    """
    Given a list of queries and an outdirectory, download images from the
    StreetView API to the outdirectory.
    """
    # TODO: Don't use this api; it doesn't allow for custom filenames
    results = google_streetview.api.results(queries)

    check_metadata(results.metadata_links, queries)

    if cautious:
        print("************** CAUTION *******************")
        print("About to download {} StreetView Images.".format(len(queries)))
        print("************** CAUTION *******************")
        input("Press Enter to continue...")


    results.preview()
    results.download_links(outdir)

    # # Prepare query parameters
    # url = 'https://maps.googleapis.com/maps/api/streetview?'
    # formatted_params = json.dumps(query_params).encode('utf8')
    #
    # # Make the request
    # req = urllib.request.Request(url, data=formatted_params,
    #                              headers={'content-type': 'application/json'})
    # print(req.data)
    # response = urllib.request.urlopen(req)
    #
    # # Write the image
    # shutil.copyfileobj(response, outfile)

def download_image(url, file_path):
  r = requests.get(url, stream=True)
  if r.status_code == 200: # if request is successful
    with open(file_path, 'wb') as f:
      r.raw.decode_content = True
      shutil.copyfileobj(r.raw, f)



def test_good_street():

    download_street("5542164")

    nodes = {
         40444276: (45.55176, -122.6027257),
         40744671: (45.5518291, -122.6039284),
         2111316434: (45.551774, -122.6035808),
         2111316437: (45.5517769, -122.60343),
         2111316442: (45.5517776, -122.60369),
         2111316444: (45.5517798, -122.6027854),
         2111316447: (45.5517849, -122.6028592),
         2111316450: (45.5517893, -122.6029892),
         2111316454: (45.5517922, -122.6037794)
    }

    way = {'id': 5542164,
           'nodes': [40744671,
                     2111316454,
                     2111316442,
                     2111316434,
                     2111316437,
                     2111316450,
                     2111316447,
                     2111316444,
                     40444276],
            'tags': {'highway': 'residential',
                  'maxspeed': '25 mph',
                  'name': 'Northeast Shaver Street',
                  'sidewalk': 'no',
                  'surface': 'unpaved',
                  'tiger:cfcc': 'A41',
                  'tiger:county': 'Multnomah, OR',
                  'tiger:name_base': 'Shaver',
                  'tiger:reviewed': 'no'},
            'type': 'way'}

    download_street(way, nodes)


def test_bad_street():
    """ This is a bad street that is not correctly mapped """
    nodes = {37387862: (45.4586904, -122.5284042),
             1410599397: (45.4586826, -122.5280183),
             1473499134: (45.4586899, -122.5277703),
             5220887377: (45.4587077, -122.5275113)}

    way = {'type': 'way',
           'id': 5282846,
           'nodes': [37387862, 1410599397, 1473499134, 5220887377],
           'tags': {'highway': 'residential',
                    'maxspeed': '20 mph',
                    'sidewalk': 'no',
                    'tiger:cfcc': 'A41',
                    'tiger:county': 'Clackamas, OR'}}

    download_street(way, nodes)


def test_street(way_id, ways, nodes):
    download_street(ways[way_id], nodes)


def check_metadata(metadata_links, queries):
    """
    TODO: Google StreetView will download the image from the closest reasonable
    street point it can find. If a street we are looking for is not on Google
    Maps, we'll get a nearby street. In this case, we don't know its
    classification; so, we want to flag these streets as unreliable or get
    rid of them.

    To do this, we need to check the downloaded metadata file that comes with
    download_links(). Check if the queried result is close enough (within,
    say, 10 feet); if so, log that the image is reliable. Otherwise, log it as
    an issue.

    Maybe, if the error is in the direction of the road and we can reasonably
    expect that we still have an image of the same road, we can still use the
    image. If we go against the direction of the road, we may have jumped to
    another road.
    """
    metadata = [requests.get(url, stream=True).json() for url in metadata_links]
    pprint(metadata)
    pprint(queries)

    for query, metadata in zip(queries, metadata):

        query_lat, query_lon = query['location'].split(',')
        meta_lat, meta_lon = metadata['location']['lat'], metadata['location']['lng']

        distance = Geodesic.WGS84.Inverse(float(query_lat), float(query_lon),
                                          float(meta_lat), float(meta_lon))['s12']
        print("Distance from query to result in meters:", distance)


if __name__ == '__main__':

    filtered_nodes = utils.read_osm("filtered_nodes.json")
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
