from __future__ import annotations

from pyspark.sql import types as spark_types

from uff.types import *
import uff.ir_pb2 as ir_pb2


primitive_type_mapping = {
    BYTES.data.primitive_type: spark_types.BinaryType(),
    STRING.data.primitive_type: spark_types.StringType(),
    INTEGER.data.primitive_type: spark_types.IntegerType(),
    LONG.data.primitive_type: spark_types.LongType(),
    FLOAT.data.primitive_type: spark_types.FloatType(),
    DOUBLE.data.primitive_type: spark_types.DoubleType(),
    BOOLEAN.data.primitive_type: spark_types.BooleanType(),
    TIMESTAMP.data.primitive_type: spark_types.TimestampType(),
}


def to_spark_type(data: ir_pb2.DType):
    if data.type_category == ir_pb2.DType.TypeCategory.PRIMITIVE:
        return primitive_type_mapping[data.primitive_type]
    elif data.complex_type == ir_pb2.DType.ComplexType.ARRAY:
        return array_spec_to_spark_type(data.array_spec)
    elif data.complex_type == ir_pb2.DType.ComplexType.MAP:
        return map_spec_to_spark_type(data.map_spec)
    elif data.complex_type == ir_pb2.DType.ComplexType.STRUCT:
        return struct_type_to_spark_type(data.struct_fields)
    else:
        raise ValueError(f"Unsupported dtype {data.complex_type}")


def array_spec_to_spark_type(array_spec: ir_pb2.DType.ArraySpec):
    return spark_types.ArrayType(to_spark_type(array_spec.element_type))


def map_spec_to_spark_type(map_spec: ir_pb2.DType.MapSpec):
    return spark_types.MapType(
        to_spark_type(map_spec.key_type), to_spark_type(map_spec.value_type)
    )


def struct_type_to_spark_type(struct_fields: list[ir_pb2.DType.StructField]):
    return spark_types.StructType(
        [
            spark_types.StructField(
                field.name, to_spark_type(field.field_type), field.nullable
            )
            for field in struct_fields
        ]
    )
