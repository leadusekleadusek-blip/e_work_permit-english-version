import datetime
import json
import urllib.request
import streamlit as st
import unicodedata
from fpdf import FPDF

# ---------------------------------------------------------
# STREAMLIT PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="P&G Amiens — e-Work Permit System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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
# STATE INITIALIZATIONS & LANGUAGE MANAGEMENT
# ---------------------------------------------------------
if "lang" not in st.session_state:
    st.session_state.lang = "FR"

if "permis_db" not in st.session_state:
    st.session_state.permis_db = []

if "kiosk_mode" not in st.session_state:
    st.session_state.kiosk_mode = "HOME"

if "step" not in st.session_state:
    st.session_state.step = 1

# --- DICTIONNAIRE TRADUCTIONS ---
TR = {
    "FR": {
        "title": "PROCTER & GAMBLE — AMIENS",
        "subtitle": "WORK PERMIT IT | BORNE TACTILE KIOSK",
        "home_select": "Veuillez sélectionner votre démarche :",
        "btn_work_permit": "🚀 PERMIS DE TRAVAIL",
        "desc_work_permit": "Émettre un nouveau Permis de Travail complet.",
        "btn_start_permit": "🚀 COMMENCER UN PERMIS DE TRAVAIL",
        "btn_pdp": "📝 ÉMARGEMENT PDP",
        "desc_pdp": "Émarger un Plan de Prévention.",
        "btn_start_pdp": "📝 SIGNER UN PLAN DE PRÉVENTION (PDP)",
        "lang_title": "🌐 Langue / Language :",
        "steps": ["Date & EE", "PDP & MoP", "Responsable N2", "Zone & Urgences", "Check-list & EPIs", "Permis Spécifiques (HRT)", "Synthèse & Signatures"],
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
        "subcontract_alert": "🤝 Gestion de la sous-traitance : L'entreprise sélectionnée étant en sous-traitance, le N2 de la société principale doit également valider le permis.",
    },
    "EN": {
        "title": "PROCTER & GAMBLE — AMIENS",
        "subtitle": "WORK PERMIT IT | TOUCH KIOSK TERMINAL",
        "home_select": "Please select your workflow:",
        "btn_work_permit": "🚀 WORK PERMIT",
        "desc_work_permit": "Issue a complete new Work Permit.",
        "btn_start_permit": "🚀 START A WORK PERMIT",
        "btn_pdp": "📝 PDP SIGN-OFF",
        "desc_pdp": "Sign off a Prevention Plan.",
        "btn_start_pdp": "📝 SIGN A PREVENTION PLAN (PDP)",
        "lang_title": "🌐 Language / Langue :",
        "steps": ["Date & Contractor", "PDP & MoP", "N2 Lead", "Location & Emergencies", "Checklist & PPE", "Specific Permits (HRT)", "Summary & Signatures"],
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
        "gate": "Guard House :",
        "infirmary": "Medical Center:",
        "fire": "Fire / Environment Response:",
        "subcontract_alert": "🤝 Subcontracting Rule: Since the selected company is a subcontractor, the main contractor's N2 supervisor must also approve and sign the permit.",
    }
}

L = TR[st.session_state.lang]

# ---------------------------------------------------------
# LIVE WEATHER — AMIENS NORTH INDUSTRIAL ZONE
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
        return {"temp_max_j0": 18, "temp_min_j0": 8, "vent_j0": 14, "code_w_j0": 0, "icon_j0": "☀️", "temp_max_j1": 19, "vent_j1": 12, "source": "Backup Mode (ZI Amiens Nord)"}

# ---------------------------------------------------------
# REFERENTIALS & P&G DATABASE
# ---------------------------------------------------------
db_societes = ["ABYLSEN", "APAVE", "AXIMA", "ENGIE", "EULER", "SOUS-TRAITANCE-EXPERT"]

db_pdps = {
    "ABYLSEN": ["PDP-2026-042 (Bâtiment M1 / Building M1)"],
    "APAVE": ["PDP-2026-104 (Inspection Pression / Pressure Test)"],
    "AXIMA": ["PDP-2026-015 (HVAC Zone Production M1)"],
    "ENGIE": ["PDP-2026-067 (Chaufferie Vapeur / Boiler House)"],
    "EULER": ["PDP-2026-090 (Génie Civil / Earthworks)"],
    "SOUS-TRAITANCE-EXPERT": ["PDP-2026-042 (Sous-traitant / Subcontractor ABYLSEN)"]
}

db_mops = {
    "PDP-2026-042 (Bâtiment M1 / Building M1)": [{"titre": "MoP-01: Peinture & Finitions / Painting", "st": False}],
    "PDP-2026-042 (Sous-traitant / Subcontractor ABYLSEN)": [{"titre": "MoP-02-ST: Électromécanique / Electromechanics", "st": True, "titulaire": "ABYLSEN"}],
    "PDP-2026-104 (Inspection Pression / Pressure Test)": [{"titre": "MoP-01: Épreuve Hydraulique / Pressure Check", "st": False}],
    "PDP-2026-015 (HVAC Zone Production M1)": [{"titre": "MoP-01: Nettoyage Filtres CTA / Air Filters", "st": False}],
    "PDP-2026-067 (Chaufferie Vapeur / Boiler House)": [{"titre": "MoP-01: Isoler Purgeur Vapeur / Steam Trap", "st": False}],
    "PDP-2026-090 (Génie Civil / Earthworks)": [{"titre": "MoP-01: Fouille Terrassement / Trenching", "st": False}]
}

db_n2 = ["Léa DUSEK", "Matthieu MARTIN", "Alexandre LEFEBVRE", "Cindy BERNARD"]

db_zones_carto = {
    "Bâtiment M1 - Zone Production / Building M1 Production": {"pr": "PR-2 (Parking Ouest / West)", "confinement": "ZC-01 (Hall M1)", "sprinkler": True, "detection": True},
    "Bâtiment M1 - Bureaux / Toiture / M1 Roof": {"pr": "PR-2 (Parking Ouest / West)", "confinement": "ZC-01 (Hall M1)", "sprinkler": False, "detection": True},
    "Bâtiment M2 - Conditionnement / M2 Packaging": {"pr": "PR-4 (Zone Nord / North)", "confinement": "ZC-03 (Atrium M2)", "sprinkler": True, "detection": True},
    "Zone Extérieure / Logistique / Outdoor": {"pr": "PR-1 (Entrée Principale / Gate)", "confinement": "ZC-00 (Control Room)", "sprinkler": False, "detection": False}
}

db_materiaux = ["Acier / Carbon Steel", "Inox 316L / Stainless Steel", "Aluminium", "Béton / Concrete", "PVC / Plastic"]
db_disques_blanchiment = ["Disque fibre abrasif / Fiber Disc", "Brosse métallique / Wire Brush", "Clean & Strip"]

# EXHAUSTIVE INITIALIZATION OF FORM_DATA
VALEURS_PAR_DEFAUT = {
    "date_str": datetime.date.today().strftime("%d/%m/%Y"),
    "societe": "ABYLSEN",
    "pdp": "PDP-2026-042 (Bâtiment M1 / Building M1)",
    "mop": "MoP-01: Peinture & Finitions / Painting",
    "is_subcontractor": False,
    "titulaire_n2": "",
    "n2_nom": "Léa DUSEK",
    "lieu_pdp": "Bâtiment M1 - Bureaux / Toiture / M1 Roof",
    "lieu_precision": "1er étage, Bureau 104 / 1st Floor, Room 104",
    "description": "Maintenance et travaux sur site / Site maintenance work",
    "intervenants": ["Léa DUSEK", "Matthieu MARTIN"],
    
    # 1. RISQUES PRINCIPAUX
    "p_hauteur": False,
    "p_toiture": False,
    "p_points_chauds": False,
    "p_excavation": False,
    "p_grutage": False,
    "p_confine": False,
    "p_electrique": False,
    "p_ouverture_circuit": False,
    "p_machines_mouvement": False,
    "p_equipement_pression": False,
    "p_laser_classe_iv": False,
    "p_demolition": False,
    "p_meuleuse": False,
    "dta_consultation": False,
    "p_consignation": False,
    "p_systeme_risque": False,

    # 2. STA (SAFETY TASK ASSIGNMENT)
    "sta_prod_chimiques": False,
    "sta_prod_chimiques_nom": "",
    "t_outils_electro": False,
    "t_travaux_manuels": True,
    "t_manutention_lourde": False,
    "t_nettoyage_chantiers": True,

    # MEULEUSE
    "meuleuse_diametre": "125 mm", "meuleuse_operateurs": ["Léa DUSEK"], "meuleuse_marque": "Bosch Pro", "meuleuse_alim": "Batterie 18V / 18V Battery", "meuleuse_ref": "MEU-042", "meuleuse_vitesse": "11000",
    "meu_env_plain_pied": True, "meu_env_hauteur": False, "meu_env_confine": False, "meu_env_excavation": False, "meu_env_stable": True, "meu_env_maintien_2mains": True, "meu_env_piece_fixee": True, "meu_env_hors_ligne_tir": True, "meu_position_op": "Debout / Standing",
    "meuleuse_u_decoupe": False, "meuleuse_mat_decoupe": db_materiaux[0], "meuleuse_u_ebavurage": False, "meuleuse_mat_ebavurage": db_materiaux[0], "meuleuse_u_flap": False, "meuleuse_u_blanchiment": False, "meuleuse_disque_blanchiment": db_disques_blanchiment[0],

    # EPIS
    "epi_lunettes_chantier_en166": True,
    "epi_lunettes_etanches": False,
    "epi_visiere_idra_en166b": False,
    "epi_lunettes_pare_visage": False,
    "epi_casque_jugulaire": True,
    "epi_casque_protection_auditive_en387": False,
    "epi_gants_anticoupure_4x43d": True,
    "epi_gants_manutention_cuir": True,
    "epi_gants_chimiques_en374": False,
    "epi_gants_elec_en60903": False,
    "epi_bouchons_oreilles": False,
    "epi_resp_ffp1_ffp2": False,
    "epi_resp_3m6000": False,
    "epi_resp_versaflo": False,
    "epi_resp_cartouche_abek_en14387": False,
    "epi_autre_texte": "",

    # PERMIS SPÉCIFIQUES COMPLETS
    "h_pirl": False, "h_pirl_vgp": True, "h_pirl_soc": "ABYLSEN",
    "h_nacelle": False, "h_nacelle_vgp": True, "h_nacelle_checklist": True, "h_nacelle_caces": True, "h_nacelle_aut": True, "h_nacelle_harnais": True, "h_nacelle_soc": "ABYLSEN",
    "h_echaf": False, "h_echaf_montage": False, "h_echaf_montage_qualif": True, "h_echaf_montage_harnais": True, "h_echaf_util": False, "h_echaf_util_qualif": True, "h_echaf_ctrl_regle": True, "h_echaf_certif_affiche": True, "h_echaf_verif_j": True, "h_echaf_soc_util": "ABYLSEN",
    "toiture_protection": "Garde-corps / Guardrail", "toiture_valideur": "Matthieu MARTIN",
    "chaud_gants_soudeur": False, "chaud_gants_chaleur": False, "chaud_gants_anticoupure": True, "chaud_extincteur1": "Eau + additifs / Water", "chaud_extincteur2": "CO2", "chaud_degage_10m": True, "chaud_baches": False, "chaud_traverse_mur": False, "chaud_vigie_opposee": False, "chaud_ouverture_10m": False, "chaud_obstruction": False, "chaud_vigie_autre_cote": False, "chaud_vigie_nom": "Matthieu MARTIN", "chaud_personne_surv_60m": "Léa DUSEK", "chaud_heure_fin": "15:00", "chaud_heure_depart": "16:00", "chaud_commentaires": "",
    "excav_plans_eaux_indus": True, "excav_plans_eaux_usees": True, "excav_plans_eaux_pluv": True, "excav_plans_eaux_incendie": True, "excav_plans_ht": True, "excav_plans_bt": True, "excav_plans_gaz": True, "excav_struct_proximite": False, "excav_architecte": False, "excav_dict": True, "excav_effondrement": False, "excav_eau_pompe": False, "excav_balisage": True, "excav_vehicule_3m": True, "excav_deblais": True, "excav_acces": "Escalier / Ramp", "excav_profondeur_130": False, "excav_blindage": False, "excav_schema_commentaires": "", "excav_chef_manoeuvre": "Léa DUSEK", "excav_do": "Matthieu MARTIN", "excav_casque_rouge": "Alexandre LEFEBVRE",
    "grut_desc_mop": "Levage rooftop chiller", "grut_poids_charge": 2500.0, "grut_poids_acc": 200.0, "grut_unite": "kg", "grut_immat": "CRANE-AMIENS-88", "grut_fleche": 35.0, "grut_portee": 20.0, "grut_pression_patin": "12 T/m²", "grut_rayon": 15.0, "grut_balisage": True, "grut_plan_vue": True, "grut_plan_elev": True, "grut_obstacles": True, "grut_anemometre": True, "grut_vent_val": 18.0, "grut_vent_unite": "km/h", "grut_pesage": True, "grut_centre_gravite": True, "grut_angles_elingue": True, "grut_plaques_rep": True, "grut_chef_m_nom": "Léa DUSEK", "grut_chef_m_soc": "ABYLSEN", "grut_elingueur_nom": "Matthieu MARTIN", "grut_elingueur_soc": "ABYLSEN", "grut_grutier_nom": "Jean LEVAGE", "grut_grutier_soc": "APAVE", "grut_certif_grue": True, "grut_certif_acc": True, "grut_certif_plaques": True, "grut_check_j_grue": True, "grut_check_j_acc": True, "grut_pattes_concu": True, "grut_pattes_defaut": False, "grut_pattes_adequation": True, "grut_charges_annexes": True, "grut_schema_commentaires": "", "grut_do_sign": "Matthieu MARTIN", "grut_casque_rouge_sign": "Alexandre LEFEBVRE",
    "conf_lieu": "Cuve C-102 / Tank C-102", "conf_r_atmo": True, "conf_r_chimique": False, "conf_r_inflam": False, "conf_r_orga": False, "conf_r_meca": False, "conf_r_thermiq": False, "conf_r_bruit": False, "conf_troudhomme_610": True, "conf_catec": True, "conf_hauteur": False, "conf_m20": True, "conf_secouriste": "Attribution automatique / Auto", "conf_medical": "Attribution automatique / Auto", "conf_action_chaud": False, "conf_ventilation_nat": True, "conf_ventilation_forcee": True, "conf_ventilation_debit": "Min 56m3/h par personne", "conf_consignation_gaz": True, "conf_cuve_vide": True, "conf_vol_caches": False, "conf_eclairage_24v": True, "conf_blocage_ouvert": True, "conf_echaf_echelle": False, "conf_prod_chim": False, "conf_laser": False, "conf_comm_type": "Talkie Walkie", "conf_o2": 20.9, "conf_o2_contre_mesure": 20.9, "conf_h2s_check": False, "conf_h2s": 0.0, "conf_co_check": False, "conf_co": 0.0, "conf_explo_check": False, "conf_explo": 0.0, "conf_temp_cuve": 22.0, "conf_verif_temp": "N2", "conf_inflam_lel": 0.0, "conf_verif_lel": "N2", "conf_schema_commentaires": "", "conf_entrant": "Léa DUSEK", "conf_standby": "Matthieu MARTIN", "conf_do": "Alexandre LEFEBVRE",
    "elec_modife": False, "elec_armoire": True, "elec_voisinage_tension": True, "elec_courant_faible": False, "elec_releve": True, "elec_chemins": False, "elec_voisinage_nues": False, "elec_valideur_ei": "E&I / PT E&I (B2, H2, BC, HC)",
    "loto_ouverture_methode": "2 vannes / 2 valves + drain", "loto_ouvert_loc1": "Vanne V-101 amont", "loto_ouvert_loc2": "Vanne V-102 aval", "loto_is_elec": True, "loto_is_elec_loc1": "TGBT-M1-Armoire 4", "loto_is_elec_loc2": "Lock #884", "loto_fusible": False, "loto_fusible_loc1": "", "loto_fusible_loc2": "", "loto_cable": False, "loto_cable_loc1": "", "loto_cable_loc2": "", "loto_pneu": False, "loto_pneu_loc1": "", "loto_pneu_loc2": "", "loto_hydra": False, "loto_hydra_loc1": "", "loto_hydra_loc2": "", "loto_residu": True, "loto_residu_loc1": "Purge pression", "loto_residu_loc2": "Manomètre à 0 bar", "loto_drain_ouvert": True, "loto_eq_ouvert": True, "loto_eq_lave": True, "loto_eq_sanitise": True,
    "sr_chimique_c1": False, "sr_chimique_nom": "", "sr_fluide_dang": False, "sr_fluide_nom": "", "sr_atex": False, "sr_atex_nom": "", "sr_balisage": True, "sr_douche_rince": True, "sr_ramonage": False, "sr_ramonage_dt": "01/10/2026 08:00", "sr_isolement": True, "sr_feuille_loto": True, "sr_zonage_atex": True, "sr_epi_ecran": True, "sr_epi_lunettes": False, "sr_epi_gants_chim": True, "sr_epi_comb1": False, "sr_epi_comb2": True, "sr_epi_bottes": True, "sr_epi_cartouche": True, "sr_epi_ari": False, "sr_epi_3m6000": False, "sr_epi_versaflo": False, "sr_epi_no_versaflo": True, "sr_auxiliaire_equipe": True, "sr_comm_moyen": "ATEX Walkie-Talkie", "sr_inspect_remise": True, "sr_inspect_nom": "Léa DUSEK", "sr_inspect_dt": "01/10/2026 17:00", "sr_schema_commentaires": "", "sr_sign_intervenant": "Léa DUSEK", "sr_sign_do": "Matthieu MARTIN", "sr_sign_operations": "Alexandre LEFEBVRE"
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
    text = text.replace("🔥", "[Hot Work]").replace("🦺", "[Confined]").replace("🧗", "[Height]").replace("⚡", "[LOTO]").replace("⚠️", "[!]").replace("✅", "[OK]").replace("🚜", "[Excavation]")
    normalized = unicodedata.normalize('NFKD', text)
    cleaned = ''.join(c for c in normalized if not unicodedata.combining(c))
    return cleaned.encode('latin-1', 'ignore').decode('latin-1')

def generer_pdf_bytes(permis):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Header
    pdf.set_fill_color(0, 51, 102)
    pdf.rect(10, 10, 190, 22, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 14)
    pdf.text(15, 20, sanitize_text("PROCTER & GAMBLE AMIENS - e-Work Permit System"))
    pdf.set_font("Helvetica", "", 10)
    pdf.text(15, 27, sanitize_text(f"Ref: {permis['id']} | Date: {permis['date_travaux']} | Time: {permis['heure']}"))
    pdf.set_y(38)

    # Status Banner
    if permis.get('statut') == 'VALIDÉ':
        pdf.set_fill_color(220, 252, 231); pdf.set_draw_color(34, 197, 94); pdf.set_text_color(22, 101, 52)
        status_str = "PERMIT VALIDATED & AUDITABLE ON ePDP ACCOUNT"
    else:
        pdf.set_fill_color(254, 240, 138); pdf.set_draw_color(234, 179, 8); pdf.set_text_color(133, 77, 14)
        status_str = "PERMIT PENDING BATCH VALIDATION (07:30 AM)"

    pdf.rect(10, 38, 190, 10, 'DF')
    pdf.set_font("Helvetica", "B", 11)
    pdf.text(15, 44.5, sanitize_text(status_str))
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(52)

    # Section 1 : General Info & Location
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(190, 6, sanitize_text("1. GENERAL INFORMATION & LOCATION"), 1, 1, 'L', True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(95, 5, sanitize_text(f"Company: {permis['societe']}"), 0, 0)
    pdf.cell(95, 5, sanitize_text(f"N2 Manager: {permis['n2']}"), 0, 1)
    pdf.cell(190, 5, sanitize_text(f"PDP: {permis['pdp']}"), 0, 1)
    pdf.cell(190, 5, sanitize_text(f"MoP: {permis['mop']}"), 0, 1)
    if permis.get("is_subcontractor"):
        pdf.cell(190, 5, sanitize_text(f"[SUBCONTRACTING] Main Contractor N2 Approver: {permis.get('titulaire_n2')}"), 0, 1)
    pdf.cell(190, 5, sanitize_text(f"Zone: {permis['zone']} ({permis.get('emplacement', '')})"), 0, 1)
    pdf.cell(190, 5, sanitize_text(f"Description: {permis.get('description', '')}"), 0, 1)
    
    # Emergency points
    carto = db_zones_carto.get(permis['zone'], {})
    pdf.cell(190, 5, sanitize_text(f"Emergency Points: Assembly: {carto.get('pr', 'N/A')} | Shelter: {carto.get('confinement', 'N/A')}"), 0, 1)
    pdf.ln(3)

    # Section 2 : Risk Matrix Table
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(190, 6, sanitize_text("2. RISK MATRIX & SPECIFIC PERMITS SUMMARY"), 1, 1, 'L', True)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(55, 6, sanitize_text("Selected Activity"), 1, 0, 'L', True)
    pdf.cell(55, 6, sanitize_text("Identified Risk"), 1, 0, 'L', True)
    pdf.cell(80, 6, sanitize_text("Main Preventive Measures"), 1, 1, 'L', True)

    pdf.set_font("Helvetica", "", 8)
    for r in permis.get("tableau_risques", []):
        pdf.cell(55, 6, sanitize_text(str(r.get("activite", "")))[:30], 1, 0)
        pdf.cell(55, 6, sanitize_text(str(r.get("risque", "")))[:30], 1, 0)
        pdf.cell(80, 6, sanitize_text(str(r.get("prevention", "")))[:48], 1, 1)
    pdf.ln(3)

    # Section 3 : Details of Specific Permits (HRT)
    details_hrt = permis.get("details_hrt", {})
    if details_hrt:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(190, 6, sanitize_text("3. HIGH RISK TASK (HRT) SPECIFIC PERMITS DETAILS"), 1, 1, 'L', True)
        pdf.set_font("Helvetica", "", 8)

        if "meuleuse" in details_hrt:
            m = details_hrt["meuleuse"]
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(190, 5, sanitize_text("• Angle Grinder Specs:"), 0, 1)
            pdf.set_font("Helvetica", "", 8)
            pdf.multi_cell(190, 4, sanitize_text(f"  Diameter: {m.get('diametre')} | Brand: {m.get('marque')} | Power: {m.get('alim')} | Ref: {m.get('ref')}"))
            pdf.multi_cell(190, 4, sanitize_text(f"  Operations: {', '.join(m.get('operations', []))}"))

        if "toiture" in details_hrt:
            t = details_hrt["toiture"]
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(190, 5, sanitize_text("• Roof Access:"), 0, 1)
            pdf.set_font("Helvetica", "", 8)
            pdf.multi_cell(190, 4, sanitize_text(f"  Protection: {t.get('protection')} | ePDP Approver: {t.get('valideur')}"))

        if "points_chauds" in details_hrt:
            ch = details_hrt["points_chauds"]
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(190, 5, sanitize_text("• Hot Work Permit:"), 0, 1)
            pdf.set_font("Helvetica", "", 8)
            pdf.multi_cell(190, 4, sanitize_text(f"  Extinguishers: {ch.get('extincteur1')} & {ch.get('extincteur2')} | Cleared 10m: {ch.get('degage_10m')}"))
            pdf.multi_cell(190, 4, sanitize_text(f"  Fire Watch: {ch.get('vigie')} | 60 min Watch: {ch.get('surveillance_60m')} | End: {ch.get('heure_fin')} | Departure: {ch.get('heure_depart')}"))

        if "excavation" in details_hrt:
            ex = details_hrt["excavation"]
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(190, 5, sanitize_text("• Excavation & Civil Works:"), 0, 1)
            pdf.set_font("Helvetica", "", 8)
            pdf.multi_cell(190, 4, sanitize_text(f"  Utility Maps: {ex.get('plans')} | DICT: {ex.get('dict')} | Access: {ex.get('acces')}"))
            pdf.multi_cell(190, 4, sanitize_text(f"  Signatures: Lead ({ex.get('chef_m')}) / DO ({ex.get('do')}) / Red Helmet ({ex.get('casque_rouge')})"))

        if "grutage" in details_hrt:
            g = details_hrt["grutage"]
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(190, 5, sanitize_text("• Lifting & Crane Operations:"), 0, 1)
            pdf.set_font("Helvetica", "", 8)
            pdf.multi_cell(190, 4, sanitize_text(f"  Crane: {g.get('immat')} | Boom: {g.get('fleche')}m | Radius: {g.get('portee')}m | Pad Pressure: {g.get('pression_patin')}"))
            pdf.multi_cell(190, 4, sanitize_text(f"  Load Weight: {g.get('poids_charge')} {g.get('unite')} | Rigging: {g.get('poids_acc')} {g.get('unite')} | Total: {g.get('poids_total')} {g.get('unite')}"))
            pdf.multi_cell(190, 4, sanitize_text(f"  Wind: {g.get('vent_val')} {g.get('vent_unite')} | Exclusion Zone: {g.get('balisage')} | Anemometer: {g.get('anemometre')}"))

        if "confine" in details_hrt:
            co = details_hrt["confine"]
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(190, 5, sanitize_text("• Confined Space Entry:"), 0, 1)
            pdf.set_font("Helvetica", "", 8)
            pdf.multi_cell(190, 4, sanitize_text(f"  Location: {co.get('lieu')} | Manhole >= 610mm: {co.get('troudhomme')} | CATEC: {co.get('catec')} | M20 Mask: {co.get('m20')}"))
            pdf.multi_cell(190, 4, sanitize_text(f"  O2 Level: {co.get('o2')}% (Countermeasure: {co.get('o2_cm')}%) | Forced Ventilation: {co.get('ventilation')}"))
            pdf.multi_cell(190, 4, sanitize_text(f"  Signatures: Entrant ({co.get('entrant')}) / Standby ({co.get('standby')}) / DO ({co.get('do')})"))

        if "electrique" in details_hrt:
            el = details_hrt["electrique"]
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(190, 5, sanitize_text("• Electrical Works:"), 0, 1)
            pdf.set_font("Helvetica", "", 8)
            pdf.multi_cell(190, 4, sanitize_text(f"  Cabinet/Enclosure: {el.get('armoire')} | Measurements: {el.get('releve')} | Live Parts Proximity: {el.get('voisinage_nues')}"))

        if "consignation" in details_hrt:
            lo = details_hrt["consignation"]
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(190, 5, sanitize_text("• Energy Lockout/Tagout (LOTO):"), 0, 1)
            pdf.set_font("Helvetica", "", 8)
            pdf.multi_cell(190, 4, sanitize_text(f"  Isolation Method: {lo.get('methode_fluide')} | Loc 1: {lo.get('loc1')} | Loc 2: {lo.get('loc2')}"))
            pdf.multi_cell(190, 4, sanitize_text(f"  Elec LOTO: {lo.get('elec')} ({lo.get('elec_loc1')} / Padlock {lo.get('elec_loc2')}) | Residual Energy Discharged: {lo.get('residu')}"))

        if "systeme_risque" in details_hrt:
            sr = details_hrt["systeme_risque"]
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(190, 5, sanitize_text("• High Risk Systems / ATEX / Chemical:"), 0, 1)
            pdf.set_font("Helvetica", "", 8)
            pdf.multi_cell(190, 4, sanitize_text(f"  Class 1: {sr.get('classe1_nom')} | Dangerous Fluid: {sr.get('fluide_nom')} | ATEX: {sr.get('atex_nom')}"))
            pdf.multi_cell(190, 4, sanitize_text(f"  Safety Shower Tested: {sr.get('douche')} | Line Flushing: {sr.get('ramonage')} | Signatures: Operator / DO / Ops"))

        pdf.ln(2)

    # Section 4 : Required PPE
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(190, 6, sanitize_text("4. REQUIRED PERSONAL PROTECTIVE EQUIPMENT (PPE)"), 1, 1, 'L', True)
    pdf.set_font("Helvetica", "", 8)
    epis_str = ", ".join(permis.get("epis_cochis", ["Basic PPE"]))
    pdf.multi_cell(190, 4, sanitize_text(f"Selected PPE: {epis_str}"))
    pdf.ln(2)

    # Section 5 : Signatures
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(190, 6, sanitize_text("5. AUDITED SIGNATURES FILED IN ePDP"), 1, 1, 'L', True)
    pdf.set_font("Helvetica", "", 8)
    for sign in permis.get("intervenants", []):
        pdf.cell(190, 5, sanitize_text(f" [OK] Timestamped worker signature: {sign}"), 1, 1)

    return bytes(pdf.output())

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Procter_%26_Gamble_logo.svg/1024px-Procter_%26_Gamble_logo.svg.png", width=80)
st.sidebar.title("e-Work Permit P&G")
st.sidebar.caption("Site d'Amiens / Amiens Plant")

role = st.sidebar.radio("Interface :", [
    "🖥️ Borne Kiosk Tactile / Touch Terminal", 
    "📊 DDS Board & Batch 07h30", 
    "📱 Inspection Terrain QR Code / Field Audit"
])

st.sidebar.divider()
st.sidebar.write(L["lang_title"])
col_l1, col_l2 = st.sidebar.columns(2)
with col_l1:
    if st.button("🇫🇷 FR", use_container_width=True, type="primary" if st.session_state.lang == "FR" else "secondary", key="sb_lang_fr"):
        st.session_state.lang = "FR"
        st.rerun()
with col_l2:
    if st.button("🇬🇧 EN", use_container_width=True, type="primary" if st.session_state.lang == "EN" else "secondary", key="sb_lang_en"):
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

        # SÉLECTEUR DE LANGUE DISCRET EN BAS DE PAGE ACCUEIL
        st.write("---")
        st.caption(L["lang_title"])
        col_fr, col_en, _ = st.columns([1, 1, 6])
        with col_fr:
            type_fr = "primary" if st.session_state.lang == "FR" else "secondary"
            if st.button("🇫🇷 FR", type=type_fr, use_container_width=True, key="btn_lang_fr_home"):
                st.session_state.lang = "FR"
                st.rerun()
        with col_en:
            type_en = "primary" if st.session_state.lang == "EN" else "secondary"
            if st.button("🇬🇧 EN", type=type_en, use_container_width=True, key="btn_lang_en_home"):
                st.session_state.lang = "EN"
                st.rerun()

    elif st.session_state.kiosk_mode == "PDP":
        if st.button(L["back_home"]): st.session_state.kiosk_mode = "HOME"; st.rerun()
        st.subheader("📝 " + ("Émargement PDP" if st.session_state.lang == "FR" else "PDP Sign-off"))
        st.divider()
        soc_pdp = st.selectbox("1. EE / Contractor :", db_societes)
        pdp_sel = st.selectbox("2. PDP :", db_pdps.get(soc_pdp, ["PDP"]))
        nom_pdp = st.text_input("Name / Nom :")
        statut_pdp = st.selectbox("Role / Statut :", ["N1 (Compagnon / Worker)", "N2 (Responsable / Lead)"])
        
        tel_pdp = ""
        if "N2" in statut_pdp:
            tel_pdp = st.text_input("Phone / Téléphone (Mandatory N2) :", placeholder="+33...")

        st.info(" [ Zone de Signature Tactile / Touch Signature Area ] ")
        if st.button("✅ " + ("VALIDER" if st.session_state.lang == "FR" else "CONFIRM"), type="primary", use_container_width=True):
            if "N2" in statut_pdp and not tel_pdp.strip():
                st.error("⚠️ Phone required / Téléphone obligatoire.")
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
                lbl_today = f"Aujourd'hui / Today : {today_date.strftime('%d/%m/%Y')}"
                lbl_tom = f"Demain / Tomorrow : {tomorrow_date.strftime('%d/%m/%Y')}"
                date_choice = st.radio("Date :", [lbl_today, lbl_tom])
                st.session_state.form_data["date_str"] = tomorrow_date.strftime("%d/%m/%Y") if lbl_tom in date_choice else today_date.strftime("%d/%m/%Y")
            with c2:
                st.session_state.form_data["societe"] = st.selectbox("Company / Entreprise :", db_societes, index=db_societes.index(get_val("societe", "ABYLSEN")) if get_val("societe") in db_societes else 0)

            c_back, c_next = st.columns(2)
            with c_back:
                if st.button(L["back_home"]): st.session_state.kiosk_mode = "HOME"; st.rerun()
            with c_next:
                if st.button(L["next"], type="primary"): st.session_state.step = 2; st.rerun()

        elif current_step == 2:
            st.subheader(f"2. {L['steps'][1]}")
            p_list = db_pdps.get(get_val("societe"), ["PDP Standard"])
            st.session_state.form_data["pdp"] = st.selectbox("PDP :", p_list, index=p_list.index(get_val("pdp")) if get_val("pdp") in p_list else 0)
            
            m_obj_list = db_mops.get(get_val("pdp"), [{"titre": "MoP Standard", "st": False}])
            m_titles = [m["titre"] for m in m_obj_list]
            selected_mop_title = st.selectbox("MoP / Method Statement :", m_titles, index=m_titles.index(get_val("mop")) if get_val("mop") in m_titles else 0)
            st.session_state.form_data["mop"] = selected_mop_title
            
            mop_info = next((m for m in m_obj_list if m["titre"] == selected_mop_title), {"st": False})
            st.session_state.form_data["is_subcontractor"] = mop_info.get("st", False)

            if get_val("is_subcontractor"):
                st.warning(f"⚠️ {L['subcontract_alert']}")
                st.session_state.form_data["titulaire_n2"] = st.text_input("Main Contractor N2 Lead Name :", value=get_val("titulaire_n2", mop_info.get('titulaire', 'ABYLSEN') + " - N2 Lead"))
            else:
                st.success("✅ Direct Contractor / Titulaire direct du PDP.")

            c_back, c_next = st.columns(2)
            with c_back:
                if st.button(L["previous"]): st.session_state.step = 1; st.rerun()
            with c_next:
                if st.button(L["next"], type="primary"): st.session_state.step = 3; st.rerun()

        elif current_step == 3:
            st.subheader(f"3. {L['steps'][2]}")
            st.session_state.form_data["n2_nom"] = st.selectbox("N2 Lead Supervisor / Responsable N2 :", db_n2, index=db_n2.index(get_val("n2_nom")) if get_val("n2_nom") in db_n2 else 0)
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

            zones_keys = list(db_zones_carto.keys())
            st.session_state.form_data["lieu_pdp"] = st.selectbox("Zone :", zones_keys, index=zones_keys.index(get_val("lieu_pdp")) if get_val("lieu_pdp") in zones_keys else 0)
            st.session_state.form_data["lieu_precision"] = st.text_input("Location Details / Précisions :", value=get_val("lieu_precision"))
            st.session_state.form_data["description"] = st.text_input("Task Description / Description des travaux :", value=get_val("description"))

            carto = db_zones_carto.get(get_val("lieu_pdp"), {})
            st.warning(f"📍 Emergency Rescue Points: PR `{carto.get('pr')}` | Shelter Zone `{carto.get('confinement')}`")

            c_back, c_next = st.columns(2)
            with c_back:
                if st.button(L["previous"]): st.session_state.step = 3; st.rerun()
            with c_next:
                if st.button(L["next"], type="primary"): st.session_state.step = 5; st.rerun()

        # ==============================================================================
        # ÉTAPE 5 : MÉTÉO -> RISQUES PRINCIPAUX -> STA -> EPIS
        # ==============================================================================
        elif current_step == 5:
            st.subheader(f"5. {L['steps'][4]}")

            meteo_live = obtenir_meteo_amiens_live()
            temp_max = meteo_live['temp_max_j0']
            vent = meteo_live['vent_j0']
            
            if vent > 36 or temp_max < 3 or temp_max > 30:
                weather_class = "weather-alert"
                status_msg = "❌ <b>WEATHER ALERT / ALERTE MÉTÉO</b> (Vent > 36 km/h ou T° Extrême)"
            elif 30 <= vent <= 36:
                weather_class = "weather-warning"
                status_msg = "⚠️ <b>WEATHER VIGILANCE / VIGILANCE MÉTÉO</b> (Vent entre 30 et 36 km/h)"
            else:
                weather_class = "weather-ok"
                status_msg = "✅ <b>FAVORABLE CONDITIONS / CONDITIONS FAVORABLES</b>"

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

            st.error("🚨 **1. MAIN RISKS (Triggers HRT Specific Permit) / RISQUES PRINCIPAUX :**")
            
            cr1, cr2 = st.columns(2)
            with cr1:
                p_hauteur = st.checkbox("Work at height / Travail en hauteur", value=get_val("p_hauteur"))
                p_toiture = st.checkbox("Roof access / Accès toiture", value=get_val("p_toiture"))
                p_points_chauds_val = get_val("p_points_chauds")
                p_excavation = st.checkbox("Trench, excavation, civil works / Excavation, tranchée", value=get_val("p_excavation"))
                p_grutage = st.checkbox("Lifting, crane / Grutage, levage", value=get_val("p_grutage"))
                p_confine = st.checkbox("Confined space / Espace confiné", value=get_val("p_confine"))

            with cr2:
                p_electrique = st.checkbox("Electrical work / Travail électrique", value=get_val("p_electrique"))
                p_ouverture_circuit = st.checkbox("Line breaking / Ouverture de circuit", value=get_val("p_ouverture_circuit"))
                p_machines_mouvement = st.checkbox("Moving machinery / Machines en mouvement", value=get_val("p_machines_mouvement"))
                p_equipement_pression = st.checkbox("Pressure equipment / Équipement sous pression", value=get_val("p_equipement_pression"))
                p_laser_classe_iv = st.checkbox("Class IV Laser / Laser Classe IV", value=get_val("p_laser_classe_iv"))
                p_demolition = st.checkbox("Demolition / Démolition", value=get_val("p_demolition"))
                p_meuleuse = st.checkbox("Angle grinder / Meuleuse", value=get_val("p_meuleuse"))

            if p_meuleuse:
                p_points_chauds_val = True
                st.session_state.form_data["t_outils_electro"] = True

            with cr1:
                p_points_chauds = st.checkbox("Hot work, sparks / Point chaud, flamme", value=p_points_chauds_val)

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
                st.session_state.form_data["dta_consultation"] = st.checkbox("Asbestos file (DTA) consultation verified / DTA consulté", value=get_val("dta_consultation"))

            st.divider()

            st.write("##### 🛠️ 2. STA (Safety Task Assignment) & Tools / Outillage :")

            st.session_state.form_data["sta_prod_chimiques"] = st.checkbox("Chemical products / Produits chimiques", value=get_val("sta_prod_chimiques"))
            if get_val("sta_prod_chimiques"):
                st.session_state.form_data["sta_prod_chimiques_nom"] = st.text_input("Chemical names / Noms des produits :", value=get_val("sta_prod_chimiques_nom"))
                st.session_state.form_data["p_systeme_risque"] = True

            ct1, ct2 = st.columns(2)
            with ct1:
                st.session_state.form_data["t_outils_electro"] = st.checkbox("Power tools / Outils électroportatifs", value=get_val("t_outils_electro"))
                st.session_state.form_data["t_travaux_manuels"] = st.checkbox("Manual work / Travaux manuels", value=get_val("t_travaux_manuels"))
            with ct2:
                st.session_state.form_data["t_manutention_lourde"] = st.checkbox("Heavy manual handling / Manutention lourde", value=get_val("t_manutention_lourde"))
                st.session_state.form_data["t_nettoyage_chantiers"] = st.checkbox("Housekeeping / Nettoyage chantier", value=get_val("t_nettoyage_chantiers"))

            st.divider()

            st.write("##### 🥽 3. PPE / Équipements de Protection Individuelle :")

            st.markdown("""
            <div class='notice-epi-card'>
                ⚠ <b>Baseline Rules:</b> High boots, Helmet with chinstrap, EN166 Safety Glasses, Hi-Viz Vest, Cut-Resistant Gloves required.
            </div>
            """, unsafe_allow_html=True)

            auto_jugulaire = p_hauteur or p_toiture
            auto_visiere = p_points_chauds or p_meuleuse or p_laser_classe_iv
            auto_gants_elec = p_electrique
            auto_gants_coupure = p_meuleuse or p_points_chauds
            auto_resp_cartouche = p_confine or get_val("sta_prod_chimiques")

            cepi_col1, cepi_col2 = st.columns(2)

            with cepi_col1:
                st.write("**• Eye & Face / Lunettes & Visages :**")
                st.session_state.form_data["epi_lunettes_chantier_en166"] = st.checkbox("Safety Glasses / Lunettes EN 166 (Mandatory)", value=get_val("epi_lunettes_chantier_en166", True))
                st.session_state.form_data["epi_lunettes_etanches"] = st.checkbox("Sealed Goggles / Lunettes étanches", value=get_val("epi_lunettes_etanches"))
                st.session_state.form_data["epi_visiere_idra_en166b"] = st.checkbox("Face Shield / Visière IDRA EN 166B", value=auto_visiere or get_val("epi_visiere_idra_en166b"))
                st.session_state.form_data["epi_lunettes_pare_visage"] = st.checkbox("Glasses + Shield / Lunettes + pare-visage", value=get_val("epi_lunettes_pare_visage"))

                st.write("**• Helmets / Casques :**")
                st.session_state.form_data["epi_casque_jugulaire"] = st.checkbox("Helmet with Chinstrap / Casque jugulaire (Mandatory)", value=auto_jugulaire or get_val("epi_casque_jugulaire", True))
                st.session_state.form_data["epi_casque_protection_auditive_en387"] = st.checkbox("Helmet with Hearing Protection / Casque anti-bruit", value=get_val("epi_casque_protection_auditive_en387"))

                st.write("**• Hearing / Bouchons :**")
                st.session_state.form_data["epi_bouchons_oreilles"] = st.checkbox("Earplugs / Bouchons d'oreilles", value=get_val("epi_bouchons_oreilles"))

            with cepi_col2:
                st.write("**• Gloves / Gants :**")
                st.session_state.form_data["epi_gants_anticoupure_4x43d"] = st.checkbox("Cut Gloves / Gants Anti-coupure 4x43D", value=auto_gants_coupure or get_val("epi_gants_anticoupure_4x43d", True))
                st.session_state.form_data["epi_gants_manutention_cuir"] = st.checkbox("Leather Gloves / Gants Cuir", value=get_val("epi_gants_manutention_cuir"))
                st.session_state.form_data["epi_gants_chimiques_en374"] = st.checkbox("Chemical Gloves EN374", value=get_val("sta_prod_chimiques") or get_val("epi_gants_chimiques_en374"))
                st.session_state.form_data["epi_gants_elec_en60903"] = st.checkbox("Electrical Gloves EN60903", value=auto_gants_elec or get_val("epi_gants_elec_en60903"))

                st.write("**• Respiratory / Protection Respiratoire :**")
                st.session_state.form_data["epi_resp_ffp1_ffp2"] = st.checkbox("FFP1 / FFP2 Mask", value=get_val("epi_resp_ffp1_ffp2"))
                st.session_state.form_data["epi_resp_3m6000"] = st.checkbox("3M6000 Half Mask / Masque 3M6000", value=get_val("epi_resp_3m6000"))
                st.session_state.form_data["epi_resp_versaflo"] = st.checkbox("Versaflo PAPR / Système Versaflo", value=get_val("epi_resp_versaflo"))
                st.session_state.form_data["epi_resp_cartouche_abek_en14387"] = st.checkbox("ABEK Cartridge / Cartouche ABEK EN14387", value=auto_resp_cartouche or get_val("epi_resp_cartouche_abek_en14387"))

            st.write("**• Other / Autre :**")
            st.session_state.form_data["epi_autre_texte"] = st.text_input("Other specific PPE / Autre EPI :", value=get_val("epi_autre_texte"))

            c_back, c_next = st.columns(2)
            with c_back:
                if st.button(L["previous"]): st.session_state.step = 4; st.rerun()
            with c_next:
                if st.button(L["next"], type="primary"): st.session_state.step = 6; st.rerun()

        # ==============================================================================
        # ÉTAPE 6 : FORMULAIRES SPÉCIFIQUES COMPLETS ET EXHAUSTIFS
        # ==============================================================================
        elif current_step == 6:
            st.subheader(f"6. {L['steps'][5]}")

            # MEULEUSE
            if get_val("p_meuleuse"):
                with st.container(border=True):
                    st.markdown("<div class='permis-header-card'><h3 style='margin:0; color:#003366;'>⚙️ MEULEUSE / ANGLE GRINDER — SPECIFICATIONS</h3></div>", unsafe_allow_html=True)
                    c_m1, c_m2 = st.columns(2)
                    with c_m1:
                        st.session_state.form_data["meuleuse_diametre"] = st.selectbox("Disc / Disque :", ["125 mm", "230 mm"], index=0 if get_val("meuleuse_diametre") == "125 mm" else 1)
                        st.session_state.form_data["meuleuse_marque"] = st.text_input("Brand / Marque :", value=get_val("meuleuse_marque"))
                    with c_m2:
                        st.session_state.form_data["meuleuse_alim"] = st.selectbox("Power / Alimentation :", ["Batterie 18V / 18V Battery", "Filaire 230V / Corded", "Pneumatique"], index=0)
                        st.session_state.form_data["meuleuse_ref"] = st.text_input("Serial Tag / N° Série :", value=get_val("meuleuse_ref"))

                    st.write("##### Operations / Opérations :")
                    cm_op1, cm_op2 = st.columns(2)
                    with cm_op1:
                        st.session_state.form_data["meuleuse_u_decoupe"] = st.checkbox("Cutting / Découpe", value=get_val("meuleuse_u_decoupe"))
                        if get_val("meuleuse_u_decoupe"):
                            st.session_state.form_data["meuleuse_mat_decoupe"] = st.selectbox("Material / Matériau découpe :", db_materiaux, index=0)
                        
                        st.session_state.form_data["meuleuse_u_ebavurage"] = st.checkbox("Deburring / Ébavurage", value=get_val("meuleuse_u_ebavurage"))
                        if get_val("meuleuse_u_ebavurage"):
                            st.session_state.form_data["meuleuse_mat_ebavurage"] = st.selectbox("Material / Matériau ébavuré :", db_materiaux, index=0)

                    with cm_op2:
                        st.session_state.form_data["meuleuse_u_flap"] = st.checkbox("Flap Disc / Disque lamelles", value=get_val("meuleuse_u_flap"))
                        st.session_state.form_data["meuleuse_u_blanchiment"] = st.checkbox("Stripping / Blanchiment", value=get_val("meuleuse_u_blanchiment"))
                        if get_val("meuleuse_u_blanchiment"):
                            st.session_state.form_data["meuleuse_disque_blanchiment"] = st.selectbox("Disc type / Type disque :", db_disques_blanchiment, index=0)

            # 1. HAUTEUR
            if get_val("p_hauteur"):
                with st.container(border=True):
                    st.markdown("<div class='permis-header-card'><h3 style='margin:0; color:#b91c1c;'>🧗 TRAVAIL EN HAUTEUR / WORK AT HEIGHT</h3></div>", unsafe_allow_html=True)
                    st.info("🥽 Helmet with chinstrap / Casque jugulaire")

                    st.session_state.form_data["h_pirl"] = st.checkbox("PIRL (Platform ladder / Plateforme)", value=get_val("h_pirl"))
                    if get_val("h_pirl"):
                        cp1, cp2 = st.columns(2)
                        with cp1: st.session_state.form_data["h_pirl_vgp"] = st.checkbox("Periodic Check / VGP OK", value=get_val("h_pirl_vgp"))
                        with cp2: st.session_state.form_data["h_pirl_soc"] = st.text_input("Owner / Propriétaire PIRL :", value=get_val("h_pirl_soc"))

                    st.session_state.form_data["h_nacelle"] = st.checkbox("MEWP / Nacelle PEMP", value=get_val("h_nacelle"))
                    if get_val("h_nacelle"):
                        cn1, cn2 = st.columns(2)
                        with cn1:
                            st.session_state.form_data["h_nacelle_vgp"] = st.checkbox("VGP & Checklist OK", value=get_val("h_nacelle_vgp"))
                            st.session_state.form_data["h_nacelle_caces"] = st.checkbox("CACES / License OK", value=get_val("h_nacelle_caces"))
                            st.session_state.form_data["h_nacelle_aut"] = st.checkbox("Driving Authorization / Autorisation de conduite OK", value=get_val("h_nacelle_aut"))
                        with cn2:
                            st.session_state.form_data["h_nacelle_harnais"] = st.checkbox("Harness Training / Formation Harnais OK", value=get_val("h_nacelle_harnais"))
                            st.session_state.form_data["h_nacelle_soc"] = st.text_input("MEWP Owner / Société Nacelle :", value=get_val("h_nacelle_soc"))

                    st.session_state.form_data["h_echaf"] = st.checkbox("Scaffolding / Échafaudage", value=get_val("h_echaf"))
                    if get_val("h_echaf"):
                        ce1, ce2 = st.columns(2)
                        with ce1:
                            st.session_state.form_data["h_echaf_montage"] = st.checkbox("Erection Operation / Montage-Démontage", value=get_val("h_echaf_montage"))
                            st.session_state.form_data["h_echaf_ctrl_regle"] = st.checkbox("Regulatory Check / Vérification réglementaire", value=get_val("h_echaf_ctrl_regle"))
                        with ce2:
                            st.session_state.form_data["h_echaf_certif_affiche"] = st.checkbox("Green tag displayed / PV de réception affiché", value=get_val("h_echaf_certif_affiche"))
                            st.session_state.form_data["h_echaf_verif_j"] = st.checkbox("Daily Check / Vérification quotidienne", value=get_val("h_echaf_verif_j"))
                        st.session_state.form_data["h_echaf_soc_util"] = st.text_input("Scaffold Operating Company / Société utilisateur :", value=get_val("h_echaf_soc_util"))

            # 2. TOITURE
            if get_val("p_toiture"):
                with st.container(border=True):
                    st.markdown("<div class='permis-header-card'><h3 style='margin:0; color:#b91c1c;'>🏢 ACCÈS TOITURE / ROOF ACCESS</h3></div>", unsafe_allow_html=True)
                    opts_protect = ["Garde-corps / Guardrail", "Ligne de vie / Lifeline", "Pas de protection / None"]
                    st.session_state.form_data["toiture_protection"] = st.selectbox("Protection :", opts_protect)
                    st.session_state.form_data["toiture_valideur"] = st.text_input("Roof Access Approver / Valideur :", value=get_val("toiture_valideur"))

            # 3. POINT CHAUD
            if get_val("p_points_chauds"):
                with st.container(border=True):
                    st.markdown("<div class='permis-header-card'><h3 style='margin:0; color:#d97706;'>🔥 PERMIS POINT CHAUD / HOT WORK</h3></div>", unsafe_allow_html=True)
                    st.write("##### Extinguishers / Extincteurs :")
                    opts_ext = ["Poudre / Powder", "Eau + additifs / Water", "CO2"]
                    cext1, cext2 = st.columns(2)
                    with cext1: st.session_state.form_data["chaud_extincteur1"] = st.selectbox("Extinguisher 1 :", opts_ext)
                    with cext2: st.session_state.form_data["chaud_extincteur2"] = st.selectbox("Extinguisher 2 :", opts_ext, index=2)
                    
                    st.session_state.form_data["chaud_degage_10m"] = st.checkbox("10m Cleared Area / Zone 10m dégagée", value=get_val("chaud_degage_10m"))
                    st.session_state.form_data["chaud_traverse_mur"] = st.checkbox("Penetrating Wall / Traversée de mur ou plancher", value=get_val("chaud_traverse_mur"))
                    st.session_state.form_data["chaud_ouverture_10m"] = st.checkbox("Opening <10m / Proximité ouverture <10m", value=get_val("chaud_ouverture_10m"))
                    
                    st.session_state.form_data["chaud_vigie_nom"] = st.text_input("Fire Watch Name / Nom Vigie pendant travaux :", value=get_val("chaud_vigie_nom"))
                    st.session_state.form_data["chaud_personne_surv_60m"] = st.text_input("Post Fire Patrol Lead (60 min) / Vigie 60 min après :", value=get_val("chaud_personne_surv_60m"))
                    
                    chf1, chf2 = st.columns(2)
                    with chf1: st.session_state.form_data["chaud_heure_fin"] = st.text_input("End Time / Heure fin travaux :", value=get_val("chaud_heure_fin"))
                    with chf2: st.session_state.form_data["chaud_heure_depart"] = st.text_input("Closeout Time / Heure départ vigie :", value=get_val("chaud_heure_depart"))
                    st.session_state.form_data["chaud_commentaires"] = st.text_area("Comments / Commentaires :", value=get_val("chaud_commentaires"))

            # 4. EXCAVATION
            if get_val("p_excavation"):
                with st.container(border=True):
                    st.markdown("<div class='permis-header-card'><h3 style='margin:0; color:#003366;'>🚜 EXCAVATION & TRENCHING</h3></div>", unsafe_allow_html=True)
                    st.write("##### Plans & Utilities / Vérification Réseaux :")
                    cx1, cx2, cx3, cx4 = st.columns(4)
                    with cx1: st.session_state.form_data["excav_plans_eaux_indus"] = st.checkbox("Water / Eaux", value=get_val("excav_plans_eaux_indus"))
                    with cx2: st.session_state.form_data["excav_plans_eaux_pluv"] = st.checkbox("Stormwater / Pluviales", value=get_val("excav_plans_eaux_pluv"))
                    with cx3: st.session_state.form_data["excav_plans_ht"] = st.checkbox("HV / HT", value=get_val("excav_plans_ht"))
                    with cx4: st.session_state.form_data["excav_plans_gaz"] = st.checkbox("Gas / Gaz", value=get_val("excav_plans_gaz"))

                    st.session_state.form_data["excav_dict"] = st.checkbox("DICT Validated / DICT enregistrée", value=get_val("excav_dict"))
                    st.session_state.form_data["excav_balisage"] = st.checkbox("Rigid Barricade / Balisage rigide", value=get_val("excav_balisage"))
                    st.session_state.form_data["excav_profondeur_130"] = st.checkbox("Depth > 1.30m / Profondeur > 1,30m", value=get_val("excav_profondeur_130"))
                    
                    st.write("##### Signatures :")
                    st.session_state.form_data["excav_chef_manoeuvre"] = st.text_input("Site Manager / Chef Manœuvre :", value=get_val("excav_chef_manoeuvre"))
                    st.session_state.form_data["excav_do"] = st.text_input("Project Owner / Donneurs d'ordres :", value=get_val("excav_do"))
                    st.session_state.form_data["excav_casque_rouge"] = st.text_input("Red Helmet / Casque Rouge P&G :", value=get_val("excav_casque_rouge"))

            # 5. GRUTAGE
            if get_val("p_grutage"):
                with st.container(border=True):
                    st.markdown("<div class='permis-header-card'><h3 style='margin:0; color:#003366;'>🏗️ CRANE & LIFTING / GRUTAGE</h3></div>", unsafe_allow_html=True)
                    st.session_state.form_data["grut_desc_mop"] = st.text_area("Load Description / Description Charge :", value=get_val("grut_desc_mop"))
                    
                    cg1, cg2 = st.columns(2)
                    with cg1: st.session_state.form_data["grut_poids_charge"] = st.number_input("Load Weight / Poids Charge :", value=float(get_val("grut_poids_charge")))
                    with cg2: st.session_state.form_data["grut_poids_acc"] = st.number_input("Rigging Weight / Poids Accessoires :", value=float(get_val("grut_poids_acc")))
                    
                    cmat1, cmat2, cmat3 = st.columns(3)
                    with cmat1: st.session_state.form_data["grut_immat"] = st.text_input("Crane Tag / Immatriculation :", value=get_val("grut_immat"))
                    with cmat2: st.session_state.form_data["grut_fleche"] = st.number_input("Boom Length / Flèche (m) :", value=float(get_val("grut_fleche")))
                    with cmat3: st.session_state.form_data["grut_portee"] = st.number_input("Working Radius / Portée (m) :", value=float(get_val("grut_portee")))

                    st.session_state.form_data["grut_anemometre"] = st.checkbox("Anemometer OK / Anémomètre OK", value=get_val("grut_anemometre"))
                    cv1, cv2 = st.columns(2)
                    with cv1: st.session_state.form_data["grut_vent_val"] = st.number_input("Measured Wind / Vent Mesuré :", value=float(get_val("grut_vent_val")))
                    with cv2: st.session_state.form_data["grut_vent_unite"] = st.selectbox("Unit / Unité :", ["km/h", "m/S"], index=0)

                    st.write("##### Signatures :")
                    st.session_state.form_data["grut_chef_m_nom"] = st.text_input("Lift Director / Chef de Manœuvre :", value=get_val("grut_chef_m_nom"))
                    st.session_state.form_data["grut_do_sign"] = st.text_input("Project Owner / Donneur d'Ordre :", value=get_val("grut_do_sign"))
                    st.session_state.form_data["grut_casque_rouge_sign"] = st.text_input("Red Helmet / Casque Rouge :", value=get_val("grut_casque_rouge_sign"))

            # 6. ESPACE CONFINÉ
            if get_val("p_confine"):
                with st.container(border=True):
                    st.markdown("<div class='permis-header-card'><h3 style='margin:0; color:#003366;'>🦺 CONFINED SPACE / ESPACE CONFINÉ</h3></div>", unsafe_allow_html=True)
                    st.session_state.form_data["conf_lieu"] = st.text_input("Vessel, Tank / Nom Équipement :", value=get_val("conf_lieu"))
                    st.session_state.form_data["conf_catec"] = st.checkbox("CATEC Certified / Formation CATEC OK", value=get_val("conf_catec"))
                    st.session_state.form_data["conf_m20"] = st.checkbox("M20 EEBD Respirator / Masque M20", value=get_val("conf_m20"))
                    st.session_state.form_data["conf_ventilation_forcee"] = st.checkbox("Forced Ventilation / Ventilation forcée", value=get_val("conf_ventilation_forcee"))
                    
                    co1, co2 = st.columns(2)
                    with co1: st.session_state.form_data["conf_o2"] = st.number_input("Measured O2 (%) :", value=float(get_val("conf_o2")))
                    with co2: st.session_state.form_data["conf_temp_cuve"] = st.number_input("Internal Temp (°C) :", value=float(get_val("conf_temp_cuve")))

                    st.session_state.form_data["conf_entrant"] = st.text_input("Entrant / Intervenant Entrant :", value=get_val("conf_entrant"))
                    st.session_state.form_data["conf_standby"] = st.text_input("Hole Watch / Vigie Extérieure :", value=get_val("conf_standby"))

            # 7. ÉLECTRIQUE
            if get_val("p_electrique"):
                with st.container(border=True):
                    st.markdown("<div class='permis-header-card'><h3 style='margin:0; color:#b91c1c;'>⚡ ELECTRICAL WORK / ÉLECTRIQUE</h3></div>", unsafe_allow_html=True)
                    st.session_state.form_data["elec_armoire"] = st.checkbox("Inside Cabinet / Intérieur Armoire", value=get_val("elec_armoire"))
                    st.session_state.form_data["elec_voisinage_tension"] = st.checkbox("Proximity Live Parts / Voisinage sous tension", value=get_val("elec_voisinage_tension"))
                    st.session_state.form_data["elec_voisinage_nues"] = st.checkbox("Bare Exposed Live Parts / Pièces nues", value=get_val("elec_voisinage_nues"))
                    st.session_state.form_data["elec_valideur_ei"] = st.text_input("E&I Testing Lead / Valideur E&I :", value=get_val("elec_valideur_ei"))

            # 8. CONSIGNATION LOTO
            if get_val("p_consignation"):
                with st.container(border=True):
                    st.markdown("<div class='permis-header-card'><h3 style='margin:0; color:#15803d;'>⚡ LOTO ISOLATION / CONSIGNATION</h3></div>", unsafe_allow_html=True)
                    opts_loto_m = ["2 vannes / 2 valves + drain", "2 vannes", "vanne unique", "platine / blind flange"]
                    st.session_state.form_data["loto_ouverture_methode"] = st.selectbox("Isolation Method / Méthode :", opts_loto_m)
                    
                    clo1, clo2 = st.columns(2)
                    with clo1: st.session_state.form_data["loto_ouvert_loc1"] = st.text_input("Primary Point / Organe 1 :", value=get_val("loto_ouvert_loc1"))
                    with clo2: st.session_state.form_data["loto_ouvert_loc2"] = st.text_input("Secondary Point / Organe 2 :", value=get_val("loto_ouvert_loc2"))
                    
                    st.session_state.form_data["loto_is_elec"] = st.checkbox("Electrical Lockout / Cadenas Électrique", value=get_val("loto_is_elec"))
                    if get_val("loto_is_elec"):
                        st.session_state.form_data["loto_is_elec_loc2"] = st.text_input("Lock ID / N° Cadenas :", value=get_val("loto_is_elec_loc2"))
                    st.session_state.form_data["loto_residu"] = st.checkbox("Zero Energy Check / Purge Énergie Résiduelle", value=get_val("loto_residu"))

            # 9. SYSTÈME À RISQUES / ATEX
            if get_val("p_systeme_risque"):
                with st.container(border=True):
                    st.markdown("<div class='permis-header-card'><h3 style='margin:0; color:#b91c1c;'>☣ HIGH HAZARDS / SYSTÈMES À RISQUES / ATEX</h3></div>", unsafe_allow_html=True)
                    st.session_state.form_data["sr_chimique_c1"] = st.checkbox("Class 1 Chemical / Produit Chimique C1", value=get_val("sr_chimique_c1"))
                    if get_val("sr_chimique_c1"):
                        st.session_state.form_data["sr_chimique_nom"] = st.text_input("Chemical Name / Nom Produit :", value=get_val("sr_chimique_nom"))
                    
                    st.session_state.form_data["sr_atex"] = st.checkbox("ATEX Zone / Zone ATEX", value=get_val("sr_atex"))
                    st.session_state.form_data["sr_balisage"] = st.checkbox("Extended Barricade / Balisage Élargi", value=get_val("sr_balisage"))
                    st.session_state.form_data["sr_douche_rince"] = st.checkbox("Safety Shower Tested / Douche Sécurité OK", value=get_val("sr_douche_rince"))

                    st.session_state.form_data["sr_sign_intervenant"] = st.text_input("Operator / Opérateur Chimique :", value=get_val("sr_sign_intervenant"))
                    st.session_state.form_data["sr_sign_do"] = st.text_input("Project Owner / Donneur d'Ordre :", value=get_val("sr_sign_do"))
                    st.session_state.form_data["sr_sign_operations"] = st.text_input("Operations Manager / Responsable Fabrications :", value=get_val("sr_sign_operations"))

            c_back, c_next = st.columns(2)
            with c_back:
                if st.button(L["previous"]): st.session_state.step = 5; st.rerun()
            with c_next:
                if st.button(L["next"], type="primary"): st.session_state.step = 7; st.rerun()

        # ==============================================================================
        # ÉTAPE 7 : RÉCAPITULATIF INTEGRAL ET SANS OMISSION
        # ==============================================================================
        elif current_step == 7:
            st.subheader(f"7. {L['steps'][6]}")

            st.markdown("<div class='status-pending'>⚠️ PERMIT PENDING BATCH VALIDATION (07:30 AM) / PERMIS EN ATTENTE BATCH</div>", unsafe_allow_html=True)

            if get_val("is_subcontractor"):
                st.warning(f"🤝 **{L['subcontract_alert']}**")

            # ---------------------------------------------------------
            # 1. INFORMATIONS GÉNÉRALES & LOCALISATION
            # ---------------------------------------------------------
            with st.container(border=True):
                st.markdown("### 📋 1. General Information & Location / Informations Générales")
                c_r1, c_r2 = st.columns(2)
                with c_r1:
                    st.write(f"• **Date :** `{get_val('date_str')}`")
                    st.write(f"• **Company / Société :** `{get_val('societe')}`")
                    st.write(f"• **PDP :** `{get_val('pdp')}`")
                    st.write(f"• **MoP :** `{get_val('mop')}`")
                    if get_val("is_subcontractor"):
                        st.write(f"• **Main Contractor N2 Lead / N2 Titulaire :** `{get_val('titulaire_n2')}`")
                with c_r2:
                    st.write(f"• **N2 Supervisor / Responsable N2 :** `{get_val('n2_nom')}`")
                    st.write(f"• **Zone :** `{get_val('lieu_pdp')}`")
                    st.write(f"• **Location Details / Précision :** `{get_val('lieu_precision')}`")
                    st.write(f"• **Description :** `{get_val('description')}`")
                    st.write(f"• **Workers / Intervenants :** `{', '.join(get_val('intervenants', []))}`")

            # ---------------------------------------------------------
            # 2. RISQUES IDENTIFIÉS & TABLEAU SYNTHÉTIQUE
            # ---------------------------------------------------------
            with st.container(border=True):
                st.markdown("### 🚨 2. Risk Assessment Summary / Tableau Synthétique des Risques")
                
                tableau_data = []
                if get_val("p_hauteur"):
                    tableau_data.append({"Activity / Activité": "Work at Height / Hauteur", "Risk / Risque": "Fall / Chute", "Prevention / Prévention": "Helmet chinstrap + VGP OK"})
                if get_val("p_toiture"):
                    tableau_data.append({"Activity / Activité": "Roof Access / Toiture", "Risk / Risque": "Fall / Chute", "Prevention / Prévention": f"{get_val('toiture_protection')} + Buddy system"})
                if get_val("p_points_chauds"):
                    tableau_data.append({"Activity / Activité": "Hot Work / Point Chaud", "Risk / Risque": "Fire / Incendie", "Prevention / Prévention": f"Visor EN166B + Extinguishers + Watch {get_val('chaud_vigie_nom')}"})
                if get_val("p_meuleuse"):
                    tableau_data.append({"Activity / Activité": "Angle Grinder / Meuleuse", "Risk / Risque": "Sparks / Cuts", "Prevention / Prévention": f"Disc {get_val('meuleuse_diametre')} + Shield EN166B"})
                if get_val("p_excavation"):
                    tableau_data.append({"Activity / Activité": "Excavation / Tranchée", "Risk / Risque": "Utilities / Collapse", "Prevention / Prévention": "7 Utilities plans OK + DICT + 3 Signatures"})
                if get_val("p_grutage"):
                    tableau_data.append({"Activity / Activité": "Crane Lifting / Grutage", "Risk / Risque": "Dropped load", "Prevention / Prévention": f"Weight {get_val('grut_poids_charge')+get_val('grut_poids_acc')} {get_val('grut_unite')} + Anemometer OK"})
                if get_val("p_confine"):
                    tableau_data.append({"Activity / Activité": "Confined Space / Confiné", "Risk / Risque": "Asphyxiation / Gas", "Prevention / Prévention": f"M20 Respirator + O2 ({get_val('conf_o2')}%) + Hole Watch"})
                if get_val("p_electrique"):
                    tableau_data.append({"Activity / Activité": "Electrical Work / Électrique", "Risk / Risque": "Arc Flash", "Prevention / Prévention": "Insulating gloves + Arc Flash helmet"})
                if get_val("p_consignation"):
                    tableau_data.append({"Activity / Activité": "LOTO Isolation / Consignation", "Risk / Risque": "Residual energy", "Prevention / Prévention": f"Method {get_val('loto_ouverture_methode')}"})
                if get_val("p_systeme_risque"):
                    tableau_data.append({"Activity / Activité": "High Hazard / ATEX / Chimique", "Risk / Risque": "Chemical / Explosion", "Prevention / Prévention": "Perimeter + Safety shower + Heavy PPE"})

                if not tableau_data:
                    tableau_data.append({"Activity / Activité": "Standard General Permit", "Risk / Risque": "Baseline PDP risks", "Prevention / Prévention": "Standard site PPEs"})

                st.table(tableau_data)

            # ---------------------------------------------------------
            # 3. LISTE COMPLÈTE DES EPIS RETENUS
            # ---------------------------------------------------------
            with st.container(border=True):
                st.markdown("### 🥽 3. Selected PPEs / Équipements de Protection Individuelle")
                epis_list = []
                if get_val("epi_lunettes_chantier_en166"): epis_list.append("Safety Glasses EN166")
                if get_val("epi_visiere_idra_en166b"): epis_list.append("Face Shield EN166B")
                if get_val("epi_casque_jugulaire"): epis_list.append("Helmet with Chinstrap")
                if get_val("epi_gants_anticoupure_4x43d"): epis_list.append("Cut Gloves 4x43D")
                if get_val("epi_gants_chimiques_en374"): epis_list.append("Chemical Gloves EN374")
                if get_val("epi_gants_elec_en60903"): epis_list.append("Electrical Gloves EN60903")
                if get_val("epi_resp_cartouche_abek_en14387"): epis_list.append("ABEK Respirator")
                if get_val("epi_autre_texte"): epis_list.append(f"Other: {get_val('epi_autre_texte')}")
                
                st.write(", ".join([f"`{e}`" for e in epis_list]))

            # ---------------------------------------------------------
            # 4. DÉTAILS DENSE ET COMPLETS DES PERMIS SPÉCIFIQUES OUVERTS
            # ---------------------------------------------------------
            with st.container(border=True):
                st.markdown("### ⚙ 4. HRT Specific Permits Technical Details / Détails Techniques")
                
                if get_val("p_meuleuse"):
                    st.write(f"• **Meuleuse / Grinder :** Disc `{get_val('meuleuse_diametre')}` | Model `{get_val('meuleuse_marque')}` | Power `{get_val('meuleuse_alim')}` | Tag `{get_val('meuleuse_ref')}`")
                
                if get_val("p_hauteur"):
                    st.write(f"• **Height / Hauteur :** PIRL (`{get_val('h_pirl')}`) | MEWP (`{get_val('h_nacelle')}`) | Scaffold (`{get_val('h_echaf')}`)")
                
                if get_val("p_toiture"):
                    st.write(f"• **Roof / Toiture :** Protection `{get_val('toiture_protection')}` | Approver `{get_val('toiture_valideur')}`")
                
                if get_val("p_points_chauds"):
                    st.write(f"• **Hot Work / Point Chaud :** Extinguishers `{get_val('chaud_extincteur1')}` & `{get_val('chaud_extincteur2')}` | Fire Watch `{get_val('chaud_vigie_nom')}` | Closeout `{get_val('chaud_heure_depart')}`")
                
                if get_val("p_excavation"):
                    st.write(f"• **Excavation :** 7 Plans Checked (`{get_val('excav_plans_ht')}`) | DICT (`{get_val('excav_dict')}`) | Signatures: Manager `{get_val('excav_chef_manoeuvre')}`, Owner `{get_val('excav_do')}`, Red Helmet `{get_val('excav_casque_rouge')}`")
                
                if get_val("p_grutage"):
                    st.write(f"• **Crane / Grutage :** Total Weight `{get_val('grut_poids_charge')+get_val('grut_poids_acc')} {get_val('grut_unite')}` | Crane Tag `{get_val('grut_immat')}` | Anemometer (`{get_val('grut_anemometre')}`) | Wind `{get_val('grut_vent_val')} {get_val('grut_vent_unite')}`")
                
                if get_val("p_confine"):
                    st.write(f"• **Confined Space / Confiné :** Tank `{get_val('conf_lieu')}` | O2 `{get_val('conf_o2')}%` | Hole Watch `{get_val('conf_standby')}` | Entrant `{get_val('conf_entrant')}`")
                
                if get_val("p_electrique"):
                    st.write(f"• **Electrical / Électrique :** Inside Cabinet (`{get_val('elec_armoire')}`) | Bare Live Proximity (`{get_val('elec_voisinage_nues')}`) | E&I Lead `{get_val('elec_valideur_ei')}`")
                
                if get_val("p_consignation"):
                    st.write(f"• **LOTO Isolation :** Method `{get_val('loto_ouverture_methode')}` | Location 1 `{get_val('loto_ouvert_loc1')}` | Lock `{get_val('loto_is_elec_loc2')}`")
                
                if get_val("p_systeme_risque"):
                    st.write(f"• **High Hazard / ATEX :** Perimeter Barricaded (`{get_val('sr_balisage')}`) | Safety Shower Tested (`{get_val('sr_douche_rince')}`) | Tripartite Signatures: Operator `{get_val('sr_sign_intervenant')}`, Owner `{get_val('sr_sign_do')}`, Ops `{get_val('sr_sign_operations')}`")

            # PREPARATION OBJET FINAL
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
                st.download_button(L["download_pdf"], data=pdf_bytes, file_name=f"Permit_{permis_final['id']}.pdf", mime="application/pdf", use_container_width=True)

            with c_sub:
                if st.button(L["submit_batch"], type="primary", use_container_width=True):
                    st.session_state.permis_db.append(permis_final)
                    st.balloons(); st.success(f"Permit {permis_final['id']} submitted!"); st.session_state.kiosk_mode = "HOME"

# ==============================================================================
# INTERFACE 2 : DDS BOARD
# ==============================================================================
elif "DDS Board" in role:
    st.markdown("<div class='pg-header' style='background: #0f172a;'><h2>DDS BOARD — BATCH VALIDATION</h2></div>", unsafe_allow_html=True)
    if st.button("✅ APPROVE 07:30 AM BATCH", type="primary"):
        for p in st.session_state.permis_db: p["statut"] = "VALIDATED"
        st.success("Batch validated!")

    for p in st.session_state.permis_db:
        with st.expander(f"Permit {p['id']} - {p['societe']} ({p['statut']})"):
            st.write(f"**Zone :** {p['zone']} | **N2 :** {p['n2']}")
            st.table(p.get("tableau_risques", []))
            pdf_valid_bytes = generer_pdf_bytes(p)
            st.download_button("📄 PDF", data=pdf_valid_bytes, file_name=f"Permit_{p['id']}.pdf", mime="application/pdf", key=f"btn_{p['id']}")

# ==============================================================================
# INTERFACE 3 : FIELD INSPECTION
# ==============================================================================
else:
    st.markdown("<div class='pg-header' style='background: #b91c1c;'><h2>FIELD AUDIT & QR CODE — RED HELMET</h2></div>", unsafe_allow_html=True)
    if st.session_state.permis_db:
        pt_sel = st.selectbox("Select permit / Permis scanné :", [p["id"] for p in st.session_state.permis_db])
        p = next(p for p in st.session_state.permis_db if p["id"] == pt_sel)
        
        st.write(f"### Permit Ref : {p['id']} ({p['statut']})")
        st.write(f"**Company :** {p['societe']} | **PDP :** {p['pdp']}")
        st.table(p.get("tableau_risques", []))
        
        if st.button("✍️ Validate Hot Work Patrol (60 min)"):
            st.success("Patrol validated by Red Helmet Lead.")
    else:
        st.info("No permits issued yet.")
