
from sqlalchemy.orm.exc import NoResultFound
from geonature.utils.env import DB
from geonature.core.users.models import (
    VUserslistForallMenu
)
from geonature.core.gn_meta.models import TDatasets
from geonature.core.gn_monitoring.models import TBaseSites, corSiteModule
from gn_module_monitoring.monitoring.models import (
    TMonitoringModules
)

from pypnnomenclature.models import (
    TNomenclatures, BibNomenclaturesTypes, CorTaxrefNomenclature
)

from gn_monitoring_odk.monitoring_config import (
    get_nomenclatures_fields
)
from apptax.taxonomie.models import BibListes, CorNomListe, Taxref, BibNoms

import csv

def get_modules_info(module_code: str):
        try:
            module = TMonitoringModules.query.filter_by(
                module_code=module_code
            ).one()
            return module
        except NoResultFound:
            return None

def get_gn2_attachments_data(
        module:TMonitoringModules
    ):
        files = {}
        # Taxon
        data = get_taxon_list(module.id_list_taxonomy)
        files['gn_taxons.csv'] = to_csv(
            header=("cd_nom", "nom_complet", "nom_vern"),
            data=data
        )
        # Observers
        data = get_observer_list(module.id_list_observer)
        files['gn_observateurs.csv'] = to_csv(
            header=("id_role", "nom_complet"),
            data=data
        )
        # JDD
        data = get_jdd_list(module.datasets)
        files['gn_jdds.csv'] = to_csv(
            header=("id_role", "nom_complet"),
            data=data
        )
        # Sites
        data = get_site_list(module.sites)
        files['gn_sites.csv'] = to_csv(
            header=("id_base_site", "base_site_name"),
            data=data
        )

        # Nomenclature
        n_fields = []
        for niveau in ["site", "visit", "observation"]:
            n_fields = n_fields + get_nomenclatures_fields(
                module_code=module.module_code,
                niveau=niveau
            )

        nomenclatures = get_nomenclature_data(n_fields)
        files['gn_nomenclature.csv'] = to_csv(
            header=("mnemonique", "id_nomenclature", "cd_nomenclature", "label_default"),
            data=nomenclatures
        )
        return files


def get_taxon_list(id_liste: int):
    """Return tuple of Taxref for id_liste

    :param id_liste: Identifier of the taxref list
    :type id_liste: int
    """
    data = (
        DB.session.query(Taxref.cd_nom, Taxref.nom_complet, Taxref.nom_vern)
        .filter(BibNoms.cd_nom == Taxref.cd_nom)
        .filter(BibNoms.id_nom == CorNomListe.id_nom)
        .filter(CorNomListe.id_liste == id_liste)
        .all()
    )
    return data


def get_site_list(sites: []):
    """Return tuple of TBase site for module

    :param sites: Liste des sites
    :type id_liste: []
    """
    data = [(s.id_base_site, s.base_site_name) for s in sites]
    return data


def get_observer_list(id_liste: int):
    """Return tuple of Observers for id_liste

    :param id_liste: Identifier of the taxref list
    :type id_liste: int
    """
    data = DB.session.query(VUserslistForallMenu.id_role, VUserslistForallMenu.nom_complet).filter_by(id_menu=id_liste)
    return data

def get_jdd_list(datasets: []):
    """Return tuple of Dataset

    :param datasets: List of associated dataset
    :type datasets: []
    """
    ids = [jdd.id_dataset for jdd in datasets]
    data = DB.session.query(
        TDatasets.id_dataset, TDatasets.dataset_name
    ).filter(TDatasets.id_dataset.in_(ids))
    return data

def get_ref_nomenclature_list(
        code_nomenclature_type: str,
        cd_nomenclatures: [] = None,
        regne: str = None,
        group2_inpn: str = None,
    ):
    q = DB.session.query(
        BibNomenclaturesTypes.mnemonique,
        TNomenclatures.id_nomenclature,
        TNomenclatures.cd_nomenclature,
        TNomenclatures.label_default
    ).filter(
        BibNomenclaturesTypes.id_type == TNomenclatures.id_type
    ).filter(
        BibNomenclaturesTypes.mnemonique == code_nomenclature_type
    )
    if cd_nomenclatures:
        q = q.filter(
            TNomenclatures.cd_nomenclature.in_(cd_nomenclatures)
        )

    if regne:
        q = q.filter(
            CorTaxrefNomenclature.id_nomenclature == TNomenclatures.id_nomenclature
        ).filter(
            CorTaxrefNomenclature.regne == regne
        )
        if group2_inpn:
            q = q.filter(
                CorTaxrefNomenclature.group2_inpn == group2_inpn
            )

    return q.all()

def get_nomenclature_data(nomenclatures_fields):
    data = []
    for f in nomenclatures_fields:
        data = data + get_ref_nomenclature_list(**f)
    return data

def to_csv(header, data):
    """Return tuple in csv format

    :param header: _description_
    :type header: _type_
    :param data: _description_
    :type data: _type_
    :return: _description_
    :rtype: _type_
    """
    out = []
    out.append(",".join(header))
    for d in data:
        out.append(",".join(map(str, d)))
    return "\n".join(out)