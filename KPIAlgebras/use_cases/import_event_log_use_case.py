from pm4py.objects.log.importer.xes import factory as xes_importer
import os
from KPIAlgebras.util import constants


class ImportEventLogUseCase(object):
    def import_event_log_from_xes(self, request_object):
        path = os.path.join(constants.upload_folder,request_object.parameters)
        event_log = xes_importer.import_log(path)
        return event_log