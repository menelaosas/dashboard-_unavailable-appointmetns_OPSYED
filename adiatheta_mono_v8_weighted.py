"""
Dashboard για Αδιάθετα Ραντεβου - 401 ΓΣΝ Αθηνών
Εστιασμένη έκδοση για ανάλυση και ανακατανομή αδιάθετων ραντεβου
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, callback, dash_table, State
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import warnings
import os

warnings.filterwarnings('ignore')

# ══════════════════════════════════════════════════════════════════════════════
# ΦΟΡΤΩΣΗ ΔΕΔΟΜΕΝΩΝ
# ══════════════════════════════════════════════════════════════════════════════

def load_unavailable_appointments_data():
    """
    Φόρτωση πραγματικών δεδομένων με εστίαση στα αδιάθετα ραντεβου
    """
    print("📄 Φόρτωση δεδομένων αδιάθετων ραντεβου...")
    
    # Προσπάθεια φόρτωσης του CSV αρχείου
    possible_files = ['OPSY_401_clean.csv']
    df = None
    used_file = None
    
    for filename in possible_files:
        try:
            df = pd.read_csv(filename, encoding='utf-8')
            used_file = filename
            print(f"✅ Επιτυχής φόρτωση: {filename}")
            print(f"📋 Στήλες αρχείου: {list(df.columns)}")
            print(f"📏 Μέγεθος δεδομένων: {df.shape}")
            break
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(filename, encoding='latin-1')
                used_file = filename
                print(f"✅ Επιτυχής φόρτωση με latin-1 encoding: {filename}")
                break
            except Exception as e:
                print(f"❌ Σφάλμα φόρτωσης {filename}: {str(e)}")
                continue
        except Exception as e:
            print(f"❌ Σφάλμα φόρτωσης {filename}: {str(e)}")
            continue
    
    if df is None:
        print("❌ ΣΦΑΛΜΑ: Δεν βρέθηκε κανένα έγκυρο CSV αρχείο!")
        print("📋 Βεβαιωθείτε ότι έχετε ένα από τα παρακάτω αρχεία στον φάκελο:")
        for filename in possible_files:
            print(f"   - {filename}")
        return pd.DataFrame()  # Επιστροφή κενού DataFrame
    
    print("🧹 Καθαρισμός και προετοιμασία δεδομένων...")
    
    # Εκκαθάριση ονομάτων στηλών
    df.columns = df.columns.str.strip()
    
    # Διορθωμένη αντιστοίχιση στηλών
    print("🔍 Έλεγχος και αντιστοίχιση στηλών...")
    
    # Δημιουργία λεξικού για τις επιθυμητές στήλες και τα πιθανά ονόματά τους
    column_mapping = {
        'ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ': ['ΑΔΙΑΘΕΤΑ ΡΑΝΤΕΒΟΥ', 'Ο ΛΥΥ ΔΕΝ ΠΡΟΣΗΛΘΕ', 'ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ', 'unavailable', 'ΑΔΙΑΘΕΤΑ'],
        'ΔΙΑΘΕΣΙΜΑ_ΡΑΝΤΕΒΟΥ': ['ΔΙΑΘΕΣΙΜΑ ΡΑΝΤΕΒΟΥ', 'ΔΙΑΘΕΣΙΜΑ_ΡΑΝΤΕΒΟΥ', 'available', 'ΔΙΑΘΕΣΙΜΑ'],
        'ΡΑΝΤΕΒΟΥ_ΠΟΥ_ΚΛΕΙΣΤΗΚΑΝ': ['ΡΑΝΤΕΒΟΥ ΠΟΥ ΚΛΕΙΣΤΗΚΑΝ', 'ΠΡΑΓΜΑΤΟΠΟΙΗΘΗΚΑΝ', 'ΡΑΝΤΕΒΟΥ_ΠΟΥ_ΚΛΕΙΣΤΗΚΑΝ', 'booked', 'ΚΛΕΙΣΤΗΚΑΝ'],
        'ΤΜΗΜΑ': ['ΤΜΗΜΑ', 'department', 'DEPARTMENT', 'ΤΜΗΜΑΤΑ', 'DEPT'],
        'ΟΝΟΜΑ_ΟΜΑΔΑΣ': ['ΟΝΟΜΑ ΟΜΑΔΑΣ', 'ΟΜΑΔΑ', 'ΟΝΟΜΑ_ΟΜΑΔΑΣ', 'team', 'ΚΑΤΗΓΟΡΙΑ ΛΥΥ', 'ΟΜΑΔΕΣ'],
        'ΜΗΝΑΣ-ΕΤΟΣ': ['ΜΗΝΑΣ-ΕΤΟΣ', 'ΜΗΝΑΣΕΤΟΣ', 'ΜΗΝΑΣ_ΕΤΟΣ', 'MONTH-YEAR', 'date', 'DATE', 'ΜΗΝΑΣ', 'ΗΜΕΡΟΜΗΝΙΑ']
    }
    
    # Ελέγχουμε αν οι στήλες υπάρχουν ήδη ή χρειάζονται mapping
    for standard_name, possible_names in column_mapping.items():
        if standard_name in df.columns:
            print(f"   ✅ Στήλη {standard_name} υπάρχει ήδη")
        else:
            found = False
            for possible_name in possible_names:
                if possible_name in df.columns:
                    df[standard_name] = df[possible_name]
                    print(f"   ✅ Mapping: {possible_name} → {standard_name}")
                    found = True
                    break
            if not found:
                print(f"   ❌ Δεν βρέθηκε στήλη για: {standard_name}")
    
    # Έλεγχος για απαραίτητες στήλες μετά το mapping
    required_columns = ['ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ', 'ΔΙΑΘΕΣΙΜΑ_ΡΑΝΤΕΒΟΥ', 'ΤΜΗΜΑ']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"❌ ΣΦΑΛΜΑ: Λείπουν απαραίτητες στήλες: {missing_columns}")
        print("📋 Διαθέσιμες στήλες μετά το mapping:")
        for i, col in enumerate(df.columns):
            print(f"   {i+1}. {col}")
        return pd.DataFrame()
    
    # Δημιουργία στήλης ομάδας αν δεν υπάρχει
    if 'ΟΝΟΜΑ_ΟΜΑΔΑΣ' not in df.columns:
        df['ΟΝΟΜΑ_ΟΜΑΔΑΣ'] = 'ΓΕΝΙΚΗ ΟΜΑΔΑ'
        print("   ➕ Δημιουργήθηκε προεπιλεγμένη στήλη ΟΝΟΜΑ_ΟΜΑΔΑΣ")
    
    # Μετατροπή σε αριθμητικές τιμές
    numeric_cols = ['ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ', 'ΔΙΑΘΕΣΙΜΑ_ΡΑΝΤΕΒΟΥ']
    if 'ΡΑΝΤΕΒΟΥ_ΠΟΥ_ΚΛΕΙΣΤΗΚΑΝ' in df.columns:
        numeric_cols.append('ΡΑΝΤΕΒΟΥ_ΠΟΥ_ΚΛΕΙΣΤΗΚΑΝ')
    
    print("🔢 Μετατροπή αριθμητικών στηλών...")
    for col in numeric_cols:
        if col in df.columns:
            original_type = df[col].dtype
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            print(f"   ✅ {col}: {original_type} → int64")
    
    # Ημερομηνία parsing - διορθωμένο για να αναγνωρίζει το ΜΗΝΑΣΕΤΟΣ
    print("📅 Επεξεργασία ημερομηνιών...")
    
    if 'ΜΗΝΑΣ-ΕΤΟΣ' in df.columns:
        date_formats = ['%Y-%m', '%m/%Y', '%Y/%m', '%m-%Y', '%d/%m/%Y', '%Y-%m-%d']
        
        df['parsed_date'] = None
        for date_format in date_formats:
            try:
                df['parsed_date'] = pd.to_datetime(df['ΜΗΝΑΣ-ΕΤΟΣ'], format=date_format, errors='coerce')
                successful_parsing = df['parsed_date'].notna().sum()
                if successful_parsing > 0:
                    print(f"   ✅ Επιτυχής parsing με format {date_format}: {successful_parsing} εγγραφές")
                    break
            except:
                continue
        
        # Αν δεν λειτούργησε κανένας format, δοκίμασε infer
        if df['parsed_date'].isna().all():
            try:
                df['parsed_date'] = pd.to_datetime(df['ΜΗΝΑΣ-ΕΤΟΣ'], infer_datetime_format=True, errors='coerce')
                successful_parsing = df['parsed_date'].notna().sum()
                print(f"   ✅ Επιτυχής parsing με infer_datetime_format: {successful_parsing} εγγραφές")
            except:
                print("   ❌ Αποτυχία parsing ημερομηνιών")
        
        # Απάλειψη NaT values
        original_count = len(df)
        df = df.dropna(subset=['parsed_date'])
        if len(df) < original_count:
            print(f"   ⚠️ Αφαιρέθηκαν {original_count - len(df)} εγγραφές με άκυρες ημερομηνίες")
    else:
        print("   ❌ Δεν βρέθηκε στήλη ημερομηνίας - θα δημιουργηθεί προεπιλεγμένη")
        # Δημιουργία προεπιλεγμένης ημερομηνίας
        df['parsed_date'] = pd.to_datetime('2024-01-01')
        print("   ⚠️ Χρησιμοποιήθηκε προεπιλεγμένη ημερομηνία")
    
    if df.empty:
        print("❌ ΣΦΑΛΜΑ: Δεν υπάρχουν έγκυρα δεδομένα μετά την επεξεργασία")
        return pd.DataFrame()
    
    # Υπολογισμός βασικών μετρικών
    print("📊 Υπολογισμός μετρικών...")
    df['ΠΟΣΟΣΤΟ_ΑΔΙΑΘΕΤΩΝ'] = (df['ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ'] / df['ΔΙΑΘΕΣΙΜΑ_ΡΑΝΤΕΒΟΥ'].replace(0, 1) * 100).clip(0, 100)
    
    if 'ΡΑΝΤΕΒΟΥ_ΠΟΥ_ΚΛΕΙΣΤΗΚΑΝ' in df.columns:
        df['ΧΡΗΣΗ_ΡΑΝΤΕΒΟΥ'] = (df['ΡΑΝΤΕΒΟΥ_ΠΟΥ_ΚΛΕΙΣΤΗΚΑΝ'] / df['ΔΙΑΘΕΣΙΜΑ_ΡΑΝΤΕΒΟΥ'].replace(0, 1) * 100).clip(0, 100)
    
    # Κατηγοριοποίηση
    df['ΚΑΤΗΓΟΡΙΑ_ΑΔΙΑΘΕΤΩΝ'] = pd.cut(df['ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ'], 
                                       bins=[0, 5, 15, 30, float('inf')],
                                       labels=['Λίγα (0-5)', 'Μέτρια (6-15)', 'Πολλά (16-30)', 'Πάρα πολλά (30+)'])
    
    # Τελική αναφορά
    print(f"✅ Δεδομένα επεξεργάστηκαν επιτυχώς!")
    print(f"📏 Τελικό μέγεθος: {len(df)} εγγραφές")
    print(f"📊 Συνολικά αδιάθετα: {df['ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ'].sum():,}")
    print(f"📅 Εύρος ημερομηνιών: {df['parsed_date'].min().strftime('%Y-%m')} έως {df['parsed_date'].max().strftime('%Y-%m')}")
    print(f"🏥 Τμήματα: {df['ΤΜΗΜΑ'].nunique()}")
    print(f"👥 Ομάδες: {df['ΟΝΟΜΑ_ΟΜΑΔΑΣ'].nunique()}")
    
    return df

# ══════════════════════════════════════════════════════════════════════════════
# ΑΝΑΛΥΤΙΚΗ ΚΛΑΣΗ ΓΙΑ ΑΔΙΑΘΕΤΑ ΡΑΝΤΕΒΟΥ
# ══════════════════════════════════════════════════════════════════════════════

class UnavailableAppointmentsAnalyzer:
    """
    Κλάση για ανάλυση αδιάθετων ραντεβου και προτάσεις ανακατανομής
    """
    
    def __init__(self, df):
        self.df = df
    
    def calculate_unavailable_kpis(self, filtered_df=None):
        """
        Υπολογισμός KPI για αδιάθετα ραντεβου
        """
        data = filtered_df if filtered_df is not None else self.df
        
        if data.empty:
            return {}
        
        # ✅ ENSURE ALL VALUES ARE PYTHON NATIVE TYPES, NOT PANDAS OBJECTS
        total_unavailable = int(data['ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ'].sum())
        total_available = int(data['ΔΙΑΘΕΣΙΜΑ_ΡΑΝΤΕΒΟΥ'].sum())
        avg_unavailable_rate = float((total_unavailable / total_available * 100) if total_available > 0 else 0)
        
        # Τμήμα με τα περισσότερα αδιάθετα
        dept_unavailable = data.groupby('ΤΜΗΜΑ')['ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ'].sum()
        worst_dept = str(dept_unavailable.idxmax()) if not dept_unavailable.empty else "Άγνωστο"
        worst_dept_count = int(dept_unavailable.max()) if not dept_unavailable.empty else 0

        # Τμήμα με τα λιγότερα αδιάθετα
        best_dept = str(dept_unavailable.idxmin()) if not dept_unavailable.empty else "Άγνωστο"
        best_dept_count = int(dept_unavailable.min()) if not dept_unavailable.empty else 0

        
        return {
            'total_unavailable': total_unavailable,
            'total_available': total_available,
            'avg_unavailable_rate': round(avg_unavailable_rate, 1),
            'worst_dept': worst_dept,
            'worst_dept_count': worst_dept_count,
            'best_dept': best_dept,                 # ← ΝΕΟ
            'best_dept_count': best_dept_count,     # ← ΝΕΟ
            'total_departments': int(data['ΤΜΗΜΑ'].nunique()),
            'total_teams': int(data['ΟΝΟΜΑ_ΟΜΑΔΑΣ'].nunique()),
            'months_analyzed': int(data['parsed_date'].nunique())
        }
    
    def suggest_fair_redistribution(self, redistribute_ratio=0.30, max_donor_fraction=0.25):
        """
        Νέος αλγόριθμος έξυπνης ανακατανομής.
        :param redistribute_ratio: ποσοστό από το σύνολο των αδιάθετων των δοτών που θα ανακατανεμηθεί (π.χ. 0.30 = 30%)
        :param max_donor_fraction: μέγιστο ποσοστό που «δίνει» κάθε δότης σε μία μεταφορά (π.χ. 0.25 = 25%)
        """
        print(f"🔄 Αλγόριθμος ανακατανομής | ratio={redistribute_ratio:.2f}, donor_cap={max_donor_fraction:.2f}")

        summary = self.df.groupby(['ΤΜΗΜΑ', 'ΟΝΟΜΑ_ΟΜΑΔΑΣ']).agg({
            'ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ': 'mean',
            'ΔΙΑΘΕΣΙΜΑ_ΡΑΝΤΕΒΟΥ': 'mean'
        }).reset_index().round(0).astype({'ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ': int, 'ΔΙΑΘΕΣΙΜΑ_ΡΑΝΤΕΒΟΥ': int})

        if summary.empty or len(summary) < 2:
            return pd.DataFrame()

        mean_unavailable = summary['ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ'].mean()
        std_unavailable = summary['ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ'].std()
        high_threshold = mean_unavailable + (std_unavailable * 0.5)
        low_threshold  = mean_unavailable - (std_unavailable * 0.5)

        donors = summary[summary['ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ'] > high_threshold].copy()
        receivers = summary[summary['ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ'] < low_threshold].copy()
        if donors.empty or receivers.empty:
            return pd.DataFrame()

        total_to_redistribute = int(max(donors['ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ'].sum() * redistribute_ratio, len(receivers)))

        receiver_weights = []
        for _, row in receivers.iterrows():
            scarcity_weight = max(1, mean_unavailable - row['ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ'] + 1)
            capacity_weight = row['ΔΙΑΘΕΣΙΜΑ_ΡΑΝΤΕΒΟΥ'] / max(1, receivers['ΔΙΑΘΕΣΙΜΑ_ΡΑΝΤΕΒΟΥ'].max())
            total_weight = scarcity_weight * 3 + capacity_weight * 2
            receiver_weights.append(total_weight)

        receivers['ΒΑΡΟΣ'] = receiver_weights
        total_receiver_weight = sum(receiver_weights)
        if total_receiver_weight <= 0:
            return pd.DataFrame()

        receivers['ΠΟΣΟΣΤΟ'] = (receivers['ΒΑΡΟΣ'] / total_receiver_weight * 100).round(1)
        receivers['ΜΕΡΙΔΙΟ'] = (total_to_redistribute * receivers['ΒΑΡΟΣ'] / total_receiver_weight).round(0).astype(int)

        transfers = []
        donors_copy = donors.sort_values('ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ', ascending=False).copy()

        for _, receiver in receivers.iterrows():
            remaining_needed = receiver['ΜΕΡΙΔΙΟ']
            if remaining_needed <= 0:
                continue
            for donor_idx in donors_copy.index:
                if remaining_needed <= 0:
                    break
                donor = donors_copy.loc[donor_idx]
                available_from_donor = donor['ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ']
                if available_from_donor <= 0:
                    continue

                donor_cap = max(1, int(available_from_donor * max_donor_fraction))
                transfer_amount = min(remaining_needed, available_from_donor, donor_cap)

                if transfer_amount > 0:
                    donors_copy.loc[donor_idx, 'ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ'] -= transfer_amount
                    remaining_needed -= transfer_amount
                    transfers.append({
                        'Τμήμα': donor['ΤΜΗΜΑ'],
                        'Από Ομάδα': donor['ΟΝΟΜΑ_ΟΜΑΔΑΣ'],
                        'Προς Ομάδα': receiver['ΟΝΟΜΑ_ΟΜΑΔΑΣ'],
                        'Αδιάθετα Δότη (Αρχικά)': int(donor['ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ']),
                        'Αδιάθετα Δέκτη (Αρχικά)': int(receiver['ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ']),
                        'Προτεινόμενη Μεταφορά': int(transfer_amount),
                        'Νέα Αδιάθετα Δότη': int(donors_copy.loc[donor_idx, 'ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ']),
                        'Νέα Αδιάθετα Δέκτη': max(0, int(receiver['ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ'] - transfer_amount)),
                        'Βελτίωση Δέκτη': f"+{transfer_amount} (από {receiver['ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ']} → {receiver['ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ'] + transfer_amount})",
                        'Αιτιολόγηση': f"Μείωση αδιάθετων: {transfer_amount} ραντεβού από '{donor['ΟΝΟΜΑ_ΟΜΑΔΑΣ']}' στην '{receiver['ΟΝΟΜΑ_ΟΜΑΔΑΣ']}'"
                    })

        return pd.DataFrame(transfers)
    
    def create_fair_redistribution_flow_chart(self, redistribute_ratio=0.30, max_donor_fraction=0.25):
        """Διάγραμμα ροής που χρησιμοποιεί το τρέχον ratio."""
        redistribution_df = self.suggest_fair_redistribution(
            redistribute_ratio=redistribute_ratio,
            max_donor_fraction=max_donor_fraction
        )
        
        if redistribution_df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="ℹ️ Δεν χρειάζεται ανακατανομή<br><br>" +
                     "<b>Πιθανοί λόγοι:</b><br>" +
                     "• Όλες οι ομάδες έχουν παρόμοια επίπεδα αδιάθετων<br>" +
                     "• Δεν υπάρχει σημαντική διακύμανση για ανακατανομή<br>" +
                     "• Ανεπαρκή δεδομένα (λιγότερες από 2 ομάδες)<br><br>" +
                     "<i>Αλγόριθμος: Δότες = πολλά αδιάθετα, Δέκτες = λίγα αδιάθετα</i>",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=14, color="darkblue"),
                bgcolor="rgba(220,235,255,0.9)",
                bordercolor="blue",
                borderwidth=2,
                borderpad=20
            )
            fig.update_layout(
                title=dict(
                    text="<b>Έξυπνη Ανακατανομή Αδιάθετων Ραντεβου</b><br>" +
                         "<sub>Ισορροπημένη κατάσταση - δεν χρειάζεται παρέμβαση</sub>",
                    x=0.5,
                    font=dict(size=16)
                ),
                height=600,
                showlegend=False,
                xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            return fig
        
        # Δημιουργία Sankey diagram βασισμένου στις πραγματικές μεταφορές
        sources = []
        targets = []
        values = []
        labels = []
        colors = []
        
        # Συλλογή όλων των μοναδικών ομάδων
        all_donors = redistribution_df['Από Ομάδα'].unique()
        all_receivers = redistribution_df['Προς Ομάδα'].unique()
        
        # Προσθήκη δοτών
        for donor in all_donors:
            labels.append(f"ΔΟΤΗΣ: {donor}")
            colors.append('rgba(255, 150, 100, 0.8)')  # Πορτοκαλί για δότες με πολλά αδιάθετα
        
        # Προσθήκη δεκτών
        for receiver in all_receivers:
            if f"ΔΟΤΗΣ: {receiver}" not in labels:  # Αποφυγή διπλών
                labels.append(f"ΔΕΚΤΗΣ: {receiver}")
                colors.append('rgba(100, 200, 255, 0.8)')  # Γαλάζιο για δέκτες με λίγα αδιάθετα
        
        # Δημιουργία συνδέσεων
        for _, row in redistribution_df.iterrows():
            donor_label = f"ΔΟΤΗΣ: {row['Από Ομάδα']}"
            receiver_label = f"ΔΕΚΤΗΣ: {row['Προς Ομάδα']}"
            
            if donor_label in labels and receiver_label in labels:
                source_idx = labels.index(donor_label)
                target_idx = labels.index(receiver_label)
                
                sources.append(source_idx)
                targets.append(target_idx)
                values.append(row['Προτεινόμενη Μεταφορά'])
        
        if not sources:  # Fallback αν δεν υπάρχουν συνδέσεις
            fig = go.Figure()
            fig.add_annotation(
                text="Δεν υπάρχουν μεταφορές για εμφάνιση",
                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(title="Έξυπνη Ανακατανομή", height=500)
            return fig
        
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=labels,
                color=colors,
                hovertemplate='%{label}<extra></extra>'
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color=['rgba(150, 180, 200, 0.4)'] * len(sources),
                hovertemplate='<b>%{source.label}</b> → <b>%{target.label}</b><br>' +
                             'Μεταφορά: %{value} ραντεβου<br>' +
                             'Βελτίωση: -%{value} αδιάθετα για δέκτη<extra></extra>'
            )
        )])
        
        total_redistributed = sum(values)
        fig.update_layout(
            title=dict(
                text=f"<b>Έξυπνη Ανακατανομή Αδιάθετων Ραντεβου</b><br>" +
                     f"<sub>Συνολική βελτίωση: {total_redistributed} ραντεβου σε {len(redistribution_df)} μεταφορές</sub><br>" +
                     f"<sub>Αυτόματος υπολογισμός βαρών βάσει διαθέσιμων ραντεβου</sub>",
                x=0.5,
                font=dict(size=14)
            ),
            font=dict(size=11),
            height=600,
            margin=dict(t=120, b=50, l=50, r=50)
        )
        
        return fig

# ══════════════════════════════════════════════════════════════════════════════
# ΦΟΡΤΩΣΗ ΔΕΔΟΜΕΝΩΝ ΚΑΙ ΑΝΑΛΥΤΗ
# ══════════════════════════════════════════════════════════════════════════════

# Φόρτωση δεδομένων και έλεγχος επιτυχίας
print("🚀 Εκκίνηση Dashboard Αδιάθετων Ραντεβου...")
df = load_unavailable_appointments_data()

# Έλεγχος αν τα δεδομένα φορτώθηκαν επιτυχώς
if df.empty:
    print("❌ ΚΡΙΣΙΜΟ ΣΦΑΛΜΑ: Δεν φορτώθηκαν δεδομένα!")
    print("Το dashboard δεν μπορεί να λειτουργήσει χωρίς δεδομένα.")
    exit(1)

analyzer = UnavailableAppointmentsAnalyzer(df)

# Υπολογισμός εύρους ημερομηνιών για το DatePicker
min_date = df['parsed_date'].min().date()
max_date = df['parsed_date'].max().date()
print(f"📅 Εύρος ημερομηνιών για φιλτράρισμα: {min_date} έως {max_date}")

# Δημιουργία λιστών για dropdowns με ασφαλείς τιμές
unique_departments = [d for d in sorted(df['ΤΜΗΜΑ'].unique()) if pd.notna(d) and d != '']
unique_teams = [t for t in sorted(df['ΟΝΟΜΑ_ΟΜΑΔΑΣ'].unique()) if pd.notna(t) and t != '']

print(f"🏥 Τμήματα: {len(unique_departments)} ({unique_departments[:3]}...)")
print(f"👥 Ομάδες: {len(unique_teams)} ({unique_teams[:3]}...)")

# ══════════════════════════════════════════════════════════════════════════════
# DASH APP SETUP
# ══════════════════════════════════════════════════════════════════════════════

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Dashboard Αδιάθετων Ραντεβου - 401 ΓΣΝ"

# Χρωματική παλέτα
colors = {
    'primary': '#e74c3c',     # Κόκκινο για αδιάθετα
    'secondary': '#3498db',   # Μπλε
    'success': '#2ecc71',     # Πράσινο για καλές τιμές
    'warning': '#f39c12',     # Πορτοκαλί για προειδοποίηση
    'danger': '#e74c3c',      # Κόκκινο για κίνδυνο
    'light': '#ecf0f1',       # Ανοιχτό γκρι
    'dark': '#2c3e50'         # Σκούρο μπλε
}

# ══════════════════════════════════════════════════════════════════════════════
# UI COMPONENTS
# ══════════════════════════════════════════════════════════════════════════════

def create_simple_kpi_card(title, value, subtitle="", color="primary", icon="📊"):
    """Δημιουργία απλής KPI κάρτας"""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.H6([icon, " ", title], className="text-muted mb-2"),
                html.H3(str(value), className=f"text-{color} mb-1 font-weight-bold"),
                html.Small(subtitle, className="text-muted")
            ], className="text-center")
        ])
    ], className="shadow-sm mb-3 border-0", style={'borderLeft': f'4px solid var(--bs-{color})'})

def create_info_alert(content, color="info"):
    if not isinstance(content, (list, tuple)):
        content = [content]   # wrap single text into list
    return dbc.Alert(
        [html.I(className="fas fa-info-circle me-2")] + list(content),
        color=color,
        className="mb-3"
    )


# ══════════════════════════════════════════════════════════════════════════════
# MAIN LAYOUT
# ══════════════════════════════════════════════════════════════════════════════

app.layout = dbc.Container([
    
    # HEADER
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H1([
                    "🏥 Dashboard Αδιάθετων Ραντεβου"
                ], className="text-danger mb-2"),
                html.H4("401 Γενικό Στρατιωτικό Νοσοκομείο Αθηνών", 
                       className="text-muted mb-3"),
                create_info_alert([
                    html.Strong("💡 Οδηγίες: "),
                    "Μελετήστε πρώτα τις οδηγίες και συστάσεις στο τέλος του dashboard, ώστε να διασφαλίσετε τη σωστή χρήση του."
                ], "primary"),
                html.Hr()
            ])
        ])
    ]),
    
    # ΦΙΛΤΡΑ
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H5("🔍 Φίλτρα Ανάλυσης", className="mb-0")
                ]),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("📅 Περίοδος:", className="fw-bold"),
                            dcc.DatePickerRange(
                                id='date-range',
                                start_date=min_date,
                                end_date=max_date,
                                display_format='MM/YYYY',
                                style={'width': '100%'}
                            )
                        ], md=4),
                        dbc.Col([
                            html.Label([
                                "🏢 Τμήματα (πολλαπλή επιλογή):", 
                                html.Small(" • Κενό = όλα • Ctrl+Click για πολλά", 
                                         className="text-muted ms-2")
                            ], className="fw-bold"),
                            dcc.Dropdown(
                                id='dept-filter',
                                options=[{'label': d, 'value': d} for d in unique_departments],
                                value=[],  # Κενή λίστα αρχικά = όλα τα τμήματα
                                multi=True,  # Επιτρέπει πολλαπλές επιλογές
                                placeholder="Επιλέξτε τμήματα (κενό = όλα)",
                                clearable=True,
                                style={'fontSize': '14px'}
                            )
                        ], md=4),
                        dbc.Col([
                            html.Label([
                                "👥 Ομάδες (πολλαπλή επιλογή):", 
                                html.Small(" • Κενό = όλες • Ctrl+Click για πολλές", 
                                         className="text-muted ms-2")
                            ], className="fw-bold"),
                            dcc.Dropdown(
                                id='team-filter',
                                options=[{'label': t, 'value': t} for t in unique_teams],
                                value=[],  # Κενή λίστα αρχικά = όλες οι ομάδες
                                multi=True,  # Επιτρέπει πολλαπλές επιλογές
                                placeholder="Επιλέξτε ομάδες (κενό = όλες)",
                                clearable=True,
                                style={'fontSize': '14px'}
                            )
                        ], md=4)
                    ])
                ])
            ], className="mb-4")
        ])
    ]),
    
    # KPI CARDS
    html.Div(id='kpi-section'),
    
    # ΓΡΑΦΗΜΑΤΑ - Μία γραμμή με δύο μεγάλα γραφήματα
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H5("📈 Εξέλιξη Αδιάθετων Ραντεβου", className="mb-0"),
                    html.Small("Παρακολούθηση τάσης αδιάθετων στο χρόνο", className="text-muted")
                ]),
                dbc.CardBody([
                    dcc.Graph(id="trend-chart")
                ])
            ], className="shadow-sm")
        ], md=8),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H5("🏆 Κατάταξη Τμημάτων", className="mb-0"),
                    html.Small("Τμήματα με τα περισσότερα και λιγότερα αδιάθετα ραντεβου", className="text-muted")
                ]),
                dbc.CardBody([
                    dcc.Graph(id="dept-ranking")
                ])
            ], className="shadow-sm")
        ], md=4)
    ], className="mb-4"),
    
    # ΑΝΑΚΑΤΑΝΟΜΗ SECTION
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H4("📄 Δίκαιη Ανακατανομή Αδιάθετων Ραντεβου", className="mb-0"),
                    html.P("Αναλογική κατανομή σε όλες τις ομάδες με βάση τις πραγματικές ανάγκες τους", 
                           className="text-muted mb-0 mt-2")
                ]),
                dbc.CardBody([
                    # Επεξήγηση αλγορίθμου
                    dbc.Alert([
                        html.H6("🧠 Βήματα Χρήσης", className="alert-heading mb-3"),
                        html.P("1. Επιλέξτε περίοδο, το τμήμα και τις ομάδες που θέλετε να αναλύσετε.", className="mb-1"),

                        html.P([
                            "2. Ρυθμίστε το ποσοστό ανακατανομής με τον διακόπτη (slider), δηλαδή πόσα από τα «περισσευούμενα» ραντεβού των ",
                            html.Strong("δοτών"),
                            " θα μοιραστούν στους ",
                            html.Strong("δέκτες"),
                            ": μικρό ποσοστό = λίγες μεταφορές ραντεβού, μεγάλο ποσοστό = περισσότερες μεταφορές ραντεβού."
                        ], className="mb-1"),

                        html.P("3. Ελέγξτε τις προτάσεις στον πίνακα και στο διάγραμμα ροής.", className="mb-0"),
                        html.P("4. Στο τέλος διαβάστε τις συστάσεις για τη σωστή εφαρμογή τους.", className="mb-0"),
                    ], color="info", className="mb-4"),


                # Έλεγχος ποσοστού ανακατανομής
                dbc.Row([
                    dbc.Col([
                        html.Label("🎚️ Ποσοστό Ανακατανομής", className="fw-bold"),
                        dcc.Slider(
                            id='redistribution-ratio',
                            min=0.0,
                            max=0.6,
                            step=0.05,
                            value=0.30,  # default 30%
                            marks={i/100: f"{i}%" for i in range(0, 61, 10)},  # 0%,10%,...,60%
                            tooltip={"placement": "bottom", "always_visible": False}
                        ),
                        html.Small(
                            id="redistribution-ratio-text",
                            className="text-muted",
                            children="Τρέχον ποσοστό: 30%"
                        )
                    ], md=12)
                ], className="mb-3"),

                    
                    # Γράφημα ροής
                    dcc.Graph(id="fair-redistribution-flow"),
                    
                    html.Hr(),
                    
                    # Πίνακας προτάσεων
                    html.Div(id="fair-redistribution-table")
                ])
            ], className="shadow-sm")
        ])
    ], className="mb-4"),

    # ΠΙΝΑΚΑΣ ΑΔΙΑΘΕΤΩΝ ΑΝΑ ΤΜΗΜΑ ΚΑΙ ΟΜΑΔΑ
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H5("📊 Πίνακας Αδιάθετων Ραντεβου ανά Τμήμα και Ομάδα", className="mb-0"),
                    html.Small("Αναλυτικά στοιχεία αδιάθετων ραντεβου με βάση τα επιλεγμένα φίλτρα", className="text-muted")
                ]),
                dbc.CardBody([
                    html.Div(id="detailed-table-section")
                ])
            ], className="shadow-sm")
        ])
    ], className="mb-4"),
    
    # ΟΔΗΓΙΕΣ ΚΑΙ ΣΥΣΤΑΣΕΙΣ
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H5("💡 Οδηγίες και Συστάσεις", className="mb-0")
                ]),
                dbc.CardBody([
                    html.Div(id="recommendations")
                ])
            ], className="shadow-sm")
        ])
    ], className="mb-4"),
    
    # FOOTER
    html.Hr(),
    dbc.Row([
        dbc.Col([
            html.P([
                "© 2024 401 ΓΣΝ - Dashboard Αδιάθετων Ραντεβου | ",
                "Στόχος: Βελτιστοποίηση εξυπηρέτησης ασθενών"
            ], className="text-center text-muted")
        ])
    ])
    
], fluid=True, style={'backgroundColor': '#f8f9fa', 'minHeight': '100vh', 'padding': '20px'})

# ══════════════════════════════════════════════════════════════════════════════
# CALLBACKS
# ══════════════════════════════════════════════════════════════════════════════

def filter_data(start_date, end_date, dept_list, team_list):
    """
    Φιλτράρισμα δεδομένων με πολλαπλές επιλογές τμημάτων και ομάδων
    """
    try:
        filtered_df = df.copy()
        
        # Debug πληροφορίες
        print(f"🔍 Φιλτράρισμα δεδομένων:")
        print(f"   📅 Από: {start_date} έως {end_date}")
        print(f"   🏢 Τμήματα: {dept_list}")
        print(f"   👥 Ομάδες: {team_list}")
        
        # Φιλτράρισμα ημερομηνιών
        if start_date and end_date and 'parsed_date' in filtered_df.columns:
            start_date_dt = pd.to_datetime(start_date)
            end_date_dt = pd.to_datetime(end_date)
            
            mask = (filtered_df['parsed_date'].dt.to_period('M') >= start_date_dt.to_period('M')) & \
                   (filtered_df['parsed_date'].dt.to_period('M') <= end_date_dt.to_period('M'))
            filtered_df = filtered_df[mask]
            print(f"   📊 Μετά το φιλτράρισμα ημερομηνιών: {len(filtered_df)} εγγραφές")
        
        # Φιλτράρισμα τμημάτων (πολλαπλή επιλογή)
        if dept_list and len(dept_list) > 0 and 'ΤΜΗΜΑ' in filtered_df.columns:
            # Αν έχουν επιλεχθεί συγκεκριμένα τμήματα
            filtered_df = filtered_df[filtered_df['ΤΜΗΜΑ'].isin(dept_list)]
            print(f"   📊 Μετά το φιλτράρισμα τμημάτων {dept_list}: {len(filtered_df)} εγγραφές")
        elif not dept_list or len(dept_list) == 0:
            # Αν δεν έχει επιλεχθεί κανένα τμήμα, δείχνει όλα
            print(f"   📊 Εμφάνιση όλων των τμημάτων: {len(filtered_df)} εγγραφές")
        
        # Φιλτράρισμα ομάδων (πολλαπλή επιλογή)
        if team_list and len(team_list) > 0 and 'ΟΝΟΜΑ_ΟΜΑΔΑΣ' in filtered_df.columns:
            # Αν έχουν επιλεχθεί συγκεκριμένες ομάδες
            filtered_df = filtered_df[filtered_df['ΟΝΟΜΑ_ΟΜΑΔΑΣ'].isin(team_list)]
            print(f"   📊 Μετά το φιλτράρισμα ομάδων {team_list}: {len(filtered_df)} εγγραφές")
        elif not team_list or len(team_list) == 0:
            # Αν δεν έχει επιλεχθεί καμία ομάδα, δείχνει όλες
            print(f"   📊 Εμφάνιση όλων των ομάδων: {len(filtered_df)} εγγραφές")
        
        numeric_columns = ['ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ', 'ΔΙΑΘΕΣΙΜΑ_ΡΑΝΤΕΒΟΥ', 'ΠΟΣΟΣΤΟ_ΑΔΙΑΘΕΤΩΝ']
        for col in numeric_columns:
            if col in filtered_df.columns:
                filtered_df[col] = filtered_df[col].fillna(0)
        
        # Replace NaN values with empty string for text columns  
        text_columns = ['ΤΜΗΜΑ', 'ΟΝΟΜΑ_ΟΜΑΔΑΣ']
        for col in text_columns:
            if col in filtered_df.columns:
                filtered_df[col] = filtered_df[col].fillna('Άγνωστο')
        
        print(f"   ✅ Τελικό αποτέλεσμα: {len(filtered_df)} εγγραφές")
        return filtered_df
        
    except Exception as e:
        print(f"❌ Σφάλμα φιλτραρίσματος: {e}")
        return df.copy()

@app.callback(
    Output('kpi-section', 'children'),
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('dept-filter', 'value'),
     Input('team-filter', 'value')]
)
def update_kpi_cards(start_date, end_date, dept_list, team_list):
    filtered_df = filter_data(start_date, end_date, dept_list, team_list)
    kpis = analyzer.calculate_unavailable_kpis(filtered_df)
    
    if not kpis:
        return dbc.Alert("Δεν υπάρχουν δεδομένα για την επιλεγμένη περίοδο", color="warning")
    
    # ✅ ENSURE ALL VALUES ARE STRINGS/NUMBERS, NOT OBJECTS
    selected_depts = len(dept_list) if dept_list else len(unique_departments)
    selected_teams = len(team_list) if team_list else len(unique_teams)
    
    # ✅ ADD SAFETY CHECKS FOR VALUES
    total_unavailable = kpis.get('total_unavailable', 0)
    total_available = kpis.get('total_available', 0)
    avg_rate = kpis.get('avg_unavailable_rate', 0)
    worst_dept = kpis.get('worst_dept', 'Άγνωστο')
    worst_count = kpis.get('worst_dept_count', 0)
    best_dept = kpis.get('best_dept', 'Άγνωστο')
    best_count = kpis.get('best_dept_count', 0)

    
    return dbc.Row([
        dbc.Col([
            create_simple_kpi_card(
                "Συνολικά Αδιάθετα", 
                f"{int(total_unavailable):,}",  # ✅ FORCE TO INT AND FORMAT
                f"από {int(total_available + total_unavailable):,} συνολικά", 
                "danger", 
                "❌"
            )
        ], md=2),
        dbc.Col([
            create_simple_kpi_card(
                "Διαθέσιμα Ραντεβου", 
                f"{int(total_available):,}",  # ✅ NEW KPI CARD FOR AVAILABLE APPOINTMENTS
                f"ενεργά ραντεβου", 
                "success", 
                "✅"
            )
        ], md=2),
        dbc.Col([
            create_simple_kpi_card(
                "Ποσοστό Αδιάθετων", 
                f"{float(avg_rate):.1f}%",  # ✅ FORCE TO FLOAT AND FORMAT
                "του συνόλου", 
                "warning", 
                "📊"
            )
        ], md=2),
        dbc.Col([
            create_simple_kpi_card(
                "Τμήμα με τα περισσότερα αδιάθετα", 
                str(worst_dept)[:15],  # ✅ FORCE TO STRING AND TRUNCATE
                f"{int(worst_count)} αδιάθετα", 
                "danger", 
                "📻"
            )
        ], md=2),
        dbc.Col([
            create_simple_kpi_card(
                "Τμήμα με τα λιγότερα αδιάθετα",
                str(best_dept)[:15],
                f"{int(best_count)} αδιάθετα",
                "success",
                "🏅"
            )
        ], md=2),
        dbc.Col([
            create_simple_kpi_card(
                "Επιλεγμένα Στοιχεία", 
                f"{int(selected_depts)} Τμ. | {int(selected_teams)} Ομ.",  # ✅ FORCE TO INT
                f"{kpis.get('months_analyzed', 0)} μήνες", 
                "info", 
                "🏥"
            )
        ], md=2)
    ])

# --- ΝΕΟΣ CALLBACK: Δυναμικές επιλογές για team-filter ανάλογα με dept-filter ---
@app.callback(
    [Output('team-filter', 'options')],
    [Output('team-filter', 'value')],
    [Input('dept-filter', 'value')],
    [State('team-filter', 'value')]
)
def update_team_options(selected_departments, current_team_values):
    """
    Ενημερώνει τις διαθέσιμες ομάδες (team-filter) βάσει των επιλεγμένων τμημάτων.
    Κρατά μόνο όσες επιλεγμένες ομάδες παραμένουν έγκυρες.
    """
    # Αν δεν έχει επιλεγεί τμήμα -> δείξε όλες τις ομάδες
    if not selected_departments:
        all_teams = sorted([t for t in df['ΟΝΟΜΑ_ΟΜΑΔΑΣ'].dropna().unique() if t != ''])
        options = [{'label': t, 'value': t} for t in all_teams]

        # Φιλτράρουμε τις τρέχουσες επιλογές ώστε να είναι έγκυρες
        valid_values = [v for v in (current_team_values or []) if v in all_teams]
        return options, valid_values

    # Έχουν επιλεγεί 1+ τμήματα -> δείξε ΜΟΝΟ τις ομάδες αυτών των τμημάτων
    mask = df['ΤΜΗΜΑ'].isin(selected_departments)
    teams_for_depts = sorted([t for t in df.loc[mask, 'ΟΝΟΜΑ_ΟΜΑΔΑΣ'].dropna().unique() if t != ''])
    options = [{'label': t, 'value': t} for t in teams_for_depts]

    # Κράτα μόνο τις ήδη επιλεγμένες ομάδες που εξακολουθούν να υπάρχουν
    valid_values = [v for v in (current_team_values or []) if v in teams_for_depts]

    return options, valid_values


@app.callback(
    Output('trend-chart', 'figure'),
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('dept-filter', 'value'),
     Input('team-filter', 'value')]
)
def update_trend_chart(start_date, end_date, dept_list, team_list):
    """Γράφημα εξέλιξης αδιάθετων"""
    filtered_df = filter_data(start_date, end_date, dept_list, team_list)
    
    if filtered_df.empty:
        return go.Figure().add_annotation(
            text="Δεν υπάρχουν δεδομένα για εμφάνιση",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
        )
    
    # Ομαδοποίηση ανά μήνα
    monthly_data = filtered_df.groupby('parsed_date').agg({
        'ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ': 'sum',
        'ΔΙΑΘΕΣΙΜΑ_ΡΑΝΤΕΒΟΥ': 'sum'
    }).reset_index()

    # ΥΠΟΛΟΓΙΣΕ σωστά το ποσοστό από τα αθροίσματα
    denom = monthly_data['ΔΙΑΘΕΣΙΜΑ_ΡΑΝΤΕΒΟΥ'].replace(0, np.nan)
    monthly_data['ΠΟΣΟΣΤΟ_ΑΔΙΑΘΕΤΩΝ'] = (monthly_data['ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ'] / denom * 100).fillna(0).round(1)

    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Γραμμή αδιάθετων
    fig.add_trace(
        go.Scatter(
            x=monthly_data['parsed_date'],
            y=monthly_data['ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ'],
            name='Αδιάθετα Ραντεβου',
            mode='lines+markers',
            line=dict(color=colors['danger'], width=3),
            marker=dict(size=8)
        ),
        secondary_y=False
    )
    
    # Ποσοστό αδιάθετων
    fig.add_trace(
        go.Scatter(
            x=monthly_data['parsed_date'],
            y=monthly_data['ΠΟΣΟΣΤΟ_ΑΔΙΑΘΕΤΩΝ'],
            name='Ποσοστό Αδιάθετων (%)',
            mode='lines',
            line=dict(color=colors['warning'], width=2, dash='dash')
        ),
        secondary_y=True
    )
    
    fig.update_layout(
        title="Εξέλιξη Αδιάθετων Ραντεβου στο Χρόνο",
        hovermode='x unified',
        height=500,
        showlegend=True
    )
    
    fig.update_xaxes(title_text="Περίοδος")
    fig.update_yaxes(title_text="Αριθμός Αδιάθετων Ραντεβου", secondary_y=False)
    fig.update_yaxes(title_text="Ποσοστό (%)", secondary_y=True)
    
    return fig

@app.callback(
    Output('dept-ranking', 'figure'),
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('dept-filter', 'value'),
     Input('team-filter', 'value')]
)
def update_dept_ranking(start_date, end_date, dept_list, team_list):
    """Κατάταξη τμημάτων με βάση αδιάθετα - τώρα δείχνει top 15 και bottom 15"""
    filtered_df = filter_data(start_date, end_date, dept_list, team_list)
    
    if filtered_df.empty:
        return go.Figure().add_annotation(
            text="Δεν υπάρχουν δεδομένα για εμφάνιση",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
        )
    
    # Ομαδοποίηση ανά τμήμα και άθροισμα αδιάθετων
    dept_stats = filtered_df.groupby('ΤΜΗΜΑ')['ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ'].sum().sort_values(ascending=False)
    
    # ✅ CHANGE: Show both top 15 and bottom 15 departments
    top_15 = dept_stats.head(15)
    bottom_15 = dept_stats.tail(15)
    
    # Combine them with a separator indicator
    combined_data = pd.concat([top_15, bottom_15])
    combined_data = combined_data.drop_duplicates()  # Remove duplicates if dataset is small
    
    # Sort for display (highest to lowest)
    combined_data = combined_data.sort_values(ascending=True)
    
    # Colors based on values - red for high, green for low
    colors_list = []
    for x in combined_data.values:
        if x in top_15.values and x >= dept_stats.median():
            colors_list.append('#e74c3c')  # Red for high unavailable
        elif x in bottom_15.values and x <= dept_stats.median():
            colors_list.append('#27ae60')  # Green for low unavailable  
        else:
            colors_list.append('#f39c12')  # Orange for middle values
    
    fig = go.Figure(go.Bar(
        x=combined_data.values,
        y=combined_data.index,
        orientation='h',
        marker_color=colors_list,
        text=[f'{x:,}' for x in combined_data.values],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Κατάταξη Τμημάτων - Περισσότερα (Κόκκινο) και Λιγότερα (Πράσινο) Αδιάθετα",
        xaxis_title="Αριθμός Αδιάθετων Ραντεβου",
        yaxis_title="Τμήμα",
        height=600,  # Increased height for more departments
        margin=dict(l=200)  # More space for department names
    )
    
    return fig

@app.callback(
    [Output('fair-redistribution-flow', 'figure'),
     Output('fair-redistribution-table', 'children'),
     Output('redistribution-ratio-text', 'children')],  # ← νέο output για να δείχνουμε το ποσοστό
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('dept-filter', 'value'),
     Input('team-filter', 'value'),
     Input('redistribution-ratio', 'value')]            # ← νέο input
)
def update_fair_redistribution_analysis(start_date, end_date, dept_list, team_list, ratio):
    filtered_df = filter_data(start_date, end_date, dept_list, team_list)
    temp_analyzer = UnavailableAppointmentsAnalyzer(filtered_df)

    # Χρησιμοποίησε το ratio από το slider
    flow_fig = temp_analyzer.create_fair_redistribution_flow_chart(
        redistribute_ratio=ratio,
        max_donor_fraction=0.25  # μπορείς να το κάνεις επίσης slider αργότερα
    )

    redistribution_df = temp_analyzer.suggest_fair_redistribution(
        redistribute_ratio=ratio,
        max_donor_fraction=0.25
    )

    if redistribution_df.empty:
        table_content = dbc.Alert([
            html.H5("ℹ️ Δεν υπάρχουν δεδομένα για ανακατανομή", className="alert-heading"),
            html.P("Αλλάξτε φίλτρα/ποσοστό ώστε να προκύψουν καθαροί δότες/δέκτες ή περισσότερα δεδομένα."),
        ], color="info")
    else:
        total_redistributed = int(redistribution_df['Προτεινόμενη Μεταφορά'].sum())
        table_content = html.Div([
            dbc.Alert([
                html.H5("✅ Επιτυχής Δίκαιη Ανακατανομή!", className="alert-heading text-success"),
                html.P([
                    f"Συνολική ανακατανομή: ", html.Strong(f"{total_redistributed:,} ραντεβού"),
                    f" | Ratio: {int(ratio*100)}%"
                ], className="mb-2"),
                html.P("Βάρη δεκτών: 3×σπανιότητα + 2×δυναμικότητα.", className="mb-0 small text-muted")
            ], color="success", className="mb-3"),
            dash_table.DataTable(
                columns=[{"name": col, "id": col, "type": "numeric" if "Αδιάθετα" in col or "Μεταφορά" in col or "%" in col else "text"} 
                         for col in redistribution_df.columns],
                data=redistribution_df.to_dict('records'),
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left','padding': '10px','fontFamily': 'Arial','fontSize': '13px'},
                style_header={'backgroundColor': colors['primary'],'color': 'white','fontWeight': 'bold','textAlign': 'center'},
                sort_action="native",
                page_size=15
            )
        ])

    ratio_text = f"Τρέχον ποσοστό: {int(ratio*100)}%"
    return flow_fig, table_content, ratio_text


@app.callback(
    Output('recommendations', 'children'),
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('dept-filter', 'value'),
     Input('team-filter', 'value')]
)
def update_recommendations(start_date, end_date, dept_list, team_list):
    """Συστάσεις και οδηγίες"""
    filtered_df = filter_data(start_date, end_date, dept_list, team_list)
    kpis = analyzer.calculate_unavailable_kpis(filtered_df)
    
    recommendations = []
    
    # Συμβουλές βάσει των KPI
    if kpis and kpis['avg_unavailable_rate'] > 20:
        recommendations.append(
            dbc.Alert([
                html.Strong("🚨 Υψηλό ποσοστό αδιάθετων ραντεβου: "),
                f"Το {kpis['avg_unavailable_rate']:.1f}% των ραντεβου είναι αδιάθετα. ",
                "Συνιστάται άμεση ανάλυση των αιτιών και εφαρμογή του αλγορίθμου δίκαιης ανακατανομής."
            ], color="danger")
        )
    elif kpis and kpis['avg_unavailable_rate'] > 10:
        recommendations.append(
            dbc.Alert([
                html.Strong("⚠️ Μέτριο ποσοστό αδιάθετων: "),
                f"Το {kpis['avg_unavailable_rate']:.1f}% των ραντεβου είναι αδιάθετα. ",
                "Χρησιμοποιήστε τη δίκαιη ανακατανομή για βελτιστοποίηση."
            ], color="warning")
        )
    else:
        recommendations.append(
            dbc.Alert([
                html.Strong("✅ Καλή διαχείριση αδιάθετων: "),
                "Το ποσοστό αδιάθετων ραντεβου είναι σε λογικά επίπεδα. ",
                "Μπορείτε να χρησιμοποιήσετε τη δίκαιη ανακατανομή για περαιτέρω βελτιστοποίηση."
            ], color="success")
        )
    
    # Γενικές συστάσεις για τη δίκαιη ανακατανομή
    general_recommendations = [
    "Ξεκινήστε πάντα επιλέγοντας την περίοδο και το τμήμα που θέλετε να αναλύσετε.",
    "Το σύστημα εντοπίζει ποιες ομάδες του τμήματος έχουν περισσότερα αδιάθετα ραντεβού και ποιες έχουν λιγότερα.",
    "Από τις ομάδες με πολλά αδιάθετα, μεταφέρεται ένα μέρος προς τις ομάδες που έχουν έλλειψη για να υπάρξει ισορροπία.",
    "Με τον διακόπτη (slider) ρυθμίζετε αν θα μεταφερθεί μικρότερος ή μεγαλύτερος αριθμός ραντεβού ανάμεσα στις ομάδες.",
    "Αν δεν εμφανιστούν προτάσεις, σημαίνει ότι οι ομάδες του τμήματος έχουν ήδη παρόμοιο αριθμό αδιάθετων ραντεβού.",
    "Χρησιμοποιήστε τον πίνακα για να δείτε αναλυτικά από ποια ομάδα προτείνεται να δοθούν ραντεβού και σε ποια να μεταφερθούν.",
    "Χρησιμοποιήστε το διάγραμμα ροής για πιο γρήγορη εικόνα: τα πορτοκαλί κουτιά είναι οι ομάδες που δίνουν ραντεβού, τα γαλάζια οι ομάδες που λαμβάνουν.",
    "Στόχος είναι όλες οι ομάδες του τμήματος να έχουν πιο δίκαιη και ισορροπημένη κατανομή ραντεβού."
]


    
    recommendations.append(
        html.Div([
            html.H5("💡 Συστάσεις για Δίκαιη Ανακατανομή:"),
            html.Ul([html.Li(rec) for rec in general_recommendations])
        ])
    )
    
    return html.Div(recommendations)

@app.callback(
    Output('detailed-table-section', 'children'),
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('dept-filter', 'value'),
     Input('team-filter', 'value')]
)
def update_detailed_table(start_date, end_date, dept_list, team_list):
    """Πίνακας αδιάθετων ραντεβου ανά τμήμα και ομάδα"""
    filtered_df = filter_data(start_date, end_date, dept_list, team_list)
    
    if filtered_df.empty:
        return dbc.Alert([
            html.H5("ℹ️ Δεν υπάρχουν δεδομένα", className="alert-heading"),
            html.P("Δεν βρέθηκαν δεδομένα για τα επιλεγμένα φίλτρα. Δοκιμάστε να αλλάξετε τα κριτήρια αναζήτησης.", className="mb-0")
        ], color="warning")
    
    # ✅ CORRECTED - Use the right column names
    summary_stats = filtered_df.groupby(['ΤΜΗΜΑ', 'ΟΝΟΜΑ_ΟΜΑΔΑΣ']).agg({
        'ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ': 'sum',
        'ΔΙΑΘΕΣΙΜΑ_ΡΑΝΤΕΒΟΥ': 'sum'
    }).reset_index()
    
    # ✅ CHANGE: Remove the "Σύνολο" column calculation as requested
    # summary_stats['ΣΥΝΟΛΙΚΑ_ΡΑΝΤΕΒΟΥ'] = summary_stats['ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ'] + summary_stats['ΔΙΑΘΕΣΙΜΑ_ΡΑΝΤΕΒΟΥ']
    
    # Calculate percentage without total column
    summary_stats['ΠΟΣΟΣΤΟ_ΑΔΙΑΘΕΤΩΝ'] = (
        summary_stats['ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ'] / (summary_stats['ΔΙΑΘΕΣΙΜΑ_ΡΑΝΤΕΒΟΥ']) * 100
    ).round(1)
    
    # Sort by unavailable appointments (descending)
    summary_stats = summary_stats.sort_values('ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ', ascending=False)
    
    # ✅ UPDATED - Column mapping without "Σύνολο"
    display_columns = {
        'ΤΜΗΜΑ': 'Τμήμα',
        'ΟΝΟΜΑ_ΟΜΑΔΑΣ': 'Ομάδα',
        'ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ': 'Αδιάθετα',
        'ΔΙΑΘΕΣΙΜΑ_ΡΑΝΤΕΒΟΥ': 'Διαθέσιμα',
        'ΠΟΣΟΣΤΟ_ΑΔΙΑΘΕΤΩΝ': 'Ποσοστό %'
    }
    
    summary_stats_renamed = summary_stats.rename(columns=display_columns)
    
    # Calculate totals for filter info
    total_unavailable = summary_stats['ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ'].sum()
    total_available = summary_stats['ΔΙΑΘΕΣΙΜΑ_ΡΑΝΤΕΒΟΥ'].sum()
    total_appointments = total_unavailable + total_available
    avg_percentage = (total_unavailable / total_appointments * 100) if total_appointments > 0 else 0
    
    # Filter display text
    selected_depts_text = f"{len(dept_list)} τμήματα" if dept_list else "όλα τα τμήματα"
    selected_teams_text = f"{len(team_list)} ομάδες" if team_list else "όλες οι ομάδες"
    
    return html.Div([
        # Info panel
        dbc.Alert([
            html.H6("📋 Στοιχεία Φιλτραρισμένων Δεδομένων:", className="alert-heading mb-3"),
            dbc.Row([
                dbc.Col([
                    html.P([html.Strong("📅 Περίοδος: "), f"{start_date} έως {end_date}"], className="mb-1"),
                    html.P([html.Strong("🏢 Φίλτρα: "), f"{selected_depts_text}, {selected_teams_text}"], className="mb-1")
                ], md=6),
                dbc.Col([
                    html.P([html.Strong("❌ Συνολικά Αδιάθετα: "), f"{total_unavailable:,}"], className="mb-1"),
                    html.P([html.Strong("📊 Μέσο Ποσοστό: "), f"{avg_percentage:.1f}%"], className="mb-1")
                ], md=6)
            ])
        ], color="info", className="mb-3"),
        
        html.H5(f"📊 Αναλυτικός Πίνακας ({len(summary_stats_renamed)} εγγραφές)", className="mb-3"),
        
        dash_table.DataTable(
            columns=[
                {"name": col, "id": col, "type": "numeric" if col in ["Αδιάθετα", "Διαθέσιμα", "Ποσοστό %"] else "text"} 
                for col in summary_stats_renamed.columns
            ],
            data=summary_stats_renamed.to_dict('records'),
            style_table={
                'overflowX': 'auto',
                'border': '1px solid #dee2e6'
            },
            style_cell={
                'textAlign': 'left',
                'padding': '12px',
                'fontFamily': 'Arial, sans-serif',
                'fontSize': '14px',
                'border': '1px solid #dee2e6'
            },
            style_header={
                'backgroundColor': colors['primary'],
                'color': 'white',
                'fontWeight': 'bold',
                'textAlign': 'center',
                'fontSize': '14px'
            },
            style_data_conditional=[
                # Alternating row colors
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgba(248, 249, 250, 0.8)'
                },
                # Red background for high percentages
                {
                    'if': {
                        'filter_query': '{Ποσοστό %} > 25',
                    },
                    'backgroundColor': 'rgba(220, 53, 69, 0.1)',
                    'color': '#dc3545',
                    'fontWeight': 'bold'
                },
                # Orange background for medium percentages  
                {
                    'if': {
                        'filter_query': '{Ποσοστό %} > 15 && {Ποσοστό %} <= 25',
                    },
                    'backgroundColor': 'rgba(255, 193, 7, 0.1)',
                    'color': '#fd7e14',
                    'fontWeight': 'bold'
                },
                # Green background for low percentages
                {
                    'if': {
                        'filter_query': '{Ποσοστό %} <= 15',
                    },
                    'backgroundColor': 'rgba(40, 167, 69, 0.1)',
                    'color': '#28a745',
                    'fontWeight': 'bold'
                }
                # Highlight high unavailable numbers
            ],
            sort_action="native",
            sort_mode="multi",
            page_size=20,
            style_cell_conditional=[
                {'if': {'column_id': 'Τμήμα'}, 'minWidth': '180px', 'maxWidth': '250px'},
                {'if': {'column_id': 'Ομάδα'}, 'minWidth': '150px', 'maxWidth': '200px'},
                {'if': {'column_id': 'Αδιάθετα'}, 'textAlign': 'center', 'minWidth': '100px'},
                {'if': {'column_id': 'Διαθέσιμα'}, 'textAlign': 'center', 'minWidth': '100px'},
                {'if': {'column_id': 'Ποσοστό %'}, 'textAlign': 'center', 'minWidth': '100px'}
            ],
            # Additional features
            filter_action="native",
            export_format="xlsx",
            export_headers="display"
        ),
        
        # Table usage info
        html.Hr(),
            html.Div([
                html.Small([
                    html.Strong("💡 Χρήσιμες λειτουργίες:"),
                ], className="text-muted"),
                html.Ul([
                    html.Li("Κάντε κλικ στις κεφαλίδες για ταξινόμηση (ascending/descending).", className="text-muted"),
                    html.Li("Χρησιμοποιήστε τα φίλτρα κάτω από τις κεφαλίδες για αναζήτηση ανά στήλη.", className="text-muted"),
                    html.Li("Εξαγωγή δεδομένων σε Excel με το κουμπί Export (πάνω δεξιά του πίνακα).", className="text-muted"),
                ], style={"marginTop": "6px", "marginBottom": "6px"}),

                html.Small(html.Strong("🔎 Χρωματική κωδικοποίηση (βάφεται ολόκληρη η γραμμή):"), className="text-muted"),
                html.Ul([
                    html.Li([
                        html.Span("  ", style={"display": "inline-block", "width": "14px", "height": "14px",
                                            "backgroundColor": "rgba(40, 167, 69, 0.12)", "border": "1px solid #28a745",
                                            "marginRight": "8px", "verticalAlign": "middle"}),
                        html.Span("Πράσινο: Ποσοστό % ≤ 15 (χαμηλά αδιάθετα).", className="text-muted"),
                    ], style={"listStyleType": "none", "marginLeft": "0"}),

                    html.Li([
                        html.Span("  ", style={"display": "inline-block", "width": "14px", "height": "14px",
                                            "backgroundColor": "rgba(255, 193, 7, 0.12)", "border": "1px solid #fd7e14",
                                            "marginRight": "8px", "verticalAlign": "middle"}),
                        html.Span("Πορτοκαλί: 15 < Ποσοστό % ≤ 25 (μέτρια αδιάθετα).", className="text-muted"),
                    ], style={"listStyleType": "none", "marginLeft": "0"}),

                    html.Li([
                        html.Span("  ", style={"display": "inline-block", "width": "14px", "height": "14px",
                                            "backgroundColor": "rgba(220, 53, 69, 0.12)", "border": "1px solid #dc3545",
                                            "marginRight": "8px", "verticalAlign": "middle"}),
                        html.Span("Κόκκινο: Ποσοστό % > 25 (υψηλά αδιάθετα).", className="text-muted"),
                    ], style={"listStyleType": "none", "marginLeft": "0"}),
                ])
            ])

    ])

# ══════════════════════════════════════════════════════════════════════════════
# RUN APP
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🏥 DASHBOARD ΑΔΙΑΘΕΤΩΝ ΡΑΝΤΕΒΟΥ - 401 ΓΣΝ")
    print("="*60)
    print("✅ Dashboard αρχικοποιήθηκε με επιτυχία!")
    print(f"📊 Συνολικές εγγραφές: {len(df):,}")
    print(f"❌ Συνολικά αδιάθετα: {df['ΑΔΙΑΘΕΤΑ_ΡΑΝΤΕΒΟΥ'].sum():,}")
    print(f"🏥 Τμήματα: {df['ΤΜΗΜΑ'].nunique()}")
    print(f"👥 Ομάδες: {df['ΟΝΟΜΑ_ΟΜΑΔΑΣ'].nunique()}")
    print(f"📅 Περίοδος: {df['ΜΗΝΑΣ-ΕΤΟΣ'].min()} έως {df['ΜΗΝΑΣ-ΕΤΟΣ'].max()}")
    
    print("\n🎯 ΣΤΟΧΟΙ DASHBOARD:")
    print("   • Παρακολούθηση αδιάθετων ραντεβου")
    print("   • Ανίχνευση προβληματικών τμημάτων")
    print("   • Δίκαιη ανακατανομή με βάση ανάγκες")
    print("   • Βελτιστοποίηση εξυπηρέτησης ασθενών")
    
    print("\n🧠 ΝΕΑ ΧΑΡΑΚΤΗΡΙΣΤΙΚΑ:")
    print("   • Αλγόριθμος δίκαιης ανακατανομής")
    print("   • Αναλογική κατανομή σε όλες τις ομάδες")
    print("   • Ρυθμιζόμενα βάρη προτεραιότητας")
    print("   • Οπτικοποίηση ροής ανακατανομής")
    
    print("\n🌐 Εκκίνηση server στη διεύθυνση: http://127.0.0.1:8050")
    print("🔌 Πατήστε Ctrl+C για τερματισμό")
    print("="*60 + "\n")
    
    app.run(debug=True, port=8050)