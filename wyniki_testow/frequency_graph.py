import os
import statistics
import matplotlib.pyplot as plt


nibble_times = [[] for _ in range(32)]

for filename in os.listdir("wyniki_testow"):
    if filename.startswith("testy_photon_") and filename.endswith(".md"):
        name = filename.removeprefix("testy_photon_") 
        name = name.removesuffix(".md")
        first, second = name.split("_")
        first = int(first)
        second = int(second) 
        times = []
        with open(f"wyniki_testow/{filename}", "r") as file:
            for line in file:
                if line.startswith("|"):
                    parts = line.split("|")
                    try:
                        time = float(parts[3].strip())
                        times.append(time)
                    except ValueError:
                        pass
        pair_mean = statistics.mean(times)
        nibble_times[first].append(pair_mean)
        nibble_times[second].append(pair_mean)

selected_nibbles=[]
for nibble in range(32):
    if len(nibble_times[nibble]) >= 3:
        selected_nibbles.append(nibble)

for nibble in selected_nibbles:
    times = nibble_times[nibble]
    x = [nibble] * len(times)
    plt.scatter(x, times)
    mean_time = statistics.mean(times)

    plt.scatter(nibble, mean_time, marker="x", s=100)

plt.xlabel("Pozycja słowa")
plt.ylabel("Średni czas pary [s]")
plt.xticks(selected_nibbles)
plt.show()