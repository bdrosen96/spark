#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import unittest
from inspect import signature
from typing import Union, Iterator, Tuple, cast, get_type_hints

from pyspark.sql.functions import mean, lit
from pyspark.testing.sqlutils import (
    ReusedSQLTestCase,
    have_pandas,
    have_pyarrow,
    pandas_requirement_message,
    pyarrow_requirement_message,
)
from pyspark.sql.pandas.typehints import infer_eval_type
from pyspark.sql.pandas.functions import pandas_udf, PandasUDFType
from pyspark.sql import Row

if have_pandas:
    import pandas as pd
    import numpy as np
    from pandas.testing import assert_frame_equal


@unittest.skipIf(
    not have_pandas or not have_pyarrow,
    cast(str, pandas_requirement_message or pyarrow_requirement_message),
)
class PandasUDFTypeHintsTests(ReusedSQLTestCase):
    def test_type_annotation_scalar(self):
        def func(col           )             :
            pass

        self.assertEqual(
            infer_eval_type(signature(func), get_type_hints(func)), PandasUDFType.SCALAR
        )

        def func(col              , col1           )                :
            pass

        self.assertEqual(
            infer_eval_type(signature(func), get_type_hints(func)), PandasUDFType.SCALAR
        )

        def func(col              , *args           )             :
            pass

        self.assertEqual(
            infer_eval_type(signature(func), get_type_hints(func)), PandasUDFType.SCALAR
        )

        def func(col           , *args           , **kwargs              )             :
            pass

        self.assertEqual(
            infer_eval_type(signature(func), get_type_hints(func)), PandasUDFType.SCALAR
        )

        def func(col           , *, col2              )                :
            pass

        self.assertEqual(
            infer_eval_type(signature(func), get_type_hints(func)), PandasUDFType.SCALAR
        )

        def func(col                                , *, col2              )             :
            pass

        self.assertEqual(
            infer_eval_type(signature(func), get_type_hints(func)), PandasUDFType.SCALAR
        )

    def test_type_annotation_scalar_iter(self):
        def func(iter                     )                       :
            pass

        self.assertEqual(
            infer_eval_type(signature(func), get_type_hints(func)), PandasUDFType.SCALAR_ITER
        )

        def func(iter                                          )                          :
            pass

        self.assertEqual(
            infer_eval_type(signature(func), get_type_hints(func)), PandasUDFType.SCALAR_ITER
        )

        def func(iter                                    )                       :
            pass

        self.assertEqual(
            infer_eval_type(signature(func), get_type_hints(func)), PandasUDFType.SCALAR_ITER
        )

        def func(iter                                                      )                       :
            pass

        self.assertEqual(
            infer_eval_type(signature(func), get_type_hints(func)), PandasUDFType.SCALAR_ITER
        )

    def test_type_annotation_group_agg(self):
        def func(col           )       :
            pass

        self.assertEqual(
            infer_eval_type(signature(func), get_type_hints(func)), PandasUDFType.GROUPED_AGG
        )

        def func(col              , col1           )       :
            pass

        self.assertEqual(
            infer_eval_type(signature(func), get_type_hints(func)), PandasUDFType.GROUPED_AGG
        )

        def func(col              , *args           )       :
            pass

        self.assertEqual(
            infer_eval_type(signature(func), get_type_hints(func)), PandasUDFType.GROUPED_AGG
        )

        def func(col           , *args           , **kwargs              )       :
            pass

        self.assertEqual(
            infer_eval_type(signature(func), get_type_hints(func)), PandasUDFType.GROUPED_AGG
        )

        def func(col           , *, col2              )         :
            pass

        self.assertEqual(
            infer_eval_type(signature(func), get_type_hints(func)), PandasUDFType.GROUPED_AGG
        )

        def func(col                                , *, col2              )         :
            pass

        self.assertEqual(
            infer_eval_type(signature(func), get_type_hints(func)), PandasUDFType.GROUPED_AGG
        )

    def test_type_annotation_negative(self):
        def func(col     )             :
            pass

        self.assertRaisesRegex(
            NotImplementedError,
            "Unsupported signature.*str",
            infer_eval_type,
            signature(func),
            get_type_hints(func),
        )

        def func(col              , col1     )                :
            pass

        self.assertRaisesRegex(
            NotImplementedError,
            "Unsupported signature.*int",
            infer_eval_type,
            signature(func),
            get_type_hints(func),
        )

        def func(col                          , col1     )                :
            pass

        self.assertRaisesRegex(
            NotImplementedError,
            "Unsupported signature.*str",
            infer_eval_type,
            signature(func),
            get_type_hints(func),
        )

        def func(col           )                       :
            pass

        self.assertRaisesRegex(
            NotImplementedError,
            "Unsupported signature.*Tuple",
            infer_eval_type,
            signature(func),
            get_type_hints(func),
        )

        def func(col, *args           )             :
            pass

        self.assertRaisesRegex(
            ValueError,
            "should be specified.*Series",
            infer_eval_type,
            signature(func),
            get_type_hints(func),
        )

        def func(col           , *args           , **kwargs              ):
            pass

        self.assertRaisesRegex(
            ValueError,
            "should be specified.*Series",
            infer_eval_type,
            signature(func),
            get_type_hints(func),
        )

        def func(col           , *, col2)                :
            pass

        self.assertRaisesRegex(
            ValueError,
            "should be specified.*Series",
            infer_eval_type,
            signature(func),
            get_type_hints(func),
        )

    def test_scalar_udf_type_hint(self):
        df = self.spark.range(10).selectExpr("id", "id as v")

        def plus_one(v                                )             :
            return v + 1  # type: ignore[return-value]

        plus_one = pandas_udf("long")(plus_one)
        actual = df.select(plus_one(df.v).alias("plus_one"))
        expected = df.selectExpr("(v + 1) as plus_one")
        assert_frame_equal(expected.toPandas(), actual.toPandas())

    def test_scalar_iter_udf_type_hint(self):
        df = self.spark.range(10).selectExpr("id", "id as v")

        def plus_one(itr                     )                       :
            for s in itr:
                yield s + 1

        plus_one = pandas_udf("long")(plus_one)

        actual = df.select(plus_one(df.v).alias("plus_one"))
        expected = df.selectExpr("(v + 1) as plus_one")
        assert_frame_equal(expected.toPandas(), actual.toPandas())

    def test_group_agg_udf_type_hint(self):
        df = self.spark.range(10).selectExpr("id", "id as v")

        def weighted_mean(v           , w           )              :
            return np.average(v, weights=w)

        weighted_mean = pandas_udf("double")(weighted_mean)

        actual = df.groupby("id").agg(weighted_mean(df.v, lit(1.0))).sort("id")
        expected = df.groupby("id").agg(mean(df.v).alias("weighted_mean(v, 1.0)")).sort("id")
        assert_frame_equal(expected.toPandas(), actual.toPandas())

    def test_ignore_type_hint_in_group_apply_in_pandas(self):
        df = self.spark.range(10)

        def pandas_plus_one(v              )                :
            return v + 1

        actual = df.groupby("id").applyInPandas(pandas_plus_one, schema=df.schema).sort("id")
        expected = df.selectExpr("id + 1 as id")
        assert_frame_equal(expected.toPandas(), actual.toPandas())

    def test_ignore_type_hint_in_cogroup_apply_in_pandas(self):
        df = self.spark.range(10)

        def pandas_plus_one(left              , right              )                :
            return left + 1

        actual = (
            df.groupby("id")
            .cogroup(self.spark.range(10).groupby("id"))
            .applyInPandas(pandas_plus_one, schema=df.schema)
            .sort("id")
        )
        expected = df.selectExpr("id + 1 as id")
        assert_frame_equal(expected.toPandas(), actual.toPandas())

    def test_ignore_type_hint_in_map_in_pandas(self):
        df = self.spark.range(10)

        def pandas_plus_one(iter                        )                          :
            return map(lambda v: v + 1, iter)

        actual = df.mapInPandas(pandas_plus_one, schema=df.schema)
        expected = df.selectExpr("id + 1 as id")
        assert_frame_equal(expected.toPandas(), actual.toPandas())

    def test_string_type_annotation(self):
        def func(col             )               :
            pass

        self.assertEqual(
            infer_eval_type(signature(func), get_type_hints(func)), PandasUDFType.SCALAR
        )

        def func(col                , col1             )                  :
            pass

        self.assertEqual(
            infer_eval_type(signature(func), get_type_hints(func)), PandasUDFType.SCALAR
        )

        def func(col                , *args             )               :
            pass

        self.assertEqual(
            infer_eval_type(signature(func), get_type_hints(func)), PandasUDFType.SCALAR
        )

        def func(col             , *args             , **kwargs                )               :
            pass

        self.assertEqual(
            infer_eval_type(signature(func), get_type_hints(func)), PandasUDFType.SCALAR
        )

        def func(col             , *, col2                )                  :
            pass

        self.assertEqual(
            infer_eval_type(signature(func), get_type_hints(func)), PandasUDFType.SCALAR
        )

        def func(col                                    , *, col2                )               :
            pass

        self.assertEqual(
            infer_eval_type(signature(func), get_type_hints(func)), PandasUDFType.SCALAR
        )

        def func(col                                  , *, col2                )               :
            pass

        self.assertEqual(
            infer_eval_type(signature(func), get_type_hints(func)), PandasUDFType.SCALAR
        )


if __name__ == "__main__":
    from pyspark.sql.tests.test_pandas_udf_typehints import *  # noqa: #401

    try:
        import xmlrunner  # type: ignore[import]

        testRunner = xmlrunner.XMLTestRunner(output="target/test-reports", verbosity=2)
    except ImportError:
        testRunner = None
    unittest.main(testRunner=testRunner, verbosity=2)
