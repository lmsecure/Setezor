from typing import Type
from setezor.signals.base_signal import Signal
from setezor.schemas.signal import SignalEnum
from setezor.signals.information_signal import InformationSignal
from setezor.signals.job_status_signal import JobStatusSignal
from setezor.signals.notify_signal import NotifySignal
from setezor.signals.result_entities_signal import ResultEntitiesSignal
from setezor.signals.task_status_signal import TaskStatusSignal

signal_strategy: dict[SignalEnum, Type[Signal]] = {
    SignalEnum.notify: NotifySignal,
    SignalEnum.job_status: JobStatusSignal,
    SignalEnum.task_status: TaskStatusSignal,
    SignalEnum.result_entities: ResultEntitiesSignal,
    SignalEnum.information: InformationSignal
}