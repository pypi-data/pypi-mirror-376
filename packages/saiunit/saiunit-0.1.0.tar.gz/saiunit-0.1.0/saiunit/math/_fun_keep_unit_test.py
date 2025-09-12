# Copyright 2024 BDP Ecosystem Limited. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

import jax.numpy as jnp
import pytest
from absl.testing import parameterized

import saiunit as u
import saiunit.math as um
from saiunit import second, meter, ms
from saiunit._base import assert_quantity


class Array(u.CustomArray):
    def __init__(self, value):
        self.value = value

fun_keep_unit_squence_inputs = [
    'row_stack', 'concatenate', 'stack', 'vstack', 'hstack', 'dstack', 'column_stack', 'block', 'append',
]
fun_keep_unit_squence_outputs = [
    'split', 'array_split', 'dsplit', 'hsplit', 'vsplit',
]
fun_keep_unit_broadcasting_arrays = [
    'atleast_1d', 'atleast_2d', 'atleast_3d', 'broadcast_arrays',
]
fun_keep_unit_array_manipulation = [
    'reshape', 'moveaxis', 'transpose', 'swapaxes', 'tile', 'repeat',
    'flip', 'fliplr', 'flipud', 'roll', 'expand_dims', 'squeeze',
    'sort', 'max', 'min', 'amax', 'amin', 'diagflat', 'diagonal', 'choose', 'ravel',
    'flatten', 'unflatten', 'remove_diag',
]
fun_keep_unit_selection = [
    'compress', 'extract', 'take', 'select', 'where', 'unique',
]
fun_keep_unit_math_other = [
    'interp', 'clip', 'histogram',
]
fun_keep_unit_math_unary = [
    'real', 'imag', 'conj', 'conjugate', 'negative', 'positive',
    'abs', 'sum', 'nancumsum', 'nansum',
    'cumsum', 'ediff1d', 'absolute', 'fabs', 'median',
    'nanmin', 'nanmax', 'ptp', 'average', 'mean', 'std',
    'nanmedian', 'nanmean', 'nanstd', 'diff', 'nan_to_num',
]

fun_accept_unitless_unary_can_return_quantity = [
    'round', 'around', 'rint',
    'floor', 'ceil', 'trunc', 'fix',
]
fun_keep_unit_math_binary = [
    'fmod', 'mod', 'remainder',
    'maximum', 'minimum', 'fmax', 'fmin',
    'add', 'subtract', 'nextafter',
]
fun_keep_unit_percentile = [
    'percentile', 'nanpercentile',
]
fun_keep_unit_quantile = [
    'quantile', 'nanquantile',
]
fun_keep_unit_math_unary_misc = [
    'trace', 'lcm', 'gcd', 'copysign', 'rot90', 'intersect1d',
]
fun_accept_unitless_unary_2_results = [
    'modf',
]


class TestFunKeepUnitWithArrayCustomArray(parameterized.TestCase):

    @parameterized.product(
        value=[(1.0, 2.0), (1.23, 2.34, 3.45)],
        unit=[second, meter]
    )
    def test_fun_keep_unit_math_unary_with_array(self, value, unit):
        bm_fun_list = [getattr(um, fun) for fun in fun_keep_unit_math_unary]
        jnp_fun_list = [getattr(jnp, fun) for fun in fun_keep_unit_math_unary]

        for bm_fun, jnp_fun in zip(bm_fun_list, jnp_fun_list):
            print(f'fun: {bm_fun.__name__}')

            result = bm_fun(jnp.array(value))
            expected = jnp_fun(jnp.array(value))
            assert_quantity(result, expected)

            array_result = Array(result)
            assert isinstance(array_result, u.CustomArray)
            assert_quantity(array_result.value, expected)

            q = jnp.array(value) * unit
            result = bm_fun(q)
            expected = jnp_fun(jnp.array(value))
            assert_quantity(result, expected, unit=unit)

            array_result = Array(result)
            assert isinstance(array_result, u.CustomArray)
            assert_quantity(array_result.value, expected, unit=unit)

            array_input = Array(q)
            result = bm_fun(array_input.value)
            array_result = Array(result)
            assert isinstance(array_result, u.CustomArray)
            assert_quantity(array_result.value, expected, unit=unit)

    @parameterized.product(
        value=[((1.0, 2.0), (3.0, 4.0)),
               ((1.23, 2.34, 3.45), (4.56, 5.67, 6.78))],
        unit=[second, meter]
    )
    def test_fun_keep_unit_math_binary_with_array(self, value, unit):
        bm_fun_list = [getattr(um, fun) for fun in fun_keep_unit_math_binary]
        jnp_fun_list = [getattr(jnp, fun) for fun in fun_keep_unit_math_binary]

        for bm_fun, jnp_fun in zip(bm_fun_list, jnp_fun_list):
            print(f'fun: {bm_fun.__name__}')

            x1, x2 = value

            result = bm_fun(jnp.array(x1), jnp.array(x2))
            expected = jnp_fun(jnp.array(x1), jnp.array(x2))
            assert_quantity(result, expected)

            array_result = Array(result)
            assert isinstance(array_result, u.CustomArray)
            assert_quantity(array_result.value, expected)

            q1 = jnp.array(x1) * unit
            q2 = jnp.array(x2) * unit
            result = bm_fun(q1, q2)
            expected = jnp_fun(jnp.array(x1), jnp.array(x2))
            assert_quantity(result, expected, unit=unit)

            array_result = Array(result)
            assert isinstance(array_result, u.CustomArray)
            assert_quantity(array_result.value, expected, unit=unit)

            array_input1 = Array(q1)
            array_input2 = Array(q2)
            result = bm_fun(array_input1.value, array_input2.value)
            array_result = Array(result)
            assert isinstance(array_result, u.CustomArray)
            assert_quantity(array_result.value, expected, unit=unit)

    def test_fun_keep_unit_array_manipulation_with_array(self):
        data = jnp.array([1.0, 2.0, 3.0, 4.0]) * meter
        test_array = Array(data)
        
        assert isinstance(test_array, u.CustomArray)
        assert hasattr(test_array, 'value')
        assert_quantity(test_array.value, jnp.array([1.0, 2.0, 3.0, 4.0]), unit=meter)
        
        reshape_result = um.reshape(test_array.value, (2, 2))
        reshape_array = Array(reshape_result)
        assert isinstance(reshape_array, u.CustomArray)
        assert_quantity(reshape_array.value, jnp.array([[1.0, 2.0], [3.0, 4.0]]), unit=meter)
        
        flip_result = um.flip(test_array.value)
        flip_array = Array(flip_result)
        assert isinstance(flip_array, u.CustomArray)
        assert_quantity(flip_array.value, jnp.array([4.0, 3.0, 2.0, 1.0]), unit=meter)

    def test_fun_keep_unit_sequence_operations_with_array(self):
        data1 = jnp.array([1.0, 2.0, 3.0]) * second
        data2 = jnp.array([4.0, 5.0, 6.0]) * second
        
        array1 = Array(data1)
        array2 = Array(data2)
        
        assert isinstance(array1, u.CustomArray)
        assert isinstance(array2, u.CustomArray)
        
        vstack_result = um.vstack((array1.value, array2.value))
        vstack_array = Array(vstack_result)
        assert isinstance(vstack_array, u.CustomArray)
        assert_quantity(vstack_array.value, jnp.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]), unit=second)
        
        hstack_result = um.hstack((array1.value, array2.value))
        hstack_array = Array(hstack_result)
        assert isinstance(hstack_array, u.CustomArray)
        assert_quantity(hstack_array.value, jnp.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0]), unit=second)

    def test_fun_keep_unit_selection_with_array(self):
        data = jnp.array([1.0, 2.0, 3.0, 4.0, 5.0]) * meter
        test_array = Array(data)
        
        assert isinstance(test_array, u.CustomArray)
        
        where_result = um.where(test_array.value > 3.0 * meter, test_array.value, 0.0 * meter)
        where_array = Array(where_result)
        assert isinstance(where_array, u.CustomArray)
        assert_quantity(where_array.value, jnp.array([0.0, 0.0, 0.0, 4.0, 5.0]), unit=meter)
        
        sort_result = um.sort(test_array.value)
        sort_array = Array(sort_result)
        assert isinstance(sort_array, u.CustomArray)
        assert_quantity(sort_array.value, jnp.array([1.0, 2.0, 3.0, 4.0, 5.0]), unit=meter)

    def test_fun_keep_unit_statistical_operations_with_array(self):
        data = jnp.array([1.0, 2.0, 3.0, 4.0, 5.0]) * second
        test_array = Array(data)
        
        assert isinstance(test_array, u.CustomArray)
        
        sum_result = um.sum(test_array.value)
        sum_array = Array(sum_result)
        assert isinstance(sum_array, u.CustomArray)
        assert_quantity(sum_array.value, 15.0, unit=second)
        
        mean_result = um.mean(test_array.value)
        mean_array = Array(mean_result)
        assert isinstance(mean_array, u.CustomArray)
        assert_quantity(mean_array.value, 3.0, unit=second)
        
        max_result = um.max(test_array.value)
        max_array = Array(max_result)
        assert isinstance(max_array, u.CustomArray)
        assert_quantity(max_array.value, 5.0, unit=second)
        
        min_result = um.min(test_array.value)
        min_array = Array(min_result)
        assert isinstance(min_array, u.CustomArray)
        assert_quantity(min_array.value, 1.0, unit=second)

    def test_fun_keep_unit_percentile_quantile_with_array(self):
        data = jnp.array([1.0, 2.0, 3.0, 4.0, 5.0]) * meter
        test_array = Array(data)
        
        assert isinstance(test_array, u.CustomArray)
        
        percentile_result = um.percentile(test_array.value, 50)
        percentile_array = Array(percentile_result)
        assert isinstance(percentile_array, u.CustomArray)
        assert_quantity(percentile_array.value, 3.0, unit=meter)
        
        quantile_result = um.quantile(test_array.value, 0.5)
        quantile_array = Array(quantile_result)
        assert isinstance(quantile_array, u.CustomArray)
        assert_quantity(quantile_array.value, 3.0, unit=meter)

    def test_fun_keep_unit_broadcasting_with_array(self):
        data = jnp.array([1.0, 2.0, 3.0]) * second
        test_array = Array(data)
        
        assert isinstance(test_array, u.CustomArray)
        
        atleast_2d_result = um.atleast_2d(test_array.value)
        atleast_2d_array = Array(atleast_2d_result)
        assert isinstance(atleast_2d_array, u.CustomArray)
        assert_quantity(atleast_2d_array.value, jnp.array([[1.0, 2.0, 3.0]]), unit=second)
        
        expand_dims_result = um.expand_dims(test_array.value, axis=0)
        expand_dims_array = Array(expand_dims_result)
        assert isinstance(expand_dims_array, u.CustomArray)
        assert_quantity(expand_dims_array.value, jnp.array([[1.0, 2.0, 3.0]]), unit=second)

    def test_fun_keep_unit_rounding_functions_with_array(self):
        data = jnp.array([1.2, 2.7, 3.1, 4.9]) * meter
        test_array = Array(data)
        
        assert isinstance(test_array, u.CustomArray)
        
        round_result = um.round(test_array.value)
        round_array = Array(round_result)
        assert isinstance(round_array, u.CustomArray)
        assert_quantity(round_array.value, jnp.array([1.0, 3.0, 3.0, 5.0]), unit=meter)
        
        floor_result = um.floor(test_array.value)
        floor_array = Array(floor_result)
        assert isinstance(floor_array, u.CustomArray)
        assert_quantity(floor_array.value, jnp.array([1.0, 2.0, 3.0, 4.0]), unit=meter)
        
        ceil_result = um.ceil(test_array.value)
        ceil_array = Array(ceil_result)
        assert isinstance(ceil_array, u.CustomArray)
        assert_quantity(ceil_array.value, jnp.array([2.0, 3.0, 4.0, 5.0]), unit=meter)

    def test_fun_keep_unit_complex_operations_with_array(self):
        real_data = jnp.array([1.0, 2.0, 3.0]) * second
        imag_data = jnp.array([4.0, 5.0, 6.0]) * second
        complex_data = real_data + 1j * imag_data
        
        test_array = Array(complex_data)
        assert isinstance(test_array, u.CustomArray)
        
        real_result = um.real(test_array.value)
        real_array = Array(real_result)
        assert isinstance(real_array, u.CustomArray)
        assert_quantity(real_array.value, jnp.array([1.0, 2.0, 3.0]), unit=second)
        
        imag_result = um.imag(test_array.value)
        imag_array = Array(imag_result)
        assert isinstance(imag_array, u.CustomArray)
        assert_quantity(imag_array.value, jnp.array([4.0, 5.0, 6.0]), unit=second)
        
        abs_result = um.abs(test_array.value)
        abs_array = Array(abs_result)
        assert isinstance(abs_array, u.CustomArray)
        expected_abs = jnp.sqrt(jnp.array([1.0, 2.0, 3.0])**2 + jnp.array([4.0, 5.0, 6.0])**2)
        assert_quantity(abs_array.value, expected_abs, unit=second)


class TestFunKeepUnitSquenceInputs(parameterized.TestCase):
    def test_row_stack(self):
        a = jnp.array([1, 2, 3])
        b = jnp.array([4, 5, 6])
        result = u.math.row_stack((a, b))
        self.assertTrue(jnp.all(result == jnp.vstack((a, b))))

        q1 = [1, 2, 3] * u.second
        q2 = [4, 5, 6] * u.second
        result_q = u.math.row_stack((q1, q2))
        expected_q = jnp.vstack((jnp.array([1, 2, 3]), jnp.array([4, 5, 6])))
        assert_quantity(result_q, expected_q, u.second)

    def test_concatenate(self):
        a = jnp.array([[1, 2], [3, 4]])
        b = jnp.array([[5, 6]])
        result = u.math.concatenate((a, b), axis=0)
        self.assertTrue(jnp.all(result == jnp.concatenate((a, b), axis=0)))

        q1 = [[1, 2], [3, 4]] * u.second
        q2 = [[5, 6]] * u.second
        result_q = u.math.concatenate((q1, q2), axis=0)
        expected_q = jnp.concatenate((jnp.array([[1, 2], [3, 4]]), jnp.array([[5, 6]])), axis=0)
        assert_quantity(result_q, expected_q, u.second)

    def test_stack(self):
        a = jnp.array([1, 2, 3])
        b = jnp.array([4, 5, 6])
        result = u.math.stack((a, b), axis=1)
        self.assertTrue(jnp.all(result == jnp.stack((a, b), axis=1)))

        q1 = [1, 2, 3] * u.second
        q2 = [4, 5, 6] * u.second
        result_q = u.math.stack((q1, q2), axis=1)
        expected_q = jnp.stack((jnp.array([1, 2, 3]), jnp.array([4, 5, 6])), axis=1)
        assert_quantity(result_q, expected_q, u.second)

    def test_vstack(self):
        a = jnp.array([1, 2, 3])
        b = jnp.array([4, 5, 6])
        result = u.math.vstack((a, b))
        self.assertTrue(jnp.all(result == jnp.vstack((a, b))))

        q1 = [1, 2, 3] * u.second
        q2 = [4, 5, 6] * u.second
        result_q = u.math.vstack((q1, q2))
        expected_q = jnp.vstack((jnp.array([1, 2, 3]), jnp.array([4, 5, 6])))
        assert_quantity(result_q, expected_q, u.second)

    def test_hstack(self):
        a = jnp.array((1, 2, 3))
        b = jnp.array((4, 5, 6))
        result = u.math.hstack((a, b))
        self.assertTrue(jnp.all(result == jnp.hstack((a, b))))

        q1 = [1, 2, 3] * u.second
        q2 = [4, 5, 6] * u.second
        result_q = u.math.hstack((q1, q2))
        expected_q = jnp.hstack((jnp.array([1, 2, 3]), jnp.array([4, 5, 6])))
        assert_quantity(result_q, expected_q, u.second)

    def test_dstack(self):
        a = jnp.array([[1], [2], [3]])
        b = jnp.array([[4], [5], [6]])
        result = u.math.dstack((a, b))
        self.assertTrue(jnp.all(result == jnp.dstack((a, b))))

        q1 = [[1], [2], [3]] * u.second
        q2 = [[4], [5], [6]] * u.second
        result_q = u.math.dstack((q1, q2))
        expected_q = jnp.dstack((jnp.array([[1], [2], [3]]), jnp.array([[4], [5], [6]])))
        assert_quantity(result_q, expected_q, u.second)

    def test_column_stack(self):
        a = jnp.array((1, 2, 3))
        b = jnp.array((4, 5, 6))
        result = u.math.column_stack((a, b))
        self.assertTrue(jnp.all(result == jnp.column_stack((a, b))))

        q1 = [1, 2, 3] * u.second
        q2 = [4, 5, 6] * u.second
        result_q = u.math.column_stack((q1, q2))
        expected_q = jnp.column_stack((jnp.array([1, 2, 3]), jnp.array([4, 5, 6])))
        assert_quantity(result_q, expected_q, u.second)

    def test_block(self):
        array = jnp.array([[1, 2], [3, 4]])
        result = u.math.block(array)
        self.assertTrue(jnp.all(result == jnp.block(array)))

        q = [[1, 2], [3, 4]] * u.second
        result_q = u.math.block(q)
        expected_q = jnp.block(jnp.array([[1, 2], [3, 4]]))
        assert_quantity(result_q, expected_q, u.second)

    def test_append(self):
        array = jnp.array([0, 1, 2])
        result = u.math.append(array, 3)
        self.assertTrue(jnp.all(result == jnp.append(array, 3)))

        q = [0, 1, 2] * u.second
        result_q = u.math.append(q, 3 * u.second)
        expected_q = jnp.append(jnp.array([0, 1, 2]), 3)
        assert_quantity(result_q, expected_q, u.second)


class TestFunKeepUnitSquenceOutputs(parameterized.TestCase):
    def test_split(self):
        array = jnp.arange(9)
        result = u.math.split(array, 3)
        expected = jnp.split(array, 3)
        for r, e in zip(result, expected):
            self.assertTrue(jnp.all(r == e))

        q = jnp.arange(9) * u.second
        result_q = u.math.split(q, 3)
        expected_q = jnp.split(jnp.arange(9), 3)
        for r, e in zip(result_q, expected_q):
            assert_quantity(r, e, u.second)

    def test_array_split(self):
        array = jnp.arange(9)
        result = u.math.array_split(array, 3)
        expected = jnp.array_split(array, 3)
        for r, e in zip(result, expected):
            self.assertTrue(jnp.all(r == e))

        q = jnp.arange(9) * u.second
        result_q = u.math.array_split(q, 3)
        expected_q = jnp.array_split(jnp.arange(9), 3)
        for r, e in zip(result_q, expected_q):
            assert_quantity(r, e, u.second)

    def test_dsplit(self):
        array = jnp.arange(16.0).reshape(2, 2, 4)
        result = u.math.dsplit(array, 2)
        expected = jnp.dsplit(array, 2)
        for r, e in zip(result, expected):
            self.assertTrue(jnp.all(r == e))

        q = jnp.arange(16.0).reshape(2, 2, 4) * u.second
        result_q = u.math.dsplit(q, 2)
        expected_q = jnp.dsplit(jnp.arange(16.0).reshape(2, 2, 4), 2)
        for r, e in zip(result_q, expected_q):
            assert_quantity(r, e, u.second)

    def test_hsplit(self):
        array = jnp.arange(16.0).reshape(4, 4)
        result = u.math.hsplit(array, 2)
        expected = jnp.hsplit(array, 2)
        for r, e in zip(result, expected):
            self.assertTrue(jnp.all(r == e))

        q = jnp.arange(16.0).reshape(4, 4) * u.second
        result_q = u.math.hsplit(q, 2)
        expected_q = jnp.hsplit(jnp.arange(16.0).reshape(4, 4), 2)
        for r, e in zip(result_q, expected_q):
            assert_quantity(r, e, u.second)

    def test_vsplit(self):
        array = jnp.arange(16.0).reshape(4, 4)
        result = u.math.vsplit(array, 2)
        expected = jnp.vsplit(array, 2)
        for r, e in zip(result, expected):
            self.assertTrue(jnp.all(r == e))

        q = jnp.arange(16.0).reshape(4, 4) * u.second
        result_q = u.math.vsplit(q, 2)
        expected_q = jnp.vsplit(jnp.arange(16.0).reshape(4, 4), 2)
        for r, e in zip(result_q, expected_q):
            assert_quantity(r, e, u.second)


class TestFunKeepUnitBroadcastingArrays(parameterized.TestCase):
    def test_atleast_1d(self):
        array = jnp.array(0)
        result = u.math.atleast_1d(array)
        self.assertTrue(jnp.all(result == jnp.atleast_1d(array)))

        q = 0 * u.second
        result_q = u.math.atleast_1d(q)
        expected_q = jnp.atleast_1d(jnp.array(0))
        assert_quantity(result_q, expected_q, u.second)

    def test_atleast_2d(self):
        array = jnp.array([0, 1, 2])
        result = u.math.atleast_2d(array)
        self.assertTrue(jnp.all(result == jnp.atleast_2d(array)))

        q = [0, 1, 2] * u.second
        result_q = u.math.atleast_2d(q)
        expected_q = jnp.atleast_2d(jnp.array([0, 1, 2]))
        assert_quantity(result_q, expected_q, u.second)

    def test_atleast_3d(self):
        array = jnp.array([[0, 1, 2], [3, 4, 5]])
        result = u.math.atleast_3d(array)
        self.assertTrue(jnp.all(result == jnp.atleast_3d(array)))

        q = [[0, 1, 2], [3, 4, 5]] * u.second
        result_q = u.math.atleast_3d(q)
        expected_q = jnp.atleast_3d(jnp.array([[0, 1, 2], [3, 4, 5]]))
        assert_quantity(result_q, expected_q, u.second)

    def test_broadcast_arrays(self):
        a = jnp.array([1, 2, 3])
        b = jnp.array([[4], [5]])
        result = u.math.broadcast_arrays(a, b)
        self.assertTrue(jnp.all(result[0] == jnp.broadcast_arrays(a, b)[0]))
        self.assertTrue(jnp.all(result[1] == jnp.broadcast_arrays(a, b)[1]))

        q1 = [1, 2, 3] * u.second
        q2 = [[4], [5]] * u.second
        result_q = u.math.broadcast_arrays(q1, q2)
        expected_q = jnp.broadcast_arrays(jnp.array([1, 2, 3]), jnp.array([[4], [5]]))
        for r, e in zip(result_q, expected_q):
            assert_quantity(r, e, u.second)


class TestFunKeepUnitArrayManipulation(parameterized.TestCase):
    def test_reshape(self):
        array = jnp.array([1, 2, 3, 4])
        result = u.math.reshape(array, (2, 2))
        self.assertTrue(jnp.all(result == jnp.reshape(array, (2, 2))))

        q = [1, 2, 3, 4] * u.second
        result_q = u.math.reshape(q, (2, 2))
        expected_q = jnp.reshape(jnp.array([1, 2, 3, 4]), (2, 2))
        assert_quantity(result_q, expected_q, u.second)

    def test_moveaxis(self):
        array = jnp.zeros((3, 4, 5))
        result = u.math.moveaxis(array, 0, -1)
        self.assertTrue(jnp.all(result == jnp.moveaxis(array, 0, -1)))

        q = jnp.zeros((3, 4, 5)) * u.second
        result_q = u.math.moveaxis(q, 0, -1)
        expected_q = jnp.moveaxis(jnp.zeros((3, 4, 5)), 0, -1)
        assert_quantity(result_q, expected_q, u.second)

    def test_transpose(self):
        array = jnp.ones((2, 3))
        result = u.math.transpose(array)
        self.assertTrue(jnp.all(result == jnp.transpose(array)))

        q = jnp.ones((2, 3)) * u.second
        result_q = u.math.transpose(q)
        expected_q = jnp.transpose(jnp.ones((2, 3)))
        assert_quantity(result_q, expected_q, u.second)

    def test_swapaxes(self):
        array = jnp.zeros((3, 4, 5))
        result = u.math.swapaxes(array, 0, 2)
        self.assertTrue(jnp.all(result == jnp.swapaxes(array, 0, 2)))

        q = jnp.zeros((3, 4, 5)) * u.second
        result_q = u.math.swapaxes(q, 0, 2)
        expected_q = jnp.swapaxes(jnp.zeros((3, 4, 5)), 0, 2)
        assert_quantity(result_q, expected_q, u.second)

    def test_tile(self):
        array = jnp.array([0, 1, 2])
        result = u.math.tile(array, 2)
        self.assertTrue(jnp.all(result == jnp.tile(array, 2)))

        q = jnp.array([0, 1, 2]) * u.second
        result_q = u.math.tile(q, 2)
        expected_q = jnp.tile(jnp.array([0, 1, 2]), 2)
        assert_quantity(result_q, expected_q, u.second)

    def test_repeat(self):
        array = jnp.array([0, 1, 2])
        result = u.math.repeat(array, 2)
        self.assertTrue(jnp.all(result == jnp.repeat(array, 2)))

        q = [0, 1, 2] * u.second
        result_q = u.math.repeat(q, 2)
        expected_q = jnp.repeat(jnp.array([0, 1, 2]), 2)
        assert_quantity(result_q, expected_q, u.second)

    def test_flip(self):
        array = jnp.array([0, 1, 2])
        result = u.math.flip(array)
        self.assertTrue(jnp.all(result == jnp.flip(array)))

        q = [0, 1, 2] * u.second
        result_q = u.math.flip(q)
        expected_q = jnp.flip(jnp.array([0, 1, 2]))
        assert_quantity(result_q, expected_q, u.second)

    def test_fliplr(self):
        array = jnp.array([[0, 1, 2], [3, 4, 5]])
        result = u.math.fliplr(array)
        self.assertTrue(jnp.all(result == jnp.fliplr(array)))

        q = [[0, 1, 2], [3, 4, 5]] * u.second
        result_q = u.math.fliplr(q)
        expected_q = jnp.fliplr(jnp.array([[0, 1, 2], [3, 4, 5]]))
        assert_quantity(result_q, expected_q, u.second)

    def test_flipud(self):
        array = jnp.array([[0, 1, 2], [3, 4, 5]])
        result = u.math.flipud(array)
        self.assertTrue(jnp.all(result == jnp.flipud(array)))

        q = [[0, 1, 2], [3, 4, 5]] * u.second
        result_q = u.math.flipud(q)
        expected_q = jnp.flipud(jnp.array([[0, 1, 2], [3, 4, 5]]))
        assert_quantity(result_q, expected_q, u.second)

    def test_roll(self):
        array = jnp.array([0, 1, 2])
        result = u.math.roll(array, 1)
        self.assertTrue(jnp.all(result == jnp.roll(array, 1)))

        q = [0, 1, 2] * u.second
        result_q = u.math.roll(q, 1)
        expected_q = jnp.roll(jnp.array([0, 1, 2]), 1)
        assert_quantity(result_q, expected_q, u.second)

    def test_expand_dims(self):
        array = jnp.array([1, 2, 3])
        result = u.math.expand_dims(array, axis=0)
        self.assertTrue(jnp.all(result == jnp.expand_dims(array, axis=0)))

        q = [1, 2, 3] * u.second
        result_q = u.math.expand_dims(q, axis=0)
        expected_q = jnp.expand_dims(jnp.array([1, 2, 3]), axis=0)
        assert_quantity(result_q, expected_q, u.second)

    def test_squeeze(self):
        array = jnp.array([[[0], [1], [2]]])
        result = u.math.squeeze(array)
        self.assertTrue(jnp.all(result == jnp.squeeze(array)))

        q = [[[0], [1], [2]]] * u.second
        result_q = u.math.squeeze(q)
        expected_q = jnp.squeeze(jnp.array([[[0], [1], [2]]]))
        assert_quantity(result_q, expected_q, u.second)

    def test_sort(self):
        array = jnp.array([2, 3, 1])
        result = u.math.sort(array)
        self.assertTrue(jnp.all(result == jnp.sort(array)))

        q = [2, 3, 1] * u.second
        result_q = u.math.sort(q)
        expected_q = jnp.sort(jnp.array([2, 3, 1]))
        assert_quantity(result_q, expected_q, u.second)

    def test_max(self):
        array = jnp.array([1, 2, 3])
        result = u.math.max(array)
        self.assertTrue(result == jnp.max(array))

        q = [1, 2, 3] * u.second
        result_q = u.math.max(q)
        expected_q = jnp.max(jnp.array([1, 2, 3]))
        assert_quantity(result_q, expected_q, u.second)

    def test_min(self):
        array = jnp.array([1, 2, 3])
        result = u.math.min(array)
        self.assertTrue(result == jnp.min(array))

        q = [1, 2, 3] * u.second
        result_q = u.math.min(q)
        expected_q = jnp.min(jnp.array([1, 2, 3]))
        assert_quantity(result_q, expected_q, u.second)

    def test_amin(self):
        array = jnp.array([1, 2, 3])
        result = u.math.amin(array)
        self.assertTrue(result == jnp.min(array))

        q = [1, 2, 3] * u.second
        result_q = u.math.amin(q)
        expected_q = jnp.min(jnp.array([1, 2, 3]))
        assert_quantity(result_q, expected_q, u.second)

    def test_amax(self):
        array = jnp.array([1, 2, 3])
        result = u.math.amax(array)
        self.assertTrue(result == jnp.max(array))

        q = [1, 2, 3] * u.second
        result_q = u.math.amax(q)
        expected_q = jnp.max(jnp.array([1, 2, 3]))
        assert_quantity(result_q, expected_q, u.second)

    def test_diagflat(self):
        array = jnp.array([1, 2, 3])
        result = u.math.diagflat(array)
        self.assertTrue(jnp.all(result == jnp.diagflat(array)))

        q = [1, 2, 3] * u.second
        result_q = u.math.diagflat(q)
        expected_q = jnp.diagflat(jnp.array([1, 2, 3]))
        assert_quantity(result_q, expected_q, u.second)

    def test_diagonal(self):
        array = jnp.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]])
        result = u.math.diagonal(array)
        self.assertTrue(jnp.all(result == jnp.diagonal(array)))

        q = [[0, 1, 2], [3, 4, 5], [6, 7, 8]] * u.second
        result_q = u.math.diagonal(q)
        expected_q = jnp.diagonal(jnp.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]]))
        assert_quantity(result_q, expected_q, u.second)

    def test_choose(self):
        choices = [jnp.array([1, 2, 3]), jnp.array([4, 5, 6]), jnp.array([7, 8, 9])]
        result = u.math.choose(jnp.array([0, 1, 2]), choices)
        self.assertTrue(jnp.all(result == jnp.choose(jnp.array([0, 1, 2]), choices)))

        q = [0, 1, 2] * u.second
        q = q.astype(jnp.int64)
        result_q = u.math.choose(q, choices)
        expected_q = jnp.choose(jnp.array([0, 1, 2]), choices)
        assert_quantity(result_q, expected_q, u.second)

    def test_ravel(self):
        array = jnp.array([[1, 2, 3], [4, 5, 6]])
        result = u.math.ravel(array)
        self.assertTrue(jnp.all(result == jnp.ravel(array)))

        q = [[1, 2, 3], [4, 5, 6]] * u.second
        result_q = u.math.ravel(q)
        expected_q = jnp.ravel(jnp.array([[1, 2, 3], [4, 5, 6]]))
        assert_quantity(result_q, expected_q, u.second)


class TestFunKeepUnitSelection(parameterized.TestCase):
    def test_compress(self):
        array = jnp.array([1, 2, 3, 4])
        result = u.math.compress(jnp.array([0, 1, 1, 0]), array)
        self.assertTrue(jnp.all(result == jnp.compress(jnp.array([0, 1, 1, 0]), array)))

        q = jnp.array([1, 2, 3, 4]) * u.second
        result_q = u.math.compress(jnp.array([0, 1, 1, 0]), q)
        expected_q = jnp.compress(jnp.array([0, 1, 1, 0]), q.mantissa)
        assert_quantity(result_q, expected_q, u.second)

    def test_extract(self):
        array = jnp.array([1, 2, 3])
        result = u.math.extract(array > 1, array)
        self.assertTrue(jnp.all(result == jnp.extract(array > 1, array)))

        q = jnp.array([1, 2, 3])
        a = array * u.second
        result_q = u.math.extract(q > 1, a)
        expected_q = jnp.extract(q > 1, jnp.array([1, 2, 3])) * u.second
        assert u.math.allclose(result_q, expected_q)

    def test_take(self):
        array = jnp.array([4, 3, 5, 7, 6, 8])
        indices = jnp.array([0, 1, 4])
        result = u.math.take(array, indices)
        self.assertTrue(jnp.all(result == jnp.take(array, indices)))

        q = [4, 3, 5, 7, 6, 8] * u.second
        i = jnp.array([0, 1, 4])
        result_q = u.math.take(q, i)
        expected_q = jnp.take(jnp.array([4, 3, 5, 7, 6, 8]), jnp.array([0, 1, 4]))
        assert_quantity(result_q, expected_q, u.second)

    def test_select(self):
        condlist = [jnp.array([True, False, True]), jnp.array([False, True, False])]
        choicelist = [jnp.array([1, 2, 3]), jnp.array([4, 5, 6])]
        result = u.math.select(condlist, choicelist, default=0)
        self.assertTrue(jnp.all(result == jnp.select(condlist, choicelist, default=0)))

        c = [jnp.array([True, False, True]), jnp.array([False, True, False])]
        ch = [[1, 2, 3] * u.second, [4, 5, 6] * u.second]
        result_q = u.math.select(c, ch, default=0)
        expected_q = jnp.select([jnp.array([True, False, True]), jnp.array([False, True, False])],
                                [jnp.array([1, 2, 3]), jnp.array([4, 5, 6])], default=0)
        assert_quantity(result_q, expected_q, u.second)

    def test_where(self):
        array = jnp.array([1, 2, 3, 4, 5])
        result = u.math.where(array > 2, array, 0)
        self.assertTrue(jnp.all(result == jnp.where(array > 2, array, 0)))

        q = [1, 2, 3, 4, 5] * u.second
        result_q = u.math.where(q > 2 * u.second, q, 0 * u.second)
        expected_q = jnp.where(jnp.array([1, 2, 3, 4, 5]) > 2, jnp.array([1, 2, 3, 4, 5]), 0)
        assert_quantity(result_q, expected_q, u.second)

    def test_unique(self):
        array = jnp.array([0, 1, 2, 1, 0])
        result = u.math.unique(array)
        self.assertTrue(jnp.all(result == jnp.unique(array)))

        q = [0, 1, 2, 1, 0] * u.second
        result_q = u.math.unique(q)
        expected_q = jnp.unique(jnp.array([0, 1, 2, 1, 0]))
        assert_quantity(result_q, expected_q, u.second)


class TestFunKeepUnitOther(parameterized.TestCase):
    def test_interp(self):
        x = jnp.array([1, 2, 3])
        xp = jnp.array([0, 1, 2, 3, 4])
        fp = jnp.array([0, 1, 2, 3, 4])
        result = u.math.interp(x, xp, fp)
        self.assertTrue(jnp.all(result == jnp.interp(x, xp, fp)))

        x = [1, 2, 3] * u.second
        xp = [0, 1, 2, 3, 4] * u.second
        fp = [0, 1, 2, 3, 4] * u.mvolt
        result_q = u.math.interp(x, xp, fp)
        expected_q = jnp.interp(jnp.array([1, 2, 3]),
                                jnp.array([0, 1, 2, 3, 4]),
                                jnp.array([0, 1, 2, 3, 4])) * u.mvolt
        assert u.math.allclose(result_q, expected_q)

    def test_clip(self):
        array = jnp.array([1, 2, 3, 4, 5])
        result = u.math.clip(array, 2, 4)
        self.assertTrue(jnp.all(result == jnp.clip(array, 2, 4)))

        q = [1, 2, 3, 4, 5] * u.ms
        result_q = u.math.clip(q, 2 * u.ms, 4 * u.ms)
        expected_q = jnp.clip(jnp.array([1, 2, 3, 4, 5]), 2, 4) * u.ms
        assert u.math.allclose(result_q, expected_q)

    def test_histogram(self):
        array = jnp.array([1, 2, 1])
        result, _ = u.math.histogram(array)
        expected, _ = jnp.histogram(array)
        self.assertTrue(jnp.all(result == expected))

        q = [1, 2, 1] * u.second
        result_q, _ = u.math.histogram(q)
        expected_q, _ = jnp.histogram(jnp.array([1, 2, 1]))
        assert_quantity(result_q, expected_q, None)


class TestFunKeepUnit(parameterized.TestCase):

    @parameterized.product(
        value=[(1.0, 2.0), (1.23, 2.34, 3.45)],
        unit=[second, meter]
    )
    def test_fun_keep_unit_math_unary(self, value, unit):
        bm_fun_list = [getattr(um, fun) for fun in fun_keep_unit_math_unary]
        jnp_fun_list = [getattr(jnp, fun) for fun in fun_keep_unit_math_unary]

        for bm_fun, jnp_fun in zip(bm_fun_list, jnp_fun_list):
            print(f'fun: {bm_fun.__name__}')

            result = bm_fun(jnp.array(value))
            expected = jnp_fun(jnp.array(value))
            assert_quantity(result, expected)

            q = value * unit
            result = bm_fun(q)
            expected = jnp_fun(jnp.array(value))
            assert_quantity(result, expected, unit=unit)

    @parameterized.product(
        value=[((1.0, 2.0), (3.0, 4.0)),
               ((1.23, 2.34, 3.45), (4.56, 5.67, 6.78))],
        unit=[second, meter]
    )
    def test_fun_keep_unit_math_binary(self, value, unit):
        bm_fun_list = [getattr(um, fun) for fun in fun_keep_unit_math_binary]
        jnp_fun_list = [getattr(jnp, fun) for fun in fun_keep_unit_math_binary]

        for bm_fun, jnp_fun in zip(bm_fun_list, jnp_fun_list):
            print(f'fun: {bm_fun.__name__}')

            x1, x2 = value

            result = bm_fun(jnp.array(x1), jnp.array(x2))
            expected = jnp_fun(jnp.array(x1), jnp.array(x2))
            assert_quantity(result, expected)

            q1 = x1 * unit
            q2 = x2 * unit
            result = bm_fun(q1, q2)
            expected = jnp_fun(jnp.array(x1), jnp.array(x2))
            assert_quantity(result, expected, unit=unit)

            with pytest.raises(AssertionError):
                result = bm_fun(q1, jnp.array(x2))

            with pytest.raises(AssertionError):
                result = bm_fun(jnp.array(x1), q2)

    @parameterized.product(
        value=[(1.0, 2.0), (1.23, jnp.nan, 3.45)],
        q=[25, 50, 75],
        unit=[second, meter]
    )
    def test_fun_keep_unit_percentile(self, value, q, unit):
        bm_fun_list = [getattr(um, fun) for fun in fun_keep_unit_percentile]
        jnp_fun_list = [getattr(jnp, fun) for fun in fun_keep_unit_percentile]

        for bm_fun, jnp_fun in zip(bm_fun_list, jnp_fun_list):
            print(f'fun: {bm_fun.__name__}')

            result = bm_fun(jnp.array(value), q)
            expected = jnp_fun(jnp.array(value), q)
            assert_quantity(result, expected)

            q_value = value * unit
            result = bm_fun(q_value, q)
            expected = jnp_fun(jnp.array(value), q)
            assert_quantity(result, expected, unit=unit)

    @parameterized.product(
        value=[(1.0, 2.0), (1.23, jnp.nan, 3.45)],
        q=[0.25, 0.5, 0.75],
        unit=[second, meter]
    )
    def test_fun_keep_unit_quantile(self, value, q, unit):
        bm_fun_list = [getattr(um, fun) for fun in fun_keep_unit_percentile]
        jnp_fun_list = [getattr(jnp, fun) for fun in fun_keep_unit_percentile]

        for bm_fun, jnp_fun in zip(bm_fun_list, jnp_fun_list):
            print(f'fun: {bm_fun.__name__}')

            result = bm_fun(jnp.array(value), q)
            expected = jnp_fun(jnp.array(value), q)
            assert_quantity(result, expected)

            q_value = value * unit
            result = bm_fun(q_value, q)
            expected = jnp_fun(jnp.array(value), q)
            assert_quantity(result, expected, unit=unit)

    @parameterized.product(
        value=[(1.123, 2.567, 3.891), (1.23, 2.34, 3.45)]
    )
    def test_fun_accept_unitless_binary_2_results(self, value):
        bm_fun_list = [getattr(um, fun) for fun in fun_accept_unitless_unary_2_results]
        jnp_fun_list = [getattr(jnp, fun) for fun in fun_accept_unitless_unary_2_results]

        for fun in fun_accept_unitless_unary_2_results:
            bm_fun = getattr(um, fun)
            jnp_fun = getattr(jnp, fun)

            print(f'fun: {bm_fun.__name__}')
            result1, result2 = bm_fun(jnp.array(value))
            expected1, expected2 = jnp_fun(jnp.array(value))
            assert_quantity(result1, expected1)
            assert_quantity(result2, expected2)

            for unit in [meter, ms]:
                q = value * unit
                result1, result2 = bm_fun(q)
                expected1, expected2 = jnp_fun(jnp.array(value))
                assert_quantity(result1, expected1, unit)
                assert_quantity(result2, expected2, unit)

    @parameterized.product(
        value=[(1.123, 2.567, 3.891), (1.23, 2.34, 3.45)]
    )
    def test_fun_accept_unitless_unary_can_return_quantity(self, value):
        for fun in fun_accept_unitless_unary_can_return_quantity:
            bm_fun = getattr(um, fun)
            jnp_fun = getattr(jnp, fun)

            print(f'fun: {bm_fun.__name__}')
            result = bm_fun(jnp.array(value))
            expected = jnp_fun(jnp.array(value))
            assert_quantity(result, expected)

            for unit in [meter, ms]:
                q = value * unit
                result = bm_fun(q)
                expected = jnp_fun(jnp.array(value))
                assert_quantity(result, expected, unit)


class TestFunKeepUnitMathFunMisc(parameterized.TestCase):
    def test_trace(self):
        a = jnp.array([[1, 2], [3, 4]])
        result = u.math.trace(a)
        self.assertTrue(result == jnp.trace(a))

        q = [[1, 2], [3, 4]] * u.second
        result_q = u.math.trace(q)
        expected_q = jnp.trace(jnp.array([[1, 2], [3, 4]]))
        assert_quantity(result_q, expected_q, u.second)

    def test_lcm(self):
        result = u.math.lcm(jnp.array([4, 5, 6]), jnp.array([2, 3, 4]))
        self.assertTrue(jnp.all(result == jnp.lcm(jnp.array([4, 5, 6]), jnp.array([2, 3, 4]))))

        q1 = [4, 5, 6] * u.second
        q2 = [2, 3, 4] * u.second
        q1 = q1.astype(jnp.int64)
        q2 = q2.astype(jnp.int64)
        result_q = u.math.lcm(q1, q2)
        expected_q = jnp.lcm(jnp.array([4, 5, 6]), jnp.array([2, 3, 4])) * u.second
        assert u.math.allclose(result_q, expected_q)

    def test_gcd(self):
        result = u.math.gcd(jnp.array([4, 5, 6]), jnp.array([2, 3, 4]))
        self.assertTrue(jnp.all(result == jnp.gcd(jnp.array([4, 5, 6]), jnp.array([2, 3, 4]))))

        q1 = [4, 5, 6] * u.second
        q2 = [2, 3, 4] * u.second
        q1 = q1.astype(jnp.int64)
        q2 = q2.astype(jnp.int64)
        result_q = u.math.gcd(q1, q2)
        expected_q = jnp.gcd(jnp.array([4, 5, 6]), jnp.array([2, 3, 4])) * u.second
        assert u.math.allclose(result_q, expected_q)

    def test_copysign(self):
        result = u.math.copysign(jnp.array([-1, 2]), jnp.array([1, -3]))
        self.assertTrue(jnp.all(result == jnp.copysign(jnp.array([-1, 2]), jnp.array([1, -3]))))

        q1 = [-1, 2] * ms
        q2 = [1, -3] * ms
        result_q = u.math.copysign(q1, q2)
        expected_q = jnp.copysign(jnp.array([-1, 2]), jnp.array([1, -3])) * ms
        assert u.math.allclose(result_q, expected_q)

    def test_rot90(self):
        a = jnp.array([[1, 2], [3, 4]])
        result = u.math.rot90(a)
        self.assertTrue(jnp.all(result == jnp.rot90(a)))

        q = [[1, 2], [3, 4]] * u.second
        result_q = u.math.rot90(q)
        expected_q = jnp.rot90(jnp.array([[1, 2], [3, 4]]))
        assert_quantity(result_q, expected_q, u.second)

    def test_intersect1d(self):
        a = jnp.array([1, 2, 3, 4, 5])
        b = jnp.array([3, 4, 5, 6, 7])
        result = u.math.intersect1d(a, b)
        self.assertTrue(jnp.all(result == jnp.intersect1d(a, b)))

        q1 = [1, 2, 3, 4, 5] * u.second
        q2 = [3, 4, 5, 6, 7] * u.second
        result_q = u.math.intersect1d(q1, q2)
        expected_q = jnp.intersect1d(jnp.array([1, 2, 3, 4, 5]), jnp.array([3, 4, 5, 6, 7]))
        assert_quantity(result_q, expected_q, u.second)


class TestGather:
    def test(self):
        # Test 1: Basic 2D example (matches PyTorch documentation)
        input_tensor = jnp.array([[1, 2], [3, 4]])
        index_tensor = jnp.array([[0, 0], [1, 0]])
        result1 = u.math.gather(input_tensor, 1, index_tensor)
        print("Test 1:")
        print("Input:", input_tensor)
        print("Index:", index_tensor)
        print("Result:", result1)
        print()

        # Test 2: 3D example
        input_3d = jnp.array([[[1, 2], [3, 4]], [[5, 6], [7, 8]]])
        index_3d = jnp.array([[[0, 1], [1, 0]], [[1, 0], [0, 1]]])
        result2 = u.math.gather(input_3d, 2, index_3d)
        print("Test 2:")
        print("Input shape:", input_3d.shape)
        print("Index shape:", index_3d.shape)
        print("Result:", result2)
        print()

        # Test 3: Gather along dim=0
        result3 = u.math.gather(input_tensor, 0, jnp.array([[1, 0], [0, 1]]))
        print("Test 3 (dim=0):")
        print("Result:", result3)

        # Test 4: Gather along dim=0
        result3 = u.math.gather(input_tensor * u.mV, 0, jnp.array([[1, 0], [0, 1]]))
        print("Test 3 (dim=0):")
        print("Result:", result3)
