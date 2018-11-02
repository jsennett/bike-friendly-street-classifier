"""
Uilities for downloading and exploring OSM data

Josh Sennett
"""
import json

def write_osm(elements, filename):
    with open(filename, 'w') as f:
        json.dump(elements, f)


def read_osm(filename):
    with open(filename) as f:
        elements = json.load(f)
    return elements


def tag_value_freq(elements, tag):
    """
    Get the frequency of the tag values in a list of elements (nodes or ways)

    For example:
    bicycle_frequencies = tag_value_freq(ways, 'bicycle')
    """
    freq = {}
    for ele in elements:
        value = ele.get('tags', {}).get(tag)
        current_freq = freq.get(value, 0)
        freq[value] = current_freq + 1
    return freq

def tag_freq(elements):
    """
    Get the frequency of the tag keys

    For example:
    tag_frequencies = tag_freq(ways)
    """
    freq = {}
    for ele in elements:
        tags = ele.get('tags', {})
        for key in tags.keys():
            current_freq = freq.get(key, 0)
            freq[key] = current_freq + 1
    return freq


def sort_by_value(d):
    """ Sort on a dictionary's values """
    return sorted(d.items(), key=lambda x: x[1])


def display_results(osm_data):
    print("Elements downloaded: ", osm_data.countElements())
    print("Ways downloaded: ", osm_data.countWays())
    print("Nodes downloaded: ", osm_data.countNodes())
    print("Areas downloaded: ", osm_data.countAreas())
    print("Relations downloaded: ", osm_data.countRelations())
