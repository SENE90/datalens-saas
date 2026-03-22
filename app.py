import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import hashlib
import json
import datetime
import warnings
warnings.filterwarnings("ignore")

# ── Configuration Stripe ──────────────────────────────────────────────────────
STRIPE_PAYMENT_LINK = "https://buy.stripe.com/test_cNi8wQ0Cuctp8r93Ol5AQ00"
STRIPE_PRICE        = "9€/mois"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DataLens Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'DM Serif Display', serif; }
section[data-testid="stSidebar"] { background: #0f0f0f; border-right: 1px solid #222; }
section[data-testid="stSidebar"] * { color: #e0ddd5 !important; }
[data-testid="metric-container"] {
    background: #f7f5f0; border: 1px solid #e0ddd5;
    border-radius: 12px; padding: 16px !important;
}
[data-testid="stFileUploadDropzone"] {
    border: 2px dashed #c8c4bb !important;
    border-radius: 16px !important; background: #faf9f6 !important;
}
.stDownloadButton > button {
    background: #0f0f0f !important; color: #fff !important;
    border-radius: 8px !important; border: none !important;
    font-weight: 500; padding: 10px 24px;
}
.auth-box {
    max-width: 440px; margin: 0 auto;
    background: #fff; border: 1px solid #e0ddd5;
    border-radius: 16px; padding: 40px;
}
.plan-free {
    background: #f7f5f0; border: 1px solid #e0ddd5;
    border-radius: 12px; padding: 20px; text-align: center;
}
.plan-pro {
    background: #0f0f0f; color: #fff;
    border-radius: 12px; padding: 20px; text-align: center;
}
.usage-bar-bg {
    background: #e0ddd5; border-radius: 20px;
    height: 8px; width: 100%; margin: 8px 0;
}
.stAlert { border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# BASE DE DONNÉES SIMULÉE (remplacée par Supabase en production)
# ══════════════════════════════════════════════════════════════════════════════

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_users_db():
    if "users_db" not in st.session_state:
        st.session_state["users_db"] = {
            "demo@datalens.com": {
                "password": hash_password("demo1234"),
                "name": "Utilisateur Demo",
                "plan": "free",
                "analyses_count": 2,
                "analyses_limit": 5,
                "created_at": "2026-03-20",
                "history": []
            }
        }
    return st.session_state["users_db"]

def get_user(email):
    db = get_users_db()
    return db.get(email)

def create_user(email, password, name):
    db = get_users_db()
    if email in db:
        return False, "Cet email est déjà utilisé."
    db[email] = {
        "password": hash_password(password),
        "name": name,
        "plan": "free",
        "analyses_count": 0,
        "analyses_limit": 5,
        "created_at": datetime.date.today().strftime("%Y-%m-%d"),
        "history": []
    }
    return True, "Compte créé avec succès !"

def login_user(email, password):
    user = get_user(email)
    if not user:
        return False, "Email introuvable."
    if user["password"] != hash_password(password):
        return False, "Mot de passe incorrect."
    return True, user

def add_analysis(email, filename):
    db = get_users_db()
    if email in db:
        db[email]["analyses_count"] += 1
        db[email]["history"].append({
            "file": filename,
            "date": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        })

def upgrade_to_pro(email):
    db = get_users_db()
    if email in db:
        db[email]["plan"] = "pro"
        db[email]["analyses_limit"] = 999999

# ══════════════════════════════════════════════════════════════════════════════
# PAGES D'AUTHENTIFICATION
# ══════════════════════════════════════════════════════════════════════════════

def show_auth_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("# 📊 DataLens Pro")
        st.markdown("#### Analysez vos données. Partout. Tout le temps.")
        st.markdown("<br>", unsafe_allow_html=True)

        tab_login, tab_signup = st.tabs(["Se connecter", "Créer un compte"])

        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            email    = st.text_input("Email", placeholder="vous@email.com", key="login_email")
            password = st.text_input("Mot de passe", type="password", key="login_pw")

            if st.button("Se connecter", use_container_width=True, type="primary"):
                if not email or not password:
                    st.error("Remplissez tous les champs.")
                else:
                    ok, result = login_user(email, password)
                    if ok:
                        st.session_state["logged_in"]   = True
                        st.session_state["user_email"]  = email
                        st.session_state["user_data"]   = result
                        st.rerun()
                    else:
                        st.error(result)

            st.markdown("<br>", unsafe_allow_html=True)
            st.info("💡 Compte demo : demo@datalens.com / demo1234")

        with tab_signup:
            st.markdown("<br>", unsafe_allow_html=True)
            name      = st.text_input("Prénom et nom", placeholder="Pape Sene", key="signup_name")
            email_s   = st.text_input("Email", placeholder="vous@email.com", key="signup_email")
            password_s = st.text_input("Mot de passe", type="password",
                                        placeholder="8 caractères minimum", key="signup_pw")
            password_s2 = st.text_input("Confirmer le mot de passe", type="password", key="signup_pw2")

            if st.button("Créer mon compte gratuit", use_container_width=True, type="primary"):
                if not all([name, email_s, password_s, password_s2]):
                    st.error("Remplissez tous les champs.")
                elif password_s != password_s2:
                    st.error("Les mots de passe ne correspondent pas.")
                elif len(password_s) < 8:
                    st.error("Le mot de passe doit contenir au moins 8 caractères.")
                elif "@" not in email_s:
                    st.error("Email invalide.")
                else:
                    ok, msg = create_user(email_s, password_s, name)
                    if ok:
                        st.success(msg)
                        ok2, result2 = login_user(email_s, password_s)
                        if ok2:
                            st.session_state["logged_in"]  = True
                            st.session_state["user_email"] = email_s
                            st.session_state["user_data"]  = result2
                            st.rerun()
                    else:
                        st.error(msg)

        st.markdown("<br><br>")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown("**🆓 Gratuit**\n\n5 analyses/mois")
        with col_b:
            st.markdown("**⚡ Pro — 9€/mois**\n\nAnalyses illimitées")
        with col_c:
            st.markdown("**📥 Export**\n\nPDF + Excel")

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR UTILISATEUR CONNECTÉ
# ══════════════════════════════════════════════════════════════════════════════

def show_sidebar(user):
    with st.sidebar:
        st.markdown("## 📊 DataLens Pro")
        st.markdown("---")

        # Profil
        initials = "".join([n[0].upper() for n in user["name"].split()[:2]])
        st.markdown(f"""
        <div style='display:flex;align-items:center;gap:10px;margin-bottom:12px'>
          <div style='width:36px;height:36px;border-radius:50%;background:#534AB7;
                      display:flex;align-items:center;justify-content:center;
                      color:#fff;font-weight:600;font-size:13px;flex-shrink:0'>{initials}</div>
          <div>
            <div style='font-weight:500;font-size:14px'>{user['name']}</div>
            <div style='font-size:11px;opacity:.6'>{st.session_state['user_email']}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Badge plan
        if user["plan"] == "pro":
            st.markdown("""<div style='background:#534AB7;color:#fff;border-radius:20px;
                          padding:4px 12px;font-size:11px;font-weight:600;
                          display:inline-block;margin-bottom:8px'>⚡ Plan Pro</div>""",
                        unsafe_allow_html=True)
        else:
            st.markdown("""<div style='background:#f7f5f0;color:#0f0f0f;border-radius:20px;
                          padding:4px 12px;font-size:11px;font-weight:600;
                          display:inline-block;margin-bottom:8px'>🆓 Plan Gratuit</div>""",
                        unsafe_allow_html=True)

        st.markdown("---")

        # Usage
        if user["plan"] == "free":
            used  = user["analyses_count"]
            limit = user["analyses_limit"]
            pct   = min(int(used / limit * 100), 100)
            color = "#e74c3c" if pct >= 80 else "#f39c12" if pct >= 60 else "#27ae60"
            st.markdown(f"**Analyses ce mois**")
            st.markdown(f"""
            <div class='usage-bar-bg'>
              <div style='background:{color};border-radius:20px;height:8px;width:{pct}%'></div>
            </div>
            <div style='font-size:12px;opacity:.7'>{used} / {limit} utilisées</div>
            """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            st.markdown(
                f'<a href="{STRIPE_PAYMENT_LINK}" target="_blank" style="'                f'display:block;background:#635bff;color:#fff;text-align:center;'                f'padding:10px;border-radius:8px;font-size:13px;font-weight:600;'                f'text-decoration:none;margin-top:4px">⚡ Passer au Pro — {STRIPE_PRICE}</a>',
                unsafe_allow_html=True
            )

        st.markdown("---")

        # Options import
        st.markdown("### Options d'import")
        sep_choice      = st.selectbox("Séparateur", [",", ";", "\\t", "|"])
        encoding_choice = st.selectbox("Encodage", ["utf-8", "latin-1", "utf-8-sig"])

        st.markdown("---")

        # Historique
        if user.get("history"):
            st.markdown("### Analyses récentes")
            for h in reversed(user["history"][-5:]):
                st.markdown(f"<div style='font-size:12px;padding:4px 0;border-bottom:0.5px solid #333'>"
                            f"📄 {h['file'][:20]}<br>"
                            f"<span style='opacity:.5'>{h['date']}</span></div>",
                            unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Se déconnecter", use_container_width=True):
            for key in ["logged_in", "user_email", "user_data", "cleaned", "show_upgrade"]:
                st.session_state.pop(key, None)
            st.rerun()

        st.markdown(
            "<small style='opacity:.4'>DataLens Pro v2.0</small>",
            unsafe_allow_html=True
        )

    return sep_choice, encoding_choice

# ══════════════════════════════════════════════════════════════════════════════
# PAGE UPGRADE
# ══════════════════════════════════════════════════════════════════════════════

def show_upgrade_page():
    st.markdown("## ⚡ Passez au Plan Pro")
    st.markdown("Débloquez toutes les fonctionnalités sans limite.")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class='plan-free'>
          <div style='font-size:13px;font-weight:600;color:#888;margin-bottom:8px'>GRATUIT</div>
          <div style='font-size:36px;font-weight:700'>0€</div>
          <div style='font-size:13px;color:#888;margin-bottom:16px'>Pour toujours</div>
          <div style='text-align:left;font-size:14px'>
            ✅ 5 analyses par mois<br>
            ✅ Export PDF<br>
            ✅ Export Excel<br>
            ❌ Historique limité<br>
            ❌ Support prioritaire<br>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class='plan-pro'>
          <div style='font-size:13px;font-weight:600;color:#AFA9EC;margin-bottom:8px'>PRO ⭐</div>
          <div style='font-size:36px;font-weight:700;color:#fff'>9€</div>
          <div style='font-size:13px;color:#888;margin-bottom:16px'>par mois</div>
          <div style='text-align:left;font-size:14px;color:#e0ddd5'>
            ✅ Analyses illimitées<br>
            ✅ Export PDF + Excel<br>
            ✅ Historique complet<br>
            ✅ Prédiction ML auto<br>
            ✅ Support prioritaire<br>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f'<a href="{STRIPE_PAYMENT_LINK}" target="_blank" style="'            f'display:block;background:#635bff;color:#fff;text-align:center;'            f'padding:14px;border-radius:8px;font-size:15px;font-weight:600;'            f'text-decoration:none;margin-top:8px">🚀 Payer 9€/mois — Activer le Plan Pro</a>',
            unsafe_allow_html=True
        )
        st.caption("Paiement sécurisé via Stripe · Annulation à tout moment")

    st.markdown("<br>")
    if st.button("← Retour à l'analyse", use_container_width=False):
        st.session_state["show_upgrade"] = False
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE PRINCIPALE — ANALYSE
# ══════════════════════════════════════════════════════════════════════════════

def show_main_app(user, sep_choice, encoding_choice):

    st.markdown("# DataLens Pro")
    st.markdown("#### Transformez vos données brutes en insights en quelques secondes.")
    st.markdown("---")

    # Vérifier limite
    if user["plan"] == "free" and user["analyses_count"] >= user["analyses_limit"]:
        st.error("🔒 Vous avez atteint votre limite de 5 analyses gratuites ce mois.")
        st.markdown("Passez au **Plan Pro** pour continuer à analyser sans limite.")
        st.markdown(
            f'<a href="{STRIPE_PAYMENT_LINK}" target="_blank" style="'            f'display:inline-block;background:#635bff;color:#fff;'            f'padding:12px 24px;border-radius:8px;font-size:14px;font-weight:600;'            f'text-decoration:none;margin-top:8px">⚡ Passer au Pro — {STRIPE_PRICE}</a>',
            unsafe_allow_html=True
        )
        st.stop()

    # Upload
    uploaded_file = st.file_uploader(
        "📂 Glissez-déposez votre fichier CSV ici",
        type=["csv"],
        help="Fichiers CSV jusqu'à 200 Mo"
    )

    if uploaded_file is None:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **Analyse automatique :**
            - 🔢 Statistiques descriptives complètes
            - 🚨 Détection valeurs manquantes & outliers
            - 📈 Graphiques Plotly interactifs
            - 🔗 Matrice de corrélation
            """)
        with col2:
            st.markdown("""
            **Fonctionnalités Pro :**
            - 🧹 Nettoyage automatique
            - 🎯 Filtre de colonnes
            - 📥 Export Excel multi-onglets
            - 🤖 Prédiction ML (bientôt)
            """)
        st.stop()

    # Chargement
    sep = "\t" if sep_choice == "\\t" else sep_choice
    try:
        df_raw = pd.read_csv(uploaded_file, sep=sep, encoding=encoding_choice)
    except Exception as e:
        st.error(f"Erreur lors du chargement : {e}")
        st.stop()

    if df_raw.empty:
        st.error("Le fichier CSV est vide ou mal formaté.")
        st.stop()

    # Compter l'analyse
    add_analysis(st.session_state["user_email"], uploaded_file.name)
    db = get_users_db()
    st.session_state["user_data"] = db[st.session_state["user_email"]]

    # ── Nettoyage ────────────────────────────────────────────────────────────
    with st.expander("🧹 Nettoyage automatique des données", expanded=False):
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            remove_dup = st.checkbox("Supprimer les doublons",
                                      value=df_raw.duplicated().sum() > 0)
        with col_b:
            fill_method = st.selectbox("Remplir les NaN",
                                        ["Ne pas remplir","Moyenne","Médiane","0","Supprimer les lignes"])
        with col_c:
            strip_spaces = st.checkbox("Supprimer espaces", value=True)
        with col_d:
            fix_types = st.checkbox("Corriger les types", value=True)

        apply_clean = st.button("✨ Appliquer le nettoyage", type="primary")
        if apply_clean:
            st.session_state["cleaned"] = True

    df = df_raw.copy()
    if st.session_state.get("cleaned", False):
        before = df.shape[0]
        if remove_dup:   df = df.drop_duplicates()
        if strip_spaces:
            oc = df.select_dtypes(include="object").columns
            df[oc] = df[oc].apply(lambda c: c.str.strip())
        if fix_types:
            for col in df.select_dtypes(include="object").columns:
                try: df[col] = pd.to_numeric(df[col])
                except Exception: pass
        if fill_method == "Moyenne":
            n = df.select_dtypes(include=np.number).columns
            df[n] = df[n].fillna(df[n].mean())
        elif fill_method == "Médiane":
            n = df.select_dtypes(include=np.number).columns
            df[n] = df[n].fillna(df[n].median())
        elif fill_method == "0":       df = df.fillna(0)
        elif fill_method == "Supprimer les lignes": df = df.dropna()
        st.success(f"✅ {before - df.shape[0]} lignes supprimées · {df.isnull().sum().sum()} NaN restants")

    # ── Filtre colonnes ───────────────────────────────────────────────────────
    with st.expander("🎯 Sélectionner les colonnes", expanded=False):
        all_cols = df.columns.tolist()
        selected_cols = st.multiselect("Colonnes", options=all_cols, default=all_cols)
        if not selected_cols: selected_cols = all_cols
    df = df[selected_cols]

    # ── Métriques ─────────────────────────────────────────────────────────────
    num_cols   = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols   = df.select_dtypes(include="object").columns.tolist()
    missing    = df.isnull().sum().sum()
    miss_pct   = round(missing / df.size * 100, 1) if df.size > 0 else 0
    duplicates = df.duplicated().sum()

    st.markdown("### Vue d'ensemble")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Lignes",        f"{df.shape[0]:,}")
    c2.metric("Colonnes",      f"{df.shape[1]}")
    c3.metric("Numériques",    f"{len(num_cols)}")
    c4.metric("Valeurs manq.", f"{missing} ({miss_pct}%)")
    c5.metric("Doublons",      f"{duplicates}")
    st.markdown("---")

    # ── Onglets ───────────────────────────────────────────────────────────────
    tabs = st.tabs([
        "📋 Données", "📊 Statistiques", "📈 Visualisations",
        "🔗 Corrélations", "🚨 Qualité", "📄 PDF", "📥 Excel"
    ])

    with tabs[0]:
        n_rows = st.slider("Lignes à afficher", 5, min(100, len(df)), 10)
        st.dataframe(df.head(n_rows), use_container_width=True)
        dtype_df = pd.DataFrame({
            "Colonne": df.columns, "Type": df.dtypes.astype(str).values,
            "Non-nuls": df.count().values, "Nuls": df.isnull().sum().values,
            "% Nuls": (df.isnull().mean()*100).round(1).astype(str).add("%").values,
        })
        st.dataframe(dtype_df, use_container_width=True, hide_index=True)

    with tabs[1]:
        if num_cols:
            desc = df[num_cols].describe().T
            desc["skewness"] = df[num_cols].skew().round(3)
            desc["kurtosis"] = df[num_cols].kurtosis().round(3)
            st.dataframe(desc.style.format("{:.3f}", na_rep="—"), use_container_width=True)
        if cat_cols:
            sel = st.selectbox("Colonne catégorielle", cat_cols)
            vc  = df[sel].value_counts().head(20)
            col1, col2 = st.columns([1,2])
            with col1:
                st.dataframe(vc.reset_index().rename(columns={sel:"Valeur","count":"Fréquence"}),
                             hide_index=True, use_container_width=True)
            with col2:
                fig = px.bar(x=vc.values, y=vc.index, orientation="h",
                              color=vc.values, color_continuous_scale="Blues",
                              title=f"Top valeurs — {sel}")
                fig.update_layout(coloraxis_showscale=False,
                                   plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                fig.update_yaxes(autorange="reversed")
                st.plotly_chart(fig, use_container_width=True)

    with tabs[2]:
        if num_cols:
            viz_col  = st.selectbox("Colonne", num_cols)
            viz_type = st.radio("Type", ["Histogramme","Box plot","Violin","Scatter"], horizontal=True)
            data_col = df[viz_col].dropna(); fig_viz = None
            if viz_type == "Histogramme":
                fig_viz = px.histogram(df, x=viz_col, nbins=40, marginal="box",
                                        color_discrete_sequence=["#2d2d2d"],
                                        title=f"Distribution — {viz_col}")
                fig_viz.add_vline(x=data_col.mean(), line_dash="dash", line_color="#e74c3c",
                                   annotation_text=f"Moy: {data_col.mean():.2f}")
                fig_viz.add_vline(x=data_col.median(), line_dash="dot", line_color="#3498db",
                                   annotation_text=f"Méd: {data_col.median():.2f}")
            elif viz_type == "Box plot":
                fig_viz = px.box(df, y=viz_col, points="outliers",
                                  color_discrete_sequence=["#2d2d2d"], title=f"Box — {viz_col}")
            elif viz_type == "Violin":
                fig_viz = px.violin(df, y=viz_col, box=True, points="outliers",
                                     color_discrete_sequence=["#534AB7"], title=f"Violin — {viz_col}")
            else:
                if len(num_cols) >= 2:
                    col_y = st.selectbox("Axe Y", [c for c in num_cols if c != viz_col])
                    cc    = st.selectbox("Couleur", ["Aucune"] + cat_cols)
                    fig_viz = px.scatter(df, x=viz_col, y=col_y, opacity=0.7,
                                          color=None if cc=="Aucune" else cc,
                                          trendline="ols", title=f"{viz_col} vs {col_y}")
            if fig_viz:
                fig_viz.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_viz, use_container_width=True)

    with tabs[3]:
        if len(num_cols) >= 2:
            corr    = df[num_cols].corr()
            fig_c   = px.imshow(corr, color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                                 text_auto=".2f", aspect="auto", title="Corrélations de Pearson")
            fig_c.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_c, use_container_width=True)
        else:
            st.warning("Il faut au moins 2 colonnes numériques.")

    with tabs[4]:
        miss_series = df.isnull().sum(); miss_series = miss_series[miss_series > 0]
        if miss_series.empty:
            st.success("✅ Aucune valeur manquante !")
        else:
            st.error(f"⚠️ {len(miss_series)} colonne(s) avec des valeurs manquantes")
            miss_df = pd.DataFrame({
                "Colonne": miss_series.index,
                "Manquantes": miss_series.values,
                "% total": (miss_series/len(df)*100).round(1).values
            })
            st.dataframe(miss_df, hide_index=True, use_container_width=True)
        st.markdown("---")
        if duplicates == 0: st.success("✅ Aucun doublon !")
        else: st.warning(f"⚠️ {duplicates} doublon(s)")
        if num_cols:
            st.markdown("#### Outliers IQR")
            out_info = []
            for col in num_cols:
                Q1=df[col].quantile(.25); Q3=df[col].quantile(.75); IQR=Q3-Q1
                n_o=((df[col]<Q1-1.5*IQR)|(df[col]>Q3+1.5*IQR)).sum()
                out_info.append({"Colonne":col,"Outliers":n_o,"% total":round(n_o/len(df)*100,1)})
            st.dataframe(pd.DataFrame(out_info).sort_values("Outliers",ascending=False),
                         use_container_width=True, hide_index=True)

    with tabs[5]:
        if st.button("🚀 Générer le rapport PDF", use_container_width=True):
            with st.spinner("Génération…"):
                buf = io.BytesIO()
                with PdfPages(buf) as pdf:
                    fig = plt.figure(figsize=(11.69,8.27)); fig.patch.set_facecolor("#0f0f0f")
                    ax  = fig.add_subplot(111); ax.axis("off"); ax.set_facecolor("#0f0f0f")
                    ax.text(0.5,0.65,"DataLens Pro",ha="center",fontsize=60,fontweight="bold",
                            color="white",transform=ax.transAxes)
                    ax.text(0.5,0.50,"Rapport d'Analyse",ha="center",fontsize=22,
                            color="#a8a8a8",transform=ax.transAxes)
                    ax.text(0.5,0.38,f"Fichier : {uploaded_file.name}",ha="center",
                            fontsize=14,color="#6b6b6b",transform=ax.transAxes)
                    ax.text(0.5,0.28,f"Généré par : {user['name']} · {datetime.date.today()}",
                            ha="center",fontsize=12,color="#534AB7",transform=ax.transAxes)
                    pdf.savefig(fig,bbox_inches="tight"); plt.close()
                    if num_cols:
                        n=len(num_cols); cpr=3; rws=(n+cpr-1)//cpr
                        fig,axes=plt.subplots(rws,cpr,figsize=(11.69,3.2*rws))
                        fig.suptitle("Distributions",fontsize=14,fontweight="bold")
                        af=np.array(axes).flatten() if n>1 else [axes]
                        for i,col in enumerate(num_cols):
                            ax=af[i]; d=df[col].dropna()
                            ax.hist(d,bins=30,color="#2d2d2d",edgecolor="white",lw=0.3)
                            ax.set_title(col,fontsize=8,fontweight="bold"); ax.tick_params(labelsize=6)
                        for j in range(i+1,len(af)): af[j].set_visible(False)
                        plt.tight_layout(); pdf.savefig(fig,bbox_inches="tight"); plt.close()
                buf.seek(0)
            st.success("✅ PDF prêt !")
            st.download_button("⬇️ Télécharger le PDF", data=buf,
                                file_name=f"rapport_{uploaded_file.name.replace('.csv','')}.pdf",
                                mime="application/pdf", use_container_width=True)

    with tabs[6]:
        export_opts = st.multiselect("Contenu",
            ["Données","Statistiques","Corrélations","Manquants","Outliers"],
            default=["Données","Statistiques","Corrélations"])
        if st.button("📥 Générer Excel", use_container_width=True, type="primary"):
            with st.spinner("Génération…"):
                ebuf = io.BytesIO()
                with pd.ExcelWriter(ebuf, engine="openpyxl") as writer:
                    if "Données"       in export_opts: df.to_excel(writer,sheet_name="Données",index=False)
                    if "Statistiques"  in export_opts and num_cols:
                        df[num_cols].describe().T.to_excel(writer,sheet_name="Statistiques")
                    if "Corrélations"  in export_opts and len(num_cols)>=2:
                        df[num_cols].corr().round(4).to_excel(writer,sheet_name="Corrélations")
                    if "Manquants"     in export_opts:
                        pd.DataFrame({"Colonne":df.columns,
                                      "Manquantes":df.isnull().sum().values,
                                      "%":(df.isnull().mean()*100).round(2).values}
                        ).to_excel(writer,sheet_name="Manquants",index=False)
                ebuf.seek(0)
            st.success("✅ Excel prêt !")
            st.download_button("⬇️ Télécharger Excel", data=ebuf,
                                file_name=f"analyse_{uploaded_file.name.replace('.csv','')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# ROUTEUR PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

if not st.session_state.get("logged_in"):
    show_auth_page()
else:
    user = st.session_state["user_data"]
    sep_choice, encoding_choice = show_sidebar(user)

    if st.session_state.get("show_upgrade"):
        show_upgrade_page()
    else:
        show_main_app(user, sep_choice, encoding_choice)
