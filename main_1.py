import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
import matplotlib.pylab as plt
from sklearn.preprocessing import OneHotEncoder
 
 
class ANN:
    def __init__(self, layers_size):
        self.layers_size = layers_size
        self.parameters = {}
        self.L = len(self.layers_size)
        self.n = 0
        self.costs = []
    
    @staticmethod
    def sigmoid(Z):
        return 1 / (1 + np.exp(-Z))

    @staticmethod
    def relu(Z):
        return np.where(Z >= 0, Z, 0)
 
    @staticmethod
    def softmax(Z):
        expZ = np.exp(Z - np.max(Z))
        return expZ / expZ.sum(axis=0, keepdims=True)
 
    def initialize_parameters(self):
        np.random.seed(1)
 
        for l in range(1, len(self.layers_size)):
            self.parameters["W_" + str(l)] = np.random.randn(self.layers_size[l - 1], self.layers_size[l]) / np.sqrt(
                self.layers_size[l - 1])
            self.parameters["b_" + str(l)] = np.zeros((self.layers_size[l], 1))
 
    def forward(self, X):
        store = {}
 
        A = X.T
        for l in range(self.L - 1):
            Z = self.parameters["W_" + str(l + 1)].T.dot(A) + self.parameters["b_" + str(l + 1)]
            A = self.relu(Z)
            store["A_" + str(l + 1)] = A
            store["W_" + str(l + 1)] = self.parameters["W_" + str(l + 1)]
            store["Z_" + str(l + 1)] = Z
 
        Z = self.parameters["W_" + str(self.L)].T.dot(A) + self.parameters["b_" + str(self.L)]
        A = self.softmax(Z)
        store["A_" + str(self.L)] = A
        store["W_" + str(self.L)] = self.parameters["W_" + str(self.L)]
        store["Z_" + str(self.L)] = Z
 
        return A, store
 
    @staticmethod
    def sigmoid_derivative(Z):
        s = 1 / (1 + np.exp(-Z))
        return s * (1 - s)

    @staticmethod
    def relu_derivative(Z):
        return np.where(Z >= 0, 1, 0)
 
    def backward(self, X, Y, store):
 
        derivatives = {}
 
        store["A_0"] = X.T
 
        A = store["A_" + str(self.L)]
        dZ = A - Y.T
 
        dW = store["A_" + str(self.L - 1)].dot(dZ.T) / self.n
        db = np.sum(dZ, axis=1, keepdims=True) / self.n
        dAPrev = store["W_" + str(self.L)].dot(dZ)
 
        derivatives["dW_" + str(self.L)] = dW
        derivatives["db_" + str(self.L)] = db
 
        for l in range(self.L - 1, 0, -1):
            dZ = dAPrev * self.relu_derivative(store["Z_" + str(l)])
            dW = 1. / self.n * store["A_" + str(l - 1)].dot(dZ.T)
            db = 1. / self.n * np.sum(dZ, axis=1, keepdims=True)
            if l > 1:
                dAPrev = store["W_" + str(l)].dot(dZ)
 
            derivatives["dW_" + str(l)] = dW
            derivatives["db_" + str(l)] = db
 
        return derivatives
 
    def fit(self, X, Y, learning_rate=0.01, n_iterations=2500):
        np.random.seed(1)
 
        self.n = X.shape[0]
 
        self.layers_size.insert(0, X.shape[1])
 
        self.initialize_parameters()
        for loop in range(n_iterations):
            A, store = self.forward(X)
            cost = -np.mean(Y * np.log(A.T+ 1e-8))
            derivatives = self.backward(X, Y, store)
 
            for l in range(1, self.L + 1):
                self.parameters["W_" + str(l)] = self.parameters["W_" + str(l)] - learning_rate * derivatives[
                    "dW_" + str(l)]
                self.parameters["b_" + str(l)] = self.parameters["b_" + str(l)] - learning_rate * derivatives[
                    "db_" + str(l)]
 
            if loop % 100 == 0:
                print("Cost: ", cost, "Train Accuracy:", self.predict(X, Y))
 
            if loop % 10 == 0:
                self.costs.append(cost)
 
    def predict(self, X, Y):
        A, cache = self.forward(X)
        y_hat = np.argmax(A, axis=0)
        Y = np.argmax(Y, axis=1)
        accuracy = (y_hat == Y).mean()
        return accuracy * 100
 
    def plot_cost(self):
        plt.figure()
        plt.plot(np.arange(len(self.costs)), self.costs)
        plt.xlabel("epochs")
        plt.ylabel("cost")
        plt.show()
 
 
def pre_process_data(train_x, train_y, test_x, test_y):
    # Normalize
    train_x = train_x / 255.
    test_x = test_x / 255.
 
    enc = OneHotEncoder(sparse=False, categories='auto')
    train_y = enc.fit_transform(train_y.reshape(len(train_y), -1))
 
    test_y = enc.transform(test_y.reshape(len(test_y), -1))
 
    return train_x, train_y, test_x, test_y
 
 
if __name__ == '__main__':
    csv_path = r"C:\Users\Thanh\Downloads\voice_gender\voice.csv"
    batch_size = 64

    df = pd.read_csv(csv_path)
    df['label'] = df['label'].replace({'male':1,'female':0})

    x = df.drop("label", axis=1).to_numpy(dtype=np.float)
    y = df["label"].values
    labels = np.zeros(shape=(y.shape[0], 2))
    labels[np.arange(y.shape[0]), y] = 1
    x = (x - np.min(x, axis=0, keepdims=True))/(np.max(x, axis=0, keepdims=True) - np.min(x, axis=0, keepdims=True))

    skf = StratifiedKFold(n_splits=5)
    for train_index, test_index in skf.split(x, y):
        train_x, test_x = x[train_index], x[test_index]
        train_y, test_y = labels[train_index], labels[test_index]
 
    layers_dims = [32, 32, 32, 32, 2]
 
    ann = ANN(layers_dims)
    ann.fit(train_x, train_y, learning_rate=0.1, n_iterations=5000)
    print("Train Accuracy:", ann.predict(train_x, train_y))
    print("Test Accuracy:", ann.predict(test_x, test_y))
    ann.plot_cost()