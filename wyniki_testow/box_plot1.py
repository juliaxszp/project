import matplotlib.pyplot as plt

all_times = []
pairs = [("3_10", "[3, 10]"), ("8_28", "[8, 28]"), ("1_15", "[1, 15]"), ("3_23", "[3, 23]"), ("5_28", "[5, 28]")]

for filename, label in pairs:
    times = []
    with open(f"wyniki_testow/testy_photon_{filename}.md", "r") as file:
        for line in file:
            if line.startswith("|"):
                parts = line.split("|")

                try:
                    time = float(parts[3].strip())
                    times.append(time)

                except ValueError:
                    pass
    print(label, "liczba pomiarow:", len(times))
    all_times.append(times)

plt.boxplot(all_times, showmeans =True, meanprops={"marker": "x", "markersize": 8})
plt.ylabel("Czas rozwiązania [s]")
plt.xticks([1, 2, 3, 4, 5], ["[3, 10]", "[8, 28]", "[1, 15]", "[3, 23]", "[5, 28]"])
plt.show()