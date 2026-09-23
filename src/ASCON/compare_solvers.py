import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Pliki źródłowe
GLUCOSE_FILE = "wyniki_ascon_sat.csv"
KISSAT_FILE = "wyniki_ascon_sat_kissat.csv"

def get_means_from_csv(filename):
    if not os.path.exists(filename):
        print(f"[!] Błąd: Brak pliku {filename}!")
        return {}
    
    df = pd.read_csv(filename)
    # Wykrywanie nazwy kolumny z bitami (Bity lub Bity_Liczba)
    bit_col = "Bity_Liczba" if "Bity_Liczba" in df.columns else "Bity"
    
    df["Czas_s"] = pd.to_numeric(df["Czas_s"], errors="coerce")
    df = df.dropna(subset=["Czas_s"])
    
    # Wyliczenie średniego czasu dla każdego progu bitowego
    means = df.groupby(bit_col)["Czas_s"].mean().to_dict()
    return means

def generate_comparison_chart():
    g_data = get_means_from_csv(GLUCOSE_FILE)
    k_data = get_means_from_csv(KISSAT_FILE)
    
    bits = [4, 8, 12, 16, 20]
    
    # Pobieranie wyliczonych średnich (lub 0 w przypadku braku danych)
    g_means = [g_data.get(b, 0) for b in bits]
    k_means = [k_data.get(b, 0) for b in bits]
    
    print("\n--- WYLICZONE ŚREDNIE CZASY [s] ---")
    for b, g, k in zip(bits, g_means, k_means):
        print(f"Bity: {b:2d} | Glucose: {g:8.2f}s | Kissat: {k:8.2f}s")
    
    # Tworzenie wykresu w skali LINOWEJ
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(10, 6))
    
    x = np.arange(len(bits))
    width = 0.35
    
    rects1 = plt.bar(x - width/2, k_means, width, label='Kissat 4.0.4', color='#2b5c8f')
    rects2 = plt.bar(x + width/2, g_means, width, label='Glucose 4.2.1', color='#d95f02')
    
    plt.xlabel('Liczba ukrytych bitów klucza', fontsize=11, fontweight='bold')
    plt.ylabel('Średni czas rozwiązywania [s]', fontsize=11, fontweight='bold')
    plt.title('Porównanie wydajności: Kissat 4.0.4 vs Glucose 4.2.1 (Skala Liniowa)', fontsize=12, fontweight='bold', pad=15)
    plt.xticks(x, [f"{b} bitów" for b in bits], fontsize=10)
    
    # Skala LINIOWA (Usunięto plt.yscale('log'))
    max_val = max(max(k_means), max(g_means)) if max(max(k_means), max(g_means)) > 0 else 100
    plt.ylim(0, max_val * 1.15)
    
    # Formatowanie etykiet tekstowych nad słupkami
    for rect in rects1:
        h = rect.get_height()
        if h == 0: continue
        label = f"{h:.2f}s" if h < 60 else f"{h/60:.1f}m ({h:.0f}s)"
        plt.annotate(label,
                    xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=8, fontweight='bold')
        
    for rect in rects2:
        h = rect.get_height()
        if h == 0: continue
        label = f"{h:.2f}s" if h < 60 else f"{h/60:.1f}m ({h:.0f}s)"
        plt.annotate(label,
                    xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=8, fontweight='bold')
        
    plt.legend(loc='upper left', frameon=True)
    plt.tight_layout()
    
    out_file = "wykres_porownanie_solverow_real.png"
    plt.savefig(out_file, dpi=300)
    print(f"\n[+] Pomyślnie wygenerowano nowy wykres liniowy: {out_file}")

if __name__ == "__main__":
    generate_comparison_chart()