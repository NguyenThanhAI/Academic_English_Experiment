import os
import pickle

import numpy as np
import matplotlib.pyplot as plt

from sklearn.preprocessing import OneHotEncoder



class ANN:
    def __init__(self, layers_size, model_dir: str=None, load: bool=False):
        self.layers_size = layers_size
        self.model_dir = model_dir
        self.load = load
        self.parameters = {}
        self.L = len(self.layers_size)
        self.n = 0
        self.train_costs = []
        self.val_costs = []
        self.train_accs = []
        self.val_accs = []
    
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

        if not self.load:
            np.random.seed(1)
 
            for l in range(1, len(self.layers_size)):
                self.parameters["W_" + str(l)] = np.random.randn(self.layers_size[l - 1], self.layers_size[l]) / np.sqrt(
                    self.layers_size[l - 1])
                self.parameters["b_" + str(l)] = np.zeros((self.layers_size[l], 1))
        
        else:
            self.load_model()
 
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
 
    def fit(self, train_x, train_y, val_x, val_y, learning_rate=0.01, batch_size=64, n_iterations=2500):
        np.random.seed(1)
 
        #self.n = X.shape[0]
        self.n = batch_size
 
        self.layers_size.insert(0, train_x.shape[1])
        indices = np.arange(train_x.shape[0])
        self.initialize_parameters()
        for loop in range(n_iterations):
            chosen_index = np.random.choice(indices, size=batch_size)
            x_batch = train_x[chosen_index]
            y_batch = train_y[chosen_index]
            A, store = self.forward(x_batch)
            #cost = -np.mean(y_batch * np.log(A.T+ 1e-8))
            derivatives = self.backward(x_batch, y_batch, store)
 
            for l in range(1, self.L + 1):
                self.parameters["W_" + str(l)] = self.parameters["W_" + str(l)] - learning_rate * derivatives[
                    "dW_" + str(l)]
                self.parameters["b_" + str(l)] = self.parameters["b_" + str(l)] - learning_rate * derivatives[
                    "db_" + str(l)]

            
            if loop % 100 == 0:
                
                train_A, _ = self.forward(train_x)
                train_cost = -np.mean(train_y * np.log(train_A.T + 1e-8) + (1 - train_y) * np.log(1 - train_A.T + 1e-8))
                train_accuracy = self.evaluate(train_x, train_y)
                val_A, _ = self.forward(val_x)
                val_cost = -np.mean(val_y * np.log(val_A.T + 1e-8) + (1 - val_y) * np.log(1 - val_A.T + 1e-8))
                val_accuracy = self.evaluate(val_x, val_y)
                print("Step: {}, Train cost: {}, Train accuracy: {}, Val cost: {}, Val accuracy: {}".format(loop, train_cost, train_accuracy, val_cost, val_accuracy))
 
            #if loop % 10 == 0:
                self.train_costs.append(train_cost)
                self.val_costs.append(val_cost)
                self.train_accs.append(train_accuracy)
                self.val_accs.append(val_accuracy)

        self.save_model()
 
    def evaluate(self, X, Y):
        A, cache = self.forward(X)
        y_hat = np.argmax(A, axis=0)
        Y = np.argmax(Y, axis=1)
        accuracy = (y_hat == Y).mean()
        return accuracy * 100

    def predict(self, X):
        A, cache = self.forward(X)
        return A

    def save_model(self):
        save_dict = {}
        save_dict["parameters"] = self.parameters
        save_dict["layers_size"] = self.layers_size
        save_dict["train_costs"] = self.train_costs
        save_dict["val_costs"] = self.val_costs
        save_dict["train_accs"] = self.train_accs
        save_dict["val_accs"] = self.val_accs
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir, exist_ok=True)
        with open(os.path.join(self.model_dir, "model.pkl"), "wb") as f:
            pickle.dump(save_dict, f)
            f.close()

        print("Model saved")

    def load_model(self):
        if self.model_dir is None:
            raise ValueError("Model dir must not be None")
        with open(os.path.join(self.model_dir, "model.pkl"), "rb") as f:
            save_dict = pickle.load(f)
            self.parameters = save_dict["parameters"]
            self.layers_size = save_dict["layers_size"]
            self.L = len(self.layers_size) - 1
            f.close()
        
        print("Model loaded")

 
    def plot_cost(self):
        #plt.figure()
        plt.subplots(2, 1, sharex=True)
        plt.subplot(2, 1, 1)
        plt.plot(np.arange(len(self.train_costs)), self.train_costs, label="train cost")
        plt.plot(np.arange(len(self.val_costs)), self.val_costs, label="val cost")
        plt.xlabel("steps")
        plt.ylabel("cost")
        plt.legend()
        plt.grid()
        plt.subplot(2, 1, 2)
        plt.plot(np.arange(len(self.train_accs)), self.train_accs, label="train accuracy")
        plt.plot(np.arange(len(self.val_accs)), self.val_accs, label="val accuracy")
        plt.xlabel("steps")
        plt.ylabel("accuracy")
        plt.legend()
        plt.grid()
        plt.show()



def pre_process_data(train_x, train_y, test_x, test_y):
    # Normalize
    train_x = train_x / 255.
    test_x = test_x / 255.

    train_x = np.reshape(train_x, newshape=(train_x.shape[0], -1))
    test_x = np.reshape(test_x, newshape=(test_x.shape[0], -1))
 
    enc = OneHotEncoder(sparse=False, categories='auto')
    train_y = enc.fit_transform(train_y.reshape(len(train_y), -1))
 
    test_y = enc.transform(test_y.reshape(len(test_y), -1))
 
    return train_x, train_y, test_x, test_y