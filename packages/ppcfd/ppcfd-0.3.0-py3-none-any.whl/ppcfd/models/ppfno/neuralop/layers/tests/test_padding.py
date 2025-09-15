import paddle
from ..padding import DomainPadding
import pytest


@pytest.mark.parametrize('mode', ['one-sided', 'symmetric'])
def test_DomainPadding(mode):
    out_size = {'one-sided': 12, 'symmetric': 14}
    data = paddle.randn(shape=(2, 3, 10, 10))
    padder = DomainPadding(0.2, mode)
    padded = padder.pad(data)
    target_shape = list(tuple(padded.shape))
    target_shape[-1] = target_shape[-2] = out_size[mode]
    assert list(tuple(padded.shape)) == target_shape
    unpadded = padder.unpad(padded)
    assert tuple(unpadded.shape) == tuple(data.shape)
