from MultiLayerPerceptron.MultiLayerPerceptron import MLPAFDebug as MLP
import unittest

class TestMLP(unittest.TestCase):
    def testMLP(self):
        inputs = [
            [0, 0, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0],
            [0, 0, 1, 1],
            [0, 1, 0, 0],
            [0, 1, 0, 1],
            [0, 1, 1, 0],
            [0, 1, 1, 1],
            [1, 0, 0, 0],
            [1, 0, 0, 1],
            [1, 0, 1, 0],
            [1, 0, 1, 1],
            [1, 1, 0, 0],
            [1, 1, 0, 1],
            [1, 1, 1, 0],
            [1, 1, 1, 1],
        ]

        outputs = [
            [0, 0, 0, 1, 1, 1, 1, 1],
            [0, 1, 0, 1, 1, 1, 1, 0],
            [0, 1, 0, 1, 1, 1, 0, 1],
            [0, 1, 0, 1, 1, 1, 0, 0],
            [0, 1, 1, 0, 1, 0, 1, 1],
            [0, 1, 1, 0, 1, 0, 1, 0],
            [0, 1, 1, 0, 1, 0, 0, 1],
            [0, 1, 1, 0, 1, 0, 0, 0],
            [0, 1, 1, 0, 0, 1, 1, 1],
            [0, 1, 1, 0, 0, 1, 1, 0],
            [0, 1, 1, 0, 0, 1, 0, 1],
            [0, 1, 1, 0, 0, 1, 0, 0],
            [0, 1, 0, 1, 0, 0, 1, 1],
            [0, 1, 0, 1, 0, 0, 1, 0],
            [0, 1, 0, 1, 0, 0, 0, 1],
            [1, 1, 0, 1, 0, 0, 0, 0],
        ]

        mlp = MLP([len(inputs[0]), 8, len(outputs[0])], 0.1, MLP.tanhActivation)
        mlp.train(inputs, outputs, 20000)
        mlp.printData()

        print("Test: ")
        mlp.predictLambda(inputs, lambda r: [round(r)])

if __name__ == "__main__":
    unittest.main()