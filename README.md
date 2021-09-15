# FAIR Data Registry

[![FAIR Data Registry](https://github.com/FAIRDataPipeline/data-registry/actions/workflows/fair-data-registry.yaml/badge.svg)](https://github.com/FAIRDataPipeline/data-registry/actions/workflows/fair-data-registry.yaml) [![codecov](https://codecov.io/gh/FAIRDataPipeline/data-registry/branch/main/graph/badge.svg?token=YT9mHzRfxn)](https://codecov.io/gh/FAIRDataPipeline/data-registry)

The *FAIR data registry* is a component of the [FAIR data pipeline](https://fairdatapipeline.github.io/) that maintains a metadata catalogue for different data types utilised and generated within a typical epidemiological modelling workflow.

### Implementation 

The *FAIR data registry* is implemented as a [Django](https://www.djangoproject.com/) web application and REST API. The [FAIR data pipeline](https://fairdatapipeline.github.io) uses the data registry to store metadata about code runs and their inputs and outputs. 

### Documentation


Information on how to run the local registry is available at [the local registry section in the project website](https://fairdatapipeline.github.io/docs/local_registry/).

Alternatively, you can run the local registry in a local VM using [Vagrant](https://www.vagrantup.com) with the included Vagrantfile.

Installation, development and maintenance guides, especially for the remote registry, are available in the [Wiki](https://github.com/FAIRDataPipeline/data-registry/wiki). User documentation for the remote registry is also available [here](docs/index.md).

[travis-master-img]: https://img.shields.io/travis/com/ScottishCovidResponse/data-registry/master?label=build-master
[travis-master-url]: https://travis-ci.com/ScottishCovidResponse/data-registry?branch=master

[travis-develop-img]: https://img.shields.io/travis/com/ScottishCovidResponse/data-registry/develop?label=build-develop
[travis-develop-url]: https://travis-ci.com/ScottishCovidResponse/data-registry?branch=develop
