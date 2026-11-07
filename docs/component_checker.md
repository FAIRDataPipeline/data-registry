# Component Checker

A script for processing data product files to display their components and check if they are registered in the
data registry is available [here](https://github.com/FAIRDataPipeline/data-registry/tree/main/tools).

## Installing

You can install this script by checking out the data-registry code and using pip:

```
git checkout git@github.com:FAIRDataPipeline/data-registry.git
cd data-registry/tools
pip install .
```

This will install the Python code and create a wrapper script called `check_components`.

## Usage 

The script is self documented, i.e.

```
check_components --help
```

Prints:

```
usage: check_components [-h] [-v] {check,status} ...

optional arguments:
  -h, --help      show this help message and exit
  -v, --verbose   Print verbose output

subcommands:
  {check,status}
    check         check file contains against registry
    status        print data registry entry for data product
```

## Examples

Checking a file to make sure the components are in the registry:

```
check_components check 20200716.0.h5
```

Prints:

```
All components match those in database for SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0
```

This is using the file hash to find the data product in the registry. You can also specify the
data_product and namespace to find the data product this way:

```
check_components check -d records/SARS-CoV-2/scotland/cases_and_management -n SCRC 20200716.0.h5
```

You can see what file components it is checking using the verbose option:

```
check_components -v check 20200716.0.h5
```

Prints:

```
File components:
> nhs_health_board/date-testing-cumulative [array(131, 14)]
> testing_location/date-cumulative [array(106, 2)]
> confirmed_suspected/date-country-hospital-special_health_board [array(112, 2)]
> date-country-deaths_registered [array(124, 1)]
> date-country-icu-special_health_board-total [array(120, 1)]
> number_vs_revised_number/date-country-carehomes-carehomes_with_suspected_cases [array(71, 2)]
> date-country-carehomes-staff_submitted_return [array(12, 1)]
> date-country-tested_positive [array(136, 1)]
> date-country-carehomes-response_rate [array(12, 1)]
> date-country-carehomes-cumulative_number_of_suspected_cases [array(95, 1)]
> nhs_health_board/date-hospital-suspected [array(112, 13)]
> call_centre/date-number_of_calls [array(120, 2)]
> test_result/date-cumulative [array(136, 3)]
> date-country-carehomes-new_suspected_cases [array(95, 1)]
> nhs_workforce/date-country-covid_related_absences [array(105, 4)]
> nhs_health_board/date-icu-total [array(120, 14)]
> confirmed_suspected_total/date-country-icu [array(120, 3)]
> date-country-carehomes-staff_absence_rate [array(12, 1)]
> testing_location/date [array(106, 2)]
> date-delayed_discharges [array(93, 1)]
> suspected_vs_reported/date-country-carehomes-cumulative [array(95, 2)]
> date-country-carehomes-proportion_that_have_reported_a_suspected_case [array(95, 1)]
> confirmed_suspected_total/date-country-hospital [array(120, 3)]
> date-country-carehomes-carehomes_submitted_return [array(12, 1)]
> nhs_health_board/date-hospital-confirmed [array(112, 14)]
> ambulance_attendances/date [array(119, 3)]
> date-country-carehomes-staff_reported_absent [array(12, 1)]

All components match those in database for SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0
```

It can also handle TOML files:

```
check_components -v check latent-period-0.1.0.toml.txt
```

Prints:

```
File components:
> latent-period [point-estimate]

All components match those in database for SCRC::human/infection/SARS-CoV-2/latent-period@0.1.0
```

You can check the status of a data product in the registry by using the `status` command:

```
check_components status -n SCRC records/SARS-CoV-2/scotland/cases_and_management
```

Prints:

```
Data registry storage location hash:
> cdb11bb599f6cdb1ecfc13a64972cb7eeef9424f

Data registry components:
> SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0:call_centre/date-number_of_calls
> SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0:confirmed_suspected_total/date-country-hospital
> SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0:date-country-carehomes-carehomes_submitted_return
> SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0:date-country-carehomes-new_suspected_cases
> SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0:date-country-carehomes-response_rate
> SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0:date-country-carehomes-staff_reported_absent
> SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0:date-country-deaths_registered
> SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0:date-country-tested_positive
> SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0:nhs_health_board/date-hospital-confirmed
> SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0:nhs_health_board/date-icu-total
> SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0:nhs_workforce/date-country-covid_related_absences
> SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0:suspected_vs_reported/date-country-carehomes-cumulative
> SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0:testing_location/date
> SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0:ambulance_attendances/date
> SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0:confirmed_suspected/date-country-hospital-special_health_board
> SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0:confirmed_suspected_total/date-country-icu
> SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0:date-country-carehomes-cumulative_number_of_suspected_cases
> SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0:date-country-carehomes-proportion_that_have_reported_a_suspected_case
> SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0:date-country-carehomes-staff_absence_rate
> SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0:date-country-carehomes-staff_submitted_return
> SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0:date-country-icu-special_health_board-total
> SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0:date-delayed_discharges
> SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0:nhs_health_board/date-hospital-suspected
> SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0:nhs_health_board/date-testing-cumulative
> SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0:number_vs_revised_number/date-country-carehomes-carehomes_with_suspected_cases
> SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0:test_result/date-cumulative
> SCRC::records/SARS-CoV-2/scotland/cases_and_management@0.20200717.0:testing_location/date-cumulative
```
