"""Explicit CPU execution for the cloud worker."""


def torch_device():
    return "cpu"


def cuda_usable():
    return False, "standalone cloud worker uses CPU"
