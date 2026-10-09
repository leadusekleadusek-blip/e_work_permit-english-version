import datetime
import json
import urllib.request
import streamlit as st
import unicodedata
from fpdf import FPDF

# ---------------------------------------------------------
# CONFIGURATION DE LA PAGE
# ---------------------------------------------------------
st.set_page_config(
    page_title="P&G Amiens — Système e-Permis de Travail",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS
st.markdown("""
<style>
    .stApp { background-color: #f8fafc !important; }
    .main { background-color: #f8fafc; }
    .pg-header {
        background: linear-gradient(135deg, #003366 0%, #0056b3 100%);
        color: white; padding: 22px; border-radius: 12px; margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .welcome-card {
        background: white; border: 1px solid #cbd5e1; padding: 30px; border-radius: 12px;
        text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 15px;
    }
    .weather-container {
        border-radius: 12px; padding: 18px 24px; margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: all 0.3s ease;
    }
    .weather-ok { background-color: #dcfce7; border: 2px solid #22c55e; color: #15803d; }
    .weather-warning { background-color: #fef08a; border: 2px solid #eab308; color: #a16207; }
    .weather-alert { background-color: #fef2f2; border: 2px solid #ef4444; color: #b91c1c; }
    
    .weather-flex { display: flex; align-items: center; gap: 25px; }
    .weather-icon-large { font-size: 4rem; line-height: 1; }
    .weather-details { flex-grow: 1; }
    
    .urgence-card {
        background-color: #fef2f2; border: 2px solid #ef4444; color: #991b1b;
        padding: 18px; border-radius: 10px; margin-bottom: 20px;
    }
    .notice-epi-card {
        background-color: #fffbebf8; border: 2px solid #f59e0b; color: #92400e;
        padding: 16px; border-radius: 10px; margin-bottom: 15px; font-weight: 600;
    }
    .status-pending {
        background-color: #fef08a; color: #854d0e; border: 2px solid #eab308;
        padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 1.1rem;
        margin-bottom: 15px;
    }
    .stButton>button { border-radius: 8px; font-weight: bold; }
    div[data-baseweb="input"] { background-color: #e0f2fe !important; border: 1.5px solid #0284c7 !important; border-radius: 8px !important; }
    div[data-baseweb="select"] > div { background-color: #e0f2fe !important; border: 1.5px solid #0284c7 !important; border-radius: 8px !important; }
    .stepper-container { background: white; border: 1px solid #cbd5e1; border-radius: 12px; padding: 24px 20px 18px 20px; margin-bottom: 25px; box-shadow: 0 2px 4px rgba(0,0,0,0.03); }
    .stepper-wrapper { position: relative; display: flex; justify-content: space-between; align-items: flex-start; }
    .progress-track { position: absolute; top: 13px; left: 5%; right: 5%; height: 4px; background-color: #e2e8f0; z-index: 1; }
    .progress-fill { height: 100%; background-color: #10b981; transition: width 0.4s ease-in-out; }
    .step-item { display: flex; flex-direction: column; align-items: center; flex: 1; font-size: 0.8rem; font-weight: 600; color: #64748b; text-align: center; z-index: 2; }
    .step-badge { width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.85rem; font-weight: bold; margin-bottom: 8px; background-color: white; border: 3px solid #cbd5e1; color: #64748b; transition: all 0.3s ease; }
    .step-completed .step-badge { background-color: #10b981; border-color: #10b981; color: white; }
    .step-completed { color: #059669; }
    .step-active .step-badge { background-color: #003366; border-color: #003366; color: white; box-shadow: 0 0 0 4px rgba(0, 51, 102, 0.2); }
    .step-active { color: #003366; font-weight: bold; }
    .step-upcoming .step-badge { background-color: white; border-color: #cbd5e1; color: #94a3b8; }
    
    .permis-header-card {
        background: #f1f5f9;
        border-left: 6px solid #003366;
        padding: 12px 18px;
        border-radius: 6px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# INITIALISATION DE L'ÉTAT ET DES TRADUCTIONS
# ---------------------------------------------------------
if "lang" not in st.session_state:
    st.session_state.lang = "FR"

if "permis_db" not in st.session_state:
    st.session_state.permis_db = []

if "kiosk_mode" not in st.session_state:
    st.session_state.kiosk_mode = "HOME"

if "step" not in st.session_state:
    st.session_state.step = 1

TR = {
    "FR": {
        "title": "PROCTER & GAMBLE — AMIENS",
        "subtitle": "SYSTÈME E-PERMIS DE TRAVAIL — BORNE TACTILE",
        "home_select": "Veuillez sélectionner votre démarche :",
        "btn_work_permit": "🚀 PERMIS DE TRAVAIL",
        "desc_work_permit": "Émettre un nouveau Permis de Travail complet.",
        "btn_start_permit": "🚀 COMMENCER UN PERMIS DE TRAVAIL",
        "btn_pdp": "📝 ÉMARGEMENT PDP",
        "desc_pdp": "Émarger un Plan de Prévention.",
        "btn_start_pdp": "📝 SIGNER UN PLAN DE PRÉVENTION (PDP)",
        "lang_title": "🌐 Langue :",
        "steps": ["Date & EE", "PDP & MoP", "Responsable N2", "Zone & Urgences", "Check-list & EPI", "Permis Spécifiques", "Synthèse & Signatures"],
        "back_home": "⬅️ Accueil",
        "next": "Suivant ➔",
        "previous": "⬅️ Précédent",
        "submit_batch": "🚀 SOUMETTRE AU BATCH DE 07h30",
        "download_pdf": "📄 TÉLÉCHARGER PERMIS PDF",
        "weather_title": "MÉTÉO EN DIRECT — ZONE INDUSTRIELLE AMIENS NORD",
        "weather_today": "Aujourd'hui :",
        "weather_tomorrow": "Demain :",
        "weather_gusts": "Rafales de vent max :",
        "emergencies_title": "📞 NUMÉROS DE TÉLÉPHONE D'URGENCE DU SITE P&G AMIENS :",
        "gate": "Poste de Garde :",
        "infirmary": "Infirmerie :",
        "fire": "Incendie / Environnement :",
        "subcontract_alert": "🤝 Règle de sous-traitance : L'entreprise sélectionnée étant en sous-traitance, le responsable N2 de la société principale doit également valider le permis.",
    },
    "EN": {
        "title": "PROCTER & GAMBLE — AMIENS",
        "subtitle": "WORK PERMIT SYSTEM — TOUCH TERMINAL",
        "home_select": "Please select your workflow:",
        "btn_work_permit": "🚀 WORK PERMIT",
        "desc_work_permit": "Issue a complete new Work Permit.",
        "btn_start_permit": "🚀 START A WORK PERMIT",
        "btn_pdp": "📝 PDP SIGN-OFF",
        "desc_pdp": "Sign off a Prevention Plan.",
        "btn_start_pdp": "📝 SIGN A PREVENTION PLAN (PDP)",
        "lang_title": "🌐 Language:",
        "steps": ["Date & Contractor", "PDP & MoP", "N2 Lead", "Location & Emergencies", "Checklist & PPE", "Specific Permits", "Summary & Signatures"],
        "back_home": "⬅️ Home",
        "next": "Next ➔",
        "previous": "⬅️ Previous",
        "submit_batch": "🚀 SUBMIT TO 07:30 AM BATCH",
        "download_pdf": "📄 DOWNLOAD PERMIT PDF",
        "weather_title": "LIVE WEATHER — AMIENS NORTH INDUSTRIAL ZONE",
        "weather_today": "Today:",
        "weather_tomorrow": "Tomorrow:",
        "weather_gusts": "Max Wind Gusts:",
        "emergencies_title": "📞 P&G AMIENS SITE EMERGENCY PHONE NUMBERS:",
        "gate": "Guard House:",
        "infirmary": "Medical Center:",
        "fire": "Fire / Environment Response:",
        "subcontract_alert": "🤝 Subcontracting Rule: Since the selected company is a subcontractor, the main contractor's N2 supervisor must also approve the permit.",
    }
}

L = TR[st.session_state.lang]

# ---------------------------------------------------------
# API MÉTÉO EN DIRECT
# ---------------------------------------------------------
@st.cache_data(ttl=1800)
def obtenir_meteo_amiens_live():
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=49.9250&longitude=2.2900&daily=temperature_2m_max,temperature_2m_min,windgusts_10m_max,weathercode&timezone=Europe%2FParis"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            code = data['daily']['weathercode'][0]
            
            if code in [0, 1]: icon = "☀️"
            elif code in [2, 3]: icon = "⛅"
            elif code in [45, 48]: icon = "🌫️"
            elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]: icon = "🌧️"
            elif code in [95, 96, 99]: icon = "🌩️"
            else: icon = "☁"

            vent = round(data['daily']['windgusts_10m_max'][0])
            if vent >= 30: icon = "💨"

            return {
                "temp_max_j0": round(data['daily']['temperature_2m_max'][0]),
                "temp_min_j0": round(data['daily']['temperature_2m_min'][0]),
                "vent_j0": vent,
                "code_w_j0": code,
                "icon_j0": icon,
                "temp_max_j1": round(data['daily']['temperature_2m_max'][1]),
                "vent_j1": round(data['daily']['windgusts_10m_max'][1]),
                "source": "Open-Meteo Live API (ZI Amiens Nord)"
            }
    except Exception:
        return {"temp_max_j0": 18, "temp_min_j0": 8, "vent_j0": 14, "code_w_j0": 0, "icon_j0": "☀️", "temp_max_j1": 19, "vent_j1": 12, "source": "Mode Secours"}

# ---------------------------------------------------------
# RÉFÉRENTIELS ET BASES DE DONNÉES P&G
# ---------------------------------------------------------
db_societes = ["ABYLSEN", "APAVE", "AXIMA", "ENGIE", "EULER", "SOUS-TRAITANCE-EXPERT"]

db_pdps = {
    "FR": {
        "ABYLSEN": ["PDP-2026-042 (Bâtiment M1)"],
        "APAVE": ["PDP-2026-104 (Inspection Pression)"],
        "AXIMA": ["PDP-2026-015 (HVAC Zone Production M1)"],
        "ENGIE": ["PDP-2026-067 (Chaufferie Vapeur)"],
        "EULER": ["PDP-2026-090 (Génie Civil / Terrassement)"],
        "SOUS-TRAITANCE-EXPERT": ["PDP-2026-042 (Sous-traitant ABYLSEN)"]
    },
    "EN": {
        "ABYLSEN": ["PDP-2026-042 (Building M1)"],
        "APAVE": ["PDP-2026-104 (Pressure Inspection)"],
        "AXIMA": ["PDP-2026-015 (HVAC Production Area M1)"],
        "ENGIE": ["PDP-2026-067 (Boiler House)"],
        "EULER": ["PDP-2026-090 (Civil Engineering)"],
        "SOUS-TRAITANCE-EXPERT": ["PDP-2026-042 (ABYLSEN Subcontractor)"]
    }
}

db_mops = {
    "FR": {
        "PDP-2026-042 (Bâtiment M1)": [{"titre": "MoP-01: Peinture & Finitions", "st": False}],
        "PDP-2026-042 (Sous-traitant ABYLSEN)": [{"titre": "MoP-02-ST: Électromécanique", "st": True, "titulaire": "ABYLSEN"}],
        "PDP-2026-104 (Inspection Pression)": [{"titre": "MoP-01: Épreuve Hydraulique", "st": False}],
        "PDP-2026-015 (HVAC Zone Production M1)": [{"titre": "MoP-01: Nettoyage Filtres CTA", "st": False}],
        "PDP-2026-067 (Chaufferie Vapeur)": [{"titre": "MoP-01: Isoler Purgeur Vapeur", "st": False}],
        "PDP-2026-090 (Génie Civil / Terrassement)": [{"titre": "MoP-01: Fouille Terrassement", "st": False}]
    },
    "EN": {
        "PDP-2026-042 (Building M1)": [{"titre": "MoP-01: Painting & Finishing", "st": False}],
        "PDP-2026-042 (ABYLSEN Subcontractor)": [{"titre": "MoP-02-ST: Electromechanics", "st": True, "titulaire": "ABYLSEN"}],
        "PDP-2026-104 (Pressure Inspection)": [{"titre": "MoP-01: Hydraulic Pressure Check", "st": False}],
        "PDP-2026-015 (HVAC Production Area M1)": [{"titre": "MoP-01: Air Filters Cleaning", "st": False}],
        "PDP-2026-067 (Boiler House)": [{"titre": "MoP-01: Steam Trap Isolation", "st": False}],
        "PDP-2026-090 (Civil Engineering)": [{"titre": "MoP-01: Trenching Work", "st": False}]
    }
}

db_n2 = ["Léa DUSEK", "Matthieu MARTIN", "Alexandre LEFEBVRE", "Cindy BERNARD"]

db_zones_carto = {
    "FR": {
        "Bâtiment M1 - Zone Production": {"pr": "PR-2 (Parking Ouest)", "confinement": "ZC-01 (Hall M1)", "sprinkler": True, "detection": True},
        "Bâtiment M1 - Bureaux / Toiture": {"pr": "PR-2 (Parking Ouest)", "confinement": "ZC-01 (Hall M1)", "sprinkler": False, "detection": True},
        "Bâtiment M2 - Conditionnement": {"pr": "PR-4 (Zone Nord)", "confinement": "ZC-03 (Atrium M2)", "sprinkler": True, "detection": True},
        "Zone Extérieure / Logistique": {"pr": "PR-1 (Entrée Principale)", "confinement": "ZC-00 (Poste de Garde)", "sprinkler": False, "detection": False}
    },
    "EN": {
        "Building M1 - Production Area": {"pr": "PR-2 (West Parking)", "confinement": "ZC-01 (Hall M1)", "sprinkler": True, "detection": True},
        "Building M1 - Roof & Offices": {"pr": "PR-2 (West Parking)", "confinement": "ZC-01 (Hall M1)", "sprinkler": False, "detection": True},
        "Building M2 - Packaging Area": {"pr": "PR-4 (North Zone)", "confinement": "ZC-03 (Atrium M2)", "sprinkler": True, "detection": True},
        "Outdoor Zone / Logistics": {"pr": "PR-1 (Main Gate)", "confinement": "ZC-00 (Control Room)", "sprinkler": False, "detection": False}
    }
}

db_materiaux = {
    "FR": ["Acier Carbone", "Inox 316L", "Aluminium", "Béton", "PVC / Plastique"],
    "EN": ["Carbon Steel", "Stainless Steel 316L", "Aluminum", "Concrete", "PVC / Plastic"]
}

db_disques_blanchiment = {
    "FR": ["Disque fibre abrasif", "Brosse métallique", "Clean & Strip"],
    "EN": ["Abrasive Fiber Disc", "Wire Brush", "Clean & Strip"]
}

VALEURS_PAR_DEFAUT = {
    "date_str": datetime.date.today().strftime("%d/%m/%Y"),
    "societe": "ABYLSEN",
    "pdp": "PDP-2026-042 (Bâtiment M1)",
    "mop": "MoP-01: Peinture & Finitions",
    "is_subcontractor": False,
    "titulaire_n2": "",
    "n2_nom": "Léa DUSEK",
    "lieu_pdp": "Bâtiment M1 - Bureaux / Toiture",
    "lieu_precision": "1er étage, Bureau 104",
    "description": "Maintenance et travaux sur site",
    "intervenants": ["Léa DUSEK", "Matthieu MARTIN"],
    
    # RISQUES PRINCIPAUX
    "p_hauteur": False, "h_exterieur": False, "p_toiture": False, "p_points_chauds": False, "p_excavation": False,
    "p_grutage": False, "grut_exterieur": True, "p_confine": False, "p_electrique": False, "p_ouverture_circuit": False,
    "p_machines_mouvement": False, "p_equipement_pression": False, "p_laser_classe_iv": False,
    "p_demolition": False, "p_meuleuse": False, "dta_consultation": False, "p_consignation": False,
    "p_systeme_risque": False,

    # STA
    "sta_prod_chimiques": False, "sta_prod_chimiques_nom": "", "t_outils_electro": False,
    "t_travaux_manuels": True, "t_manutention_lourde": False, "t_nettoyage_chantiers": True,

    # MEULEUSE
    "meuleuse_diametre": "125 mm", "meuleuse_operateurs": ["Léa DUSEK"], "meuleuse_marque": "Bosch Pro",
    "meuleuse_alim": "Batterie 18V", "meuleuse_ref": "MEU-042", "meuleuse_vitesse": "11000",
    "meu_env_plain_pied": True, "meu_env_hauteur": False, "meu_env_confine": False, "meu_env_excavation": False,
    "meu_env_stable": True, "meu_env_maintien_2mains": True, "meu_env_piece_fixee": True, "meu_env_hors_ligne_tir": True,
    "meuleuse_u_decoupe": False, "meuleuse_mat_decoupe": "Acier Carbone", "meuleuse_u_ebavurage": False,
    "meuleuse_mat_ebavurage": "Acier Carbone", "meuleuse_u_flap": False, "meuleuse_u_blanchiment": False,
    "meuleuse_disque_blanchiment": "Disque fibre abrasif",

    # EPIS
    "epi_lunettes_chantier_en166": True, "epi_lunettes_etanches": False, "epi_visiere_idra_en166b": False,
    "epi_lunettes_pare_visage": False, "epi_casque_jugulaire": True, "epi_casque_protection_auditive_en387": False,
    "epi_gants_anticoupure_4x43d": True, "epi_gants_manutention_cuir": True, "epi_gants_chimiques_en374": False,
    "epi_gants_elec_en60903": False, "epi_bouchons_oreilles": False, "epi_resp_ffp1_ffp2": False,
    "epi_resp_3m6000": False, "epi_resp_versaflo": False, "epi_resp_cartouche_abek_en14387": False, "epi_autre_texte": "",

    # PERMIS SPÉCIFIQUES
    "h_pirl": False, "h_pirl_vgp": True, "h_pirl_soc": "ABYLSEN",
    "h_nacelle": False, "h_nacelle_vgp": True, "h_nacelle_checklist": True, "h_nacelle_caces": True, "h_nacelle_aut": True, "h_nacelle_harnais": True, "h_nacelle_soc": "ABYLSEN",
    "h_echaf": False, "h_echaf_montage": False, "h_echaf_montage_qualif": True, "h_echaf_montage_harnais": True, "h_echaf_util": False, "h_echaf_util_qualif": True, "h_echaf_ctrl_regle": True, "h_echaf_certif_affiche": True, "h_echaf_verif_j": True, "h_echaf_soc_util": "ABYLSEN",
    "toiture_protection": "Garde-corps", "toiture_valideur": "Matthieu MARTIN",
    "chaud_gants_soudeur": False, "chaud_gants_chaleur": False, "chaud_gants_anticoupure": True, "chaud_extincteur1": "Eau + additifs", "chaud_extincteur2": "CO2", "chaud_degage_10m": True, "chaud_baches": False, "chaud_traverse_mur": False, "chaud_vigie_opposee": False, "chaud_ouverture_10m": False, "chaud_obstruction": False, "chaud_vigie_autre_cote": False, "chaud_vigie_nom": "Matthieu MARTIN", "chaud_personne_surv_60m": "Léa DUSEK", "chaud_heure_fin": "15:00", "chaud_heure_depart": "16:00", "chaud_commentaires": "",
    "excav_plans_eaux_indus": True, "excav_plans_eaux_usees": True, "excav_plans_eaux_pluv": True, "excav_plans_eaux_incendie": True, "excav_plans_ht": True, "excav_plans_bt": True, "excav_plans_gaz": True, "excav_struct_proximite": False, "excav_architecte": False, "excav_dict": True, "excav_effondrement": False, "excav_eau_pompe": False, "excav_balisage": True, "excav_vehicule_3m": True, "excav_deblais": True, "excav_acces": "Escalier / Rampe", "excav_profondeur_130": False, "excav_blindage": False, "excav_schema_commentaires": "", "excav_chef_manoeuvre": "Léa DUSEK", "excav_do": "Matthieu MARTIN", "excav_casque_rouge": "Alexandre LEFEBVRE",
    "grut_desc_mop": "Levage groupe froid rooftop", "grut_poids_charge": 2500.0, "grut_poids_acc": 200.0, "grut_unite": "kg", "grut_immat": "CRANE-AMIENS-88", "grut_fleche": 35.0, "grut_portee": 20.0, "grut_pression_patin": "12 T/m²", "grut_rayon": 15.0, "grut_balisage": True, "grut_plan_vue": True, "grut_plan_elev": True, "grut_obstacles": True, "grut_anemometre": True, "grut_vent_val": 18.0, "grut_vent_unite": "km/h", "grut_pesage": True, "grut_centre_gravite": True, "grut_angles_elingue": True, "grut_plaques_rep": True, "grut_chef_m_nom": "Léa DUSEK", "grut_chef_m_soc": "ABYLSEN", "grut_elingueur_nom": "Matthieu MARTIN", "grut_elingueur_soc": "ABYLSEN", "grut_grutier_nom": "Jean LEVAGE", "grut_grutier_soc": "APAVE", "grut_certif_grue": True, "grut_certif_acc": True, "grut_certif_plaques": True, "grut_check_j_grue": True, "grut_check_j_acc": True, "grut_pattes_concu": True, "grut_pattes_defaut": False, "grut_pattes_adequation": True, "grut_charges_annexes": True, "grut_schema_commentaires": "", "grut_do_sign": "Matthieu MARTIN", "grut_casque_rouge_sign": "Alexandre LEFEBVRE",
    "conf_lieu": "Cuve C-102", "conf_r_atmo": True, "conf_r_chimique": False, "conf_r_inflam": False, "conf_r_orga": False, "conf_r_meca": False, "conf_r_thermiq": False, "conf_r_bruit": False, "conf_troudhomme_610": True, "conf_catec": True, "conf_hauteur": False, "conf_m20": True, "conf_secouriste": "Attribution automatique", "conf_medical": "Attribution automatique", "conf_action_chaud": False, "conf_ventilation_nat": True, "conf_ventilation_forcee": True, "conf_ventilation_debit": "Min 56m3/h par personne", "conf_consignation_gaz": True, "conf_cuve_vide": True, "conf_vol_caches": False, "conf_eclairage_24v": True, "conf_blocage_ouvert": True, "conf_echaf_echelle": False, "conf_prod_chim": False, "conf_laser": False, "conf_comm_type": "Talkie Walkie", "conf_o2": 20.9, "conf_o2_contre_mesure": 20.9, "conf_h2s_check": False, "conf_h2s": 0.0, "conf_co_check": False, "conf_co": 0.0, "conf_explo_check": False, "conf_explo": 0.0, "conf_temp_cuve": 22.0, "conf_verif_temp": "N2", "conf_inflam_lel": 0.0, "conf_verif_lel": "N2", "conf_schema_commentaires": "", "conf_entrant": "Léa DUSEK", "conf_standby": "Matthieu MARTIN", "conf_do": "Alexandre LEFEBVRE",
    "elec_modife": False, "elec_armoire": True, "elec_voisinage_tension": True, "elec_courant_faible": False, "elec_releve": True, "elec_chemins": False, "elec_voisinage_nues": False, "elec_valideur_ei": "E&I / PT E&I (B2, H2, BC, HC)",
    "loto_ouverture_methode": "2 vannes + drain", "loto_ouvert_loc1": "Vanne V-101 amont", "loto_ouvert_loc2": "Vanne V-102 aval", "loto_is_elec": True, "loto_is_elec_loc1": "TGBT-M1-Armoire 4", "loto_is_elec_loc2": "Cadenas #884", "loto_fusible": False, "loto_fusible_loc1": "", "loto_fusible_loc2": "", "loto_cable": False, "loto_cable_loc1": "", "loto_cable_loc2": "", "loto_pneu": False, "loto_pneu_loc1": "", "loto_pneu_loc2": "", "loto_hydra": False, "loto_hydra_loc1": "", "loto_hydra_loc2": "", "loto_residu": True, "loto_residu_loc1": "Purge pression", "loto_residu_loc2": "Manomètre à 0 bar", "loto_drain_ouvert": True, "loto_eq_ouvert": True, "loto_eq_lave": True, "loto_eq_sanitise": True,
    "sr_chimique_c1": False, "sr_chimique_nom": "", "sr_fluide_dang": False, "sr_fluide_nom": "", "sr_atex": False, "sr_atex_nom": "", "sr_balisage": True, "sr_douche_rince": True, "sr_ramonage": False, "sr_ramonage_dt": "01/10/2026 08:00", "sr_isolement": True, "sr_feuille_loto": True, "sr_zonage_atex": True, "sr_epi_ecran": True, "sr_epi_lunettes": False, "sr_epi_gants_chim": True, "sr_epi_comb1": False, "sr_epi_comb2": True, "sr_epi_bottes": True, "sr_epi_cartouche": True, "sr_epi_ari": False, "sr_epi_3m6000": False, "sr_epi_versaflo": False, "sr_epi_no_versaflo": True, "sr_auxiliaire_equipe": True, "sr_comm_moyen": "Talkie-Walkie ATEX", "sr_inspect_remise": True, "sr_inspect_nom": "Léa DUSEK", "sr_inspect_dt": "01/10/2026 17:00", "sr_schema_commentaires": "", "sr_sign_intervenant": "Léa DUSEK", "sr_sign_do": "Matthieu MARTIN", "sr_sign_operations": "Alexandre LEFEBVRE"
}

if "form_data" not in st.session_state:
    st.session_state.form_data = dict(VALEURS_PAR_DEFAUT)
else:
    for k, v in VALEURS_PAR_DEFAUT.items():
        if k not in st.session_state.form_data:
            st.session_state.form_data[k] = v

def get_val(key, default=None):
    if default is None:
        default = VALEURS_PAR_DEFAUT.get(key, False)
    return st.session_state.form_data.get(key, default)

def sanitize_text(text):
    if not isinstance(text, str): text = str(text)
    text = text.replace("🔥", "[Point Chaud]").replace("🦺", "[Confiné]").replace("🧗", "[Hauteur]").replace("⚡", "[Consignation]").replace("⚠️", "[!]").replace("✅", "[OK]").replace("🚜", "[Excavation]")
    normalized = unicodedata.normalize('NFKD', text)
    cleaned = ''.join(c for c in normalized if not unicodedata.combining(c))
    return cleaned.encode('latin-1', 'ignore').decode('latin-1')

# Helper pour détecter les blocages météo stricts (seulement sur extérieur)
def is_meteo_blocked(vent, temp_max):
    critique = (vent > 36 or temp_max < 3 or temp_max > 30)
    hauteur_ext = get_val("p_hauteur") and get_val("h_exterieur")
    grutage_ext = get_val("p_grutage") and get_val("grut_exterieur")
    toiture = get_val("p_toiture")
    return critique and (hauteur_ext or grutage_ext or toiture)

# ---------------------------------------------------------
# GÉNÉRATION DU PDF EXACTEMENT IDENTIQUE À L'ÉTAPE 7
# ---------------------------------------------------------
def generer_pdf_bytes(permis):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    is_fr = (st.session_state.lang == "FR")

    # Entête PDF
    pdf.set_fill_color(0, 51, 102)
    pdf.rect(10, 10, 190, 22, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 13)
    titre_pdf = "PROCTER & GAMBLE AMIENS - e-Permis de Travail" if is_fr else "PROCTER & GAMBLE AMIENS - e-Work Permit"
    pdf.text(15, 20, sanitize_text(titre_pdf))
    pdf.set_font("Helvetica", "", 10)
    pdf.text(15, 27, sanitize_text(f"Ref: {permis['id']} | Date: {permis['date_travaux']} | Heure: {permis['heure']}"))
    pdf.set_y(38)

    # Bandeau de statut
    if permis.get('statut') == 'VALIDÉ':
        pdf.set_fill_color(220, 252, 231); pdf.set_draw_color(34, 197, 94); pdf.set_text_color(22, 101, 52)
        status_str = "PERMIS VALIDÉ ET AUDITABLE SUR COMPTE ePDP" if is_fr else "PERMIT VALIDATED & AUDITABLE ON ePDP ACCOUNT"
    else:
        pdf.set_fill_color(254, 240, 138); pdf.set_draw_color(234, 179, 8); pdf.set_text_color(133, 77, 14)
        status_str = "PERMIS EN ATTENTE DE VALIDATION BATCH (07h30)" if is_fr else "PERMIT PENDING BATCH VALIDATION (07:30 AM)"

    pdf.rect(10, 38, 190, 10, 'DF')
    pdf.set_font("Helvetica", "B", 10)
    pdf.text(15, 44.5, sanitize_text(status_str))
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(52)

    # Section 1 : Informations Générales
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_fill_color(241, 245, 249)
    lbl_s1 = "1. INFORMATIONS GÉNÉRALES ET LOCALISATION" if is_fr else "1. GENERAL INFORMATION & LOCATION"
    pdf.cell(190, 6, sanitize_text(lbl_s1), 1, 1, 'L', True)
    pdf.set_font("Helvetica", "", 9)
    
    pdf.cell(95, 5, sanitize_text(f"Société: {permis['societe']}" if is_fr else f"Company: {permis['societe']}"), 0, 0)
    pdf.cell(95, 5, sanitize_text(f"Responsable N2: {permis['n2']}" if is_fr else f"N2 Supervisor: {permis['n2']}"), 0, 1)
    pdf.cell(190, 5, sanitize_text(f"PDP: {permis['pdp']}"), 0, 1)
    pdf.cell(190, 5, sanitize_text(f"MoP: {permis['mop']}"), 0, 1)
    if permis.get("is_subcontractor"):
        lbl_st = f"Responsable N2 Titulaire: {permis.get('titulaire_n2')}" if is_fr else f"Main Contractor N2 Lead: {permis.get('titulaire_n2')}"
        pdf.cell(190, 5, sanitize_text(f"[SOUS-TRAITANCE] {lbl_st}"), 0, 1)
    
    pdf.cell(190, 5, sanitize_text(f"Zone: {permis['zone']} ({permis.get('emplacement', '')})"), 0, 1)
    pdf.cell(190, 5, sanitize_text(f"Description: {permis.get('description', '')}"), 0, 1)
    pdf.cell(190, 5, sanitize_text(f"Intervenants: {', '.join(permis.get('intervenants', []))}"), 0, 1)
    
    carto = db_zones_carto.get(st.session_state.lang, {}).get(permis['zone'], {})
    lbl_urg = f"Points de Secours : PR {carto.get('pr', 'N/A')} | Confinement {carto.get('confinement', 'N/A')}" if is_fr else f"Emergency Points: Assembly {carto.get('pr', 'N/A')} | Shelter {carto.get('confinement', 'N/A')}"
    pdf.cell(190, 5, sanitize_text(lbl_urg), 0, 1)
    pdf.ln(3)

    # Section 2 : Tableau des risques
    pdf.set_font("Helvetica", "B", 11)
    lbl_s2 = "2. TABLEAU SYNTHÉTIQUE DES RISQUES IDENTIFIÉS" if is_fr else "2. RISK ASSESSMENT SUMMARY"
    pdf.cell(190, 6, sanitize_text(lbl_s2), 1, 1, 'L', True)
    pdf.set_font("Helvetica", "B", 8)
    
    lbl_c1 = "Activité / Travail" if is_fr else "Activity"
    lbl_c2 = "Risque Identifié" if is_fr else "Risk"
    lbl_c3 = "Mesures de Prévention" if is_fr else "Prevention"
    pdf.cell(55, 6, sanitize_text(lbl_c1), 1, 0, 'L', True)
    pdf.cell(55, 6, sanitize_text(lbl_c2), 1, 0, 'L', True)
    pdf.cell(80, 6, sanitize_text(lbl_c3), 1, 1, 'L', True)

    pdf.set_font("Helvetica", "", 8)
    for r in permis.get("tableau_risques", []):
        act_val = list(r.values())[0] if isinstance(r, dict) else r.get("activite", "")
        ris_val = list(r.values())[1] if isinstance(r, dict) else r.get("risque", "")
        prev_val = list(r.values())[2] if isinstance(r, dict) else r.get("prevention", "")
        
        pdf.cell(55, 6, sanitize_text(str(act_val))[:32], 1, 0)
        pdf.cell(55, 6, sanitize_text(str(ris_val))[:32], 1, 0)
        pdf.cell(80, 6, sanitize_text(str(prev_val))[:48], 1, 1)
    pdf.ln(3)

    # Section 3 : EPI
    pdf.set_font("Helvetica", "B", 11)
    lbl_s3 = "3. ÉQUIPEMENTS DE PROTECTION INDIVIDUELLE (EPI)" if is_fr else "3. PERSONAL PROTECTIVE EQUIPMENT (PPE)"
    pdf.cell(190, 6, sanitize_text(lbl_s3), 1, 1, 'L', True)
    pdf.set_font("Helvetica", "", 8)
    epis_str = ", ".join(permis.get("epis_cochis", ["EPI de base"]))
    pdf.multi_cell(190, 4, sanitize_text(f"EPI retenus: {epis_str}" if is_fr else f"Selected PPE: {epis_str}"))
    pdf.ln(3)

    # Section 4 : Permis spécifiques
    pdf.set_font("Helvetica", "B", 11)
    lbl_s4 = "4. DÉTAILS TECHNIQUES DES PERMIS SPÉCIFIQUES" if is_fr else "4. SPECIFIC PERMITS TECHNICAL DETAILS"
    pdf.cell(190, 6, sanitize_text(lbl_s4), 1, 1, 'L', True)
    pdf.set_font("Helvetica", "", 8)

    fd = st.session_state.form_data

    if fd.get("p_meuleuse"):
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(190, 4, sanitize_text("• Meuleuse :" if is_fr else "• Angle Grinder:"), 0, 1)
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(190, 4, sanitize_text(f"  Disque: {fd.get('meuleuse_diametre')} | Marque: {fd.get('meuleuse_marque')} | Alim: {fd.get('meuleuse_alim')} | N° Série: {fd.get('meuleuse_ref')}"))

    if fd.get("p_hauteur"):
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(190, 4, sanitize_text("• Travail en Hauteur :" if is_fr else "• Work at Height:"), 0, 1)
        pdf.set_font("Helvetica", "", 8)
        env_str = "Extérieur" if fd.get("h_exterieur") else "Intérieur (Sous bâtiment)"
        if not is_fr: env_str = "Outdoor" if fd.get("h_exterieur") else "Indoor (Inside building)"
        pdf.multi_cell(190, 4, sanitize_text(f"  Lieu: {env_str} | PIRL: {fd.get('h_pirl')} | Nacelle: {fd.get('h_nacelle')} | Échafaudage: {fd.get('h_echaf')}"))

    if fd.get("p_toiture"):
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(190, 4, sanitize_text("• Accès Toiture :" if is_fr else "• Roof Access:"), 0, 1)
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(190, 4, sanitize_text(f"  Protection: {fd.get('toiture_protection')} | Valideur: {fd.get('toiture_valideur')}"))

    if fd.get("p_points_chauds"):
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(190, 4, sanitize_text("• Permis Point Chaud :" if is_fr else "• Hot Work Permit:"), 0, 1)
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(190, 4, sanitize_text(f"  Extincteurs: {fd.get('chaud_extincteur1')} & {fd.get('chaud_extincteur2')} | Vigie: {fd.get('chaud_vigie_nom')} | Surveillance 60 min: {fd.get('chaud_personne_surv_60m')} | Départ: {fd.get('chaud_heure_depart')}"))

    if fd.get("p_excavation"):
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(190, 4, sanitize_text("• Excavation & Tranchée :" if is_fr else "• Excavation & Trenching:"), 0, 1)
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(190, 4, sanitize_text(f"  7 Plans Vérifiés | DICT OK | Signatures: Chef ({fd.get('excav_chef_manoeuvre')}), DO ({fd.get('excav_do')}), Casque Rouge ({fd.get('excav_casque_rouge')})"))

    if fd.get("p_grutage"):
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(190, 4, sanitize_text("• Grutage & Levage :" if is_fr else "• Crane & Lifting:"), 0, 1)
        pdf.set_font("Helvetica", "", 8)
        env_g_str = "Extérieur (Grue/Bras)" if fd.get("grut_exterieur") else "Intérieur (Palan/Pont roulant)"
        if not is_fr: env_g_str = "Outdoor (Crane)" if fd.get("grut_exterieur") else "Indoor (Hoist/Crane)"
        poids_t = float(fd.get('grut_poids_charge', 0)) + float(fd.get('grut_poids_acc', 0))
        pdf.multi_cell(190, 4, sanitize_text(f"  Zone: {env_g_str} | Poids Total: {poids_t} {fd.get('grut_unite')} | Immatriculation: {fd.get('grut_immat')} | Vent Mesuré: {fd.get('grut_vent_val')} {fd.get('grut_vent_unite')} | Anémomètre OK"))

    if fd.get("p_confine"):
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(190, 4, sanitize_text("• Espace Confiné :" if is_fr else "• Confined Space:"), 0, 1)
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(190, 4, sanitize_text(f"  Équipement: {fd.get('conf_lieu')} | Taux O2: {fd.get('conf_o2')}% | Entrant: {fd.get('conf_entrant')} | Vigie Extérieure: {fd.get('conf_standby')}"))

    if fd.get("p_electrique"):
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(190, 4, sanitize_text("• Travaux Électriques :" if is_fr else "• Electrical Works:"), 0, 1)
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(190, 4, sanitize_text(f"  Intérieur Armoire: {fd.get('elec_armoire')} | Pièces nues: {fd.get('elec_voisinage_nues')} | Valideur E&I: {fd.get('elec_valideur_ei')}"))

    if fd.get("p_consignation"):
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(190, 4, sanitize_text("• Consignation LOTO :" if is_fr else "• LOTO Isolation:"), 0, 1)
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(190, 4, sanitize_text(f"  Méthode: {fd.get('loto_ouverture_methode')} | N° Cadenas Elec: {fd.get('loto_is_elec_loc2')} | Purge résiduelle OK"))

    if fd.get("p_systeme_risque"):
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(190, 4, sanitize_text("• Systèmes à Risques / ATEX :" if st.session_state.lang == "FR" else "• High Hazard / ATEX:"), 0, 1)
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(190, 4, sanitize_text(f"  Balisage élargi OK | Douche sécurité vérifiée | Signatures: Opérateur ({fd.get('sr_sign_intervenant')}), DO ({fd.get('sr_sign_do')}), Fabrication ({fd.get('sr_sign_operations')})"))

    pdf.ln(3)

    # Section 5 : Signatures
    pdf.set_font("Helvetica", "B", 11)
    lbl_s5 = "5. SIGNATURES ÉLECTRONIQUES HORODATÉES DANS ePDP" if is_fr else "5. TIMESTAMPED ELECTRONIC SIGNATURES IN ePDP"
    pdf.cell(190, 6, sanitize_text(lbl_s5), 1, 1, 'L', True)
    pdf.set_font("Helvetica", "", 8)
    for sign in permis.get("intervenants", []):
        pdf.cell(190, 5, sanitize_text(f" [OK] Signature horodatée: {sign}"), 1, 1)

    return bytes(pdf.output())

# ---------------------------------------------------------
# BARRE LATÉRALE — DRAPEAUX EXCLUSIFS
# ---------------------------------------------------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Procter_%26_Gamble_logo.svg/1024px-Procter_%26_Gamble_logo.svg.png", width=80)
st.sidebar.title("e-Permis P&G")
st.sidebar.caption("Site d'Amiens")

role = st.sidebar.radio("Interface :", [
    "🖥️ Borne Kiosk Tactile", 
    "📊 DDS Board & Batch 07h30", 
    "📱 Inspection Terrain QR Code"
])

st.sidebar.divider()
st.sidebar.write(L["lang_title"])

col_l1, col_l2 = st.sidebar.columns(2)
with col_l1:
    if st.button("🇫🇷", use_container_width=True, type="primary" if st.session_state.lang == "FR" else "secondary", key="sb_lang_fr"):
        st.session_state.lang = "FR"
        st.rerun()
with col_l2:
    if st.button("🇬🇧", use_container_width=True, type="primary" if st.session_state.lang == "EN" else "secondary", key="sb_lang_en"):
        st.session_state.lang = "EN"
        st.rerun()

# ==============================================================================
# INTERFACE 1 : BORNE KIOSK TACTILE
# ==============================================================================
if "Kiosk" in role:

    st.markdown(f"<div class='pg-header'><h1 style='margin:0;'>{L['title']}</h1><p style='margin:0;'>{L['subtitle']}</p></div>", unsafe_allow_html=True)

    if st.session_state.kiosk_mode == "HOME":
        st.markdown("<div class='welcome-card'>", unsafe_allow_html=True)
        st.write(f"### {L['home_select']}")
        
        c_k1, c_k2 = st.columns(2)
        with c_k1:
            st.info(f"**{L['btn_work_permit']}**\n\n{L['desc_work_permit']}")
            if st.button(L["btn_start_permit"], type="primary", use_container_width=True):
                st.session_state.kiosk_mode = "PERMIS"
                st.session_state.step = 1
                st.rerun()
        with c_k2:
            st.success(f"**{L['btn_pdp']}**\n\n{L['desc_pdp']}")
            if st.button(L["btn_start_pdp"], type="primary", use_container_width=True):
                st.session_state.kiosk_mode = "PDP"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    elif st.session_state.kiosk_mode == "PDP":
        if st.button(L["back_home"]): st.session_state.kiosk_mode = "HOME"; st.rerun()
        st.subheader("📝 " + ("Émargement PDP" if st.session_state.lang == "FR" else "PDP Sign-off"))
        st.divider()
        soc_pdp = st.selectbox("1. Entreprise Extérieure :" if st.session_state.lang == "FR" else "1. Contractor:", db_societes)
        pdp_sel = st.selectbox("2. PDP :", db_pdps[st.session_state.lang].get(soc_pdp, ["PDP"]))
        nom_pdp = st.text_input("Nom & Prénom :" if st.session_state.lang == "FR" else "Full Name:")
        statut_pdp = st.selectbox("Rôle :" if st.session_state.lang == "FR" else "Role:", ["N1 (Compagnon)", "N2 (Responsable)"] if st.session_state.lang == "FR" else ["N1 (Worker)", "N2 (Lead)"])
        
        tel_pdp = ""
        if "N2" in statut_pdp:
            tel_pdp = st.text_input("Téléphone (Obligatoire N2) :" if st.session_state.lang == "FR" else "Phone (Mandatory N2):", placeholder="+33...")

        st.info(" [ Zone de Signature Tactile ] " if st.session_state.lang == "FR" else " [ Touch Signature Area ] ")
        if st.button("✅ " + ("VALIDER" if st.session_state.lang == "FR" else "CONFIRM"), type="primary", use_container_width=True):
            if "N2" in statut_pdp and not tel_pdp.strip():
                st.error("⚠️ Téléphone obligatoire pour le N2." if st.session_state.lang == "FR" else "⚠️ Phone required for N2.")
            else:
                st.balloons(); st.success("OK !"); st.session_state.kiosk_mode = "HOME"

    elif st.session_state.kiosk_mode == "PERMIS":
        current_step = st.session_state.step
        total_steps = len(L["steps"])
        progress_pct = int(((current_step - 1) / (total_steps - 1)) * 100)

        steps_items_html = ""
        for idx, name in enumerate(L["steps"], 1):
            if idx < current_step: steps_items_html += f'<div class="step-item step-completed"><div class="step-badge">✓</div><span>{name}</span></div>'
            elif idx == current_step: steps_items_html += f'<div class="step-item step-active"><div class="step-badge">{idx}</div><span>{name}</span></div>'
            else: steps_items_html += f'<div class="step-item step-upcoming"><div class="step-badge">{idx}</div><span>{name}</span></div>'

        st.markdown(f'<div class="stepper-container"><div class="stepper-wrapper"><div class="progress-track"><div class="progress-fill" style="width: {progress_pct}%;"></div></div>{steps_items_html}</div></div>', unsafe_allow_html=True)

        if current_step == 1:
            st.subheader(f"1. {L['steps'][0]}")
            c1, c2 = st.columns(2)
            today_date = datetime.date.today(); tomorrow_date = today_date + datetime.timedelta(days=1)
            with c1:
                if st.session_state.lang == "FR":
                    lbl_today = f"Aujourd'hui : {today_date.strftime('%d/%m/%Y')}"
                    lbl_tom = f"Demain : {tomorrow_date.strftime('%d/%m/%Y')}"
                else:
                    lbl_today = f"Today: {today_date.strftime('%d/%m/%Y')}"
                    lbl_tom = f"Tomorrow: {tomorrow_date.strftime('%d/%m/%Y')}"
                date_choice = st.radio("Date :", [lbl_today, lbl_tom])
                st.session_state.form_data["date_str"] = tomorrow_date.strftime("%d/%m/%Y") if lbl_tom in date_choice else today_date.strftime("%d/%m/%Y")
            with c2:
                lbl_soc = "Entreprise :" if st.session_state.lang == "FR" else "Company:"
                st.session_state.form_data["societe"] = st.selectbox(lbl_soc, db_societes, index=db_societes.index(get_val("societe", "ABYLSEN")) if get_val("societe") in db_societes else 0)

            c_back, c_next = st.columns(2)
            with c_back:
                if st.button(L["back_home"]): st.session_state.kiosk_mode = "HOME"; st.rerun()
            with c_next:
                if st.button(L["next"], type="primary"): st.session_state.step = 2; st.rerun()

        elif current_step == 2:
            st.subheader(f"2. {L['steps'][1]}")
            p_list = db_pdps[st.session_state.lang].get(get_val("societe"), ["PDP Standard"])
            st.session_state.form_data["pdp"] = st.selectbox("PDP :", p_list, index=p_list.index(get_val("pdp")) if get_val("pdp") in p_list else 0)
            
            m_obj_list = db_mops[st.session_state.lang].get(get_val("pdp"), [{"titre": "MoP Standard", "st": False}])
            m_titles = [m["titre"] for m in m_obj_list]
            selected_mop_title = st.selectbox("Mode Opératoire (MoP) :" if st.session_state.lang == "FR" else "Method Statement (MoP):", m_titles, index=m_titles.index(get_val("mop")) if get_val("mop") in m_titles else 0)
            st.session_state.form_data["mop"] = selected_mop_title
            
            mop_info = next((m for m in m_obj_list if m["titre"] == selected_mop_title), {"st": False})
            st.session_state.form_data["is_subcontractor"] = mop_info.get("st", False)

            if get_val("is_subcontractor"):
                st.warning(f"⚠️ {L['subcontract_alert']}")
                lbl_n2_tit = "Nom du responsable N2 de la société titulaire :" if st.session_state.lang == "FR" else "Main Contractor N2 Lead Name:"
                st.session_state.form_data["titulaire_n2"] = st.text_input(lbl_n2_tit, value=get_val("titulaire_n2", mop_info.get('titulaire', 'ABYLSEN') + " - Responsable N2"))
            else:
                st.success("✅ Entreprise titulaire directe du PDP." if st.session_state.lang == "FR" else "✅ Direct Contractor / PDP Holder.")

            c_back, c_next = st.columns(2)
            with c_back:
                if st.button(L["previous"]): st.session_state.step = 1; st.rerun()
            with c_next:
                if st.button(L["next"], type="primary"): st.session_state.step = 3; st.rerun()

        elif current_step == 3:
            st.subheader(f"3. {L['steps'][2]}")
            lbl_n2_sel = "Responsable N2 Superviseur :" if st.session_state.lang == "FR" else "N2 Lead Supervisor:"
            st.session_state.form_data["n2_nom"] = st.selectbox(lbl_n2_sel, db_n2, index=db_n2.index(get_val("n2_nom")) if get_val("n2_nom") in db_n2 else 0)
            c_back, c_next = st.columns(2)
            with c_back:
                if st.button(L["previous"]): st.session_state.step = 2; st.rerun()
            with c_next:
                if st.button(L["next"], type="primary"): st.session_state.step = 4; st.rerun()

        elif current_step == 4:
            st.subheader(f"4. {L['steps'][3]}")
            
            st.markdown(f"""
            <div class='urgence-card'>
                {L['emergencies_title']}<br>
                • <b>{L['gate']}</b> +33 3 22 54 32 00<br>
                • <b>{L['infirmary']}</b> +33 3 22 54 30 00 / +33 6 75 16 05 54<br>
                • <b>{L['fire']}</b> +33 3 22 54 33 33
            </div>
            """, unsafe_allow_html=True)

            zones_keys = list(db_zones_carto[st.session_state.lang].keys())
            st.session_state.form_data["lieu_pdp"] = st.selectbox("Zone :", zones_keys, index=zones_keys.index(get_val("lieu_pdp")) if get_val("lieu_pdp") in zones_keys else 0)
            
            lbl_prec = "Précision sur la localisation :" if st.session_state.lang == "FR" else "Location Details:"
            lbl_desc = "Description des travaux :" if st.session_state.lang == "FR" else "Task Description:"
            st.session_state.form_data["lieu_precision"] = st.text_input(lbl_prec, value=get_val("lieu_precision"))
            st.session_state.form_data["description"] = st.text_input(lbl_desc, value=get_val("description"))

            carto = db_zones_carto[st.session_state.lang].get(get_val("lieu_pdp"), {})
            msg_pr = f"📍 Points de secours : PR `{carto.get('pr')}` | Zone de Confinement `{carto.get('confinement')}`" if st.session_state.lang == "FR" else f"📍 Emergency Rescue Points: PR `{carto.get('pr')}` | Shelter Zone `{carto.get('confinement')}`"
            st.warning(msg_pr)

            c_back, c_next = st.columns(2)
            with c_back:
                if st.button(L["previous"]): st.session_state.step = 3; st.rerun()
            with c_next:
                if st.button(L["next"], type="primary"): st.session_state.step = 5; st.rerun()

        # ==============================================================================
        # ÉTAPE 5 : MÉTÉO EN DIRECT & SÉLECTION DES RISQUES / EPI
        # ==============================================================================
        elif current_step == 5:
            st.subheader(f"5. {L['steps'][4]}")

            meteo_live = obtenir_meteo_amiens_live()
            temp_max = meteo_live['temp_max_j0']
            vent = meteo_live['vent_j0']
            
            meteo_critique = (vent > 36 or temp_max < 3 or temp_max > 30)

            if meteo_critique:
                weather_class = "weather-alert"
                status_msg = f"❌ <b>ALERTE MÉTÉO : CONDITIONS DÉFAVORABLES EN EXTÉRIEUR</b><br>• Vent mesuré : <b>{vent} km/h</b> (Seuil d'arrêt : 36 km/h)<br>• Les travaux en Hauteur <u>en extérieur</u>, l'Accès Toiture et le Grutage/Levage <u>en extérieur</u> sont <b>strictement bloqués</b>.<br>• <i>Les travaux en hauteur et levages réalisés en intérieur (dans un bâtiment) restent autorisés.</i>" if st.session_state.lang == "FR" else f"❌ <b>WEATHER ALERT: UNFAVORABLE OUTDOOR CONDITIONS</b><br>• Measured wind: <b>{vent} km/h</b> (Stop limit: 36 km/h)<br>• <u>Outdoor</u> Height work, Roof Access, and <u>Outdoor</u> Crane Lifting are <b>strictly blocked</b>.<br>• <i>Indoor height works and indoor lifting inside buildings remain allowed.</i>"
            elif 30 <= vent <= 36:
                weather_class = "weather-warning"
                status_msg = f"⚠️ <b>VIGILANCE MÉTÉO RENFORCÉE</b><br>• Vent mesuré : <b>{vent} km/h</b> (Seuil de pré-alerte)<br>• Anémomètre obligatoire pour le grutage et vigilance accrue sur nacelle." if st.session_state.lang == "FR" else f"⚠️ <b>ENHANCED WEATHER VIGILANCE</b><br>• Measured wind: <b>{vent} km/h</b> (Warning limit)<br>• Anemometer required for crane lifting and high vigilance on MEWP."
            else:
                weather_class = "weather-ok"
                status_msg = "✅ <b>CONDITIONS MÉTÉOROLOGIQUES FAVORABLES</b>" if st.session_state.lang == "FR" else "✅ <b>FAVORABLE WEATHER CONDITIONS</b>"

            st.markdown(f"""
            <div class='weather-container {weather_class}'>
                <div class='weather-flex'>
                    <div class='weather-icon-large'>{meteo_live['icon_j0']}</div>
                    <div class='weather-details'>
                        <div style='font-size:1.1rem; font-weight:bold; margin-bottom:4px;'>{L['weather_title']}</div>
                        <div>
                            • <b>{L['weather_today']}</b> Temp Min <b>{meteo_live['temp_min_j0']}°C</b> / Max <b>{meteo_live['temp_max_j0']}°C</b> | 💨 {L['weather_gusts']} <b>{vent} km/h</b><br>
                            • <b>{L['weather_tomorrow']}</b> Temp Max {meteo_live['temp_max_j1']}°C | 💨 {meteo_live['vent_j1']} km/h
                        </div>
                        <div style='margin-top:8px;'>{status_msg}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            txt_r_title = "🚨 **1. RISQUES PRINCIPAUX (Déclenchent un permis spécifique) :**" if st.session_state.lang == "FR" else "🚨 **1. MAIN RISKS (Triggers Specific Permit):**"
            st.error(txt_r_title)
            
            cr1, cr2 = st.columns(2)
            with cr1:
                p_hauteur_val = get_val("p_hauteur")
                p_toiture_val = get_val("p_toiture")
                p_grutage_val = get_val("p_grutage")

                p_hauteur = st.checkbox("Travail en hauteur" if st.session_state.lang == "FR" else "Work at height", value=p_hauteur_val)
                p_toiture = st.checkbox("Accès toiture" if st.session_state.lang == "FR" else "Roof access", value=p_toiture_val)
                p_points_chauds_val = get_val("p_points_chauds")
                p_excavation = st.checkbox("Excavation, tranchée, génie civil" if st.session_state.lang == "FR" else "Trench, excavation, civil works", value=get_val("p_excavation"))
                
                p_grutage = st.checkbox("Grutage, levage" if st.session_state.lang == "FR" else "Lifting, crane", value=p_grutage_val)

                p_confine = st.checkbox("Espace confiné" if st.session_state.lang == "FR" else "Confined space", value=get_val("p_confine"))

            with cr2:
                p_electrique = st.checkbox("Travail électrique" if st.session_state.lang == "FR" else "Electrical work", value=get_val("p_electrique"))
                p_ouverture_circuit = st.checkbox("Ouverture de circuit / fluide" if st.session_state.lang == "FR" else "Line breaking", value=get_val("p_ouverture_circuit"))
                p_machines_mouvement = st.checkbox("Machines en mouvement" if st.session_state.lang == "FR" else "Moving machinery", value=get_val("p_machines_mouvement"))
                p_equipement_pression = st.checkbox("Équipement sous pression" if st.session_state.lang == "FR" else "Pressure equipment", value=get_val("p_equipement_pression"))
                p_laser_classe_iv = st.checkbox("Laser Classe IV" if st.session_state.lang == "FR" else "Class IV Laser", value=get_val("p_laser_classe_iv"))
                p_demolition = st.checkbox("Démolition" if st.session_state.lang == "FR" else "Demolition", value=get_val("p_demolition"))
                p_meuleuse = st.checkbox("Utilisation meuleuse" if st.session_state.lang == "FR" else "Angle grinder", value=get_val("p_meuleuse"))

            if p_meuleuse:
                p_points_chauds_val = True
                st.session_state.form_data["t_outils_electro"] = True

            with cr1:
                p_points_chauds = st.checkbox("Point chaud, flamme, étincelles" if st.session_state.lang == "FR" else "Hot work, sparks", value=p_points_chauds_val)

            st.session_state.form_data["p_hauteur"] = p_hauteur
            st.session_state.form_data["p_toiture"] = p_toiture
            st.session_state.form_data["p_points_chauds"] = p_points_chauds
            st.session_state.form_data["p_excavation"] = p_excavation
            st.session_state.form_data["p_grutage"] = p_grutage
            st.session_state.form_data["p_confine"] = p_confine
            st.session_state.form_data["p_electrique"] = p_electrique
            st.session_state.form_data["p_ouverture_circuit"] = p_ouverture_circuit
            st.session_state.form_data["p_machines_mouvement"] = p_machines_mouvement
            st.session_state.form_data["p_equipement_pression"] = p_equipement_pression
            st.session_state.form_data["p_laser_classe_iv"] = p_laser_classe_iv
            st.session_state.form_data["p_demolition"] = p_demolition
            st.session_state.form_data["p_meuleuse"] = p_meuleuse

            if p_ouverture_circuit or p_machines_mouvement or p_equipement_pression or p_laser_classe_iv:
                st.session_state.form_data["p_consignation"] = True

            if p_demolition:
                lbl_dta = "Consultation Dossier Technique Amiante (DTA) vérifiée" if st.session_state.lang == "FR" else "Asbestos file (DTA) consultation verified"
                st.session_state.form_data["dta_consultation"] = st.checkbox(lbl_dta, value=get_val("dta_consultation"))

            st.divider()

            st.write("##### 🛠️ 2. STA & Outillage :" if st.session_state.lang == "FR" else "##### 🛠️ 2. STA & Tools:")

            st.session_state.form_data["sta_prod_chimiques"] = st.checkbox("Utilisation de produits chimiques" if st.session_state.lang == "FR" else "Chemical products", value=get_val("sta_prod_chimiques"))
            if get_val("sta_prod_chimiques"):
                lbl_ch_nom = "Noms des produits chimiques :" if st.session_state.lang == "FR" else "Chemical names:"
                st.session_state.form_data["sta_prod_chimiques_nom"] = st.text_input(lbl_ch_nom, value=get_val("sta_prod_chimiques_nom"))
                st.session_state.form_data["p_systeme_risque"] = True

            ct1, ct2 = st.columns(2)
            with ct1:
                st.session_state.form_data["t_outils_electro"] = st.checkbox("Outils électroportatifs" if st.session_state.lang == "FR" else "Power tools", value=get_val("t_outils_electro"))
                st.session_state.form_data["t_travaux_manuels"] = st.checkbox("Travaux manuels" if st.session_state.lang == "FR" else "Manual work", value=get_val("t_travaux_manuels"))
            with ct2:
                st.session_state.form_data["t_manutention_lourde"] = st.checkbox("Manutention lourde" if st.session_state.lang == "FR" else "Heavy manual handling", value=get_val("t_manutention_lourde"))
                st.session_state.form_data["t_nettoyage_chantiers"] = st.checkbox("Nettoyage chantier" if st.session_state.lang == "FR" else "Housekeeping", value=get_val("t_nettoyage_chantiers"))

            st.divider()

            st.write("##### 🥽 3. Équipements de Protection Individuelle (EPI) :" if st.session_state.lang == "FR" else "##### 🥽 3. PPE (Personal Protective Equipment):")

            msg_epi = """
            <div class='notice-epi-card'>
                ⚠ <b>Règles de base :</b> Chaussures montantes, Casque avec jugulaire, Lunettes EN166, Gilet Haute Visibilité, Gants anti-coupure obligatoires.
            </div>
            """ if st.session_state.lang == "FR" else """
            <div class='notice-epi-card'>
                ⚠ <b>Baseline Rules:</b> High boots, Helmet with chinstrap, EN166 Safety Glasses, Hi-Viz Vest, Cut-Resistant Gloves required.
            </div>
            """
            st.markdown(msg_epi, unsafe_allow_html=True)

            auto_jugulaire = p_hauteur or p_toiture
            auto_visiere = p_points_chauds or p_meuleuse or p_laser_classe_iv
            auto_gants_elec = p_electrique
            auto_gants_coupure = p_meuleuse or p_points_chauds
            auto_resp_cartouche = p_confine or get_val("sta_prod_chimiques")

            cepi_col1, cepi_col2 = st.columns(2)

            with cepi_col1:
                st.write("**• Protection des yeux & visage :**" if st.session_state.lang == "FR" else "**• Eye & Face:**")
                st.session_state.form_data["epi_lunettes_chantier_en166"] = st.checkbox("Lunettes EN 166 (Obligatoire)" if st.session_state.lang == "FR" else "Safety Glasses EN 166 (Mandatory)", value=get_val("epi_lunettes_chantier_en166", True))
                st.session_state.form_data["epi_lunettes_etanches"] = st.checkbox("Lunettes étanches" if st.session_state.lang == "FR" else "Sealed Goggles", value=get_val("epi_lunettes_etanches"))
                st.session_state.form_data["epi_visiere_idra_en166b"] = st.checkbox("Visière IDRA EN 166B" if st.session_state.lang == "FR" else "Face Shield IDRA EN 166B", value=auto_visiere or get_val("epi_visiere_idra_en166b"))
                st.session_state.form_data["epi_lunettes_pare_visage"] = st.checkbox("Lunettes + pare-visage" if st.session_state.lang == "FR" else "Glasses + Shield", value=get_val("epi_lunettes_pare_visage"))

                st.write("**• Casques :**" if st.session_state.lang == "FR" else "**• Helmets:**")
                st.session_state.form_data["epi_casque_jugulaire"] = st.checkbox("Casque jugulaire (Obligatoire)" if st.session_state.lang == "FR" else "Helmet with Chinstrap (Mandatory)", value=auto_jugulaire or get_val("epi_casque_jugulaire", True))
                st.session_state.form_data["epi_casque_protection_auditive_en387"] = st.checkbox("Casque anti-bruit" if st.session_state.lang == "FR" else "Helmet with Hearing Protection", value=get_val("epi_casque_protection_auditive_en387"))

                st.write("**• Protection auditive :**" if st.session_state.lang == "FR" else "**• Hearing:**")
                st.session_state.form_data["epi_bouchons_oreilles"] = st.checkbox("Bouchons d'oreilles" if st.session_state.lang == "FR" else "Earplugs", value=get_val("epi_bouchons_oreilles"))

            with cepi_col2:
                st.write("**• Gants :**" if st.session_state.lang == "FR" else "**• Gloves:**")
                st.session_state.form_data["epi_gants_anticoupure_4x43d"] = st.checkbox("Gants Anti-coupure 4x43D" if st.session_state.lang == "FR" else "Cut Gloves 4x43D", value=auto_gants_coupure or get_val("epi_gants_anticoupure_4x43d", True))
                st.session_state.form_data["epi_gants_manutention_cuir"] = st.checkbox("Gants Cuir manutention" if st.session_state.lang == "FR" else "Leather Gloves", value=get_val("epi_gants_manutention_cuir"))
                st.session_state.form_data["epi_gants_chimiques_en374"] = st.checkbox("Gants Chimiques EN374" if st.session_state.lang == "FR" else "Chemical Gloves EN374", value=get_val("sta_prod_chimiques") or get_val("epi_gants_chimiques_en374"))
                st.session_state.form_data["epi_gants_elec_en60903"] = st.checkbox("Gants Électriques EN60903" if st.session_state.lang == "FR" else "Electrical Gloves EN60903", value=auto_gants_elec or get_val("epi_gants_elec_en60903"))

                st.write("**• Protection Respiratoire :**" if st.session_state.lang == "FR" else "**• Respiratory:**")
                st.session_state.form_data["epi_resp_ffp1_ffp2"] = st.checkbox("Masque FFP1 / FFP2", value=get_val("epi_resp_ffp1_ffp2"))
                st.session_state.form_data["epi_resp_3m6000"] = st.checkbox("Demi-masque 3M6000" if st.session_state.lang == "FR" else "3M6000 Half Mask", value=get_val("epi_resp_3m6000"))
                st.session_state.form_data["epi_resp_versaflo"] = st.checkbox("Système Versaflo PAPR" if st.session_state.lang == "FR" else "Versaflo PAPR System", value=get_val("epi_resp_versaflo"))
                st.session_state.form_data["epi_resp_cartouche_abek_en14387"] = st.checkbox("Cartouche ABEK EN14387", value=auto_resp_cartouche or get_val("epi_resp_cartouche_abek_en14387"))

            st.write("**• Autre :**" if st.session_state.lang == "FR" else "**• Other:**")
            st.session_state.form_data["epi_autre_texte"] = st.text_input("Autre EPI spécifique :" if st.session_state.lang == "FR" else "Other specific PPE:", value=get_val("epi_autre_texte"))

            c_back, c_next = st.columns(2)
            with c_back:
                if st.button(L["previous"]): st.session_state.step = 4; st.rerun()
            with c_next:
                if is_meteo_blocked(vent, temp_max):
                    st.error("🛑 Impossible de continuer : Conditions météo incompatibles avec les permis sélectionnés en extérieur." if st.session_state.lang == "FR" else "🛑 Cannot proceed: Weather conditions prohibit the selected outdoor permits.")
                else:
                    if st.button(L["next"], type="primary"): st.session_state.step = 6; st.rerun()

        # ==============================================================================
        # ÉTAPE 6 : PERMIS SPÉCIFIQUES (DYNAMIQUES ET SÉCURISÉS MÉTÉO)
        # ==============================================================================
        elif current_step == 6:
            st.subheader(f"6. {L['steps'][5]}")

            meteo_live = obtenir_meteo_amiens_live()
            vent = meteo_live['vent_j0']
            temp_max = meteo_live['temp_max_j0']
            meteo_critique = (vent > 36 or temp_max < 3 or temp_max > 30)

            # MEULEUSE
            if get_val("p_meuleuse"):
                with st.container(border=True):
                    titre_meuleuse = "⚙️ MEULEUSE — SPÉCIFICATIONS" if st.session_state.lang == "FR" else "⚙️ ANGLE GRINDER — SPECIFICATIONS"
                    st.markdown(f"<div class='permis-header-card'><h3 style='margin:0; color:#003366;'>{titre_meuleuse}</h3></div>", unsafe_allow_html=True)
                    c_m1, c_m2 = st.columns(2)
                    with c_m1:
                        st.session_state.form_data["meuleuse_diametre"] = st.selectbox("Diamètre du disque :" if st.session_state.lang == "FR" else "Disc Diameter:", ["125 mm", "230 mm"], index=0 if get_val("meuleuse_diametre") == "125 mm" else 1)
                        st.session_state.form_data["meuleuse_marque"] = st.text_input("Marque :" if st.session_state.lang == "FR" else "Brand:", value=get_val("meuleuse_marque"))
                    with c_m2:
                        opts_alim = ["Batterie 18V", "Filaire 230V", "Pneumatique"] if st.session_state.lang == "FR" else ["18V Battery", "Corded 230V", "Pneumatic"]
                        st.session_state.form_data["meuleuse_alim"] = st.selectbox("Alimentation :" if st.session_state.lang == "FR" else "Power:", opts_alim, index=0)
                        st.session_state.form_data["meuleuse_ref"] = st.text_input("N° de Série :" if st.session_state.lang == "FR" else "Serial Tag:", value=get_val("meuleuse_ref"))

                    st.write("##### Opérations :" if st.session_state.lang == "FR" else "##### Operations:")
                    cm_op1, cm_op2 = st.columns(2)
                    with cm_op1:
                        st.session_state.form_data["meuleuse_u_decoupe"] = st.checkbox("Découpe" if st.session_state.lang == "FR" else "Cutting", value=get_val("meuleuse_u_decoupe"))
                        if get_val("meuleuse_u_decoupe"):
                            st.session_state.form_data["meuleuse_mat_decoupe"] = st.selectbox("Matériau à découper :" if st.session_state.lang == "FR" else "Material:", db_materiaux[st.session_state.lang], index=0)
                        
                        st.session_state.form_data["meuleuse_u_ebavurage"] = st.checkbox("Ébavurage" if st.session_state.lang == "FR" else "Deburring", value=get_val("meuleuse_u_ebavurage"))
                        if get_val("meuleuse_u_ebavurage"):
                            st.session_state.form_data["meuleuse_mat_ebavurage"] = st.selectbox("Matériau ébavuré :" if st.session_state.lang == "FR" else "Material:", db_materiaux[st.session_state.lang], index=0)

                    with cm_op2:
                        st.session_state.form_data["meuleuse_u_flap"] = st.checkbox("Disque à lamelles" if st.session_state.lang == "FR" else "Flap Disc", value=get_val("meuleuse_u_flap"))
                        st.session_state.form_data["meuleuse_u_blanchiment"] = st.checkbox("Blanchiment / Décapage" if st.session_state.lang == "FR" else "Stripping", value=get_val("meuleuse_u_blanchiment"))
                        if get_val("meuleuse_u_blanchiment"):
                            st.session_state.form_data["meuleuse_disque_blanchiment"] = st.selectbox("Type de disque :" if st.session_state.lang == "FR" else "Disc type:", db_disques_blanchiment[st.session_state.lang], index=0)

            # 1. HAUTEUR
            if get_val("p_hauteur"):
                with st.container(border=True):
                    titre_hauteur = "🧗 TRAVAIL EN HAUTEUR" if st.session_state.lang == "FR" else "🧗 WORKING AT HEIGHT"
                    st.markdown(f"<div class='permis-header-card'><h3 style='margin:0; color:#b91c1c;'>{titre_hauteur}</h3></div>", unsafe_allow_html=True)
                    
                    lbl_env_h = "Zone de travail en hauteur :" if st.session_state.lang == "FR" else "Height Work Location:"
                    opts_env = ["🏢 En intérieur (Sous bâtiment)", "🌧️ En extérieur"] if st.session_state.lang == "FR" else ["🏢 Indoor (Inside building)", "🌧️ Outdoor"]
                    choice_env = st.radio(lbl_env_h, opts_env, index=1 if get_val("h_exterieur") else 0)
                    st.session_state.form_data["h_exterieur"] = ("extérieur" in choice_env or "Outdoor" in choice_env)

                    if meteo_critique:
                        if get_val("h_exterieur"):
                            st.error(f"🛑 **BLOCAGE MÉTÉO EN DIRECT :** Vent {vent} km/h > 36 km/h. Les travaux en hauteur extérieurs sont strictement interdits !" if st.session_state.lang == "FR" else f"🛑 **LIVE WEATHER BLOCK:** Wind {vent} km/h > 36 km/h. Outdoor height work is strictly prohibited!")
                        else:
                            st.warning(f"ℹ️ **ALERTE MÉTÉO EXTÉRIEURE ({vent} km/h) :** Travaux autorisés car réalisés en intérieur." if st.session_state.lang == "FR" else f"ℹ️ **OUTDOOR WEATHER ALERT ({vent} km/h):** Works allowed because executed indoors.")

                    st.info("🥽 Casque avec jugulaire obligatoire" if st.session_state.lang == "FR" else "🥽 Helmet with chinstrap required")

                    st.session_state.form_data["h_pirl"] = st.checkbox("Plateforme PIRL" if st.session_state.lang == "FR" else "PIRL Platform", value=get_val("h_pirl"))
                    if get_val("h_pirl"):
                        cp1, cp2 = st.columns(2)
                        with cp1: st.session_state.form_data["h_pirl_vgp"] = st.checkbox("Vérification VGP OK", value=get_val("h_pirl_vgp"))
                        with cp2: st.session_state.form_data["h_pirl_soc"] = st.text_input("Propriétaire PIRL :" if st.session_state.lang == "FR" else "Owner:", value=get_val("h_pirl_soc"))

                    st.session_state.form_data["h_nacelle"] = st.checkbox("Nacelle PEMP" if st.session_state.lang == "FR" else "MEWP Platform", value=get_val("h_nacelle"))
                    if get_val("h_nacelle"):
                        cn1, cn2 = st.columns(2)
                        with cn1:
                            st.session_state.form_data["h_nacelle_vgp"] = st.checkbox("VGP & Checklist OK", value=get_val("h_nacelle_vgp"))
                            st.session_state.form_data["h_nacelle_caces"] = st.checkbox("CACES OK", value=get_val("h_nacelle_caces"))
                            st.session_state.form_data["h_nacelle_aut"] = st.checkbox("Autorisation de conduite OK" if st.session_state.lang == "FR" else "Driving Authorization OK", value=get_val("h_nacelle_aut"))
                        with cn2:
                            st.session_state.form_data["h_nacelle_harnais"] = st.checkbox("Formation Harnais OK" if st.session_state.lang == "FR" else "Harness Training OK", value=get_val("h_nacelle_harnais"))
                            st.session_state.form_data["h_nacelle_soc"] = st.text_input("Société Nacelle :" if st.session_state.lang == "FR" else "MEWP Owner:", value=get_val("h_nacelle_soc"))

                    st.session_state.form_data["h_echaf"] = st.checkbox("Échafaudage" if st.session_state.lang == "FR" else "Scaffolding", value=get_val("h_echaf"))
                    if get_val("h_echaf"):
                        ce1, ce2 = st.columns(2)
                        with ce1:
                            st.session_state.form_data["h_echaf_montage"] = st.checkbox("Opération Montage-Démontage" if st.session_state.lang == "FR" else "Erection Operation", value=get_val("h_echaf_montage"))
                            st.session_state.form_data["h_echaf_ctrl_regle"] = st.checkbox("Vérification réglementaire" if st.session_state.lang == "FR" else "Regulatory Check", value=get_val("h_echaf_ctrl_regle"))
                        with ce2:
                            st.session_state.form_data["h_echaf_certif_affiche"] = st.checkbox("PV de réception affiché" if st.session_state.lang == "FR" else "Green tag displayed", value=get_val("h_echaf_certif_affiche"))
                            st.session_state.form_data["h_echaf_verif_j"] = st.checkbox("Vérification quotidienne" if st.session_state.lang == "FR" else "Daily Check", value=get_val("h_echaf_verif_j"))
                        st.session_state.form_data["h_echaf_soc_util"] = st.text_input("Société utilisateur :" if st.session_state.lang == "FR" else "Operating Company:", value=get_val("h_echaf_soc_util"))

            # 2. TOITURE
            if get_val("p_toiture"):
                with st.container(border=True):
                    titre_toiture = "🏢 ACCÈS TOITURE" if st.session_state.lang == "FR" else "🏢 ROOF ACCESS"
                    st.markdown(f"<div class='permis-header-card'><h3 style='margin:0; color:#b91c1c;'>{titre_toiture}</h3></div>", unsafe_allow_html=True)
                    
                    if meteo_critique:
                        st.error(f"🛑 **BLOCAGE MÉTÉO EN DIRECT :** Vent {vent} km/h > 36 km/h. L'accès toiture est strictly interdit !" if st.session_state.lang == "FR" else f"🛑 **LIVE WEATHER BLOCK:** Wind {vent} km/h > 36 km/h. Roof access is strictly prohibited!")

                    opts_protect = ["Garde-corps", "Ligne de vie", "Pas de protection"] if st.session_state.lang == "FR" else ["Guardrail", "Lifeline", "None"]
                    st.session_state.form_data["toiture_protection"] = st.selectbox("Protection :", opts_protect)
                    st.session_state.form_data["toiture_valideur"] = st.text_input("Valideur accès toiture :" if st.session_state.lang == "FR" else "Roof Access Approver:", value=get_val("toiture_valideur"))

            # 3. POINT CHAUD
            if get_val("p_points_chauds"):
                with st.container(border=True):
                    titre_chaud = "🔥 PERMIS POINT CHAUD" if st.session_state.lang == "FR" else "🔥 HOT WORK PERMIT"
                    st.markdown(f"<div class='permis-header-card'><h3 style='margin:0; color:#d97706;'>{titre_chaud}</h3></div>", unsafe_allow_html=True)
                    st.write("##### Extincteurs :" if st.session_state.lang == "FR" else "##### Extinguishers:")
                    opts_ext = ["Poudre", "Eau + additifs", "CO2"] if st.session_state.lang == "FR" else ["Powder", "Water + additives", "CO2"]
                    cext1, cext2 = st.columns(2)
                    with cext1: st.session_state.form_data["chaud_extincteur1"] = st.selectbox("Extincteur 1 :", opts_ext)
                    with cext2: st.session_state.form_data["chaud_extincteur2"] = st.selectbox("Extincteur 2 :", opts_ext, index=2)
                    
                    st.session_state.form_data["chaud_degage_10m"] = st.checkbox("Zone 10m dégagée" if st.session_state.lang == "FR" else "10m Cleared Area", value=get_val("chaud_degage_10m"))
                    st.session_state.form_data["chaud_traverse_mur"] = st.checkbox("Traversée de mur ou plancher" if st.session_state.lang == "FR" else "Penetrating Wall", value=get_val("chaud_traverse_mur"))
                    st.session_state.form_data["chaud_ouverture_10m"] = st.checkbox("Proximité ouverture < 10m" if st.session_state.lang == "FR" else "Opening < 10m nearby", value=get_val("chaud_ouverture_10m"))
                    
                    st.session_state.form_data["chaud_vigie_nom"] = st.text_input("Nom Vigie pendant travaux :" if st.session_state.lang == "FR" else "Fire Watch Name:", value=get_val("chaud_vigie_nom"))
                    st.session_state.form_data["chaud_personne_surv_60m"] = st.text_input("Vigie 60 min après travaux :" if st.session_state.lang == "FR" else "60 min Watch Lead:", value=get_val("chaud_personne_surv_60m"))
                    
                    chf1, chf2 = st.columns(2)
                    with chf1: st.session_state.form_data["chaud_heure_fin"] = st.text_input("Heure fin travaux :" if st.session_state.lang == "FR" else "End Time:", value=get_val("chaud_heure_fin"))
                    with chf2: st.session_state.form_data["chaud_heure_depart"] = st.text_input("Heure départ vigie :" if st.session_state.lang == "FR" else "Closeout Time:", value=get_val("chaud_heure_depart"))
                    st.session_state.form_data["chaud_commentaires"] = st.text_area("Commentaires :" if st.session_state.lang == "FR" else "Comments:", value=get_val("chaud_commentaires"))

            # 4. EXCAVATION
            if get_val("p_excavation"):
                with st.container(border=True):
                    titre_excav = "🚜 EXCAVATION & TRANCHÉE" if st.session_state.lang == "FR" else "🚜 EXCAVATION & TRENCHING"
                    st.markdown(f"<div class='permis-header-card'><h3 style='margin:0; color:#003366;'>{titre_excav}</h3></div>", unsafe_allow_html=True)
                    st.write("##### Vérification Réseaux :" if st.session_state.lang == "FR" else "##### Utility Maps Check:")
                    cx1, cx2, cx3, cx4 = st.columns(4)
                    with cx1: st.session_state.form_data["excav_plans_eaux_indus"] = st.checkbox("Eaux" if st.session_state.lang == "FR" else "Water", value=get_val("excav_plans_eaux_indus"))
                    with cx2: st.session_state.form_data["excav_plans_eaux_pluv"] = st.checkbox("Pluviales" if st.session_state.lang == "FR" else "Stormwater", value=get_val("excav_plans_eaux_pluv"))
                    with cx3: st.session_state.form_data["excav_plans_ht"] = st.checkbox("Haute Tension" if st.session_state.lang == "FR" else "HV", value=get_val("excav_plans_ht"))
                    with cx4: st.session_state.form_data["excav_plans_gaz"] = st.checkbox("Gaz" if st.session_state.lang == "FR" else "Gas", value=get_val("excav_plans_gaz"))

                    st.session_state.form_data["excav_dict"] = st.checkbox("DICT enregistrée" if st.session_state.lang == "FR" else "DICT Validated", value=get_val("excav_dict"))
                    st.session_state.form_data["excav_balisage"] = st.checkbox("Balisage rigide" if st.session_state.lang == "FR" else "Rigid Barricade", value=get_val("excav_balisage"))
                    st.session_state.form_data["excav_profondeur_130"] = st.checkbox("Profondeur > 1,30m" if st.session_state.lang == "FR" else "Depth > 1.30m", value=get_val("excav_profondeur_130"))
                    
                    st.write("##### Signatures :" if st.session_state.lang == "FR" else "##### Signatures:")
                    st.session_state.form_data["excav_chef_manoeuvre"] = st.text_input("Chef de Manœuvre :" if st.session_state.lang == "FR" else "Site Manager:", value=get_val("excav_chef_manoeuvre"))
                    st.session_state.form_data["excav_do"] = st.text_input("Donneur d'Ordre :" if st.session_state.lang == "FR" else "Project Owner:", value=get_val("excav_do"))
                    st.session_state.form_data["excav_casque_rouge"] = st.text_input("Casque Rouge P&G :" if st.session_state.lang == "FR" else "P&G Red Helmet:", value=get_val("excav_casque_rouge"))

            # 5. GRUTAGE / LEVAGE
            if get_val("p_grutage"):
                with st.container(border=True):
                    titre_grut = "🏗️ GRUTAGE & LEVAGE" if st.session_state.lang == "FR" else "🏗️ CRANE & LIFTING"
                    st.markdown(f"<div class='permis-header-card'><h3 style='margin:0; color:#003366;'>{titre_grut}</h3></div>", unsafe_allow_html=True)
                    
                    lbl_env_g = "Zone de levage :" if st.session_state.lang == "FR" else "Lifting Location:"
                    opts_env_g = ["🏢 En intérieur (Palan, Pont roulant, Levage sous bâtiment)", "🌧️ En extérieur (Grue mobile, Bras de grue)"] if st.session_state.lang == "FR" else ["🏢 Indoor (Hoist, Overhead crane, Inside building)", "🌧️ Outdoor (Mobile crane, Crane arm)"]
                    choice_env_g = st.radio(lbl_env_g, opts_env_g, index=1 if get_val("grut_exterieur") else 0)
                    st.session_state.form_data["grut_exterieur"] = ("extérieur" in choice_env_g or "Outdoor" in choice_env_g)

                    if meteo_critique:
                        if get_val("grut_exterieur"):
                            st.error(f"🛑 **BLOCAGE MÉTÉO EN DIRECT :** Vent {vent} km/h > 36 km/h. Les opérations de levage/grutage en extérieur sont strictement interdites !" if st.session_state.lang == "FR" else f"🛑 **LIVE WEATHER BLOCK:** Wind {vent} km/h > 36 km/h. Outdoor crane/lifting operations are strictly prohibited!")
                        else:
                            st.warning(f"ℹ️ **ALERTE MÉTÉO EXTÉRIEURE ({vent} km/h) :** Levage autorisé car réalisé en intérieur (sans exposition au vent)." if st.session_state.lang == "FR" else f"ℹ️ **OUTDOOR WEATHER ALERT ({vent} km/h):** Lifting allowed because executed indoors.")

                    st.session_state.form_data["grut_desc_mop"] = st.text_area("Description de la charge :" if st.session_state.lang == "FR" else "Load Description:", value=get_val("grut_desc_mop"))
                    
                    cg1, cg2 = st.columns(2)
                    with cg1: st.session_state.form_data["grut_poids_charge"] = st.number_input("Poids Charge :" if st.session_state.lang == "FR" else "Load Weight:", value=float(get_val("grut_poids_charge")))
                    with cg2: st.session_state.form_data["grut_poids_acc"] = st.number_input("Poids Accessoires :" if st.session_state.lang == "FR" else "Rigging Weight:", value=float(get_val("grut_poids_acc")))
                    
                    cmat1, cmat2, cmat3 = st.columns(3)
                    with cmat1: st.session_state.form_data["grut_immat"] = st.text_input("Immatriculation Grue / Tag :" if st.session_state.lang == "FR" else "Crane Tag:", value=get_val("grut_immat"))
                    with cmat2: st.session_state.form_data["grut_fleche"] = st.number_input("Longueur Flèche (m) :" if st.session_state.lang == "FR" else "Boom Length (m):", value=float(get_val("grut_fleche")))
                    with cmat3: st.session_state.form_data["grut_portee"] = st.number_input("Portée (m) :" if st.session_state.lang == "FR" else "Working Radius (m):", value=float(get_val("grut_portee")))

                    st.session_state.form_data["grut_anemometre"] = st.checkbox("Anémomètre OK", value=get_val("grut_anemometre"))
                    cv1, cv2 = st.columns(2)
                    with cv1: st.session_state.form_data["grut_vent_val"] = st.number_input("Vent Mesuré :" if st.session_state.lang == "FR" else "Measured Wind:", value=float(get_val("grut_vent_val")))
                    with cv2: st.session_state.form_data["grut_vent_unite"] = st.selectbox("Unité :" if st.session_state.lang == "FR" else "Unit:", ["km/h", "m/S"], index=0)

                    st.write("##### Signatures :" if st.session_state.lang == "FR" else "##### Signatures:")
                    st.session_state.form_data["grut_chef_m_nom"] = st.text_input("Chef de Manœuvre :" if st.session_state.lang == "FR" else "Lift Director:", value=get_val("grut_chef_m_nom"))
                    st.session_state.form_data["grut_do_sign"] = st.text_input("Donneur d'Ordre :" if st.session_state.lang == "FR" else "Project Owner:", value=get_val("grut_do_sign"))
                    st.session_state.form_data["grut_casque_rouge_sign"] = st.text_input("Casque Rouge :" if st.session_state.lang == "FR" else "Red Helmet:", value=get_val("grut_casque_rouge_sign"))

            # 6. ESPACE CONFINÉ
            if get_val("p_confine"):
                with st.container(border=True):
                    titre_conf = "🦺 ESPACE CONFINÉ" if st.session_state.lang == "FR" else "🦺 CONFINED SPACE"
                    st.markdown(f"<div class='permis-header-card'><h3 style='margin:0; color:#003366;'>{titre_conf}</h3></div>", unsafe_allow_html=True)
                    st.session_state.form_data["conf_lieu"] = st.text_input("Nom de la cuve / équipement :" if st.session_state.lang == "FR" else "Vessel, Tank Name:", value=get_val("conf_lieu"))
                    st.session_state.form_data["conf_catec"] = st.checkbox("Certifié CATEC OK", value=get_val("conf_catec"))
                    st.session_state.form_data["conf_m20"] = st.checkbox("Masque d'évacuation M20 OK", value=get_val("conf_m20"))
                    st.session_state.form_data["conf_ventilation_forcee"] = st.checkbox("Ventilation forcée OK" if st.session_state.lang == "FR" else "Forced Ventilation OK", value=get_val("conf_ventilation_forcee"))
                    
                    co1, co2 = st.columns(2)
                    with co1: st.session_state.form_data["conf_o2"] = st.number_input("Taux O2 (%) :", value=float(get_val("conf_o2")))
                    with co2: st.session_state.form_data["conf_temp_cuve"] = st.number_input("Température Interne (°C) :" if st.session_state.lang == "FR" else "Internal Temp (°C):", value=float(get_val("conf_temp_cuve")))

                    st.session_state.form_data["conf_entrant"] = st.text_input("Intervenant Entrant :" if st.session_state.lang == "FR" else "Entrant Name:", value=get_val("conf_entrant"))
                    st.session_state.form_data["conf_standby"] = st.text_input("Vigie Extérieure :" if st.session_state.lang == "FR" else "Hole Watch:", value=get_val("conf_standby"))

            # 7. ÉLECTRIQUE
            if get_val("p_electrique"):
                with st.container(border=True):
                    titre_elec = "⚡ TRAVAUX ÉLECTRIQUES" if st.session_state.lang == "FR" else "⚡ ELECTRICAL WORKS"
                    st.markdown(f"<div class='permis-header-card'><h3 style='margin:0; color:#b91c1c;'>{titre_elec}</h3></div>", unsafe_allow_html=True)
                    st.session_state.form_data["elec_armoire"] = st.checkbox("Intervention intérieur armoire" if st.session_state.lang == "FR" else "Inside Cabinet", value=get_val("elec_armoire"))
                    st.session_state.form_data["elec_voisinage_tension"] = st.checkbox("Voisinage sous tension" if st.session_state.lang == "FR" else "Live Parts Proximity", value=get_val("elec_voisinage_tension"))
                    st.session_state.form_data["elec_voisinage_nues"] = st.checkbox("Pièces nues sous tension" if st.session_state.lang == "FR" else "Bare Exposed Live Parts", value=get_val("elec_voisinage_nues"))
                    st.session_state.form_data["elec_valideur_ei"] = st.text_input("Valideur E&I :" if st.session_state.lang == "FR" else "E&I Testing Lead:", value=get_val("elec_valideur_ei"))

            # 8. CONSIGNATION LOTO
            if get_val("p_consignation"):
                with st.container(border=True):
                    titre_loto = "⚡ CONSIGNATION LOTO" if st.session_state.lang == "FR" else "⚡ LOTO ISOLATION"
                    st.markdown(f"<div class='permis-header-card'><h3 style='margin:0; color:#15803d;'>{titre_loto}</h3></div>", unsafe_allow_html=True)
                    opts_loto_m = ["2 vannes + drain", "2 vannes", "vanne unique", "platine"] if st.session_state.lang == "FR" else ["2 valves + drain", "2 valves", "single valve", "blind flange"]
                    st.session_state.form_data["loto_ouverture_methode"] = st.selectbox("Méthode de séparation :" if st.session_state.lang == "FR" else "Isolation Method:", opts_loto_m)
                    
                    clo1, clo2 = st.columns(2)
                    with clo1: st.session_state.form_data["loto_ouvert_loc1"] = st.text_input("Organe 1 :" if st.session_state.lang == "FR" else "Primary Point:", value=get_val("loto_ouvert_loc1"))
                    with clo2: st.session_state.form_data["loto_ouvert_loc2"] = st.text_input("Organe 2 :" if st.session_state.lang == "FR" else "Secondary Point:", value=get_val("loto_ouvert_loc2"))
                    
                    st.session_state.form_data["loto_is_elec"] = st.checkbox("Cadenas Électrique" if st.session_state.lang == "FR" else "Electrical Lockout", value=get_val("loto_is_elec"))
                    if get_val("loto_is_elec"):
                        st.session_state.form_data["loto_is_elec_loc2"] = st.text_input("N° Cadenas :" if st.session_state.lang == "FR" else "Lock ID:", value=get_val("loto_is_elec_loc2"))
                    st.session_state.form_data["loto_residu"] = st.checkbox("Purge énergie résiduelle OK" if st.session_state.lang == "FR" else "Zero Energy Check OK", value=get_val("loto_residu"))

            # 9. SYSTÈME À RISQUES / ATEX
            if get_val("p_systeme_risque"):
                with st.container(border=True):
                    titre_sr = "☣ SYSTÈMES À RISQUES / ATEX" if st.session_state.lang == "FR" else "☣ HIGH HAZARD SYSTEMS / ATEX"
                    st.markdown(f"<div class='permis-header-card'><h3 style='margin:0; color:#b91c1c;'>{titre_sr}</h3></div>", unsafe_allow_html=True)
                    st.session_state.form_data["sr_chimique_c1"] = st.checkbox("Produit Chimique Classe 1" if st.session_state.lang == "FR" else "Class 1 Chemical", value=get_val("sr_chimique_c1"))
                    if get_val("sr_chimique_c1"):
                        st.session_state.form_data["sr_chimique_nom"] = st.text_input("Nom Produit :" if st.session_state.lang == "FR" else "Chemical Name:", value=get_val("sr_chimique_nom"))
                    
                    st.session_state.form_data["sr_atex"] = st.checkbox("Zone ATEX", value=get_val("sr_atex"))
                    st.session_state.form_data["sr_balisage"] = st.checkbox("Balisage élargi" if st.session_state.lang == "FR" else "Extended Barricade", value=get_val("sr_balisage"))
                    st.session_state.form_data["sr_douche_rince"] = st.checkbox("Douche de sécurité testée" if st.session_state.lang == "FR" else "Safety Shower Tested", value=get_val("sr_douche_rince"))

                    st.session_state.form_data["sr_sign_intervenant"] = st.text_input("Opérateur :" if st.session_state.lang == "FR" else "Operator:", value=get_val("sr_sign_intervenant"))
                    st.session_state.form_data["sr_sign_do"] = st.text_input("Donneur d'Ordre :" if st.session_state.lang == "FR" else "Project Owner:", value=get_val("sr_sign_do"))
                    st.session_state.form_data["sr_sign_operations"] = st.text_input("Responsable Fabrication :" if st.session_state.lang == "FR" else "Operations Manager:", value=get_val("sr_sign_operations"))

            c_back, c_next = st.columns(2)
            with c_back:
                if st.button(L["previous"]): st.session_state.step = 5; st.rerun()
            with c_next:
                if is_meteo_blocked(vent, temp_max):
                    st.error("🛑 Impossible de valider : Vents trop fort (> 36km/h) pour les permis extérieurs sélectionnés !" if st.session_state.lang == "FR" else "🛑 Validation blocked: High wind (> 36km/h) for selected outdoor permits!")
                else:
                    if st.button(L["next"], type="primary"): st.session_state.step = 7; st.rerun()

        # ==============================================================================
        # ÉTAPE 7 : RÉCAPITULATIF DÉTAILLÉ
        # ==============================================================================
        elif current_step == 7:
            st.subheader(f"7. {L['steps'][6]}")

            meteo_live = obtenir_meteo_amiens_live()
            vent = meteo_live['vent_j0']
            temp_max = meteo_live['temp_max_j0']

            msg_pending = "⚠️ PERMIS EN ATTENTE DE VALIDATION BATCH (07h30)" if st.session_state.lang == "FR" else "⚠️ PERMIT PENDING BATCH VALIDATION (07:30 AM)"
            st.markdown(f"<div class='status-pending'>{msg_pending}</div>", unsafe_allow_html=True)

            if is_meteo_blocked(vent, temp_max):
                st.error("🛑 **ALERTE MÉTÉO CRITIQUE SUR CE PERMIS :** Les travaux en hauteur extérieurs, toiture ou grutage extérieurs sélectionnés ne pourront pas démarrer sans une baisse de vent sous 36 km/h !" if st.session_state.lang == "FR" else "🛑 **CRITICAL WEATHER ALERT:** Selected outdoor height, roof, or outdoor crane works cannot start until wind drops below 36 km/h!")

            if get_val("is_subcontractor"):
                st.warning(f"🤝 **{L['subcontract_alert']}**")

            # 1. INFORMATIONS GÉNÉRALES
            with st.container(border=True):
                tit_s1 = "### 📋 1. Informations Générales & Localisation" if st.session_state.lang == "FR" else "### 📋 1. General Information & Location"
                st.markdown(tit_s1)
                c_r1, c_r2 = st.columns(2)
                with c_r1:
                    st.write(f"• **Date :** `{get_val('date_str')}`")
                    st.write(f"• **Société :** `{get_val('societe')}`")
                    st.write(f"• **PDP :** `{get_val('pdp')}`")
                    st.write(f"• **MoP :** `{get_val('mop')}`")
                    if get_val("is_subcontractor"):
                        lbl_n2_t = "Responsable N2 Entreprise Titulaire :" if st.session_state.lang == "FR" else "Main Contractor N2 Lead:"
                        st.write(f"• **{lbl_n2_t}** `{get_val('titulaire_n2')}`")
                with c_r2:
                    lbl_n2_s = "Responsable N2 Superviseur :" if st.session_state.lang == "FR" else "N2 Supervisor:"
                    st.write(f"• **{lbl_n2_s}** `{get_val('n2_nom')}`")
                    st.write(f"• **Zone :** `{get_val('lieu_pdp')}`")
                    st.write(f"• **Précision localisation :** `{get_val('lieu_precision')}`")
                    st.write(f"• **Description :** `{get_val('description')}`")
                    st.write(f"• **Intervenants :** `{', '.join(get_val('intervenants', []))}`")

            # 2. RISQUES IDENTIFIÉS
            with st.container(border=True):
                tit_s2 = "### 🚨 2. Tableau Synthétique des Risques Identifiés" if st.session_state.lang == "FR" else "### 🚨 2. Risk Assessment Summary"
                st.markdown(tit_s2)
                
                tableau_data = []
                is_fr = (st.session_state.lang == "FR")

                if get_val("p_hauteur"):
                    env_lbl = " (Extérieur)" if get_val("h_exterieur") else " (Intérieur)"
                    tableau_data.append({"Activité": ("Hauteur" if is_fr else "Height") + env_lbl, "Risque": "Chute de hauteur" if is_fr else "Fall", "Prévention": "Casque jugulaire + VGP nacelle/pirl OK"})
                if get_val("p_toiture"):
                    tableau_data.append({"Activité": "Toiture" if is_fr else "Roof", "Risque": "Chute à travers toit" if is_fr else "Fall", "Prévention": f"{get_val('toiture_protection')} + Valideur {get_val('toiture_valideur')}"})
                if get_val("p_points_chauds"):
                    tableau_data.append({"Activité": "Point Chaud" if is_fr else "Hot Work", "Risque": "Incendie / Brûlure" if is_fr else "Fire", "Prévention": f"Visière EN166B + Extincteurs + Vigie {get_val('chaud_vigie_nom')}"})
                if get_val("p_meuleuse"):
                    tableau_data.append({"Activité": "Meuleuse" if is_fr else "Grinder", "Risque": "Projection / Coupure" if is_fr else "Sparks / Cuts", "Prévention": f"Disque {get_val('meuleuse_diametre')} + Écran facial IDRA"})
                if get_val("p_excavation"):
                    tableau_data.append({"Activité": "Excavation", "Risque": "Réseaux / Effondrement" if is_fr else "Utilities", "Prévention": "Plans réseaux OK + DICT + 3 Signatures"})
                if get_val("p_grutage"):
                    env_g_lbl = " (Extérieur)" if get_val("grut_exterieur") else " (Intérieur)"
                    tableau_data.append({"Activité": ("Grutage/Levage" if is_fr else "Lifting") + env_g_lbl, "Risque": "Chute de charge" if is_fr else "Dropped load", "Prévention": f"Poids total {float(get_val('grut_poids_charge',0))+float(get_val('grut_poids_acc',0))} {get_val('grut_unite')} + Anémomètre OK"})
                if get_val("p_confine"):
                    tableau_data.append({"Activité": "Espace Confiné" if is_fr else "Confined Space", "Risque": "Asphyxie / Gaz" if is_fr else "Gas", "Prévention": f"Masque M20 + O2 ({get_val('conf_o2')}%) + Vigie extérieure"})
                if get_val("p_electrique"):
                    tableau_data.append({"Activité": "Électrique" if is_fr else "Electrical", "Risque": "Arc électrique" if is_fr else "Arc Flash", "Prévention": "Gants isolants + Visière + Valideur E&I"})
                if get_val("p_consignation"):
                    tableau_data.append({"Activité": "Consignation LOTO" if is_fr else "LOTO Isolation", "Risque": "Énergie résiduelle" if is_fr else "Residual energy", "Prévention": f"Séparation {get_val('loto_ouverture_methode')} + Purge vérifiée"})
                if get_val("p_systeme_risque"):
                    tableau_data.append({"Activité": "Système à risques / ATEX", "Risque": "Chimique / Explosion" if is_fr else "Chemical", "Prévention": "Balisage élargi + Douche testée + Signatures"})

                if not tableau_data:
                    tableau_data.append({"Activité": "Permis Général", "Risque": "Risques standards PDP", "Prévention": "EPI de base du site"})

                st.table(tableau_data)

            # 3. EPIS RETENUS
            with st.container(border=True):
                tit_s3 = "### 🥽 3. Équipements de Protection Individuelle Retenus" if st.session_state.lang == "FR" else "### 🥽 3. Selected Personal Protective Equipment"
                st.markdown(tit_s3)
                epis_list = []
                if get_val("epi_lunettes_chantier_en166"): epis_list.append("Lunettes EN166" if is_fr else "Glasses EN166")
                if get_val("epi_visiere_idra_en166b"): epis_list.append("Visière IDRA EN166B" if is_fr else "Face Shield EN166B")
                if get_val("epi_casque_jugulaire"): epis_list.append("Casque Jugulaire" if is_fr else "Chinstrap Helmet")
                if get_val("epi_gants_anticoupure_4x43d"): epis_list.append("Gants Anti-coupure 4x43D" if is_fr else "Cut Gloves 4x43D")
                if get_val("epi_gants_chimiques_en374"): epis_list.append("Gants Chimiques EN374" if is_fr else "Chemical Gloves EN374")
                if get_val("epi_gants_elec_en60903"): epis_list.append("Gants Électriques EN60903" if is_fr else "Electrical Gloves EN60903")
                if get_val("epi_resp_cartouche_abek_en14387"): epis_list.append("Masque Cartouche ABEK" if is_fr else "ABEK Respirator")
                if get_val("epi_autre_texte"): epis_list.append(f"Autre: {get_val('epi_autre_texte')}")
                
                st.write(", ".join([f"`{e}`" for e in epis_list]))

            # 4. PERMIS SPÉCIFIQUES HRT
            with st.container(border=True):
                tit_s4 = "### ⚙ 4. Détails Techniques des Permis Spécifiques" if st.session_state.lang == "FR" else "### ⚙ 4. Specific Permits Technical Details"
                st.markdown(tit_s4)
                
                if get_val("p_meuleuse"):
                    st.write(f"• **Meuleuse :** Disque `{get_val('meuleuse_diametre')}` | Modèle `{get_val('meuleuse_marque')}` | Alim `{get_val('meuleuse_alim')}` | Tag `{get_val('meuleuse_ref')}`")
                
                if get_val("p_hauteur"):
                    env_str = "Extérieur" if get_val("h_exterieur") else "Intérieur (Sous bâtiment)"
                    if not is_fr: env_str = "Outdoor" if get_val("h_exterieur") else "Indoor (Inside building)"
                    st.write(f"• **Hauteur :** Lieu `{env_str}` | PIRL (`{get_val('h_pirl')}`) | Nacelle (`{get_val('h_nacelle')}`) | Échafaudage (`{get_val('h_echaf')}`)")
                
                if get_val("p_toiture"):
                    st.write(f"• **Toiture :** Protection `{get_val('toiture_protection')}` | Valideur `{get_val('toiture_valideur')}`")
                
                if get_val("p_points_chauds"):
                    st.write(f"• **Point Chaud :** Extincteurs `{get_val('chaud_extincteur1')}` & `{get_val('chaud_extincteur2')}` | Vigie `{get_val('chaud_vigie_nom')}` | Fin surveillance `{get_val('chaud_heure_depart')}`")
                
                if get_val("p_excavation"):
                    st.write(f"• **Excavation :** Plans Réseaux Vérifiés | DICT (`{get_val('excav_dict')}`) | Signatures: Chef `{get_val('excav_chef_manoeuvre')}`, DO `{get_val('excav_do')}`, Casque Rouge `{get_val('excav_casque_rouge')}`")
                
                if get_val("p_grutage"):
                    env_g_str = "Extérieur (Grue/Bras)" if get_val("grut_exterieur") else "Intérieur (Palan/Pont roulant)"
                    if not is_fr: env_g_str = "Outdoor (Crane)" if get_val("grut_exterieur") else "Indoor (Hoist/Crane)"
                    poids_t = float(get_val('grut_poids_charge', 0)) + float(get_val('grut_poids_acc', 0))
                    st.write(f"• **Grutage :** Zone `{env_g_str}` | Poids Total `{poids_t} {get_val('grut_unite')}` | Immatriculation/Tag `{get_val('grut_immat')}` | Anémomètre (`{get_val('grut_anemometre')}`) | Vent `{get_val('grut_vent_val')} {get_val('grut_vent_unite')}`")
                
                if get_val("p_confine"):
                    st.write(f"• **Espace Confiné :** Équipement `{get_val('conf_lieu')}` | Taux O2 `{get_val('conf_o2')}%` | Vigie `{get_val('conf_standby')}` | Entrant `{get_val('conf_entrant')}`")
                
                if get_val("p_electrique"):
                    st.write(f"• **Électrique :** Intérieur Armoire (`{get_val('elec_armoire')}`) | Voisinage pièces nues (`{get_val('elec_voisinage_nues')}`) | Valideur E&I `{get_val('elec_valideur_ei')}`")
                
                if get_val("p_consignation"):
                    st.write(f"• **Consignation LOTO :** Méthode `{get_val('loto_ouverture_methode')}` | Organe 1 `{get_val('loto_ouvert_loc1')}` | Cadenas `{get_val('loto_is_elec_loc2')}`")
                
                if get_val("p_systeme_risque"):
                    st.write(f"• **Systèmes à Risques / ATEX :** Balisage élargi (`{get_val('sr_balisage')}`) | Douche testée (`{get_val('sr_douche_rince')}`) | Signatures: Opérateur `{get_val('sr_sign_intervenant')}`, DO `{get_val('sr_sign_do')}`, Fab `{get_val('sr_sign_operations')}`")

            # Enregistrement de l'objet final
            permis_final = {
                "id": f"PT-2026-EXACT-0{len(st.session_state.permis_db)+1}",
                "date_travaux": get_val("date_str"),
                "societe": get_val("societe"),
                "pdp": get_val("pdp"),
                "mop": get_val("mop"),
                "is_subcontractor": get_val("is_subcontractor"),
                "titulaire_n2": get_val("titulaire_n2"),
                "n2": get_val("n2_nom"),
                "zone": get_val("lieu_pdp"),
                "emplacement": get_val("lieu_precision"),
                "description": get_val("description"),
                "statut": "PENDING_BATCH",
                "heure": datetime.datetime.now().strftime("%H:%M"),
                "intervenants": list(get_val("intervenants", [])),
                "tableau_risques": tableau_data,
                "epis_cochis": epis_list
            }

            pdf_bytes = generer_pdf_bytes(permis_final)

            c_back, c_sub, c_pdf = st.columns([1, 2, 2])
            with c_back:
                if st.button(L["previous"]): st.session_state.step = 6; st.rerun()

            with c_pdf:
                st.download_button(L["download_pdf"], data=pdf_bytes, file_name=f"Permis_{permis_final['id']}.pdf", mime="application/pdf", use_container_width=True)

            with c_sub:
                if is_meteo_blocked(vent, temp_max):
                    st.error("🛑 Soumission bloquée : Rafales > 36km/h incompatibles avec les permis extérieurs retenus." if st.session_state.lang == "FR" else "🛑 Submission blocked: Wind gusts > 36km/h incompatible with selected outdoor permits.")
                else:
                    if st.button(L["submit_batch"], type="primary", use_container_width=True):
                        st.session_state.permis_db.append(permis_final)
                        st.balloons(); st.success(f"Permis {permis_final['id']} soumis au batch !"); st.session_state.kiosk_mode = "HOME"

# ==============================================================================
# INTERFACE 2 : DDS BOARD
# ==============================================================================
elif "DDS Board" in role:
    st.markdown("<div class='pg-header' style='background: #0f172a;'><h2>DDS BOARD — VALIDATION DES BATCHS</h2></div>", unsafe_allow_html=True)
    if st.button("✅ VALIDER LE BATCH DE 07H30", type="primary"):
        for p in st.session_state.permis_db: p["statut"] = "VALIDATED"
        st.success("Batch validé !")

    for p in st.session_state.permis_db:
        with st.expander(f"Permis {p['id']} - {p['societe']} ({p['statut']})"):
            st.write(f"**Zone :** {p['zone']} | **N2 :** {p['n2']}")
            st.table(p.get("tableau_risques", []))
            pdf_valid_bytes = generer_pdf_bytes(p)
            st.download_button("📄 Télécharger PDF", data=pdf_valid_bytes, file_name=f"Permis_{p['id']}.pdf", mime="application/pdf", key=f"btn_{p['id']}")

# ==============================================================================
# INTERFACE 3 : FIELD INSPECTION
# ==============================================================================
else:
    st.markdown("<div class='pg-header' style='background: #b91c1c;'><h2>INSPECTION TERRAIN ET QR CODE</h2></div>", unsafe_allow_html=True)
    if st.session_state.permis_db:
        pt_sel = st.selectbox("Sélectionner le permis scanné :", [p["id"] for p in st.session_state.permis_db])
        p = next(p for p in st.session_state.permis_db if p["id"] == pt_sel)
        
        st.write(f"### Réf Permis : {p['id']} ({p['statut']})")
        st.write(f"**Société :** {p['societe']} | **PDP :** {p['pdp']}")
        st.table(p.get("tableau_risques", []))
        
        if st.button("✍️ Valider Ronde Point Chaud (60 min)"):
            st.success("Ronde validée par le Casque Rouge.")
    else:
        st.info("Aucun permis enregistré pour le moment.")
