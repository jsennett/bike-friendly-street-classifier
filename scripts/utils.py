"""
Uilities for downloading and exploring OSM data

Josh Sennett
"""
import json

def write_osm(elements, filename):
    with open(filename, 'w') as f:
        json.dump(elements, f)
        print(filename, "saved.")


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
    for ele in elements.values():
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
    for ele in elements.values():
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


def ways_descriptives(ways_filename, outfile):

    ways = read_osm(ways_filename)
    num_to_show = 50

    # Tag frequencies
    tags = sort_by_value(tag_freq(ways)) # returns a list of (tag, freq) pairs
    with open(outfile, 'w') as f:

        for (t, n) in tags[-num_to_show:]:
            print(t, n)
            f.write("{} - {}\n".format(t, n))

        for tag in ['highway', 'sidewalk', 'bicycle', 'lanes', 'oneway', 'cycleway',
                    'RLIS:bicycle', 'source:bicycle']:

            f.write('\n************\n {} \n************\n'.format(tag))
            tag_value_freqs = sort_by_value(tag_value_freq(ways, tag))

            for (t, n) in tag_value_freqs[-num_to_show:]:
                f.write("{} - {}\n".format(t, n))

    print(outfile, "saved.")




if __name__ == '__main__':
    for region in ["boulder", "pittsburgh", "seattle", "chicago",
                   "portland", "washington", "madison", "sanfrancisco"]:

        ways_descriptives("../data/processed/ways_{}.json".format(region),
                          "../data/descriptives/{}.txt".format(region))
