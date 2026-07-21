from taskflow.api import Api
from taskflow.models import TaskState


def test_submit_poll_ack_roundtrip():
    api = Api()
    submitted = api.submit("default", {"kind": "email"})
    claimed = api.poll("default")
    assert claimed is not None and claimed.id == submitted.id
    finished = api.ack(claimed, ok=True)
    assert finished.state is TaskState.DONE


def test_retry_until_failed():
    api = Api()
    api.submit("default", {"kind": "flaky"})
    for _ in range(3):
        task = api.poll("default")
        task = api.ack(task, ok=False)
    assert task.state is TaskState.FAILED
