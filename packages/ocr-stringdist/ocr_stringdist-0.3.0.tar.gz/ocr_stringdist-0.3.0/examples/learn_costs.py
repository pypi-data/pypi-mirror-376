from ocr_stringdist import WeightedLevenshtein
from ocr_stringdist.learner import Learner

data = [
    ("kitten", "sitting"),  # k -> s, e -> i, insert g
    ("flaw", "lawn"),  # delete f, insert n
    ("Hallo", "Hello"),  # a -> e
    ("W0rld", "World"),  # 0 -> o
    ("W0rd", "Word"),  # 0 -> o
    ("This sentence misses a dot", "This sentence misses a dot."),  # insert .
    ("This one also does", "This one also does."),  # insert .
    ("Include correct data, too.", "Include correct data, too."),
]

learner = Learner().with_smoothing(1.0)

wl = learner.fit(data)
wl = WeightedLevenshtein.learn_from(data)

print("Learned costs:")
print("Substitution costs:")
print(wl.substitution_costs)
print("Insertion costs:")
print(wl.insertion_costs)
print("Deletion costs:")
print(wl.deletion_costs)
