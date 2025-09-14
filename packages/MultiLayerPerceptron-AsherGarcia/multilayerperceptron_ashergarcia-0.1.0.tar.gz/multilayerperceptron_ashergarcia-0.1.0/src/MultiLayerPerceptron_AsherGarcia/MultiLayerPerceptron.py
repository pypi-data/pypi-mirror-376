import math
import random

SIGMOID = 0
RELU = 1
LEAKYRELU = 2
TANH = 3

class MLP:
    def __init__(self, structure, learningRate):
        assert isinstance(structure, list) and len(structure) >= 3, "You must provide a 3 item list in the neural network structure"

        self.structure = structure
        self.learningRate = learningRate
        self.layersCount = len(structure)
        self.weights = [self.initWeights(nOut, nIn) for nIn, nOut in zip(structure[:-1], structure[1:])]
        self.biases = [[random.uniform(-1, 1) for _ in range(n)] for n in structure[1:]]
    
    def initWeights(self, rows, cols):
        return [[random.uniform(-1, 1) for _ in range(cols)] for _ in range(rows)]

    def sigmoid(self, x):
        return 1 / (1 + math.exp(-x))

    def sigmoidDeriv(self, x):
        s = self.sigmoid(x)
        return s * (1 - s)
    
    def feedforward(self, inputVector):
        activations = [inputVector]
        zs =[]

        for i in range(self.layersCount - 1):
            z = [sum(w * a for w, a in zip(neuron, activations[-1])) + b for neuron, b in zip(self.weights[i], self.biases[i])]
            zs.append(z)
            activations.append([self.sigmoid(val) for val in z])

        return activations, zs
    
    def printData(self):
        print(f'\n------------------------------------------Data------------------------------------------\n')
        print("Counts:")
        print(f"Inputs: {self.structure[0]}\tHidden: {[self.structure[h] for h in range(1, self.layersCount-1)]}\tOutput: {self.structure[-1]}")
        print(f"Structure: {self.structure}\tLayers: {len(self.structure)}")
        print(f"\nWeights:\n{self.weights}")
        print(f"\nBias:\n{self.biases}")
    
    def train(self, inputs, outputs, rounds, logs = False):
        assert isinstance(inputs, (list)), "Inputs must be in a list"
        assert isinstance(outputs, (list)), "Outputs must be in a list"
        assert not (hasattr(outputs[0], '__iter__') and len(outputs[0]) != self.structure[-1]), f"Each output must have {self.structure[-1]} values to match the number of output neurons"
        

        outputs = [[y] if not isinstance(y, list) else y for y in outputs]

        for round in range(rounds):
            totalError = 0

            if logs and (round+1) % 1000 == 0:
                print(f'\n------------------------------------------Round #{round+1}------------------------------------------\n')
            
            for input, output in zip(inputs, outputs):
                activations, zs = self.feedforward(input)

                deltas = [None] * (self.layersCount - 1)
                deltas[-1] = [(yI - aI) * self.sigmoidDeriv(zI) for yI, aI, zI in zip(output, activations[-1], zs[-1])]

                for l in range(self.layersCount - 3, -1, -1):
                    layerWeights = self.weights[l + 1]
                    deltaNext = deltas[l + 1]
                    z = zs[l]
                    sp = [self.sigmoidDeriv(zI) for zI in z]
                    deltas[l] = [sum(layerWeights[k][j] * deltaNext[k] for k in range(len(deltaNext))) * sp[j] for j in range(len(sp))]

                for l in range(self.layersCount - 1):
                    for i in range(len(self.weights[l])):
                        for j in range(len(self.weights[l][i])):
                            self.weights[l][i][j] += self.learningRate * deltas[l][i] * activations[l][j]
                        self.biases[l][i] += self.learningRate * deltas[l][i]

                totalError += sum((yI - aI) ** 2 for yI, aI in zip(output, activations[-1]))

                if logs and (round + 1) % 1000 == 0:
                    print(f"Value: {input} =>\n{self.predict(input, False)}")
                    print(f"Error: {totalError}\n")

    def predict(self, inputs, logs = True):
        results = []

        inputs = [[i] if not isinstance(i, list) else i for i in inputs]
        for input in inputs:
            r = [round(o) for o in (self.feedforward(input)[0][-1])]
            results.append(r)

            if logs:
                print(f"{input} => {r}")

        return results

class MLPAF:
    sigmoidActivation = SIGMOID
    reluActivation = RELU
    leakyReluActivation = LEAKYRELU
    tanhActivation = TANH

    def __init__(self, structure, learningRate, activationFunction = SIGMOID):
        assert isinstance(structure, list) and len(structure) >= 3, "You must provide a 3 item list in the neural network structure"

        self.structure = structure
        self.learningRate = learningRate
        self.layersCount = len(structure)
        self.weights = [self.initWeights(n_out, n_in) for n_in, n_out in zip(structure[:-1], structure[1:])]
        self.biases = [[random.uniform(-1, 1) for _ in range(n)] for n in structure[1:]]
        self.activationFunction = activationFunction
        self.lastError = 0

    def ReLU(self, x):
        return max(0, x)
    
    def ReLUDeriv(self, x):
        return 1 if x > 0 else 0
    
    def leakyReLU(self, x, alpha = 0.01):
        return x if x > 0 else alpha * x

    def leakyReLUDeriv(self, x, alpha = 0.01):
        return 1 if x > 0 else alpha

    def tanh(self, x):
        return math.tanh(x)
    
    def tanhDeriv(self, x):
        return 1 - math.tanh(x) ** 2

    def sigmoid(self, x):
        return 1 / (1 + math.exp(-x))

    def sigmoidDeriv(self, x):
        s = self.sigmoid(x)
        return s * (1 - s)
    
    def initWeights(self, rows, cols):
        return [[random.uniform(-1, 1) for _ in range(cols)] for _ in range(rows)]
    
    def feedforward(self, inputVector):
        activations = [inputVector]
        zs =[]

        for i in range(self.layersCount - 1):
            z = [sum(w * a for w, a in zip(neuron, activations[-1])) + b for neuron, b in zip(self.weights[i], self.biases[i])]
            zs.append(z)           

            if self.activationFunction == MLPAF.reluActivation:
                activations.append([self.ReLU(val) for val in z])

            elif self.activationFunction == MLPAF.leakyReluActivation:
                activations.append([self.leakyReLU(val) for val in z])
                
            elif self.activationFunction == MLPAF.tanhActivation:
                activations.append([self.tanh(val) for val in z])

            else:
                activations.append([self.sigmoid(val) for val in z])

        return activations, zs
    
    def train(self, inputs, outputs, rounds, logs = False):
        assert isinstance(inputs, (list)), "Inputs must be in a list"
        assert isinstance(outputs, (list)), "Outputs must be in a list"
        assert not (hasattr(outputs[0], '__iter__') and len(outputs[0]) != self.structure[-1]), f"Each output must have {self.structure[-1]} values to match the number of output neurons"

        outputs = [[y] if not isinstance(y, list) else y for y in outputs]

        for round in range(rounds):
            totalError = 0

            if logs and (round+1) % 1000 == 0:
                print(f'\n------------------------------------------Round #{round+1}------------------------------------------\n')
            
            for input, output in zip(inputs, outputs):
                activations, zs = self.feedforward(input)
                deltas = [None] * (self.layersCount - 1)

                deltas[-1] = [(yI - aI) * self.sigmoidDeriv(zI) for yI, aI, zI in zip(output, activations[-1], zs[-1])]

                for l in range(self.layersCount - 3, -1, -1):
                    layerWeights = self.weights[l + 1]
                    deltaNext = deltas[l + 1]
                    z = zs[l]
                    if self.activationFunction == MLPAF.reluActivation:
                        sp = [self.ReLUDeriv(zI) for zI in z]

                    elif self.activationFunction == MLPAF.leakyReluActivation:
                        sp = [self.leakyReLUDeriv(zI) for zI in z]

                    elif self.activationFunction == MLPAF.tanhActivation:
                        sp = [self.tanhDeriv(zI) for zI in z]

                    else:
                        sp = [self.sigmoidDeriv(zI) for zI in z]

                    deltas[l] = [sum(layerWeights[k][j] * deltaNext[k] for k in range(len(deltaNext))) * sp[j] for j in range(len(sp))]

                for l in range(self.layersCount - 1):
                    for i in range(len(self.weights[l])):
                        for j in range(len(self.weights[l][i])):
                            self.weights[l][i][j] += self.learningRate * deltas[l][i] * activations[l][j]
                        self.biases[l][i] += self.learningRate * deltas[l][i]

                totalError += sum((yI - aI) ** 2 for yI, aI in zip(output, activations[-1]))

                if logs and (round + 1) % 1000 == 0:
                    print(f"Value: {input} =>\n{self.predict(input, False)}")
                    print(f"Error: {totalError}\n")
                
            self.lastError = totalError
    
    def printData(self):
        print(f'\n------------------------------------------Data------------------------------------------\n')
        if self.activationFunction == MLPAF.reluActivation:
            print("Activation Function: ReLU")
        elif self.activationFunction == MLPAF.leakyReluActivation:
            print("Activation Function: Leaky ReLU")
        elif self.activationFunction == MLPAF.tanhActivation:
            print("Activation Function: Tanh")
        else:
            print("Activation Function: Sigmoid")
        print("Counts:")
        print(f"Inputs: {self.structure[0]}\tHidden: {[self.structure[h] for h in range(1, self.layersCount-1)]}\tOutput: {self.structure[-1]}")
        print(f"Structure: {self.structure}\tLayers: {len(self.structure)}")
        print(f"Last Error: {self.lastError}")
        print(f"\nWeights:\n{self.weights}")
        print(f"\nBias:\n{self.biases}")

    def predictLambda(self, inputs, funcion = lambda x: x, logs = True):
        results = []

        inputs = [[i] if not isinstance(i, list) else i for i in inputs]
        for input in inputs:
            r = [funcion(o) for o in (self.feedforward(input)[0][-1])]
            results.append(r)

            if logs:
                print(f"{input} => {r}")

        return results

    def predictRounded(self, inputs, logs = True):
        results = []

        inputs = [[i] if not isinstance(i, list) else i for i in inputs]
        for input in inputs:
            r = [round(o) for o in (self.feedforward(input)[0][-1])]
            results.append(r)

            if logs:
                print(f"{input} => {r}")

        return results

    def predict(self, inputs, logs = True):
        results = []

        inputs = [[i] if not isinstance(i, list) else i for i in inputs]
        for input in inputs:
            r = [self.feedforward(input)[0][-1]]
            results.append(r)

            if logs:
                print(f"{input} => {r}")

        return results
    
class MLPAFDebug:
    sigmoidActivation = SIGMOID
    reluActivation = RELU
    leakyReluActivation = LEAKYRELU
    tanhActivation = TANH

    def __init__(self, structure, learningRate, activationFunction = SIGMOID):
        assert isinstance(structure, list) and len(structure) >= 3, "You must provide a 3 item list in the neural network structure"

        self.structure = structure
        self.learningRate = learningRate
        self.layersCount = len(structure)
        self.weights = [self.initWeights(n_out, n_in) for n_in, n_out in zip(structure[:-1], structure[1:])]
        self.biases = [[random.uniform(-1, 1) for _ in range(n)] for n in structure[1:]]
        self.activationFunction = activationFunction
        self.lastError = 0

    def ReLU(self, x):
        return max(0, x)
    
    def ReLUDeriv(self, x):
        return 1 if x > 0 else 0
    
    def leakyReLU(self, x, alpha = 0.01):
        return x if x > 0 else alpha * x

    def leakyReLUDeriv(self, x, alpha = 0.01):
        return 1 if x > 0 else alpha

    def tanh(self, x):
        return math.tanh(x)
    
    def tanhDeriv(self, x):
        return 1 - math.tanh(x) ** 2

    def sigmoid(self, x):
        return 1 / (1 + math.exp(-x))

    def sigmoidDeriv(self, x):
        s = self.sigmoid(x)
        return s * (1 - s)
    
    def initWeights(self, rows, cols):
        return [[random.uniform(-1, 1) for _ in range(cols)] for _ in range(rows)]
    
    def feedforward(self, inputVector):
        activations = [inputVector]
        zs =[]

        for i in range(self.layersCount - 1):
            z = [sum(w * a for w, a in zip(neuron, activations[-1])) + b for neuron, b in zip(self.weights[i], self.biases[i])]
            zs.append(z)           

            if self.activationFunction == MLPAFDebug.reluActivation:
                activations.append([self.ReLU(val) for val in z])

            elif self.activationFunction == MLPAFDebug.leakyReluActivation:
                activations.append([self.leakyReLU(val) for val in z])
                
            elif self.activationFunction == MLPAFDebug.tanhActivation:
                activations.append([self.tanh(val) for val in z])

            else:
                activations.append([self.sigmoid(val) for val in z])

        return activations, zs
    
    def train(self, inputs, outputs, rounds, logs = False):
        assert isinstance(inputs, (list)), "Inputs must be in a list"
        assert isinstance(outputs, (list)), "Outputs must be in a list"
        assert not (hasattr(outputs[0], '_iter_') and len(outputs[0]) != self.structure[-1]), f"Each output must have {self.structure[-1]} values to match the number of output neurons"

        outputs = [[y] if not isinstance(y, list) else y for y in outputs]

        for round in range(rounds):
            totalError = 0
            if logs and (round+1) % 1000 == 0:
                print(f'\n------------------------------------------Round #{round+1}------------------------------------------\n')
            else:
                progress = (round + 1) / rounds
                bar_length = 50
                filled_length = int(bar_length * progress)
                bar = '█' * filled_length + '-' * (bar_length - filled_length)
                print(f'\rEntrenamiento: |{bar}| {round+1}/{rounds} rondas    ({progress*100:.2f}%)', end='', flush=True)

                if progress == 1: print()
            
            for input, output in zip(inputs, outputs):
                activations, zs = self.feedforward(input)
                deltas = [None] * (self.layersCount - 1)

                deltas[-1] = [(yI - aI) * self.sigmoidDeriv(zI) for yI, aI, zI in zip(output, activations[-1], zs[-1])]

                for l in range(self.layersCount - 3, -1, -1):
                    layerWeights = self.weights[l + 1]
                    deltaNext = deltas[l + 1]
                    z = zs[l]
                    if self.activationFunction == MLPAFDebug.reluActivation:
                        sp = [self.ReLUDeriv(zI) for zI in z]

                    elif self.activationFunction == MLPAFDebug.leakyReluActivation:
                        sp = [self.leakyReLUDeriv(zI) for zI in z]

                    elif self.activationFunction == MLPAFDebug.tanhActivation:
                        sp = [self.tanhDeriv(zI) for zI in z]

                    else:
                        sp = [self.sigmoidDeriv(zI) for zI in z]

                    deltas[l] = [sum(layerWeights[k][j] * deltaNext[k] for k in range(len(deltaNext))) * sp[j] for j in range(len(sp))]

                for l in range(self.layersCount - 1):
                    for i in range(len(self.weights[l])):
                        for j in range(len(self.weights[l][i])):
                            self.weights[l][i][j] += self.learningRate * deltas[l][i] * activations[l][j]
                        self.biases[l][i] += self.learningRate * deltas[l][i]

                totalError += sum((yI - aI) ** 2 for yI, aI in zip(output, activations[-1]))

                if logs and (round + 1) % 1000 == 0:
                    print(f"Value: {input} =>\n{self.predict(input, False)}")
                    print(f"Error: {totalError}\n")
                
            self.lastError = totalError
    
    def printData(self):
        print(f'\n------------------------------------------Data------------------------------------------\n')
        if self.activationFunction == MLPAFDebug.reluActivation:
            print("Activation Function: ReLU")
        elif self.activationFunction == MLPAFDebug.leakyReluActivation:
            print("Activation Function: Leaky ReLU")
        elif self.activationFunction == MLPAFDebug.tanhActivation:
            print("Activation Function: Tanh")
        else:
            print("Activation Function: Sigmoid")

        print("Counts:")
        print(f"Inputs: {self.structure[0]}\tHidden: {[self.structure[h] for h in range(1, self.layersCount-1)]}\tOutput: {self.structure[-1]}")
        print(f"Structure: {self.structure}\tLayers: {len(self.structure)}")
        print(f"Last Error: {self.lastError}")
        print(f"\nWeights:\n{self.weights}")
        print(f"\nBiases:\n{self.biases}")

    def predictLambda(self, inputs, funcion = lambda x: x, logs = True):
        results = []

        inputs = [[i] if not isinstance(i, list) else i for i in inputs]
        for input in inputs:
            r = [funcion(o) for o in (self.feedforward(input)[0][-1])]
            results.append(r)

            if logs:
                print(f"{input} => {r}")

        return results

    def predictRounded(self, inputs, logs = True):
        results = []

        inputs = [[i] if not isinstance(i, list) else i for i in inputs]
        for input in inputs:
            r = [round(o) for o in (self.feedforward(input)[0][-1])]
            results.append(r)

            if logs:
                print(f"{input} => {r}")

        return results

    def predict(self, inputs, logs = True):
        results = []

        inputs = [[i] if not isinstance(i, list) else i for i in inputs]
        for input in inputs:
            r = [self.feedforward(input)[0][-1]]
            results.append(r)

            if logs:
                print(f"{input} => {r}")

        return results