import os
import torch
from torchvision import datasets
from datasets import load_dataset

from .standard import b_data_standard2d

from byzh.core import B_os

def check(filepaths:list):
    flag = 1
    for filepath in filepaths:
        flag = flag and os.path.exists(filepath)
    return flag

def b_get_MNIST_TV(save_dir='./mnist', mean=None, std=None):
    '''
    采用 torchvision 下载数据集\n

    :param save_dir:
    :return: X_train, y_train, X_test, y_test
    '''
    name = 'mnist'
    downloading_dir = f'{name}_download_dir'
    save_paths = [
        os.path.join(save_dir, f'{name}_X_train.pt'),
        os.path.join(save_dir, f'{name}_y_train.pt'),
        os.path.join(save_dir, f'{name}_X_test.pt'),
        os.path.join(save_dir, f'{name}_y_test.pt'),
    ]

    if check(save_paths):
        X_train = torch.load(save_paths[0])
        y_train = torch.load(save_paths[1])
        X_test = torch.load(save_paths[2])
        y_test = torch.load(save_paths[3])
        return X_train, y_train, X_test, y_test

    # 未标准化
    train_data = datasets.MNIST(root=downloading_dir, train=True, download=True)
    test_data = datasets.MNIST(root=downloading_dir, train=False, download=True)

    # 拆分
    X_train = torch.tensor(train_data.data).unsqueeze(1) / 255.0  # shape [60000, 1, 28, 28]
    y_train = torch.tensor(train_data.targets)  # shape [60000]
    X_test = torch.tensor(test_data.data).unsqueeze(1) / 255.0  # shape [10000, 1, 28, 28]
    y_test = torch.tensor(test_data.targets)  # shape [10000]
    print(f"X_train.shape: {X_train.shape}")
    print(f"y_train.shape: {y_train.shape}")
    print(f"X_test.shape: {X_test.shape}")
    print(f"y_test.shape: {y_test.shape}")
    B, C, H, W = X_train.shape
    print(f"X_train[{B//2}, {C//2}, {H//2}]=\n{X_train[B//2, C//2, H//2]}")

    # 标准化
    X_train, X_test = b_data_standard2d(
        datas=[X_train, X_test],
        template_data=X_train,
        mean=mean,
        std=std
    )

    # 保存
    os.makedirs(save_dir, exist_ok=True)
    torch.save(X_train, save_paths[0])
    torch.save(y_train, save_paths[1])
    torch.save(X_test,save_paths[2])
    torch.save(y_test,save_paths[3])

    B_os.rm(downloading_dir)

    return X_train, y_train, X_test, y_test


# def b_get_mnist2(save_dir='./mnist', mean=0.1307, std=0.3081) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
#     '''
#     采用 datasets 下载 mnist 数据集\n
#     https://huggingface.co/datasets/ylecun/mnist\n
#     https://hf-mirror.com/datasets/ylecun/mnist\n
#
#     :param save_dir:
#     :return: train_images, train_labels, test_images, test_labels
#     '''
#     if check(save_dir, 'mnist'):
#         train_images = np.load(os.path.join(save_dir,'mnist_train_images.npy'))
#         train_labels = np.load(os.path.join(save_dir,'mnist_train_labels.npy'))
#         test_images = np.load(os.path.join(save_dir,'mnist_test_images.npy'))
#         test_labels = np.load(os.path.join(save_dir,'mnist_test_labels.npy'))
#         return train_images, train_labels, test_images, test_labels
#
#     from datasets import load_dataset
#     dataset = load_dataset("mnist")
#
#     train_images = np.stack([np.array(example['image']) for example in dataset['train']])
#     train_images = train_images[:, np.newaxis, :, :]
#     train_labels = np.array([example['label'] for example in dataset['train']])
#
#     test_images = np.stack([np.array(example['image']) for example in dataset['test']])
#     test_images = test_images[:, np.newaxis, :, :]
#     test_labels = np.array([example['label'] for example in dataset['test']])
#
#     # print(train_images[4000][0][6])
#
#     from .standard import b_data_standard2d
#     train_images, test_images = b_data_standard2d(
#         datas=[train_images, test_images],
#         template_data=train_images,
#         mean=mean,
#         std=std
#     )
#     # print(train_images[4000][0][6])
#
#     save_npys(save_dir, train_images, train_labels, 'mnist_train')
#     save_npys(save_dir, test_images, test_labels, 'mnist_test')
#
#     return train_images, train_labels, test_images, test_labels


def b_get_FashionMNIST_TV(save_dir='./fashion_mnist', mean=None, std=None):
    '''
    采用 torchvision 下载数据集\n

    :param save_dir:
    :return: X_train, y_train, X_test, y_test
    '''
    name = 'fashion_mnist'
    downloading_dir = f'{name}_download_dir'
    save_paths = [
        os.path.join(save_dir, f'{name}_X_train.pt'),
        os.path.join(save_dir, f'{name}_y_train.pt'),
        os.path.join(save_dir, f'{name}_X_test.pt'),
        os.path.join(save_dir, f'{name}_y_test.pt'),
    ]

    if check(save_paths):
        X_train = torch.load(save_paths[0])
        y_train = torch.load(save_paths[1])
        X_test = torch.load(save_paths[2])
        y_test = torch.load(save_paths[3])
        return X_train, y_train, X_test, y_test

    # 未标准化
    train_data = datasets.FashionMNIST(root=downloading_dir, train=True, download=True)
    test_data = datasets.FashionMNIST(root=downloading_dir, train=False, download=True)

    # 拆分
    X_train = torch.tensor(train_data.data).unsqueeze(1) / 255.0  # shape [60000, 1, 28, 28]
    y_train = torch.tensor(train_data.targets)  # shape [60000]
    X_test = torch.tensor(test_data.data).unsqueeze(1) / 255.0  # shape [10000, 1, 28, 28]
    y_test = torch.tensor(test_data.targets)  # shape [10000]
    print(f"X_train.shape: {X_train.shape}")
    print(f"y_train.shape: {y_train.shape}")
    print(f"X_test.shape: {X_test.shape}")
    print(f"y_test.shape: {y_test.shape}")
    B, C, H, W = X_train.shape
    print(f"X_train[{B // 2}, {C // 2}, {H // 2}]=\n{X_train[B // 2, C // 2, H // 2]}")

    # 标准化
    X_train, X_test = b_data_standard2d(
        datas=[X_train, X_test],
        template_data=X_train,
        mean=mean,
        std=std
    )

    # 保存
    os.makedirs(save_dir, exist_ok=True)
    torch.save(X_train, save_paths[0])
    torch.save(y_train, save_paths[1])
    torch.save(X_test, save_paths[2])
    torch.save(y_test, save_paths[3])

    B_os.rm(downloading_dir)

    return X_train, y_train, X_test, y_test

def b_get_CIFAR10_TV(save_dir='./cifar10', mean=None, std=None):
    '''
    采用 torchvision 下载数据集\n

    :param save_dir:
    :return: X_train, y_train, X_test, y_test
    '''
    name = 'cifar10'
    downloading_dir = f'{name}_download_dir'
    save_paths = [
        os.path.join(save_dir, f'{name}_X_train.pt'),
        os.path.join(save_dir, f'{name}_y_train.pt'),
        os.path.join(save_dir, f'{name}_X_test.pt'),
        os.path.join(save_dir, f'{name}_y_test.pt'),
    ]

    if check(save_paths):
        X_train = torch.load(save_paths[0])
        y_train = torch.load(save_paths[1])
        X_test = torch.load(save_paths[2])
        y_test = torch.load(save_paths[3])
        return X_train, y_train, X_test, y_test

    # 未标准化
    train_data = datasets.CIFAR10(root=downloading_dir, train=True, download=True)
    test_data = datasets.CIFAR10(root=downloading_dir, train=False, download=True)

    # 拆分
    X_train = torch.tensor(train_data.data).permute(0, 3, 1, 2) / 255.0  # shape [50000, 3, 32, 32]
    y_train = torch.tensor(train_data.targets)  # shape [50000]
    X_test = torch.tensor(test_data.data).permute(0, 3, 1, 2) / 255.0  # shape [10000, 3, 32, 32]
    y_test = torch.tensor(test_data.targets)  # shape [10000]
    print(f"X_train.shape: {X_train.shape}")
    print(f"y_train.shape: {y_train.shape}")
    print(f"X_test.shape: {X_test.shape}")
    print(f"y_test.shape: {y_test.shape}")
    B, C, H, W = X_train.shape
    print(f"X_train[{B // 2}, {C // 2}, {H // 2}]=\n{X_train[B // 2, C // 2, H // 2]}")

    # 标准化
    X_train, X_test = b_data_standard2d(
        datas=[X_train, X_test],
        template_data=X_train,
        mean=mean,
        std=std
    )

    # 保存
    os.makedirs(save_dir, exist_ok=True)
    torch.save(X_train, save_paths[0])
    torch.save(y_train, save_paths[1])
    torch.save(X_test, save_paths[2])
    torch.save(y_test, save_paths[3])

    B_os.rm(downloading_dir)

    return X_train, y_train, X_test, y_test

def b_get_CIFAR100_TV(save_dir='./cifar100', mean=None, std=None):
    '''
    采用 torchvision 下载数据集\n

    :param save_dir:
    :return: X_train, y_train, X_test, y_test
    '''
    name = 'cifar100'
    downloading_dir = f'{name}_download_dir'
    save_paths = [
        os.path.join(save_dir, f'{name}_X_train.pt'),
        os.path.join(save_dir, f'{name}_y_train.pt'),
        os.path.join(save_dir, f'{name}_X_test.pt'),
        os.path.join(save_dir, f'{name}_y_test.pt'),
    ]

    if check(save_paths):
        X_train = torch.load(save_paths[0])
        y_train = torch.load(save_paths[1])
        X_test = torch.load(save_paths[2])
        y_test = torch.load(save_paths[3])
        return X_train, y_train, X_test, y_test

    # 未标准化
    train_data = datasets.CIFAR100(root=downloading_dir, train=True, download=True)
    test_data = datasets.CIFAR100(root=downloading_dir, train=False, download=True)

    # 拆分
    X_train = torch.tensor(train_data.data).permute(0, 3, 1, 2) / 255.0  # shape [50000, 3, 32, 32]
    y_train = torch.tensor(train_data.targets)  # shape [50000]
    X_test = torch.tensor(test_data.data).permute(0, 3, 1, 2) / 255.0  # shape [10000, 3, 32, 32]
    y_test = torch.tensor(test_data.targets)  # shape [10000]
    print(f"X_train.shape: {X_train.shape}")
    print(f"y_train.shape: {y_train.shape}")
    print(f"X_test.shape: {X_test.shape}")
    print(f"y_test.shape: {y_test.shape}")
    B, C, H, W = X_train.shape
    print(f"X_train[{B // 2}, {C // 2}, {H // 2}]=\n{X_train[B // 2, C // 2, H // 2]}")

    # 标准化
    X_train, X_test = b_data_standard2d(
        datas=[X_train, X_test],
        template_data=X_train,
        mean=mean,
        std=std
    )

    # 保存
    os.makedirs(save_dir, exist_ok=True)
    torch.save(X_train, save_paths[0])
    torch.save(y_train, save_paths[1])
    torch.save(X_test, save_paths[2])
    torch.save(y_test, save_paths[3])

    B_os.rm(downloading_dir)

    return X_train, y_train, X_test, y_test
