import os
import h5py
import toml
import argparse
import requests
import html
import hashlib

API_ROOT = 'https://data.fairdatapipeline.org/api/'
DATA_PRODUCT_ENDPOINT = 'data_product/'
NAMESPACE_ENDPOINT = 'namespace/'
STORAGE_LOCATION_ENDPOINT = 'storage_location/'
OBJECT_ENDPOINT = 'object/'


def is_leaf(node):
    for (_, child) in node.items():
        if isinstance(child, h5py.Group):
            return False
    return True


def get_node_type(node):
    type = 'unknown'
    for (name, child) in node.items():
        if name == 'array':
            type = 'array%s' % str(child.shape)
        if name == 'table':
            type = 'table'
    return type


def find_leaf_nodes(name, node, components):
    if isinstance(node, h5py.Group) and is_leaf(node):
        type = get_node_type(node)
        components.append((name, type))


def process_hdf5(file):
    h5file = h5py.File(file, 'r')
    components = []
    h5file.visititems(lambda name, node: find_leaf_nodes(name, node, components))
    return set(components)


def process_toml(file):
    data = toml.load(file)
    components = []
    for name, value in data.items():
        type = value['type'] if 'type' in value else 'unknown'
        components.append((name, type))
    return components


def process(file):
    _, ext = os.path.splitext(file)
    if ext == '.h5':
        components = process_hdf5(file)
    elif ext in ('.txt', '.toml'):
        components = process_toml(file)
    else:
        raise ValueError('Unknown file type')
    return components


def url_to_id(url):
    return int(url.split('/')[-2])


def read_api(url, error_message):
    r = requests.get(url)

    if r.status_code != 200:
        raise Exception(r.content)

    data = r.json()

    if not data:
        raise Exception(error_message)

    if 'count' in data:
        if data['count'] == 0:
            raise Exception(error_message)
        if data['count'] > 1:
            raise Exception('multiple entries found for API query %s' % url)
        return data['results'][0]

    return data


def get_component_names(component_urls):
    names = []
    for url in component_urls:
        r = requests.get(url)
        if r.status_code != 200:
            raise Exception(r.content)
        result = r.json()
        names.append(result['name'])
    return names


def find_object_by_file_hash(file_hash, opts):
    url = API_ROOT + STORAGE_LOCATION_ENDPOINT + '?format=json&hash=%s' % html.escape(file_hash)

    result = read_api(url, 'Could not find storage location with file hash matching %s' % opts.file)
    storage_location_id = url_to_id(result['url'])

    url = API_ROOT + OBJECT_ENDPOINT + '?format=json&storage_location=%d' % storage_location_id
    object_data = read_api(url, 'Could not find object with storage_location %d' % storage_location_id)

    object_id = url_to_id(object_data['url'])
    url = API_ROOT + DATA_PRODUCT_ENDPOINT + '?format=json&object=%d' % object_id
    data_product = read_api(url, 'Could not find data product %s' % opts.data_product)
    namespace = read_api(data_product['namespace'], 'Failed to read namespace %s' % data_product['namespace'])

    data_product_name = '%s::%s@%s' % (namespace['name'], data_product['name'], data_product['version'])

    return data_product_name, object_data


def find_object_by_data_product(opts):
    url = API_ROOT + DATA_PRODUCT_ENDPOINT + '?format=json&name=%s' % html.escape(opts.data_product)
    if opts.namespace:
        namespace_id = find_namespace_id(opts)
        url += '&namespace=%d' % namespace_id

    data_product = read_api(url, 'Could not find data product %s' % opts.data_product)
    object_url = data_product['object']
    namespace = read_api(data_product['namespace'], 'Failed to read namespace %s' % data_product['namespace'])

    data_product_name = '%s::%s@%s' % (namespace['name'], data_product['name'], data_product['version'])
    object_data = read_api(object_url, 'Failed to read object_url %s' % object_url)

    return data_product_name, object_data


def find_namespace_id(opts):
    url = API_ROOT + NAMESPACE_ENDPOINT + '?format=json&name=%s' % html.escape(opts.namespace)
    namespace = read_api(url, 'Could not find namespace %s' % opts.namespace)
    return url_to_id(namespace['url'])


def check_file(opts):
    components = process(opts.file)

    if opts.data_product:
        data_product_name, object_data = find_object_by_data_product(opts)
    else:
        with open(opts.file, 'rb') as f:
            bytes = f.read()
        file_hash = hashlib.sha1(bytes)
        data_product_name, object_data = find_object_by_file_hash(file_hash.hexdigest(), opts)

    component_urls = object_data['components']
    names = get_component_names(component_urls)

    if opts.verbose:
        print('File components:')
        for comp in components:
            print('> %s [%s]' % (comp[0], comp[1]))
        print()

    errors = []
    comp_names = [c[0] for c in components]

    for comp_name in comp_names:
        if comp_name not in names:
            errors.append('File component %s not found in registry' % comp_name)

    for n in names:
        if n not in comp_names:
            errors.append('Registry component %s not found in file' % n)

    if not errors:
        print('All components match those in database for %s' % data_product_name)
    else:
        print('Errors found:')
        for e in errors:
            print('> %s ' % e)


def get_status(opts):
    data_product_name, object_data = find_object_by_data_product(opts)

    storage_location_url = object_data['storage_location']
    storage_location_data = read_api(storage_location_url, 'failed to read storage_location %s' % storage_location_url)

    print('Data registry storage location hash:')
    print('> %s' % storage_location_data['hash'])
    print()

    component_urls = object_data['components']
    names = get_component_names(component_urls)
    print('Data registry components:')
    for n in names:
        print('> %s:%s' % (data_product_name, n))


def main(args=None):
    if args is None:
        import sys
        args = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true', help='Print verbose output')

    subparsers = parser.add_subparsers(title='subcommands', dest='subcommand')

    check_parser = subparsers.add_parser('check', help='check file contains against registry')
    check_parser.add_argument('-d', '--data_product', type=str, help='Registry data product to look up')
    check_parser.add_argument('-n', '--namespace', type=str, help='Namespace of data product')
    check_parser.add_argument('file', type=str, help='File to process')

    status_parser = subparsers.add_parser('status', help='print data registry entry for data product')
    status_parser.add_argument('-n', '--namespace', type=str, help='Namespace of data product')
    status_parser.add_argument('data_product', type=str, help='Registry data product to look up')

    opts = parser.parse_args(args)

    try:
        if opts.subcommand == 'check':
            check_file(opts)
        elif opts.subcommand == 'status':
            get_status(opts)
        else:
            print('unknown command %s' % opts.subcommand)
    except Exception as ex:
        print('error: %s' % str(ex))


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
