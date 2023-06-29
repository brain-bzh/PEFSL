import torch
import torch.nn as nn
<<<<<<< Updated upstream
import random  # for manifold mixup
=======
import random # for manifold mixup
>>>>>>> Stashed changes
from functools import partial


class ConvBN2d(nn.Module):
    def __init__(
        self,
        in_f,
        out_f,
        kernel_size=3,
        stride=1,
        padding=1,
        groups=1,
        outRelu=False,
        leaky=True,
    ):
        super(ConvBN2d, self).__init__()
        self.conv = nn.Conv2d(
            in_f,
            out_f,
            kernel_size=kernel_size,
            stride=stride,
            padding=padding,
            groups=groups,
            bias=False,
        )
        self.bn = nn.BatchNorm2d(out_f)
        self.outRelu = outRelu
        self.leaky = leaky
        if leaky:
            nn.init.kaiming_normal_(
                self.conv.weight, mode="fan_out", nonlinearity="leaky_relu"
            )
            nn.init.constant_(self.bn.weight, 1)
            nn.init.constant_(self.bn.bias, 0)

    def forward(self, x, lbda=None, perm=None):
        y = self.bn(self.conv(x))
        if lbda is not None:
            y = lbda * y + (1 - lbda) * y[perm]
        if self.outRelu:
            if not self.leaky:
                return torch.relu(y)
            else:
                return torch.nn.functional.leaky_relu(y, negative_slope=0.1)
        else:
            return y


class BasicBlockRN12(nn.Module):
    def __init__(self, in_f, out_f, use_strides, leaky=True):
        super(BasicBlockRN12, self).__init__()
        self.conv1 = ConvBN2d(in_f, out_f, outRelu=True)
        self.conv2 = ConvBN2d(out_f, out_f, outRelu=True)
        self.leaky = True
        if use_strides:
            self.conv3 = ConvBN2d(out_f, out_f, stride=2)
            self.sc = ConvBN2d(in_f, out_f, kernel_size=1, padding=0, stride=2)
        else:
            self.conv3 = ConvBN2d(out_f, out_f)
            self.sc = ConvBN2d(in_f, out_f, kernel_size=1, padding=0)

    def forward(self, x, lbda=None, perm=None):
        y = self.conv1(x)
        y = self.conv2(y)
        y = self.conv3(y)
        y += self.sc(x)
        if lbda is not None:
            y = lbda * y + (1 - lbda) * y[perm]
        if self.leaky:
            return torch.nn.functional.leaky_relu(y, negative_slope=0.1)
        else:
            return torch.relu(y)


class ResNet9(nn.Module):
    def __init__(self, feature_maps,use_strides=False):
        super(ResNet9, self).__init__()
        self.block1 = BasicBlockRN12(3, feature_maps,use_strides=use_strides)
        self.block2 = BasicBlockRN12(feature_maps, int(2.5 * feature_maps),use_strides=use_strides)
        self.block3 = BasicBlockRN12(int(2.5 * feature_maps), 5 * feature_maps,use_strides=use_strides)
<<<<<<< Updated upstream
        self.mp =nn.Identity() if use_strides else nn.MaxPool2d(2)
=======
        self.mp =nn.Identity() if use_strides else nn.MaxPool2d(2) 
>>>>>>> Stashed changes

    def forward(self, x, mixup=None, lbda=None, perm=None):
        mixup_layer = -1
        if mixup == "mixup":
            mixup_layer = 0
        elif mixup == "manifold mixup":
            mixup_layer = random.randint(0, 4)

        if mixup_layer == 0:
            x = lbda * x + (1 - lbda) * x[perm]
        if x.shape[1] == 1:
            x = x.repeat(1, 3, 1, 1)

        if mixup_layer == 1:
            y = self.mp(self.block1(x, lbda, perm))
        else:
            y = self.mp(self.block1(x))

        if mixup_layer == 2:
            y = self.mp(self.block2(y, lbda, perm))
        else:
            y = self.mp(self.block2(y))

        if mixup_layer == 3:
            y = self.mp(self.block3(y, lbda, perm))
        else:
            y = self.mp(self.block3(y))

        y = y.mean(dim=list(range(2, len(y.shape))))
        return y


class ResNet12Brain(nn.Module):
    def __init__(self, feature_maps,use_strides=False):
        super(ResNet12Brain, self).__init__()
        self.block1 = BasicBlockRN12(3, feature_maps,use_strides=use_strides)
        self.block2 = BasicBlockRN12(feature_maps, int(2.5 * feature_maps),use_strides=use_strides)
        self.block3 = BasicBlockRN12(int(2.5 * feature_maps), 5 * feature_maps,use_strides=use_strides)
        self.block4 = BasicBlockRN12(5 * feature_maps, 10 * feature_maps,use_strides=use_strides)
<<<<<<< Updated upstream
        self.mp =nn.Identity() if use_strides else nn.MaxPool2d(2)
=======
        self.mp =nn.Identity() if use_strides else nn.MaxPool2d(2) 
>>>>>>> Stashed changes

    def forward(self, x, mixup=None, lbda=None, perm=None):
        mixup_layer = -1
        if mixup == "mixup":
            mixup_layer = 0
        elif mixup == "manifold mixup":
            mixup_layer = random.randint(0, 4)

        if mixup_layer == 0:
            x = lbda * x + (1 - lbda) * x[perm]
        if x.shape[1] == 1:
            x = x.repeat(1, 3, 1, 1)

        if mixup_layer == 1:
            y = self.mp(self.block1(x, lbda, perm))
        else:
            y = self.mp(self.block1(x))

        if mixup_layer == 2:
            y = self.mp(self.block2(y, lbda, perm))
        else:
            y = self.mp(self.block2(y))

        if mixup_layer == 3:
            y = self.mp(self.block3(y, lbda, perm))
        else:
            y = self.mp(self.block3(y))

        if mixup_layer == 4:
            y = self.mp(self.block4(y, lbda, perm))
        else:
            y = self.mp(self.block4(y))

        y = y.mean(dim=list(range(2, len(y.shape))))
        return y
