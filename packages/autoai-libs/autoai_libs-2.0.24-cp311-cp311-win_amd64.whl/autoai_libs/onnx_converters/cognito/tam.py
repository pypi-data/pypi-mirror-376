################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################
import numpy as np
from skl2onnx import update_registered_converter
from skl2onnx.algebra.onnx_operator import OnnxSubEstimator
from skl2onnx.algebra.onnx_ops import OnnxConcat, OnnxCast, OnnxReshape
from skl2onnx.common._container import ModelComponentContainer
from skl2onnx.common._topology import Operator, Scope
from skl2onnx.common.data_types import guess_numpy_type, guess_proto_type
from sklearn.decomposition import PCA

from autoai_libs.cognito.transforms.transform_extras import ClusterDBSCAN, IsolationForestAnomaly
from autoai_libs.cognito.transforms.transform_utils import TAM
from autoai_libs.onnx_converters.cognito.utils import onnx_replace_nan_and_inf


def tam_shape_calculator(operator: Operator) -> None:
    op_features = sum(map(lambda x: x.type.shape[1], operator.inputs))
    transformer = operator.raw_operator.trans_class_obj_
    if isinstance(transformer, PCA):
        dims = [operator.inputs[0].get_first_dimension(), transformer.components_.shape[1] + op_features]
    elif isinstance(transformer, (ClusterDBSCAN, IsolationForestAnomaly)):
        dims = [operator.inputs[0].get_first_dimension(), 1 + op_features]
    else:
        dims = [operator.inputs[0].get_first_dimension(), op_features * 2]
    operator.outputs[0].type = operator.inputs[0].type.__class__(dims)


def tam_transformer_converter(scope: Scope, operator: Operator, container: ModelComponentContainer) -> None:
    op: TAM = operator.raw_operator
    opv = container.target_opset

    transformer = op.trans_class_obj_
    if isinstance(transformer, ClusterDBSCAN):
        scaler = OnnxSubEstimator(transformer.scaler, *operator.inputs, op_version=opv)
        knn_proba = scope.get_unique_variable_name("knn_proba")
        knn_label = scope.get_unique_variable_name("knn_label")
        knn = OnnxSubEstimator(transformer.knn, scaler, op_version=opv, output_names=[knn_label, knn_proba])
        knn.add_to(scope, container)
        onnx_transformer = OnnxReshape(
            OnnxCast(knn_label, to=guess_proto_type(operator.inputs[0].type), op_version=opv),
            np.array([-1, 1], dtype=np.int64),
            op_version=opv,
        )
    elif isinstance(transformer, IsolationForestAnomaly):
        isoforest_proba = scope.get_unique_variable_name("isoforest_proba")
        isoforest_label = scope.get_unique_variable_name("isoforest_label")
        isoforest = OnnxSubEstimator(
            transformer.isoforest, *operator.inputs, op_version=opv, output_names=[isoforest_label, isoforest_proba]
        )
        isoforest.add_to(scope, container)
        onnx_transformer = OnnxReshape(
            OnnxCast(isoforest_label, to=guess_proto_type(operator.inputs[0].type), op_version=opv),
            np.array([-1, 1], dtype=np.int64),
            op_version=opv,
        )
    else:
        onnx_transformer = OnnxSubEstimator(transformer, *operator.inputs, op_version=opv)

    replaced = onnx_replace_nan_and_inf(
        onnx_transformer, dtype=guess_numpy_type(operator.inputs[0].type), op_version=opv
    )
    output = OnnxConcat(*(operator.inputs + [replaced]), axis=1, op_version=opv, output_names=operator.outputs)
    output.add_to(scope, container)


transformer = TAM
update_registered_converter(
    model=transformer,
    alias=f"AutoAI{transformer.__name__}",
    shape_fct=tam_shape_calculator,
    convert_fct=tam_transformer_converter,
)
