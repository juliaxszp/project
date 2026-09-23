import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

CSV_FILE = "wyniki_ascon_kat_30.csv"

def run_analysis():
    if not os.path.exists(CSV_FILE):
        print(f"Błąd: Plik {CSV_FILE} jeszcze nie istnieje!")
        return

    # 1. Wczytanie danych
    df = pd.read_csv(CSV_FILE)
    if df.empty:
        print("Plik CSV jest pusty. Poczekaj na zebranie pierwszych wyników!")
        return

    # Konwersja czasu na typ numeryczny
    df['Czas_s'] = pd.to_numeric(df['Czas_s'], errors='coerce')
    df = df.dropna(subset=['Czas_s'])

    print("=" * 70)
    print(f"   PODSUMOWANIE STATYSTYCZNE BADAŃ SAT (Liczba próbek: {len(df)})")
    print("=" * 70)

    # 2. Tabela statystyk: Liczba bitów vs Wzorzec
    stats = df.groupby(['Bity_Liczba', 'Wzorzec'])['Czas_s'].agg(
        Liczba_Prob='count',
        Srednia_s='mean',
        Mediana_s='median',
        Odchylenie_Std='std',
        Min_s='min',
        Maks_s='max'
    ).reset_index()

    print("\n--- STATYSTYKA OPISOWA DLA KOMBINACJI BITÓW I WZORCÓW ---")
    print(stats.to_string(index=False))

    # 3. Wykres 1: Wzrost czasu w zależności od liczby ukrytych bitów (Wykres pudełkowy / Boxplot)
    plt.figure(figsize=(10, 6))
    sns.boxplot(
        data=df, 
        x='Bity_Liczba', 
        y='Czas_s', 
        hue='Wzorzec', 
        palette='Set2'
    )
    plt.title('Czas rozwiązywania przez Kissat 4.0.4 w zależności od liczby ukrytych bitów', fontsize=12, fontweight='bold')
    plt.xlabel('Liczba ukrytych bitów klucza', fontsize=11)
    plt.ylabel('Czas wykonania solve [s]', fontsize=11)
    plt.yscale('log')  # Skala logarytmiczna dla lepszej widoczności wykładniczego wzrostu
    plt.grid(True, which="both", ls="--", linewidth=0.5, alpha=0.7)
    plt.legend(title='Wzorcerz ukrycia', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    chart_path1 = "wykres_czas_vs_bity.png"
    plt.savefig(chart_path1, dpi=300)
    plt.close()
    print(f"\n[+] Wygenerowano wykres: {chart_path1}")

    # 4. Wykres 2: Średni czas rozwiązywania dla poszczególnych bajtów klucza (0-15)
    byte_times = {i: [] for i in range(16)}
    for _, row in df.iterrows():
        if pd.isna(row["Ukryte_Indeksy"]):
            continue
        indices = [int(x) for x in str(row["Ukryte_Indeksy"]).split(";")]
        t = float(row["Czas_s"])
        affected_bytes = set(idx // 8 for idx in indices)
        for b in affected_bytes:
            byte_times[b].append(t)

    byte_stats = []
    for b in range(16):
        times = byte_times[b]
        if times:
            byte_stats.append({'Bajt': f'Bajt {b}', 'Sredni_Czas_s': sum(times)/len(times)})
    
    df_bytes = pd.DataFrame(byte_stats)

    if not df_bytes.empty:
        plt.figure(figsize=(12, 5))
        sns.barplot(data=df_bytes, x='Bajt', y='Sredni_Czas_s', hue='Bajt', palette='viridis', legend=False)
        plt.title('Średni czas rozwiązywania w zależności od dotkniętego bajtu klucza (0-15)', fontsize=12, fontweight='bold')
        plt.xlabel('Indeks bajtu klucza (Bajt 0-7: Słowo x0, Bajt 8-15: Słowo x1)', fontsize=11)
        plt.ylabel('Średni czas [s]', fontsize=11)
        plt.xticks(rotation=45)
        plt.grid(True, axis='y', ls="--", alpha=0.7)
        plt.tight_layout()
        
        chart_path2 = "wykres_analiza_bajtow.png"
        plt.savefig(chart_path2, dpi=300)
        plt.close()
        print(f"[+] Wygenerowano wykres: {chart_path2}")

    print("\n[OK] Analiza zakończona sukcesem!")

if __name__ == "__main__":
    run_analysis()