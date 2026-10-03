"""
Application PDF Analyzer & Anonymizer - Interface Streamlit
"""

import streamlit as st
import os
import tempfile
from datetime import datetime
from pdf_reader import PDFReader
from anonymizer import Anonymizer, PATTERNS

# Configuration de la page
st.set_page_config(
    page_title="PDF Analyzer & Anonymizer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Titre et description
st.title("📄 PDF Analyzer & Anonymizer")
st.markdown("---")

with st.sidebar:
    st.header("⚙️ Paramètres")
    
    # Sélection du mode
    mode = st.radio(
        "Mode d'opération",
        ["Extract only", "Anonymize", "Both (extract + anonymize)"],
        help="Choisissez si vous voulez juste extraire le texte ou l'anonymiser aussi"
    )
    
    # Langue
    language = st.selectbox(
        "Langage du document",
        ["Français (fr)", "English (en)"],
        index=0
    )
    lang_code = language.split("(")[1].split(")")[0]
    
    # Patterns personnalisés
    st.markdown("---")
    st.subheader("Patterns personnalisés")
    custom_pattern = st.text_input("Pattern regex", placeholder="Ex: \\d{3}-\\d{2}-\\d{4}")
    custom_replacement = st.text_input("Remplacement", value="[ID]")
    
    add_custom = st.button("Ajouter pattern")
    if add_custom and custom_pattern:
        st.success(f"Pattern '{custom_pattern}' ajouté")
    
    st.markdown("---")
    st.subheader("Statistiques")
    if "stats" in st.session_state:
        st.info(f"""
        - Pages analysées: {st.session_state.stats['pages_analysed']}
        - Caractères totaux: {st.session_state.stats['chars_total']:,}
        - Caractères anonymisés: {st.session_state.stats['chars_anonymized']:,}
        - Taux de réduction: {st.session_state.stats['reduction_pct']:.1f}%
        """)

# Zone principale
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📤 Téléverser un PDF")
    uploaded_file = st.file_uploader(
        "Choisir un fichier PDF",
        type=["pdf"],
        help="Sélectionnez un fichier PDF à analyser et/ou anonymiser"
    )
    
    if uploaded_file is not None:
        st.info(f"✓ Fichier: {uploaded_file.name} ({uploaded_file.size/1024:.1f} Ko)")
        
        # Bouton de traitement
        if st.button("🚀 Traiter le document", type="primary"):
            with st.spinner("Traitement en cours..."):
                # Sauvegarder le fichier temporairement
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                
                try:
                    # Initialisation de l'anonymizer
                    anonymizer = Anonymizer()
                    if custom_pattern:
                        anonymizer.add_pattern(
                            "custom", custom_pattern, custom_replacement
                        )
                    
                    # Traitement
                    from pdf_reader import PDFReader
                    reader = PDFReader(use_ocr=False, ocr_language=lang_code)
                    
                    text, metadata = reader.extract_text(tmp_path)
                    
                    # Anonymisation
                    mode_lower = mode.lower().replace(" ", "")
                    if mode_lower == "anonymize":
                        anonymized = anonymizer.anonymize(text)
                    elif mode_lower == "both":
                        anonymized = anonymizer.anonymize(text)
                        # Compter le taux de réduction
                        reduction = ((len(text) - len(anonymized)) / len(text) * 100) if text else 0
                    else:
                        anonymized = text
                        reduction = 0
                    
                    # Stockage des stats dans session
                    st.session_state.stats = {
                        "pages_analysed": metadata["pages_with_text"],
                        "chars_total": len(text),
                        "chars_anonymized": len(anonymized),
                        "reduction_pct": reduction
                    }
                    
                    # Affichage des résultats
                    st.success("✅ Traitement terminé !")
                    
                    # Onglets de résultat
                    result_tabs = st.tabs(["📄 Texte brut", "🔒 Texte anonymisé", "📊 Statistiques"])
                    
                    with result_tabs[0]:
                        st.text_area(
                            "Texte extrait",
                            value=text,
                            height=400,
                            help="Texte extrait du PDF (non anonymisé)"
                        )
                    
                    with result_tabs[1]:
                        st.text_area(
                            "Texte anonymisé",
                            value=anonymized,
                            height=400,
                            help="Texte avec données sensibles masquées"
                        )
                        
                        # Bouton de téléchargement
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        st.download_button(
                            "⬇️ Télécharger le rapport anonymisé",
                            anonymized,
                            file_name=f"rapport_anonyme_{ts}.txt",
                            mime="text/plain"
                        )
                    
                    with result_tabs[2]:
                        st.json(st.session_state.stats)
                        
                        # Afficher les types de données détectées
                        if anonymizer.custom_patterns:
                            with st.expander("Patterns détectés"):
                                for ptype, ppattern in anonymizer.custom_patterns.items():
                                    st.code(f"{ptype}: {ppattern.pattern[:50]}...")
                        
                        # Compteurs par type
                        st.markdown("#### Détections par type")
                        st.info("Types de données détectées par les patterns regex standards")
                        
                except Exception as e:
                    st.error(f"❌ Erreur durant le traitement: {str(e)}")
                    st.exception(e)
                finally:
                    # Nettoyage
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)

with col2:
    st.subheader("ℹ️ À propos")
    st.markdown("""
    **PDF Analyzer & Anonymizer**
    
    - Extrait le texte des PDFs (12 pages max recommandé)
    - Détecte et masque les données sensibles
    - Formats détectés : SSN, téléphones, emails, noms, adresses, IBAN, dates
    - Export vers fichier TXT
    
    **Patterns par défaut :** 13 types de données sensibles
    """)
    
    with st.expander("Patterns détectés par défaut"):
        for ptype, ppattern in PATTERNS.items():
            st.caption(f"• {ptype}: {ppattern.pattern[:60]}...")

# Footer
st.markdown("---")
st.caption("""🔧 **OpenClaw PDF Tools** | 
Pour toute question, consulter la documentation ou modifier les patterns d'anonymisation.""")
