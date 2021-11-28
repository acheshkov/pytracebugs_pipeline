import pickle
import pandas
import glob

dfs = []

#for i in range(516+1):
for pos, f in enumerate(glob.glob("stat/*.pickle")):
    d = pickle.load(open(f, "rb"))
    
    dfs.append(d)

    #if pos > 5:
        #break

merged = pandas.concat(dfs)
merged.sort_values("times" ,inplace=True, ascending=False)
pickle.dump(merged, open(f"stable_dataset.pickle", "wb"))


#for pos, i in enumerate(range(0, len(d), 10000)):
    #pickle.dump(d.iloc[i:i+10000], open(f"splitted{pos}_correct_source_code_valid.pickle", "wb"))

