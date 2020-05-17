import torch
import torch.nn as nn
import torchvision
import time
import numpy as np
import sys

def get_model_op(model_,print_flag = False):
    print('/********************* modules *******************/')
    op_dict = {}
    idx = 0
    for m in model_.modules():
        idx += 1
        if isinstance(m, nn.Conv2d):
            if 'Conv2d' not in op_dict.keys():
                op_dict['Conv2d'] = 1
            else:
                op_dict['Conv2d'] += 1
            if print_flag:
                print('{})  {}'.format(idx,m))
            pass
        elif isinstance(m, nn.BatchNorm2d):
            if 'BatchNorm2d' not in op_dict.keys():
                op_dict['BatchNorm2d'] = 1
            else:
                op_dict['BatchNorm2d'] += 1
            if print_flag:
                print('{})  {}'.format(idx,m))
            pass
        elif isinstance(m, nn.Linear):
            if 'Linear' not in op_dict.keys():
                op_dict['Linear'] = 1
            else:
                op_dict['Linear'] += 1
            if print_flag:
                print('{})  {}'.format(idx,m))
            pass
        elif isinstance(m, nn.Sequential):
            if print_flag:
                print('*******************{})  {}'.format(idx,m))
            for n in m:
                if print_flag:
                    print('{})  {}'.format(idx,n))
                if 'Conv2d' not in op_dict.keys():
                    op_dict['Conv2d'] = 1
                else:
                    op_dict['Conv2d'] += 1
                if 'BatchNorm2d' not in op_dict.keys():
                    op_dict['BatchNorm2d'] = 1
                else:
                    op_dict['BatchNorm2d'] += 1
                if 'Linear' not in op_dict.keys():
                    op_dict['Linear'] = 1
                else:
                    op_dict['Linear'] += 1
                if 'ReLU6' not in op_dict.keys():
                    op_dict['ReLU6'] = 1
                else:
                    op_dict['ReLU6'] += 1
            pass
        elif isinstance(m, nn.ReLU6):
            if print_flag:
                print('{})  {}'.format(idx,m))
            if 'ReLU6' not in op_dict.keys():
                op_dict['ReLU6'] = 1
            else:
                op_dict['ReLU6'] += 1
            pass
        elif isinstance(m, nn.Module):
            if print_flag:
                print('{})  {}'.format(idx,m))
            for n in m.modules():
                if isinstance(n, nn.Conv2d):
                    if print_flag:
                        print('{})  {}'.format(idx,n))
                    if 'Conv2d' not in op_dict.keys():
                        op_dict['Conv2d'] = 1
                    else:
                        op_dict['Conv2d'] += 1
                    if 'BatchNorm2d' not in op_dict.keys():
                        op_dict['BatchNorm2d'] = 1
                    else:
                        op_dict['BatchNorm2d'] += 1
                    if 'Linear' not in op_dict.keys():
                        op_dict['Linear'] = 1
                    else:
                        op_dict['Linear'] += 1
                    if 'ReLU6' not in op_dict.keys():
                        op_dict['ReLU6'] = 1
                    else:
                        op_dict['ReLU6'] += 1
                    pass
            pass

        else:
            if print_flag:
                print('{})  {}'.format(idx,m))
            pass

    # print('\n/********************** {} ********************/\n'.format(ops.network))
    for key in op_dict.keys():
        print(' operation - {} : {}'.format(key,op_dict[key]))

class DummyModule(nn.Module):
    def __init__(self):
        super(DummyModule, self).__init__()

    def forward(self, x):
        return x

def fuse(conv, bn):
    # https://tehnokv.com/posts/fusing-batchnorm-and-conv/
    with torch.no_grad():
        # init
        if isinstance(conv, nn.Conv2d):
            fusedconv = torch.nn.Conv2d(conv.in_channels,
                                        conv.out_channels,
                                        kernel_size=conv.kernel_size,
                                        stride=conv.stride,
                                        padding=conv.padding,
                                        bias=True)
        elif isinstance(conv, nn.ConvTranspose2d):  # not supprot nn.ConvTranspose2d
            fusedconv = nn.ConvTranspose2d(
                conv.in_channels,
                conv.out_channels,
                kernel_size=conv.kernel_size,
                stride=conv.stride,
                padding=conv.padding,
                output_padding=conv.output_padding,
                bias=True)
        else:
            print("error")
            exit()

        # prepare filters
        w_conv = conv.weight.clone().view(conv.out_channels, -1)
        w_bn = torch.diag(bn.weight.div(torch.sqrt(bn.eps + bn.running_var)))
        fusedconv.weight.copy_(torch.mm(w_bn, w_conv).view(fusedconv.weight.size()))

        # prepare spatial bias
        if conv.bias is not None:
            b_conv = conv.bias
            #b_conv = conv.bias.mul(bn.weight.div(torch.sqrt(bn.running_var + bn.eps)))  #  maybe, you should this one ?
        else:
            b_conv = torch.zeros(conv.weight.size(0))
        b_bn = bn.bias - bn.weight.mul(bn.running_mean).div(torch.sqrt(bn.running_var + bn.eps))
        fusedconv.bias.copy_(b_conv + b_bn)

        return fusedconv

idxx = 0
def fuse_module(m):
    global idxx
    children = list(m.named_children())
    c = None
    cn = None

    for name, child in children:
        idxx += 1

        if (idxx<=56) or (76>idxx>=60):
            print('--------->> {} fuse_module'.format(idxx))
        else:
            continue
        # print("name {}, child {}".format(name, child))
        if isinstance(child, nn.BatchNorm2d) and c is not None:
            bc = fuse(c, child)
            m._modules[cn] = bc
            # print('DummyModule()  : ',DummyModule())
            m._modules[name] = DummyModule()
            c = None
        elif isinstance(child, nn.Conv2d):
            c = child
            cn = name
        else:
            fuse_module(child)

def fuse_landmarks_module(m):

    children = list(m.named_children())
    c = None
    cn = None

    for name, child in children:

        # print("name {}, child {}".format(name, child))
        if isinstance(child, nn.BatchNorm2d) and c is not None:
            bc = fuse(c, child)
            m._modules[cn] = bc
            # print('DummyModule()  : ',DummyModule())
            m._modules[name] = DummyModule()
            c = None
        elif isinstance(child, nn.Conv2d):
            c = child
            cn = name
        else:
            fuse_landmarks_module(child)

def test_net(ops,m):

    use_cuda = torch.cuda.is_available()
    use_cpu = False
    if ops.force_cpu or use_cuda == False:
        p = torch.randn([1, 3, 256, 256])
        device = torch.device("cpu")
        use_cpu = True
    else:
        p = torch.randn([1, 3, 256, 256]).cuda()
        device = torch.device("cuda:0")

    count = 50
    time_org = []
    m_o = m.to(device)
    get_model_op(m_o)
    # print(m)
    for i in range(count):
        s1 = time.time()
        if use_cpu:
            o_output = m_o(p)
        else:
            o_output = m_o(p).cpu()
        s2 = time.time()
        time_org.append(s2 - s1)
        print("Original time: ", s2 - s1)
    print('------------------------------------>>>>')

    fuse_module(m.to(torch.device("cpu")))

    # print(m)

    m_f = m.to(device)
    get_model_op(m_f)

    time_fuse = []
    for i in range(count):
        s1 = time.time()
        if use_cpu:
            f_output = m_f(p)
        else:
            f_output = m_f(p).cpu()
        s2 = time.time()
        time_fuse.append(s2 - s1)
        print("Fused time: ", s2 - s1)

    print("-" * 50)
    print("org time:", np.mean(time_org))
    print("fuse time:", np.mean(time_fuse))
    for o in o_output:
        print("org size:", o.size())
    for o in f_output:
        print("fuse size:", o.size())
    for i in range(len(o_output)):
        assert o_output[i].size()==f_output[i].size()
        print("output[{}] max abs diff: {}".format(i, (o_output[i] - f_output[i]).abs().max().item()))
        print("output[{}] MSE diff: {}".format(i, nn.MSELoss()(o_output[i], f_output[i]).item()))


def acc_model(ops,m):
    print('\n-------------------------------->>> before acc model')
    get_model_op(m)
    fuse_module(m)
    print('\n-------------------------------->>> after acc model')
    get_model_op(m)

    return m

def acc_landmarks_model(ops,m):
    print('\n-------------------------------->>> before acc model')
    get_model_op(m)
    fuse_landmarks_module(m)
    print('\n-------------------------------->>> after acc model')
    get_model_op(m)

    return m

if __name__ == "__main__":
    import os
    import argparse
    from models.resnet import resnet18, resnet34, resnet50, resnet101, resnet152

    parser = argparse.ArgumentParser(description=' Acc Model')

    parser.add_argument('--network',  type=str, default='resnet_101',
        help='Backbone network : resnet_18,resnet_34,resnet_50,resnet_101,resnet_152,mobilenetv2')
    parser.add_argument('--model', type=str, default = './resnet101/model_epoch-1300.pth',
        help = 'model') # 模型路径
    parser.add_argument('--input_shape', type=tuple , default = (1,3,256,256),
        help = 'input_shape') #
    parser.add_argument('--num_classes', type=int , default = 196,
        help = 'num_classes') # 模型输入图片颜色偏置
    parser.add_argument('--force_cpu', type=bool, default = False,
        help = 'force_cpu') # 前向推断硬件选择
    parser.add_argument('--GPUS', type=str, default = '0',
        help = 'GPUS') # GPU选择

    print('\n/******************* {} ******************/\n'.format(parser.description))
    #--------------------------------------------------------------------------
    ops = parser.parse_args()# 解析添加参数
    #--------------------------------------------------------------------------
    print('----------------------------------')

    unparsed = vars(ops) # parse_args()方法的返回值为namespace，用vars()内建函数化为字典
    for key in unparsed.keys():
        print('{} : {}'.format(key,unparsed[key]))

    os.environ['CUDA_VISIBLE_DEVICES'] = ops.GPUS
    #---------------------------------------------------------------- 构建 landmarks 模型
    if ops.network == 'resnet_18':
        model_=resnet18(num_classes=ops.num_classes, img_size=ops.input_shape[2])
    elif ops.network == 'resnet_34':
        model_=resnet34(num_classes=ops.num_classes, img_size=ops.input_shape[2])
    elif ops.network == 'resnet_50':
        model_=resnet50(num_classes=ops.num_classes, img_size=ops.input_shape[2])
    elif ops.network == 'resnet_101':
        model_=resnet101(num_classes=ops.num_classes, img_size=ops.input_shape[2])
    elif ops.network == 'resnet_152':
        model_=resnet152(num_classes=ops.num_classes, img_size=ops.input_shape[2])
    elif ops.network == 'mobilenetv2':
        model_=MobileNetV2(n_class =ops.num_classes, input_size=ops.input_shape[2])
    else:
        print('error no the struct model : {}'.format(ops.network))

    # 加载测试模型
    if os.access(ops.model,os.F_OK):# checkpoint
        chkpt = torch.load(ops.model, map_location=lambda storage, loc: storage)
        model_.load_state_dict(chkpt)
        print(' \nload model : {}'.format(ops.model))

    model_.eval()
    test_net(ops,model_)
