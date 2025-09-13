from cdc import cdc_cluster
import numpy as np
X = np.random.rand(100, 2)
labels = cdc_cluster(k_num=5, ratio=0.1, X=X)
n_clusters = len(np.unique(labels))
print(f"Number of clusters: {n_clusters}")
