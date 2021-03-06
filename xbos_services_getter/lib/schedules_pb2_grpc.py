# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

from . import schedules_pb2 as schedules__pb2


class SchedulesStub(object):
  """The temperature service definition.
  """

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.GetComfortband = channel.unary_unary(
        '/schedules_historical.Schedules/GetComfortband',
        request_serializer=schedules__pb2.Request.SerializeToString,
        response_deserializer=schedules__pb2.ScheduleReply.FromString,
        )
    self.GetDoNotExceed = channel.unary_unary(
        '/schedules_historical.Schedules/GetDoNotExceed',
        request_serializer=schedules__pb2.Request.SerializeToString,
        response_deserializer=schedules__pb2.ScheduleReply.FromString,
        )


class SchedulesServicer(object):
  """The temperature service definition.
  """

  def GetComfortband(self, request, context):
    """A simple RPC.

    Sends the historic occupancy for a given building and zone within a duration (start, end), and a requested window
    An error  is returned if there are no temperature for the given request
    """
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def GetDoNotExceed(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_SchedulesServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'GetComfortband': grpc.unary_unary_rpc_method_handler(
          servicer.GetComfortband,
          request_deserializer=schedules__pb2.Request.FromString,
          response_serializer=schedules__pb2.ScheduleReply.SerializeToString,
      ),
      'GetDoNotExceed': grpc.unary_unary_rpc_method_handler(
          servicer.GetDoNotExceed,
          request_deserializer=schedules__pb2.Request.FromString,
          response_serializer=schedules__pb2.ScheduleReply.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'schedules_historical.Schedules', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))
