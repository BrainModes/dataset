import requests
from ..config import ConfigClass
from ..commons.logger_services.logger_factory_service import SrvLoggerFactory

__logger = SrvLoggerFactory('es_helper').get_logger()


def insert_one(es_type, es_index, data):
    url = ConfigClass.ELASTIC_SEARCH_SERVICE + \
        '{}/{}'.format(es_index, es_type)

    res = requests.post(url, json=data)

    return res.json()


def insert_one_by_id(es_type, es_index, data, id):
    url = ConfigClass.ELASTIC_SEARCH_SERVICE + \
        '{}/{}/{}'.format(es_index, es_type, id)

    res = requests.put(url, json=data)

    return res.json()


def get_one_by_id(es_index, es_type, id):
    url = ConfigClass.ELASTIC_SEARCH_SERVICE + \
        '{}/{}/{}'.format(es_index, es_type, id)

    res = requests.get(url)

    return res.json()


def search(es_index, page, page_size, data, sort_by=None, sort_type=None):
    url = ConfigClass.ELASTIC_SEARCH_SERVICE + '{}/_search'.format(es_index)

    search_fields = []

    for item in data:
        if item['nested']:
            field_values = [
                {"match": {"attributes.name": item['name']}}
            ]

            if 'attribute_name' in item:
                field_values.append(
                    {"match": {"attributes.attribute_name": item['attribute_name']}})
            if 'search_type' in item:
                if item['search_type'] == 'wildcard':
                    field_values.append(
                        {"wildcard": {"attributes.value": item['value']}})
                elif item['search_type'] == 'match':
                    field_values.append(
                        {"match": {"attributes.value": item['value']}})
                elif item['search_type'] == 'should':
                    options = []
                    for option in item['value']:
                        options.append({"match": {"attributes.value": option}})
                    field_values.append({
                        "bool": {
                            "should": options
                        }
                    })
                elif item['search_type'] == 'must':
                    options = []
                    for option in item['value']:
                        options.append({"match": {"attributes.value": option}})
                    field_values.append({
                        "bool": {
                            "must": options
                        }
                    })

            search_fields.append({
                "nested": {
                    "path": item['field'],
                    "query": {
                        "bool": {
                            "must": field_values,
                        }
                    }
                }
            })
        elif item['range']:
            if len(item['range']) == 1:
                value = str(item['range'][0])
                if len(value) > 20:
                    value = value[:19]
                if item['search_type'] == 'lte':
                    search_fields.append({
                        "range": {
                            item['field']: {"lte": int(value)}
                        }
                    })
                else:
                    search_fields.append({
                        "range": {
                            item['field']: {"gte": int(value)}
                        }
                    })
            else:
                value1 = str(item['range'][0])
                value2 = str(item['range'][1])

                if len(value1) > 20:
                    value1 = value1[:19]

                if len(value2) > 20:
                    value2 = value2[:19]

                search_fields.append({
                    "range": {
                        item['field']: {"gte": int(value1), "lte": int(value2)}
                    }
                })
        elif item['multi_values']:
            options = []
            for option in item['value']:
                options.append({"term": {item['field']: option}})

            if item['search_type'] == 'should':
                search_fields.append({
                    "bool": {
                        "should": options
                    }
                })
            else:
                search_fields.append({
                    "bool": {
                        "must": options
                    }
                })
        else:
            if item['search_type'] == 'contain':
                search_fields.append({
                    "wildcard": {
                        item['field']: '*{}*'.format(item['value'])
                    }
                })
            else:
                search_fields.append({
                    "term": {
                        item['field']: item['value']
                    }
                })

    search_params = {
        "query": {
            "bool": {
                "must": search_fields
            }
        },
        "size": page_size,
        "from": page * page_size,
        "sort": [
            {sort_by: sort_type}
        ]
    }
    __logger.info("elastic search url: {}".format(url))
    __logger.info("elastic search params: {}".format(str(search_params)))
    res = requests.get(url, json=search_params)
    return res.json()