from dargs import Argument, Variant
from dflow.plugins.dispatcher import DispatcherExecutor

def dispatcher_args():
    """free style dispatcher args"""
    return []


def variant_executor():
    doc = f"The type of the executor."
    return Variant(
        "type",
        [
            Argument("dispatcher", dict, dispatcher_args()),
        ],
        doc=doc,
        default_tag="dispatcher"
    )


def template_conf_args():
    doc_image = "The image to run the step."
    doc_timeout = "The time limit of the OP. Unit is second."
    doc_retry_on_transient_error = (
        "The number of retry times if a TransientError is raised."
    )
    doc_timeout_as_transient_error = "Treat the timeout as TransientError."
    doc_envs = "The environmental variables."
    return [
        Argument("image", str, optional=True, default=None, doc=doc_image),
        Argument("timeout", int, optional=True, default=None, doc=doc_timeout),
        Argument(
            "retry_on_transient_error",
            int,
            optional=True,
            default=None,
            doc=doc_retry_on_transient_error,
        ),
        Argument(
            "timeout_as_transient_error",
            bool,
            optional=True,
            default=False,
            doc=doc_timeout_as_transient_error,
        ),
        Argument("envs", dict, optional=True, default=None, doc=doc_envs),
    ]

def template_slice_conf_args():
    doc_group_size = "The number of tasks running on a single node. It is efficient for a large number of short tasks."
    doc_pool_size = "The number of tasks running at the same time on one node."
    return [
        Argument("group_size", int, optional=True, default=None, doc=doc_group_size),
        Argument("pool_size", int, optional=True, default=None, doc=doc_pool_size),
    ]

def step_conf_args():
    doc_template = "The configs passed to the PythonOPTemplate."
    doc_template_slice = "The configs passed to the Slices."
    doc_executor = "The executor of the step."
    doc_continue_on_failed = "If continue the the step is failed (FatalError, TransientError, A certain number of retrial is reached...)."
    doc_continue_on_num_success = "Only in the sliced OP case. Continue the workflow if a certain number of the sliced jobs are successful."
    doc_continue_on_success_ratio = "Only in the sliced OP case. Continue the workflow if a certain ratio of the sliced jobs are successful."
    doc_parallelism = "The parallelism for the step"

    return [
        Argument(
            "template_config",
            dict,
            template_conf_args(),
            optional=True,
            default={"image": None},
            doc=doc_template,
        ),
        Argument(
            "template_slice_config",
            dict,
            template_slice_conf_args(),
            optional=True,
            doc=doc_template_slice,
        ),
        Argument(
            "continue_on_failed",
            bool,
            optional=True,
            default=False,
            doc=doc_continue_on_failed,
        ),
        Argument(
            "continue_on_num_success",
            int,
            optional=True,
            default=None,
            doc=doc_continue_on_num_success,
        ),
        Argument(
            "continue_on_success_ratio",
            float,
            optional=True,
            default=None,
            doc=doc_continue_on_success_ratio,
        ),
        Argument("parallelism", int, optional=True, default=None, doc=doc_parallelism),
        Argument(
            "executor",
            dict,
            [],
            [variant_executor()],
            optional=True,
            default=None,
            doc=doc_executor,
        ),
    ]


def normalize_step_config(data):
    sca = step_conf_args()
    base = Argument("base", dict, sca)
    data = base.normalize_value(data, trim_pattern="_*")
    # not possible to strictly check dispatcher arguments, dirty hack!
    base.check_value(data, strict=False)
    return data



def init_executor(
    executor_dict,
):
    if executor_dict is None:
        return None
    etype = executor_dict.pop("type")
    if etype == "dispatcher":
        return DispatcherExecutor(**executor_dict)
    else:
        raise RuntimeError("unknown executor type", etype)
