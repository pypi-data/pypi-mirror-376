from MultiLayerPerceptron.Perceptron import Perceptron
import unittest

class TestMLP(unittest.TestCase):
    def testMLP(self):
        inputs = [
            [0, 0],
            [0, 1],
            [1, 0],
            [1, 1]
        ]

        outputs = [0, 0, 0, 1]

        perceptron = Perceptron([0.0, 0.0], 0.1, 0)
        perceptron.train(inputs, outputs, 100, True)
        perceptron.predict([[0, 0], [1, 1], [0, 1]])

if __name__ == "__main__":
    unittest.main()