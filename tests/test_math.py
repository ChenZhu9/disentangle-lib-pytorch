#  ~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~
#  MIT License
#
#  Copyright (c) 2021 Nathan Juraj Michlo
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
#  ~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~

import numpy as np
import pytest
import torch
from scipy.stats import gmean
from scipy.stats import hmean

from disent.data.groundtruth import XYSquaresData
from disent.dataset.groundtruth import GroundTruthDataset
from disent.dataset.groundtruth import GroundTruthDatasetPairs
from disent.transform import ToStandardisedTensor
from disent.transform.functional import conv2d_channel_wise
from disent.transform.functional import conv2d_channel_wise_fft
from disent.transform.kernel import make_gaussian_kernel_2d
from disent.util import to_numpy
from disent.util.math import dct
from disent.util.math import dct2
from disent.util.math import idct
from disent.util.math import idct2
from disent.util.math import torch_corr_matrix
from disent.util.math import torch_cov_matrix
from disent.util.math import torch_mean_generalized


def test_cov_corr():

    for i in range(5, 1000, 250):
        for j in range(2, 100, 25):

            # these match when torch.float64 is used, not when torch float32 is used...
            xs = torch.randn(i, j, dtype=torch.float64)

            np_cov = torch.from_numpy(np.cov(to_numpy(xs), rowvar=False, ddof=0)).to(xs.dtype)
            np_cor = torch.from_numpy(np.corrcoef(to_numpy(xs), rowvar=False, ddof=0)).to(xs.dtype)

            cov = torch_cov_matrix(xs)
            cor = torch_corr_matrix(xs)

            assert torch.allclose(np_cov, cov)
            assert torch.allclose(np_cor, cor)


def test_generalised_mean():
    xs = torch.abs(torch.randn(2, 1000, 3, dtype=torch.float64))

    # normal
    assert torch.allclose(torch_mean_generalized(xs, p='arithmetic', dim=1), torch.mean(xs, dim=1))
    assert torch.allclose(torch_mean_generalized(xs, p=1, dim=1), torch.mean(xs, dim=1))

    # scipy equivalents
    assert torch.allclose(torch_mean_generalized(xs, p='geometric', dim=1), torch.as_tensor(gmean(xs, axis=1)))
    assert torch.allclose(torch_mean_generalized(xs, p='harmonic', dim=1), torch.as_tensor(hmean(xs, axis=1)))
    assert torch.allclose(torch_mean_generalized(xs, p=0, dim=1), torch.as_tensor(gmean(xs, axis=1)))
    assert torch.allclose(torch_mean_generalized(xs, p=-1, dim=1), torch.as_tensor(hmean(xs, axis=1)))
    assert torch.allclose(torch_mean_generalized(xs, p=0), torch.as_tensor(gmean(xs, axis=None)))  # scipy default axis is 0
    assert torch.allclose(torch_mean_generalized(xs, p=-1), torch.as_tensor(hmean(xs, axis=None)))  # scipy default axis is 0

    # min max
    assert torch.allclose(torch_mean_generalized(xs, p='maximum', dim=1), torch.max(xs, dim=1).values)
    assert torch.allclose(torch_mean_generalized(xs, p='minimum', dim=1), torch.min(xs, dim=1).values)
    assert torch.allclose(torch_mean_generalized(xs, p=np.inf, dim=1), torch.max(xs, dim=1).values)
    assert torch.allclose(torch_mean_generalized(xs, p=-np.inf, dim=1), torch.min(xs, dim=1).values)



def test_dct():
    x = torch.randn(128, 3, 64, 32, dtype=torch.float64)

    # chceck +ve dims
    assert torch.allclose(x, idct(dct(x, dim=0), dim=0))
    with pytest.raises(ValueError, match='does not support odd sized dimension'):
        torch.allclose(x, idct(dct(x, dim=1), dim=1))
    assert torch.allclose(x, idct(dct(x, dim=2), dim=2))
    assert torch.allclose(x, idct(dct(x, dim=3), dim=3))

    # chceck -ve dims
    assert torch.allclose(x, idct(dct(x, dim=-4), dim=-4))
    with pytest.raises(ValueError, match='does not support odd sized dimension'):
        torch.allclose(x, idct(dct(x, dim=-3), dim=-3))
    assert torch.allclose(x, idct(dct(x, dim=-2), dim=-2))
    assert torch.allclose(x, idct(dct(x, dim=-1), dim=-1))

    # check defaults
    assert torch.allclose(dct(x), dct(x, dim=-1))
    assert torch.allclose(idct(x), idct(x, dim=-1))

    # check dct2
    assert torch.allclose(x, idct2(dct2(x)))
    assert torch.allclose(x, idct2(dct2(x)))

    # check defaults dct2
    assert torch.allclose(dct2(x), dct2(x, dim1=-1, dim2=-2))
    assert torch.allclose(dct2(x), dct2(x, dim1=-2, dim2=-1))
    assert torch.allclose(idct2(x), idct2(x, dim1=-1, dim2=-2))
    assert torch.allclose(idct2(x), idct2(x, dim1=-2, dim2=-1))
    # check order dct2
    assert torch.allclose(dct2(x, dim1=-1, dim2=-2), dct2(x, dim1=-2, dim2=-1))
    assert torch.allclose(dct2(x, dim1=-1, dim2=-4), dct2(x, dim1=-4, dim2=-1))
    assert torch.allclose(dct2(x, dim1=-4, dim2=-1), dct2(x, dim1=-1, dim2=-4))
    assert torch.allclose(idct2(x, dim1=-1, dim2=-2), idct2(x, dim1=-2, dim2=-1))
    assert torch.allclose(idct2(x, dim1=-1, dim2=-4), idct2(x, dim1=-4, dim2=-1))
    assert torch.allclose(idct2(x, dim1=-4, dim2=-1), idct2(x, dim1=-1, dim2=-4))


def test_fft_conv2d():
    data = XYSquaresData()
    dataset = GroundTruthDataset(data, transform=ToStandardisedTensor(), augment=None)
    # sample data
    factors = dataset.sample_random_traversal_factors(f_idx=2)
    batch = dataset.dataset_batch_from_factors(factors=factors, mode="input")
    # test conv2d_channel_wise variants
    for i in range(1, 5):
        kernel = make_gaussian_kernel_2d(sigma=i)
        out_cnv = conv2d_channel_wise(signal=batch, kernel=kernel)[0]
        out_fft = conv2d_channel_wise_fft(signal=batch, kernel=kernel)[0]
        assert torch.max(torch.abs(out_cnv - out_fft)) < 1e-6
