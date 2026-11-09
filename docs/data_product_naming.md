## Data Product naming

The file formats the pipeline's APIs read and write, and their components, are described in the
[API documentation](https://www.fairdatapipeline.org/docs/api/).

### Naming conventions

We suggest that namespaces for Data Products should only contain ASCII letters, ASCII digits, underscores, and dashes (A-Za-z0-9_-), names in the namespace can also include forward slashes (/) to denote structure. Component names in [TOML][toml] should use the same characters allowed in namespaces (A-Za-z0-9_-) – these correspond to the characters allowed in TOML's [*bare keys*][toml-keys]. Component names in hdf5 files, like Data Product names, can also include forward slashes (/) to denote sub-components. At the moment none of these conventions are enforced, but we suggest that everyone maintains them until we find a reason to change them.

## TOML file format

### Single-component TOML files

For TOML files, there are currently three types of information that can be stored in one:

1. A simple point estimate of a parameter
```
[latent-period]
type = "point-estimate"
value = 123.12
```

2. The distribution of a parameter 
```
[latent-period]
type = "distribution" 
distribution = "gamma" 
shape = 1
scale = 2 
```
 
 3. Empirical samples drawn from the distribution of a parameter
```
[latent-period] 
type = "samples" 
samples = [1.0, 2.0, 3.0, 4.0, 5.0]
```

In the examples above, each file had a single component called `latent-period` in the data product. If there's only one component in a data product, then we suggest giving it the same name as the last part of the data product's name in the namespace, so for `human/infection/SARS-CoV-2/latent-period`, this would be `latent-period`. This will be the default if no component name is given in a funtion call.

### Multiple-component TOML files

You can have multiple components of any kind in a single data product. For example:

```
[latent-period]
type = "point-estimate"
value = 123.12

[asymptomatic-period] 
type = "point-estimate" 
value = 200.1
```

The only further constraint is that all of the component names (here `latent-period` and `asymptomatic-period`) are different.

[toml]: https://toml.io/en/

[toml-keys]: https://toml.io/en/v1.0.0-rc.1#keys
