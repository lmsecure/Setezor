from enum import StrEnum


class SignalEnum(StrEnum):
    notify = 'notify'
    job_status = 'job_status'
    task_status = 'task_status'
    result_entities = 'result_entities'
    information = 'information'