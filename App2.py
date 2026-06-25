import streamlit as st
import pandas as pd
import zipfile
from io import BytesIO
import re


# TITLE
st.set_page_config(
    page_title="Segments Builder",
    layout="wide"
)

# HEADER
col1, col2 = st.columns([1, 4])
with col1:
    st.image("logo_moov_africa.jfif", width=80)

with col2:
    st.markdown("### Segments Builder")
    st.markdown("Chargez une base de données et obtenez vos segments.")

st.divider()


# FUNCTIONS

def load_file(uploaded_file):
    """Lecture des fichiers CSV / Excel / XLSB"""

    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)

    elif file_name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)

    elif file_name.endswith(".xlsb"):
        df = pd.read_excel(uploaded_file, engine="pyxlsb")

    else:
        st.error("Format non supporté")
        return None

    return df


def clean_filename(text):
    """Nettoyage des noms de fichiers"""
    text = str(text)
    return re.sub(r'[\\/*?:"<>| ]', "_", text)


def create_zip(df, segment_column, selected_columns, file_format, prefix):
    """Création du ZIP contenant tous les segments"""

    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:

        unique_values = df[segment_column].dropna().unique()

        progress = st.progress(0)

        for i, value in enumerate(unique_values):

            data = df[df[segment_column] == value]

            # colonnes sélectionnées
            data = data[selected_columns]

            safe_value = clean_filename(value)
            filename = f"{prefix}{safe_value}"

            buffer = BytesIO()

            # FORMAT EXCEL
            if file_format == "Excel (.xlsx)":
                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    data.to_excel(writer, index=False)
                extension = ".xlsx"

            # FORMAT CSV
            else:
                data.to_csv(buffer, index=False)
                extension = ".csv"

            zip_file.writestr(filename + extension, buffer.getvalue())

            progress.progress((i + 1) / len(unique_values))

    return zip_buffer


# SIDEBAR (CONFIG)

st.sidebar.header("⚙️ Paramètres")

uploaded_file = st.sidebar.file_uploader(
    "Importer un fichier",
    type=["csv", "xlsx", "xlsb"]
)


# MAIN APP

if uploaded_file is not None:

    df = load_file(uploaded_file)

    if df is not None:

        
        # SIDEBAR CONFIG CONTINUE
        
        segment_column = st.sidebar.selectbox(
            "Variable de segmentation",
            df.columns
        )

        mode = st.sidebar.radio(
            "Colonnes à exporter",
            ["Toutes les colonnes", "Choisir des colonnes"]
        )

        if mode == "Toutes les colonnes":
            selected_columns = list(df.columns)
        else:
            selected_columns = st.sidebar.multiselect(
                "Sélection des colonnes",
                df.columns,
                default=list(df.columns)
            )

        file_format = st.sidebar.radio(
            "Format de sortie",
            ["Excel (.xlsx)", "CSV (.csv)"]
        )

        prefix = st.sidebar.text_input(
            "Préfixe du fichier",
            "20260625_SEGMENT_"
        )

        generate = st.sidebar.button("🚀 Générer les segments")


        # MAIN DISPLAY

        st.subheader("📊 Aperçu des données")
        st.dataframe(df.head())

        col1, col2 = st.columns(2)
        col1.metric("Nombre de lignes", len(df))
        col2.metric("Nombre de colonnes", len(df.columns))

        st.divider()


        # SEGMENT STATS

        st.subheader("📦 Distribution des segments")

        counts = df[segment_column].value_counts()

        st.dataframe(
            counts.reset_index().rename(
                columns={
                    "index": "Segment",
                    segment_column: "Volume"
                }
            )
        )

        st.divider()


        # GENERATION

        if generate:

            st.info("Génération en cours...")

            zip_buffer = create_zip(
                df,
                segment_column,
                selected_columns,
                file_format,
                prefix
            )

            st.success("Segments générés avec succès")

            st.download_button(
                label="📥 Télécharger tous les segments (ZIP)",
                data=zip_buffer.getvalue(),
                file_name="segments.zip",
                mime="application/zip"
            )

else:
    st.info(" Importez un fichier")

# FOOTER
# =========================
st.divider()
st.markdown(
    "<center><small>Moov Africa (GVC) – Moov Money</small></center>",
    unsafe_allow_html=True
)