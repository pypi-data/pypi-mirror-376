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
from saiunit import second, meter
from saiunit._base import assert_quantity


class Array(u.CustomArray):
    def __init__(self, value):
        self.value = value

fun_array_creation_given_shape = [
    'empty', 'ones', 'zeros',
]
fun_array_creation_given_shape_fill_value = [
    'full',
]
fun_array_creation_given_int = [
    'eye', 'identity', 'tri',
]
fun_array_creation_given_array = [
    'empty_like', 'ones_like', 'zeros_like', 'diag',
]
fun_array_creation_given_array_fill_value = [
    'full_like',
]
fun_array_creation_given_square_array = [
    'tril', 'triu',
]
fun_array_creation_given_square_array_fill_value = [
    'fill_diagonal',
]
fun_array_creation_misc1 = [
    'arange', 'linspace', 'logspace',
]
fun_array_creation_misc2 = [
    'meshgrid', 'vander',
]
fun_array_creation_asarray = [
    'array', 'asarray',
]
fun_array_creation_indices = [
    'tril_indices', 'triu_indices'
]
fun_array_creation_indices_from = [
    'tril_indices_from', 'triu_indices_from',
]
fun_array_creation_other = [
    'from_numpy',
    'as_numpy',
    'tree_ones_like',
    'tree_zeros_like',
]


class TestFunArrayCreationWithArrayCustomArray(parameterized.TestCase):

    @parameterized.product(
        shape=[(1,), (2, 3), (4, 5, 6)],
        unit=[second, meter]
    )
    def test_fun_array_creation_given_shape_with_array(self, shape, unit):
        bm_fun_list = [getattr(um, fun) for fun in fun_array_creation_given_shape]
        jnp_fun_list = [getattr(jnp, fun) for fun in fun_array_creation_given_shape]

        for bm_fun, jnp_fun in zip(bm_fun_list, jnp_fun_list):
            print(f'fun: {bm_fun.__name__}')

            result = bm_fun(shape)
            expected = jnp_fun(shape)
            assert_quantity(result, expected)

            array_result = Array(result)
            assert isinstance(array_result, u.CustomArray)
            assert_quantity(array_result.value, expected)

            result = bm_fun(shape, unit=unit)
            expected = jnp_fun(shape)
            assert_quantity(result, expected, unit=unit)

            array_result = Array(result)
            assert isinstance(array_result, u.CustomArray)
            assert_quantity(array_result.value, expected, unit=unit)

    @parameterized.product(
        shape=[(1,), (2, 3), (4, 5, 6)],
        unit=[second, meter],
        fill_value=[-1., 1.]
    )
    def test_fun_array_creation_given_shape_fill_value_with_array(self, shape, unit, fill_value):
        bm_fun_list = [getattr(um, fun) for fun in fun_array_creation_given_shape_fill_value]
        jnp_fun_list = [getattr(jnp, fun) for fun in fun_array_creation_given_shape_fill_value]

        for bm_fun, jnp_fun in zip(bm_fun_list, jnp_fun_list):
            print(f'fun: {bm_fun.__name__}')

            result = bm_fun(shape, fill_value=fill_value)
            expected = jnp_fun(shape, fill_value=fill_value)
            assert_quantity(result, expected)

            array_result = Array(result)
            assert isinstance(array_result, u.CustomArray)
            assert_quantity(array_result.value, expected)

            result = bm_fun(shape, fill_value=fill_value * unit)
            expected = jnp_fun(shape, fill_value=fill_value)
            assert_quantity(result, expected, unit=unit)

            array_result = Array(result)
            assert isinstance(array_result, u.CustomArray)
            assert_quantity(array_result.value, expected, unit=unit)

    @parameterized.product(
        value=[1, 10, 100],
        unit=[second, meter]
    )
    def test_fun_array_creation_given_int_with_array(self, value, unit):
        bm_fun_list = [getattr(um, fun) for fun in fun_array_creation_given_int]
        jnp_fun_list = [getattr(jnp, fun) for fun in fun_array_creation_given_int]

        for bm_fun, jnp_fun in zip(bm_fun_list, jnp_fun_list):
            print(f'fun: {bm_fun.__name__}')

            result = bm_fun(value)
            expected = jnp_fun(value)
            assert_quantity(result, expected)

            array_result = Array(result)
            assert isinstance(array_result, u.CustomArray)
            assert_quantity(array_result.value, expected)

            result = bm_fun(value, unit=unit)
            expected = jnp_fun(value)
            assert_quantity(result, expected, unit=unit)

            array_result = Array(result)
            assert isinstance(array_result, u.CustomArray)
            assert_quantity(array_result.value, expected, unit=unit)

    @parameterized.product(
        array=[jnp.array([1.0, 2.0]), jnp.array([[1.0, 2.0], [3.0, 4.0]])],
        unit=[second, meter]
    )
    def test_fun_array_creation_given_array_with_array(self, array, unit):
        bm_fun_list = [getattr(um, fun) for fun in fun_array_creation_given_array]
        jnp_fun_list = [getattr(jnp, fun) for fun in fun_array_creation_given_array]

        for bm_fun, jnp_fun in zip(bm_fun_list, jnp_fun_list):
            print(f'fun: {bm_fun.__name__}')

            result = bm_fun(array)
            expected = jnp_fun(array)
            assert_quantity(result, expected)

            array_result = Array(result)
            assert isinstance(array_result, u.CustomArray)
            assert_quantity(array_result.value, expected)

            result = bm_fun(array, unit=unit)
            expected = jnp_fun(array)
            assert_quantity(result, expected, unit=unit)

            array_result = Array(result)
            assert isinstance(array_result, u.CustomArray)
            assert_quantity(array_result.value, expected, unit=unit)

    @parameterized.product(
        array=[jnp.array([1.0, 2.0]), jnp.array([[1.0, 2.0], [3.0, 4.0]])],
        unit=[second, meter],
        fill_value=[-1., 1.]
    )
    def test_fun_array_creation_given_array_fill_value_with_array(self, array, unit, fill_value):
        bm_fun_list = [getattr(um, fun) for fun in fun_array_creation_given_array_fill_value]
        jnp_fun_list = [getattr(jnp, fun) for fun in fun_array_creation_given_array_fill_value]

        for bm_fun, jnp_fun in zip(bm_fun_list, jnp_fun_list):
            print(f'fun: {bm_fun.__name__}')

            result = bm_fun(array, fill_value=fill_value)
            expected = jnp_fun(array, fill_value=fill_value)
            assert_quantity(result, expected)

            array_result = Array(result)
            assert isinstance(array_result, u.CustomArray)
            assert_quantity(array_result.value, expected)

            result = bm_fun(array * unit, fill_value=fill_value * unit)
            expected = jnp_fun(array, fill_value=fill_value)
            assert_quantity(result, expected, unit=unit)

            array_result = Array(result)
            assert isinstance(array_result, u.CustomArray)
            assert_quantity(array_result.value, expected, unit=unit)

            with pytest.raises(AssertionError):
                result = bm_fun(array, fill_value=fill_value * unit)

    @parameterized.product(
        unit=[second, meter],
    )
    def test_fun_array_creation_asarray_with_array(self, unit):
        bm_fun_list = [getattr(um, fun) for fun in fun_array_creation_asarray]
        jnp_fun_list = [getattr(jnp, fun) for fun in fun_array_creation_asarray]

        for bm_fun, jnp_fun in zip(bm_fun_list, jnp_fun_list):
            result = bm_fun([1, 2, 3])
            expected = jnp_fun([1, 2, 3])
            assert_quantity(result, expected)

            array_result = Array(result)
            assert isinstance(array_result, u.CustomArray)
            assert_quantity(array_result.value, expected)

            result = bm_fun([1, 2, 3] * unit)
            expected = jnp_fun([1, 2, 3])
            assert_quantity(result, expected, unit=unit)

            array_result = Array(result)
            assert isinstance(array_result, u.CustomArray)
            assert_quantity(array_result.value, expected, unit=unit)

            result = bm_fun([1 * unit, 2 * unit, 3 * unit])
            expected = jnp_fun([1, 2, 3])
            assert_quantity(result, expected, unit=unit)

            array_result = Array(result)
            assert isinstance(array_result, u.CustomArray)
            assert_quantity(array_result.value, expected, unit=unit)

            result = bm_fun(1 * unit)
            expected = jnp_fun(1)
            assert_quantity(result, expected, unit=unit)

            array_result = Array(result)
            assert isinstance(array_result, u.CustomArray)
            assert_quantity(array_result.value, expected, unit=unit)

            with pytest.raises(u.UnitMismatchError):
                result = bm_fun(1 * unit, unit=u.volt)

    def test_array_custom_array_compatibility(self):
        test_array = Array(jnp.array([1.0, 2.0, 3.0]) * meter)
        
        assert isinstance(test_array, u.CustomArray)
        assert hasattr(test_array, 'value')
        assert_quantity(test_array.value, jnp.array([1.0, 2.0, 3.0]), unit=meter)
        
        result = um.zeros_like(test_array.value)
        array_result = Array(result)
        assert isinstance(array_result, u.CustomArray)
        assert_quantity(array_result.value, jnp.zeros(3), unit=meter)

    def test_array_creation_with_custom_array_input(self):
        original_data = jnp.array([[1.0, 2.0], [3.0, 4.0]]) * second
        test_array = Array(original_data)
        
        result = um.ones_like(test_array.value)
        expected = jnp.ones((2, 2))
        assert_quantity(result, expected, unit=second)
        
        array_result = Array(result)
        assert isinstance(array_result, u.CustomArray)
        assert_quantity(array_result.value, expected, unit=second)
        
        result = um.empty_like(test_array.value)
        array_result = Array(result)
        assert isinstance(array_result, u.CustomArray)
        assert array_result.value.shape == (2, 2)
        assert u.get_unit(array_result.value) == second


class TestFunArrayCreation(parameterized.TestCase):

    @parameterized.product(
        shape=[(1,), (2, 3), (4, 5, 6)],
        unit=[second, meter]
    )
    def test_fun_array_creation_given_shape(self, shape, unit):
        bm_fun_list = [getattr(um, fun) for fun in fun_array_creation_given_shape]
        jnp_fun_list = [getattr(jnp, fun) for fun in fun_array_creation_given_shape]

        for bm_fun, jnp_fun in zip(bm_fun_list, jnp_fun_list):
            print(f'fun: {bm_fun.__name__}')

            result = bm_fun(shape)
            expected = jnp_fun(shape)
            assert_quantity(result, expected)

            result = bm_fun(shape, unit=unit)
            expected = jnp_fun(shape)
            assert_quantity(result, expected, unit=unit)

    @parameterized.product(
        shape=[(1,), (2, 3), (4, 5, 6)],
        unit=[second, meter],
        fill_value=[-1., 1.]
    )
    def test_fun_array_creation_given_shape_fill_value(self, shape, unit, fill_value):
        bm_fun_list = [getattr(um, fun) for fun in fun_array_creation_given_shape_fill_value]
        jnp_fun_list = [getattr(jnp, fun) for fun in fun_array_creation_given_shape_fill_value]

        for bm_fun, jnp_fun in zip(bm_fun_list, jnp_fun_list):
            print(f'fun: {bm_fun.__name__}')

            result = bm_fun(shape, fill_value=fill_value)
            expected = jnp_fun(shape, fill_value=fill_value)
            assert_quantity(result, expected)

            result = bm_fun(shape, fill_value=fill_value * unit)
            expected = jnp_fun(shape, fill_value=fill_value)
            assert_quantity(result, expected, unit=unit)

    @parameterized.product(
        value=[1, 10, 100],
        unit=[second, meter]
    )
    def test_fun_array_creation_given_int(self, value, unit):
        bm_fun_list = [getattr(um, fun) for fun in fun_array_creation_given_shape]
        jnp_fun_list = [getattr(jnp, fun) for fun in fun_array_creation_given_shape]

        for bm_fun, jnp_fun in zip(bm_fun_list, jnp_fun_list):
            print(f'fun: {bm_fun.__name__}')

            result = bm_fun(value)
            expected = jnp_fun(value)
            assert_quantity(result, expected)

            result = bm_fun(value, unit=unit)
            expected = jnp_fun(value)
            assert_quantity(result, expected, unit=unit)

    @parameterized.product(
        array=[jnp.array([1.0, 2.0]), jnp.array([[1.0, 2.0], [3.0, 4.0]])],
        unit=[second, meter]
    )
    def test_fun_array_creation_given_array(self, array, unit):
        bm_fun_list = [getattr(um, fun) for fun in fun_array_creation_given_array]
        jnp_fun_list = [getattr(jnp, fun) for fun in fun_array_creation_given_array]

        for bm_fun, jnp_fun in zip(bm_fun_list, jnp_fun_list):
            print(f'fun: {bm_fun.__name__}')

            result = bm_fun(array)
            expected = jnp_fun(array)
            assert_quantity(result, expected)

            result = bm_fun(array, unit=unit)
            expected = jnp_fun(array)
            assert_quantity(result, expected, unit=unit)

    @parameterized.product(
        array=[jnp.array([1.0, 2.0]), jnp.array([[1.0, 2.0], [3.0, 4.0]])],
        unit=[second, meter],
        fill_value=[-1., 1.]
    )
    def test_fun_array_creation_given_array_fill_value(self, array, unit, fill_value):
        bm_fun_list = [getattr(um, fun) for fun in fun_array_creation_given_array_fill_value]
        jnp_fun_list = [getattr(jnp, fun) for fun in fun_array_creation_given_array_fill_value]

        for bm_fun, jnp_fun in zip(bm_fun_list, jnp_fun_list):
            print(f'fun: {bm_fun.__name__}')

            result = bm_fun(array, fill_value=fill_value)
            expected = jnp_fun(array, fill_value=fill_value)
            assert_quantity(result, expected)

            result = bm_fun(array * unit, fill_value=fill_value * unit)
            expected = jnp_fun(array, fill_value=fill_value)
            assert_quantity(result, expected, unit=unit)

            with pytest.raises(AssertionError):
                result = bm_fun(array, fill_value=fill_value * unit)

    @parameterized.product(
        shape=[(3, 3), (6, 6), (10, 10)],
        unit=[second, meter],
    )
    def test_fun_array_creation_given_square_array(self, shape, unit):
        bm_fun_list = [getattr(um, fun) for fun in fun_array_creation_given_square_array]
        jnp_fun_list = [getattr(jnp, fun) for fun in fun_array_creation_given_square_array]

        for bm_fun, jnp_fun in zip(bm_fun_list, jnp_fun_list):
            print(f'fun: {bm_fun.__name__}')

            value = jnp.ones(shape)
            result = bm_fun(value)
            expected = jnp_fun(value)
            assert_quantity(result, expected)

            result = bm_fun(value, unit=unit)
            expected = jnp_fun(value)
            assert_quantity(result, expected, unit=unit)

    @parameterized.product(
        unit=[second, meter],
    )
    def test_fun_array_creation_misc1(self, unit):
        bm_fun_list = [getattr(um, fun) for fun in fun_array_creation_misc1]
        jnp_fun_list = [getattr(jnp, fun) for fun in fun_array_creation_misc1]

        for bm_fun, jnp_fun in zip(bm_fun_list, jnp_fun_list):
            print(f'fun: {bm_fun.__name__}')

            if bm_fun.__name__ == 'arange':
                result = bm_fun(5)
                expected = jnp_fun(5)
                assert_quantity(result, expected)

                result = bm_fun(1, 5)
                expected = jnp_fun(1, 5)
                assert_quantity(result, expected)

                result = bm_fun(1, 5, 2)
                expected = jnp_fun(1, 5, 2)
                assert_quantity(result, expected)

                result = bm_fun(5 * unit, step=1 * unit)
                expected = jnp_fun(5, step=1)
                assert_quantity(result, expected, unit=unit)

                result = bm_fun(3 * unit, 9 * unit, 1 * unit)
                expected = jnp_fun(3, 9, 1)
                assert_quantity(result, expected, unit=unit)

                with pytest.raises(u.UnitMismatchError):
                    result = bm_fun(5 * unit, step=1)

                with pytest.raises(u.UnitMismatchError):
                    result = bm_fun(5, step=1 * unit)

                with pytest.raises(u.UnitMismatchError):
                    result = bm_fun(3 * unit, 9 * unit, 1)
                with pytest.raises(u.UnitMismatchError):
                    result = bm_fun(3 * unit, 9, 1)

                with pytest.raises(u.UnitMismatchError):
                    result = bm_fun(3, 9 * unit, 1)

                with pytest.raises(u.UnitMismatchError):
                    result = bm_fun(3, 9, 1 * unit)
            else:
                result = bm_fun(5, 15, 5)
                expected = jnp_fun(5, 15, 5)
                assert_quantity(result, expected)

                result = bm_fun(5 * unit, 15 * unit, 5)
                expected = jnp_fun(5, 15, 5)
                assert_quantity(result, expected, unit=unit)

                with pytest.raises(u.UnitMismatchError):
                    result = bm_fun(5, 15 * unit, 5)

                with pytest.raises(u.UnitMismatchError):
                    result = bm_fun(5 * unit, 15, 5)

    @parameterized.product(
        unit=[second, meter],
    )
    def test_fun_array_creation_misc2(self, unit):
        bm_fun_list = [getattr(um, fun) for fun in fun_array_creation_misc2]
        jnp_fun_list = [getattr(jnp, fun) for fun in fun_array_creation_misc2]

        for bm_fun, jnp_fun in zip(bm_fun_list, jnp_fun_list):
            if bm_fun.__name__ == 'meshgrid':
                result = bm_fun(jnp.array([1, 2, 3]), jnp.array([4, 5, 6]))
                expected = jnp_fun(jnp.array([1, 2, 3]), jnp.array([4, 5, 6]))
                for r, e in zip(result, expected):
                    assert_quantity(r, e)

                result = bm_fun(jnp.array([1, 2, 3]) * unit, jnp.array([4, 5, 6]) * unit)
                expected = jnp_fun(jnp.array([1, 2, 3]), jnp.array([4, 5, 6]))
                for r, e in zip(result, expected):
                    assert_quantity(r, e, unit=unit)

            elif bm_fun.__name__ == 'vander':
                result = bm_fun(jnp.array([1, 2, 3]), 3)
                expected = jnp_fun(jnp.array([1, 2, 3]), 3)
                assert_quantity(result, expected)

                result = bm_fun(jnp.array([1, 2, 3]), 3, unit=unit)
                expected = jnp_fun(jnp.array([1, 2, 3]), 3)
                assert_quantity(result, expected, unit=unit)

                with pytest.raises(AssertionError):
                    result = bm_fun(jnp.array([1, 2, 3]) * unit, 3)

    @parameterized.product(
        unit=[second, meter],
    )
    def test_fun_array_creation_asarray(self, unit):
        bm_fun_list = [getattr(um, fun) for fun in fun_array_creation_asarray]
        jnp_fun_list = [getattr(jnp, fun) for fun in fun_array_creation_asarray]

        for bm_fun, jnp_fun in zip(bm_fun_list, jnp_fun_list):
            result = bm_fun([1, 2, 3])
            expected = jnp_fun([1, 2, 3])
            assert_quantity(result, expected)

            result = bm_fun([1, 2, 3] * unit)
            expected = jnp_fun([1, 2, 3])
            assert_quantity(result, expected, unit=unit)

            result = bm_fun([1 * unit, 2 * unit, 3 * unit])
            expected = jnp_fun([1, 2, 3])
            assert_quantity(result, expected, unit=unit)

            # list of list
            result = bm_fun([[1, 2], [3, 4]])
            expected = jnp_fun([[1, 2], [3, 4]])
            assert_quantity(result, expected)

            result = bm_fun([[1, 2], [3, 4]] * unit)
            expected = jnp_fun([[1, 2], [3, 4]])
            assert_quantity(result, expected, unit=unit)

            # scalar
            result = bm_fun(1)
            expected = jnp_fun(1)
            assert_quantity(result, expected)

            result = bm_fun(1 * unit)
            expected = jnp_fun(1)
            assert_quantity(result, expected, unit=unit)

            with pytest.raises(u.UnitMismatchError):
                result = bm_fun(1 * unit, unit=u.volt)

            with pytest.raises(u.UnitMismatchError):
                result = bm_fun([1 * unit, 2 * unit * unit, 3 * unit / unit])

    @parameterized.product(
        value=[1, 10, 100]
    )
    def test_fun_array_creation_indices(self, value):
        bm_fun_list = [getattr(um, fun) for fun in fun_array_creation_indices]
        jnp_fun_list = [getattr(jnp, fun) for fun in fun_array_creation_indices]

        for bm_fun, jnp_fun in zip(bm_fun_list, jnp_fun_list):
            print(f'fun: {bm_fun.__name__}')

            result = bm_fun(value)
            expected = jnp_fun(value)
            for r, e in zip(result, expected):
                assert_quantity(r, e)

    @parameterized.product(
        shape=[(3, 3), (6, 6), (10, 10)]
    )
    def test_fun_array_creation_indices_from(self, shape):
        bm_fun_list = [getattr(um, fun) for fun in fun_array_creation_indices_from]
        jnp_fun_list = [getattr(jnp, fun) for fun in fun_array_creation_indices_from]

        for bm_fun, jnp_fun in zip(bm_fun_list, jnp_fun_list):
            print(f'fun: {bm_fun.__name__}')

            value = jnp.ones(shape)
            result = bm_fun(value)
            expected = jnp_fun(value)
            for r, e in zip(result, expected):
                assert_quantity(r, e)

    def test_fun_array_creation_other(self):
        # TODO
        ...
