import uuid
from datetime import datetime

from .ground_station import GroundStation, ground_station_from_dict
from .horizontal_coords import HorizontalCoords, horizontal_coords_to_dict, horizontal_coords_from_dict
from .satellite import Satellite, satellite_from_dict


class Session:
    STATUS_SCHEDULED = 'scheduled'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'

    def __init__(self, id: uuid.UUID, satellite: Satellite, ground_station: GroundStation, start_datetime: datetime, end_datetime: datetime, status: str, tca_coords: HorizontalCoords, created_by: str):
        self._id = id
        self._satellite = satellite
        self._ground_station = ground_station
        self._start_datetime = start_datetime
        self._end_datetime = end_datetime
        self._status = status
        self._tca_coords = tca_coords
        self._created_by = created_by

    @property
    def id(self) -> uuid.UUID:
        return self._id

    @property
    def satellite(self) -> Satellite:
        return self._satellite

    @property
    def ground_station(self) -> GroundStation:
        return self._ground_station

    @property
    def start_datetime(self) -> datetime:
        return self._start_datetime

    @property
    def end_datetime(self) -> datetime:
        return self._end_datetime

    @property
    def status(self) -> str:
        return self._status

    def statuses(self) -> list:
        return [self.STATUS_SCHEDULED, self.STATUS_IN_PROGRESS, self.STATUS_SUCCESS, self.STATUS_FAILED]

    @property
    def tca_coords(self) -> HorizontalCoords:
        return self._tca_coords

    @property
    def created_by(self) -> str:
        return self._created_by

    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'status': self.status,
            'satellite': {'id': self.satellite.id},
            'groundStation': {'id': self.ground_station.id},
            'startDateTime': self.start_datetime.isoformat(sep='T', timespec='auto'),
            'endDateTime': self.end_datetime.isoformat(sep='T', timespec='auto'),
            'tcaCoords': horizontal_coords_to_dict(self.tca_coords),
            'createdBy': self._created_by,
        }


def session_from_dict(ses_dict: dict) -> Session:
    return Session(
        id=uuid.UUID(ses_dict['id']),
        satellite=satellite_from_dict(ses_dict['satellite']) if 'satellite' in ses_dict else None,
        ground_station=ground_station_from_dict(ses_dict['groundStation']) if 'groundStation' in ses_dict else None,
        status=ses_dict.get('status'),
        start_datetime=datetime.fromisoformat(ses_dict['startDateTime']) if 'startDateTime' in ses_dict else None,
        end_datetime=datetime.fromisoformat(ses_dict['endDateTime']) if 'endDateTime' in ses_dict else None,
        tca_coords=horizontal_coords_from_dict(ses_dict['tcaCoords']) if 'tcaCoords' in ses_dict else None,
        created_by=ses_dict.get('createdBy'),
    )
