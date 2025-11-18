import numpy as np

# Source: Supplementary Information S.21

# bins and their probabilities
bins = [
    (0, 10),
    (11, 20),
    (21, 40),
    (41, 60),
    (61, 80),
    (81, 100),
    (101, 120),
    (121, 150),  # paper says > 120; cap for practicality
]

probs = np.array(
    [
        0.04,  # 0–10
        0.12,  # 11–20
        0.30,  # 21–40
        0.37,  # 41–60
        0.06,  # 61–80
        0.06,  # 81–100
        0.02,  # 101–120
        0.03,  # >120
    ]
)

probs = probs / probs.sum()


def sample_lsu(shift=0.0):
    # Shift allows user to adjust the expected mean
    idx = np.random.choice(len(bins), size=1, p=probs)
    low, high = bins[idx[0]]
    return max(0, np.random.uniform(low, high) + shift)
