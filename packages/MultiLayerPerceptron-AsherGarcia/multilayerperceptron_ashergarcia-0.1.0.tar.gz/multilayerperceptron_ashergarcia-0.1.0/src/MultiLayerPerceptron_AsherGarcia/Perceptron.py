class Perceptron:
    def __init__(self, weight, rateLearning, bias):
        assert isinstance(weight, (list)), "Weights must be in a list"

        self.weight = weight
        self.rateLearning = rateLearning
        self.bias = bias

    def activate(self, sum):
        return 1 if sum > 0 else 0
        
    def calculate(self, x):
        sum = 0

        if hasattr(x, '__iter__'):
            for j in range(len(x)):
                sum += x[j] * self.weight[j]
        else:
            sum += x*self.weight[0]
        
        sum += self.bias

        return sum

    def train(self, inputs, outputs, rounds, logs = False):
        assert isinstance(inputs, (list)), "Inputs must be in a list"
        assert isinstance(outputs, (list)), "Outputs must be in a list"

        if len(inputs) == len(outputs):

            for round in range(rounds):
                if logs:
                    print(f'\n------------------------------------------Round #{round+1}------------------------------------------\n')

                for input, output in zip(inputs, outputs):
                    gotten = self.activate(self.calculate(input))
                    error =  output - gotten

                    if error != 0:
                        if hasattr(input, '__iter__'):
                            for j in range(len(input)):
                                self.weight[j] += self.rateLearning * error * input[j]
                        else:
                            self.weight[0] += self.rateLearning * error * input

                        self.bias += self.rateLearning * error

                    if logs:
                        print("------------------Inputs-------------------")
                        print(input)
                        print("------------------Outputs------------------")
                        print(f"Expected: {output}\tGotten: {gotten}")
                        print(f"Weigths: {self.weight}\tError: {error}\tBias: {self.bias}\n")

            return 1
        else:
            print("You must provide the same number of inputs and outputs")
            return 0

    def predict(self, inputs):
        assert isinstance(inputs, (list)), "Inputs must be in a list"

        for x in inputs:
            print(f"Inputs: {x}\t->\tResult: {self.activate(self.calculate(x))}")