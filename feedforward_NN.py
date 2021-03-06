#!/usr/bin/env python
# coding: utf-8

import numpy as np
import matplotlib.pyplot as plt
import sys
from sklearn.datasets import fetch_mldata
from sklearn.cross_validation import train_test_split
from sklearn.preprocessing import LabelBinarizer

"""
三層フィードフォワード型のニューラルネットとバックプロパゲーションによる学習
"""
# multi-layer perceptron
# 参照　aidiary(scikit-learnの扱い)、『深層学習』
# 参照可能　DLtutorials MLPのtips and tricks
#　実装環境:python numpy matplotlib scikit-learn

"""
適宜自分でコメント
入力は10*10 ５種類から　配列か読み込み
各画素値は0~1の浮動小数点
ノイズ(d%は確率d%で各画素をランダム画素値に置換)を加えた場合の性能変化　0~25%
ノイズ耐性は何に左右されるか考えて実験で示す
注意:ニューロン数、結合荷重初期値、係数、学習則なんか　中間層のニューロンと初期値
1.中間層のニューロンは何をしてるか:
各ニューロンの受容野(重みが有意に大きい入力範囲)
最適刺激(出力が最大になる入力パタン)
cf. 重みベクトルとの内積が最大になるベクトル=重みと同じ(入力画像として表す)
を調べる.
識別能力を維持できる最少のニューロン数の時どうなるか.
2.画像特徴抽出をして、各特徴検出器の出力をニューラルネットの入力としてみたら性能はどう変わるか.
"""

# 中間層は正規化線形関数
# 多クラス分類なので出力層の活性化関数はソフトマックス関数で、誤差関数は交差エントロピー式
class ff_NN:
    def __init__(self, n_input, n_internal, n_output):
        # 各層のセット(バイアス項を追加)
        self.n_input = n_input + 1
        self.n_internal = n_internal + 1
        self.n_output = n_output
        # 重みを初期化 -1.0~1.0　一様乱数
        self.inp_int_weight = np.random.uniform(-1.0, 1.0, (self.n_internal, self.n_input))
        self.int_out_weight = np.random.uniform(-1.0, 1.0, (self.n_output, self.n_internal))
        # 入力に対するノイズ率
        self.noise_rate = 0.0

    # 訓練データに対するノイズ付与
    def noise(self, noise_rate):
        self.noise_rate = noise_rate

    # 学習
    def train(self, X, Y, epoch):
        # 学習係数
        #　TODO:Adagradの実装、慣性項は付与するか
        learning = 0.05

        # バイアス項を追加
        X = np.hstack([np.ones([X.shape[0], 1]), X])
        Y = np.array(Y)

        print "Training for %d epochs" %epoch

        for i in range(epoch):
            # データ選択
            ind = np.random.randint(X.shape[0])
            # ノイズ付与
            for j in range(1, len(X[ind])):
                pixel_noise = np.random.rand()
                if pixel_noise <= self.noise_rate:
                    X[ind][j] = np.random.rand()

            # Forward Propagation
            inp_l = X[ind]
            int_l = rectifier(np.dot(self.inp_int_weight, inp_l))
            out_l = softmax(np.dot(self.int_out_weight, int_l))

            # Back Propagation
            # 誤差の計算
            out_delta = out_l - Y[ind]
            int_delta = rectifier_dot(np.dot(self.inp_int_weight, inp_l)) * np.dot(self.int_out_weight.T, out_delta)
            # 重みの更新
            inp_l = np.atleast_2d(inp_l)
            int_delta = np.atleast_2d(int_delta)
            self.inp_int_weight -= learning * np.dot(int_delta.T, inp_l)
            int_l = np.atleast_2d(int_l)
            out_delta = np.atleast_2d(out_delta)
            self.int_out_weight -= learning * np.dot(out_delta.T, int_l)

    # 評価
    def test(self, X, Y):
        correct = 0.0
        false = 0.0
        for i in range(X.shape[0]):
            x = np.array(X[i])
            x_inp = np.insert(x, 0, 1)
            x_int = rectifier(np.dot(self.inp_int_weight, x_inp))
            x_out = softmax(np.dot(self.int_out_weight, x_int))
            label_predict = np.argmax(x_out)
            if label_predict == Y[i]:
                correct += 1
            else:
                false += 1
        num_test = correct + false
        correct_rate = (correct / num_test) * 100
        print "Identification Rate : %f percent out of %d" % (correct_rate, num_test)
        return correct_rate

    # 中間層の可視化
    def print_internal(self, thre=-1):
        # 重みの正規化、負の値は排除 black is 0, white is 1
        bias, img = np.hsplit(self.inp_int_weight, [1])
        plt.clf()
        for i, unit in enumerate(np.array(img)):
            unit = unit / np.fabs(unit.max())
            for j in range(0, len(unit)):
                if unit[j] <= 0.0:
                    unit[j] = 0.0
                if thre != -1:
                    if unit[j] >= thre:
                        unit[j] = 1.0
                    else:
                        unit[j] = 0.0

            plt.subplot(4, 4, i + 1)
            plt.axis('off') #[0, 27, 0, 27]
            plt.imshow(unit.reshape(28, 28), interpolation='nearest')
            plt.title('%i' % i, fontsize=10)
            plt.gray()
        plt.show()
        #plt.savefig('inp_int_weight.png')

    # TODO
    # 三層自己符号化 重み共有
    # 初期値にDenoising auto-encoder ランダム初期値と比較

    # 重みの保存
    def save_weight(self, path):
        np.savez(path, inp_int = self.inp_int_weight, int_out = self.int_out_weight)

    # 重みの読み込み
    def load_weight(self, path):
        npzfile = np.load(path)
        self.inp_int_weight = npzfile['inp_int']
        self.int_out_weight = npzfile['int_out']

# 活性化関数としてsigmoidやrelu
# ReLU
def rectifier(x):
    return x * (x > 0)

def rectifier_dot(x):
    return 1. * (x > 0)

#　出力はソフトマックスで→重み減衰をつけるか
# softmax
def softmax(x):
    exp_x = np.exp(x)
    return exp_x / np.sum(exp_x)

# 入力画像の表示
def print_img(x, y):
    if x.size == 28*28 + 1:
        bias, x_1 = np.hsplit(x,[1])
    else:
        x_1 = x
    x_2 = x_1.reshape((28, 28))
    plt.clf()
    plt.imshow(x_2, interpolation='none')
    plt.title('%i' % y)
    plt.axis('off')
    plt.gray()
    plt.show()

# 画像特徴抽出
def pre_cv(x):
    # TODO
    return x


if __name__ == '__main__':

    #　TODO:Arduinoによるデータセットの自作
    # 0~9の手書き数字認識
    # MNIST 28*28 70000samples
    mnist_org = fetch_mldata('MNIST original', data_home=".")
    X = mnist_org.data
    Y = mnist_org.target
    # 入力データの正規化、訓練・テスト分離、教師データの変換(目標:0010000等)
    X = X.astype(np.float64)
    X = X / X.max()
    X_training, X_testing, Y_training, Y_testing = train_test_split(X, Y, test_size = 0.1)
    label_training = LabelBinarizer().fit_transform(Y_training)

    """
    # ノイズ率別の識別率
    for noise_rate in range(0, 30, 5):

        # ニューラルネットの構築
        feedforward_NN = ff_NN(28*28, 9, 10)

        # 重みの読み込み
        #feedforward_NN.load_weight('ff_NN_weight.npz')

        print ""
        print "Noise Rate : %f" %(0.01*noise_rate)

        # 学習と評価
        feedforward_NN.noise(0.01*noise_rate)
        num_epochs = [0]
        before_training = feedforward_NN.test(X_testing, Y_testing)
        correct_list = [before_training]
        for i in range(20):
            feedforward_NN.train(X_training, label_training, 1000)
            correct_case = feedforward_NN.test(X_testing, Y_testing)
            num_epochs.append(1000 * (i + 1))
            correct_list.append(correct_case)
        num_epochs = np.array(num_epochs)
        correct_list = np.array(correct_list)
        #　学習過程の図式化
        plt.plot(num_epochs, correct_list, '-o')

    plt.grid()
    plt.legend([' 0[%]', ' 5[%]', '10[%]', '15[%]', '20[%]', '25[%]'], title='noise rate', loc='best')
    plt.title('identification rate (based on noise rates)')
    plt.xlabel('number of epochs [times]')
    plt.ylabel('identification rate [%]')
    plt.show()
    #plt.savefig("identification_rate.png")
    #plt.clf()
    """

    # ニューラルネットの構築
    #　中間層の素子数をいじる
    feedforward_NN = ff_NN(28*28, 15, 10)

    # 重みの読み込み
    #feedforward_NN.load_weight('ff_NN_weight.npz')

    # 学習と評価
    # E^RMSによる打ち切りもあり
    num_epochs = [0]
    before_training = feedforward_NN.test(X_testing, Y_testing)
    correct_list = [before_training]
    for i in range(20):
        feedforward_NN.train(X_training, label_training, 1000)
        correct_case = feedforward_NN.test(X_testing, Y_testing)
        num_epochs.append(1000 * (i + 1))
        correct_list.append(correct_case)
    num_epochs = np.array(num_epochs)
    correct_list = np.array(correct_list)
    #　学習過程の図式化
    plt.plot(num_epochs, correct_list, '-o')
    plt.grid()
    plt.title('identification rate (internal layers:9+1)')
    plt.xlabel('number of epochs [times]')
    plt.ylabel('identification rate [%]')
    plt.show()

    # 中間層の表示 中間層数に合わせていじる必要あり
    feedforward_NN.print_internal(0.7)

    # 重みの保存
    #feedforward_NN.save_weight('ff_NN_weight.npz')
