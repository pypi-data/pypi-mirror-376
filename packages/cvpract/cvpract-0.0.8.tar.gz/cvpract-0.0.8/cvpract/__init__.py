def show():
    print(r"""

==============================
PRACTICE 1: SIMPLE LINEAR REGRESSION
==============================
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

# Generate simple dataset (X = study hours, y = exam score)
X = np.array([1,2,3,4,5,6,7,8,9]).reshape(-1,1)
y = np.array([30,35,50,55,65,70,75,80,90])

# Fit model
model = LinearRegression()
model.fit(X, y)

# Coefficients
print("Intercept:", model.intercept_)
print("Slope:", model.coef_)

# Predictions
y_pred = model.predict(X)

# Evaluation
print("R-squared:", r2_score(y, y_pred))
print("MSE:", mean_squared_error(y, y_pred))

# Plot
plt.scatter(X, y, color="blue", label="Data")
plt.plot(X, y_pred, color="red", label="Regression Line")
plt.legend()
plt.show()


==============================
PRACTICE 2: MULTIPLE LINEAR REGRESSION
==============================
from sklearn.model_selection import train_test_split

# Generate dataset (Hours studied, Sleep hours, Previous scores → Final score)
data = {
    "hours_study": [2,3,4,5,6,7,8,9,10],
    "hours_sleep": [8,7,6,6,5,5,4,3,2],
    "prev_score":  [40,50,55,60,65,70,75,80,85],
    "final_score": [45,52,58,65,70,74,78,82,90]
}
df = pd.DataFrame(data)

X = df[["hours_study", "hours_sleep", "prev_score"]]
y = df["final_score"]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Fit model
mlr = LinearRegression()
mlr.fit(X_train, y_train)

# Coefficients
print("\nIntercept:", mlr.intercept_)
print("Coefficients:", mlr.coef_)
print("Feature Names:", X.columns.tolist())

# Predictions
y_pred = mlr.predict(X_test)

# Evaluation
print("R-squared:", r2_score(y_test, y_pred))
print("MSE:", mean_squared_error(y_test, y_pred))


==============================
PRACTICE 3: REGULARIZED LINEAR MODELS (Ridge, Lasso, ElasticNet)
==============================
from sklearn.linear_model import Ridge, Lasso, ElasticNet

# Use same multiple regression dataset
X = df[["hours_study", "hours_sleep", "prev_score"]]
y = df["final_score"]

# Ridge Regression
ridge = Ridge(alpha=1.0)
ridge.fit(X, y)
print("\nRidge Coefficients:", ridge.coef_)

# Lasso Regression
lasso = Lasso(alpha=0.1)
lasso.fit(X, y)
print("Lasso Coefficients:", lasso.coef_)

# ElasticNet Regression
elastic = ElasticNet(alpha=0.1, l1_ratio=0.5)
elastic.fit(X, y)
print("ElasticNet Coefficients:", elastic.coef_)



=============================================
DISCRIMINATIVE MODELS (OC2, OC6) — IRIS DATASET
=============================================

# 1) Logistic Regression (Binary Classification: Setosa vs Others)
from sklearn.datasets import load_iris
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_curve, auc
import matplotlib.pyplot as plt

iris = load_iris()
df = pd.DataFrame(iris.data, columns=iris.feature_names)
df["target"] = (iris.target == 0).astype(int)  # Binary: Setosa=1, Others=0

X = df.drop("target", axis=1)
y = df["target"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:,1]

print("Accuracy:", accuracy_score(y_test, y_pred))
print("Precision:", precision_score(y_test, y_pred))
print("Recall:", recall_score(y_test, y_pred))

fpr, tpr, _ = roc_curve(y_test, y_prob)
roc_auc = auc(fpr, tpr)
plt.plot(fpr, tpr, label=f"AUC = {roc_auc:.2f}")
plt.plot([0,1],[0,1],'--')
plt.xlabel("FPR")
plt.ylabel("TPR")
plt.title("ROC Curve - Logistic Regression")
plt.legend()
plt.show()


# 2) K-Nearest Neighbors (KNN)
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score

iris = load_iris()
X, y = iris.data, iris.target

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

knn = KNeighborsClassifier(n_neighbors=5)
knn.fit(X_train, y_train)
y_pred = knn.predict(X_test)

print("KNN Accuracy:", accuracy_score(y_test, y_pred))
print("First 10 Predictions:", y_pred[:10])
print("First 10 Actual:", y_test[:10])


# 3) Decision Tree Classifier
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt

iris = load_iris()
X, y = iris.data, iris.target
feature_names = iris.feature_names
class_names = iris.target_names

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

tree = DecisionTreeClassifier(max_depth=3, random_state=0)
tree.fit(X_train, y_train)
y_pred = tree.predict(X_test)

print("Decision Tree Accuracy:", accuracy_score(y_test, y_pred))

plt.figure(figsize=(12,8))
plot_tree(tree, feature_names=feature_names, class_names=class_names, filled=True)
plt.show()


# 4) Support Vector Machine (SVM)
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score

iris = load_iris()
X, y = iris.data, iris.target

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

svm = SVC(kernel="linear")
svm.fit(X_train, y_train)
y_pred = svm.predict(X_test)

print("SVM Accuracy:", accuracy_score(y_test, y_pred))


# 5) Random Forest
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

iris = load_iris()
X, y = iris.data, iris.target

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

rf = RandomForestClassifier(n_estimators=100, random_state=0)
rf.fit(X_train, y_train)
y_pred = rf.predict(X_test)

print("Random Forest Accuracy:", accuracy_score(y_test, y_pred))
print("Feature Importances:", rf.feature_importances_)


# 6) Gradient Boosting (XGBoost)
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score

iris = load_iris()
X, y = iris.data, iris.target

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

xgb = XGBClassifier(use_label_encoder=False, eval_metric="mlogloss")
xgb.fit(X_train, y_train)
y_pred = xgb.predict(X_test)

print("XGBoost Accuracy:", accuracy_score(y_test, y_pred))
print("Feature Importances:", xgb.feature_importances_)


""")

