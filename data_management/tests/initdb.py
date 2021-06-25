from dateutil import parser

from data_management.models import *
from django.contrib.auth import get_user_model


def reset_db():
    Object.objects.all().delete()
    StorageRoot.objects.all().delete()
    Issue.objects.all().delete()
    Source.objects.all().delete()
    Namespace.objects.all().delete()


def init_db(test=True):
    user = get_user_model().objects.first()

    if test:
        get_user_model().objects.create(username='testusera')
        get_user_model().objects.create(username='testuserb')
        get_user_model().objects.create(username='testuserc')

    sr_jptcp = StorageRoot.objects.create(
        updated_by=user,
        name='https://jptcp.com/',
        root='https://jptcp.com/',
    )

    sr_repo = StorageRoot.objects.create(
        updated_by=user,
        name='DataRepository',
        root='https://raw.githubusercontent.com/ScottishCovidResponse/DataRepository/',
    )

    sr_github = StorageRoot.objects.create(
        updated_by=user,
        name='github',
        root='https://github.com',
    )

    sr_textfiles = StorageRoot.objects.create(
        updated_by=user,
        name='text_file',
        root='https://data.scrc.uk/api/text_file/',
    )

    sr_scot = StorageRoot.objects.create(
        updated_by=user,
        name='Scottish Government Open Data Repository',
        root='https://statistics.gov.scot/sparql.csv?query=',
    )

    sr_boydorr = StorageRoot.objects.create(
        updated_by=user,
        name='boydorr',
        root='ftp://boydorr.gla.ac.uk/scrc/',
    )

    sr_temp = StorageRoot.objects.create(
        updated_by=user,
        name='temporary_data',
        root='https://raw.githubusercontent.com/ScottishCovidResponse/temporary_data/master/',
    )

    sl_repo_prob = StorageLocation.objects.create(
        updated_by=user,
        path='master/SCRC/human/infection/SARS-CoV-2/symptom-probability/0.1.0.toml',
        hash='eaa3833986a51b2f079dda9b702b0a3d510f2255',
        storage_root=sr_repo,
    )

    sl_repo_delay = StorageLocation.objects.create(
        updated_by=user,
        path='master/SCRC/human/infection/SARS-CoV-2/symptom-delay/0.1.0.toml',
        hash='68cebe4e507ca71b6d518313bd75c9326f3b6359',
        storage_root=sr_repo,
    )

    sl_repo_infect = StorageLocation.objects.create(
        updated_by=user,
        path='master/SCRC/human/infection/SARS-CoV-2/infectious-duration/0.1.0.toml',
        hash='67e0759d404d150b3f3eb3d5838570880fe8dd25',
        storage_root=sr_repo,
    )

    sl_repo_latent = StorageLocation.objects.create(
        updated_by=user,
        path='master/SCRC/human/infection/SARS-CoV-2/latent-period/0.1.0.toml',
        hash='7c0e14caec08674d7d4e52c305cb4320babaf90f',
        storage_root=sr_repo,
    )

    sl_repo_asym = StorageLocation.objects.create(
        updated_by=user,
        path='master/SCRC/human/infection/SARS-CoV-2/asymptomatic-period/0.1.0.toml',
        hash='8142974eaf721e6606830b36ffac3c3a00337a77',
        storage_root=sr_repo,
    )

    sl_boy_cases_h5 = StorageLocation.objects.create(
        updated_by=user,
        path='human/infection/SARS-CoV-2/scotland/cases_and_management/v0.1.0.h5',
        hash='43faf6d048b92ed1820db2e662ba403eb0e371fb',
        storage_root=sr_boydorr,
    )

    sl_boy_cases_csv = StorageLocation.objects.create(
        updated_by=user,
        path='human/infection/SARS-CoV-2/scotland/cases_and_management/v0.1.0.csv',
        hash='9c1eb0ff807a0cd73aaec297ffc780cba00b443d',
        storage_root=sr_boydorr,
    )

    StorageLocation.objects.create(
        updated_by=user,
        path='PREFIX qb: <http://purl.org/linked-data/cube#>PREFIX data: <http://statistics.gov.scot/data/>PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>PREFIX mp: <http://statistics.gov.scot/def/measure-properties/>PREFIX dim: <http://purl.org/linked-data/sdmx/2009/dimension#>PREFIX sdim: <http://statistics.gov.scot/def/dimension/>PREFIX stat: <http://statistics.data.gov.uk/def/statistical-entity#>SELECT ?featurecode ?featurename ?date ?measure ?variable ?countWHERE {  ?indicator qb:dataSet data:coronavirus-covid-19-management-information;              dim:refArea ?featurecode;              dim:refPeriod ?period;              sdim:variable ?varname;              qb:measureType ?type.{?indicator mp:count ?count.} UNION {?indicator mp:ratio ?count.}  ?featurecode <http://publishmydata.com/def/ontology/foi/displayName> ?featurename.  ?period rdfs:label ?date.  ?varname rdfs:label ?variable.  ?type rdfs:label ?measure.}',
        hash='69299198a904374a242fc0bd4d0811cdec384b02',
        storage_root=sr_scot,
    )

    StorageLocation.objects.create(
        updated_by=user,
        path='ScottishCovidResponse/SCRCdata',
        hash='b4e5ff9b34092cdb3baf16f789546e325a2427a0',
        storage_root=sr_github,
    )

    sl_boy_mort_h5 = StorageLocation.objects.create(
        updated_by=user,
        path='human/infection/SARS-CoV-2/scotland/mortality/v0.1.0.h5',
        hash='acb68022433c8782c171ce21ba1b1e4c026532b4',
        storage_root=sr_boydorr,
    )

    sl_scot = StorageLocation.objects.create(
        updated_by=user,
        path='PREFIX qb: <http://purl.org/linked-data/cube#>PREFIX data: <http://statistics.gov.scot/data/>PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>PREFIX dim: <http://purl.org/linked-data/sdmx/2009/dimension#>PREFIX sdim: <http://statistics.gov.scot/def/dimension/>PREFIX stat: <http://statistics.data.gov.uk/def/statistical-entity#>PREFIX mp: <http://statistics.gov.scot/def/measure-properties/>SELECT ?featurecode ?featurename ?areatypename ?date ?cause ?location ?gender ?age ?type ?countWHERE {  ?indicator qb:dataSet data:deaths-involving-coronavirus-covid-19;              mp:count ?count;              qb:measureType ?measType;              sdim:age ?value;              sdim:causeofdeath ?causeDeath;              sdim:locationofdeath ?locDeath;              sdim:sex ?sex;              dim:refArea ?featurecode;              dim:refPeriod ?period.              ?measType rdfs:label ?type.              ?value rdfs:label ?age.              ?causeDeath rdfs:label ?cause.              ?locDeath rdfs:label ?location.              ?sex rdfs:label ?gender.              ?featurecode stat:code ?areatype;                rdfs:label ?featurename.              ?areatype rdfs:label ?areatypename.              ?period rdfs:label ?date.}',
        hash='346df017da291fe0e9d1169846efb12f3377ae18',
        storage_root=sr_scot,
    )

    sl_boy_mort_csv = StorageLocation.objects.create(
        updated_by=user,
        path='human/infection/SARS-CoV-2/scotland/mortality/v0.1.0.csv',
        hash='06586f2d31f20682e0611c815c6234cfc8e3c4d3',
        storage_root=sr_boydorr,
    )

    sl_temp_pop = StorageLocation.objects.create(
        updated_by=user,
        path='simple_network_sim/human/population/data/data.csv',
        hash='1219832fdd6a2d9af5d33b1e10bfa69c6787748c',
        storage_root=sr_temp,
    )

    sl_temp_mixing = StorageLocation.objects.create(
        updated_by=user,
        path='simple_network_sim/human/mixing-matrix/data/data.csv',
        hash='141e15d0f8f467debbaf3b607971ecd6c6c04833',
        storage_root=sr_temp,
    )

    sl_temp_comp = StorageLocation.objects.create(
        updated_by=user,
        path='simple_network_sim/human/compartment-transition/data/data.csv',
        hash='3a9f2e43c148633afb7057bd134b859c77f382d7',
        storage_root=sr_temp,
    )

    sl_temp_commutes = StorageLocation.objects.create(
        updated_by=user,
        path='simple_network_sim/human/commutes/data/data.csv',
        hash='dae8dd8b1053e2f33979da109259344f0f9e273f',
        storage_root=sr_temp,
    )

    sl_code = StorageLocation.objects.create(
        updated_by=user,
        path='ScottishCovidResponse/SCRCdata repository',
        hash='b98782baaaea3bf6cc2882ad7d1c5de7aece362a',
        storage_root=sr_github,
    )

    sl_script = StorageLocation.objects.create(
        updated_by=user,
        path='16/?format=text',
        hash='5b6fafc594cdb619104ceeef7a4802f4086e90e9',
        storage_root=sr_textfiles,
    )

    o_paper = Object.objects.create(updated_by=user)

    o_repo_prob = Object.objects.create(updated_by=user, storage_location=sl_repo_prob)
    o_repo_delay = Object.objects.create(updated_by=user, storage_location=sl_repo_delay)
    o_repo_infect = Object.objects.create(updated_by=user, storage_location=sl_repo_infect)
    o_repo_latent = Object.objects.create(updated_by=user, storage_location=sl_repo_latent)
    o_repo_asym = Object.objects.create(updated_by=user, storage_location=sl_repo_asym)

    o_boy_cases_h5 = Object.objects.create(updated_by=user, storage_location=sl_boy_cases_h5)
    o_boy_cases_csv = Object.objects.create(updated_by=user, storage_location=sl_boy_cases_csv)
    o_boy_mort_h5 = Object.objects.create(updated_by=user, storage_location=sl_boy_mort_h5)
    o_boy_mort_csv = Object.objects.create(updated_by=user, storage_location=sl_boy_mort_csv)

    o_temp_commutes = Object.objects.create(updated_by=user, storage_location=sl_temp_commutes)
    o_temp_comp = Object.objects.create(updated_by=user, storage_location=sl_temp_comp)
    o_temp_mixing = Object.objects.create(updated_by=user, storage_location=sl_temp_mixing)
    o_temp_pop = Object.objects.create(updated_by=user, storage_location=sl_temp_pop)

    o_code = Object.objects.create(updated_by=user, storage_location=sl_code)
    o_script = Object.objects.create(updated_by=user, storage_location=sl_script)

    oc_prob = ObjectComponent.objects.create(updated_by=user, object=o_repo_prob, name='symptom-probability')

    oc_delay = ObjectComponent.objects.create(updated_by=user, object=o_repo_delay, name='symptom-probability')

    oc_infect = ObjectComponent.objects.create(updated_by=user, object=o_repo_infect, name='symptom-probability')

    oc_latent = ObjectComponent.objects.create(updated_by=user, object=o_repo_latent, name='symptom-probability')

    oc_asym = ObjectComponent.objects.create(updated_by=user, object=o_repo_asym, name='symptom-probability')

    ObjectComponent.objects.create(updated_by=user, object=o_boy_mort_h5,
                                   name='scotland/per_week/covid_related_deaths/persons/by_agegroup')
    ObjectComponent.objects.create(updated_by=user, object=o_boy_mort_h5,
                                   name='scotland/per_week/covid_related_deaths/persons/all_ages')
    ObjectComponent.objects.create(updated_by=user, object=o_boy_mort_h5,
                                   name='scotland/per_week/covid_related_deaths/males/by_agegroup')
    ObjectComponent.objects.create(updated_by=user, object=o_boy_mort_h5,
                                   name='scotland/per_week/covid_related_deaths/males/all_ages')
    ObjectComponent.objects.create(updated_by=user, object=o_boy_mort_h5,
                                   name='scotland/per_week/covid_related_deaths/females/by_agegroup')
    ObjectComponent.objects.create(updated_by=user, object=o_boy_mort_h5,
                                   name='scotland/per_week/covid_related_deaths/females/all_ages')
    ObjectComponent.objects.create(updated_by=user, object=o_boy_mort_h5,
                                   name='scotland/per_week/all_deaths/persons/by_agegroup')
    ObjectComponent.objects.create(updated_by=user, object=o_boy_mort_h5,
                                   name='scotland/per_week/all_deaths/persons/averaged_over_5years')
    ObjectComponent.objects.create(updated_by=user, object=o_boy_mort_h5,
                                   name='scotland/per_week/all_deaths/persons/all_ages')
    ObjectComponent.objects.create(updated_by=user, object=o_boy_mort_h5,
                                   name='scotland/per_week/all_deaths/males/by_agegroup')
    ObjectComponent.objects.create(updated_by=user, object=o_boy_mort_h5,
                                   name='scotland/per_week/all_deaths/males/all_ages')
    ObjectComponent.objects.create(updated_by=user, object=o_boy_mort_h5,
                                   name='scotland/per_week/all_deaths/females/by_agegroup')
    ObjectComponent.objects.create(updated_by=user, object=o_boy_mort_h5,
                                   name='scotland/per_week/all_deaths/females/all_ages')
    ObjectComponent.objects.create(updated_by=user, object=o_boy_mort_h5,
                                   name='nhs_health_board/per_week/covid_related_deaths')
    ObjectComponent.objects.create(updated_by=user, object=o_boy_mort_h5, name='nhs_health_board/per_week/all_deaths')
    ObjectComponent.objects.create(updated_by=user, object=o_boy_mort_h5,
                                   name='nhs_health_board/per_location/covid_related_deaths')
    ObjectComponent.objects.create(updated_by=user, object=o_boy_mort_h5,
                                   name='nhs_health_board/per_location/all_deaths')
    ObjectComponent.objects.create(updated_by=user, object=o_boy_mort_h5, name='location/per_week/covid_related_deaths')
    ObjectComponent.objects.create(updated_by=user, object=o_boy_mort_h5, name='location/per_week/all_deaths')
    ObjectComponent.objects.create(updated_by=user, object=o_boy_mort_h5,
                                   name='council_area/per_week/covid_related_deaths')
    ObjectComponent.objects.create(updated_by=user, object=o_boy_mort_h5, name='council_area/per_week/all_deaths')
    ObjectComponent.objects.create(updated_by=user, object=o_boy_mort_h5,
                                   name='council_area/per_location/covid_related_deaths')
    ObjectComponent.objects.create(updated_by=user, object=o_boy_mort_h5, name='council_area/per_location/all_deaths')

    ObjectComponent.objects.create(updated_by=user, object=o_temp_pop, name='population')

    ObjectComponent.objects.create(updated_by=user, object=o_temp_comp, name='compartment-transition')

    ObjectComponent.objects.create(updated_by=user, object=o_temp_commutes, name='commutes')

    ObjectComponent.objects.create(updated_by=user, object=o_temp_mixing, name='mixing-matrix')

    n_fair = Namespace.objects.create(updated_by=user, name='FAIR')

    n_simp = Namespace.objects.create(updated_by=user, name='simple_network_sim')

    Keyword.objects.create(updated_by=user, object=o_paper, keyphrase='treatment')
    Keyword.objects.create(updated_by=user, object=o_paper, keyphrase='non-invasive mechanical ventilation')
    Keyword.objects.create(updated_by=user, object=o_paper, keyphrase='monoclonal antibodies')
    Keyword.objects.create(updated_by=user, object=o_paper, keyphrase='coronavirus disease')
    Keyword.objects.create(updated_by=user, object=o_paper, keyphrase='covid-19')

    ExternalObject.objects.create(
        updated_by=user,
        object=o_boy_mort_csv,
        doi_or_unique_name='scottish deaths-involving-coronavirus-covid-19',
        release_date=parser.isoparse('2010-07-09T12:00Z'),
        title='scottish deaths-involving-coronavirus-covid-19',
        description='scottish deaths-involving-coronavirus-covid-19 dataset',
        original_store=sl_scot
    )

    ExternalObject.objects.create(
        updated_by=user,
        object=o_paper,
        doi_or_unique_name='10.15586/jptcp.v27iSP1.691',
        release_date=parser.isoparse('2020-01-01T12:00Z'),
        title='Covid-19: A systemic disease treated with a wide-ranging approach: A case report',
        description='''At the end of December 2019, the Health Commission of the city of Wuhan, China, alerted the World Health Organization (WHO) to a pneumonia cluster in the city. The cause was identified as being a new virus, later named SARS-CoV-2. We can distinguish three clinical phases of the disease with a distinct pathogenesis, manifestations and prognosis. Here, we describe the case of a 45-year-old male, successfully treated for Coronavirus disease (COVID-19). The patient was feeling sick in early April 2020; he had a fever and pharyngodynia. When he came to our COVID hospital, his breathing was normal. The nasopharyngeal swab specimen turned out positive. High-resolution computed tomography (HRCT) showed mild interstitial pneumonia. The patient was admitted to our department and treated with hydroxychloroquine, ritonavir, darunavir, azithromycin and enoxaparin. On day seven of the disease, the patient's respiratory condition got worse as he was developing acute respiratory distress syndrome (ARDS). He was given tocilizumab and corticosteroids and was immediately treated with non-invasive mechanical ventilation (NIMV). His condition improved, and in the ensuing days, the treatment gradually switched to a high-flow nasal cannula (HFNC); after 18 days, the patient's clinical condition was good.The successful results we have been able to obtain are closely associated with avoidance of invasive ventilation that may lead to intensive care unit (ICU)-related superinfections. In our opinion, it is fundamental to understand that COVID-19 is a systemic disease that is a consequence of an overwhelming inflammatory response, which can cause severe medical conditions, even in young patients.'''
    )

    ExternalObject.objects.create(
        updated_by=user,
        object=o_boy_cases_csv,
        doi_or_unique_name='scottish coronavirus-covid-19-management-information',
        release_date=parser.isoparse('2010-07-10T18:38:00Z'),
        title='scottish coronavirus-covid-19-management-information',
        description='scottish coronavirus-covid-19-management-information dataset',
        original_store=sl_scot
    )

    DataProduct.objects.create(
        updated_by=user,
        object=o_repo_prob,
        namespace=n_fair,
        name='human/infection/SARS-CoV-2/symptom-probability',
        version='0.1.0',
    )

    DataProduct.objects.create(
        updated_by=user,
        object=o_repo_delay,
        namespace=n_fair,
        name='human/infection/SARS-CoV-2/symptom-delay',
        version='0.1.0',
    )

    DataProduct.objects.create(
        updated_by=user,
        object=o_repo_infect,
        namespace=n_fair,
        name='human/infection/SARS-CoV-2/infectious-duration',
        version='0.1.0',
    )

    DataProduct.objects.create(
        updated_by=user,
        object=o_repo_latent,
        namespace=n_fair,
        name='human/infection/SARS-CoV-2/latent-period',
        version='0.1.0',
    )

    DataProduct.objects.create(
        updated_by=user,
        object=o_repo_asym,
        namespace=n_fair,
        name='human/infection/SARS-CoV-2/asymptomatic-period',
        version='0.1.0',
    )

    DataProduct.objects.create(
        updated_by=user,
        object=o_boy_mort_h5,
        namespace=n_fair,
        name='human/infection/SARS-CoV-2/scotland/cases_and_management',
        version='0.1.0',
    )

    DataProduct.objects.create(
        updated_by=user,
        object=o_boy_cases_h5,
        namespace=n_fair,
        name='human/infection/SARS-CoV-2/scotland/mortality',
        version='0.1.0',
    )

    DataProduct.objects.create(
        updated_by=user,
        object=o_temp_commutes,
        namespace=n_simp,
        name='human/commutes',
        version='0.1.0',
    )

    DataProduct.objects.create(
        updated_by=user,
        object=o_temp_comp,
        namespace=n_simp,
        name='human/compartment-transition',
        version='0.1.0',
    )

    DataProduct.objects.create(
        updated_by=user,
        object=o_temp_mixing,
        namespace=n_simp,
        name='human/mixing-matrix',
        version='0.1.0',
    )

    DataProduct.objects.create(
        updated_by=user,
        object=o_temp_pop,
        namespace=n_simp,
        name='human/population',
        version='0.1.0',
    )

    a1 = Author.objects.create(updated_by=user, family_name='Valenti', given_name='Ivana')
    a2 = Author.objects.create(updated_by=user, family_name='Cipriani', given_name='Maria Stella')
    a3 = Author.objects.create(updated_by=user, family_name='Massabeti', given_name='Rosanna')

    oao1 = ObjectAuthorOrg.objects.create(updated_by=user, author=a1, object=o_paper)
    oao2 = ObjectAuthorOrg.objects.create(updated_by=user, author=a2, object=o_paper)
    oao3 = ObjectAuthorOrg.objects.create(updated_by=user, author=a3, object=o_paper)

    crr_code = CodeRepoRelease.objects.create(
        updated_by=user,
        name="ScottishCovidResponse/SCRCdata",
        version="0.1.0",
        website="https://github.com/ScottishCovidResponse/SCRCdata",
        object=o_code
    )

    cr = CodeRun.objects.create(
        updated_by=user,
        run_date='2020-07-17T18:21:11Z',
        description='Script run to upload and process scottish coronavirus-covid-19-management-information',
        code_repo=o_code,
        submission_script=o_script,
    )
    cr.inputs.set([oc_prob, oc_infect, oc_latent])
    cr.outputs.set([oc_prob, oc_infect, oc_latent])

    QualityControlled.objects.create(updated_by=user, object=o_code)
    QualityControlled.objects.create(updated_by=user, object=o_boy_cases_h5)
    QualityControlled.objects.create(updated_by=user, object=o_boy_mort_h5)

    Licence.objects.create(updated_by=user, object=o_code, licence_info='''
    Copyright 2020 SCRC

    Permission is hereby granted, free of charge, to any person obtaining a copy of this
    software and associated documentation files (the "Software"), to deal in the Software
    without restriction, including without limitation the rights to use, copy, modify, merge,
    publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons
    to whom the Software is furnished to do so, subject to the following conditions:
    
    The above copyright notice and this permission notice shall be included in all copies or
    substantial portions of the Software.
    
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
    BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
    ''')

    KeyValue.objects.create(updated_by=user, object=o_paper, key='TestKey1', value='TestValue1')
    KeyValue.objects.create(updated_by=user, object=o_paper, key='TestKey2', value='TestValue2')
    KeyValue.objects.create(updated_by=user, object=o_paper, key='TestKey3', value='TestValue3')
    KeyValue.objects.create(updated_by=user, object=o_paper, key='TestKey4', value='TestValue4')

    if test:
        Issue.objects.create(updated_by=user, severity=3, description="Test Issue 1")
        Issue.objects.create(updated_by=user, severity=6, description="Test Issue 2")
        Issue.objects.create(updated_by=user, severity=9, description="Test Issue 3")


if __name__ == '__main__':
    reset_db()
    init_db(test=False)
