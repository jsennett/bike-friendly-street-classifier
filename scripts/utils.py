"""
Uilities for downloading and exploring OSM and Street View data.
Running this script without input arguments will generate descriptives for
selected cities.
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


def write_ways_descriptives(ways_filename, outfile, excluded_highways=None, num_to_show=50):

    # Read in file
    ways = read_osm(ways_filename)

    # exclude certain ways, if this option is specified
    if excluded_highways is not None:
        filtered_ways = {}
        for way in ways:
            if ways.get(way).get('tags').get('highway') not in excluded_highways:
                filtered_ways[way] = ways[way]
        ways = filtered_ways

    # Tag frequencies
    tags = sort_by_value(tag_freq(ways)) # returns a list of (tag, freq) pairs
    with open(outfile, 'w') as f:

        for (t, n) in tags[-num_to_show:]:
            f.write("{} - {}\n".format(t, n))

        for tag in ['highway', 'sidewalk', 'bicycle', 'lanes', 'oneway', 'cycleway',
                    'RLIS:bicycle', 'source:bicycle']:

            f.write('\n************\n {} \n************\n'.format(tag))
            tag_value_freqs = tag_value_freq(ways, tag)
            sorted_value_freqs = sort_by_value(tag_value_freqs)

            for (t, n) in sorted_value_freqs[-num_to_show:]:
                f.write("{} - {}\n".format(t, n))

            if tag == 'bicycle':
                print('Designated:', tag_value_freqs.get('designated', 0) + tag_value_freqs.get('yes', 0),
                      'Not:', tag_value_freqs.get(None, 0) + tag_value_freqs.get('no', 0))

    print(outfile, "saved.")


def get_image_labels(output_filename=None):

    import os
    import csv
    filenames = os.listdir('../data/images/')

    all_way_info = {
        'portland': read_osm("../data/processed/ways_portland.json"),
        'pittsburgh': read_osm("../data/processed/ways_pittsburgh.json"),
        'seattle': read_osm("../data/processed/ways_seattle.json"),
        'boulder': read_osm("../data/processed/ways_boulder.json"),
    }

    # return road_characteristics
    rows = []
    not_found = 0
    for filename in filenames:

        row = {}
        way_id = filename.split('_')[0][1:]
        way_info = None

        for region in ["boulder", "pittsburgh", "seattle", "portland"]:

            if way_info is None:
                way_info = all_way_info.get(region, {}).get(way_id, {}).get('tags', {})

        # Add way characteristics
        if way_info == {}:
            print(filename, "not found *******")
            not_found += 1

        row['region'] = region
        row['filename'] = filename

        for tag in ['highway', 'bicycle', 'cycleway', 'lanes', 'maxspeed', 'oneway']:
            row[tag] = way_info.get(tag, '').strip()

        # Determine the image label from its characteristics
        if (row['bicycle'] == 'designated' or 'yes' in row['bicycle'] or
            row['cycleway'] in ['lane', 'shared', 'shared_lane',
                                'opposite_lane', 'yes', 'cycle_greenway',
                                'track', 'share_busway']):
            row['label'] = 1
        else:
            row['label'] = 0

        rows.append(row)

    # Optional - write to file.
    if output_filename is not None:
        keys = rows[0].keys()
        with open(output_filename, 'w') as outfile:
            dict_writer = csv.DictWriter(outfile, keys)
            dict_writer.writeheader()
            dict_writer.writerows(rows)
            print(output_filename, "saved with", len(rows), "rows." )

    print(not_found, 'not found')
    return rows


def organize_images():

    from shutil import copyfile
    import pandas as pd

    df = pd.read_csv('../descriptives/image_labels.csv')
    labels = dict(zip(df['filename'],df['label']))

    copied = 0
    for filename in labels.keys():
        from_path = '../data/images/%s' % filename
        to_path = '../data/images/%d/%s' % (labels[filename], filename)
        copyfile(from_path, to_path)
        copied += 1
        if copied % 1000 == 0: print(copied, 'of', len(df))


if __name__ == '__main__':
    organize_images()
