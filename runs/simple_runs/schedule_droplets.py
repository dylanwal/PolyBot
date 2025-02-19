from datetime import datetime, timedelta

from unitpy import Unit, Quantity

from chembot.scheduler import JobSequence, JobConcurrent, Event, Schedule
from chembot.scheduler.job_submitter import JobSubmitter
from chembot.equipment.valves import ValveServo
from chembot.equipment.pumps import SyringePumpHarvard

from runs.launch_equipment.names import NamesPump, NamesValves


def job_flow(volume: Quantity, flow_rate: Quantity):
    return JobSequence(
        [
            _valves(),
            _flow(volume, flow_rate)
        ]
    )


def _valves() -> JobConcurrent:
    return JobConcurrent(
        [
            Event(
                resource=NamesValves.BACK,
                callable_=ValveServo.write_move,
                duration=timedelta(seconds=1.5),
                kwargs={"position": "flow"}
            ),
            Event(
                resource=NamesValves.MIDDLE,
                callable_=ValveServo.write_move,
                duration=timedelta(seconds=1.5),
                kwargs={"position": "flow"}
            ),
            Event(
                resource=NamesValves.FRONT,
                callable_=ValveServo.write_move,
                duration=timedelta(seconds=1.5),
                kwargs={"position": "flow"}
            ),
        ]
    )


def _flow(volume: Quantity, flow_rate: Quantity) -> JobConcurrent:
    return JobConcurrent(
        [
            Event(
                resource=NamesPump.BACK,
                callable_=SyringePumpHarvard.write_infuse,
                duration=SyringePumpHarvard.compute_run_time(volume, flow_rate).to_timedelta(),
                kwargs={"volume": volume, "flow_rate": flow_rate}
            ),
            Event(
                resource=NamesPump.FRONT,
                callable_=SyringePumpHarvard.write_infuse,
                duration=SyringePumpHarvard.compute_run_time(volume, flow_rate).to_timedelta(),
                kwargs={"volume": volume, "flow_rate": flow_rate}
            )
        ]
    )


def job_fill_back(volume: Quantity, flow_rate: Quantity):
    return JobSequence(
        [
            Event(
                resource=NamesValves.BACK,
                callable_=ValveServo.write_move,
                duration=timedelta(seconds=1.5),
                kwargs={"position": "fill"}
            ),
            Event(
                resource=NamesPump.BACK,
                callable_=SyringePumpHarvard.write_withdraw,
                duration=SyringePumpHarvard.compute_run_time(volume, flow_rate).to_timedelta(),
                kwargs={"volume": volume, "flow_rate": flow_rate}
            ),
        ]
    )


def job_fill_front(volume: Quantity, flow_rate: Quantity):
    return JobSequence(
        [
            Event(
                resource=NamesValves.FRONT,
                callable_=ValveServo.write_move,
                duration=timedelta(seconds=1.5),
                kwargs={"position": "fill"}
            ),
            Event(
                resource=NamesPump.FRONT,
                callable_=SyringePumpHarvard.write_withdraw,
                duration=SyringePumpHarvard.compute_run_time(volume, flow_rate).to_timedelta(),
                kwargs={"volume": volume, "flow_rate": flow_rate}
            ),
        ]
    )


def job_fill(volume: Quantity, flow_rate: Quantity) -> JobConcurrent:
    return JobConcurrent(
        [
            job_fill_back(volume, flow_rate),
            job_fill_front(volume, flow_rate)
        ]
    )


def job_air_purge() -> JobSequence:
    volume = 1 * Unit.ml
    flow_rate = 5 * Unit("ml/min")

    return JobSequence(
        [
            Event(
                resource=NamesValves.BACK,
                callable_=ValveServo.write_move,
                duration=timedelta(seconds=1.5),
                kwargs={"position": "fill"}
            ),
            Event(
                resource=NamesPump.BACK,
                callable_=SyringePumpHarvard.write_withdraw,
                duration=SyringePumpHarvard.compute_run_time(volume, flow_rate).to_timedelta(),
                kwargs={"volume": volume, "flow_rate": flow_rate},
            ),
            Event(
                resource=NamesValves.BACK,
                callable_=ValveServo.write_move,
                duration=timedelta(seconds=1.5),
                kwargs={"position": "flow"}
            ),
            Event(
                resource=NamesPump.BACK,
                callable_=SyringePumpHarvard.write_infuse,
                duration=SyringePumpHarvard.compute_run_time(volume, flow_rate).to_timedelta(),
                kwargs={"volume": volume, "flow_rate": flow_rate}
            ),
        ]
    )


def job_droplets(volume: Quantity, flow_rate: Quantity, flow_rate_fill: Quantity) -> JobSequence:
    return JobSequence(
        [
            job_fill(volume, flow_rate_fill),
            job_flow(volume, flow_rate),
            job_air_purge(),
        ]
    )


def main():
    job_submitter = JobSubmitter()

    job = job_droplets(
        volume=0.4 * Unit.mL,
        flow_rate=0.2 * (Unit.mL / Unit.min),
        flow_rate_fill=1.5 * (Unit.mL / Unit.min)
    )
    result = job_submitter.submit(job)
    print(result)

    # full_schedule = job_submitter.get_schedule()
    # print(full_schedule)

    print("hi")


if __name__ == "__main__":
    main()
