import pytest, csv, sys
from click.testing import CliRunner
import uuid


from odk2gn.tests.fixtures import (
    submissions,
    datasets,
    header,
    data,
    taxon_and_list,
    module,
    point,
    module,
    nomenclature,
    observers_and_list,
    test,
    the_csv,
    mon_schema_fields,
    my_config,
    attachment,
    mail,
    review_state,
    site_type,
    pf_sub,
    plant,
    type_nomenclature,
)
from odk2gn.tests.fixtures import site
from odk2gn.gn2_utils import (
    format_jdd_list,
    to_csv,
    get_site_list,
    get_taxon_list,
    get_observer_list,
    get_nomenclature_data,
    get_ref_nomenclature_list,
    get_modules_info,
    get_gn2_attachments_data,
)
from odk2gn.contrib.flore_proritaire.src.odk_flore_prioritaire.odk_methods import (
    to_wkt,
    write_files,
)
from geonature.core.gn_monitoring.models import TBaseSites
from odk2gn.odk_api import ODKSchema

from pypnusershub.db.models import UserList, User

from geonature.utils.env import db


from odk2gn.main import synchronize, synchronize_monitoring, get_submissions, test
from odk2gn.main import get_modules_info


@pytest.mark.usefixtures("temporary_transaction")
class TestCommand:
    def test_synchronize_monitoring(
        self, mocker, submissions, mon_schema_fields, module, my_config, attachment, app, site
    ):
        mocker.patch("odk2gn.main.get_submissions", return_value=submissions)
        mocker.patch("odk2gn.odk_api.ODKSchema._get_schema_fields", return_value=mon_schema_fields)
        mocker.patch("odk2gn.main.get_config", return_value=my_config)
        mocker.patch("odk2gn.main.get_attachment", return_value=attachment)
        mocker.patch("odk2gn.main.create_app", return_value=app)
        runner = CliRunner()
        result = runner.invoke(
            synchronize,
            ["monitoring", module.module_code, "--project_id", 99, "--form_id", "bidon"],
        )

        assert result.exit_code == 0

    def test_synchronize_flore_prio(self, mocker, app, pf_sub):
        mocker.patch("odk2gn.main.create_app", return_value=app)
        mocker.patch(
            "odk_flore_prioritaire.odk_methods.get_submissions",
            return_value=pf_sub,
        )
        mocker.patch("odk_flore_prioritaire.odk_methods.update_review_state")
        runner = CliRunner()
        result = runner.invoke(
            synchronize,
            ["flore-prio", "--project_id", 99, "--form_id", "bidon2"],
        )
        print(result.stdout)
        assert result.exit_code == 0

    def test_bis(self, module):
        runner = CliRunner()

        result = runner.invoke(test)
        assert result.exit_code == 0


@pytest.mark.usefixtures("temporary_transaction")
class TestUtilsFunctions:
    def test_format_jdd_list1(self, datasets):
        ds = format_jdd_list(datasets)

        assert type(ds) is list
        dict_cols = set(ds[0].keys())
        assert set(["id_dataset", "dataset_name"]).issubset(dict_cols)

    def test_to_csv1(self, header, data):
        content = to_csv(header, data).split("\n")
        print("content = ", content)
        reader = csv.reader(content)
        assert header == reader.__next__()
        r_data = []
        for row in reader:
            r_data.append(row)
        print("r_data  = ", r_data)
        assert r_data == [["1", "2"], ["3", "4"], []]

    def test_get_taxon_list1(self, taxon_and_list):
        taxons = get_taxon_list(taxon_and_list["tax_list"].id_liste)
        # autre chose)
        # assert taxon_and_list["taxon"].cd_nom in [t[0] for t in taxons]
        assert type(taxons) is list
        dict_cols = set(taxons[0].keys())
        assert set(["cd_nom", "nom_vern", "nom_complet"]).issubset(dict_cols)

    def test_get_observer_list1(self, observers_and_list):
        observers = get_observer_list(observers_and_list["list"].id_liste)
        assert type(observers) is list
        dict_cols = set(observers[0].keys())
        assert set(["id_role", "nom_complet"]).issubset(dict_cols)

    def test_get_site_list1(self, module, site):
        sites = get_site_list(module.id_module)
        print(sites)
        assert type(sites) is list
        dict_cols = set(sites[0].keys())
        assert set(["id_base_site", "base_site_name", "geometry"]).issubset(dict_cols)

    def test_get_nomenclature_list1(self, nomenclature):
        nomenclatures = get_ref_nomenclature_list(code_nomenclature_type="TEST")
        assert nomenclature.id_nomenclature in [nom["id_nomenclature"] for nom in nomenclatures]
        assert type(nomenclatures) is list
        dict_cols = set(nomenclatures[0].keys())
        assert set(["mnemonique", "id_nomenclature", "cd_nomenclature", "label_default"]).issubset(
            dict_cols
        )
        assert nomenclatures[0]["mnemonique"] == "TEST"
        noms2 = get_ref_nomenclature_list(code_nomenclature_type="TEST", cd_nomenclatures=["test"])
        assert nomenclature.id_nomenclature in [nom["id_nomenclature"] for nom in noms2]
        assert type(noms2) is list
        dict_cols = set(noms2[0].keys())
        assert set(["mnemonique", "id_nomenclature", "cd_nomenclature", "label_default"]).issubset(
            dict_cols
        )

    """ def test_bidule(self, test):
        user = db.session.query(User).filter_by(identifiant="bidule").one()
        print(user) """

    def test_get_modules_info1(self, module):
        mod = get_modules_info(module.module_code)
        assert mod == module

    # def test_bidule2(test):
    #     user = db.session.query(UserList).filter_by(identifiant="bidule").one()
    #     print(user)

    def test_pf_files(self):
        files = write_files()
        assert type(files) is dict
        files_names = set(files.keys())
        assert set(["pf_nomenclatures.csv", "pf_observers.csv", "pf_taxons.csv"]).issubset(
            files_names
        )

    def test_monitoring_files(self, module):
        files = get_gn2_attachments_data(module, skip_nomenclatures=True)
        assert type(files) is dict
        files_names = set(files.keys())
        assert set(
            [
                "gn_jdds.csv",
                "gn_observateurs.csv",
                "gn_sites.csv",
                "gn_taxons.csv",
            ]
        ).issubset(files_names)
